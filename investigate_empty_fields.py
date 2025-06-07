#!/usr/bin/env python3
"""Investigate why queue item 9 has empty fields arrays."""

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
print("INVESTIGATING EMPTY FIELDS IN QUEUE ITEM 9")
print("=" * 80)

# Get queue item 9
result = supabase.table('ai_extraction_queue').select('*').eq('id', 9).single().execute()

if result.data:
    item = result.data
    upload_id = item.get('upload_id')
    
    print(f"Queue ID: {item['id']}")
    print(f"Upload ID: {upload_id}")
    print(f"Status: {item['status']}")
    
    # Check extraction_config
    extraction_config = item.get('extraction_config')
    if isinstance(extraction_config, str):
        extraction_config = json.loads(extraction_config)
    
    print("\n\nExtraction Config Stage Fields:")
    if extraction_config and 'stages' in extraction_config:
        for stage, config in extraction_config['stages'].items():
            fields = config.get('fields', [])
            print(f"  {stage}: {len(fields)} fields")
    
    # Now check the upload to see what configuration was selected
    print("\n\nChecking Upload Configuration:")
    upload_result = supabase.table('uploads').select('*').eq('id', upload_id).single().execute()
    
    if upload_result.data:
        upload = upload_result.data
        print(f"Upload Title: {upload.get('title')}")
        print(f"Configuration Type: {upload.get('configuration_type')}")
        
        # Check field_selection
        field_selection = upload.get('field_selection')
        if field_selection:
            if isinstance(field_selection, str):
                field_selection = json.loads(field_selection)
            print(f"\nField Selection from Upload:")
            print(json.dumps(field_selection, indent=2))
    
    # Check if there are any field definitions for this upload
    print("\n\nChecking Field Definitions:")
    field_defs = supabase.table('field_definitions').select('*').eq('upload_id', upload_id).execute()
    
    if field_defs.data:
        print(f"Found {len(field_defs.data)} field definitions for this upload")
        for fd in field_defs.data[:3]:  # Show first 3
            print(f"  - {fd.get('stage')}: {fd.get('name')} ({fd.get('type')})")
    else:
        print("❌ No field definitions found for this upload!")
    
    # Check if this was created before field definitions were implemented
    print("\n\nTiming Analysis:")
    print(f"Upload created: {upload.get('created_at')}")
    print(f"Queue item created: {item.get('created_at')}")
    
    # Check if any uploads have field definitions
    print("\n\nChecking if ANY uploads have field definitions:")
    any_fields = supabase.table('field_definitions').select('upload_id').limit(5).execute()
    if any_fields.data:
        print(f"Found field definitions for uploads:")
        for fd in any_fields.data:
            print(f"  - {fd.get('upload_id')}")
    else:
        print("❌ No field definitions found in the entire table!")
        
        # Check if field_definitions table exists
        print("\n\nChecking table structure:")
        # This would normally check table existence but we can infer from the query result