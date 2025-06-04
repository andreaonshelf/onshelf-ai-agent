#!/usr/bin/env python3
"""
Fix for structure_extraction double nesting issue.

The problem: When building Pydantic models from field definitions,
the system is incorrectly expecting structure_extraction.structure_extraction
instead of just the fields at the root level.
"""

from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type


def build_model_from_field_definitions(
    model_name: str,
    field_definitions: Dict[str, Any],
    nested_as_root: bool = True
) -> Type[BaseModel]:
    """
    Build a Pydantic model from field definitions.
    
    Args:
        model_name: Name of the model to create
        field_definitions: Dictionary of field definitions from the database
        nested_as_root: If True, treat nested object fields as the root model fields
                       If False, wrap everything under the model_name key
    
    Returns:
        A Pydantic model class
    """
    
    def get_python_type(field_def: Dict[str, Any]) -> Any:
        """Convert field definition type to Python type"""
        field_type = field_def.get('type', 'string')
        
        if field_type == 'string':
            return str
        elif field_type == 'integer':
            return int
        elif field_type == 'number':
            return float
        elif field_type == 'boolean':
            return bool
        elif field_type == 'array':
            item_type = get_item_type(field_def.get('items', {}))
            return List[item_type]
        elif field_type == 'object':
            # Build nested model if properties exist
            properties = field_def.get('properties', {})
            if properties:
                nested_fields = {}
                for prop_name, prop_def in properties.items():
                    nested_fields[prop_name] = (
                        get_python_type(prop_def),
                        Field(description=prop_def.get('description', ''))
                    )
                return create_model(f"{model_name}_{field_def.get('name', 'nested')}", **nested_fields)
            else:
                return Dict[str, Any]
        else:
            return Any
    
    def get_item_type(item_def: Dict[str, Any]) -> Any:
        """Get the type for array items"""
        if isinstance(item_def, dict):
            return get_python_type(item_def)
        else:
            return Any
    
    # Build fields for the model
    model_fields = {}
    
    for field_name, field_def in field_definitions.items():
        # Get the Python type
        python_type = get_python_type(field_def)
        
        # Create field with description
        model_fields[field_name] = (
            python_type,
            Field(description=field_def.get('description', ''))
        )
    
    # Create the model
    if nested_as_root:
        # Return model with fields at root level (correct behavior)
        return create_model(model_name, **model_fields)
    else:
        # Wrap in another layer (incorrect - causes double nesting)
        wrapper_fields = {
            model_name.lower(): (create_model(f"{model_name}_inner", **model_fields), Field(...))
        }
        return create_model(model_name, **wrapper_fields)


# Example of correct usage
if __name__ == "__main__":
    # Field definitions from the database
    structure_fields = {
        "total_shelves": {
            "type": "integer",
            "description": "Total number of shelves visible in the planogram"
        },
        "shelves": {
            "type": "array",
            "description": "Array of shelf objects",
            "items": {
                "type": "object",
                "properties": {
                    "shelf_number": {
                        "type": "integer",
                        "description": "Shelf number from top (1) to bottom"
                    },
                    "has_price_rail": {
                        "type": "boolean",
                        "description": "Whether shelf has a visible price rail"
                    }
                }
            }
        },
        "non_product_elements": {
            "type": "object",
            "description": "Non-product elements in the planogram",
            "properties": {
                "security_devices": {
                    "type": "array",
                    "description": "Security devices with location",
                    "items": {"type": "string"}
                }
            }
        }
    }
    
    # Build model correctly (fields at root)
    CorrectModel = build_model_from_field_definitions(
        "StructureExtraction",
        structure_fields,
        nested_as_root=True
    )
    
    # This creates a model expecting:
    # {
    #     "total_shelves": 5,
    #     "shelves": [...],
    #     "non_product_elements": {...}
    # }
    
    # Build model incorrectly (double nesting)
    IncorrectModel = build_model_from_field_definitions(
        "structure_extraction",
        structure_fields,
        nested_as_root=False
    )
    
    # This creates a model expecting:
    # {
    #     "structure_extraction": {
    #         "total_shelves": 5,
    #         "shelves": [...],
    #         "non_product_elements": {...}
    #     }
    # }
    
    print("Correct model schema:")
    print(CorrectModel.schema_json(indent=2))
    print("\nIncorrect model schema (double nesting):")
    print(IncorrectModel.schema_json(indent=2))