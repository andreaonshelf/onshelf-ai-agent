"""
Field Schema Builder API
Builds Pydantic models from field definitions for Instructor
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type, Union
import json
from enum import Enum

from ..utils import logger

router = APIRouter(prefix="/api/schema", tags=["Schema Builder"])


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    OBJECT = "object"


class FieldDefinition(BaseModel):
    name: str
    type: FieldType
    description: str
    required: bool = True
    default: Any = None
    examples: Optional[List[str]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    enum_values: Optional[List[str]] = None
    list_item_type: Optional[str] = None  # For LIST type
    nested_fields: Optional[List['FieldDefinition']] = None  # For OBJECT type


class SchemaDefinition(BaseModel):
    name: str
    description: str
    fields: List[FieldDefinition]
    version: str = "1.0"


def build_pydantic_field(field_def: FieldDefinition) -> tuple:
    """Build a Pydantic field from field definition"""
    
    # Determine the Python type
    if field_def.type == FieldType.STRING:
        if field_def.enum_values:
            # Create enum type
            enum_class = Enum(f"{field_def.name}_enum", {v: v for v in field_def.enum_values})
            field_type = enum_class
        else:
            field_type = str
    elif field_def.type == FieldType.INTEGER:
        field_type = int
    elif field_def.type == FieldType.FLOAT:
        field_type = float
    elif field_def.type == FieldType.BOOLEAN:
        field_type = bool
    elif field_def.type == FieldType.LIST:
        # Determine list item type
        if field_def.list_item_type == "string":
            field_type = List[str]
        elif field_def.list_item_type == "integer":
            field_type = List[int]
        elif field_def.list_item_type == "float":
            field_type = List[float]
        else:
            field_type = List[Any]
    elif field_def.type == FieldType.DICT:
        field_type = Dict[str, Any]
    elif field_def.type == FieldType.OBJECT and field_def.nested_fields:
        # Build nested model
        nested_fields = {}
        for nested_field in field_def.nested_fields:
            nested_name, nested_info = build_pydantic_field(nested_field)
            nested_fields[nested_name] = nested_info
        field_type = create_model(f"{field_def.name}_model", **nested_fields)
    else:
        field_type = Any
    
    # Make optional if not required
    if not field_def.required:
        field_type = Optional[field_type]
    
    # Build field info
    field_kwargs = {
        "description": field_def.description
    }
    
    if field_def.default is not None:
        field_kwargs["default"] = field_def.default
    elif not field_def.required:
        field_kwargs["default"] = None
    
    if field_def.min_value is not None:
        field_kwargs["ge"] = field_def.min_value
    if field_def.max_value is not None:
        field_kwargs["le"] = field_def.max_value
    
    if field_def.examples:
        field_kwargs["examples"] = field_def.examples
    
    return field_def.name, (field_type, Field(**field_kwargs))


def build_pydantic_model(schema_def: SchemaDefinition) -> Type[BaseModel]:
    """Build a Pydantic model from schema definition"""
    
    fields = {}
    for field_def in schema_def.fields:
        field_name, field_info = build_pydantic_field(field_def)
        fields[field_name] = field_info
    
    # Create the model
    model = create_model(
        schema_def.name,
        __doc__=schema_def.description,
        **fields
    )
    
    return model


@router.post("/build")
async def build_schema(schema_def: SchemaDefinition):
    """Build a Pydantic model from field definitions"""
    try:
        # Build the model
        model = build_pydantic_model(schema_def)
        
        # Generate example schema
        example_schema = model.model_json_schema()
        
        # Generate example instance
        example_data = {}
        for field in schema_def.fields:
            if field.examples and len(field.examples) > 0:
                example_data[field.name] = field.examples[0]
            elif field.type == FieldType.STRING:
                example_data[field.name] = "example"
            elif field.type == FieldType.INTEGER:
                example_data[field.name] = 1
            elif field.type == FieldType.FLOAT:
                example_data[field.name] = 1.0
            elif field.type == FieldType.BOOLEAN:
                example_data[field.name] = True
            elif field.type == FieldType.LIST:
                example_data[field.name] = []
            elif field.type == FieldType.DICT:
                example_data[field.name] = {}
        
        # Validate example
        try:
            instance = model(**example_data)
            validation_result = "Valid"
        except Exception as e:
            validation_result = f"Validation error: {str(e)}"
        
        return {
            "success": True,
            "model_name": schema_def.name,
            "json_schema": example_schema,
            "example_data": example_data,
            "validation_result": validation_result,
            "field_count": len(schema_def.fields)
        }
        
    except Exception as e:
        logger.error(f"Failed to build schema: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/examples/product-extraction")
async def get_product_extraction_example():
    """Get example schema for product extraction"""
    
    example = {
        "name": "ProductExtraction",
        "description": "Extract product information from shelf images",
        "version": "1.0",
        "fields": [
            {
                "name": "products",
                "type": "list",
                "description": "List of all products visible on the shelf",
                "required": True,
                "list_item_type": "object",
                "nested_fields": [
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Full product name as shown on packaging",
                        "required": True,
                        "examples": ["Coca-Cola Zero Sugar 330ml", "Pepsi Max 500ml"]
                    },
                    {
                        "name": "brand",
                        "type": "string",
                        "description": "Brand or manufacturer name",
                        "required": True,
                        "examples": ["Coca-Cola", "Pepsi", "Red Bull"]
                    },
                    {
                        "name": "price",
                        "type": "float",
                        "description": "Product price in local currency",
                        "required": False,
                        "min_value": 0,
                        "examples": [2.99, 1.50]
                    },
                    {
                        "name": "position",
                        "type": "object",
                        "description": "Product position on shelf",
                        "required": True,
                        "nested_fields": [
                            {
                                "name": "shelf_number",
                                "type": "integer",
                                "description": "Shelf number from top (1-based)",
                                "required": True,
                                "min_value": 1,
                                "examples": [1, 2, 3]
                            },
                            {
                                "name": "position_from_left",
                                "type": "integer",
                                "description": "Position from left side of shelf (1-based)",
                                "required": True,
                                "min_value": 1,
                                "examples": [1, 2, 3, 4]
                            }
                        ]
                    },
                    {
                        "name": "facings",
                        "type": "integer",
                        "description": "Number of identical products placed side by side",
                        "required": True,
                        "min_value": 1,
                        "default": 1,
                        "examples": [1, 2, 3]
                    },
                    {
                        "name": "pack_size",
                        "type": "string",
                        "description": "Package size or volume",
                        "required": False,
                        "examples": ["330ml", "500ml", "6-pack"]
                    },
                    {
                        "name": "is_promotional",
                        "type": "boolean",
                        "description": "Whether product has promotional pricing or signage",
                        "required": False,
                        "default": False
                    }
                ]
            },
            {
                "name": "shelf_structure",
                "type": "object",
                "description": "Overall shelf structure information",
                "required": True,
                "nested_fields": [
                    {
                        "name": "total_shelves",
                        "type": "integer",
                        "description": "Total number of shelves",
                        "required": True,
                        "min_value": 1,
                        "examples": [3, 4, 5]
                    },
                    {
                        "name": "shelf_type",
                        "type": "string",
                        "description": "Type of shelf/fixture",
                        "required": False,
                        "enum_values": ["standard", "cooler", "end_cap", "display_unit"],
                        "default": "standard"
                    }
                ]
            }
        ]
    }
    
    return example


@router.get("/examples/structure-analysis")
async def get_structure_analysis_example():
    """Get example schema for shelf structure analysis"""
    
    example = {
        "name": "ShelfStructureAnalysis",
        "description": "Analyze the physical structure of retail shelving",
        "version": "1.0",
        "fields": [
            {
                "name": "shelf_count",
                "type": "integer",
                "description": "Total number of horizontal shelves",
                "required": True,
                "min_value": 1,
                "max_value": 10,
                "examples": [3, 4, 5]
            },
            {
                "name": "sections",
                "type": "list",
                "description": "Vertical sections of the shelf unit",
                "required": True,
                "list_item_type": "object",
                "nested_fields": [
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Section identifier",
                        "required": True,
                        "examples": ["Left", "Center", "Right"]
                    },
                    {
                        "name": "width_estimate",
                        "type": "float",
                        "description": "Estimated width in meters",
                        "required": False,
                        "min_value": 0.1,
                        "max_value": 5.0
                    }
                ]
            },
            {
                "name": "fixture_type",
                "type": "string",
                "description": "Type of shelving fixture",
                "required": True,
                "enum_values": ["gondola", "wall_unit", "cooler", "freezer", "end_cap"],
                "default": "gondola"
            },
            {
                "name": "dimensions",
                "type": "object",
                "description": "Overall dimensions of the fixture",
                "required": False,
                "nested_fields": [
                    {
                        "name": "height_meters",
                        "type": "float",
                        "description": "Total height in meters",
                        "required": False,
                        "min_value": 0.5,
                        "max_value": 3.0
                    },
                    {
                        "name": "width_meters",
                        "type": "float",
                        "description": "Total width in meters",
                        "required": False,
                        "min_value": 0.5,
                        "max_value": 10.0
                    }
                ]
            }
        ]
    }
    
    return example


# Make FieldDefinition support forward references
FieldDefinition.model_rebuild()