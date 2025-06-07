#!/usr/bin/env python3
"""Check the approval flow from media_files to queue"""

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

# Upload IDs to check
upload_ids = ["upload-1748280644041-qcpodl", "upload-1748342011996-y1y6yk"]

print("=" * 80)
print("CHECKING APPROVAL FLOW")
print("=" * 80)

# 1. Check if ai_extraction_queue table exists
print("\n1. CHECKING AI_EXTRACTION_QUEUE TABLE:")
print("-" * 60)
try:
    response = supabase.table("ai_extraction_queue").select("*").limit(1).execute()
    print("✓ ai_extraction_queue table exists")
    
    # Get column names
    if response.data:
        columns = list(response.data[0].keys())
        print(f"Columns: {', '.join(sorted(columns))}")
except Exception as e:
    print(f"✗ ai_extraction_queue table error: {e}")

# 2. Check for items related to our uploads
print("\n\n2. CHECKING QUEUE ITEMS FOR OUR UPLOADS:")
print("-" * 60)
for upload_id in upload_ids:
    try:
        response = supabase.table("ai_extraction_queue").select("*").eq("upload_id", upload_id).execute()
        if response.data:
            print(f"\nUpload {upload_id} has {len(response.data)} queue items:")
            for item in response.data:
                print(f"  Queue ID: {item.get('id')}")
                print(f"  Status: {item.get('status')}")
                print(f"  Created: {item.get('created_at')}")
                print(f"  Updated: {item.get('updated_at')}")
                print(f"  Media Count: {item.get('total_media_files')}")
                print(f"  Processing Time: {item.get('average_processing_time')}")
                print(f"  Current System: {item.get('current_extraction_system')}")
                
                if item.get('error_message'):
                    print(f"  Error: {str(item.get('error_message'))[:100]}...")
                
                if item.get('extraction_results'):
                    print(f"  Has results: Yes (data size: {len(str(item.get('extraction_results')))} chars)")
        else:
            print(f"\nNo queue items found for upload: {upload_id}")
    except Exception as e:
        print(f"\nError checking queue for {upload_id}: {e}")

# 3. Check if there's a trigger or function to create queue items
print("\n\n3. CHECKING FOR APPROVAL TRIGGERS:")
print("-" * 60)
# Check the latest approved media files
response = supabase.table("media_files").select("*").eq("approval_status", "approved").order("updated_at", desc=True).limit(5).execute()
if response.data:
    print("\nRecently approved media files:")
    for media in response.data:
        print(f"\n  Media ID: {media.get('media_id')}")
        print(f"  Upload ID: {media.get('upload_id')}")
        print(f"  Status: {media.get('status')}")
        print(f"  Approved At: {media.get('approved_at')}")
        print(f"  File: {media.get('file_path')}")

# 4. Check for any recent queue items
print("\n\n4. RECENT QUEUE ITEMS (last 5):")
print("-" * 60)
try:
    response = supabase.table("ai_extraction_queue").select("*").order("created_at", desc=True).limit(5).execute()
    if response.data:
        for item in response.data:
            print(f"\nQueue ID: {item.get('id')}")
            print(f"  Upload ID: {item.get('upload_id')}")
            print(f"  Status: {item.get('status')}")
            print(f"  Created: {item.get('created_at')}")
            print(f"  Total Files: {item.get('total_media_files')}")
    else:
        print("No items in ai_extraction_queue")
except Exception as e:
    print(f"Error: {e}")

# 5. Check if there's a mismatch in expectations
print("\n\n5. ANALYSIS:")
print("-" * 60)
print("\nKey findings:")
print("1. The UI expects to approve media files and have them appear in ai_extraction_queue")
print("2. The processing endpoint expects items in ai_extraction_queue with specific structure")
print("3. Need to check if there's a trigger or manual process to create queue items after approval")