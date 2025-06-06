import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get one media file to see structure
    media_result = supabase.table("media_files").select("*").limit(1).execute()
    if media_result.data:
        print("Media files table structure:")
        media = media_result.data[0]
        for key, value in media.items():
            print(f"  - {key}: {value}")
            
    # Now check for our specific upload
    upload_id = "upload-1748280814805-d5wfh8"
    media_result = supabase.table("media_files").select("*").eq("upload_id", upload_id).limit(5).execute()
    if media_result.data:
        print(f"\n\nMedia files for upload {upload_id}:")
        for i, media in enumerate(media_result.data):
            print(f"\n  Media {i+1}:")
            print(f"    id: {media.get('id')}")
            print(f"    file_path: {media.get('file_path')}")
            print(f"    original_filename: {media.get('original_filename')}")
            print(f"    capture_sequence: {media.get('capture_sequence')}")
            print(f"    validation_status: {media.get('validation_status')}")
            
            # If we find a valid path, update the queue
            if media.get('file_path'):
                print(f"\n    Found valid path! Updating queue item...")
                update_result = supabase.table("ai_extraction_queue").update({
                    "enhanced_image_path": media['file_path']
                }).eq("upload_id", upload_id).execute()
                if update_result.data:
                    print(f"    ✓ Updated queue items with path: {media['file_path']}")
                break