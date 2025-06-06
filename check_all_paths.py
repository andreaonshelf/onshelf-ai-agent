import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all queue items
    result = supabase.table("ai_extraction_queue").select("*").limit(5).execute()
    
    print(f"Checking first 5 queue items:")
    
    for item in result.data:
        print(f"\n=== Queue Item {item['id']} ===")
        print(f"  upload_id: {item.get('upload_id')}")
        print(f"  ready_media_id: {item.get('ready_media_id')}")
        print(f"  enhanced_image_path: {item.get('enhanced_image_path')}")
        print(f"  status: {item.get('status')}")
        
        # If enhanced_image_path is empty, try to get from uploads
        if item.get('upload_id') and not item.get('enhanced_image_path'):
            upload_result = supabase.table("uploads").select("file_path").eq("id", item['upload_id']).execute()
            if upload_result.data:
                print(f"  uploads.file_path: {upload_result.data[0].get('file_path')}")
                
                # Update the queue item
                if upload_result.data[0].get('file_path'):
                    update_result = supabase.table("ai_extraction_queue").update({
                        "enhanced_image_path": upload_result.data[0]['file_path']
                    }).eq("id", item['id']).execute()
                    print(f"  ✓ Updated enhanced_image_path")