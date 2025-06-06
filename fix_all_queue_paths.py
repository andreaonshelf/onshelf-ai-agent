import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all queue items without enhanced_image_path
    queue_result = supabase.table("ai_extraction_queue").select("*").or_("enhanced_image_path.is.null,enhanced_image_path.eq.").execute()
    
    print(f"Found {len(queue_result.data)} queue items without image paths")
    
    fixed_count = 0
    for item in queue_result.data:
        upload_id = item.get('upload_id')
        if not upload_id:
            continue
            
        # Get media files for this upload
        media_result = supabase.table("media_files").select("file_path").eq("upload_id", upload_id).execute()
        
        if media_result.data:
            # Find first valid path
            for media in media_result.data:
                if media.get('file_path'):
                    # Update queue item
                    update_result = supabase.table("ai_extraction_queue").update({
                        "enhanced_image_path": media['file_path']
                    }).eq("id", item['id']).execute()
                    
                    if update_result.data:
                        print(f"✓ Fixed item {item['id']} with path: {media['file_path']}")
                        fixed_count += 1
                    break
    
    print(f"\nFixed {fixed_count} queue items")