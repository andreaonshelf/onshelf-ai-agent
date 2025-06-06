#!/usr/bin/env python3
"""
Convert JSON Schema format fields to UI field array format for all prompts
"""

import json
import os
from supabase import create_client, Client
from typing import Dict, List, Any

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    exit(1)

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

def convert_json_schema_to_ui_fields(schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert JSON Schema format to UI field array format"""
    
    if not isinstance(schema, dict):
        return schema  # Already in correct format
    
    # Check if this is JSON Schema format
    if 'type' in schema and 'properties' in schema:
        # This is JSON Schema format - convert it
        fields = []
        
        for prop_name, prop_def in schema.get('properties', {}).items():
            field = {
                'name': prop_name,
                'type': prop_def.get('type', 'string'),
                'description': prop_def.get('description', ''),
                'required': prop_name in schema.get('required', [])
            }
            
            # Handle enum/literal types
            if 'enum' in prop_def:
                field['type'] = 'literal'
                field['allowed_values'] = prop_def['enum']
            
            # Handle nested objects
            if prop_def.get('type') == 'object' and 'properties' in prop_def:
                field['nested_fields'] = convert_json_schema_to_ui_fields(prop_def)
            
            # Handle arrays
            if prop_def.get('type') == 'array':
                field['type'] = 'list'
                items = prop_def.get('items', {})
                
                if items.get('type') == 'object':
                    field['list_item_type'] = 'object'
                    field['nested_fields'] = convert_json_schema_to_ui_fields(items)
                elif 'enum' in items:
                    field['list_item_type'] = 'literal'
                    field['allowed_values'] = items['enum']
                else:
                    field['list_item_type'] = items.get('type', 'string')
            
            fields.append(field)
        
        return fields
    
    # Already in UI format
    return schema

def fix_prompt_fields():
    """Fix all prompts with incorrect field format"""
    
    # Get all prompts
    try:
        response = supabase.table('prompt_templates').select('*').execute()
        prompts = response.data
        
        print(f"Found {len(prompts)} prompts to check")
        
        fixed_count = 0
        
        for prompt in prompts:
            if not prompt.get('fields'):
                continue
                
            try:
                # Parse fields
                fields = json.loads(prompt['fields']) if isinstance(prompt['fields'], str) else prompt['fields']
                
                # Check if conversion is needed
                if isinstance(fields, dict) and 'type' in fields and 'properties' in fields:
                    print(f"\nFixing {prompt['name']} (ID: {prompt['prompt_id']})")
                    
                    # Convert to UI format
                    ui_fields = convert_json_schema_to_ui_fields(fields)
                    
                    # Update database
                    update_result = supabase.table('prompt_templates').update({
                        'fields': json.dumps(ui_fields)
                    }).eq('prompt_id', prompt['prompt_id']).execute()
                    
                    print(f"✓ Converted {prompt['name']} from JSON Schema to UI format")
                    fixed_count += 1
                    
            except Exception as e:
                print(f"✗ Error processing {prompt['name']}: {e}")
        
        print(f"\nFixed {fixed_count} prompts")
        
    except Exception as e:
        print(f"Error fetching prompts: {e}")

if __name__ == "__main__":
    fix_prompt_fields()