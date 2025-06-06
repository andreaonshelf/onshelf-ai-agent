#!/usr/bin/env python3
"""
Test real extraction with monitoring
"""

import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from supabase import create_client
from src.config import SystemConfig
from src.utils import logger

async def test_extraction():
    """Test extraction with real monitoring"""
    
    # Initialize config
    config = SystemConfig()
    supabase = create_client(config.supabase_url, config.supabase_service_key)
    
    # Get any item (pending, failed, or completed) to test
    result = supabase.table("ai_extraction_queue").select("*").limit(1).execute()
    
    if not result.data:
        print("No items found in queue")
        return
        
    item = result.data[0]
    print(f"\n🎯 Testing extraction for item {item['id']}")
    print(f"   Upload ID: {item['upload_id']}")
    print(f"   Current status: {item['status']}")
    
    # Reset to pending if not already
    if item['status'] != 'pending':
        print(f"   Resetting status from {item['status']} to pending...")
        supabase.table("ai_extraction_queue").update({
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "final_accuracy": None,
            "extraction_result": None,
            "planogram_result": None,
            "api_cost": None,
            "iterations_completed": None
        }).eq("id", item['id']).execute()
    
    # Import the API endpoint
    from src.api.queue_processing import run_extraction
    
    print("\n📡 Starting extraction with monitoring...")
    print("   Open the dashboard to see real-time updates!")
    print(f"   http://localhost:8130/new_dashboard.html")
    
    try:
        # Run extraction directly
        await run_extraction(
            item_id=item['id'],
            upload_id=item['upload_id'],
            system='custom_consensus',
            max_budget=1.50,
            configuration={}
        )
        
        print("\n✅ Extraction completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 OnShelf AI - Real Extraction Test")
    print("=" * 50)
    asyncio.run(test_extraction())