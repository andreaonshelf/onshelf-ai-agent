import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Looking for Product v1 fields in prompt_templates...")
print("="*80)

# Get all prompt templates
response = supabase.table('prompt_templates').select('*').execute()

print(f"\nTotal prompt templates: {len(response.data)}")

# Look for Product v1 or similar
product_prompts = []
for prompt in response.data:
    # Check various fields for "Product" and "v1" references
    name = str(prompt.get('name', '')).lower()
    prompt_type = str(prompt.get('prompt_type', '')).lower()
    description = str(prompt.get('description', '')).lower()
    template_text = str(prompt.get('template', '')).lower()
    prompt_text = str(prompt.get('prompt_text', '')).lower()
    
    # Look for Product v1 specifically
    if ('product' in name and 'v1' in name) or \
       ('product' in prompt_type and 'v1' in prompt_type) or \
       ('product v1' in description) or \
       ('product v1' in template_text) or \
       ('product v1' in prompt_text):
        product_prompts.append(prompt)
        continue
    
    # Also check field_definitions for Product-related content
    if prompt.get('field_definitions'):
        field_str = json.dumps(prompt['field_definitions']).lower()
        if 'product' in field_str or 'product_name' in field_str:
            product_prompts.append(prompt)

print(f"\nFound {len(product_prompts)} Product-related prompts")

# Analyze each Product prompt
for i, prompt in enumerate(product_prompts):
    print(f"\n{'='*80}")
    print(f"Prompt {i+1}:")
    print(f"  ID: {prompt.get('prompt_id')}")
    print(f"  Name: {prompt.get('name')}")
    print(f"  Type: {prompt.get('prompt_type')}")
    print(f"  Description: {prompt.get('description', 'N/A')[:100]}...")
    
    # Check if it has field_definitions
    if prompt.get('field_definitions'):
        field_defs = prompt['field_definitions']
        print(f"\n  Field Definitions ({type(field_defs).__name__}):")
        
        if isinstance(field_defs, list):
            print(f"    Total fields: {len(field_defs)}")
            
            # Analyze the structure
            field_names = []
            nested_fields = []
            
            for field in field_defs:
                if isinstance(field, dict):
                    field_name = field.get('name', 'unnamed')
                    field_names.append(field_name)
                    
                    # Check for nested structure
                    if field.get('properties') or (field.get('items') and isinstance(field.get('items'), dict) and field['items'].get('properties')):
                        nested_fields.append(field_name)
            
            print(f"    Field names: {', '.join(field_names[:10])}{' ...' if len(field_names) > 10 else ''}")
            if nested_fields:
                print(f"    Nested/Complex fields: {', '.join(nested_fields)}")
            
            # Look for duplicates
            duplicates = [name for name in field_names if field_names.count(name) > 1]
            if duplicates:
                print(f"    ⚠️  DUPLICATES FOUND: {set(duplicates)}")
            
            # Show the actual structure of first few fields
            print("\n    First 3 fields in detail:")
            for j, field in enumerate(field_defs[:3]):
                if isinstance(field, dict):
                    print(f"\n    Field {j+1}: {field.get('name', 'unnamed')}")
                    print(f"      Type: {field.get('type', 'unknown')}")
                    print(f"      Required: {field.get('required', False)}")
                    print(f"      Description: {field.get('description', 'N/A')[:60]}...")
                    
                    # Check for nested structure
                    if field.get('properties'):
                        print(f"      Properties: {list(field['properties'].keys())}")
                    elif field.get('items') and isinstance(field.get('items'), dict):
                        items = field['items']
                        if items.get('properties'):
                            print(f"      Item Properties: {list(items['properties'].keys())[:5]}...")
                            
        elif isinstance(field_defs, dict):
            print(f"    Field definitions is a dict with keys: {list(field_defs.keys())}")
        else:
            print(f"    Unexpected type for field_definitions")
    else:
        print(f"  No field_definitions")

# Now let's specifically look for the problematic parsing
print("\n" + "="*80)
print("\nAnalyzing field structure for potential parsing issues:")

for prompt in product_prompts:
    if prompt.get('field_definitions') and isinstance(prompt['field_definitions'], list):
        print(f"\nPrompt: {prompt.get('name', 'unnamed')}")
        
        # Build a complete field map
        all_fields = []
        
        def extract_fields(field_list, parent_path=""):
            for field in field_list:
                if isinstance(field, dict):
                    field_name = field.get('name', 'unnamed')
                    current_path = f"{parent_path}/{field_name}" if parent_path else field_name
                    
                    all_fields.append({
                        'path': current_path,
                        'name': field_name,
                        'type': field.get('type', 'unknown'),
                        'level': current_path.count('/')
                    })
                    
                    # Check for nested fields
                    if field.get('properties'):
                        # Object with properties
                        for prop_name, prop_def in field['properties'].items():
                            all_fields.append({
                                'path': f"{current_path}/{prop_name}",
                                'name': prop_name,
                                'type': prop_def.get('type', 'unknown') if isinstance(prop_def, dict) else 'unknown',
                                'level': current_path.count('/') + 1
                            })
                    elif field.get('items') and isinstance(field['items'], dict) and field['items'].get('properties'):
                        # Array with object items
                        for prop_name, prop_def in field['items']['properties'].items():
                            all_fields.append({
                                'path': f"{current_path}[*]/{prop_name}",
                                'name': prop_name,
                                'type': prop_def.get('type', 'unknown') if isinstance(prop_def, dict) else 'unknown',
                                'level': current_path.count('/') + 1
                            })
        
        extract_fields(prompt['field_definitions'])
        
        # Check for duplicate names at different levels
        field_name_levels = {}
        for field in all_fields:
            name = field['name']
            if name not in field_name_levels:
                field_name_levels[name] = []
            field_name_levels[name].append(field['level'])
        
        # Report duplicates at different levels
        multi_level_fields = {name: levels for name, levels in field_name_levels.items() if len(set(levels)) > 1}
        if multi_level_fields:
            print("  ⚠️  Fields appearing at multiple levels:")
            for name, levels in multi_level_fields.items():
                print(f"    - {name}: appears at levels {sorted(set(levels))}")