import os
from supabase import create_client
from datetime import datetime

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get the completed items
    completed_items = [8, 5, 9]
    
    for item_id in completed_items:
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        if result.data:
            item = result.data[0]
            print(f"\n=== Item {item_id} ===")
            print(f"Completed at: {item.get('completed_at')}")
            
            # Parse the time
            if item.get('completed_at'):
                completed_time = datetime.fromisoformat(item['completed_at'].replace('Z', '+00:00'))
                print(f"That was at: {completed_time.strftime('%I:%M %p')} UTC")
                
                # Check if this matches when we ran the reset script
                print(f"\nThis was marked complete AFTER we reset it to pending!")
                print("Someone or something marked it as complete with fake data.")
    
    # Let's check the logs around that time
    print("\n\nChecking logs around 06:28 UTC...")
    import subprocess
    result = subprocess.run(
        ["grep", "06:28", f"/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/logs/onshelf_ai_{datetime.now().strftime('%Y%m%d')}.log"],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print("\nLog entries around that time:")
        for line in result.stdout.strip().split('\n')[:10]:
            if 'complete' in line.lower() or 'mock' in line.lower():
                print(line)