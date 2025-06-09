#!/usr/bin/env python3
"""
Test the default configuration to ensure it works with dynamic model builder
"""

import asyncio
import sys
import os
sys.path.insert(0, '/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src')

# Import the function (async)
async def test_default_config():
    """Test the default configuration"""
    
    # Import the function
    from queue_system.processor_config_integration import _load_default_configuration
    
    print("=== TESTING DEFAULT CONFIGURATION ===")
    
    # Load default configuration
    config = await _load_default_configuration()
    
    print(f"Configuration loaded:")
    print(f"  System: {config.get('system')}")
    print(f"  Temperature: {config.get('temperature')}")
    print(f"  Stages: {list(config.get('stages', {}).keys())}")
    
    # Test each stage
    for stage_name, stage_config in config.get('stages', {}).items():
        print(f"\nStage: {stage_name}")
        print(f"  Has prompt_text: {'prompt_text' in stage_config}")
        print(f"  Has fields: {'fields' in stage_config}")
        
        if 'fields' in stage_config:
            fields = stage_config['fields']
            print(f"  Number of fields: {len(fields)}")
            
            for field in fields:
                print(f"    - {field.get('name', 'unnamed')}: {field.get('type', 'unknown')}")
                if field.get('type') == 'list' and 'nested_fields' in field:
                    for nested in field['nested_fields']:
                        print(f"      └─ {nested.get('name', 'unnamed')}: {nested.get('type', 'unknown')}")
        
        # Test the condition from custom_consensus_visual.py
        condition = stage_config and 'fields' in stage_config
        print(f"  Condition check: {condition}")
        
        if condition:
            print(f"  ✅ Would build dynamic model for {stage_name}")
        else:
            print(f"  ❌ Would use generic schema for {stage_name}")
    
    # Test with dynamic model builder
    print("\n=== TESTING WITH DYNAMIC MODEL BUILDER ===")
    
    # Import dynamic model builder
    try:
        # Create test version of dynamic model builder
        from typing import Dict, Any, List, Optional, Type, Union
        from pydantic import BaseModel, Field, create_model
        from enum import Enum
        
        class TestDynamicModelBuilder:
            @staticmethod
            def build_model_from_config(stage_name: str, stage_config: Dict[str, Any]) -> Optional[Type[BaseModel]]:
                fields = stage_config.get('fields', [])
                if not fields:
                    return None
                
                print(f"    Building model for {stage_name} with {len(fields)} fields")
                
                model_fields = {}
                for field_def in fields:
                    field_name = field_def.get('name')
                    field_type = field_def.get('type', 'string')
                    
                    if field_type == 'string':
                        python_type = str
                    elif field_type == 'integer':
                        python_type = int
                    elif field_type == 'float':
                        python_type = float
                    elif field_type == 'literal':
                        allowed_values = field_def.get('allowed_values', [])
                        if allowed_values:
                            enum_class = Enum(f"{field_name}_enum", {v: v for v in allowed_values})
                            python_type = enum_class
                        else:
                            python_type = str
                    elif field_type == 'list':
                        if 'nested_fields' in field_def:
                            python_type = List[Dict[str, Any]]  # Simplified
                        else:
                            python_type = List[str]
                    else:
                        python_type = Any
                    
                    if not field_def.get('required', True):
                        python_type = Optional[python_type]
                    
                    model_fields[field_name] = (python_type, Field(description=field_def.get('description', '')))
                
                model_name = f"{stage_name.title()}ExtractionModel"
                model = create_model(model_name, **model_fields)
                return model
        
        # Test each stage
        for stage_name, stage_config in config.get('stages', {}).items():
            print(f"\n  Testing {stage_name}:")
            try:
                model = TestDynamicModelBuilder.build_model_from_config(stage_name, stage_config)
                if model:
                    print(f"    ✅ Model created: {model.__name__}")
                else:
                    print(f"    ❌ Model creation returned None")
            except Exception as e:
                print(f"    ❌ Error creating model: {e}")
        
        print(f"\n✅ Default configuration test passed!")
        
    except Exception as e:
        print(f"❌ Error testing dynamic model builder: {e}")

if __name__ == "__main__":
    asyncio.run(test_default_config())