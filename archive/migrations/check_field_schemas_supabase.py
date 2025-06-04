import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("SUPABASE_URL and SUPABASE_SERVICE_KEY required in .env file")
    exit(1)

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

try:
    print("=== CHECKING FIELD_SCHEMA CONTENT IN PROMPT_TEMPLATES ===\n")
    
    # Query all prompts with their field schemas
    response = supabase.table('prompt_templates').select(
        'template_id, name, prompt_type, stage_type, field_schema'
    ).order('name', desc=False).execute()
    
    if not response.data:
        print("No prompts found!")
    else:
        print(f"Found {len(response.data)} prompts total\n")
        
        # Group by whether they have field_schema
        with_schema = []
        without_schema = []
        
        for prompt in response.data:
            if prompt.get('field_schema'):
                with_schema.append(prompt)
            else:
                without_schema.append(prompt)
        
        # Show prompts with field schemas
        print(f"=== PROMPTS WITH FIELD_SCHEMA ({len(with_schema)}) ===\n")
        
        for prompt in with_schema:
            print(f"--- {prompt['name']} ({prompt.get('stage_type', 'N/A')}) ---")
            print(f"Template ID: {prompt['template_id']}")
            print(f"Prompt Type: {prompt['prompt_type']}")
            
            try:
                # Parse and display the schema
                if isinstance(prompt['field_schema'], str):
                    schema = json.loads(prompt['field_schema'])
                else:
                    schema = prompt['field_schema']
                
                print("Field Schema:")
                print(json.dumps(schema, indent=2))
                
                # Check if it's a valid Pydantic schema structure
                if isinstance(schema, dict):
                    if 'properties' in schema:
                        print("✓ Has 'properties' key")
                    else:
                        print("✗ Missing 'properties' key")
                    
                    if 'type' in schema and schema['type'] == 'object':
                        print("✓ Type is 'object'")
                    else:
                        print("✗ Type is not 'object'")
                    
                    if 'required' in schema:
                        print(f"✓ Has 'required' fields: {schema['required']}")
                    else:
                        print("✗ Missing 'required' key")
                else:
                    print("✗ Schema is not a dictionary!")
                
            except json.JSONDecodeError as e:
                print(f"✗ Error parsing JSON: {e}")
                print(f"Raw value: {prompt['field_schema']}")
            except Exception as e:
                print(f"✗ Unexpected error: {e}")
            
            print()
        
        # Show prompts without field schemas
        print(f"\n=== PROMPTS WITHOUT FIELD_SCHEMA ({len(without_schema)}) ===\n")
        
        for prompt in without_schema:
            print(f"- {prompt['name']} ({prompt.get('stage_type', 'N/A')}) - {prompt['prompt_type']}")
    
except Exception as e:
    print(f"Error querying database: {e}")
    import traceback
    traceback.print_exc()