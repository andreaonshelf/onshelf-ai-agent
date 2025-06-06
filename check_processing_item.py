import os
from supabase import create_client
from datetime import datetime, timedelta

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get all processing items
    result = supabase.table("ai_extraction_queue").select("*").eq("status", "processing").execute()
    
    print(f"Found {len(result.data)} items marked as 'processing':\n")
    
    for item in result.data:
        print(f"=== Item {item['id']} ===")
        print(f"  Upload ID: {item.get('upload_id')}")
        print(f"  Status: {item['status']}")
        print(f"  Started at: {item.get('started_at')}")
        print(f"  Current system: {item.get('current_extraction_system')}")
        print(f"  Selected systems: {item.get('selected_systems')}")
        
        # Check how long it's been processing
        if item.get('started_at'):
            started = datetime.fromisoformat(item['started_at'].replace('Z', '+00:00'))
            duration = datetime.utcnow().replace(tzinfo=started.tzinfo) - started
            print(f"  Duration: {duration}")
            
            if duration > timedelta(minutes=5):
                print(f"  ⚠️  STUCK - Processing for over 5 minutes!")
        
        # Check if there's any monitoring data
        print(f"\n  Checking for active processing...")
        
        # Look for recent logs
        import subprocess
        result = subprocess.run(
            ["tail", "-100", f"/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/logs/onshelf_ai_{datetime.now().strftime('%Y%m%d')}.log"],
            capture_output=True,
            text=True
        )
        
        if result.stdout and item.get('upload_id'):
            upload_id = item['upload_id']
            relevant_logs = [line for line in result.stdout.split('\n') if upload_id in line]
            if relevant_logs:
                print(f"  Recent log entries:")
                for log in relevant_logs[-5:]:
                    print(f"    {log[:100]}...")
            else:
                print(f"  ❌ NO LOGS found for this upload_id")
        
        print()