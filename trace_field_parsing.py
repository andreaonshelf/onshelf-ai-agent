import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Tracing how Product v1 fields are parsed...")
print("="*80)

# Get the Product v1 prompt
response = supabase.table('prompt_templates').select('*').eq('name', 'Product v1').execute()

if not response.data:
    print("Product v1 prompt not found!")
    exit(1)

prompt = response.data[0]

# Get the fields
fields_raw = prompt.get('fields', [])
if isinstance(fields_raw, str):
    fields = json.loads(fields_raw)
else:
    fields = fields_raw

print(f"Product v1 has {len(fields)} top-level fields")

# Function to simulate the parsing that might be creating duplicates
def simulate_field_parsing(fields_list, level=0):
    """Simulate how fields might be parsed incorrectly"""
    parsed_fields = []
    
    for field in fields_list:
        if not isinstance(field, dict):
            continue
            
        field_name = field.get('name', 'unnamed')
        field_type = field.get('type', 'unknown')
        
        print(f"{'  ' * level}Processing field: {field_name} (type: {field_type})")
        
        # Add this field
        parsed_fields.append({
            'name': field_name,
            'type': field_type,
            'level': level,
            'path': field_name
        })
        
        # Check for nested fields
        if 'nested_fields' in field:
            print(f"{'  ' * level}  -> Has nested_fields")
            nested = field['nested_fields']
            if isinstance(nested, list):
                # ISSUE 1: If parser adds nested fields at root level
                print(f"{'  ' * level}  ⚠️  Parser might add these nested fields at root level:")
                for nf in nested:
                    if isinstance(nf, dict):
                        print(f"{'  ' * level}     - {nf.get('name', 'unnamed')}")
                
                # Recursive parsing
                nested_parsed = simulate_field_parsing(nested, level + 1)
                parsed_fields.extend(nested_parsed)
        
        # Check for list item types with nested fields
        if field_type == 'list' and field.get('list_item_type') == 'object':
            print(f"{'  ' * level}  -> List with object items")
            if 'nested_fields' in field:
                # ISSUE 2: Parser might process these as top-level fields
                print(f"{'  ' * level}  ⚠️  List item fields might be parsed as top-level:")
                for nf in field['nested_fields']:
                    if isinstance(nf, dict):
                        print(f"{'  ' * level}     - {nf.get('name', 'unnamed')}")
    
    return parsed_fields

print("\nSimulating field parsing:")
print("="*80)
all_parsed = simulate_field_parsing(fields)

# Count duplicates
name_counts = {}
for field in all_parsed:
    name = field['name']
    if name not in name_counts:
        name_counts[name] = 0
    name_counts[name] += 1

print("\n" + "="*80)
print("PARSING RESULTS:")
print("="*80)
print(f"Total fields parsed: {len(all_parsed)}")

duplicates = {name: count for name, count in name_counts.items() if count > 1}
if duplicates:
    print(f"\n⚠️  Found {len(duplicates)} duplicate field names:")
    for name, count in duplicates.items():
        print(f"  - '{name}' appears {count} times")
else:
    print("\n✓ No duplicates found in parsing")

# Now let's see how the UI schema builder would handle this
print("\n" + "="*80)
print("UI SCHEMA BUILDER APPROACH:")
print("="*80)

def build_ui_schema(fields_list, parent_path=""):
    """Build UI schema correctly without duplicates"""
    ui_fields = []
    
    for field in fields_list:
        if not isinstance(field, dict):
            continue
            
        field_name = field.get('name', 'unnamed')
        field_type = field.get('type', 'unknown')
        current_path = f"{parent_path}.{field_name}" if parent_path else field_name
        
        # Create field entry
        ui_field = {
            'name': field_name,
            'type': field_type,
            'path': current_path,
            'description': field.get('description', ''),
            'required': field.get('required', False)
        }
        
        # Handle nested fields properly
        if 'nested_fields' in field and isinstance(field['nested_fields'], list):
            ui_field['nested_fields'] = build_ui_schema(field['nested_fields'], current_path)
        
        # Handle list item type
        if field_type == 'list' and 'list_item_type' in field:
            ui_field['list_item_type'] = field['list_item_type']
        
        ui_fields.append(ui_field)
    
    return ui_fields

ui_schema = build_ui_schema(fields)
print(f"UI Schema has {len(ui_schema)} top-level fields")
print(f"Structure: {json.dumps(ui_schema, indent=2)[:1000]}...")

# Check how this might be converted to Pydantic
print("\n" + "="*80)
print("PYDANTIC MODEL GENERATION:")
print("="*80)

def count_pydantic_fields(fields_list, model_name="Model"):
    """Count fields that would be in a Pydantic model"""
    field_count = 0
    
    for field in fields_list:
        if not isinstance(field, dict):
            continue
        
        field_count += 1
        
        # Nested fields become a nested model, not additional fields
        if field.get('type') == 'object' and 'nested_fields' in field:
            print(f"  - {field['name']}: Would be a nested Pydantic model")
        elif field.get('type') == 'list' and field.get('list_item_type') == 'object':
            print(f"  - {field['name']}: Would be List[NestedModel]")
        else:
            print(f"  - {field['name']}: {field.get('type', 'Any')}")
    
    return field_count

print(f"\nPydantic model would have {count_pydantic_fields(fields)} fields at root level")