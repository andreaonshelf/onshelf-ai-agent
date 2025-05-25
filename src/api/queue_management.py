"""
Queue Management API
Provides endpoints for managing the extraction queue and system selection
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import io
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
        # Query ai_extraction_queue with proper prioritization
        query = supabase.table("ai_extraction_queue").select("""
            id,
            ready_media_id,
            enhanced_image_path,
            status,
            human_review_required,
            final_accuracy,
            selected_systems,
            comparison_group_id,
            current_extraction_system,
            processing_attempts,
            created_at,
            started_at,
            completed_at,
            iterations_completed,
            api_cost
        """)
        
        # Apply status filter
        if status:
            if status == 'review':
                query = query.eq("human_review_required", True)
            else:
                query = query.eq("status", status)
        else:
            # Default: show all relevant statuses
            query = query.in_("status", ["pending", "processing", "completed", "failed"])
        
        # Apply system filter
        if system:
            query = query.contains("selected_systems", [system])
        
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
    """Start processing a queue item with selected systems"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        systems = request_data.get('systems', [])
        if not systems:
            raise HTTPException(status_code=400, detail="At least one system must be selected")
        
        # Validate systems
        valid_systems = ['custom_consensus', 'langgraph', 'hybrid']
        invalid_systems = [s for s in systems if s not in valid_systems]
        if invalid_systems:
            raise HTTPException(status_code=400, detail=f"Invalid systems: {invalid_systems}")
        
        # Generate comparison group ID
        import uuid
        comparison_group_id = str(uuid.uuid4())
        
        # Update queue item
        update_data = {
            "status": "processing",
            "selected_systems": systems,
            "comparison_group_id": comparison_group_id,
            "current_extraction_system": systems[0],  # Start with first system
            "started_at": datetime.utcnow().isoformat(),
            "processing_attempts": 1
        }
        
        result = supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        logger.info(
            f"Started processing for item {item_id} with systems {systems}",
            component="queue_api",
            comparison_group_id=comparison_group_id
        )
        
        # TODO: Trigger actual processing pipeline here
        # For now, we'll simulate processing by updating status after a delay
        
        return {
            "success": True,
            "item_id": item_id,
            "comparison_group_id": comparison_group_id,
            "systems": systems,
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
        # Get results from extraction_results table
        result = supabase.table("extraction_results").select("*").eq(
            "comparison_group_id", comparison_group_id
        ).execute()
        
        if not result.data:
            return {"results": [], "comparison_group_id": comparison_group_id}
        
        return {
            "results": result.data,
            "comparison_group_id": comparison_group_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get comparison results for {comparison_group_id}: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to get comparison results: {str(e)}")


@router.post("/reset-fake-completed")
async def reset_fake_completed_items():
    """Reset items that are marked completed but have no extraction results"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Find items that are "completed" but have no real results
        result = supabase.table("ai_extraction_queue").select("*").eq("status", "completed").execute()
        
        if not result.data:
            return {"message": "No completed items found", "reset_count": 0}
        
        # Filter items that have null extraction results (fake completed)
        fake_completed = [
            item for item in result.data 
            if not item.get('extraction_result') or not item.get('planogram_result')
        ]
        
        if not fake_completed:
            return {"message": "All completed items have valid results", "reset_count": 0}
        
        # Reset fake completed items to pending
        reset_ids = [item['id'] for item in fake_completed]
        
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
            "escalation_reason": None
        }
        
        # Update all fake completed items
        for item_id in reset_ids:
            supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        logger.info(f"Reset {len(reset_ids)} fake completed items to pending", component="queue_api")
        
        return {
            "message": f"Successfully reset {len(reset_ids)} items to pending status",
            "reset_count": len(reset_ids),
            "reset_ids": reset_ids
        }
        
    except Exception as e:
        logger.error(f"Failed to reset fake completed items: {e}", component="queue_api")
        raise HTTPException(status_code=500, detail=f"Failed to reset items: {str(e)}") 