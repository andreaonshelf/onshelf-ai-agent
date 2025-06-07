#!/usr/bin/env python3
"""Check exact mismatches between database configuration and code expectations."""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

print("=" * 80)
print("CHECKING EXACT MISMATCHES BETWEEN DATABASE AND CODE")
print("=" * 80)

# 1. Check media_files table for image paths
print("\n1. MEDIA FILES - IMAGE PATHS:")
print("-" * 40)
try:
    media_response = supabase.table('media_files').select('*').limit(5).execute()
    print(f"Found {len(media_response.data)} media files")
    
    for media in media_response.data:
        print(f"\nMedia ID: {media.get('id')}")
        print(f"  File Name: {media.get('file_name')}")
        print(f"  Image Path: {media.get('image_path')}")
        print(f"  Upload ID: {media.get('upload_id')}")
        print(f"  Status: {media.get('status')}")
        
        # Check if image_path is a full URL or relative path
        path = media.get('image_path', '')
        if path.startswith('http'):
            print(f"  → Full URL detected")
        elif path.startswith('/'):
            print(f"  → Absolute path detected")
        else:
            print(f"  → Relative path detected")
            
except Exception as e:
    print(f"Error querying media_files: {e}")

# 2. Check processing_queue table for extraction_config
print("\n\n2. PROCESSING QUEUE - EXTRACTION CONFIG:")
print("-" * 40)
try:
    queue_response = supabase.table('processing_queue').select('*').limit(5).execute()
    print(f"Found {len(queue_response.data)} queue items")
    
    for item in queue_response.data:
        print(f"\nQueue ID: {item.get('id')}")
        print(f"  Media File ID: {item.get('media_file_id')}")
        print(f"  Status: {item.get('status')}")
        
        config = item.get('extraction_config')
        if config:
            print(f"  Extraction Config Type: {type(config)}")
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except:
                    pass
            
            if isinstance(config, dict):
                print(f"  Config Keys: {list(config.keys())}")
                
                # Check for stages vs prompts
                if 'stages' in config:
                    print(f"  → Has 'stages' key")
                    print(f"    Stage Keys: {list(config['stages'].keys()) if isinstance(config['stages'], dict) else 'Not a dict'}")
                if 'prompts' in config:
                    print(f"  → Has 'prompts' key")
                    print(f"    Prompt Keys: {list(config['prompts'].keys()) if isinstance(config['prompts'], dict) else 'Not a dict'}")
                
                # Check other important keys
                for key in ['model_config', 'system_type', 'iteration_count']:
                    if key in config:
                        print(f"  → Has '{key}': {config[key]}")
                        
except Exception as e:
    print(f"Error querying queue_processor: {e}")

# 3. Check prompt_templates table
print("\n\n3. PROMPT TEMPLATES:")
print("-" * 40)
try:
    prompt_response = supabase.table('prompt_templates').select('*').limit(10).execute()
    print(f"Found {len(prompt_response.data)} prompt templates")
    
    prompt_types = set()
    for prompt in prompt_response.data:
        prompt_type = prompt.get('prompt_type')
        prompt_types.add(prompt_type)
        
    print(f"Unique prompt types: {sorted(list(prompt_types))}")
    
    # Show a few examples
    for prompt in prompt_response.data[:3]:
        print(f"\nPrompt ID: {prompt.get('id')}")
        print(f"  Name: {prompt.get('name')}")
        print(f"  Type: {prompt.get('prompt_type')}")
        print(f"  Stage: {prompt.get('stage')}")
        print(f"  System Type: {prompt.get('system_type')}")
        
except Exception as e:
    print(f"Error querying prompt_templates: {e}")

# 4. Check a real extraction config from queue
print("\n\n4. DETAILED EXTRACTION CONFIG ANALYSIS:")
print("-" * 40)
try:
    # Get a recent queue item with extraction_config
    recent_queue = supabase.table('processing_queue').select('*').not_.is_('extraction_config', 'null').limit(1).execute()
    
    if recent_queue.data:
        item = recent_queue.data[0]
        config = item.get('extraction_config')
        
        if isinstance(config, str):
            config = json.loads(config)
            
        print("Full extraction_config structure:")
        print(json.dumps(config, indent=2))
        
except Exception as e:
    print(f"Error analyzing extraction config: {e}")

# 5. Check media_files with real data
print("\n\n5. MEDIA FILES WITH ACTUAL DATA:")
print("-" * 40)
try:
    # Get media files that have non-null image_path
    media_with_path = supabase.table('media_files').select('*').not_.is_('image_path', 'null').limit(5).execute()
    
    if media_with_path.data:
        print(f"Found {len(media_with_path.data)} media files with image_path")
        for media in media_with_path.data:
            print(f"\nMedia ID: {media.get('id')}")
            print(f"  Upload ID: {media.get('upload_id')}")
            print(f"  Image Path: {media.get('image_path')}")
            print(f"  File Path: {media.get('file_path')}")
            print(f"  File Name: {media.get('file_name')}")
            print(f"  File Type: {media.get('file_type')}")
            
except Exception as e:
    print(f"Error checking media files: {e}")

# 6. Check ai_extraction_queue table (system dispatcher uses this)
print("\n\n6. AI EXTRACTION QUEUE:")
print("-" * 40)
try:
    queue_items = supabase.table('ai_extraction_queue').select('*').limit(3).execute()
    
    if queue_items.data:
        print(f"Found {len(queue_items.data)} items in ai_extraction_queue")
        for item in queue_items.data:
            print(f"\nQueue Item:")
            print(f"  Upload ID: {item.get('upload_id')}")
            print(f"  Enhanced Image Path: {item.get('enhanced_image_path')}")
            print(f"  Status: {item.get('status')}")
            
except Exception as e:
    print(f"Error checking ai_extraction_queue: {e}")