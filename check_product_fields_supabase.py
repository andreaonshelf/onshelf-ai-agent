import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from datetime import datetime

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Fetching Product v1 fields from Supabase...")
print("="*80)

# Get all fields for Product v1
response = supabase.table('field_definitions').select('*').eq('category', 'Product').eq('version', 'v1').order('field_order').order('field_name').execute()

fields = response.data
print(f'\nTotal fields found for Product v1: {len(fields)}')
print('\n' + '='*80 + '\n')

# Display fields in a structured way
for field in fields:
    print(f'Field: {field["field_name"]} (ID: {field["id"]})')
    print(f'  Display Name: {field["display_name"]}')
    print(f'  Type: {field["field_type"]}')
    print(f'  Required: {field["is_required"]}')
    print(f'  Parent: {field["parent_field"]}')
    print(f'  Order: {field["field_order"]}')
    print(f'  Organization: {field["organization"]}')
    print(f'  Created: {field["created_at"]}')
    print(f'  Updated: {field["updated_at"]}')
    if field.get("validation_rules"):
        print(f'  Validation: {json.dumps(field["validation_rules"], indent=4)}')
    print('-' * 40)

# Check for duplicates
print('\n' + '='*80 + '\n')
print('CHECKING FOR DUPLICATES:')
print('='*80 + '\n')

field_counts = {}
for field in fields:
    name = field['field_name']
    if name not in field_counts:
        field_counts[name] = []
    field_counts[name].append(field)

duplicates = {name: entries for name, entries in field_counts.items() if len(entries) > 1}

if duplicates:
    print(f'Found {len(duplicates)} fields with duplicates:\n')
    for field_name, entries in duplicates.items():
        print(f'Field: {field_name}')
        print(f'  Count: {len(entries)}')
        print(f'  IDs: {[e["id"] for e in entries]}')
        print(f'  Parents: {[e["parent_field"] for e in entries]}')
        print(f'  Organizations: {[e["organization"] for e in entries]}')
        print('-' * 40)
else:
    print('No duplicate field names found.')

# Build hierarchical structure
print('\n' + '='*80 + '\n')
print('HIERARCHICAL STRUCTURE:')
print('='*80 + '\n')

# Build field lookup
field_lookup = {f['field_name']: f for f in fields}

# Function to print hierarchy
def print_hierarchy(field_name=None, level=0, visited=None):
    if visited is None:
        visited = set()
    
    if field_name in visited:
        print(f'{"  " * level}[CIRCULAR REFERENCE: {field_name}]')
        return
    
    visited.add(field_name)
    
    # Find children of this field
    children = [f for f in fields if f['parent_field'] == field_name]
    
    if field_name is None:
        # Root level - fields with no parent
        children = [f for f in fields if f['parent_field'] is None]
        print('Root level fields:')
    
    # Sort by field_order, then by field_name
    children.sort(key=lambda x: (x['field_order'] or 999, x['field_name']))
    
    for child in children:
        indent = '  ' * level
        print(f'{indent}- {child["field_name"]} ({child["display_name"]}) [order: {child["field_order"]}, org: {child["organization"]}]')
        # Recursively print children
        print_hierarchy(child['field_name'], level + 1, visited.copy())

print_hierarchy()

# Analyze by organization
print('\n' + '='*80 + '\n')
print('ANALYSIS BY ORGANIZATION:')
print('='*80 + '\n')

org_groups = {}
for field in fields:
    org = field['organization'] or 'NULL'
    if org not in org_groups:
        org_groups[org] = []
    org_groups[org].append(field['field_name'])

for org, field_names in sorted(org_groups.items()):
    print(f'\nOrganization: {org}')
    print(f'  Count: {len(field_names)}')
    print(f'  Fields: {", ".join(sorted(field_names))}')

# Check for potential parsing issues
print('\n' + '='*80 + '\n')
print('POTENTIAL PARSING ISSUES:')
print('='*80 + '\n')

# Look for fields that might be incorrectly nested
print('\nFields with unexpected parent relationships:')
for field in fields:
    if field['parent_field'] and field['parent_field'] not in field_lookup:
        print(f'  - {field["field_name"]} has parent {field["parent_field"]} which does not exist!')
    
    # Check if a field that should be a parent is actually a child
    if field['field_name'] in ['dimensions', 'nutrition', 'allergens', 'storage']:
        if field['parent_field'] is not None:
            print(f'  - {field["field_name"]} is nested under {field["parent_field"]} but should probably be a root field')

# Check for fields that appear at multiple levels
print('\nFields appearing at multiple hierarchy levels:')
for field_name, entries in field_counts.items():
    if len(entries) > 1:
        parents = [e['parent_field'] for e in entries]
        if len(set(parents)) > 1:
            print(f'  - {field_name} appears under different parents: {parents}')