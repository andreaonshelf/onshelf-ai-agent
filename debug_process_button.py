#!/usr/bin/env python3
"""
Debug what happens when you click Process
"""

import asyncio
import aiohttp
import json
import time

async def debug_process():
    """Debug the entire process flow"""
    
    print("🔍 DEBUGGING PROCESS BUTTON CLICK")
    print("=" * 50)
    
    # Step 1: Check what items are available
    print("\n1️⃣ Getting queue items...")
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8130/api/queue/items") as response:
            items = await response.json()
            print(f"   Found {len(items['items'])} items")
            
            # Find a pending item
            pending_item = None
            for item in items['items']:
                print(f"   - Item {item['id']}: {item['status']}")
                if item['status'] == 'pending':
                    pending_item = item
                    break
            
            if not pending_item:
                print("   ❌ No pending items found!")
                return
            
            print(f"\n2️⃣ Testing process for item {pending_item['id']}")
            
            # Step 2: Call the process endpoint
            print(f"   Calling POST /api/queue/process/{pending_item['id']}")
            
            process_data = {
                "system": "custom_consensus",
                "max_budget": 2.0,
                "configuration": {}
            }
            
            async with session.post(
                f"http://localhost:8130/api/queue/process/{pending_item['id']}", 
                json=process_data
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    print(f"   ❌ API Error: {error}")
                    return
                
                result = await response.json()
                print(f"   ✅ API Response: {json.dumps(result, indent=2)}")
            
            # Step 3: Check if background task is running
            print(f"\n3️⃣ Checking if extraction actually started...")
            
            # Wait a bit for background task to start
            await asyncio.sleep(2)
            
            # Check monitoring data
            try:
                async with session.get(f"http://localhost:8130/api/queue/monitor/{pending_item['id']}") as response:
                    if response.status == 200:
                        monitor_data = await response.json()
                        print(f"   Monitor data: {json.dumps(monitor_data, indent=2)}")
                    else:
                        print(f"   ❌ No monitoring data (status {response.status})")
            except Exception as e:
                print(f"   ❌ Error getting monitor data: {e}")
            
            # Step 4: Check queue item status
            print(f"\n4️⃣ Checking queue item status...")
            async with session.get("http://localhost:8130/api/queue/items") as response:
                items = await response.json()
                for item in items['items']:
                    if item['id'] == pending_item['id']:
                        print(f"   Item status: {item['status']}")
                        if item.get('error_message'):
                            print(f"   Error: {item['error_message']}")
                        break
            
            # Step 5: Check logs
            print(f"\n5️⃣ Recent log entries:")
            import subprocess
            result = subprocess.run(
                f"tail -20 /Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/logs/onshelf_ai_*.log | grep -E '(item {pending_item['id']}|ERROR|Starting extraction|run_extraction)'",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(result.stdout)
            else:
                print("   No relevant logs found")

if __name__ == "__main__":
    asyncio.run(debug_process())