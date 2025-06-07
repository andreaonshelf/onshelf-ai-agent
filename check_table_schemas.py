#!/usr/bin/env python3
"""Check table schemas to understand the structure"""

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
print("CHECKING TABLE SCHEMAS")
print("=" * 80)

# Check schema of key tables
tables_to_check = ["uploads", "media_files", "processing_queue", "prompt_templates", "field_definitions"]

for table in tables_to_check:
    print(f"\n\n{table.upper()} TABLE SCHEMA:")
    print("-" * 60)
    
    try:
        # Get one row to see the columns
        response = supabase.table(table).select("*").limit(1).execute()
        if response.data and len(response.data) > 0:
            columns = list(response.data[0].keys())
            print(f"Columns: {', '.join(sorted(columns))}")
            
            # Show sample data
            print("\nSample row:")
            for key, value in response.data[0].items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value)[:100] + "..." if len(json.dumps(value)) > 100 else json.dumps(value)
                print(f"  {key}: {value}")
        else:
            print("No data in table")
            
    except Exception as e:
        print(f"Error checking {table}: {e}")

# Special check for processing_queue to understand relationships
print("\n\nPROCESSING_QUEUE RELATIONSHIPS:")
print("-" * 60)
try:
    # Get a few rows to understand the structure
    response = supabase.table("processing_queue").select("*").limit(5).execute()
    if response.data:
        print(f"Found {len(response.data)} items")
        for idx, item in enumerate(response.data):
            print(f"\nItem {idx + 1}:")
            print(f"  ID: {item.get('id')}")
            print(f"  Media File ID: {item.get('media_file_id')}")
            print(f"  Status: {item.get('status')}")
            print(f"  Stage: {item.get('current_stage')}")
            if item.get('error_message'):
                print(f"  Error: {str(item.get('error_message'))[:100]}...")
except Exception as e:
    print(f"Error: {e}")