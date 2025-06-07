#!/usr/bin/env python3
"""Test downloading images from Supabase storage"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Test with one of the image paths
test_path = "uploads/upload-1748342011996-y1y6yk/images/1748342026567-40h72dh4-4211163-1748281153000.jpeg"

print("=" * 80)
print("TESTING IMAGE DOWNLOAD")
print("=" * 80)

print(f"\nTesting download of: {test_path}")

try:
    # Try to download the image
    image_data = supabase.storage.from_("retail-captures").download(test_path)
    print(f"✅ Successfully downloaded image: {len(image_data)} bytes ({len(image_data)/1024/1024:.2f} MB)")
    
    # Save first few bytes to verify it's an image
    if image_data[:2] == b'\xff\xd8':
        print("✅ File starts with JPEG header (FFD8)")
    elif image_data[:8] == b'\x89PNG\r\n\x1a\n':
        print("✅ File starts with PNG header")
    else:
        print(f"⚠️  Unknown file header: {image_data[:10].hex()}")
        
except Exception as e:
    print(f"❌ Failed to download image: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try listing files in the bucket
    print("\nTrying to list files in the upload folder:")
    try:
        folder_path = "uploads/upload-1748342011996-y1y6yk/"
        files = supabase.storage.from_("retail-captures").list(folder_path)
        print(f"Found {len(files)} items in {folder_path}")
        for f in files[:5]:  # Show first 5
            print(f"  - {f['name']} (id: {f.get('id')})")
    except Exception as list_error:
        print(f"Failed to list files: {list_error}")