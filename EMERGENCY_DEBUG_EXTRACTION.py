#!/usr/bin/env python3
"""
EMERGENCY DEBUG: Test what happens when we process an extraction item
This will trace the EXACT path that happens when you click "Process"
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemConfig
from src.orchestrator.system_dispatcher import SystemDispatcher
from src.utils import logger

async def debug_extraction_processing():
    """Debug what happens during extraction processing"""
    
    print("=" * 80)
    print("EMERGENCY DEBUG: Testing Extraction Processing")
    print("=" * 80)
    
    # Step 1: Test configuration loading
    print("\n1. Testing configuration loading...")
    config = SystemConfig()
    print(f"   ✓ Config loaded")
    print(f"   - Supabase URL: {config.supabase_url[:50]}...")
    print(f"   - Models configured: {config.models}")
    
    # Step 2: Test Supabase connection and get a real queue item
    print("\n2. Testing Supabase connection...")
    from supabase import create_client
    try:
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        # Get a pending item from the queue
        result = supabase.table("ai_extraction_queue").select("*").eq("status", "pending").limit(1).execute()
        
        if not result.data:
            print("   ❌ No pending items found in queue")
            print("   Creating a fake test item...")
            test_item = {
                'id': 999,
                'upload_id': 'test_debug_001',
                'status': 'pending',
                'extraction_config': {
                    'stages': {
                        'structure': {
                            'prompt_text': 'Test structure prompt for debugging'
                        },
                        'products': {
                            'prompt_text': 'Test products prompt for debugging'  
                        }
                    }
                },
                'current_extraction_system': 'custom_consensus'
            }
        else:
            test_item = result.data[0]
            print(f"   ✓ Found queue item {test_item['id']}")
            
    except Exception as e:
        print(f"   ❌ Supabase connection failed: {e}")
        return
        
    # Step 3: Test configuration extraction
    print("\n3. Testing configuration extraction...")
    extraction_config = test_item.get('extraction_config', {})
    print(f"   - Has extraction_config: {bool(extraction_config)}")
    print(f"   - Has stages: {'stages' in extraction_config}")
    if 'stages' in extraction_config:
        stages = extraction_config['stages']
        print(f"   - Stages found: {list(stages.keys())}")
        for stage_id, stage_config in stages.items():
            has_prompt = 'prompt_text' in stage_config if isinstance(stage_config, dict) else False
            print(f"     - {stage_id}: has_prompt={has_prompt}")
    
    # Step 4: Test SystemDispatcher initialization
    print("\n4. Testing SystemDispatcher...")
    try:
        orchestrator = SystemDispatcher(config, supabase_client=supabase)
        print(f"   ✓ SystemDispatcher created")
    except Exception as e:
        print(f"   ❌ SystemDispatcher failed: {e}")
        return
    
    # Step 5: Test system creation
    print("\n5. Testing extraction system creation...")
    try:
        from src.systems.base_system import ExtractionSystemFactory
        system_type = 'custom'
        extraction_system = ExtractionSystemFactory.get_system(system_type, config)
        print(f"   ✓ Extraction system created: {type(extraction_system).__name__}")
    except Exception as e:
        print(f"   ❌ System creation failed: {e}")
        return
    
    # Step 6: Test configuration passing
    print("\n6. Testing configuration passing...")
    try:
        configuration = extraction_config if extraction_config.get('stages') else {}
        
        # Extract stage prompts exactly like SystemDispatcher does
        stage_prompts = {}
        stages = configuration.get('stages', {})
        
        for stage_id, stage_config in stages.items():
            if isinstance(stage_config, dict) and 'prompt_text' in stage_config:
                stage_prompts[stage_id] = stage_config['prompt_text']
        
        extraction_system.stage_prompts = stage_prompts
        extraction_system.stage_configs = stages
        
        print(f"   ✓ Configuration passed")
        print(f"   - Stage prompts loaded: {list(stage_prompts.keys())}")
        print(f"   - Has prompts: {bool(stage_prompts)}")
        
    except Exception as e:
        print(f"   ❌ Configuration passing failed: {e}")
        return
    
    # Step 7: Test if we have prompts (this is what causes the failure!)
    print("\n7. Testing prompt validation...")
    if not stage_prompts:
        print("   ❌ FOUND THE PROBLEM: No stage prompts loaded!")
        print("   This is why extraction fails immediately!")
        print("   The system refuses to run without custom prompts.")
        return
    else:
        print("   ✓ Stage prompts are available")
    
    # Step 8: Test image loading (if item exists)
    print("\n8. Testing image loading...")
    if test_item.get('id') != 999:  # Real item
        try:
            upload_id = test_item['upload_id']
            images = await orchestrator._get_images(upload_id)
            print(f"   ✓ Images loaded: {len(images)} images")
            print(f"   - Image types: {list(images.keys())}")
            print(f"   - Total image data: {sum(len(img) for img in images.values())} bytes")
        except Exception as e:
            print(f"   ❌ Image loading failed: {e}")
            print("   This could cause processing to fail")
            return
    else:
        print("   ⚠️  Skipping image loading for fake test item")
    
    # Step 9: Test API key availability
    print("\n9. Testing API keys...")
    api_keys = {
        'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
        'ANTHROPIC_API_KEY': bool(os.getenv('ANTHROPIC_API_KEY')),
        'GOOGLE_API_KEY': bool(os.getenv('GOOGLE_API_KEY'))
    }
    
    for key, available in api_keys.items():
        status = "✓" if available else "❌"
        print(f"   {status} {key}: {'Available' if available else 'Missing'}")
    
    if not any(api_keys.values()):
        print("   ❌ NO API KEYS FOUND! This will cause extraction to fail!")
        return
    
    print("\n" + "=" * 80)
    print("DEBUG SUMMARY:")
    print("=" * 80)
    
    if stage_prompts:
        print("✓ Prompts are loaded correctly")
    else:
        print("❌ MAIN ISSUE: No prompts loaded - this causes immediate failure")
        
    if any(api_keys.values()):
        print("✓ At least one API key is available")
    else:
        print("❌ CRITICAL: No API keys available")
        
    if test_item.get('id') != 999:
        print("✓ Real queue item found for testing")
    else:
        print("⚠️  No real queue items available for testing")
    
    print("\nNext steps:")
    print("1. Check if prompts are properly saved in the UI")
    print("2. Check if extraction_config is properly stored in queue items")
    print("3. Verify API keys are set in environment")
    print("4. Check logs for the actual error message")

if __name__ == "__main__":
    asyncio.run(debug_extraction_processing())