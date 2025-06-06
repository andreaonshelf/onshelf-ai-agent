import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=== CHECKING PRODUCT V1 PROMPT FIELDS STRUCTURE ===")
try:
    # Query prompt_templates for Product v1
    result = supabase.table('prompt_templates').select('*').ilike('name', '%Product%v1%').execute()
    
    if result.data:
        print(f"\nFound {len(result.data)} Product v1 prompts\n")
        
        for prompt in result.data:
            print(f"Prompt: {prompt.get('name', 'No name')}")
            print(f"  Template ID: {prompt.get('template_id', 'N/A')}")
            print(f"  Prompt Type: {prompt.get('prompt_type', 'N/A')}")
            print(f"  Stage Type: {prompt.get('stage_type', 'N/A')}")
            
            # Check the fields column
            if 'fields' in prompt and prompt['fields'] is not None:
                fields_data = prompt['fields']
                print(f"\n  Fields column type: {type(fields_data)}")
                
                # Print raw data
                print(f"\n  Raw fields data:")
                if isinstance(fields_data, str):
                    print(f"    String length: {len(fields_data)}")
                    print(f"    First 500 chars: {fields_data[:500]}")
                    
                    # Try to parse as JSON
                    try:
                        parsed = json.loads(fields_data)
                        print(f"\n    Parsed as JSON successfully!")
                        print(f"    Type after parsing: {type(parsed)}")
                        if isinstance(parsed, list):
                            print(f"    List length: {len(parsed)}")
                            print(f"    First item: {json.dumps(parsed[0] if parsed else 'Empty list', indent=2)}")
                        elif isinstance(parsed, dict):
                            print(f"    Dict keys: {list(parsed.keys())}")
                            print(f"    Sample: {json.dumps(dict(list(parsed.items())[:2]), indent=2)}")
                    except json.JSONDecodeError as e:
                        print(f"    Failed to parse as JSON: {e}")
                        
                elif isinstance(fields_data, list):
                    print(f"    Already a list with {len(fields_data)} items")
                    if fields_data:
                        print(f"    First item type: {type(fields_data[0])}")
                        print(f"    First item: {json.dumps(fields_data[0], indent=2)}")
                        
                        # Check for problematic nested structures
                        def check_depth(item, current_depth=0, max_depth=0, path=[]):
                            if current_depth > max_depth:
                                max_depth = current_depth
                            
                            if isinstance(item, dict):
                                for key, value in item.items():
                                    if key == 'nested_fields' and isinstance(value, list):
                                        for nested in value:
                                            max_depth = max(max_depth, check_depth(nested, current_depth + 1, max_depth, path + [item.get('name', 'unnamed')]))
                            elif isinstance(item, list):
                                for sub_item in item:
                                    max_depth = max(max_depth, check_depth(sub_item, current_depth, max_depth, path))
                            
                            return max_depth
                        
                        max_nesting = check_depth(fields_data)
                        print(f"\n    Maximum nesting depth: {max_nesting}")
                        
                elif isinstance(fields_data, dict):
                    print(f"    Dictionary with keys: {list(fields_data.keys())}")
                    print(f"    Sample: {json.dumps(dict(list(fields_data.items())[:2]), indent=2)}")
                else:
                    print(f"    Unexpected type: {type(fields_data)}")
                    print(f"    Value: {fields_data}")
            else:
                print("  Fields column is NULL or missing")
            
            print("\n" + "="*80 + "\n")
            
    else:
        print("No Product v1 prompts found")
        
    # Also check if there are any prompts with 'product' in template_id
    print("\n=== CHECKING BY TEMPLATE_ID ===")
    result2 = supabase.table('prompt_templates').select('template_id, name, fields').ilike('template_id', '%product%v1%').execute()
    
    if result2.data:
        print(f"\nFound {len(result2.data)} prompts with 'product' in template_id")
        for prompt in result2.data:
            print(f"  - {prompt['template_id']} ({prompt.get('name', 'No name')})")
            if prompt.get('fields'):
                print(f"    Has fields: {type(prompt['fields'])}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()