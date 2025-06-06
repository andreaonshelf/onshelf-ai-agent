#!/usr/bin/env python3
"""
TEST FULL PROCESS - Reset item and test processing
"""

import asyncio
import os
import sys
import aiohttp
import json
from supabase import create_client

async def test_full_process():
    """Test the complete process flow"""
    
    print("🚀 TESTING FULL PROCESS FLOW")
    print("=" * 50)
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
        
    supabase = create_client(supabase_url, supabase_key)
    
    # Step 1: Reset item 7 to pending directly in database
    print("\n1️⃣ Resetting item 7 to pending...")
    
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
    }).eq("id", 7).execute()
    
    if update_result.data:
        print("   ✅ Reset successful")
    else:
        print("   ❌ Reset failed")
        return
    
    # Wait a bit for database to sync
    await asyncio.sleep(1)
    
    # Step 2: Start the server
    print("\n2️⃣ Starting server...")
    import subprocess
    
    # Kill any existing server
    subprocess.run("lsof -i :8130 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null", shell=True)
    await asyncio.sleep(1)
    
    # Start new server
    server_process = subprocess.Popen(
        ["python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("   Waiting for server to start...")
    for i in range(10):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8130/api/queue/items") as response:
                    if response.status == 200:
                        print("   ✅ Server is running")
                        break
        except:
            await asyncio.sleep(1)
    else:
        print("   ❌ Server failed to start")
        server_process.kill()
        return
    
    # Step 3: Process the item
    print("\n3️⃣ Processing item 7...")
    
    async with aiohttp.ClientSession() as session:
        # First check the item status
        async with session.get("http://localhost:8130/api/queue/items") as response:
            items = await response.json()
            item_7 = None
            for item in items['items']:
                if item['id'] == 7:
                    item_7 = item
                    print(f"   Current status: {item['status']}")
                    break
            
            if not item_7:
                print("   ❌ Item 7 not found!")
                server_process.kill()
                return
            
            if item_7['status'] != 'pending':
                print(f"   ⚠️  Item is {item_7['status']}, not pending!")
        
        # Call process endpoint
        print("\n   Calling process endpoint...")
        process_data = {
            "system": "custom_consensus",
            "max_budget": 2.0,
            "configuration": {}
        }
        
        async with session.post(
            "http://localhost:8130/api/queue/process/7", 
            json=process_data
        ) as response:
            print(f"   Response status: {response.status}")
            result = await response.json()
            print(f"   Response: {json.dumps(result, indent=2)}")
    
    # Step 4: Monitor extraction
    print("\n4️⃣ Monitoring extraction...")
    
    for i in range(30):  # Monitor for 30 seconds
        await asyncio.sleep(1)
        
        # Check monitoring data
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8130/api/queue/monitor/7") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') != 'processing':
                            print(f"\n   Status: {data.get('status')}")
                            print(f"   Data: {json.dumps(data, indent=2)}")
                        else:
                            # Show progress
                            stage = data.get('current_stage', 'Unknown')
                            iteration = data.get('current_iteration', 0)
                            duration = data.get('duration', 0)
                            print(f"\r   Progress: Iteration {iteration} - {stage} - {duration}s", end='', flush=True)
            except Exception as e:
                print(f"\r   Waiting... ({i}s)", end='', flush=True)
    
    print("\n\n5️⃣ Final check...")
    
    # Check final status
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8130/api/queue/items") as response:
            items = await response.json()
            for item in items['items']:
                if item['id'] == 7:
                    print(f"   Final status: {item['status']}")
                    if item.get('error_message'):
                        print(f"   Error: {item['error_message']}")
                    break
    
    # Check logs
    print("\n6️⃣ Recent logs:")
    result = subprocess.run(
        "tail -50 /Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/logs/onshelf_ai_*.log | grep -E '(item 7|ERROR|Starting extraction|run_extraction|Processing stage)'",
        shell=True,
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout[-1000:])  # Last 1000 chars
    
    # Kill server
    print("\n7️⃣ Cleaning up...")
    server_process.kill()
    print("   ✅ Server stopped")

if __name__ == "__main__":
    asyncio.run(test_full_process())