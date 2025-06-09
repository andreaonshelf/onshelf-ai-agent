"""
Queue Management API
Provides endpoints for managing the extraction queue and system selection
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import io
import json
import glob
import asyncio
from supabase import create_client, Client

from ..config import SystemConfig
from ..utils import logger

router = APIRouter(prefix="/api/queue", tags=["Queue Management"])

# Initialize Supabase client
config = SystemConfig()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)


@router.get("/items")
async def get_queue_items(
    status: Optional[str] = Query(None),
    system: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get queue items with filtering and prioritization"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Query ai_extraction_queue without joins first
        query = supabase.table("ai_extraction_queue").select(
            "id, upload_id, ready_media_id, enhanced_image_path, status, "
            "human_review_required, final_accuracy, selected_systems, "
            "comparison_group_id, current_extraction_system, processing_attempts, "
            "created_at, started_at, completed_at, iterations_completed, api_cost"
        )
        
        # Apply status filter
        if status:
            if status == 'review':
                query = query.eq("human_review_required", True)
            else:
                query = query.eq("status", status)
        else:
            # Default: show all relevant statuses
            # Build query with OR conditions for multiple statuses
            query = query.or_(
                "status.eq.pending,"
                "status.eq.processing,"
                "status.eq.completed,"
                "status.eq.failed"
            )
        
        # Apply system filter
        if system:
            query = query.contains("selected_systems", system)
        
        # Execute query with limit
        result = query.limit(limit).execute()
        
        if not result.data:
            return {"items": [], "total": 0}
        
        # Sort by priority: review required > processing > failed > completed > pending
        def get_priority(item):
            if item.get('human_review_required'):
                return 1
            status = item.get('status', '')
            if status == 'processing':
                return 2
            elif status == 'failed':
                return 3
            elif status == 'completed':
                return 4
            else:  # pending
                return 5
        
        sorted_items = sorted(result.data, key=lambda x: (
            get_priority(x),
            -(datetime.fromisoformat(x['created_at'].replace('Z', '+00:00')).timestamp())
        ))
        
        # Enrich items with upload data and extraction results
        for item in sorted_items:
            try:
                # Initialize defaults
                item['store_name'] = 'Unknown Store'
                item['category'] = 'Unknown Category'
                
                # Parse extraction results to get product count
                if item.get('extraction_result') and isinstance(item['extraction_result'], dict):
                    extraction_result = item['extraction_result']
                    total_products = 0
                    
                    # Check different possible locations for products
                    if "stages" in extraction_result:
                        stages = extraction_result.get("stages", {})
                        if "products" in stages and isinstance(stages["products"], dict):
                            products_data = stages["products"].get("data", [])
                            if isinstance(products_data, list):
                                total_products = len(products_data)
                        elif "product_v1" in stages and isinstance(stages["product_v1"], dict):
                            products_data = stages["product_v1"].get("data", [])
                            if isinstance(products_data, list):
                                total_products = len(products_data)
                    elif "products" in extraction_result:
                        if isinstance(extraction_result["products"], list):
                            total_products = len(extraction_result["products"])
                    
                    # Add extraction_results summary for sidebar display
                    item['extraction_results'] = {
                        'total_products': total_products
                    }
                
                # Skip if no upload_id
                if not item.get('upload_id'):
                    continue
                    
                # Get upload data with store info from metadata
                upload_result = supabase.table("uploads").select(
                    "category, created_at, metadata"
                ).eq("id", item['upload_id']).execute()
                
                if upload_result.data and len(upload_result.data) > 0:
                    upload_data = upload_result.data[0]
                    
                    # Flatten category at top level for frontend
                    if upload_data.get('category'):
                        item['category'] = upload_data['category']
                    
                    # Try to get store info from collection_id first (more accurate)
                    store_name_found = False
                    if upload_data.get('collection_id'):
                        collection_result = supabase.table("collections").select(
                            "store_id"
                        ).eq("id", upload_data['collection_id']).execute()
                        
                        if collection_result.data and len(collection_result.data) > 0:
                            collection_data = collection_result.data[0]
                            item['uploads']['collections'] = collection_data
                            
                            # Get store info if store_id exists
                            if collection_data.get('store_id'):
                                store_result = supabase.table("stores").select(
                                    "retailer_name, format, location_city, location_address, country"
                                ).eq("store_id", collection_data['store_id']).execute()
                                
                                if store_result.data and len(store_result.data) > 0:
                                    store_info = store_result.data[0]
                                    item['uploads']['collections']['stores'] = store_info
                                    
                                    # Flatten store name at top level for frontend
                                    store_name = store_info.get('retailer_name', '')
                                    if store_info.get('location_city'):
                                        store_name += f" - {store_info['location_city']}"
                                    item['store_name'] = store_name
                                    store_name_found = True
                    
                    # Fallback to metadata if no store found from collection
                    if not store_name_found:
                        metadata = upload_data.get('metadata', {})
                        if isinstance(metadata, dict):
                            store_name = metadata.get('store_name', metadata.get('retailer', 'Unknown Store'))
                        else:
                            store_name = 'Unknown Store'
                        item['store_name'] = store_name
            except Exception as e:
                logger.warning(f"Failed to enrich item {item['id']} with upload data: {e}")
                # Continue processing other items - defaults already set
                
        logger.info(f"Retrieved {len(sorted_items)} queue items", component="queue_api")
        
        return {
            "items": sorted_items,
            "total": len(sorted_items)
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue items: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get queue items: {str(e)}")


@router.get("/image/{item_id}")
async def get_queue_item_image(item_id: int):
    """Get image for a queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get image path from queue
        result = supabase.table("ai_extraction_queue").select(
            "enhanced_image_path"
        ).eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        image_path = result.data[0].get('enhanced_image_path')
        if not image_path:
            raise HTTPException(status_code=404, detail="Image path not found")
        
        # Download from Supabase storage
        file_data = supabase.storage.from_("retail-captures").download(image_path)
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="image/jpeg",
            headers={"Cache-Control": "max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get image for item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get image: {str(e)}")


