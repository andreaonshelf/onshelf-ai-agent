"""Debug script to check what's happening when Product v1 is selected"""

import json

# The issue is likely in the dashboard HTML where it's trying to handle field definitions
# Let's create a minimal test case

test_fields = {
    "simple": [
        {"name": "field1", "type": "string", "description": "Simple field"}
    ],
    "nested": [
        {
            "name": "parent",
            "type": "object",
            "description": "Parent field",
            "nested_fields": [
                {"name": "child", "type": "string", "description": "Child field"}
            ]
        }
    ],
    "deeply_nested": [
        {
            "name": "level1",
            "type": "object",
            "description": "Level 1",
            "nested_fields": [
                {
                    "name": "level2",
                    "type": "object",
                    "description": "Level 2",
                    "nested_fields": [
                        {
                            "name": "level3",
                            "type": "object",
                            "description": "Level 3",
                            "nested_fields": [
                                {"name": "leaf", "type": "string", "description": "Leaf node"}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# Check if any structure could cause infinite recursion
def check_recursion(fields, visited=None, path=None):
    if visited is None:
        visited = set()
    if path is None:
        path = []
    
    for field in fields:
        field_id = id(field)
        if field_id in visited:
            print(f"CIRCULAR REFERENCE DETECTED: {' -> '.join(path + [field['name']])}")
            return True
        
        visited.add(field_id)
        
        if 'nested_fields' in field and field['nested_fields']:
            if check_recursion(field['nested_fields'], visited.copy(), path + [field['name']]):
                return True
    
    return False

# Test each structure
for name, fields in test_fields.items():
    print(f"\nTesting {name}:")
    print(f"Structure: {json.dumps(fields, indent=2)}")
    has_recursion = check_recursion(fields)
    print(f"Has circular reference: {has_recursion}")

# The crash might be caused by:
# 1. Circular references in field definitions
# 2. Too deep nesting causing stack overflow
# 3. Malformed data structure
# 4. React state update loop

print("\n\nPossible causes of crash:")
print("1. If Product v1 has circular field references")
print("2. If the field structure is too deeply nested")
print("3. If there's a React state update loop when parsing fields")
print("4. If the API returns malformed data")

# Let's check what a problematic structure might look like
problematic_field = {
    "name": "product",
    "type": "object",
    "nested_fields": []
}
# Create circular reference
problematic_field["nested_fields"].append(problematic_field)

print("\n\nExample of problematic circular structure:")
try:
    json.dumps(problematic_field)
except Exception as e:
    print(f"Cannot serialize: {e}")
    print("This would cause React to crash when trying to render!")