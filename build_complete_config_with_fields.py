#!/usr/bin/env python3
"""
Build complete configuration using user's prompts + field definitions
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def build_complete_extraction_config():
    """Build complete config with prompts from database + field definitions from JSON files"""
    
    # Load prompts from database
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("📥 Loading prompts from database...")
    result = supabase.table("prompt_templates").select("*").eq("is_active", True).execute()
    
    # Get prompts by type
    prompts = {}
    for prompt in result.data:
        prompt_type = prompt.get('prompt_type')
        name = prompt.get('name', '')
        
        if 'v1' in name.lower():  # Prefer v1 versions
            prompts[prompt_type] = prompt.get('prompt_text', '')
    
    print(f"✅ Loaded prompts: {list(prompts.keys())}")
    
    # Load field definitions from JSON files
    print("📥 Loading field definitions from JSON files...")
    
    def load_json_fields(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                return data
        except:
            print(f"⚠️ Could not load {filename}")
            return None
    
    # Load each stage's field definitions
    structure_fields = load_json_fields('ui_schema_structure_v1.json')
    products_fields = load_json_fields('ui_schema_product_v1.json') 
    details_fields = load_json_fields('ui_schema_detail_v1.json')
    
    # Build complete configuration
    extraction_config = {
        "system": "custom_consensus",
        "temperature": 0.1,
        "orchestrator_model": "claude-4-opus",
        "max_budget": 2.0,
        "stages": {},
        "stage_models": {
            "structure": ["gpt-4o"],
            "products": ["gpt-4o", "claude-3-sonnet"],
            "details": ["gpt-4o", "claude-3-sonnet"]
        }
    }
    
    # Add structure stage
    if 'structure' in prompts and structure_fields:
        extraction_config["stages"]["structure"] = {
            "prompt_text": prompts['structure'],
            "fields": [structure_fields]  # Wrap in list as expected
        }
        print("✅ Structure: prompt + field definitions")
    
    # Add products stage  
    if 'product' in prompts and products_fields:
        extraction_config["stages"]["products"] = {
            "prompt_text": prompts['product'],
            "fields": [products_fields]  # Wrap in list as expected
        }
        print("✅ Products: prompt + field definitions")
    
    # Add details stage
    if 'detail' in prompts and details_fields:
        extraction_config["stages"]["details"] = {
            "prompt_text": prompts['detail'],
            "fields": [details_fields]  # Wrap in list as expected
        }
        print("✅ Details: prompt + field definitions")
    
    print(f"\n🎯 Complete configuration with {len(extraction_config['stages'])} stages")
    return extraction_config

def update_queue_item_with_complete_config():
    """Update queue item 8 with complete configuration"""
    
    config = build_complete_extraction_config()
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("🔄 Updating queue item 8 with complete configuration...")
    
    result = supabase.table("ai_extraction_queue").update({
        "extraction_config": config,
        "status": "pending"
    }).eq("id", 8).execute()
    
    print(f"✅ Updated queue item with complete config: {len(config['stages'])} stages")
    return result

if __name__ == "__main__":
    update_queue_item_with_complete_config()