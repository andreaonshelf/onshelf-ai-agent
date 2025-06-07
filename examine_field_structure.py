#!/usr/bin/env python3
"""Examine the exact field structure in extraction_config."""

import os
import json
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("EXAMINING FIELD STRUCTURE IN EXTRACTION CONFIG")
print("=" * 80)

# Get queue item 8 which has fields
result = supabase.table('ai_extraction_queue').select('*').eq('id', 8).single().execute()

if result.data:
    item = result.data
    extraction_config = item.get('extraction_config')
    
    if isinstance(extraction_config, str):
        extraction_config = json.loads(extraction_config)
    
    print(f"Queue ID: {item['id']}")
    print(f"Status: {item['status']}")
    print(f"\nExtraction Config Structure:")
    print(json.dumps(extraction_config, indent=2))
    
    # Now trace how this should be used
    print("\n\n" + "=" * 80)
    print("HOW FIELDS SHOULD BE USED:")
    print("=" * 80)
    
    if 'stages' in extraction_config:
        for stage_id, stage_config in extraction_config['stages'].items():
            print(f"\nStage: {stage_id}")
            
            if 'fields' in stage_config and isinstance(stage_config['fields'], list):
                fields = stage_config['fields']
                print(f"  Fields: {len(fields)} field definitions")
                
                # The fields are in UI schema format
                # They need to be converted to Pydantic model format
                print("\n  Field structure (UI Schema format):")
                for field in fields:
                    print(f"    - {field.get('name')} ({field.get('type')})")
                    if 'nested_fields' in field and field['nested_fields']:
                        for nested in field['nested_fields']:
                            print(f"      - {nested.get('name')} ({nested.get('type')})")
                
                print("\n  These fields should be used to:")
                print("  1. Build dynamic Pydantic models")
                print("  2. Pass to extraction engine as output_schema")
                print("  3. Structure the extraction results")
else:
    print("Could not find queue item 8")