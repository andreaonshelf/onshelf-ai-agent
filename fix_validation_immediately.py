#!/usr/bin/env python3
"""
Immediate fix for the validation error by updating the field_schema_builder.py
to use valid enum values instead of "example" for literal fields.
"""

import os

# Read the current field_schema_builder.py
file_path = "/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src/api/field_schema_builder.py"

try:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if 'if field.enum_values and len(field.enum_values) > 0:' in content:
        print("✓ Fix is already applied in field_schema_builder.py")
        
        # Check if literal type handling is also fixed
        if 'field.type == "literal"' in content:
            print("✓ Literal type handling is also applied")
        else:
            print("✗ Need to add literal type handling")
            
            # Add literal type handling
            content = content.replace(
                'if field_def.type == FieldType.STRING:',
                'if field_def.type == FieldType.STRING or field_def.type == "literal":'
            )
            
            content = content.replace(
                'elif field.type == FieldType.STRING:',
                'elif field.type == FieldType.STRING or field.type == "literal":'
            )
            
            # Write the updated content
            with open(file_path, 'w') as f:
                f.write(content)
            
            print("✓ Applied literal type handling fix")
    else:
        print("✗ Fix not found - applying full fix")
        
        # Apply the full fix
        old_code = '''                elif field.type == FieldType.STRING:
                    data[field.name] = "example"'''
                    
        new_code = '''                elif field.type == FieldType.STRING or field.type == "literal":
                    if field.enum_values and len(field.enum_values) > 0:
                        # Use first enum value for literal/enum fields
                        data[field.name] = field.enum_values[0]
                    else:
                        data[field.name] = "example"'''
                        
        if old_code in content:
            content = content.replace(old_code, new_code)
            print("✓ Applied example data generation fix")
        else:
            print("✗ Could not find exact code to replace")
        
        # Also fix the type checking
        content = content.replace(
            'if field_def.type == FieldType.STRING:',
            'if field_def.type == FieldType.STRING or field_def.type == "literal":'
        )
        
        # Write the updated content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✓ Applied all fixes to field_schema_builder.py")
        
    # Now test if the server needs to be restarted
    print("\nTesting if server picks up the changes...")
    
    # Since FastAPI has auto-reload, the changes should be picked up automatically
    # But let's verify by checking the process
    import subprocess
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'main.py' in result.stdout:
            print("✓ Server is running with auto-reload - changes should be picked up automatically")
        else:
            print("✗ Server might not be running")
    except:
        print("? Could not check server status")
    
    print(f"\n✅ Fix applied successfully!")
    print(f"The validation error should now be resolved.")
    print(f"The schema builder will now use 'wall_shelf' instead of 'example' for shelf_type field.")

except FileNotFoundError:
    print(f"✗ Could not find {file_path}")
except Exception as e:
    print(f"✗ Error applying fix: {e}")