#!/usr/bin/env python3
"""Debug queue item 9 extraction failure"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("Investigating Queue Item 9 Extraction Failure")
print("=" * 60)

# 1. Check if ai_extraction_queue table exists and get item 9
try:
    response = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()
    if response.data:
        item = response.data[0]
        print("✓ Queue Item 9 found:")
        print(f"  ID: {item.get('id')}")
        print(f"  Status: {item.get('status')}")
        print(f"  Media ID: {item.get('media_id')}")
        print(f"  System Type: {item.get('system_type')}")
        print(f"  Stage: {item.get('stage')}")
        print(f"  Priority: {item.get('priority')}")
        print(f"  Retry Count: {item.get('retry_count')}")
        print(f"  Created: {item.get('created_at')}")
        print(f"  Updated: {item.get('updated_at')}")
        
        # Check extraction_config column
        if "extraction_config" in item:
            config = item.get("extraction_config")
            print("\nExtraction Config:")
            if config:
                if isinstance(config, str):
                    try:
                        config = json.loads(config)
                    except:
                        pass
                print(json.dumps(config, indent=2))
            else:
                print("  None/Empty")
        else:
            print("\n❌ No extraction_config column found")
            
        # Show all columns
        print("\nAll columns in item:")
        for key, value in item.items():
            if key != "extraction_config":  # Already shown above
                print(f"  {key}: {value}")
                
    else:
        print("❌ Queue item 9 not found")
        
        # Check if table exists at all
        try:
            response = supabase.table("ai_extraction_queue").select("id").limit(5).execute()
            print(f"\nTable exists, showing first {len(response.data)} items:")
            for item in response.data:
                print(f"  ID: {item.get('id')}")
        except Exception as e:
            print(f"\n❌ Table might not exist: {e}")
            
except Exception as e:
    print(f"❌ Error accessing ai_extraction_queue: {e}")

# 2. Check prompt_templates for structure stage
print("\n" + "=" * 60)
print("Checking Prompt Templates for 'structure' stage")
print("=" * 60)

try:
    # Look for structure prompts
    response = supabase.table("prompt_templates").select("*").ilike("stage_type", "%structure%").execute()
    if response.data:
        print(f"✓ Found {len(response.data)} structure-related prompts:")
        for prompt in response.data:
            print(f"\n  Prompt ID: {prompt.get('prompt_id')}")
            print(f"  Name: {prompt.get('name')}")
            print(f"  Stage Type: {prompt.get('stage_type')}")
            print(f"  Model Type: {prompt.get('model_type')}")
            print(f"  Active: {prompt.get('is_active')}")
            
            # Check if it has fields
            if "fields" in prompt and prompt.get("fields"):
                fields = prompt.get("fields")
                if isinstance(fields, str):
                    try:
                        fields = json.loads(fields)
                    except:
                        pass
                print(f"  Has Fields: Yes ({len(fields) if isinstance(fields, (list, dict)) else 'unknown format'})")
            else:
                print(f"  Has Fields: No")
    else:
        print("❌ No structure-related prompts found")
        
    # Also check for structure_v1 specifically
    response = supabase.table("prompt_templates").select("*").eq("stage_type", "structure_v1").execute()
    if response.data:
        print(f"\n✓ Found {len(response.data)} structure_v1 prompts:")
        for prompt in response.data:
            print(f"  - {prompt.get('name')} (Active: {prompt.get('is_active')})")
    else:
        print("\n❌ No structure_v1 prompts found")
        
except Exception as e:
    print(f"❌ Error checking prompt_templates: {e}")

# 3. Check field_definitions table
print("\n" + "=" * 60)
print("Checking Field Definitions Table")
print("=" * 60)

try:
    response = supabase.table("field_definitions").select("*").ilike("stage", "%structure%").execute()
    if response.data:
        print(f"✓ Found {len(response.data)} structure field definitions:")
        for field_def in response.data:
            print(f"\n  Field ID: {field_def.get('field_id')}")
            print(f"  Stage: {field_def.get('stage')}")
            print(f"  Name: {field_def.get('field_name')}")
            print(f"  Type: {field_def.get('field_type')}")
            print(f"  Required: {field_def.get('is_required')}")
    else:
        print("❌ No structure field definitions found")
        
        # Check what stages do exist
        response = supabase.table("field_definitions").select("stage").execute()
        if response.data:
            stages = set(item.get("stage") for item in response.data)
            print(f"\nAvailable stages in field_definitions: {list(stages)}")
        
except Exception as e:
    print(f"❌ Error checking field_definitions: {e}")

# 4. Let's also check the media file associated with queue item 9
print("\n" + "=" * 60)
print("Checking Associated Media File")
print("=" * 60)

try:
    # First get the queue item again to get media_id
    response = supabase.table("ai_extraction_queue").select("media_id").eq("id", 9).execute()
    if response.data:
        media_id = response.data[0].get("media_id")
        print(f"Media ID for queue item 9: {media_id}")
        
        if media_id:
            # Check media file details
            response = supabase.table("media_files").select("*").eq("media_id", media_id).execute()
            if response.data:
                media = response.data[0]
                print(f"\n✓ Media file found:")
                print(f"  File Path: {media.get('file_path')}")
                print(f"  Status: {media.get('status')}")
                print(f"  Approval: {media.get('approval_status')}")
                print(f"  Upload ID: {media.get('upload_id')}")
            else:
                print(f"\n❌ Media file {media_id} not found")
    else:
        print("❌ Could not get media_id from queue item 9")
        
except Exception as e:
    print(f"❌ Error checking media file: {e}")

print("\n" + "=" * 60)
print("Investigation Complete")
print("=" * 60)