#!/usr/bin/env python3
"""Verify the current state of prompt_templates table"""

import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY required")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("=== Verifying prompt_templates table state ===\n")

# Try different column names to see what works
test_data_variants = [
    {
        "name": "prompt_text",
        "data": {
            "template_id": "test_text_col",
            "prompt_type": "test",
            "model_type": "test",
            "prompt_version": "1.0",
            "prompt_text": "test content",
            "is_active": False
        }
    },
    {
        "name": "prompt_content",
        "data": {
            "template_id": "test_content_col",
            "prompt_type": "test",
            "model_type": "test", 
            "prompt_version": "1.0",
            "prompt_content": "test content",
            "is_active": False
        }
    }
]

successful_variant = None

for variant in test_data_variants:
    print(f"Testing with column: {variant['name']}")
    try:
        result = supabase.table("prompt_templates").insert(variant['data']).execute()
        if result.data:
            print(f"  ✓ Success! Table uses '{variant['name']}' column")
            successful_variant = variant['name']
            
            # Get the structure
            print(f"\n  Available columns:")
            for key in sorted(result.data[0].keys()):
                print(f"    - {key}")
            
            # Clean up
            prompt_id = result.data[0]['prompt_id']
            supabase.table("prompt_templates").delete().eq("prompt_id", prompt_id).execute()
            break
    except Exception as e:
        error_msg = str(e)
        if "column" in error_msg and "does not exist" in error_msg:
            print(f"  ✗ Column '{variant['name']}' does not exist")
        else:
            print(f"  ✗ Error: {error_msg}")

if successful_variant:
    print(f"\n=== Recommendation ===")
    print(f"The prompt_templates table uses '{successful_variant}' for storing prompts.")
    print(f"\nTo fix the issue:")
    print(f"1. The API is correctly detecting and using the right column")
    print(f"2. Make sure the frontend is sending the correct data format")
    print(f"3. Check the browser console for any JavaScript errors")
else:
    print("\n=== ERROR ===")
    print("Could not determine the correct column structure!")
    print("The table might need migration or there might be permission issues.")