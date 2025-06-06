import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all queue items with missing image paths
    result = supabase.table("ai_extraction_queue").select("*").is_("enhanced_image_path", "null").execute()
    
    print(f"Found {len(result.data)} queue items with missing image paths")
    
    for item in result.data:
        upload_id = item.get('upload_id')
        if upload_id:
            # Get the upload record
            upload_result = supabase.table("uploads").select("*").eq("id", upload_id).execute()
            if upload_result.data:
                upload = upload_result.data[0]
                file_path = upload.get('file_path')
                
                if file_path:
                    print(f"\nFixing queue item {item['id']}:")
                    print(f"  Upload ID: {upload_id}")
                    print(f"  File path: {file_path}")
                    
                    # Update the queue item with the image path
                    update_result = supabase.table("ai_extraction_queue").update({
                        "enhanced_image_path": file_path
                    }).eq("id", item['id']).execute()
                    
                    if update_result.data:
                        print(f"  ✓ Updated successfully")
                    else:
                        print(f"  ✗ Update failed")