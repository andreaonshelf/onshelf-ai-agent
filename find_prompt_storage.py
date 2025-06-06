#!/usr/bin/env python3
"""Find where prompts should be saved"""

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

print("=== Looking for prompt storage options ===\n")

# Check prompt_templates table structure
print("1. Checking prompt_templates table:")
try:
    result = supabase.table("prompt_templates").select("*").limit(1).execute()
    if result.data:
        print("  Columns:")
        for key in result.data[0].keys():
            print(f"    - {key}")
        
        # Check if it has the fields we need
        required_fields = ['name', 'stage_type', 'fields']
        has_fields = all(field in result.data[0].keys() for field in required_fields)
        print(f"\n  Has required fields (name, stage_type, fields): {has_fields}")
        
        # Try to insert a test prompt
        print("\n  Testing insert capability...")
        test_data = {
            "template_id": f"user_test_{int(os.urandom(4).hex(), 16)}",
            "prompt_type": "products",
            "model_type": "all",
            "prompt_version": "1.0",
            "prompt_content": "Test prompt content",
            "name": "Test User Prompt",
            "stage_type": "products",
            "fields": [{"name": "test", "type": "string"}],
            "is_active": True,
            "created_at": "2025-05-28T10:00:00Z"
        }
        
        try:
            insert_result = supabase.table("prompt_templates").insert(test_data).execute()
            if insert_result.data:
                print("  ✓ Can insert prompts!")
                prompt_id = insert_result.data[0]['prompt_id']
                # Clean up
                supabase.table("prompt_templates").delete().eq("prompt_id", prompt_id).execute()
                print("  ✓ Test prompt deleted")
            else:
                print("  ✗ Insert returned no data")
        except Exception as e:
            print(f"  ✗ Cannot insert: {str(e)}")
            
except Exception as e:
    print(f"  Error: {str(e)}")

# Check for other potential tables
print("\n2. Checking for other prompt-related tables:")
potential_tables = [
    'saved_prompts', 'user_prompts', 'custom_prompts', 
    'extraction_prompts', 'prompt_history', 'prompt_versions'
]

for table in potential_tables:
    try:
        result = supabase.table(table).select("*").limit(1).execute()
        print(f"  ✓ Table '{table}' exists")
    except Exception as e:
        if "does not exist" in str(e):
            pass  # Expected
        else:
            print(f"  ? Table '{table}': {str(e)}")

print("\n=== Recommendation ===")
print("Based on the analysis, we should:")
print("1. Use the prompt_templates table for saving prompts")
print("2. Ensure we include all required fields when saving")
print("3. The prompt_library table needs to be created in the database")