@router.post("/process/{item_id}")
async def start_processing(item_id: int, request_data: Dict[str, Any]):
    """Start processing a queue item with selected systems and model configuration"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Handle both old and new request formats (backwards compatible)
        system = request_data.get('system', 'custom_consensus')
        systems = request_data.get('systems', [])
        
        # If no systems array provided, use the single system
        if not systems and system:
            systems = [system]
        
        # Ensure we have at least one system
        if not systems:
            raise HTTPException(status_code=400, detail="At least one system must be selected")
        
        # Extract configuration data
        # First check if we have a complete extraction_config with field definitions
        extraction_config = request_data.get('extraction_config')
        if not extraction_config:
            # Try to load the last saved configuration from database
            try:
                # Get the most recent configuration that has proper field definitions
                config_result = supabase.table("ai_extraction_queue").select("extraction_config").not_.is_("extraction_config", "null").order("created_at", desc=True).limit(1).execute()
                
                if config_result.data and config_result.data[0].get('extraction_config'):
                    saved_config = config_result.data[0]['extraction_config']
                    # Validate that it has stages with fields
                    if saved_config.get('stages') and all(stage.get('fields') for stage in saved_config['stages'].values()):
                        extraction_config = saved_config
                        logger.info(f"Using last saved configuration with {len(saved_config['stages'])} stages", component="queue_api")
                    else:
                        raise HTTPException(status_code=400, detail="Last saved configuration has empty fields - please configure extraction fields first")
                else:
                    raise HTTPException(status_code=400, detail="No valid configuration found - please configure extraction fields first")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to load saved configuration: {e}", component="queue_api")
                raise HTTPException(status_code=400, detail="No valid configuration found - please configure extraction fields first")
        else:
            # Validate provided configuration has proper field definitions
            if not extraction_config.get('stages'):
                raise HTTPException(status_code=400, detail="Configuration must include stages with field definitions")
            
            # Check that stages have field definitions
            empty_stages = [stage_name for stage_name, stage_config in extraction_config['stages'].items() 
                          if not stage_config.get('fields')]
            if empty_stages:
                raise HTTPException(status_code=400, detail=f"Stages {empty_stages} have empty field definitions - configure fields first")
        
        # Log what we received
        logger.info(
            f"Processing item {item_id} with extraction config",
            component="queue_api",
            has_stages=bool(extraction_config.get('stages')),
            stages_list=list(extraction_config.get('stages', {}).keys()) if extraction_config.get('stages') else [],
            system=extraction_config.get('system', system)
        )
        
        # Generate comparison group ID
        import uuid
        comparison_group_id = str(uuid.uuid4())
        
        # Check if we have a complete configuration object
        if 'configuration' in request_data:
            # Use the complete configuration, ensuring temperature is 0.1
            model_config = request_data['configuration']
            if 'temperature' not in model_config:
                model_config['temperature'] = 0.1
        else:
            # Build configuration from both approaches
            model_config = {
                "system": system,
                "temperature": request_data.get('temperature', 0.1),  # Default to 0.1
                "max_budget": request_data.get('max_budget', 2.0),
                "orchestrator_model": request_data.get('orchestrator_model', 'claude-4-opus'),
                "orchestrator_prompt": request_data.get('orchestrator_prompt', ''),
                "orchestrators": request_data.get('orchestrators', {
                    "master": { "model": "claude-4-opus", "prompt": "" },
                    "extraction": { "model": "claude-4-sonnet", "prompt": "" },
                    "planogram": { "model": "gpt-4o-mini", "prompt": "" }
                }),
                "stage_models": request_data.get('stage_models', {}),
                "comparison_config": request_data.get('comparison_config', {
                    "model": configuration.get('comparison_model', 'gpt-4-vision-preview') if 'configuration' in locals() else "gpt-4-vision-preview",
                    "prompt": "",
                    "use_visual_comparison": True,
                    "abstraction_layers": []
                })
            }
        
        # Update queue item with both extraction_config and model_config for compatibility
        update_data = {
            "status": "processing",
            "selected_systems": systems,
            "comparison_group_id": comparison_group_id,
            "current_extraction_system": system,
            "started_at": datetime.utcnow().isoformat(),
            "processing_attempts": 1,
            "extraction_config": extraction_config,  # Keep for backward compatibility
            "model_config": model_config  # Store full model configuration
        }
        
        result = supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        logger.info(
            f"Started processing for item {item_id} with system {system}",
            component="queue_api",
            comparison_group_id=comparison_group_id,
            has_extraction_config=bool(extraction_config),
            extraction_config_stages=list(extraction_config.get('stages', {}).keys()) if extraction_config else [],
            model_config=model_config
        )
        
        # Log detailed extraction config info
        if extraction_config and extraction_config.get('stages'):
            for stage_name, stage_config in extraction_config['stages'].items():
                logger.info(
                    f"Stage {stage_name} configured",
                    component="queue_api",
                    queue_item_id=item_id,
                    has_prompt=bool(stage_config.get('prompt_text')),
                    prompt_length=len(stage_config.get('prompt_text', '')),
                    has_fields=bool(stage_config.get('fields'))
                )
        
        # Trigger actual processing via the queue-process API
        from fastapi import BackgroundTasks
        from ..api.queue_processing import run_extraction
        
        try:
            logger.info(f"Triggering extraction for queue item {item_id}", component="queue_api")
            
            # Get the queue item data
            queue_result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
            if not queue_result.data:
                logger.error(f"Queue item {item_id} not found", component="queue_api")
                return
                
            queue_item = queue_result.data[0]
            upload_id = queue_item.get("upload_id")
            
            if not upload_id:
                logger.error(f"No upload_id for queue item {item_id}", component="queue_api")
                return
            
            # Start the extraction in a background task
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Create a task to run the extraction
            task = loop.create_task(
                run_extraction(
                    item_id=item_id,
                    upload_id=upload_id,
                    system=system,
                    max_budget=model_config.get("max_budget", 2.0),
                    configuration=model_config
                )
            )
            
            logger.info(f"Extraction task created for item {item_id}", component="queue_api")
            
        except Exception as e:
            logger.error(f"Failed to trigger extraction: {e}", component="queue_api", exc_info=True)
        
        return {
            "success": True,
            "item_id": item_id,
            "comparison_group_id": comparison_group_id,
            "systems": systems,
            "extraction_config": extraction_config,
            "message": "Processing started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start processing for item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to start processing: {str(e)}")


@router.post("/reprocess/{item_id}")
async def reprocess_item(item_id: int):
    """Reprocess a completed queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current item data
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        item = result.data[0]
        
        if item['status'] not in ['completed', 'failed']:
            raise HTTPException(status_code=400, detail="Item must be completed or failed to reprocess")
        
        # Update for reprocessing
        update_data = {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "processing_attempts": (item.get('processing_attempts', 0) + 1)
        }
        
        result = supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        logger.info(f"Started reprocessing for item {item_id}", component="queue_api")
        
        return {
            "success": True,
            "item_id": item_id,
            "message": "Reprocessing started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to reprocess item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess: {str(e)}")


