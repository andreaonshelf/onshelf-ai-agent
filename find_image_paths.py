import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Check queue item 6 that was failing
    queue_result = supabase.table("ai_extraction_queue").select("*").eq("id", 6).execute()
    if queue_result.data:
        item = queue_result.data[0]
        upload_id = item.get('upload_id')
        print(f"Queue Item 6 - Upload ID: {upload_id}")
        
        # Try to find media files for this upload
        media_result = supabase.table("media_files").select("*").eq("upload_id", upload_id).execute()
        if media_result.data:
            print(f"\nFound {len(media_result.data)} media files:")
            for media in media_result.data:
                print(f"  - {media.get('filename')}: {media.get('storage_path')}")
                
                # Update queue item with first media file path
                if media.get('storage_path') and not item.get('enhanced_image_path'):
                    update_result = supabase.table("ai_extraction_queue").update({
                        "enhanced_image_path": media['storage_path']
                    }).eq("id", 6).execute()
                    print(f"\n✓ Updated queue item with path: {media['storage_path']}")
                    break
        else:
            print("\nNo media files found in media_files table")
            
        # Check if the upload ID might be used as a path
        print(f"\nTrying to use upload_id as path...")
        # Common patterns for storage paths
        possible_paths = [
            f"uploads/{upload_id}/enhanced.jpg",
            f"uploads/{upload_id}/image.jpg",
            f"{upload_id}/enhanced.jpg",
            f"{upload_id}.jpg"
        ]
        
        for path in possible_paths:
            try:
                # Try to download to check if it exists
                data = supabase.storage.from_("retail-captures").download(path)
                if data:
                    print(f"✓ Found image at: {path}")
                    # Update the queue item
                    update_result = supabase.table("ai_extraction_queue").update({
                        "enhanced_image_path": path
                    }).eq("id", 6).execute()
                    print(f"✓ Updated queue item with path: {path}")
                    break
            except Exception as e:
                continue