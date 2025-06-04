#!/usr/bin/env python3
"""
Fix for field definition nesting issue.

The problem: Users define fields in a logical hierarchy:
- structure_extraction (Object - nested)
  - shelf_structure (Object - nested)
    - total_shelves (Integer)
    - other fields...

But the system is generating a Pydantic model that expects structure_extraction.structure_extraction,
which is wrong.

This fix ensures the system correctly interprets the user's field definitions and builds
appropriate Pydantic models without double nesting.
"""

from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type, Union
import json
from enum import Enum

from src.utils import logger


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    OBJECT = "object"
    NUMBER = "number"
    ARRAY = "array"


def flatten_nested_field_definitions(field_definitions: Dict[str, Any], stage_name: str) -> Dict[str, Any]:
    """
    Flatten nested field definitions to prevent double nesting.
    
    This function recursively flattens nested object structures to create a flat
    field structure that matches what the AI will return.
    
    Args:
        field_definitions: Field definitions from the database
        stage_name: Name of the extraction stage
        
    Returns:
        Flattened field definitions
    """
    
    def flatten_object_properties(obj_def: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """Recursively flatten object properties"""
        flattened = {}
        
        if not isinstance(obj_def, dict):
            return flattened
            
        # If it's an object with properties, flatten them
        if obj_def.get('type') == 'object' and 'properties' in obj_def:
            for prop_name, prop_def in obj_def['properties'].items():
                if isinstance(prop_def, dict) and prop_def.get('type') == 'object' and 'properties' in prop_def:
                    # Recursively flatten nested objects
                    nested_flat = flatten_object_properties(prop_def, prop_name)
                    flattened.update(nested_flat)
                else:
                    # Add non-object properties directly
                    flattened[prop_name] = prop_def
        
        return flattened
    
    # Check if we have a single field that matches the stage name or is the only object field
    if len(field_definitions) == 1:
        field_name = list(field_definitions.keys())[0]
        field_def = field_definitions[field_name]
        
        # Check if it's an object type with properties
        if isinstance(field_def, dict) and field_def.get('type') == 'object' and 'properties' in field_def:
            # Recursively flatten all nested properties
            logger.info(
                f"Flattening nested field '{field_name}' for stage '{stage_name}'",
                component="field_definition_fixer"
            )
            return flatten_object_properties(field_def)
    
    # Check for a common pattern: stage_name field inside stage_name
    if stage_name in field_definitions:
        stage_field = field_definitions[stage_name]
        if isinstance(stage_field, dict) and stage_field.get('type') == 'object' and 'properties' in stage_field:
            # This is likely a double-nesting situation
            logger.info(
                f"Detected potential double-nesting for stage '{stage_name}', flattening",
                component="field_definition_fixer"
            )
            # Recursively flatten the stage field
            flattened = flatten_object_properties(stage_field)
            
            # Add any other top-level fields
            for key, value in field_definitions.items():
                if key != stage_name:
                    if isinstance(value, dict) and value.get('type') == 'object' and 'properties' in value:
                        # Flatten other objects too
                        flattened.update(flatten_object_properties(value))
                    else:
                        flattened[key] = value
            
            return flattened
    
    # For other cases, check each field and flatten if needed
    flattened = {}
    for key, value in field_definitions.items():
        if isinstance(value, dict) and value.get('type') == 'object' and 'properties' in value:
            # Flatten object properties
            nested_flat = flatten_object_properties(value)
            flattened.update(nested_flat)
        else:
            # Keep non-object fields as-is
            flattened[key] = value
    
    return flattened if flattened else field_definitions


def build_extraction_model_safe(stage_name: str, field_definitions: Dict[str, Any]) -> Type[BaseModel]:
    """
    Build a Pydantic model from field definitions with automatic flattening.
    
    This function detects and fixes double-nesting issues automatically.
    
    Args:
        stage_name: Name of the extraction stage (e.g., "structure_extraction")
        field_definitions: Dictionary of field definitions from the database/config
        
    Returns:
        A Pydantic model class with properly structured fields
    """
    
    # First, flatten any nested definitions to prevent double nesting
    flattened_definitions = flatten_nested_field_definitions(field_definitions, stage_name)
    
    def get_python_type(field_def: Dict[str, Any], field_name: str = "") -> Any:
        """Convert field definition to Python type"""
        if not isinstance(field_def, dict):
            return Any
            
        field_type = field_def.get('type', 'string').lower()
        
        if field_type in ['string', 'str']:
            return str
        elif field_type in ['integer', 'int']:
            return int
        elif field_type in ['number', 'float']:
            return float
        elif field_type in ['boolean', 'bool']:
            return bool
        elif field_type in ['array', 'list']:
            item_def = field_def.get('items', {})
            item_type = get_python_type(item_def, f"{field_name}_item")
            return List[item_type]
        elif field_type in ['object', 'dict']:
            # For nested objects, check if properties are defined
            properties = field_def.get('properties', {})
            if properties:
                # Create a nested model
                nested_fields = {}
                for prop_name, prop_def in properties.items():
                    if isinstance(prop_def, dict):
                        nested_type = get_python_type(prop_def, prop_name)
                        nested_fields[prop_name] = (
                            nested_type,
                            Field(description=prop_def.get('description', ''))
                        )
                
                # Create nested model with unique name
                nested_model_name = f"{stage_name}_{field_name}_nested".replace('__', '_')
                return create_model(nested_model_name, **nested_fields)
            else:
                # Generic dict if no properties specified
                return Dict[str, Any]
        else:
            return Any
    
    # Build fields for the model
    model_fields = {}
    
    for field_name, field_def in flattened_definitions.items():
        # Skip invalid field definitions
        if not isinstance(field_def, dict):
            logger.warning(f"Skipping invalid field definition for {field_name}: {field_def}")
            continue
        
        try:
            # Get the Python type
            python_type = get_python_type(field_def, field_name)
            
            # Check if field is required
            is_required = field_def.get('required', False)
            
            # Create field with metadata
            field_description = field_def.get('description', f"Field {field_name}")
            
            if is_required:
                model_fields[field_name] = (
                    python_type,
                    Field(description=field_description)
                )
            else:
                # Make optional with default None
                model_fields[field_name] = (
                    Optional[python_type],
                    Field(default=None, description=field_description)
                )
                
        except Exception as e:
            logger.error(f"Error building field {field_name}: {e}")
            # Add as Any type to avoid breaking the model
            model_fields[field_name] = (Any, Field(default=None))
    
    # Create the model with a clean name
    model_name = f"{stage_name.replace('_', ' ').title().replace(' ', '')}Model"
    
    logger.info(
        f"Building model {model_name} with fields: {list(model_fields.keys())}",
        component="field_definition_fixer"
    )
    
    # Create model with fields at ROOT level
    return create_model(model_name, **model_fields)


def patch_dynamic_model_builder():
    """
    Patch the existing dynamic_model_builder.py to use the safe builder.
    
    This can be imported and called to fix the issue in the running system.
    """
    try:
        # Import the existing module
        import src.extraction.dynamic_model_builder as dmb
        
        # Replace the build_extraction_model function with our safe version
        dmb.build_extraction_model = build_extraction_model_safe
        
        logger.info(
            "Successfully patched dynamic_model_builder with safe field flattening",
            component="field_definition_fixer"
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to patch dynamic_model_builder: {e}",
            component="field_definition_fixer"
        )
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: User's logical structure (what they define in UI)
    user_defined_fields = {
        "structure_extraction": {
            "type": "object",
            "description": "Extract shelf structure information",
            "properties": {
                "shelf_structure": {
                    "type": "object",
                    "description": "Shelf structure details",
                    "properties": {
                        "total_shelves": {
                            "type": "integer",
                            "description": "Total number of shelves",
                            "required": True
                        },
                        "shelf_height": {
                            "type": "number",
                            "description": "Height of each shelf in cm"
                        }
                    }
                },
                "fixture_type": {
                    "type": "string",
                    "description": "Type of shelf fixture"
                }
            }
        }
    }
    
    # Test case 2: Already flat structure (should work as-is)
    flat_fields = {
        "total_shelves": {
            "type": "integer",
            "description": "Total number of shelves",
            "required": True
        },
        "shelves": {
            "type": "array",
            "description": "Array of shelf objects",
            "items": {
                "type": "object",
                "properties": {
                    "shelf_number": {"type": "integer"},
                    "has_price_rail": {"type": "boolean"}
                }
            }
        }
    }
    
    print("Test Case 1: User's nested structure")
    print("="*60)
    print("Input field definitions:")
    print(json.dumps(user_defined_fields, indent=2))
    
    # Build model with automatic flattening
    Model1 = build_extraction_model_safe("structure_extraction", user_defined_fields)
    print("\nGenerated model schema:")
    print(json.dumps(Model1.model_json_schema(), indent=2))
    
    # Test creating an instance
    try:
        instance = Model1(
            total_shelves=5,
            shelf_height=30.5,
            fixture_type="gondola"
        )
        print("\n✓ Model instance created successfully!")
        print(f"  Data: {instance.model_dump()}")
    except Exception as e:
        print(f"\n✗ Error creating instance: {e}")
    
    print("\n" + "="*60)
    print("Test Case 2: Already flat structure")
    print("="*60)
    
    Model2 = build_extraction_model_safe("structure_extraction", flat_fields)
    print("Generated model schema:")
    print(json.dumps(Model2.model_json_schema(), indent=2))
    
    # Test creating an instance
    try:
        instance2 = Model2(
            total_shelves=3,
            shelves=[
                {"shelf_number": 1, "has_price_rail": True},
                {"shelf_number": 2, "has_price_rail": False}
            ]
        )
        print("\n✓ Model instance created successfully!")
        print(f"  Data: {instance2.model_dump()}")
    except Exception as e:
        print(f"\n✗ Error creating instance: {e}")
    
    # Show the fix in action
    print("\n" + "="*60)
    print("Summary: The fix automatically detects and flattens nested structures")
    print("="*60)
    print("User defines:")
    print("  structure_extraction > shelf_structure > total_shelves")
    print("\nSystem expects:")
    print("  total_shelves (at root level)")
    print("\n✓ The fix bridges this gap automatically!")