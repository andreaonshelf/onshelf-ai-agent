import os
from supabase import create_client
from datetime import datetime, timedelta

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all processing and failed items
    result = supabase.table("ai_extraction_queue").select("*").in_("status", ["processing", "failed"]).execute()
    
    print(f"Found {len(result.data)} stuck/failed items:\n")
    
    for item in result.data:
        print(f"=== Item {item['id']} ===")
        print(f"  Status: {item['status']}")
        print(f"  Upload ID: {item.get('upload_id')}")
        print(f"  Enhanced image path: {item.get('enhanced_image_path') or 'MISSING'}")
        print(f"  Error: {item.get('error_message') or 'None'}")
        print(f"  Started at: {item.get('started_at')}")
        
        # Check if it's been stuck for too long
        if item['status'] == 'processing' and item.get('started_at'):
            started = datetime.fromisoformat(item['started_at'].replace('Z', '+00:00'))
            duration = datetime.utcnow().replace(tzinfo=started.tzinfo) - started
            print(f"  Duration: {duration}")
            if duration > timedelta(minutes=10):
                print(f"  ⚠️  STUCK for over 10 minutes!")
        
        print()