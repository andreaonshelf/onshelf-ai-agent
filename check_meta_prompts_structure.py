#!/usr/bin/env python3
"""Check the actual structure of meta_prompts table"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("=== Checking meta_prompts table structure ===")

try:
    # Get a sample row to see the columns
    result = supabase.table("meta_prompts").select("*").limit(1).execute()
    
    if result.data:
        print("\nColumns in meta_prompts table:")
        for key in result.data[0].keys():
            print(f"  - {key}: {type(result.data[0][key]).__name__}")
        
        print("\nSample data:")
        for key, value in result.data[0].items():
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"  {key}: {value}")
    else:
        print("No data in meta_prompts table")
        
except Exception as e:
    print(f"Error: {str(e)}")

print("\n=== Checking if meta_prompts has different structure ===")
# Try different queries to understand the table
queries = [
    ("Check if 'stage' column exists", "stage", "products"),
    ("Check if 'category' column exists", "category", "extraction"),
    ("Check if 'name' column exists", "name", "Test"),
]

for desc, col, val in queries:
    try:
        result = supabase.table("meta_prompts").select("*").eq(col, val).limit(1).execute()
        print(f"✓ {desc}: YES")
    except Exception as e:
        if "column" in str(e) and "does not exist" in str(e):
            print(f"✗ {desc}: NO")
        else:
            print(f"? {desc}: {str(e)}")