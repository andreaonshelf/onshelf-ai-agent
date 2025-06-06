#!/usr/bin/env python3
"""
Debug Dynamic Model Building Issue
Test to understand why dynamic models are not being built for structure stage
"""

import os
import sys
sys.path.insert(0, '/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src')

from config import SystemConfig
from orchestrator.system_dispatcher import SystemDispatcher
from utils import logger

async def test_dynamic_model_issue():
    """Test what stage configs are being passed to the extraction system"""
    
    # Create a test configuration that mimics what the UI should send
    test_configuration = {
        'system': 'custom_consensus',
        'temperature': 0.7,
        'orchestrator_model': 'claude-4-opus',
        'stages': {
            'structure': {
                'prompt_text': 'Analyze the shelf structure...',
                'fields': [
                    {
                        'name': 'shelf_count',
                        'type': 'integer', 
                        'description': 'Number of shelves',
                        'required': True
                    },
                    {
                        'name': 'fixture_type',
                        'type': 'string',
                        'description': 'Type of fixture',
                        'required': True
                    }
                ]
            },
            'products': {
                'prompt_text': 'Extract all products...',
                'fields': [
                    {
                        'name': 'products',
                        'type': 'list',
                        'description': 'List of products',
                        'required': True,
                        'nested_fields': [
                            {
                                'name': 'name',
                                'type': 'string',
                                'description': 'Product name',
                                'required': True
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    # Initialize system dispatcher
    config = SystemConfig()
    dispatcher = SystemDispatcher(config)
    
    # Test system creation with configuration
    from systems.base_system import ExtractionSystemFactory
    
    extraction_system = ExtractionSystemFactory.get_system(
        system_type='custom',
        config=config
    )
    
    # Simulate what system dispatcher does
    if test_configuration:
        extraction_system.configuration = test_configuration
        extraction_system.temperature = test_configuration.get('temperature', 0.7)
        extraction_system.stage_models = test_configuration.get('stage_models', {})
        
        # Extract stage prompts from stages configuration
        stage_prompts = {}
        stages = test_configuration.get('stages', {})
        for stage_id, stage_config in stages.items():
            if isinstance(stage_config, dict) and 'prompt_text' in stage_config:
                stage_prompts[stage_id] = stage_config['prompt_text']
        
        extraction_system.stage_prompts = stage_prompts
        
        # Pass the full stage configurations for dynamic model building
        extraction_system.stage_configs = stages
        
        print("=== DEBUG STAGE CONFIGS ===")
        print(f"Number of stage configs: {len(stages)}")
        for stage_id, stage_config in stages.items():
            print(f"\nStage: {stage_id}")
            print(f"  Has prompt_text: {'prompt_text' in stage_config}")
            print(f"  Has fields: {'fields' in stage_config}")
            if 'fields' in stage_config:
                print(f"  Number of fields: {len(stage_config['fields'])}")
                for field in stage_config['fields']:
                    print(f"    - {field.get('name', 'unnamed')}: {field.get('type', 'unknown')}")
    
    # Test dynamic model building directly
    from extraction.dynamic_model_builder import DynamicModelBuilder
    
    print("\n=== TESTING DYNAMIC MODEL BUILDER ===")
    
    for stage_name, stage_config in stages.items():
        print(f"\nTesting stage: {stage_name}")
        print(f"Stage config keys: {list(stage_config.keys())}")
        
        # Test if fields exist
        fields = stage_config.get('fields', [])
        if not fields:
            print(f"  ❌ No fields found for stage {stage_name}")
            continue
            
        print(f"  ✅ Found {len(fields)} fields for stage {stage_name}")
        
        # Try to build dynamic model
        try:
            dynamic_model = DynamicModelBuilder.build_model_from_config(stage_name, stage_config)
            if dynamic_model:
                print(f"  ✅ Dynamic model built successfully: {dynamic_model.__name__}")
                
                # Test instantiation
                try:
                    if stage_name == 'structure':
                        test_data = {'shelf_count': 4, 'fixture_type': 'gondola'}
                    else:
                        test_data = {'products': [{'name': 'Test Product'}]}
                    
                    instance = dynamic_model(**test_data)
                    print(f"  ✅ Model instance created successfully")
                    print(f"    Data: {instance.model_dump()}")
                except Exception as e:
                    print(f"  ❌ Failed to create model instance: {e}")
            else:
                print(f"  ❌ Dynamic model builder returned None")
        except Exception as e:
            print(f"  ❌ Failed to build dynamic model: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_dynamic_model_issue())