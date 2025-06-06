#!/usr/bin/env python3
"""
Force process a specific item with full debugging
"""

import asyncio
import os
import sys
from supabase import create_client

async def force_process(item_id):
    """Force process a specific item"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials")
        return
        
    supabase = create_client(supabase_url, supabase_key)
    
    print(f"🔄 Resetting item {item_id} to pending...")
    
    # Force reset to pending
    update_result = supabase.table("ai_extraction_queue").update({
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "final_accuracy": None,
        "extraction_result": None,
        "planogram_result": None,
        "api_cost": None,
        "iterations_completed": None,
        "current_extraction_system": None,
        "processing_duration_seconds": None
    }).eq("id", item_id).execute()
    
    if not update_result.data:
        print(f"❌ Failed to reset item {item_id}")
        return
        
    print(f"✅ Reset item {item_id} to pending")
    
    # Now trigger processing via API
    import aiohttp
    
    print(f"\n🚀 Triggering extraction for item {item_id}...")
    
    async with aiohttp.ClientSession() as session:
        url = f"http://localhost:8130/api/queue/process/{item_id}"
        data = {
            "system": "custom_consensus",
            "max_budget": 2.0,
            "configuration": {}
        }
        
        try:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Processing started: {result}")
                    
                    print(f"\n📊 Monitor the extraction at:")
                    print(f"   http://localhost:8130/new_dashboard.html")
                    print(f"   Click 'Monitor' on item {item_id}")
                    
                    print(f"\n📝 Watch logs in real-time:")
                    print(f"   python watch_extraction_logs.py {item_id}")
                    
                else:
                    error = await response.text()
                    print(f"❌ Failed to start processing: {error}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python force_process_item.py <item_id>")
        sys.exit(1)
        
    item_id = int(sys.argv[1])
    asyncio.run(force_process(item_id))