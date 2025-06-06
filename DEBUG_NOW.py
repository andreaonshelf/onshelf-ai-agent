#!/usr/bin/env python3
"""
DEBUG EXACTLY WHY PROMPTS AREN'T LOADING
"""

import asyncio
import os
from supabase import create_client
import json

async def debug_prompt_flow():
    print("🔍 DEBUGGING PROMPT LOADING FLOW")
    print("=" * 50)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(supabase_url, supabase_key)
    
    # 1. Check what prompts are in the database
    print("\n1️⃣ PROMPTS IN DATABASE:")
    prompts = supabase.table("prompt_templates").select("*").execute()
    
    for p in prompts.data:
        print(f"\n   ID: {p.get('prompt_id', 'NO_ID')}")
        print(f"   Name: {p.get('name', 'NO_NAME')}")
        print(f"   Stage: {p.get('stage', p.get('stage_type', 'NO_STAGE'))}")
        print(f"   First 100 chars: {p.get('prompt_text', 'NO_PROMPT')[:100]}...")
    
    # 2. Check extraction configurations
    print("\n\n2️⃣ EXTRACTION CONFIGS IN DATABASE:")
    configs = supabase.table("extraction_configs").select("*").order("created_at", desc=True).limit(3).execute()
    
    for c in configs.data:
        print(f"\n   Config: {c['name']}")
        print(f"   Created: {c['created_at']}")
        stages = c.get('stages', {})
        print(f"   Stages configured: {list(stages.keys())}")
        
        # Check if stages have prompt_text
        for stage_id, stage_data in stages.items():
            if isinstance(stage_data, dict):
                has_prompt = 'prompt_text' in stage_data
                prompt_id = stage_data.get('prompt_id')
                print(f"     - {stage_id}: has_prompt_text={has_prompt}, prompt_id={prompt_id}")
    
    # 3. Check what happens when we process an item
    print("\n\n3️⃣ CHECKING QUEUE ITEM CONFIGURATION:")
    
    # Get a queue item
    queue_items = supabase.table("ai_extraction_queue").select("*").limit(1).execute()
    
    if queue_items.data:
        item = queue_items.data[0]
        print(f"\n   Queue Item ID: {item['id']}")
        print(f"   Status: {item['status']}")
        
        # Check model_config
        model_config = item.get('model_config')
        if model_config:
            print(f"   Has model_config: YES")
            print(f"   Config keys: {list(model_config.keys()) if isinstance(model_config, dict) else 'Not a dict'}")
            
            if isinstance(model_config, dict):
                # Check for stages
                stages = model_config.get('stages', {})
                print(f"   Stages in model_config: {list(stages.keys())}")
                
                # Check for extraction_config
                extraction_config = model_config.get('extraction_config', {})
                if extraction_config:
                    print(f"   Has extraction_config: YES")
                    ec_stages = extraction_config.get('stages', {})
                    print(f"   Stages in extraction_config: {list(ec_stages.keys())}")
        else:
            print(f"   Has model_config: NO")
    
    # 4. Test the configuration flow
    print("\n\n4️⃣ TESTING CONFIGURATION RETRIEVAL:")
    
    # Simulate what happens in queue_processing.py
    latest_config = supabase.table("extraction_configs").select("*").order("created_at", desc=True).limit(1).execute()
    
    if latest_config.data:
        config = latest_config.data[0]
        print(f"\n   Using config: {config['name']}")
        
        # This is what gets passed to the extraction
        extraction_config = {
            "system": "custom_consensus",
            "max_budget": 2.0,
            "temperature": 0.1,
            "stages": config.get('stages', {}),
            "stage_models": config.get('stage_models', {}),
            "orchestrators": config.get('orchestrators', {})
        }
        
        print(f"\n   Extraction config that would be passed:")
        print(json.dumps(extraction_config, indent=2)[:500] + "...")
        
        # Check if prompts are there
        stages = extraction_config.get('stages', {})
        prompts_found = False
        for stage_id, stage_data in stages.items():
            if isinstance(stage_data, dict) and 'prompt_text' in stage_data:
                prompts_found = True
                print(f"\n   ✅ Found prompt for {stage_id}")
                print(f"      First 100 chars: {stage_data['prompt_text'][:100]}...")
        
        if not prompts_found:
            print("\n   ❌ NO PROMPTS FOUND IN CONFIGURATION!")

if __name__ == "__main__":
    asyncio.run(debug_prompt_flow())