#!/usr/bin/env python3
"""
Fix Empty Field Configurations
Updates queue items and saved configurations that have empty field definitions
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemConfig
from supabase import create_client
from src.utils import logger

def load_field_definitions():
    """Load field definitions from JSON files"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    field_files = {
        'structure': 'ui_schema_structure_v1.json',
        'products': 'ui_schema_product_v1.json',
        'details': 'ui_schema_detail_v1.json',
        'visual': 'ui_schema_visual_v1.json',
        'comparison': 'ui_schema_visual_v1.json'  # comparison uses visual schema
    }
    
    field_definitions = {}
    
    for stage, filename in field_files.items():
        filepath = os.path.join(project_root, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                field_definitions[stage] = json.load(f)
            print(f"✓ Loaded {stage} fields from {filename}")
        else:
            print(f"✗ Could not find {filename}")
    
    return field_definitions

def fix_queue_items(supabase, field_definitions):
    """Fix extraction_config in queue items with empty fields"""
    print("\n=== Fixing Queue Items ===")
    
    # Get all queue items
    result = supabase.table('ai_extraction_queue').select('*').execute()
    
    if not result.data:
        print("No queue items found")
        return
    
    fixed_count = 0
    
    for item in result.data:
        item_id = item['id']
        extraction_config = item.get('extraction_config', {})
        
        if not extraction_config:
            continue
            
        stages = extraction_config.get('stages', {})
        needs_fix = False
        
        # Check if any stage has empty fields
        for stage_name, stage_config in stages.items():
            fields = stage_config.get('fields', [])
            if not fields and stage_name in field_definitions:
                # Fix empty fields
                stage_config['fields'] = [field_definitions[stage_name]]
                needs_fix = True
                print(f"  Queue item {item_id}: Fixed empty {stage_name} fields")
        
        if needs_fix:
            # Update the queue item
            try:
                supabase.table('ai_extraction_queue').update({
                    'extraction_config': extraction_config,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', item_id).execute()
                fixed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to update queue item {item_id}: {e}")
    
    print(f"\nFixed {fixed_count} queue items")

def fix_saved_configurations(supabase, field_definitions):
    """Fix saved configurations in prompt_templates table"""
    print("\n=== Fixing Saved Configurations ===")
    
    # Get all saved configurations
    result = supabase.table('prompt_templates').select('*').eq('prompt_type', 'configuration').execute()
    
    if not result.data:
        print("No saved configurations found")
        return
    
    fixed_count = 0
    
    for config in result.data:
        prompt_id = config['prompt_id']
        name = config.get('name', 'Unnamed')
        extraction_config = config.get('extraction_config', {})
        
        if not extraction_config:
            continue
            
        stages = extraction_config.get('stages', {})
        needs_fix = False
        
        # Check if any stage has empty fields
        for stage_name, stage_config in stages.items():
            fields = stage_config.get('fields', [])
            if not fields and stage_name in field_definitions:
                # Fix empty fields
                stage_config['fields'] = [field_definitions[stage_name]]
                needs_fix = True
                print(f"  Config '{name}': Fixed empty {stage_name} fields")
        
        if needs_fix:
            # Update the configuration
            try:
                supabase.table('prompt_templates').update({
                    'extraction_config': extraction_config,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('prompt_id', prompt_id).execute()
                fixed_count += 1
            except Exception as e:
                print(f"  ✗ Failed to update config '{name}': {e}")
    
    print(f"\nFixed {fixed_count} saved configurations")

def main():
    """Main function"""
    print("Empty Field Configuration Fixer")
    print("================================")
    
    # Initialize Supabase
    config = SystemConfig()
    supabase = create_client(config.supabase_url, config.supabase_service_key)
    
    # Load field definitions
    field_definitions = load_field_definitions()
    
    if not field_definitions:
        print("\n✗ Could not load any field definitions. Exiting.")
        return
    
    # Fix queue items
    fix_queue_items(supabase, field_definitions)
    
    # Fix saved configurations
    fix_saved_configurations(supabase, field_definitions)
    
    print("\n✓ Done!")

if __name__ == "__main__":
    main()