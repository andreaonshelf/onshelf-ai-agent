#!/usr/bin/env python3
"""
Test dynamic model builder directly by copying the code
"""

from typing import Dict, Any, List, Optional, Type, Union
from pydantic import BaseModel, Field, create_model
from enum import Enum


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
            print(f"❌ No fields defined for stage {stage_name}")
            return None
            
        print(f"✅ Building dynamic model for stage {stage_name} with {len(fields)} fields")
        
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
        
        print(f"✅ Created dynamic model {model_name} with fields: {list(model_fields.keys())}")
        
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
        
        print(f"  Building field: {field_name} ({field_type})")
        
        # Map field types to Python types
        if field_type == 'string':
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


def test_real_scenario():
    """Test with realistic stage configuration"""
    
    print("=== TESTING REALISTIC SCENARIO ===")
    
    # Test structure stage config
    structure_config = {
        'prompt_text': 'Analyze the shelf structure...',
        'fields': [
            {
                'name': 'shelf_count',
                'type': 'integer', 
                'description': 'Number of shelves visible',
                'required': True
            },
            {
                'name': 'fixture_type',
                'type': 'string',
                'description': 'Type of shelf fixture',
                'required': True
            }
        ]
    }
    
    print(f"Structure config has fields: {'fields' in structure_config}")
    print(f"Number of fields: {len(structure_config.get('fields', []))}")
    
    # Test the condition from custom_consensus_visual.py line 579
    condition = structure_config and 'fields' in structure_config
    print(f"Condition check result: {condition}")
    
    if condition:
        model = DynamicModelBuilder.build_model_from_config('structure', structure_config)
        if model:
            print(f"✅ Model created: {model}")
            
            # Test instantiation
            try:
                instance = model(shelf_count=4, fixture_type='gondola')
                print(f"✅ Instance created: {instance.model_dump()}")
            except Exception as e:
                print(f"❌ Failed to create instance: {e}")
        else:
            print("❌ Model creation returned None")
    else:
        print("❌ Condition check failed - this is the issue!")


if __name__ == "__main__":
    test_real_scenario()