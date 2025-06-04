import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Dict, Any, List

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


def convert_field_to_json_schema(field: Dict[str, Any]) -> Dict[str, Any]:
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


def convert_fields_array_to_json_schema(fields: List[Dict[str, Any]]) -> Dict[str, Any]:
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


def main():
    try:
        print("=== CONVERTING FIELD DEFINITIONS TO JSON SCHEMA ===\n")
        
        # First, check if field_schema column exists
        print("Checking if field_schema column exists...")
        
        # Get all prompts with fields
        response = supabase.table('prompt_templates').select(
            'template_id, name, fields'
        ).not_.is_('fields', 'null').execute()
        
        if not response.data:
            print("No prompts with fields found!")
            return
        
        print(f"Found {len(response.data)} prompts with field definitions\n")
        
        # Try to add field_schema column if it doesn't exist
        print("Adding field_schema column if it doesn't exist...")
        try:
            # This will fail if column already exists, which is fine
            supabase.rpc('query', {
                'query': 'ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS field_schema JSONB'
            }).execute()
            print("✓ field_schema column added or already exists")
        except:
            print("Note: Could not add field_schema column via RPC. It may already exist or require direct SQL access.")
        
        # Convert each prompt's fields to JSON Schema
        updates = []
        for prompt in response.data:
            if prompt['fields'] and isinstance(prompt['fields'], list) and len(prompt['fields']) > 0:
                print(f"\nConverting: {prompt['name']}")
                
                # Convert fields to JSON Schema
                json_schema = convert_fields_array_to_json_schema(prompt['fields'])
                
                if json_schema:
                    print(f"✓ Converted to JSON Schema with {len(json_schema['properties'])} properties")
                    print(f"  Properties: {', '.join(json_schema['properties'].keys())}")
                    
                    updates.append({
                        'template_id': prompt['template_id'],
                        'name': prompt['name'],
                        'json_schema': json_schema
                    })
        
        # Show the SQL updates needed
        print("\n=== SQL UPDATES NEEDED ===\n")
        print("-- First ensure the column exists:")
        print("ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS field_schema JSONB;\n")
        
        print("-- Then update each prompt with its JSON Schema:")
        for update in updates:
            schema_str = json.dumps(update['json_schema'], indent=2)
            # Escape single quotes for SQL
            schema_str = schema_str.replace("'", "''")
            
            print(f"-- Update {update['name']}")
            print(f"UPDATE prompt_templates")
            print(f"SET field_schema = '{schema_str}'::jsonb")
            print(f"WHERE template_id = '{update['template_id']}';")
            print()
        
        # Save to SQL file
        with open('update_field_schemas.sql', 'w') as f:
            f.write("-- Add field_schema column if it doesn't exist\n")
            f.write("ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS field_schema JSONB;\n\n")
            
            f.write("-- Update each prompt with its JSON Schema\n")
            for update in updates:
                schema_str = json.dumps(update['json_schema'], indent=2)
                schema_str = schema_str.replace("'", "''")
                
                f.write(f"-- Update {update['name']}\n")
                f.write(f"UPDATE prompt_templates\n")
                f.write(f"SET field_schema = '{schema_str}'::jsonb\n")
                f.write(f"WHERE template_id = '{update['template_id']}';\n\n")
        
        print(f"\n✓ SQL updates saved to: update_field_schemas.sql")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()