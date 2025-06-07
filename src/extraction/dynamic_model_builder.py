"""
Dynamic Model Builder for User-Defined Fields
Converts UI field definitions to Pydantic models for extraction
"""

from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, Field, create_model
from enum import Enum

from ..utils import logger


class DynamicModelBuilder:
    """Builds Pydantic models from user-defined field configurations"""
    
    @staticmethod
    def build_model_from_config(stage_name: str, stage_config: Dict[str, Any]) -> Optional[Type[BaseModel]]:
        """
        Build a Pydantic model from stage configuration fields
        
        Args:
            stage_name: Name of the stage (e.g., 'structure', 'products')
            stage_config: Stage configuration containing fields definition
            
        Returns:
            Pydantic model class or None if no fields defined
        """
        fields = stage_config.get('fields', [])
        if not fields:
            # Some stages like 'visual' legitimately have no fields (they do comparison, not extraction)
            if stage_name in ['visual', 'comparison']:
                logger.info(
                    f"Stage {stage_name} has no fields (comparison-only stage)",
                    component="dynamic_model_builder"
                )
                return None
            else:
                logger.error(
                    f"No fields defined for stage {stage_name} - this should not happen! "
                    f"Fields must be loaded from the database.",
                    component="dynamic_model_builder"
                )
                raise ValueError(f"No field definitions found for stage {stage_name}. Check database configuration.")
            
        logger.info(
            f"Building dynamic model for stage {stage_name} with {len(fields)} fields",
            component="dynamic_model_builder",
            field_names=[f.get('name') for f in fields]
        )
        
        model_fields = {}
        
        for field_def in fields:
            field_name, field_info = DynamicModelBuilder._build_field(field_def)
            if field_name and field_info:
                model_fields[field_name] = field_info
        
        # Create the model with a descriptive name
        model_name = f"{stage_name.title()}ExtractionModel"
        model = create_model(
            model_name,
            __doc__=f"Dynamic model for {stage_name} extraction based on user-defined fields",
            **model_fields
        )
        
        logger.info(
            f"Created dynamic model {model_name} with fields: {list(model_fields.keys())}",
            component="dynamic_model_builder"
        )
        
        return model
    
    @staticmethod
    def _build_field(field_def: Dict[str, Any]) -> tuple:
        """Build a single Pydantic field from field definition"""
        
        field_name = field_def.get('name')
        field_type = field_def.get('type', 'string')
        description = field_def.get('description', '')
        required = field_def.get('required', True)
        
        if not field_name:
            return None, None
        
        # Map field types to Python types
        if field_type == 'string':
            # Check if this string field has enum constraints
            allowed_values = field_def.get('allowed_values', [])
            if allowed_values:
                # Create enum for string fields with allowed_values
                enum_class = Enum(f"{field_name}_enum", {v: v for v in allowed_values})
                python_type = enum_class
            else:
                python_type = str
        elif field_type == 'literal':
            # Handle literal/enum types
            allowed_values = field_def.get('allowed_values', [])
            if allowed_values:
                # Create enum
                enum_class = Enum(f"{field_name}_enum", {v: v for v in allowed_values})
                python_type = enum_class
            else:
                python_type = str
        elif field_type == 'integer':
            python_type = int
        elif field_type == 'float':
            python_type = float
        elif field_type == 'boolean':
            python_type = bool
        elif field_type == 'list':
            # Check for list item type
            item_type = field_def.get('list_item_type', 'string')
            nested_fields = field_def.get('nested_fields', [])
            
            if nested_fields:
                # Build nested model for list items
                nested_model = DynamicModelBuilder._build_nested_model(
                    f"{field_name}_item",
                    nested_fields
                )
                python_type = List[nested_model]
            elif item_type == 'string':
                python_type = List[str]
            elif item_type == 'integer':
                python_type = List[int]
            elif item_type == 'object':
                python_type = List[Dict[str, Any]]
            else:
                python_type = List[Any]
        elif field_type == 'dict':
            python_type = Dict[str, Any]
        elif field_type == 'object':
            # Build nested model
            nested_fields = field_def.get('nested_fields', [])
            if nested_fields:
                python_type = DynamicModelBuilder._build_nested_model(field_name, nested_fields)
            else:
                python_type = Dict[str, Any]
        else:
            python_type = Any
        
        # Make optional if not required
        if not required:
            python_type = Optional[python_type]
        
        # Build field kwargs
        field_kwargs = {
            "description": description
        }
        
        # If this is an enum field, enhance description with valid values
        allowed_values = field_def.get('allowed_values', [])
        if allowed_values:
            quoted_values = [f'"{v}"' for v in allowed_values]
            enum_instruction = f" MUST use exactly one of: {', '.join(quoted_values)}"
            field_kwargs["description"] = f"{description}.{enum_instruction}"
        
        # Add default if not required
        if not required:
            field_kwargs["default"] = None
        
        return field_name, (python_type, Field(**field_kwargs))
    
    @staticmethod
    def _build_nested_model(model_name: str, nested_fields: List[Dict[str, Any]]) -> Type[BaseModel]:
        """Build a nested Pydantic model from nested field definitions"""
        
        nested_model_fields = {}
        
        for nested_field in nested_fields:
            field_name, field_info = DynamicModelBuilder._build_field(nested_field)
            if field_name and field_info:
                nested_model_fields[field_name] = field_info
        
        # Create nested model with unique name
        safe_name = model_name.replace(' ', '_').replace('-', '_')
        nested_model = create_model(
            f"{safe_name}_nested",
            **nested_model_fields
        )
        
        return nested_model