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

def main():
    print("=== UPDATING PROMPT TEMPLATES WITH JSON SCHEMA ===\n")
    
    # First, let's manually update each prompt that has fields
    # Get all prompts with fields
    response = supabase.table('prompt_templates').select(
        'template_id, name, fields'
    ).not_.is_('fields', 'null').execute()
    
    if not response.data:
        print("No prompts with fields found!")
        return
    
    print(f"Found {len(response.data)} prompts to update\n")
    
    # Convert and update each one
    for prompt in response.data:
        if prompt['fields'] and isinstance(prompt['fields'], list) and len(prompt['fields']) > 0:
            print(f"Updating: {prompt['name']}")
            
            # Convert fields to JSON Schema
            json_schema = convert_fields_array_to_json_schema(prompt['fields'])
            
            if json_schema:
                try:
                    # Update the prompt with the JSON schema
                    update_response = supabase.table('prompt_templates').update({
                        'field_schema': json_schema
                    }).eq('template_id', prompt['template_id']).execute()
                    
                    print(f"✓ Updated successfully")
                except Exception as e:
                    print(f"✗ Error updating: {e}")
            else:
                print(f"✗ Could not convert fields to schema")
    
    # Verify the updates
    print("\n=== VERIFYING UPDATES ===")
    
    # Check which prompts now have field_schema
    response = supabase.table('prompt_templates').select(
        'template_id, name, field_schema'
    ).not_.is_('field_schema', 'null').execute()
    
    if response.data:
        print(f"\nPrompts with field_schema: {len(response.data)}")
        for prompt in response.data:
            if prompt['field_schema']:
                schema = prompt['field_schema']
                prop_count = len(schema.get('properties', {})) if isinstance(schema, dict) else 0
                print(f"  - {prompt['name']}: {prop_count} root properties")
    else:
        print("\nNo prompts with field_schema found!")
    
    print("\n✓ Update process completed!")


def convert_field_to_json_schema(field):
    """Convert a custom field definition to JSON Schema format"""
    
    # Map custom types to JSON Schema types
    type_mapping = {
        'string': 'string',
        'integer': 'integer',
        'float': 'number',
        'boolean': 'boolean',
        'list': 'array',
        'object': 'object',
        'dict': 'object'
    }
    
    schema = {}
    
    # Set the type
    field_type = field.get('type', 'string')
    schema['type'] = type_mapping.get(field_type, field_type)
    
    # Add description
    if 'description' in field:
        schema['description'] = field['description']
    
    # Handle list/array types
    if field_type == 'list' and 'nested_fields' in field:
        # This is an array of objects
        items_schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        for nested_field in field['nested_fields']:
            prop_name = nested_field['name']
            items_schema['properties'][prop_name] = convert_field_to_json_schema(nested_field)
            if nested_field.get('required', False):
                items_schema['required'].append(prop_name)
        
        schema['items'] = items_schema
    
    elif field_type == 'list' and 'list_item_type' in field:
        # Simple array type
        item_type = field['list_item_type']
        schema['items'] = {'type': type_mapping.get(item_type, item_type)}
    
    # Handle object types
    elif field_type == 'object' and 'nested_fields' in field:
        schema['properties'] = {}
        schema['required'] = []
        
        for nested_field in field['nested_fields']:
            prop_name = nested_field['name']
            schema['properties'][prop_name] = convert_field_to_json_schema(nested_field)
            if nested_field.get('required', False):
                schema['required'].append(prop_name)
    
    # Add constraints
    if 'min_value' in field:
        schema['minimum'] = field['min_value']
    if 'max_value' in field:
        schema['maximum'] = field['max_value']
    if 'enum_values' in field:
        schema['enum'] = field['enum_values']
    
    return schema


def convert_fields_array_to_json_schema(fields):
    """Convert an array of field definitions to a complete JSON Schema"""
    
    if not fields:
        return None
    
    # Create the root schema
    schema = {
        'type': 'object',
        'properties': {},
        'required': []
    }
    
    # Process each field
    for field in fields:
        field_name = field['name']
        schema['properties'][field_name] = convert_field_to_json_schema(field)
        if field.get('required', False):
            schema['required'].append(field_name)
    
    return schema


if __name__ == "__main__":
    main()