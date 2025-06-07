#!/usr/bin/env python3
"""
Check the failed extractions and their configurations
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client, Client
import json
from datetime import datetime

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL', 'https://fxyfzjaaehgbdemjnumt.supabase.co')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU')
supabase: Client = create_client(supabase_url, supabase_key)

print("Checking failed extractions...")
print("=" * 80)

# Check the two specific failed uploads
upload_ids = [
    'upload-1748280644041-qcpodl',  # Tesco Express (beverages)
    'upload-1748342011996-y1y6yk'   # Co-op Food - Greenwich - Trafalgar Road (alcoholic-drinks)
]

for upload_id in upload_ids:
    print(f"\nChecking upload: {upload_id}")
    print("-" * 40)
    
    # Get upload details
    upload = supabase.table('uploads').select('*').eq('id', upload_id).execute()
    
    if upload.data:
        item = upload.data[0]
        metadata = item.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        print(f"Status: {item.get('status')}")
        print(f"Store: {metadata.get('store_name', 'Unknown')}")
        print(f"Category: {metadata.get('category', 'Unknown')}")
        print(f"Created: {item.get('created_at')}")
        print(f"Updated: {item.get('updated_at')}")
        
        # Check for extraction configuration
        extraction_config = item.get('extraction_config')
        if extraction_config:
            if isinstance(extraction_config, str):
                try:
                    extraction_config = json.loads(extraction_config)
                except:
                    pass
            print(f"Extraction Config: {json.dumps(extraction_config, indent=2) if extraction_config else 'None'}")
        else:
            print("Extraction Config: None")
        
        # Check media files
        media_files = supabase.table('media_files').select('*').eq('upload_id', upload_id).execute()
        if media_files.data:
            print(f"Media Files: {len(media_files.data)}")
            for media in media_files.data:
                print(f"  - {media.get('media_id')}: {media.get('file_type')} - Path: {media.get('image_path', 'None')}")
        else:
            print("Media Files: None found")
        
        # Check processing queue (skip if media_id is UUID type)
        try:
            # Try to get all queue items and filter in Python
            all_queue = supabase.table('processing_queue').select('*').execute()
            if all_queue.data:
                matching_items = [q for q in all_queue.data if str(q.get('media_id', '')) == upload_id]
                if matching_items:
                    print(f"Processing Queue Items: {len(matching_items)}")
                    for queue in matching_items:
                        print(f"  - Queue ID: {queue.get('queue_id')}, Status: {queue.get('queue_status')}, Type: {queue.get('process_type')}")
                else:
                    print("Processing Queue Items: None found")
        except Exception as e:
            print(f"Error checking processing queue: {e}")
        
        # Check extraction results
        results = supabase.table('extraction_results').select('*').eq('upload_id', upload_id).execute()
        if results.data:
            print(f"Extraction Results: {len(results.data)}")
            for result in results.data:
                print(f"  - System: {result.get('system_type')}, Accuracy: {result.get('overall_accuracy')}, Created: {result.get('created_at')}")

print("\n\nChecking recent prompt template configurations...")
print("=" * 80)

# Check prompt templates to see if there are field definitions
prompt_templates = supabase.table('prompt_templates').select('*').eq('is_active', True).execute()

if prompt_templates.data:
    # Group by prompt type
    by_type = {}
    for prompt in prompt_templates.data:
        ptype = prompt.get('prompt_type', 'unknown')
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(prompt)
    
    for ptype, prompts in by_type.items():
        print(f"\n{ptype.upper()} prompts: {len(prompts)}")
        for prompt in prompts[:2]:  # Show first 2 of each type
            fields = prompt.get('fields')
            if fields:
                if isinstance(fields, str):
                    try:
                        fields = json.loads(fields)
                    except:
                        pass
                print(f"  - {prompt.get('prompt_id')}: {prompt.get('model_type')} - Fields: {len(fields) if isinstance(fields, list) else 'Invalid'}")
            else:
                print(f"  - {prompt.get('prompt_id')}: {prompt.get('model_type')} - Fields: None")

print("\n\nChecking field definitions...")
print("=" * 80)

# Check if field definitions table exists
try:
    field_defs = supabase.table('field_definitions').select('*').limit(5).execute()
    if field_defs.data:
        print(f"Field definitions found: {len(field_defs.data)} (showing first 5)")
        for field in field_defs.data:
            print(f"  - {field.get('field_name')} ({field.get('stage')}): {field.get('field_type')}")
except Exception as e:
    print(f"Error checking field definitions: {e}")