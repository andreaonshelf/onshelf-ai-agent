"""
Dynamic Model Builder for Extraction Pipeline
Correctly builds Pydantic models from field definitions without double nesting
"""

from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type, Union
import json
from enum import Enum

from ..utils import logger


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


def build_extraction_model(stage_name: str, field_definitions: Dict[str, Any]) -> Type[BaseModel]:
    """
    Build a Pydantic model from field definitions for a specific extraction stage.
    
    IMPORTANT: This creates a model with fields at the ROOT level, not nested
    under the stage name. This prevents the double-nesting bug.
    
    Args:
        stage_name: Name of the extraction stage (e.g., "structure_extraction")
        field_definitions: Dictionary of field definitions from the database/config
        
    Returns:
        A Pydantic model class with fields at the root level
    """
    
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
                nested_model_name = f"{stage_name}_{field_name}_nested"
                return create_model(nested_model_name, **nested_fields)
            else:
                # Generic dict if no properties specified
                return Dict[str, Any]
        else:
            return Any
    
    # Build fields for the model
    model_fields = {}
    
    for field_name, field_def in field_definitions.items():
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
        component="dynamic_model_builder"
    )
    
    # Create model with fields at ROOT level - NO WRAPPING!
    return create_model(model_name, **model_fields)


def build_model_from_stage_config(stage_config: Dict[str, Any]) -> Type[BaseModel]:
    """
    Build a Pydantic model from a stage configuration.
    
    Args:
        stage_config: Stage configuration with fields definition
        
    Returns:
        A Pydantic model class
    """
    stage_name = stage_config.get('name', 'extraction')
    fields = stage_config.get('fields', {})
    
    # Convert fields list to dict if necessary
    if isinstance(fields, list):
        fields_dict = {}
        for field in fields:
            if isinstance(field, dict) and 'name' in field:
                field_name = field['name']
                fields_dict[field_name] = {
                    'type': field.get('type', 'string'),
                    'description': field.get('description', ''),
                    'required': field.get('required', False)
                }
        fields = fields_dict
    
    return build_extraction_model(stage_name, fields)


# Example usage and testing
if __name__ == "__main__":
    # Test with structure extraction fields
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
        }
    }
    
    # Build the model
    StructureModel = build_extraction_model("structure_extraction", structure_fields)
    
    print("Model schema:")
    print(json.dumps(StructureModel.model_json_schema(), indent=2))
    
    # Test instance creation
    try:
        instance = StructureModel(
            total_shelves=3,
            shelves=[
                {"shelf_number": 1, "has_price_rail": True},
                {"shelf_number": 2, "has_price_rail": False}
            ]
        )
        print("\n✓ Instance created successfully!")
        print(f"Data: {instance.model_dump()}")
    except Exception as e:
        print(f"\n✗ Error: {e}")