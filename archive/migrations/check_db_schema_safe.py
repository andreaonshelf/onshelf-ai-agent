#!/usr/bin/env python3
"""
Check database schema with various connection methods
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Checking environment variables...")
print(f"DATABASE_URL exists: {'DATABASE_URL' in os.environ}")
print(f"SUPABASE_URL exists: {'SUPABASE_URL' in os.environ}")
print(f"SUPABASE_SERVICE_KEY exists: {'SUPABASE_SERVICE_KEY' in os.environ}")
print(f"SUPABASE_SERVICE_ROLE_KEY exists: {'SUPABASE_SERVICE_ROLE_KEY' in os.environ}")
print(f"SUPABASE_ANON_KEY exists: {'SUPABASE_ANON_KEY' in os.environ}")

# Try Supabase client first
try:
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if supabase_url and supabase_key:
        print("\nTrying Supabase client connection...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Check prompt_templates table
        print("\n=== PROMPT_TEMPLATES TABLE ===")
        try:
            result = supabase.table('prompt_templates').select('*').limit(1).execute()
            if result.data:
                print("Table exists. Sample columns:")
                for key in result.data[0].keys():
                    print(f"  - {key}")
                
                # Check if specific columns exist
                print("\nChecking for field-related columns:")
                sample = result.data[0]
                field_cols = ['fields', 'field_schema', 'field_definitions', 'instructor_fields']
                for col in field_cols:
                    if col in sample:
                        print(f"  ✓ {col} exists")
                    else:
                        print(f"  ✗ {col} not found")
            else:
                print("Table exists but is empty")
        except Exception as e:
            print(f"Error accessing prompt_templates: {e}")
        
        # Check meta_prompts table
        print("\n=== META_PROMPTS TABLE ===")
        try:
            result = supabase.table('meta_prompts').select('*').limit(1).execute()
            if result.data:
                print("Table exists. Columns:")
                for key in result.data[0].keys():
                    print(f"  - {key}")
            else:
                print("Table exists but is empty")
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                print("Table does not exist")
            else:
                print(f"Error accessing meta_prompts: {e}")
        
        # Check field_definitions table
        print("\n=== FIELD_DEFINITIONS TABLE ===")
        try:
            result = supabase.table('field_definitions').select('*').limit(1).execute()
            if result.data:
                print("Table exists. Columns:")
                for key in result.data[0].keys():
                    print(f"  - {key}")
                
                # Show sample instructor_fields
                if 'instructor_fields' in result.data[0] and result.data[0]['instructor_fields']:
                    print("\nSample instructor_fields format:")
                    print(json.dumps(result.data[0]['instructor_fields'], indent=2))
            else:
                print("Table exists but is empty")
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                print("Table does not exist")
            else:
                print(f"Error accessing field_definitions: {e}")
                
        # Check for SQL files with insert statements
        print("\n=== CHECKING SQL INSERT FILES ===")
        sql_files = [
            'insert_planogram_prompts_current_schema.sql',
            'insert_all_prompts_complete.sql',
            'insert_prompts_without_conflict.sql'
        ]
        
        for sql_file in sql_files:
            if os.path.exists(sql_file):
                print(f"\n{sql_file} exists")
                with open(sql_file, 'r') as f:
                    content = f.read()
                    # Check which column names are used in INSERT statements
                    if 'fields' in content and 'field_schema' not in content:
                        print("  Uses: fields column")
                    elif 'field_schema' in content and 'fields' not in content:
                        print("  Uses: field_schema column")
                    elif 'fields' in content and 'field_schema' in content:
                        print("  Uses: both fields and field_schema columns")
                    elif 'instructor_fields' in content:
                        print("  Uses: instructor_fields column")
                    
    else:
        print("Supabase credentials not found")
        
except ImportError:
    print("Supabase client not installed")
except Exception as e:
    print(f"Error with Supabase client: {e}")

print("\nDone!")