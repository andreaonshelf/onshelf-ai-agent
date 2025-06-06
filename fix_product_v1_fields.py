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

def json_schema_to_field_array(schema, parent_path=""):
    """Convert JSON schema format to field array format"""
    fields = []
    
    if isinstance(schema, dict):
        if 'properties' in schema:
            # This is an object with properties
            for prop_name, prop_schema in schema['properties'].items():
                field = {
                    'name': prop_name,
                    'type': prop_schema.get('type', 'string'),
                    'description': prop_schema.get('description', ''),
                    'required': prop_schema.get('required', False)
                }
                
                # Handle enum values
                if 'enum' in prop_schema:
                    field['allowed_values'] = prop_schema['enum']
                    field['type'] = 'enum'
                
                # Handle nested objects
                if prop_schema.get('type') == 'object' and 'properties' in prop_schema:
                    field['nested_fields'] = json_schema_to_field_array(prop_schema)
                
                # Handle arrays
                elif prop_schema.get('type') == 'array' and 'items' in prop_schema:
                    item_schema = prop_schema['items']
                    if item_schema.get('type') == 'object' and 'properties' in item_schema:
                        field['type'] = 'list'
                        field['list_item_type'] = 'object'
                        field['nested_fields'] = json_schema_to_field_array(item_schema)
                    else:
                        field['type'] = 'list'
                        field['list_item_type'] = item_schema.get('type', 'string')
                
                fields.append(field)
                
        elif len(schema) == 1:
            # If there's only one top-level key, unwrap it
            key = list(schema.keys())[0]
            return json_schema_to_field_array(schema[key])
    
    return fields

print("=== FIXING PRODUCT V1 FIELDS FORMAT ===")

try:
    # Query Product v1 prompt
    result = supabase.table('prompt_templates').select('*').eq('name', 'Product v1').execute()
    
    if result.data and len(result.data) > 0:
        prompt = result.data[0]
        print(f"\nFound Product v1 prompt: {prompt['template_id']}")
        
        # Parse the fields
        if prompt.get('fields'):
            fields_data = prompt['fields']
            if isinstance(fields_data, str):
                try:
                    parsed_schema = json.loads(fields_data)
                    print(f"\nParsed JSON schema successfully")
                    
                    # Convert to field array format
                    field_array = json_schema_to_field_array(parsed_schema)
                    print(f"\nConverted to field array with {len(field_array)} fields")
                    
                    # Print the converted structure
                    print("\nConverted field structure:")
                    print(json.dumps(field_array, indent=2))
                    
                    # Update the prompt with the new format
                    update_result = supabase.table('prompt_templates').update({
                        'fields': json.dumps(field_array)
                    }).eq('prompt_id', prompt['prompt_id']).execute()
                    
                    print(f"\nUpdated Product v1 prompt with field array format")
                    
                except json.JSONDecodeError as e:
                    print(f"Failed to parse fields as JSON: {e}")
            else:
                print("Fields are not a string, might already be in correct format")
        else:
            print("No fields found in Product v1 prompt")
    else:
        print("Product v1 prompt not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()