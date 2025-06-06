"""
Reset all queue items from failed/processed back to pending
"""

import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def reset_all_queue_items():
    """Reset all queue items to pending status"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    print("=== RESETTING ALL QUEUE ITEMS ===")
    
    # First, get counts of current statuses
    result = supabase.table("ai_extraction_queue") \
        .select("status", count="exact") \
        .execute()
    
    print(f"\nTotal items in queue: {result.count}")
    
    # Get status breakdown
    status_counts = {}
    for item in result.data:
        status = item['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nCurrent status breakdown:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # Reset all non-pending items to pending
    try:
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
        
        print(f"\nReset {len(failed_result.data)} failed items to pending")
        
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
        
        print(f"Reset {len(processing_result.data)} processing items to pending")
        
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
        
        print(f"Reset {len(completed_result.data)} completed items to pending")
        
        # Get final counts
        final_result = supabase.table("ai_extraction_queue") \
            .select("status", count="exact") \
            .eq("status", "pending") \
            .execute()
        
        print(f"\n✅ SUCCESS: {final_result.count} items are now pending")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True

async def check_approved_media_not_in_queue():
    """Check for approved media files that aren't in the extraction queue"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    print("\n\n=== CHECKING APPROVED MEDIA NOT IN QUEUE ===")
    
    # Get all approved media files
    approved_media = supabase.table("media_files") \
        .select("media_id, file_path, approval_status, approved_at") \
        .eq("approval_status", "approved") \
        .execute()
    
    print(f"\nTotal approved media files: {len(approved_media.data)}")
    
    # Get all queue items
    queue_items = supabase.table("ai_extraction_queue") \
        .select("media_id") \
        .execute()
    
    queue_media_ids = {item['media_id'] for item in queue_items.data}
    print(f"Total items in extraction queue: {len(queue_media_ids)}")
    
    # Find approved media not in queue
    missing_from_queue = []
    for media in approved_media.data:
        if media['media_id'] not in queue_media_ids:
            missing_from_queue.append(media)
    
    print(f"\n⚠️  Approved media files NOT in extraction queue: {len(missing_from_queue)}")
    
    if missing_from_queue:
        print("\nMissing items (first 10):")
        for item in missing_from_queue[:10]:
            print(f"  - ID: {item['media_id']}, Path: {item['file_path']}")
            print(f"    Approved at: {item['approved_at']}")
        
        if len(missing_from_queue) > 10:
            print(f"  ... and {len(missing_from_queue) - 10} more")
    
    return missing_from_queue

async def check_queue_trigger():
    """Check if the queue trigger function exists and is working"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    print("\n\n=== CHECKING QUEUE TRIGGER ===")
    
    # Try to manually trigger queue insertion for one approved item
    approved_media = supabase.table("media_files") \
        .select("media_id") \
        .eq("approval_status", "approved") \
        .limit(1) \
        .execute()
    
    if approved_media.data:
        media_id = approved_media.data[0]['media_id']
        print(f"\nTesting manual queue insertion for media_id: {media_id}")
        
        try:
            # Check if already in queue
            existing = supabase.table("ai_extraction_queue") \
                .select("id") \
                .eq("media_id", media_id) \
                .execute()
            
            if existing.data:
                print(f"  Item already in queue with id: {existing.data[0]['id']}")
            else:
                # Try to insert manually
                result = supabase.table("ai_extraction_queue") \
                    .insert({
                        "media_id": media_id,
                        "status": "pending",
                        "priority": 5,
                        "created_at": datetime.utcnow().isoformat()
                    }) \
                    .execute()
                
                if result.data:
                    print(f"  ✅ Successfully inserted into queue")
                    # Delete it to clean up
                    supabase.table("ai_extraction_queue") \
                        .delete() \
                        .eq("id", result.data[0]['id']) \
                        .execute()
                    print(f"  Cleaned up test insertion")
        except Exception as e:
            print(f"  ❌ Error during manual insertion: {e}")

if __name__ == "__main__":
    async def main():
        # Reset all queue items
        await reset_all_queue_items()
        
        # Check for missing approved items
        missing_items = await check_approved_media_not_in_queue()
        
        # Check trigger
        await check_queue_trigger()
        
        if missing_items:
            print("\n\n=== RECOMMENDATION ===")
            print("The approved media files are not being automatically added to the queue.")
            print("This suggests the trigger function is not working properly.")
            print("\nYou should check:")
            print("1. If the trigger 'on_media_approval' exists on the media_files table")
            print("2. If the function 'add_to_extraction_queue()' exists and is correct")
            print("3. Review the trigger/function definitions")
    
    asyncio.run(main())