@router.post("/reset/{item_id}")
async def reset_item(item_id: int):
    """Reset a specific queue item (clear status and errors)"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current item data
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        # Reset item to clean state
        update_data = {
            "status": "pending",
            "extraction_result": None,
            "planogram_result": None,
            "final_accuracy": None,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "iterations_completed": None,
            "processing_duration_seconds": None,
            "api_cost": None,
            "human_review_required": False,
            "escalation_reason": None,
            "processing_attempts": 0
        }
        
        result = supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        logger.info(f"Reset queue item {item_id} to clean state", component="queue_api")
        
        return {
            "success": True,
            "item_id": item_id,
            "status": "pending",
            "message": "Item has been reset to pending status",
            "reset_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to reset item: {str(e)}")


@router.delete("/remove/{item_id}")
async def remove_item(item_id: int):
    """Remove a queue item completely"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current item data to verify it exists
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        item = result.data[0]
        
        # Delete the item from the queue
        delete_result = supabase.table("ai_extraction_queue").delete().eq("id", item_id).execute()
        
        logger.info(f"Removed queue item {item_id} from database", component="queue_api")
        
        return {
            "success": True,
            "item_id": item_id,
            "message": f"Item #{item_id} has been removed from the queue",
            "removed_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to remove item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to remove item: {str(e)}")


@router.post("/reset-all")
async def reset_all_items():
    """Reset ALL queue items to pending status"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all items regardless of status
        result = supabase.table("ai_extraction_queue").select("*").execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No items found in queue",
                "reset_count": 0
            }
        
        # Reset ALL items
        reset_data = {
            "status": "pending",
            "extraction_result": None,
            "planogram_result": None,
            "final_accuracy": None,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "iterations_completed": None,
            "processing_duration_seconds": None,
            "api_cost": None,
            "human_review_required": False,
            "escalation_reason": None,
            "processing_attempts": 0
        }
        
        reset_ids = [item["id"] for item in result.data]
        
        # Update all items
        for item_id in reset_ids:
            supabase.table("ai_extraction_queue").update(reset_data).eq("id", item_id).execute()
        
        logger.info(f"Reset {len(reset_ids)} items to pending", component="queue_api")
        
        return {
            "success": True,
            "message": f"Successfully reset {len(reset_ids)} items to pending",
            "reset_count": len(reset_ids),
            "reset_ids": reset_ids,
            "reset_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset all items: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to reset all items: {str(e)}")


@router.post("/reset-all-failed")
async def reset_all_failed_items():
    """Reset all failed and stuck items"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Find all failed and stuck (processing for too long) items
        result = supabase.table("ai_extraction_queue").select("*").in_(
            "status", ["failed", "processing"]
        ).execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No failed or stuck items found",
                "reset_count": 0
            }
        
        # Filter processing items that are truly stuck (processing for more than 1 hour)
        stuck_items = []
        current_time = datetime.utcnow()
        
        for item in result.data:
            if item["status"] == "failed":
                stuck_items.append(item)
            elif item["status"] == "processing" and item.get("started_at"):
                started_at = datetime.fromisoformat(item["started_at"].replace('Z', '+00:00'))
                if (current_time - started_at.replace(tzinfo=None)).total_seconds() > 3600:  # 1 hour
                    stuck_items.append(item)
        
        if not stuck_items:
            return {
                "success": True,
                "message": "No stuck items found (processing items are still within normal time)",
                "reset_count": 0
            }
        
        # Reset all stuck items
        reset_data = {
            "status": "pending",
            "extraction_result": None,
            "planogram_result": None,
            "final_accuracy": None,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "iterations_completed": None,
            "processing_duration_seconds": None,
            "api_cost": None,
            "human_review_required": False,
            "escalation_reason": None,
            "processing_attempts": 0
        }
        
        reset_ids = [item["id"] for item in stuck_items]
        
        # Update all stuck items
        for item_id in reset_ids:
            supabase.table("ai_extraction_queue").update(reset_data).eq("id", item_id).execute()
        
        logger.info(f"Reset {len(reset_ids)} failed/stuck items to pending", component="queue_api")
        
        return {
            "success": True,
            "message": f"Successfully reset {len(reset_ids)} failed/stuck items",
            "reset_count": len(reset_ids),
            "reset_ids": reset_ids,
            "reset_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset failed items: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to reset failed items: {str(e)}")


