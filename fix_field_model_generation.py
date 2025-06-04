#!/usr/bin/env python3
"""
Fix for the structure_extraction field model generation issue.

The problem: When building Pydantic models from field definitions stored in the database,
the system is creating models with incorrect nesting, expecting structure_extraction.structure_extraction
instead of just the fields at the root level.

This script provides a corrected model builder and patches the extraction system.
"""

from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type, Union
import json


def build_model_from_db_fields(stage_name: str, field_definitions: Dict[str, Any]) -> Type[BaseModel]:
    """
    Build a Pydantic model from field definitions stored in the database.
    
    This corrects the double-nesting issue by putting fields at the root level
    instead of wrapping them in another layer.
    
    Args:
        stage_name: Name of the extraction stage (e.g., "structure_extraction")
        field_definitions: Dictionary of field definitions from the database
        
    Returns:
        A Pydantic model class with fields at the root level
    """
    
    def get_field_type(field_def: Dict[str, Any]) -> Any:
        """Convert database field definition to Python type"""
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
            item_def = field_def.get('items', {})
            item_type = get_field_type(item_def)
            return List[item_type]
        elif field_type == 'object':
            # For nested objects, create a nested model
            properties = field_def.get('properties', {})
            if properties:
                nested_fields = {}
                for prop_name, prop_def in properties.items():
                    nested_fields[prop_name] = (
                        get_field_type(prop_def),
                        Field(description=prop_def.get('description', ''))
                    )
                # Create nested model with a unique name
                nested_model_name = f"{stage_name}_{field_def.get('name', 'nested')}_model"
                return create_model(nested_model_name, **nested_fields)
            else:
                # If no properties defined, use generic dict
                return Dict[str, Any]
        else:
            return Any
    
    # Build fields for the model
    model_fields = {}
    
    for field_name, field_def in field_definitions.items():
        # Skip if field_def is not a dict (might be a string or other type)
        if not isinstance(field_def, dict):
            continue
            
        # Get the Python type
        python_type = get_field_type(field_def)
        
        # Check if field is required (default to False for safety)
        is_required = field_def.get('required', False)
        
        # Create field with description and optional status
        if is_required:
            model_fields[field_name] = (
                python_type,
                Field(description=field_def.get('description', ''))
            )
        else:
            model_fields[field_name] = (
                Optional[python_type],
                Field(default=None, description=field_def.get('description', ''))
            )
    
    # Create the model with fields at root level (NO WRAPPING!)
    model_name = f"{stage_name}_model"
    return create_model(model_name, **model_fields)


def patch_extraction_engine_model_building():
    """
    Patch for the extraction engine to use correct model building.
    
    This should be applied where the extraction engine builds models from field definitions.
    """
    
    # Example of how the extraction engine should build models:
    code = '''
    # In the extraction engine or wherever models are built from field definitions:
    
    async def build_model_for_stage(self, stage_name: str, field_definitions: Dict[str, Any]):
        """Build Pydantic model for a specific extraction stage"""
        
        # Use the corrected model builder
        from fix_field_model_generation import build_model_from_db_fields
        
        # Build model with fields at root level
        model = build_model_from_db_fields(stage_name, field_definitions)
        
        # Use this model with instructor
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            response_model=model  # This expects fields at root level
        )
        
        return response
    '''
    
    return code


# Test the fix
if __name__ == "__main__":
    # Example field definitions from the database
    structure_fields = {
        "total_shelves": {
            "type": "integer",
            "description": "Total number of shelves visible in the planogram",
            "required": True
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
    
    # Build the model correctly
    StructureModel = build_model_from_db_fields("structure_extraction", structure_fields)
    
    print("Model schema (correct - fields at root):")
    print(json.dumps(StructureModel.schema(), indent=2))
    
    # Test creating an instance
    print("\nTest instance creation:")
    try:
        instance = StructureModel(
            total_shelves=5,
            shelves=[
                {"shelf_number": 1, "has_price_rail": True},
                {"shelf_number": 2, "has_price_rail": False}
            ],
            non_product_elements={
                "security_devices": ["Camera at top left"]
            }
        )
        print("✓ Instance created successfully")
        print(f"  total_shelves: {instance.total_shelves}")
        print(f"  shelves count: {len(instance.shelves)}")
    except Exception as e:
        print(f"✗ Error creating instance: {e}")
    
    # Show what the incorrect double-nested structure would look like
    print("\n" + "="*60)
    print("INCORRECT double-nested structure would expect:")
    print({
        "structure_extraction": {
            "structure_extraction": {
                "total_shelves": 5,
                "shelves": [...],
                "non_product_elements": {...}
            }
        }
    })
    print("\nBut we're providing:")
    print({
        "total_shelves": 5,
        "shelves": [...],
        "non_product_elements": {...}
    })
    print("\nThis mismatch causes the validation error!")