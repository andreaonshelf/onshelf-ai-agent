import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get Supabase URL and key
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)
print("Connected to Supabase")

# Since we can't directly query information_schema via Supabase client,
# let's do a practical check by inserting a test prompt and seeing what works

print("\n=== TESTING ACTUAL SCHEMA ===")

# First, let's try to query all data from prompt_templates
try:
    result = supabase.table('prompt_templates').select("*").limit(1).execute()
    if result.data and len(result.data) > 0:
        print("\nColumns found in prompt_templates:")
        for key in result.data[0].keys():
            print(f"  - {key}")
    else:
        print("\nNo data in prompt_templates table, trying to insert test data...")
        
        # Try different insert patterns to see what works
        test_inserts = [
            # Pattern 1: New schema (from create_prompt_templates_table.sql)
            {
                "name": "Test Prompt New Schema",
                "description": "Testing new schema",
                "prompt_text": "Test prompt content",
                "fields": [],
                "stage_type": "products",
                "tags": ["test"],
                "is_default": False,
                "usage_count": 0
            },
            # Pattern 2: Old schema (from database_schema.sql)
            {
                "template_id": "test_old_schema",
                "prompt_type": "structure",
                "model_type": "gpt4o",
                "prompt_version": "1.0",
                "prompt_content": "Test prompt content",
                "performance_score": 0.0,
                "usage_count": 0,
                "correction_rate": 0.0,
                "is_active": False,
                "created_from_feedback": False
            },
            # Pattern 3: Mixed schema (from alter_prompt_templates_table.sql)
            {
                "template_id": "test_mixed_schema",
                "prompt_type": "structure",
                "model_type": "gpt4o",
                "prompt_version": "1.0",
                "prompt_content": "Test prompt content",
                "name": "Test Mixed Schema",
                "description": "Testing mixed schema",
                "field_definitions": [],
                "is_user_created": False,
                "tags": ["test"]
            },
            # Pattern 4: Minimal new schema
            {
                "name": "Test Minimal",
                "prompt_text": "Test prompt",
                "stage_type": "products"
            },
            # Pattern 5: Alternative naming
            {
                "name": "Test Alternative",
                "content": "Test prompt content",
                "prompt_type": "structure",
                "system_name": "custom_consensus"
            }
        ]
        
        for i, test_data in enumerate(test_inserts):
            try:
                print(f"\nTrying insert pattern {i+1}: {list(test_data.keys())}")
                insert_result = supabase.table('prompt_templates').insert(test_data).execute()
                print(f"✓ SUCCESS with pattern {i+1}!")
                print(f"  Inserted data keys: {list(insert_result.data[0].keys())}")
                
                # Delete the test record
                if 'id' in insert_result.data[0]:
                    supabase.table('prompt_templates').delete().eq('id', insert_result.data[0]['id']).execute()
                elif 'prompt_id' in insert_result.data[0]:
                    supabase.table('prompt_templates').delete().eq('prompt_id', insert_result.data[0]['prompt_id']).execute()
                
                break
                
            except Exception as e:
                print(f"✗ Failed with pattern {i+1}: {str(e)}")
                if "column" in str(e).lower():
                    # Extract column name from error
                    error_str = str(e)
                    if "column" in error_str and "does not exist" in error_str:
                        print(f"  Missing column mentioned in error")

except Exception as e:
    print(f"Error querying prompt_templates: {str(e)}")

# Now let's check what prompts exist by trying different query patterns
print("\n=== CHECKING EXISTING PROMPTS ===")

query_patterns = [
    # Query by different column names
    ("name", "name"),
    ("template_id", "template_id"),
    ("prompt_type", "prompt_type"),
    ("stage_type", "stage_type"),
    ("system_name", "system_name")
]

for col_name, col_alias in query_patterns:
    try:
        result = supabase.table('prompt_templates').select(f"{col_name}").limit(5).execute()
        if result.data:
            print(f"\n✓ Column '{col_name}' exists. Sample values:")
            for row in result.data[:3]:
                print(f"  - {row.get(col_name)}")
    except Exception as e:
        if "column" in str(e).lower() and "does not exist" in str(e).lower():
            print(f"\n✗ Column '{col_name}' does not exist")

print("\n✅ Schema investigation complete")