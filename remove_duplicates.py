#!/usr/bin/env python3
"""
Remove duplicate fields from the Product v1 structure
"""

import json
import os
from supabase import create_client, Client

def remove_duplicates_from_fields(fields, seen_at_level=None):
    """Remove duplicate fields recursively"""
    if seen_at_level is None:
        seen_at_level = set()
    
    clean_fields = []
    local_seen = set()
    
    for field in fields:
        field_name = field.get('name')
        
        # Skip if we've seen this field name at this level
        if field_name in local_seen:
            print(f"Removing duplicate field: {field_name}")
            continue
            
        local_seen.add(field_name)
        
        # Clean the field
        clean_field = field.copy()
        
        # Recursively clean nested fields
        if 'nested_fields' in field and field['nested_fields']:
            clean_field['nested_fields'] = remove_duplicates_from_fields(
                field['nested_fields'], 
                seen_at_level.copy()
            )
        
        clean_fields.append(clean_field)
    
    return clean_fields

# Get current Product v1 from database
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

# Get current fields
try:
    result = supabase.table('prompt_templates').select('fields').eq('name', 'Product v1').execute()
    current_fields = json.loads(result.data[0]['fields']) if result.data else []
    
    print(f"Current structure has {len(current_fields)} top-level fields")
    
    # Remove duplicates
    clean_fields = remove_duplicates_from_fields(current_fields)
    
    print(f"After cleaning: {len(clean_fields)} top-level fields")
    
    # Save clean version
    with open('product_v1_no_duplicates_final.json', 'w') as f:
        json.dump(clean_fields, f, indent=2)
    
    # Update database
    update_result = supabase.table('prompt_templates').update({
        'fields': json.dumps(clean_fields)
    }).eq('name', 'Product v1').execute()
    
    print("✓ Updated Product v1 with duplicates removed")
    
except Exception as e:
    print(f"Error: {e}")