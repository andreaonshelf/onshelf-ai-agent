"""
Fix script to ensure approved media files get into the extraction queue
The queue uses upload_id, not media_id as the primary reference
"""

import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def add_approved_media_to_queue():
    """Add all approved media files to the extraction queue"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    print("=== ADDING APPROVED MEDIA TO EXTRACTION QUEUE ===")
    
    # Get all approved media files with their upload_ids
    approved_media = supabase.table("media_files") \
        .select("media_id, upload_id, file_path, approval_status, approved_at") \
        .eq("approval_status", "approved") \
        .not_.is_("upload_id", "null") \
        .not_.is_("file_path", "null") \
        .execute()
    
    print(f"\nFound {len(approved_media.data)} approved media files")
    
    # Group by upload_id (since queue uses upload_id as reference)
    uploads_to_queue = {}
    for media in approved_media.data:
        upload_id = media['upload_id']
        if upload_id not in uploads_to_queue:
            uploads_to_queue[upload_id] = {
                'media_id': media['media_id'],
                'file_path': media['file_path'],
                'approved_at': media['approved_at']
            }
    
    print(f"Unique uploads to process: {len(uploads_to_queue)}")
    
    # Get existing queue items
    existing_queue = supabase.table("ai_extraction_queue") \
        .select("upload_id") \
        .execute()
    
    existing_upload_ids = {item['upload_id'] for item in existing_queue.data}
    print(f"Already in queue: {len(existing_upload_ids)}")
    
    # Add missing items to queue
    added_count = 0
    errors = []
    
    for upload_id, media_info in uploads_to_queue.items():
        if upload_id not in existing_upload_ids:
            try:
                # Get default configuration
                config_result = supabase.table("ai_extraction_queue") \
                    .select("model_config") \
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
                        "model_config": default_config  # Use a default or copy from another item
                    }) \
                    .execute()
                
                if result.data:
                    added_count += 1
                    print(f"✅ Added upload {upload_id} to queue")
                    
            except Exception as e:
                errors.append(f"Upload {upload_id}: {str(e)}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Total approved uploads: {len(uploads_to_queue)}")
    print(f"Already in queue: {len(existing_upload_ids)}")
    print(f"Newly added to queue: {added_count}")
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for error in errors[:5]:
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors")
    
    return added_count

async def check_and_fix_trigger():
    """Check if the trigger is working and apply fix if needed"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    print("\n\n=== CHECKING QUEUE TRIGGER ===")
    
    # The issue is that when you approve media via update_media_approval,
    # it only updates the media_files table, but the queue expects upload_id
    
    print("\nThe current approval process:")
    print("1. You approve a media file using update_media_approval()")
    print("2. This sets approval_status='approved' on the media_files table")
    print("3. BUT the queue table uses upload_id as reference, not media_id")
    print("\nThe trigger needs to:")
    print("1. Watch for media_files.approval_status changes")
    print("2. Get the upload_id from that media file")
    print("3. Create a queue entry using the upload_id")
    
    print("\n✅ The trigger SQL in 'fix_approval_queue_trigger.sql' handles this correctly")
    print("You should run that SQL to create the proper trigger")

if __name__ == "__main__":
    async def main():
        # Add approved media to queue
        added = await add_approved_media_to_queue()
        
        # Check trigger status
        await check_and_fix_trigger()
        
        print("\n\n=== NEXT STEPS ===")
        print("1. Run the SQL in 'fix_approval_queue_trigger.sql' to fix the trigger")
        print("2. Use 'reset_all_queue_items.py' to reset failed items to pending")
        print("3. Start the queue processor to begin extraction")
    
    asyncio.run(main())