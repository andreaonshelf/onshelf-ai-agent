#!/usr/bin/env python3
"""Check media file types in the database"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Upload to check
upload_id = "upload-1748342011996-y1y6yk"

print("=" * 80)
print("CHECKING MEDIA FILE TYPES")
print("=" * 80)

# Get all media files for this upload
response = supabase.table("media_files").select("*").eq("upload_id", upload_id).execute()

if response.data:
    print(f"\nFound {len(response.data)} media files for upload {upload_id}:")
    print("\nFile types in database:")
    for media in response.data:
        print(f"\nMedia ID: {media.get('media_id')}")
        print(f"  File Path: {media.get('file_path')}")
        print(f"  File Type: '{media.get('file_type')}'")
        print(f"  Status: {media.get('status')}")
        
        # Check if it's an image based on file extension
        file_path = media.get('file_path', '')
        if any(file_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
            print(f"  -> This appears to be an IMAGE file based on extension")

# Check what unique file_type values exist
print("\n\nALL UNIQUE FILE TYPES IN DATABASE:")
print("-" * 60)
response = supabase.table("media_files").select("file_type").execute()
if response.data:
    file_types = set(item.get('file_type') for item in response.data if item.get('file_type'))
    for ft in sorted(file_types):
        print(f"  - '{ft}'")