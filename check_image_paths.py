import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Check a specific queue item that's failing
    result = supabase.table("ai_extraction_queue").select("*").eq("id", 6).execute()
    if result.data:
        item = result.data[0]
        print(f"Queue item 6:")
        print(f"- upload_id: {item.get('upload_id')}")
        print(f"- ready_media_id: {item.get('ready_media_id')}")
        print(f"- enhanced_image_path: {item.get('enhanced_image_path')}")
        
        # Check the ready_media table
        if item.get('ready_media_id'):
            media_result = supabase.table("ready_media").select("*").eq("id", item['ready_media_id']).execute()
            if media_result.data:
                print(f"\nReady media:")
                print(f"- enhanced_image_path: {media_result.data[0].get('enhanced_image_path')}")
                print(f"- original_image_path: {media_result.data[0].get('original_image_path')}")
        
        # Check the uploads table
        if item.get('upload_id'):
            upload_result = supabase.table("uploads").select("*").eq("id", item['upload_id']).execute()
            if upload_result.data:
                print(f"\nUpload:")
                print(f"- file_path: {upload_result.data[0].get('file_path')}")
                print(f"- original_filename: {upload_result.data[0].get('original_filename')}")