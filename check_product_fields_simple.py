import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=== CHECKING PRODUCT V1 FIELD DEFINITIONS ===")
try:
    # Query field definitions for product_v1
    result = supabase.table('field_definitions').select('*').eq('extraction_type', 'product_v1').execute()
    
    if result.data:
        print(f"\nFound {len(result.data)} field definitions for product_v1\n")
        
        # Create a map for easy lookup
        fields_by_id = {f['id']: f for f in result.data}
        
        # Sort by order_index
        sorted_fields = sorted(result.data, key=lambda x: x.get('order_index', 0))
        
        for field in sorted_fields:
            print(f"Field: {field['name']}")
            print(f"  ID: {field['id']}")
            print(f"  Type: {field['type']}")
            print(f"  Order: {field.get('order_index', 'N/A')}")
            print(f"  Parent ID: {field.get('parent_id', 'None')}")
            
            # Check if parent exists
            if field.get('parent_id'):
                parent = fields_by_id.get(field['parent_id'])
                if parent:
                    print(f"  Parent Name: {parent['name']}")
                else:
                    print(f"  WARNING: Parent ID {field['parent_id']} not found!")
            
            # Check fields column
            if 'fields' in field and field['fields']:
                print(f"  Has nested fields structure: {len(field['fields'])} items")
                # Print first few items to avoid too much output
                print(f"  Fields preview: {json.dumps(field['fields'][:2] if isinstance(field['fields'], list) else field['fields'], indent=4)}")
            
            print("-" * 60)
        
        # Check for potential issues
        print("\n=== CHECKING FOR POTENTIAL ISSUES ===")
        
        # 1. Check for circular references
        print("\n1. Circular Reference Check:")
        for field in result.data:
            if field.get('parent_id'):
                visited = set()
                current_id = field['id']
                path = [field['name']]
                
                while current_id:
                    if current_id in visited:
                        print(f"  CIRCULAR REFERENCE: {' -> '.join(path)}")
                        break
                    
                    visited.add(current_id)
                    current_field = fields_by_id.get(current_id)
                    
                    if current_field and current_field.get('parent_id'):
                        current_id = current_field['parent_id']
                        parent = fields_by_id.get(current_id)
                        if parent:
                            path.append(parent['name'])
                    else:
                        break
        
        # 2. Check for orphaned fields
        print("\n2. Orphaned Fields Check:")
        for field in result.data:
            if field.get('parent_id') and field['parent_id'] not in fields_by_id:
                print(f"  ORPHANED: {field['name']} references non-existent parent {field['parent_id']}")
        
        # 3. Check for duplicate order indices
        print("\n3. Duplicate Order Index Check:")
        order_counts = {}
        for field in result.data:
            order = field.get('order_index', 0)
            if order not in order_counts:
                order_counts[order] = []
            order_counts[order].append(field['name'])
        
        for order, names in order_counts.items():
            if len(names) > 1:
                print(f"  Order {order}: {', '.join(names)}")
        
    else:
        print("No field definitions found for product_v1")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()