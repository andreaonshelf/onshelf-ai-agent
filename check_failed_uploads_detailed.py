#!/usr/bin/env python3
"""Check detailed information about failed uploads"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Upload IDs to check
upload_ids = ["upload-1748280644041-qcpodl", "upload-1748342011996-y1y6yk"]

print("=" * 80)
print("INVESTIGATING FAILED UPLOADS")
print("=" * 80)

# 1. Check uploads table
print("\n1. UPLOADS TABLE:")
print("-" * 60)
for upload_id in upload_ids:
    response = supabase.table("uploads").select("*").eq("id", upload_id).execute()
    if response.data:
        for upload in response.data:
            print(f"\nUpload ID: {upload_id}")
            print(f"Status: {upload.get('status')}")
            print(f"Created: {upload.get('created_at')}")
            print(f"Updated: {upload.get('updated_at')}")
            print(f"Error: {upload.get('error_message')}")
            print(f"User: {upload.get('user_id')}")
            print(f"Processing Started: {upload.get('processing_started_at')}")
            print(f"Processing Completed: {upload.get('processing_completed_at')}")
    else:
        print(f"\nNo upload found with ID: {upload_id}")

# 2. Check media_files table
print("\n\n2. MEDIA_FILES TABLE:")
print("-" * 60)
for upload_id in upload_ids:
    response = supabase.table("media_files").select("*").eq("upload_id", upload_id).execute()
    if response.data:
        for media in response.data:
            print(f"\nMedia File for Upload: {upload_id}")
            print(f"Media ID: {media.get('id')}")
            print(f"Filename: {media.get('filename')}")
            print(f"File Path: {media.get('file_path')}")
            print(f"Status: {media.get('status')}")
            print(f"Created: {media.get('created_at')}")
            print(f"Approved: {media.get('approved_at')}")
            print(f"Approved By: {media.get('approved_by')}")
            print(f"Tags: {media.get('tags')}")
            print(f"Notes: {media.get('notes')}")
    else:
        print(f"\nNo media files found for upload: {upload_id}")

# 3. Check processing_queue table (with error messages)
print("\n\n3. PROCESSING_QUEUE TABLE:")
print("-" * 60)
for upload_id in upload_ids:
    # First try by upload_id
    response = supabase.table("processing_queue").select("*").eq("upload_id", upload_id).execute()
    if not response.data:
        # Try through media_files
        media_response = supabase.table("media_files").select("id").eq("upload_id", upload_id).execute()
        if media_response.data:
            media_id = media_response.data[0]['id']
            response = supabase.table("processing_queue").select("*").eq("media_file_id", media_id).execute()
    
    if response.data:
        for item in response.data:
            print(f"\nQueue Item for Upload: {upload_id}")
            print(f"Queue ID: {item.get('id')}")
            print(f"Media File ID: {item.get('media_file_id')}")
            print(f"Status: {item.get('status')}")
            print(f"Stage: {item.get('current_stage')}")
            print(f"Created: {item.get('created_at')}")
            print(f"Updated: {item.get('updated_at')}")
            print(f"Started: {item.get('started_at')}")
            print(f"Completed: {item.get('completed_at')}")
            print(f"Error Count: {item.get('error_count', 0)}")
            print(f"\nError Message:")
            if item.get('error_message'):
                # Try to format JSON error messages
                try:
                    error_obj = json.loads(item['error_message'])
                    print(json.dumps(error_obj, indent=2))
                except:
                    print(item.get('error_message'))
            else:
                print("No error message")
            
            # Check extraction results
            if item.get('extraction_results'):
                print(f"\nExtraction Results:")
                try:
                    results = item['extraction_results']
                    if isinstance(results, str):
                        results = json.loads(results)
                    print(json.dumps(results, indent=2)[:500] + "..." if len(json.dumps(results)) > 500 else json.dumps(results, indent=2))
                except:
                    print(item.get('extraction_results')[:500] + "..." if len(str(item.get('extraction_results'))) > 500 else item.get('extraction_results'))
    else:
        print(f"\nNo queue items found for upload: {upload_id}")

# 4. Check prompt_templates table
print("\n\n4. PROMPT_TEMPLATES TABLE:")
print("-" * 60)
response = supabase.table("prompt_templates").select("system_type, stage, count(*)").execute()
if response.data:
    print("\nAvailable prompts by system and stage:")
    # Group by system_type and stage manually
    prompt_counts = {}
    for row in response.data:
        key = f"{row.get('system_type')} - {row.get('stage')}"
        if key not in prompt_counts:
            prompt_counts[key] = 0
        prompt_counts[key] += 1
    
    for key, count in sorted(prompt_counts.items()):
        print(f"  {key}: {count} prompt(s)")

# 5. Check extraction_config table if it exists
print("\n\n5. EXTRACTION CONFIG:")
print("-" * 60)
try:
    response = supabase.table("extraction_config").select("*").execute()
    if response.data:
        for config in response.data[:3]:  # Show first 3
            print(f"\nConfig: {config.get('name')}")
            print(f"Type: {config.get('type')}")
            print(f"Active: {config.get('is_active')}")
    else:
        print("No extraction configs found")
except Exception as e:
    print(f"extraction_config table might not exist: {e}")

# 6. Check field_definitions table
print("\n\n6. FIELD_DEFINITIONS TABLE:")
print("-" * 60)
response = supabase.table("field_definitions").select("stage, count(*)").execute()
if response.data:
    print("\nField definitions by stage:")
    # Group by stage manually
    field_counts = {}
    for row in response.data:
        stage = row.get('stage', 'unknown')
        if stage not in field_counts:
            field_counts[stage] = 0
        field_counts[stage] += 1
    
    for stage, count in sorted(field_counts.items()):
        print(f"  {stage}: {count} fields")

# 7. Check recent errors in processing_queue
print("\n\n7. RECENT QUEUE ERRORS (last 5):")
print("-" * 60)
response = supabase.table("processing_queue").select("*").not_.is_("error_message", "null").order("updated_at", desc=True).limit(5).execute()
if response.data:
    for item in response.data:
        print(f"\nQueue ID: {item.get('id')}")
        print(f"Media File: {item.get('media_file_id')}")
        print(f"Updated: {item.get('updated_at')}")
        print(f"Error: {item.get('error_message')[:200] + '...' if len(str(item.get('error_message', ''))) > 200 else item.get('error_message')}")