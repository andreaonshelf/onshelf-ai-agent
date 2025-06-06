#!/usr/bin/env python3
"""Check if prompt_templates table has the required columns"""

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

print("=== Checking prompt_templates table structure ===\n")

try:
    # Get a sample row to see the columns
    result = supabase.table("prompt_templates").select("*").limit(1).execute()
    
    if result.data:
        print("Columns in prompt_templates table:")
        columns = list(result.data[0].keys())
        for col in sorted(columns):
            print(f"  - {col}")
        
        # Check for required columns
        required_columns = ['name', 'fields', 'stage_type', 'tags', 'description']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            print(f"\nMissing columns: {missing_columns}")
            print("\nThe migration needs to be applied!")
            print("Run: psql $DATABASE_URL < archive/migrations/migrate_prompt_templates_SAFE.sql")
        else:
            print("\n✓ All required columns exist!")
    else:
        print("No data in prompt_templates table to check structure")
        print("\nTrying to describe table structure...")
        
        # Try inserting a test row to see what columns exist
        test_data = {
            "template_id": "test_structure_check",
            "prompt_type": "test",
            "model_type": "test",
            "prompt_version": "1.0",
            "prompt_content": "test",
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        try:
            result = supabase.table("prompt_templates").insert(test_data).execute()
            if result.data:
                columns = list(result.data[0].keys())
                print(f"Available columns: {sorted(columns)}")
                # Clean up
                supabase.table("prompt_templates").delete().eq("template_id", "test_structure_check").execute()
        except Exception as e:
            print(f"Could not determine structure: {e}")
        
except Exception as e:
    print(f"Error: {str(e)}")