#!/usr/bin/env python3
"""
FORCE REAL EXTRACTION - No more bullshit
"""

import asyncio
import os
from supabase import create_client
import aiohttp

async def force_real_extraction():
    """Force a real extraction to happen NOW"""
    
    print("🔥 FORCING REAL EXTRACTION")
    print("=" * 50)
    
    # Get Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(supabase_url, supabase_key)
    
    # Step 1: Reset item 7 to pending
    print("\n1️⃣ Resetting item 7 to pending...")
    
    result = supabase.table("ai_extraction_queue").update({
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
        "processing_duration_seconds": None,
        "comparison_group_id": None
    }).eq("id", 7).execute()
    
    if result.data:
        print("   ✅ Reset successful")
    else:
        print("   ❌ Reset failed")
        return
    
    # Wait a moment
    await asyncio.sleep(2)
    
    # Step 2: Call the process endpoint
    print("\n2️⃣ Calling process endpoint...")
    
    async with aiohttp.ClientSession() as session:
        url = "http://localhost:8130/api/queue/process/7"
        data = {
            "system": "custom_consensus",
            "max_budget": 2.0,
            "configuration": {}
        }
        
        try:
            async with session.post(url, json=data) as response:
                result = await response.json()
                print(f"   Response: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
    
    # Step 3: Run the extraction DIRECTLY
    print("\n3️⃣ Running extraction DIRECTLY (fuck the background task)...")
    
    from src.api.queue_processing import run_extraction
    
    try:
        # Run it RIGHT NOW
        await run_extraction(
            item_id=7,
            upload_id="upload-1748283096845-z057h5",
            system='custom_consensus',
            max_budget=2.0,
            configuration={}
        )
        print("   ✅ Extraction completed!")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("This will FORCE extraction to happen NOW")
    print("Watch the logs and monitor in the dashboard")
    asyncio.run(force_real_extraction())