#!/usr/bin/env python3
"""Check what tables exist in the database"""

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
print("CHECKING DATABASE TABLES")
print("=" * 80)

# Alternative approach - try common table names
print("\nChecking common tables:")
table_names = [
    "uploads", "media_files", "queue", "queue_items", "queue_processor",
    "extraction_queue", "processing_queue", "prompt_templates", "field_definitions",
    "extraction_config", "extraction_runs", "extraction_results"
]

for table in table_names:
    try:
        response = supabase.table(table).select("*").limit(1).execute()
        print(f"  ✓ {table} exists")
    except Exception as e:
        if "does not exist" not in str(e):
            print(f"  ? {table} - error: {str(e)[:50]}")