#!/usr/bin/env python3
"""Find queue items that have extraction_config with fields."""

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
print("FINDING QUEUE ITEMS WITH EXTRACTION CONFIG")
print("=" * 80)

# Look for queue items with extraction_config
queue_items = supabase.table('ai_extraction_queue').select('*').not_.is_('extraction_config', 'null').limit(10).execute()

found_with_fields = 0

if queue_items.data:
    print(f"\nFound {len(queue_items.data)} items with extraction_config")
    
    for item in queue_items.data:
        queue_id = item['id']
        status = item.get('status')
        
        extraction_config = item.get('extraction_config')
        if isinstance(extraction_config, str):
            try:
                extraction_config = json.loads(extraction_config)
            except:
                continue
                
        if isinstance(extraction_config, dict) and 'stages' in extraction_config:
            stages = extraction_config['stages']
            has_fields = False
            
            # Check if any stage has fields
            for stage_id, stage_config in stages.items():
                if isinstance(stage_config, dict) and 'fields' in stage_config:
                    fields = stage_config['fields']
                    if fields and (isinstance(fields, list) and len(fields) > 0):
                        has_fields = True
                        break
                        
            if has_fields:
                found_with_fields += 1
                print(f"\n✓ Queue ID: {queue_id} (Status: {status})")
                print(f"  Stages: {list(stages.keys())}")
                
                for stage_id, stage_config in stages.items():
                    if isinstance(stage_config, dict) and 'fields' in stage_config:
                        fields = stage_config['fields']
                        if fields and isinstance(fields, list):
                            print(f"  {stage_id}: {len(fields)} fields defined")
                            # Show first field structure
                            if fields and isinstance(fields[0], dict):
                                first_field = fields[0]
                                print(f"    Example field structure: {list(first_field.keys())}")
                                if 'properties' in first_field:
                                    print(f"    Properties: {list(first_field['properties'].keys())}")

print(f"\n\nSummary: Found {found_with_fields} queue items with field definitions")

# Also check model_config
print("\n" + "=" * 80)
print("CHECKING MODEL_CONFIG ITEMS")
print("=" * 80)

model_config_items = supabase.table('ai_extraction_queue').select('*').not_.is_('model_config', 'null').limit(10).execute()

if model_config_items.data:
    print(f"\nFound {len(model_config_items.data)} items with model_config")
    
    for item in model_config_items.data[:3]:  # Show first 3
        queue_id = item['id']
        model_config = item.get('model_config')
        
        if isinstance(model_config, str):
            try:
                model_config = json.loads(model_config)
            except:
                continue
                
        if isinstance(model_config, dict):
            print(f"\nQueue ID: {queue_id}")
            print(f"  Model config keys: {list(model_config.keys())}")
            
            if 'stages' in model_config:
                print("  Has 'stages' key!")
                stages = model_config['stages']
                if isinstance(stages, dict):
                    for stage_id, stage_config in stages.items():
                        if isinstance(stage_config, dict) and 'fields' in stage_config:
                            print(f"    {stage_id} has fields!")