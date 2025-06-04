#!/usr/bin/env python3
import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Missing Supabase credentials in environment variables")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)

# First, let's check what columns exist in prompt_templates
print("Checking prompt_templates table structure...")

try:
    # Get one row to see the structure
    response = supabase.table('prompt_templates').select('*').limit(1).execute()
    
    if response.data:
        print("\nColumns in prompt_templates table:")
        for key in response.data[0].keys():
            print(f"  - {key}: {type(response.data[0][key]).__name__}")
    
    # Now let's see all the prompts and their current structure
    all_prompts = supabase.table('prompt_templates').select('*').order('prompt_type').execute()
    
    print(f"\n\nFound {len(all_prompts.data)} prompts:")
    for prompt in all_prompts.data:
        print(f"\n{'='*60}")
        print(f"Type: {prompt.get('prompt_type')}")
        print(f"Description: {prompt.get('description', 'No description')}")
        
        # Check if there's any schema-related field
        for key in prompt.keys():
            if 'schema' in key.lower() or 'pydantic' in key.lower() or 'output' in key.lower():
                print(f"{key}: {prompt[key]}")
        
        # Also check the prompt_template field for any schema info
        template = prompt.get('prompt_template', '')
        if 'pydantic' in template.lower() or 'schema' in template.lower():
            print("Note: Prompt template contains schema references")
            
except Exception as e:
    print(f"Error: {e}")