@router.get("/stats")
async def get_queue_stats():
    """Get queue statistics"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all items for stats
        result = supabase.table("ai_extraction_queue").select(
            "status, human_review_required"
        ).execute()
        
        if not result.data:
            return {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "needs_review": 0
            }
        
        items = result.data
        stats = {
            "total": len(items),
            "pending": len([i for i in items if i['status'] == 'pending']),
            "processing": len([i for i in items if i['status'] == 'processing']),
            "completed": len([i for i in items if i['status'] == 'completed']),
            "failed": len([i for i in items if i['status'] == 'failed']),
            "needs_review": len([i for i in items if i.get('human_review_required')])
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/systems")
async def get_available_systems():
    """Get list of available extraction systems"""
    
    return {
        "systems": [
            {
                "id": "custom_consensus",
                "name": "Custom Consensus",
                "description": "Direct API calls with weighted voting",
                "default": True
            },
            {
                "id": "langgraph",
                "name": "LangGraph",
                "description": "Professional workflow orchestration",
                "default": False
            },
            {
                "id": "hybrid",
                "name": "Hybrid",
                "description": "Combines both approaches",
                "default": False
            }
        ]
    }


@router.get("/comparison/{comparison_group_id}")
async def get_comparison_results(comparison_group_id: str):
    """Get comparison results for a group of extractions"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Query ai_extraction_queue table instead of extraction_results
        # since that's where the real data is stored
        result = supabase.table("ai_extraction_queue").select("*").eq(
            "comparison_group_id", comparison_group_id
        ).execute()
        
        if not result.data:
            return {"results": [], "comparison_group_id": comparison_group_id}
        
        # Transform the queue data into comparison results format
        comparison_results = []
        for item in result.data:
            comparison_results.append({
                "id": item["id"],
                "system_type": item.get("current_extraction_system", "unknown"),
                "overall_accuracy": item.get("final_accuracy"),
                "processing_time_seconds": item.get("processing_duration_seconds"),
                "total_cost": item.get("api_cost"),
                "iteration_count": item.get("iterations_completed"),
                "status": item["status"],
                "extraction_result": item.get("extraction_result"),
                "planogram_result": item.get("planogram_result"),
                "created_at": item["created_at"]
            })
        
        return {
            "results": comparison_results,
            "comparison_group_id": comparison_group_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get comparison results for {comparison_group_id}: {e}", component="queue_api")
        # Return empty results instead of error to avoid breaking the UI
        return {"results": [], "comparison_group_id": comparison_group_id}




@router.get("/stores")
async def get_stores():
    """Get unique stores from uploads metadata"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all uploads with metadata
        result = supabase.table("uploads").select("metadata").execute()
        
        stores = set()
        for item in result.data:
            if item.get('metadata'):
                store_name = item['metadata'].get('store_name') or item['metadata'].get('retailer')
                if store_name:
                    stores.add(store_name)
        
        # Sort and format for frontend
        store_list = [{"id": s, "name": s} for s in sorted(stores)]
        
        logger.info(f"Retrieved {len(store_list)} unique stores", component="queue_api")
        return store_list
        
    except Exception as e:
        logger.error(f"Failed to get stores: {e}", component="queue_api")
        return []  # Return empty instead of error to avoid breaking the UI


@router.get("/categories") 
async def get_categories():
    """Get unique categories from uploads"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all uploads with category
        result = supabase.table("uploads").select("category").execute()
        
        categories = set()
        for item in result.data:
            if item.get('category'):
                categories.add(item['category'])
        
        # Sort and format for frontend
        category_list = [{"id": c, "name": c} for c in sorted(categories)]
        
        logger.info(f"Retrieved {len(category_list)} unique categories", component="queue_api")
        return category_list
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}", component="queue_api")
        return []  # Return empty instead of error to avoid breaking the UI


@router.get("/countries")
async def get_countries():
    """Get unique countries from uploads metadata"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all uploads with metadata
        result = supabase.table("uploads").select("metadata").execute()
        
        countries = set()
        for item in result.data:
            if item.get('metadata') and item['metadata'].get('country'):
                countries.add(item['metadata']['country'])
        
        # Sort and format for frontend
        country_list = [{"id": c, "name": c} for c in sorted(countries)]
        
        logger.info(f"Retrieved {len(country_list)} unique countries", component="queue_api")
        return country_list
        
    except Exception as e:
        logger.error(f"Failed to get countries: {e}", component="queue_api")
        return []  # Return empty instead of error to avoid breaking the UI


@router.get("/cities")
async def get_cities():
    """Get unique cities from uploads metadata"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all uploads with metadata
        result = supabase.table("uploads").select("metadata").execute()
        
        cities = set()
        for item in result.data:
            if item.get('metadata') and item['metadata'].get('city'):
                cities.add(item['metadata']['city'])
        
        # Sort and format for frontend
        city_list = [{"id": c, "name": c} for c in sorted(cities)]
        
        logger.info(f"Retrieved {len(city_list)} unique cities", component="queue_api")
        return city_list
        
    except Exception as e:
        logger.error(f"Failed to get cities: {e}", component="queue_api")
        return []  # Return empty instead of error to avoid breaking the UI


