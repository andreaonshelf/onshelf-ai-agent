#!/usr/bin/env python3
"""Test script to verify extraction system fixes"""

import asyncio
import sys
from src.config import SystemConfig
from src.orchestrator.system_dispatcher import SystemDispatcher
from supabase import create_client

async def test_extraction_with_configuration():
    """Test extraction with proper configuration including stages"""
    
    config = SystemConfig()
    supabase = create_client(config.supabase_url, config.supabase_service_key)
    
    # Get a pending queue item
    result = supabase.table("ai_extraction_queue").select("*").eq("status", "pending").limit(1).execute()
    
    if not result.data:
        print("No pending items found!")
        return
        
    queue_item = result.data[0]
    print(f"Testing with queue item: {queue_item['id']}")
    print(f"Upload ID: {queue_item['upload_id']}")
    
    # Build full configuration with stages
    configuration = {
        "system": "langgraph_consensus",
        "temperature": 0.7,
        "stages": {
            "structure": {
                "prompt_text": "Extract the shelf structure from this retail shelf image. Identify shelf levels and sections.",
                "fields": []
            },
            "products": {
                "prompt_text": "Extract all products from this retail shelf image. Include brand, name, price, and position.",
                "fields": []
            }
        }
    }
    
    print("\n📋 Configuration to be sent:")
    print(f"  - System: {configuration['system']}")
    print(f"  - Has stages: {'stages' in configuration}")
    print(f"  - Stage count: {len(configuration.get('stages', {}))}")
    
    # Test image path retrieval
    print("\n🖼️ Testing image path retrieval...")
    dispatcher = SystemDispatcher(config, supabase_client=supabase, queue_item_id=queue_item['id'])
    
    try:
        images = await dispatcher._get_images(queue_item['upload_id'])
        print(f"✅ Successfully retrieved {len(images)} images")
        for img_path in images.keys():
            print(f"  - {img_path}")
    except Exception as e:
        print(f"❌ Failed to retrieve images: {e}")
        return
    
    # Now test the full extraction
    print("\n🚀 Starting extraction with full configuration...")
    try:
        result = await dispatcher.achieve_target_accuracy(
            upload_id=queue_item['upload_id'],
            target_accuracy=0.85,
            max_iterations=1,
            queue_item_id=queue_item['id'],
            system=configuration['system'],
            configuration=configuration
        )
        
        print(f"\n✅ Extraction completed!")
        print(f"  - Final accuracy: {result.final_accuracy}")
        print(f"  - Iterations: {result.iterations_completed}")
        print(f"  - Cost: ${result.total_cost:.3f}")
        
    except Exception as e:
        print(f"\n❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 Testing Extraction System Fixes")
    print("=" * 50)
    asyncio.run(test_extraction_with_configuration())