#!/usr/bin/env python3
"""Debug queue item 9 configuration state."""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def debug_config():
    """Debug the current configuration state"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("=" * 80)
    print("DEBUGGING QUEUE ITEM 9 CONFIGURATION")
    print("=" * 80)
    
    # Get current configuration
    result = supabase.table("ai_extraction_queue").select("*").eq("id", 9).single().execute()
    
    if result.data:
        item = result.data
        extraction_config = item.get('extraction_config', {})
        model_config = item.get('model_config', {})
        
        if isinstance(extraction_config, str):
            extraction_config = json.loads(extraction_config)
        if isinstance(model_config, str):
            model_config = json.loads(model_config)
        
        print(f"Status: {item['status']}")
        print(f"Upload ID: {item['upload_id']}")
        
        print("\n\nEXTRACTION CONFIG:")
        print("-" * 50)
        print(json.dumps(extraction_config, indent=2))
        
        print("\n\nMODEL CONFIG:")
        print("-" * 50)
        print(json.dumps(model_config, indent=2))
        
        # Check stages specifically
        print("\n\nSTAGE ANALYSIS:")
        print("-" * 50)
        
        extraction_stages = extraction_config.get('stages', {})
        model_stages = model_config.get('stages', {})
        
        print(f"Extraction config stages: {list(extraction_stages.keys())}")
        print(f"Model config stages: {list(model_stages.keys())}")
        
        for stage_name in ['structure', 'products', 'details']:
            ext_stage = extraction_stages.get(stage_name, {})
            model_stage = model_stages.get(stage_name, {})
            
            print(f"\n{stage_name.upper()}:")
            print(f"  In extraction_config: {stage_name in extraction_stages}")
            print(f"  In model_config: {stage_name in model_stages}")
            
            if ext_stage:
                print(f"  extraction_config fields: {len(ext_stage.get('fields', []))}")
                print(f"  extraction_config has prompt: {'prompt_text' in ext_stage}")
            
            if model_stage:
                print(f"  model_config fields: {len(model_stage.get('fields', []))}")
                print(f"  model_config has prompt: {'prompt_text' in model_stage}")

if __name__ == "__main__":
    debug_config()