@router.get("/analysis/{item_id}")
async def get_queue_item_analysis(item_id: int):
    """Get analysis data for a queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get item from queue
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        item = result.data[0]
        
        # Return analysis data based on extraction results
        analysis = {
            "item_id": item_id,
            "status": item["status"],
            "accuracy": item.get("final_accuracy"),
            "processing_time": item.get("processing_duration_seconds"),
            "iterations": item.get("iterations_completed"),
            "cost": item.get("api_cost"),
            "extraction_summary": item.get("extraction_result"),
            "planogram_summary": item.get("planogram_result")
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to get analysis for item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.post("/batch-configure")
async def batch_configure_items(request_data: Dict[str, Any]):
    """Apply extraction configuration to multiple queue items"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        item_ids = request_data.get('item_ids', [])
        extraction_config = request_data.get('extraction_config', {})
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="item_ids is required")
        
        if not extraction_config:
            raise HTTPException(status_code=400, detail="extraction_config is required")
        
        # Extract system and validate
        system = extraction_config.get('system', 'custom_consensus')
        models = extraction_config.get('models', {})
        prompts = extraction_config.get('prompts', {})
        reasoning = extraction_config.get('reasoning', {})
        
        # Build stages with prompt texts if not present
        if 'stages' not in extraction_config:
            stages = {}
            
            # Load prompts from database for each stage type
            prompt_types = ['structure', 'products', 'details', 'visual']
            for prompt_type in prompt_types:
                # Get prompt from database
                try:
                    result = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type).eq("is_active", True).limit(1).execute()
                    
                    if result.data:
                        prompt_data = result.data[0]
                        stages[prompt_type] = {
                            "prompt_text": prompt_data.get('prompt_text', f"Extract {prompt_type} from the image"),
                            "fields": prompt_data.get('extraction_fields', [])
                        }
                    else:
                        # Fallback defaults
                        if prompt_type == 'structure':
                            stages[prompt_type] = {
                                "prompt_text": "Extract the shelf structure from this retail shelf image. Identify shelf levels and sections.",
                                "fields": []
                            }
                        elif prompt_type == 'products':
                            stages[prompt_type] = {
                                "prompt_text": "Extract all products from this retail shelf image. Include brand, name, price, and position.",
                                "fields": []
                            }
                        elif prompt_type == 'visual':
                            stages[prompt_type] = {
                                "prompt_text": "Compare the extracted data with the original image to verify accuracy.",
                                "fields": []
                            }
                except Exception as e:
                    logger.warning(f"Failed to load prompt for {prompt_type}: {e}")
                    # Use minimal defaults
                    stages[prompt_type] = {
                        "prompt_text": f"Extract {prompt_type} information from the retail shelf image.",
                        "fields": []
                    }
            
            extraction_config['stages'] = stages
        
        # Validate system
        valid_systems = ['custom_consensus', 'langgraph', 'hybrid']
        if system not in valid_systems:
            raise HTTPException(status_code=400, detail=f"Invalid system. Must be one of: {valid_systems}")
        
        # Update all specified items
        updated_items = []
        failed_items = []
        
        for item_id in item_ids:
            try:
                # First check if extraction_config column exists by trying to update
                update_data = {
                    "current_extraction_system": system,
                    "status": "configured",
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Try to add extraction_config if the column exists
                try:
                    result = supabase.table("ai_extraction_queue").update({
                        **update_data,
                        "extraction_config": extraction_config
                    }).eq("id", item_id).execute()
                except Exception as e:
                    # If extraction_config column doesn't exist, use other columns
                    logger.warning(f"extraction_config column may not exist, using fallback: {e}")
                    result = supabase.table("ai_extraction_queue").update({
                        **update_data,
                        "prompt_overrides": prompts,
                        "enhanced_config": {
                            "system": system,
                            "models": models,
                            "prompts": prompts,
                            "reasoning": reasoning,
                            "applied_at": datetime.utcnow().isoformat()
                        }
                    }).eq("id", item_id).execute()
                
                if result.data:
                    updated_items.append(item_id)
                else:
                    failed_items.append({"id": item_id, "error": "Update failed"})
                    
            except Exception as e:
                logger.warning(f"Failed to update item {item_id}: {e}")
                failed_items.append({"id": item_id, "error": str(e)})
        
        logger.info(f"Applied batch configuration to {len(updated_items)} items", 
                   component="queue_api", 
                   system=system, 
                   item_count=len(updated_items))
        
        return {
            "success": True,
            "updated_count": len(updated_items),
            "updated_items": updated_items,
            "failed_items": failed_items,
            "configuration": extraction_config,
            "message": f"Configuration applied to {len(updated_items)} items"
        }
        
    except Exception as e:
        logger.error(f"Failed to batch configure items: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to batch configure: {str(e)}")


@router.post("/batch-reset")
async def batch_reset_items(request_data: Dict[str, Any]):
    """Reset queue items to default configuration"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        item_ids = request_data.get('item_ids', [])
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="item_ids is required")
        
        # Reset configuration for all specified items using existing schema
        reset_items = []
        for item_id in item_ids:
            try:
                result = supabase.table("ai_extraction_queue").update({
                    "current_extraction_system": "custom_consensus",  # Reset to default
                    "status": "pending"  # Reset to pending
                }).eq("id", item_id).execute()
                
                if result.data:
                    reset_items.append(item_id)
                    
            except Exception as e:
                logger.warning(f"Failed to reset item {item_id}: {e}")
        
        logger.info(f"Reset configuration for {len(reset_items)} items", 
                   component="queue_api", 
                   item_count=len(reset_items))
        
        return {
            "success": True,
            "reset_items": reset_items,
            "failed_items": [id for id in item_ids if id not in reset_items],
            "message": f"Configuration reset for {len(reset_items)} items"
        }
        
    except Exception as e:
        logger.error(f"Failed to batch reset items: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to batch reset: {str(e)}")


@router.get("/flow/{item_id}")
async def get_queue_item_flow(item_id: int):
    """Get processing flow data for a queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get item from queue
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        item = result.data[0]
        
        # Create flow data based on item status and timestamps
        flow_steps = []
        
        if item.get("created_at"):
            flow_steps.append({
                "step": "queued",
                "timestamp": item["created_at"],
                "status": "completed"
            })
        
        if item.get("started_at"):
            flow_steps.append({
                "step": "processing_started",
                "timestamp": item["started_at"],
                "status": "completed"
            })
        
        if item["status"] == "processing":
            flow_steps.append({
                "step": "extraction_in_progress",
                "timestamp": item.get("started_at"),
                "status": "in_progress"
            })
        elif item["status"] == "completed":
            flow_steps.append({
                "step": "extraction_completed",
                "timestamp": item.get("completed_at"),
                "status": "completed"
            })
            flow_steps.append({
                "step": "planogram_generated",
                "timestamp": item.get("completed_at"),
                "status": "completed"
            })
        elif item["status"] == "failed":
            flow_steps.append({
                "step": "extraction_failed",
                "timestamp": item.get("failed_at"),
                "status": "failed",
                "error": item.get("error_message")
            })
        
        flow = {
            "item_id": item_id,
            "current_status": item["status"],
            "steps": flow_steps,
            "processing_attempts": item.get("processing_attempts", 0)
        }
        
        return flow
        
    except Exception as e:
        logger.error(f"Failed to get flow for item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get flow: {str(e)}")


@router.post("/approve/{upload_id}")
async def approve_upload_for_processing(upload_id: str):
    """Mark upload as completed to trigger automatic queue entry creation"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Check if upload exists
        upload_result = supabase.table("uploads").select("*").eq("id", upload_id).execute()
        
        if not upload_result.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = upload_result.data[0]
        current_status = upload.get("status")
        
        # Check if already completed
        if current_status == "completed":
            # Check if already queued
            existing = supabase.table("ai_extraction_queue").select("id").eq("upload_id", upload_id).execute()
            
            if existing.data:
                return {
                    "message": "Already approved and queued",
                    "queue_id": existing.data[0]["id"],
                    "status": "existing",
                    "upload_status": current_status
                }
            else:
                return {
                    "message": "Already approved, queue entry may be pending",
                    "status": "completed",
                    "upload_status": current_status
                }
        
        # Mark upload as completed - this will trigger the database trigger
        update_result = supabase.table("uploads").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", upload_id).execute()
        
        if update_result.data:
            logger.info(f"Approved upload (marked as completed): {upload_id}", component="queue_api")
            
            # Wait a moment for trigger to fire
            await asyncio.sleep(0.5)
            
            # Check if queue entry was created
            queue_check = supabase.table("ai_extraction_queue").select("id").eq("upload_id", upload_id).execute()
            
            if queue_check.data:
                return {
                    "message": "Upload approved and queued for extraction",
                    "queue_id": queue_check.data[0]["id"],
                    "status": "created",
                    "upload_status": "completed"
                }
            else:
                return {
                    "message": "Upload approved, queue entry creation pending",
                    "status": "completed",
                    "upload_status": "completed"
                }
        else:
            raise HTTPException(status_code=500, detail="Failed to approve upload")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve upload {upload_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to approve upload: {str(e)}")


@router.get("/logs")
async def get_logs():
    """Get logs for the system"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get logs from Supabase storage
        result = supabase.storage.from_("system-logs").list()
        
        if not result.data:
            return {"logs": []}
        
        logs = []
        for item in result.data:
            logs.append({
                "name": item["name"],
                "last_modified": item["last_modified"]
            })
        
        return {"logs": logs}
        
    except Exception as e:
        logger.error(f"Failed to get logs: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/error-summary")
async def get_error_summary():
    """Get error summary for the system"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get error summary from Supabase storage
        result = supabase.storage.from_("system-error-summary").list()
        
        if not result.data:
            return {"error_summary": []}
        
        error_summary = []
        for item in result.data:
            error_summary.append({
                "name": item["name"],
                "last_modified": item["last_modified"]
            })
        
        return {"error_summary": error_summary}
        
    except Exception as e:
        logger.error(f"Failed to get error summary: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get error summary: {str(e)}")





@router.post("/batch/process")
async def batch_process_items(request: Dict[str, Any]):
    """Process multiple queue items with specified system and prompts"""
    
    try:
        item_ids = request.get("item_ids", [])
        system_type = request.get("system_type", "custom")
        prompt_overrides = request.get("prompt_overrides", {})
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="item_ids is required")
        
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Validate system type
        from ..systems.base_system import ExtractionSystemFactory
        if system_type not in ExtractionSystemFactory.AVAILABLE_SYSTEMS:
            raise HTTPException(status_code=400, detail=f"Invalid system_type: {system_type}")
        
        results = []
        
        for item_id in item_ids:
            try:
                # Get queue item
                result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
                
                if not result.data:
                    results.append({
                        "item_id": item_id,
                        "success": False,
                        "error": "Queue item not found"
                    })
                    continue
                
                item = result.data[0]
                
                # Update item status to processing
                supabase.table("ai_extraction_queue").update({
                    "status": "processing",
                    "system_type": system_type,
                    "prompt_overrides": prompt_overrides,
                    "started_at": datetime.utcnow().isoformat()
                }).eq("id", item_id).execute()
                
                results.append({
                    "item_id": item_id,
                    "success": True,
                    "message": f"Started processing with {system_type} system",
                    "system_type": system_type
                })
                
                logger.info(f"Started batch processing item {item_id} with {system_type}")
                
            except Exception as e:
                results.append({
                    "item_id": item_id,
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"Failed to process item {item_id}: {e}")
        
        return {
            "success": True,
            "processed_count": len([r for r in results if r["success"]]),
            "failed_count": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to batch process items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch process items: {str(e)}")


@router.post("/batch/configure")
async def batch_configure_items(request: Dict[str, Any]):
    """Apply configuration to multiple queue items"""
    
    try:
        item_ids = request.get("item_ids", [])
        system_type = request.get("system_type")
        prompt_overrides = request.get("prompt_overrides", {})
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="item_ids is required")
        
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Update all selected items
        update_data = {}
        if system_type:
            update_data["system_type"] = system_type
        if prompt_overrides:
            update_data["prompt_overrides"] = prompt_overrides
        
        if update_data:
            for item_id in item_ids:
                supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        logger.info(f"Applied configuration to {len(item_ids)} items")
        
        return {
            "success": True,
            "message": f"Applied configuration to {len(item_ids)} items",
            "updated_count": len(item_ids)
        }
        
    except Exception as e:
        logger.error(f"Failed to configure items: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure items: {str(e)}")


@router.get("/logs/errors")
async def get_recent_errors(limit: int = Query(5, ge=1, le=50)):
    """Get recent errors across all extractions"""
    
    try:
        # Read recent log files
        logs_dir = "logs"
        log_files = []
        
        # Get log files from the last 24 hours
        now = datetime.now()
        for hours_back in range(25):  # 24 hours + current hour
            date = now - timedelta(hours=hours_back)
            log_file = f"{logs_dir}/onshelf_ai_{date.strftime('%Y%m%d')}.log"
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        errors = []
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            # Try to parse as JSON first
                            log_entry = json.loads(line)
                            timestamp = log_entry.get("timestamp", "")
                            log_level = log_entry.get("level", "INFO")
                            log_component = log_entry.get("component", "unknown")
                            message = log_entry.get("message", "")
                            
                        except json.JSONDecodeError:
                            # Parse structured log format
                            parts = line.split(" | ")
                            if len(parts) >= 4:
                                timestamp = parts[0]
                                log_level = parts[1]
                                log_component = parts[2]
                                message = " | ".join(parts[3:])
                            else:
                                continue
                        
                        # Only include ERROR and WARNING levels
                        if log_level not in ["ERROR", "WARNING"]:
                            continue
                        
                        # Parse timestamp for sorting
                        try:
                            if ":" in timestamp and len(timestamp.split(":")) >= 2:
                                log_time = datetime.strptime(timestamp, "%H:%M:%S").time()
                                log_datetime = datetime.combine(datetime.now().date(), log_time)
                            else:
                                log_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            log_datetime = datetime.now()
                        
                        errors.append({
                            "timestamp": timestamp,
                            "level": log_level,
                            "component": log_component,
                            "message": message,
                            "datetime": log_datetime
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to read log file {log_file}: {e}")
                continue
        
        # Sort by timestamp (newest first) and limit
        errors.sort(key=lambda x: x["datetime"], reverse=True)
        errors = errors[:limit]
        
        # Remove datetime field before returning
        for error in errors:
            del error["datetime"]
        
        return {
            "errors": errors,
            "total_found": len(errors)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent errors: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get recent errors: {str(e)}")


@router.get("/logs/{item_id}")
async def get_extraction_logs(
    item_id: int, 
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, description="Filter by log level: ERROR, WARNING, INFO, DEBUG"),
    component: Optional[str] = Query(None, description="Filter by component"),
    search: Optional[str] = Query(None, description="Search in log messages"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
):
    """Get extraction logs for a specific queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get queue item to find agent_id
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        item = result.data[0]
        agent_id = item.get("agent_id")
        upload_id = item.get("upload_id")
        ready_media_id = item.get("ready_media_id")
        
        # Read log files from the logs directory
        logs_dir = "logs"
        log_files = []
        
        # Get log files from the last N hours
        now = datetime.now()
        for hours_back in range(hours + 1):
            date = now - timedelta(hours=hours_back)
            log_file = f"{logs_dir}/onshelf_ai_{date.strftime('%Y%m%d')}.log"
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        # Parse logs and filter
        filtered_logs = []
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            # Try to parse as JSON first
                            log_entry = json.loads(line)
                            timestamp = log_entry.get("timestamp", "")
                            log_level = log_entry.get("level", "INFO")
                            log_component = log_entry.get("component", "unknown")
                            message = log_entry.get("message", "")
                            
                        except json.JSONDecodeError:
                            # Parse structured log format: TIMESTAMP | LEVEL | COMPONENT | MESSAGE
                            parts = line.split(" | ")
                            if len(parts) >= 4:
                                timestamp = parts[0]
                                log_level = parts[1]
                                log_component = parts[2]
                                message = " | ".join(parts[3:])
                            else:
                                # Fallback for unstructured logs
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                log_level = "INFO"
                                log_component = "unknown"
                                message = line
                        
                        # Filter by agent_id, upload_id, or ready_media_id
                        if agent_id and agent_id not in message:
                            if upload_id and upload_id not in message:
                                if ready_media_id and ready_media_id not in message:
                                    continue
                        
                        # Apply filters
                        if level and log_level != level:
                            continue
                        
                        if component and log_component != component:
                            continue
                        
                        if search and search.lower() not in message.lower():
                            continue
                        
                        # Parse timestamp for sorting
                        try:
                            if ":" in timestamp and len(timestamp.split(":")) >= 2:
                                log_time = datetime.strptime(timestamp, "%H:%M:%S").time()
                                log_datetime = datetime.combine(date.date(), log_time)
                            else:
                                log_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        except:
                            log_datetime = datetime.now()
                        
                        filtered_logs.append({
                            "timestamp": timestamp,
                            "level": log_level,
                            "component": log_component,
                            "message": message,
                            "datetime": log_datetime,
                            "item_id": item_id
                        })
                        
            except Exception as e:
                logger.warning(f"Failed to read log file {log_file}: {e}")
                continue
        
        # Sort by timestamp (newest first) and limit
        filtered_logs.sort(key=lambda x: x["datetime"], reverse=True)
        filtered_logs = filtered_logs[:limit]
        
        # Remove datetime field before returning
        for log in filtered_logs:
            del log["datetime"]
        
        return {
            "logs": filtered_logs,
            "item_id": item_id,
            "total_found": len(filtered_logs),
            "filters_applied": {
                "level": level,
                "component": component,
                "search": search,
                "hours": hours
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs for item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/results/{item_id}")
async def get_queue_item_results(item_id: int):
    """Get extraction and planogram results for a queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get queue item with all result data
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        item = result.data[0]
        
        # Get upload data to extract store name from metadata
        upload_data = None
        store_name = "Unknown Store"
        category = "Unknown Category"
        
        if item.get('upload_id'):
            upload_result = supabase.table("uploads").select(
                "category, metadata, created_at"
            ).eq("id", item['upload_id']).execute()
            
            if upload_result.data and len(upload_result.data) > 0:
                upload_data = upload_result.data[0]
                category = upload_data.get('category', 'Unknown Category')
                
                # Extract store name from metadata JSON field
                metadata = upload_data.get('metadata', {})
                if isinstance(metadata, dict):
                    store_name = metadata.get('store_name', metadata.get('retailer', 'Unknown Store'))
        
        # Parse extraction results to extract products
        products = []
        total_products = 0
        iterations_data = []
        
        extraction_result = item.get("extraction_result")
        if extraction_result and isinstance(extraction_result, dict):
            # Check if we have stages with products
            if "stages" in extraction_result:
                stages = extraction_result.get("stages", {})
                # Look for products in different possible locations
                if "products" in stages and isinstance(stages["products"], dict):
                    products_data = stages["products"].get("data", [])
                    if isinstance(products_data, list):
                        products = products_data
                elif "product_v1" in stages and isinstance(stages["product_v1"], dict):
                    products_data = stages["product_v1"].get("data", [])
                    if isinstance(products_data, list):
                        products = products_data
                # Also check for products at root level
            elif "products" in extraction_result:
                if isinstance(extraction_result["products"], list):
                    products = extraction_result["products"]
            
            # Extract iterations data if available
            if "iterations" in extraction_result:
                iterations_data = extraction_result.get("iterations", [])
        
        total_products = len(products)
        
        # Parse planogram result to get SVG
        planogram_svg = None
        planogram_result = item.get("planogram_result")
        if planogram_result and isinstance(planogram_result, dict):
            planogram_svg = planogram_result.get("svg") or planogram_result.get("planogram_svg")
        
        # Get image URL
        image_url = None
        if item.get("enhanced_image_path"):
            # Build the image URL using the queue image endpoint
            image_url = f"/api/queue/image/{item['id']}"
        
        # Format completed time
        completed_time = None
        if item.get("completed_at"):
            try:
                completed_dt = datetime.fromisoformat(item["completed_at"].replace('Z', '+00:00'))
                completed_time = completed_dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                completed_time = item.get("completed_at")
        
        # Build the response matching what the Results page expects
        response = {
            "id": item["id"],
            "item_id": item["id"],  # Some parts of frontend use item_id
            "upload_id": item.get("upload_id"),
            "ready_media_id": item.get("ready_media_id"),
            "enhanced_image_path": item.get("enhanced_image_path"),
            "status": item.get("status"),
            "store_name": store_name,
            "category": category,
            "created_at": item.get("created_at"),
            "completed_at": item.get("completed_at"),
            "completed_time": completed_time,
            "processing_duration_seconds": item.get("processing_duration_seconds"),
            "api_cost": item.get("api_cost"),
            "iterations_completed": item.get("iterations_completed"),
            "final_accuracy": item.get("final_accuracy"),
            "human_review_required": item.get("human_review_required"),
            "escalation_reason": item.get("escalation_reason"),
            "selected_systems": item.get("selected_systems", []),
            "current_extraction_system": item.get("current_extraction_system"),
            "comparison_group_id": item.get("comparison_group_id"),
            
            # Parsed results for frontend
            "products": products,
            "total_products": total_products,
            "iterations_data": iterations_data,
            "planogram_svg": planogram_svg,
            "original_image_url": image_url,
            
            # Keep raw results for debugging
            "extraction_result": item.get("extraction_result"),
            "planogram_result": item.get("planogram_result"),
            
            # Additional metadata
            "error_message": item.get("error_message"),
            "processing_attempts": item.get("processing_attempts", 0),
            "upload_created_at": upload_data.get("created_at") if upload_data else None
        }
        
        logger.info(f"Retrieved results for queue item {item_id}", component="queue_api", 
                   status=item.get("status"), has_extraction=bool(item.get("extraction_result")), 
                   has_planogram=bool(item.get("planogram_result")))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for item {item_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.post("/batch-configure-enhanced")
async def batch_configure_enhanced(request: Dict[str, Any]):
    """Apply enhanced configuration to multiple queue items"""
    
    try:
        item_ids = request.get("item_ids", [])
        configuration = request.get("configuration", {})
        reasoning = request.get("reasoning", "Manual configuration via enhanced UI")
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="item_ids is required")
        
        if not configuration:
            raise HTTPException(status_code=400, detail="configuration is required")
        
        if not supabase:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Validate configuration structure
        system_type = configuration.get("system")
        models = configuration.get("models", {})
        prompts = configuration.get("prompts", {})
        
        if not system_type:
            raise HTTPException(status_code=400, detail="configuration.system is required")
        
        # Validate system type
        from ..systems.base_system import ExtractionSystemFactory
        if system_type not in ExtractionSystemFactory.AVAILABLE_SYSTEMS:
            raise HTTPException(status_code=400, detail=f"Invalid system_type: {system_type}")
        
        updated_items = []
        failed_items = []
        
        for item_id in item_ids:
            try:
                # Get current item
                result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
                
                if not result.data:
                    failed_items.append({
                        "item_id": item_id,
                        "error": "Queue item not found"
                    })
                    continue
                
                item = result.data[0]
                
                # Prepare enhanced configuration data
                enhanced_config = {
                    "system_type": system_type,
                    "model_assignments": models,
                    "prompt_assignments": prompts,
                    "configuration_reasoning": reasoning,
                    "configured_at": datetime.utcnow().isoformat(),
                    "configured_via": "enhanced_ui"
                }
                
                # Update the item with enhanced configuration
                update_result = supabase.table("ai_extraction_queue").update({
                    "system_type": system_type,
                    "enhanced_config": enhanced_config,
                    "prompt_overrides": prompts,  # Keep backward compatibility
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", item_id).execute()
                
                if update_result.data:
                    updated_items.append({
                        "item_id": item_id,
                        "system_type": system_type,
                        "models": models,
                        "prompts": prompts
                    })
                    logger.info(f"Applied enhanced configuration to item {item_id}: {system_type}")
                else:
                    failed_items.append({
                        "item_id": item_id,
                        "error": "Failed to update item"
                    })
                
            except Exception as e:
                failed_items.append({
                    "item_id": item_id,
                    "error": str(e)
                })
                logger.error(f"Failed to configure item {item_id}: {e}")
        
        return {
            "success": True,
            "message": f"Enhanced configuration applied to {len(updated_items)} items",
            "updated_items": updated_items,
            "failed_items": failed_items,
            "configuration": {
                "system": system_type,
                "models": models,
                "prompts": prompts,
                "reasoning": reasoning
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to apply enhanced configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply enhanced configuration: {str(e)}") 