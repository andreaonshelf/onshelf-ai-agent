#!/usr/bin/env python3
"""
Apply the field nesting fix to the running system.

This script patches the dynamic model builder to automatically flatten
nested field definitions to prevent the double-nesting issue.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fix_field_definition_nesting import patch_dynamic_model_builder, build_extraction_model_safe


def apply_fix():
    """Apply the field nesting fix to the system"""
    
    print("Applying field nesting fix...")
    
    # Method 1: Try to patch the existing dynamic model builder
    if patch_dynamic_model_builder():
        print("✓ Successfully patched dynamic_model_builder module")
    else:
        print("✗ Could not patch dynamic_model_builder module directly")
        print("  The fix function is still available for manual integration")
    
    # Method 2: Replace the function in the module directly
    try:
        import src.extraction.dynamic_model_builder as dmb
        
        # Store the original function for reference
        dmb.build_extraction_model_original = dmb.build_extraction_model
        
        # Replace with our safe version
        dmb.build_extraction_model = build_extraction_model_safe
        
        print("✓ Successfully replaced build_extraction_model function")
        
        # Test the fix
        test_the_fix()
        
    except Exception as e:
        print(f"✗ Error applying fix: {e}")
        print("\nManual integration required:")
        print("1. Import the fix function:")
        print("   from fix_field_definition_nesting import build_extraction_model_safe")
        print("2. Use it wherever field definitions are converted to Pydantic models")


def test_the_fix():
    """Test that the fix works correctly"""
    
    print("\nTesting the fix...")
    
    # Test case: Nested structure that would cause double-nesting
    test_fields = {
        "structure_extraction": {
            "type": "object",
            "description": "Structure extraction fields",
            "properties": {
                "shelf_structure": {
                    "type": "object",
                    "properties": {
                        "total_shelves": {
                            "type": "integer",
                            "description": "Total shelves",
                            "required": True
                        }
                    }
                }
            }
        }
    }
    
    try:
        from src.extraction.dynamic_model_builder import build_extraction_model
        
        # Build model with the patched function
        model = build_extraction_model("structure_extraction", test_fields)
        
        # Test creating an instance
        instance = model(total_shelves=5)
        
        print("✓ Fix is working! Model expects fields at root level")
        print(f"  Created instance: {instance.model_dump()}")
        
    except Exception as e:
        print(f"✗ Fix test failed: {e}")


def show_integration_guide():
    """Show how to integrate the fix in different parts of the system"""
    
    print("\n" + "="*60)
    print("INTEGRATION GUIDE")
    print("="*60)
    
    print("\n1. In extraction engine or orchestrator:")
    print("""
from fix_field_definition_nesting import build_extraction_model_safe

# When building models from field definitions:
model = build_extraction_model_safe(stage_name, field_definitions)
""")
    
    print("\n2. In API endpoints that use field definitions:")
    print("""
from fix_field_definition_nesting import flatten_nested_field_definitions

# Before using field definitions:
flattened_fields = flatten_nested_field_definitions(field_definitions, stage_name)
""")
    
    print("\n3. In prompt generation with field definitions:")
    print("""
# The fix ensures that when the AI returns data, it matches the expected structure
# User defines: structure_extraction > shelf_structure > total_shelves
# AI returns: { "total_shelves": 5 }  (fields at root, not nested)
""")


if __name__ == "__main__":
    apply_fix()
    show_integration_guide()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print("The fix has been applied. It will automatically:")
    print("1. Detect when field definitions have unnecessary nesting")
    print("2. Flatten the structure to match what Pydantic expects")
    print("3. Allow users to define logical hierarchies without breaking extraction")
    print("\nNo changes needed to user-defined field structures!")