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

# Query current prompt templates to see their schemas
try:
    response = supabase.table('prompt_templates').select('*').order('prompt_type').execute()
    
    print(f"Found {len(response.data)} prompt templates in database\n")
    
    # Display each prompt's schema
    for prompt in response.data:
        print(f"\n{'='*80}")
        print(f"Prompt Type: {prompt['prompt_type']}")
        print(f"Description: {prompt.get('description', 'No description')}")
        
        schema = prompt.get('pydantic_schema')
        if schema:
            if isinstance(schema, str):
                try:
                    schema_obj = json.loads(schema)
                    print(f"\nPydantic Schema (formatted):")
                    print(json.dumps(schema_obj, indent=2))
                except:
                    print(f"\nPydantic Schema (raw): {schema}")
            else:
                print(f"\nPydantic Schema (formatted):")
                print(json.dumps(schema, indent=2))
        else:
            print("No schema defined")
            
except Exception as e:
    print(f"Error querying database: {e}")