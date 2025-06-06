import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Fetching all field definitions...")
print("="*80)

# Get all fields to see what categories exist
response = supabase.table('field_definitions').select('*').execute()
all_fields = response.data

# Group by category
categories = {}
for field in all_fields:
    cat = field.get('category', 'Unknown')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(field)

print(f"\nTotal fields in database: {len(all_fields)}")
print(f"\nCategories found:")
for cat, fields in categories.items():
    print(f"  - {cat}: {len(fields)} fields")

# Now let's look at Product fields specifically
print("\n" + "="*80 + "\n")
print("PRODUCT FIELDS:")
print("="*80 + "\n")

# Try different case variations
for cat_variant in ['Product', 'product', 'PRODUCT']:
    response = supabase.table('field_definitions').select('*').eq('category', cat_variant).execute()
    if response.data:
        print(f"\nFound {len(response.data)} fields with category='{cat_variant}'")
        product_fields = response.data
        break
else:
    print("\nNo Product fields found with standard category names.")
    # Let's check if there are any fields that might be products
    print("\nLooking for product-related fields by name...")
    product_fields = [f for f in all_fields if 'product' in f.get('field_name', '').lower() or 
                      'product' in f.get('display_name', '').lower() or
                      'product' in f.get('category', '').lower()]

if product_fields:
    # Sort by sort_order and field_name
    product_fields.sort(key=lambda x: (x.get('sort_order', 999), x.get('field_name', '')))
    
    print(f"\nDisplaying {len(product_fields)} product-related fields:\n")
    
    for field in product_fields:
        print(f"Field: {field['field_name']} (ID: {field['id']})")
        print(f"  Display Name: {field.get('display_name', 'N/A')}")
        print(f"  Category: {field.get('category', 'N/A')}")
        print(f"  Data Type: {field.get('data_type', 'N/A')}")
        print(f"  Required: {field.get('is_required', False)}")
        print(f"  Parent: {field.get('parent_field', 'None')}")
        print(f"  Sort Order: {field.get('sort_order', 'N/A')}")
        print(f"  Definition: {field.get('definition', 'N/A')}")
        if field.get('validation_rules'):
            print(f"  Validation: {json.dumps(field['validation_rules'], indent=4)}")
        print("-" * 40)
    
    # Check for duplicates
    print("\n" + "="*80 + "\n")
    print("CHECKING FOR DUPLICATE FIELD NAMES:")
    print("="*80 + "\n")
    
    field_name_counts = {}
    for field in product_fields:
        name = field['field_name']
        if name not in field_name_counts:
            field_name_counts[name] = []
        field_name_counts[name].append(field)
    
    duplicates = {name: fields for name, fields in field_name_counts.items() if len(fields) > 1}
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicate field names:")
        for name, fields in duplicates.items():
            print(f"\n'{name}' appears {len(fields)} times:")
            for f in fields:
                print(f"  - ID: {f['id']}, Parent: {f.get('parent_field', 'None')}, Category: {f.get('category', 'N/A')}")
    else:
        print("No duplicate field names found.")
    
    # Build hierarchy
    print("\n" + "="*80 + "\n")
    print("HIERARCHICAL STRUCTURE:")
    print("="*80 + "\n")
    
    # Find root fields (no parent)
    root_fields = [f for f in product_fields if not f.get('parent_field')]
    print(f"Root fields ({len(root_fields)}):")
    
    def print_field_tree(fields, parent=None, level=0):
        children = [f for f in fields if f.get('parent_field') == parent]
        children.sort(key=lambda x: (x.get('sort_order', 999), x.get('field_name', '')))
        
        for child in children:
            indent = "  " * level
            print(f"{indent}- {child['field_name']} [{child.get('data_type', 'unknown')}]")
            # Recursively print children
            print_field_tree(fields, child['field_name'], level + 1)
    
    print_field_tree(product_fields, None, 0)
    
else:
    print("\nNo product-related fields found in the database.")