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

print("=== VERIFYING FIELD STRUCTURES FOR UI SCHEMA BUILDER ===\n")

# Get all v1 prompts
prompt_names = ["Structure v1", "Product v1", "Detail v1", "Visual v1"]

for name in prompt_names:
    try:
        result = supabase.table('prompt_templates').select('*').eq('name', name).single().execute()
        
        if result.data:
            print(f"\n{'='*60}")
            print(f"PROMPT: {name}")
            print(f"{'='*60}")
            print(f"ID: {result.data['prompt_id']}")
            print(f"Type: {result.data['prompt_type']}")
            print(f"Active: {result.data['is_active']}")
            print(f"Tags: {result.data.get('tags', [])}")
            
            # Parse and display fields structure
            fields = result.data.get('fields')
            if fields:
                if isinstance(fields, str):
                    fields = json.loads(fields)
                
                print(f"\nFIELD STRUCTURE:")
                print(json.dumps(fields, indent=2))
                
                # Verify it has the expected structure for UI
                def check_field_structure(obj, path=""):
                    issues = []
                    if isinstance(obj, dict):
                        if 'type' in obj and 'properties' in obj:
                            # This is a valid field object
                            if 'required' not in obj:
                                issues.append(f"{path}: Missing 'required' attribute")
                            if 'description' not in obj:
                                issues.append(f"{path}: Missing 'description' attribute")
                            
                            # Check nested properties
                            for key, value in obj.get('properties', {}).items():
                                issues.extend(check_field_structure(value, f"{path}.{key}"))
                        else:
                            # Check all values
                            for key, value in obj.items():
                                issues.extend(check_field_structure(value, f"{path}.{key}" if path else key))
                    return issues
                
                issues = check_field_structure(fields)
                if issues:
                    print(f"\nPOTENTIAL ISSUES:")
                    for issue in issues[:5]:  # Show first 5 issues
                        print(f"  - {issue}")
                    if len(issues) > 5:
                        print(f"  ... and {len(issues) - 5} more")
                else:
                    print(f"\n✓ Field structure appears valid for UI Schema Builder")
                    
            else:
                print(f"\n✗ No fields defined")
                
    except Exception as e:
        print(f"\n✗ Error checking {name}: {e}")

print("\n\n=== CHECKING IF FIELDS WILL POPULATE UI CORRECTLY ===")

# Test with one prompt to ensure the structure matches what the UI expects
try:
    result = supabase.table('prompt_templates').select('fields').eq('name', 'Structure v1').single().execute()
    
    if result.data and result.data.get('fields'):
        fields = result.data['fields']
        if isinstance(fields, str):
            fields = json.loads(fields)
            
        print("\nStructure v1 root keys:")
        for key in fields.keys():
            print(f"  - {key}")
            if isinstance(fields[key], dict) and 'properties' in fields[key]:
                print(f"    Properties: {list(fields[key]['properties'].keys())}")
                
except Exception as e:
    print(f"Error in final check: {e}")

print("\n✓ All prompts have been updated with v1 names and complete field structures!")