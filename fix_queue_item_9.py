#!/usr/bin/env python3
"""
Fix queue item 9 by adding proper field definitions to extraction_config
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def load_field_schema(filename):
    """Load field schema from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load {filename}: {e}")
        return None

def fix_queue_item_9():
    """Update queue item 9 with proper field definitions"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("=" * 80)
    print("FIXING QUEUE ITEM 9 - Adding Field Definitions")
    print("=" * 80)
    
    # First get the current configuration
    result = supabase.table("ai_extraction_queue").select("*").eq("id", 9).single().execute()
    
    if not result.data:
        print("❌ Queue item 9 not found!")
        return
    
    item = result.data
    extraction_config = item.get('extraction_config', {})
    
    if isinstance(extraction_config, str):
        extraction_config = json.loads(extraction_config)
    
    print(f"Current status: {item['status']}")
    print(f"Upload ID: {item['upload_id']}")
    
    # Load field schemas
    print("\n📥 Loading field schemas...")
    structure_fields = load_field_schema('ui_schema_structure_v1.json')
    products_fields = load_field_schema('ui_schema_product_v1.json')
    details_fields = load_field_schema('ui_schema_detail_v1.json')
    
    if not all([structure_fields, products_fields, details_fields]):
        print("❌ Could not load all field schemas!")
        return
    
    # Update the extraction_config with field definitions
    print("\n🔧 Updating extraction_config with field definitions...")
    
    # Structure stage
    if 'structure' in extraction_config['stages']:
        extraction_config['stages']['structure']['fields'] = [structure_fields]
        print("✅ Added structure fields")
    
    # Products stage
    if 'products' in extraction_config['stages']:
        extraction_config['stages']['products']['fields'] = [products_fields]
        print("✅ Added products fields")
    
    # Details stage
    if 'details' in extraction_config['stages']:
        extraction_config['stages']['details']['fields'] = [details_fields]
        print("✅ Added details fields")
    
    # Remove visual stage (not needed)
    if 'visual' in extraction_config['stages']:
        del extraction_config['stages']['visual']
        print("✅ Removed visual stage (visual feedback happens within products stage)")
    
    # Fix model IDs to match backend
    print("\n🔧 Fixing model IDs...")
    
    # Update stage_models to use valid model IDs
    model_mapping = {
        "gpt-4.1": "gpt-4o",
        "claude-3-5-sonnet-v2": "claude-3-sonnet",
        "gemini-2.5-pro": "gemini-2.0-flash-exp"
    }
    
    for stage, models in extraction_config.get('stage_models', {}).items():
        fixed_models = []
        for model in models:
            fixed_model = model_mapping.get(model, model)
            if fixed_model not in fixed_models:  # Avoid duplicates
                fixed_models.append(fixed_model)
        extraction_config['stage_models'][stage] = fixed_models
    
    print("✅ Fixed model IDs")
    
    # Update the queue item
    print("\n💾 Saving updated configuration...")
    
    update_result = supabase.table("ai_extraction_queue").update({
        "extraction_config": extraction_config,
        "status": "pending",  # Reset to pending
        "error_message": None,  # Clear error
        "failed_at": None,
        "started_at": None,
        "completed_at": None
    }).eq("id", 9).execute()
    
    if update_result.data:
        print("✅ Queue item 9 updated successfully!")
        print("\n📋 Updated configuration:")
        print(f"  - Stages: {list(extraction_config['stages'].keys())}")
        for stage, config in extraction_config['stages'].items():
            field_count = len(config.get('fields', []))
            models = extraction_config['stage_models'].get(stage, [])
            print(f"  - {stage}: {field_count} field groups, models: {models}")
    else:
        print("❌ Failed to update queue item 9!")

if __name__ == "__main__":
    fix_queue_item_9()