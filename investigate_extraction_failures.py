#!/usr/bin/env python3
"""Investigate extraction failures in detail"""

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
print("INVESTIGATING EXTRACTION FAILURES")
print("=" * 80)

# 1. Get media files for these uploads
print("\n1. MEDIA FILES FOR UPLOADS:")
print("-" * 60)
media_ids = []
for upload_id in upload_ids:
    response = supabase.table("media_files").select("*").eq("upload_id", upload_id).execute()
    if response.data:
        print(f"\nUpload {upload_id} has {len(response.data)} media files:")
        for media in response.data:
            media_id = media.get('media_id')
            media_ids.append(media_id)
            print(f"  - Media ID: {media_id}")
            print(f"    File: {media.get('file_path')}")
            print(f"    Status: {media.get('status')}")
            print(f"    Approval: {media.get('approval_status')}")
    else:
        print(f"\nNo media files found for upload: {upload_id}")

# 2. Check processing queue for these media files
print("\n\n2. PROCESSING QUEUE STATUS:")
print("-" * 60)
for media_id in media_ids:
    response = supabase.table("processing_queue").select("*").eq("media_id", media_id).execute()
    if response.data:
        for item in response.data:
            print(f"\nMedia ID: {media_id}")
            print(f"  Queue ID: {item.get('queue_id')}")
            print(f"  Process Type: {item.get('process_type')}")
            print(f"  Status: {item.get('queue_status')}")
            print(f"  Priority: {item.get('priority')}")
            print(f"  Retry Count: {item.get('retry_count')}/{item.get('max_retries')}")
            print(f"  Created: {item.get('created_at')}")
            print(f"  Updated: {item.get('updated_at')}")
    else:
        print(f"\nNo processing queue items for media: {media_id}")

# 3. Check extraction_results table
print("\n\n3. EXTRACTION RESULTS:")
print("-" * 60)
for media_id in media_ids[:3]:  # Check first 3
    response = supabase.table("extraction_results").select("*").eq("media_id", media_id).execute()
    if response.data:
        for result in response.data:
            print(f"\nMedia ID: {media_id}")
            print(f"  Result ID: {result.get('result_id')}")
            print(f"  System Type: {result.get('system_type')}")
            print(f"  Stage: {result.get('stage')}")
            print(f"  Status: {result.get('status')}")
            print(f"  Created: {result.get('created_at')}")
            
            # Check error details
            if result.get('error_details'):
                print(f"  Error Details:")
                try:
                    error = json.loads(result['error_details']) if isinstance(result['error_details'], str) else result['error_details']
                    print(f"    {json.dumps(error, indent=4)[:500]}...")
                except:
                    print(f"    {str(result['error_details'])[:500]}...")
            
            # Check extracted data
            if result.get('extracted_data'):
                print(f"  Has extracted data: Yes")
    else:
        print(f"\nNo extraction results for media: {media_id}")

# 4. Check if there are any extraction runs
print("\n\n4. EXTRACTION RUNS:")
print("-" * 60)
try:
    response = supabase.table("extraction_runs").select("*").order("created_at", desc=True).limit(5).execute()
    if response.data:
        for run in response.data:
            print(f"\nRun ID: {run.get('run_id')}")
            print(f"  Media ID: {run.get('media_id')}")
            print(f"  Status: {run.get('status')}")
            print(f"  System: {run.get('system_type')}")
            print(f"  Stage: {run.get('stage')}")
            print(f"  Created: {run.get('created_at')}")
            
            if run.get('error_message'):
                print(f"  Error: {str(run.get('error_message'))[:200]}...")
except Exception as e:
    print(f"extraction_runs table might not exist: {e}")

# 5. Check prompt templates availability
print("\n\n5. PROMPT TEMPLATES AVAILABILITY:")
print("-" * 60)
# Check for each system type and stage
systems = ['langgraph', 'custom_consensus', 'custom_consensus_visual', 'hybrid']
stages = ['visual_v1', 'structure_v1', 'product_v1', 'detail_v1', 'comparison']

for system in systems:
    print(f"\n{system}:")
    for stage in stages:
        response = supabase.table("prompt_templates").select("prompt_id, name, is_active").eq("model_type", system).eq("stage_type", stage).execute()
        if response.data:
            print(f"  {stage}: {len(response.data)} prompts ({'ACTIVE' if any(p['is_active'] for p in response.data) else 'INACTIVE'})")
        else:
            print(f"  {stage}: NO PROMPTS")

# 6. Look for recent errors in any logs
print("\n\n6. RECENT ERRORS IN SYSTEM:")
print("-" * 60)

# Check extraction_results for recent errors
response = supabase.table("extraction_results").select("*").not_.is_("error_details", "null").order("created_at", desc=True).limit(5).execute()
if response.data:
    print("\nRecent extraction errors:")
    for result in response.data:
        print(f"\n- Media: {result.get('media_id')}")
        print(f"  Stage: {result.get('stage')}")
        print(f"  System: {result.get('system_type')}")
        print(f"  Time: {result.get('created_at')}")
        if result.get('error_details'):
            try:
                error = json.loads(result['error_details']) if isinstance(result['error_details'], str) else result['error_details']
                if isinstance(error, dict) and 'message' in error:
                    print(f"  Error: {error['message'][:200]}...")
                else:
                    print(f"  Error: {str(error)[:200]}...")
            except:
                print(f"  Error: {str(result['error_details'])[:200]}...")