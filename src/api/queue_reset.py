"""
API endpoint for resetting queue items
"""

from fastapi import APIRouter, HTTPException
from supabase import create_client
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Supabase client will be initialized on demand
def get_supabase_client():
    """Get Supabase client instance"""
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )

@router.post("/queue/reset-all")
async def reset_all_queue_items():
    """Reset all failed and completed queue items to pending status"""
    try:
        supabase = get_supabase_client()
        reset_count = 0
        
        # Reset failed items
        failed_result = supabase.table("ai_extraction_queue") \
            .update({
                "status": "pending",
                "processing_started_at": None,
                "processing_completed_at": None,
                "error_message": None,
                "retry_count": 0,
                "extraction_results": None
            }) \
            .eq("status", "failed") \
            .execute()
        
        reset_count += len(failed_result.data)
        
        # Reset processing items (stuck)
        processing_result = supabase.table("ai_extraction_queue") \
            .update({
                "status": "pending",
                "processing_started_at": None,
                "processing_completed_at": None,
                "error_message": None,
                "retry_count": 0
            }) \
            .eq("status", "processing") \
            .execute()
        
        reset_count += len(processing_result.data)
        
        # Reset completed items
        completed_result = supabase.table("ai_extraction_queue") \
            .update({
                "status": "pending",
                "processing_started_at": None,
                "processing_completed_at": None,
                "extraction_results": None,
                "retry_count": 0
            }) \
            .eq("status", "completed") \
            .execute()
        
        reset_count += len(completed_result.data)
        
        logger.info(f"Reset {reset_count} queue items to pending status")
        
        return {
            "success": True,
            "reset_count": reset_count,
            "message": f"Successfully reset {reset_count} items to pending status"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset queue items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/queue/add-approved-media")
async def add_approved_media_to_queue():
    """Add all approved media files to the extraction queue"""
    try:
        supabase = get_supabase_client()
        # Get all approved media files with their upload_ids
        approved_media = supabase.table("media_files") \
            .select("media_id, upload_id, file_path, approval_status") \
            .eq("approval_status", "approved") \
            .not_.is_("upload_id", "null") \
            .not_.is_("file_path", "null") \
            .execute()
        
        # Group by upload_id
        uploads_to_queue = {}
        for media in approved_media.data:
            upload_id = media['upload_id']
            if upload_id not in uploads_to_queue:
                uploads_to_queue[upload_id] = {
                    'media_id': media['media_id'],
                    'file_path': media['file_path']
                }
        
        # Get existing queue items
        existing_queue = supabase.table("ai_extraction_queue") \
            .select("upload_id") \
            .execute()
        
        existing_upload_ids = {item['upload_id'] for item in existing_queue.data}
        
        # Add missing items
        added_count = 0
        for upload_id, media_info in uploads_to_queue.items():
            if upload_id not in existing_upload_ids:
                try:
                    # Get a sample configuration
                    config_result = supabase.table("ai_extraction_queue") \
                        .select("model_config") \
                        .not_.is_("model_config", "null") \
                        .limit(1) \
                        .execute()
                    
                    default_config = None
                    if config_result.data and config_result.data[0].get('model_config'):
                        default_config = config_result.data[0]['model_config']
                    
                    # Insert into queue
                    result = supabase.table("ai_extraction_queue") \
                        .insert({
                            "upload_id": upload_id,
                            "status": "pending",
                            "ready_media_id": media_info['media_id'],
                            "enhanced_image_path": media_info['file_path'],
                            "current_extraction_system": "custom_consensus",
                            "processing_attempts": 0,
                            "created_at": datetime.utcnow().isoformat(),
                            "model_config": default_config
                        }) \
                        .execute()
                    
                    if result.data:
                        added_count += 1
                        
                except Exception as e:
                    logger.error(f"Failed to add upload {upload_id}: {e}")
        
        return {
            "success": True,
            "total_approved": len(uploads_to_queue),
            "already_in_queue": len(existing_upload_ids),
            "newly_added": added_count,
            "message": f"Added {added_count} approved items to queue"
        }
        
    except Exception as e:
        logger.error(f"Failed to add approved media to queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))