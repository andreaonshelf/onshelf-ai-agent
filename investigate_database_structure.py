import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Investigating database structure...")
print("="*80)

# Let's check what tables exist
print("\nChecking available tables...")

# Common table names to check
tables_to_check = [
    'field_definitions',
    'prompt_templates', 
    'prompts',
    'products',
    'product_fields',
    'extraction_fields',
    'field_schemas',
    'categories',
    'versions'
]

print("\nQuerying known tables:")
for table_name in tables_to_check:
    try:
        response = supabase.table(table_name).select('*').limit(1).execute()
        if response.data:
            print(f"\n✓ Table '{table_name}' exists")
            print(f"  Columns: {list(response.data[0].keys())}")
        else:
            print(f"\n✓ Table '{table_name}' exists but is empty")
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            print(f"\n✗ Table '{table_name}' does not exist")
        else:
            print(f"\n? Table '{table_name}' - Error: {str(e)[:100]}")

# Let's check prompt_templates for field-related content
print("\n" + "="*80)
print("\nChecking prompt_templates for field definitions:")
try:
    response = supabase.table('prompt_templates').select('*').execute()
    
    print(f"\nFound {len(response.data)} prompt templates")
    
    # Check for field_definitions column
    if response.data:
        sample = response.data[0]
        if 'field_definitions' in sample:
            print("\n✓ prompt_templates table has 'field_definitions' column")
            
            # Look for Product v1 related prompts
            for prompt in response.data:
                if prompt.get('field_definitions'):
                    prompt_name = prompt.get('prompt_name', '') or ''
                    prompt_type = prompt.get('prompt_type', '') or ''
                    description = prompt.get('description', '') or ''
                    
                    if 'product' in prompt_name.lower() or 'product' in prompt_type.lower() or 'v1' in str(prompt):
                        print(f"\nFound prompt with field definitions:")
                        print(f"  Name: {prompt_name}")
                        print(f"  Type: {prompt_type}")
                        print(f"  Description: {description[:100]}...")
                        print(f"  Field count: {len(prompt['field_definitions']) if isinstance(prompt['field_definitions'], list) else 'Not a list'}")
                        
                        # Print first few fields
                        if isinstance(prompt['field_definitions'], list) and prompt['field_definitions']:
                            print("  First few fields:")
                            for i, field in enumerate(prompt['field_definitions'][:3]):
                                if isinstance(field, dict):
                                    print(f"    - {field.get('name', 'unnamed')} ({field.get('type', 'unknown')})")
        else:
            print("\n✗ prompt_templates table does not have 'field_definitions' column")
            print(f"  Available columns: {list(sample.keys())}")
            
except Exception as e:
    print(f"\nError checking prompt_templates: {e}")

# Check for any "Product v1" references across tables
print("\n" + "="*80)
print("\nSearching for 'Product v1' references:")

# Check field_definitions for any Product-related entries
try:
    response = supabase.table('field_definitions').select('*').execute()
    
    print(f"\nTotal field_definitions entries: {len(response.data)}")
    
    # Group by category
    categories = {}
    for field in response.data:
        cat = field.get('category', 'Unknown')
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    print("\nCategories in field_definitions:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count} fields")
        
    # Look for any v1 references
    v1_refs = []
    for field in response.data:
        field_str = json.dumps(field)
        if 'v1' in field_str.lower():
            v1_refs.append(field)
    
    if v1_refs:
        print(f"\nFound {len(v1_refs)} fields with 'v1' references:")
        for field in v1_refs[:5]:
            print(f"  - {field.get('field_name', 'unnamed')} in category '{field.get('category', 'unknown')}'")
            
except Exception as e:
    print(f"\nError searching field_definitions: {e}")