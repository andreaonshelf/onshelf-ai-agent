#!/usr/bin/env python3
"""Check extraction_results table schema"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

print("=" * 80)
print("CHECKING EXTRACTION_RESULTS SCHEMA")
print("=" * 80)

# Get one row to see columns
response = supabase.table("extraction_results").select("*").limit(1).execute()
if response.data and len(response.data) > 0:
    columns = list(response.data[0].keys())
    print(f"\nColumns in extraction_results: {', '.join(sorted(columns))}")
    
    print("\n\nSample row:")
    for key, value in response.data[0].items():
        if isinstance(value, str) and len(value) > 100:
            value = value[:100] + "..."
        print(f"  {key}: {value}")
else:
    print("No data in extraction_results table")

# Check for recent extraction results
print("\n\nRECENT EXTRACTION RESULTS (last 10):")
print("-" * 60)
response = supabase.table("extraction_results").select("*").order("created_at", desc=True).limit(10).execute()
if response.data:
    for idx, result in enumerate(response.data):
        print(f"\nResult {idx + 1}:")
        print(f"  ID: {result.get('result_id')}")
        print(f"  Upload ID: {result.get('upload_id')}")
        print(f"  Media ID: {result.get('media_file_id') or result.get('media_id')}")  
        print(f"  System: {result.get('system_type')}")
        print(f"  Stage: {result.get('stage')}")
        print(f"  Status: {result.get('status')}")
        print(f"  Created: {result.get('created_at')}")
        if result.get('error_details'):
            print(f"  Error: {str(result.get('error_details'))[:100]}...")