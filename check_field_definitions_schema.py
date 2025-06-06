import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Checking field_definitions table schema...")
print("="*80)

# First, let's try to get just one row to see the structure
try:
    response = supabase.table('field_definitions').select('*').limit(1).execute()
    
    if response.data and len(response.data) > 0:
        print("\nSample row from field_definitions:")
        sample = response.data[0]
        for key, value in sample.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
except Exception as e:
    print(f"Error fetching sample: {e}")

print("\n" + "="*80 + "\n")

# Now let's get all Product fields (without version filter)
try:
    response = supabase.table('field_definitions').select('*').eq('category', 'Product').execute()
    
    fields = response.data
    print(f'Total Product fields found: {len(fields)}')
    
    # Check if there's a version field or similar
    if fields:
        sample = fields[0]
        print(f"\nAvailable columns: {list(sample.keys())}")
        
        # Group by unique combinations of certain fields to understand structure
        unique_combos = {}
        for field in fields:
            # Create a key based on potential version indicators
            key = f"{field.get('category', '')}|{field.get('organization', '')}|{field.get('parent_field', '')}"
            if key not in unique_combos:
                unique_combos[key] = []
            unique_combos[key].append(field['field_name'])
        
        print(f"\nUnique category/organization/parent combinations:")
        for key, field_names in unique_combos.items():
            cat, org, parent = key.split('|')
            print(f"\n  Category: {cat}, Org: {org or 'None'}, Parent: {parent or 'None'}")
            print(f"    Fields: {', '.join(field_names[:5])}{' ...' if len(field_names) > 5 else ''} ({len(field_names)} total)")
            
except Exception as e:
    print(f"Error fetching Product fields: {e}")

# Let's also look for any fields that might indicate version
print("\n" + "="*80 + "\n")
print("Looking for version-like patterns in field data...")

try:
    # Get all Product fields
    response = supabase.table('field_definitions').select('*').eq('category', 'Product').execute()
    fields = response.data
    
    # Look for v1 patterns in field names or other attributes
    v1_indicators = []
    for field in fields:
        for key, value in field.items():
            if value and isinstance(value, str) and 'v1' in str(value).lower():
                v1_indicators.append({
                    'field_name': field['field_name'],
                    'column': key,
                    'value': value
                })
    
    if v1_indicators:
        print(f"\nFound 'v1' in {len(v1_indicators)} places:")
        for ind in v1_indicators[:10]:  # Show first 10
            print(f"  Field '{ind['field_name']}' has '{ind['value']}' in column '{ind['column']}'")
    else:
        print("\nNo 'v1' patterns found in the data")
        
except Exception as e:
    print(f"Error analyzing fields: {e}")