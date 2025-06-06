#!/usr/bin/env python3
"""Debug what's actually in the queue item's extraction_config"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def debug_queue_config():
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("🔍 Checking queue item 8 configuration...")
    
    result = supabase.table("ai_extraction_queue").select("*").eq("id", 8).execute()
    
    if result.data:
        item = result.data[0]
        
        print(f"Status: {item.get('status')}")
        print(f"System: {item.get('current_extraction_system')}")
        
        extraction_config = item.get('extraction_config')
        model_config = item.get('model_config')
        
        print(f"\n📊 extraction_config exists: {bool(extraction_config)}")
        if extraction_config:
            stages = extraction_config.get('stages', {})
            print(f"   Stages: {list(stages.keys())}")
            for stage_name, stage_config in stages.items():
                fields = stage_config.get('fields', [])
                prompt_len = len(stage_config.get('prompt_text', ''))
                print(f"   {stage_name}: {len(fields)} fields, {prompt_len} chars prompt")
        
        print(f"\n📊 model_config exists: {bool(model_config)}")
        if model_config:
            stages = model_config.get('stages', {})
            print(f"   Stages: {list(stages.keys())}")
        
        return item
    else:
        print("❌ Queue item 8 not found")
        return None

if __name__ == "__main__":
    debug_queue_config()