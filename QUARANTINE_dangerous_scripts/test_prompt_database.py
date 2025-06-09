#!/usr/bin/env python3
"""Test script to check prompt saving and retrieval from database"""

import os
import sys
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    sys.exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)

def check_tables():
    """Check which prompt-related tables exist"""
    print("\n=== Checking Tables ===")
    
    tables_to_check = ['prompt_templates', 'prompt_library', 'meta_prompts']
    
    for table in tables_to_check:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"✓ Table '{table}' exists")
        except Exception as e:
            print(f"✗ Table '{table}' error: {str(e)}")

def test_save_to_prompt_library():
    """Test saving a prompt to prompt_library table"""
    print("\n=== Testing Save to prompt_library ===")
    
    test_prompt = {
        "name": f"Test Prompt {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Test prompt for debugging",
        "prompt_text": "Extract all products from this image.",
        "fields": [
            {"name": "brand", "type": "string", "required": True},
            {"name": "price", "type": "number", "required": False}
        ],
        "stage_type": "products",
        "tags": ["test", "debug"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "is_default": False,
        "usage_count": 0
    }
    
    try:
        result = supabase.table("prompt_library").insert(test_prompt).execute()
        if result.data:
            print(f"✓ Successfully saved prompt with ID: {result.data[0]['id']}")
            return result.data[0]['id']
        else:
            print("✗ No data returned from insert")
    except Exception as e:
        print(f"✗ Failed to save: {str(e)}")
        return None

def test_fetch_prompts(stage_type):
    """Test fetching prompts for a specific stage"""
    print(f"\n=== Fetching Prompts for Stage: {stage_type} ===")
    
    # Try prompt_templates table
    print("\nFrom prompt_templates:")
    try:
        result = supabase.table("prompt_templates")\
            .select("*")\
            .eq("stage_type", stage_type)\
            .eq("is_active", True)\
            .execute()
        print(f"  Found {len(result.data)} prompts")
        for prompt in result.data[:3]:  # Show first 3
            print(f"  - {prompt.get('name', 'Unnamed')} (ID: {prompt['prompt_id']})")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    # Try prompt_library table
    print("\nFrom prompt_library:")
    try:
        result = supabase.table("prompt_library")\
            .select("*")\
            .eq("stage_type", stage_type)\
            .execute()
        print(f"  Found {len(result.data)} prompts")
        for prompt in result.data[:3]:  # Show first 3
            print(f"  - {prompt['name']} (ID: {prompt['id']})")
    except Exception as e:
        print(f"  Error: {str(e)}")
    
    # Try meta_prompts table
    print("\nFrom meta_prompts:")
    try:
        result = supabase.table("meta_prompts")\
            .select("*")\
            .eq("stage", stage_type)\
            .eq("is_active", True)\
            .execute()
        print(f"  Found {len(result.data)} prompts")
        for prompt in result.data[:3]:  # Show first 3
            print(f"  - {prompt['name']} (ID: {prompt['id']})")
    except Exception as e:
        print(f"  Error: {str(e)}")

def main():
    print("=== Prompt Database Test ===")
    
    # Check which tables exist
    check_tables()
    
    # Test saving a prompt
    prompt_id = test_save_to_prompt_library()
    
    # Test fetching prompts
    test_fetch_prompts("products")
    
    # If we saved a prompt, try to fetch it
    if prompt_id:
        print(f"\n=== Fetching Saved Prompt (ID: {prompt_id}) ===")
        try:
            result = supabase.table("prompt_library")\
                .select("*")\
                .eq("id", prompt_id)\
                .single()\
                .execute()
            print(f"✓ Successfully fetched: {result.data['name']}")
        except Exception as e:
            print(f"✗ Failed to fetch: {str(e)}")

if __name__ == "__main__":
    main()