#!/usr/bin/env python3
"""Check details of failed queue items"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

print("=" * 80)
print("CHECKING FAILED QUEUE ITEMS")
print("=" * 80)

# Get the failed queue item for our upload
queue_id = 9  # From previous output
response = supabase.table("ai_extraction_queue").select("*").eq("id", queue_id).execute()

if response.data:
    item = response.data[0]
    print(f"\nQueue Item ID: {item.get('id')}")
    print(f"Upload ID: {item.get('upload_id')}")
    print(f"Status: {item.get('status')}")
    print(f"System: {item.get('current_extraction_system')}")
    print(f"Created: {item.get('created_at')}")
    print(f"Started: {item.get('started_at')}")
    print(f"Failed: {item.get('failed_at')}")
    
    print("\n\nERROR MESSAGE:")
    print("-" * 60)
    error = item.get('error_message')
    if error:
        # Try to parse as JSON first
        try:
            if isinstance(error, str) and (error.startswith('{') or error.startswith('[')):
                error_obj = json.loads(error)
                print(json.dumps(error_obj, indent=2))
            else:
                print(error)
        except:
            print(error)
    
    print("\n\nEXTRACTION CONFIG:")
    print("-" * 60)
    config = item.get('extraction_config')
    if config:
        try:
            if isinstance(config, str):
                config = json.loads(config)
            print(json.dumps(config, indent=2))
        except:
            print(config)
    
    print("\n\nMODEL CONFIG:")
    print("-" * 60)
    model_config = item.get('model_config')
    if model_config:
        try:
            if isinstance(model_config, str):
                model_config = json.loads(model_config)
            print(json.dumps(model_config, indent=2))
        except:
            print(model_config)
    
    print("\n\nREADY MEDIA ID:")
    print("-" * 60)
    print(f"Ready Media ID: {item.get('ready_media_id')}")
    
    # Check if media exists
    if item.get('ready_media_id'):
        media_response = supabase.table("media_files").select("*").eq("media_id", item.get('ready_media_id')).execute()
        if media_response.data:
            media = media_response.data[0]
            print(f"\nMedia file exists:")
            print(f"  File Path: {media.get('file_path')}")
            print(f"  Status: {media.get('status')}")
        else:
            print("\n❌ Media file NOT FOUND in media_files table!")

# Also check recent failed items to see if there's a pattern
print("\n\n" + "=" * 80)
print("CHECKING ALL FAILED ITEMS FOR PATTERNS")
print("=" * 80)

response = supabase.table("ai_extraction_queue").select("*").eq("status", "failed").order("failed_at", desc=True).limit(5).execute()
if response.data:
    for idx, item in enumerate(response.data):
        print(f"\n{idx + 1}. Queue ID: {item.get('id')} | Upload: {item.get('upload_id')}")
        print(f"   System: {item.get('current_extraction_system')}")
        print(f"   Error: {str(item.get('error_message'))[:100]}...")
        print(f"   Ready Media: {item.get('ready_media_id')}")