import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Analyzing Product v1 field structure...")
print("="*80)

# Get the Product v1 prompt
response = supabase.table('prompt_templates').select('*').eq('name', 'Product v1').execute()

if not response.data:
    print("Product v1 prompt not found!")
    exit(1)

prompt = response.data[0]
fields = prompt.get('fields', [])

if not fields:
    print("No fields found!")
    exit(1)

print(f"Total top-level fields: {len(fields)}")

# Function to extract all fields recursively
def extract_all_fields(field_list, parent_path="", level=0):
    all_fields = []
    
    for field in field_list:
        if isinstance(field, dict):
            field_name = field.get('name', 'unnamed')
            field_type = field.get('type', 'unknown')
            current_path = f"{parent_path}.{field_name}" if parent_path else field_name
            
            field_info = {
                'path': current_path,
                'name': field_name,
                'type': field_type,
                'level': level,
                'required': field.get('required', False),
                'description': field.get('description', '')[:50] + '...' if field.get('description') else '',
                'has_nested': 'nested_fields' in field
            }
            
            all_fields.append(field_info)
            
            # Process nested fields
            if 'nested_fields' in field and isinstance(field['nested_fields'], list):
                nested = extract_all_fields(field['nested_fields'], current_path, level + 1)
                all_fields.extend(nested)
    
    return all_fields

# Extract all fields
all_fields = extract_all_fields(fields)

print(f"\nTotal fields (including nested): {len(all_fields)}")

# Group by field name to find duplicates
field_name_occurrences = {}
for field in all_fields:
    name = field['name']
    if name not in field_name_occurrences:
        field_name_occurrences[name] = []
    field_name_occurrences[name].append(field)

# Find duplicates
duplicates = {name: occurrences for name, occurrences in field_name_occurrences.items() if len(occurrences) > 1}

if duplicates:
    print(f"\n⚠️  Found {len(duplicates)} field names that appear multiple times:")
    for name, occurrences in sorted(duplicates.items()):
        print(f"\n  '{name}' appears {len(occurrences)} times:")
        for occ in occurrences:
            print(f"    - Path: {occ['path']}")
            print(f"      Level: {occ['level']}, Type: {occ['type']}, Required: {occ['required']}")
else:
    print("\n✓ No duplicate field names found")

# Show the hierarchical structure
print("\n" + "="*80)
print("HIERARCHICAL STRUCTURE:")
print("="*80)

def print_field_tree(field_list, indent=0):
    for field in field_list:
        if isinstance(field, dict):
            prefix = "  " * indent + "- "
            field_name = field.get('name', 'unnamed')
            field_type = field.get('type', 'unknown')
            required = "required" if field.get('required') else "optional"
            
            print(f"{prefix}{field_name} ({field_type}, {required})")
            
            if field.get('description'):
                desc = field['description'][:60] + '...' if len(field['description']) > 60 else field['description']
                print(f"{'  ' * (indent + 1)}  → {desc}")
            
            # Handle nested fields
            if 'nested_fields' in field and isinstance(field['nested_fields'], list):
                print_field_tree(field['nested_fields'], indent + 1)
            
            # Handle list item types with nested fields
            if field_type == 'list' and 'list_item_type' in field and field['list_item_type'] == 'object':
                if 'nested_fields' in field:
                    # Already handled above
                    pass
                else:
                    print(f"{'  ' * (indent + 1)}  [List items have no nested fields defined]")

print_field_tree(fields)

# Analyze potential parsing issues
print("\n" + "="*80)
print("POTENTIAL PARSING ISSUES:")
print("="*80)

issues = []

# Check for fields that might be parsed incorrectly
for field in all_fields:
    # Check for common problematic patterns
    if field['type'] == 'list' and field['has_nested']:
        issues.append(f"List field '{field['name']}' has nested fields - might create duplicates at different levels")
    
    if field['name'] in ['dimensions', 'nutrition', 'allergens', 'storage'] and field['level'] > 0:
        issues.append(f"Field '{field['name']}' appears at level {field['level']} - might be incorrectly nested")

if issues:
    print("\nFound potential issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\nNo obvious parsing issues detected")

# Show the raw JSON for the first field to understand the structure
print("\n" + "="*80)
print("RAW STRUCTURE OF FIRST FIELD:")
print("="*80)
print(json.dumps(fields[0], indent=2))