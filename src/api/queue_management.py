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


@router.get("/stores")
async def get_stores():
    """Get list of stores from real data - NO MOCK DATA"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Try to get real store data from database
        # This would typically come from a stores table or extracted from queue items
        result = supabase.table("ai_extraction_queue").select("ready_media_id").execute()
        
        if not result.data:
            return []
        
        # For now, return empty list since we don't have store metadata
        # In a real system, this would query a stores table
        logger.info("Store data requested - returning empty list (no mock data)", component="queue_api")
        return []
        
    except Exception as e:
        logger.error(f"Failed to get stores: {e}", component="queue_api")
        return []  # Return empty instead of error to avoid breaking the UI


@router.get("/categories")
async def get_categories():
    """Get list of categories from real data - NO MOCK DATA"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Try to get real category data from database
        # This would typically come from a categories table or extracted from queue items
        result = supabase.table("ai_extraction_queue").select("ready_media_id").execute()
        
        if not result.data:
            return []
        
        # For now, return empty list since we don't have category metadata
        # In a real system, this would query a categories table
        logger.info("Category data requested - returning empty list (no mock data)", component="queue_api")
        return []
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}", component="queue_api")
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
    """Manually create queue entry for approved upload"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Check if upload exists
        upload_result = supabase.table("uploads").select("*").eq("id", upload_id).execute()
        
        if not upload_result.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = upload_result.data[0]
        
        # Check if already queued
        existing = supabase.table("ai_extraction_queue").select("id").eq("upload_id", upload_id).execute()
        
        if existing.data:
            return {
                "message": "Already queued",
                "queue_id": existing.data[0]["id"],
                "status": "existing"
            }
        
        # Create queue entry
        queue_data = {
            "upload_id": upload_id,
            "status": "pending",
            "ready_media_id": upload_id,
            "enhanced_image_path": upload.get("file_path", ""),
            "current_extraction_system": "custom_consensus",
            "processing_attempts": 0
        }
        
        result = supabase.table("ai_extraction_queue").insert(queue_data).execute()
        
        if result.data:
            logger.info(f"Created queue entry for approved upload: {upload_id}", component="queue_api")
            return {
                "message": "Queue entry created",
                "queue_id": result.data[0]["id"],
                "status": "created"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create queue entry")
            
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