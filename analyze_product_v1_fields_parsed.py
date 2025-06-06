import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Analyzing Product v1 field structure (properly parsed)...")
print("="*80)

# Get the Product v1 prompt
response = supabase.table('prompt_templates').select('*').eq('name', 'Product v1').execute()

if not response.data:
    print("Product v1 prompt not found!")
    exit(1)

prompt = response.data[0]
fields_raw = prompt.get('fields', [])

# Parse the fields if they're a string
if isinstance(fields_raw, str):
    try:
        fields = json.loads(fields_raw)
        print(f"Parsed fields from JSON string")
    except json.JSONDecodeError:
        print("Failed to parse fields as JSON")
        exit(1)
else:
    fields = fields_raw

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

# Look for specific problematic fields
print("\n" + "="*80)
print("SEARCHING FOR SPECIFIC FIELDS:")
print("="*80)

target_fields = ['dimensions', 'nutrition', 'allergens', 'storage', 'width', 'height', 'depth']

for target in target_fields:
    occurrences = [f for f in all_fields if target in f['name'].lower()]
    if occurrences:
        print(f"\nField containing '{target}':")
        for occ in occurrences:
            print(f"  - {occ['name']} at {occ['path']} (level {occ['level']})")

# Show the raw JSON structure to understand better
print("\n" + "="*80)
print("RAW JSON STRUCTURE:")
print("="*80)
print(json.dumps(fields, indent=2)[:3000])
if len(json.dumps(fields)) > 3000:
    print("\n... (truncated)")

# Check how this might be parsed incorrectly
print("\n" + "="*80)
print("ANALYSIS OF PARSING LOGIC:")
print("="*80)

# The issue might be in how nested_fields are being processed
# Let's trace through what a parser might do
print("\nIf a parser flattens nested_fields without proper parent tracking:")
for field in fields:
    if isinstance(field, dict) and 'nested_fields' in field:
        print(f"\nField '{field['name']}' has nested_fields:")
        for nested in field.get('nested_fields', []):
            if isinstance(nested, dict):
                print(f"  - {nested.get('name', 'unnamed')} would be added at root level")
                if 'nested_fields' in nested:
                    print(f"    (and this has its own nested fields!)")