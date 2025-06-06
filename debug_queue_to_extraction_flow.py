#!/usr/bin/env python3
"""
Debug the flow from queue processing to extraction to see where fields are lost
"""

import sys
import os
sys.path.insert(0, '/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src')

# Mock configuration that simulates what queue processor would pass
def test_configuration_flow():
    """Test the exact flow from queue to extraction"""
    
    print("=== TESTING CONFIGURATION FLOW ===")
    
    # Mock configuration as it would come from queue processor
    queue_config = {
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
                    }
                ]
            }
        }
    }
    
    print("Original configuration:")
    print(f"  Has stages: {'stages' in queue_config}")
    print(f"  Number of stages: {len(queue_config.get('stages', {}))}")
    
    for stage_id, stage_config in queue_config.get('stages', {}).items():
        print(f"  Stage {stage_id}:")
        print(f"    Keys: {list(stage_config.keys())}")
        print(f"    Has fields: {'fields' in stage_config}")
        print(f"    Fields count: {len(stage_config.get('fields', []))}")
    
    # Test system dispatcher logic
    print("\n=== SYSTEM DISPATCHER PROCESSING ===")
    
    stages = queue_config.get('stages', {})
    
    # Extract stage prompts (this is what system dispatcher does)
    stage_prompts = {}
    for stage_id, stage_config in stages.items():
        if isinstance(stage_config, dict) and 'prompt_text' in stage_config:
            stage_prompts[stage_id] = stage_config['prompt_text']
    
    print(f"Stage prompts extracted: {list(stage_prompts.keys())}")
    
    # This is what gets assigned to extraction_system.stage_configs
    extraction_system_stage_configs = stages
    
    print(f"Stage configs passed to extraction system:")
    for stage_id, stage_config in extraction_system_stage_configs.items():
        print(f"  Stage {stage_id}:")
        print(f"    Type: {type(stage_config)}")
        print(f"    Keys: {list(stage_config.keys()) if isinstance(stage_config, dict) else 'Not dict'}")
        print(f"    Has fields: {'fields' in stage_config if isinstance(stage_config, dict) else False}")
    
    # Test custom_consensus_visual logic
    print("\n=== CUSTOM CONSENSUS VISUAL PROCESSING ===")
    
    for stage in ['structure', 'products']:
        # This is the exact logic from custom_consensus_visual.py line 573
        stage_config = extraction_system_stage_configs.get(stage, {})
        
        print(f"Stage {stage}:")
        print(f"  stage_config type: {type(stage_config)}")
        print(f"  stage_config keys: {list(stage_config.keys()) if isinstance(stage_config, dict) else 'Not dict'}")
        print(f"  has fields key: {'fields' in stage_config if isinstance(stage_config, dict) else False}")
        
        # The exact condition check
        condition = stage_config and 'fields' in stage_config
        print(f"  Condition (stage_config and 'fields' in stage_config): {condition}")
        
        if condition:
            fields = stage_config.get('fields', [])
            print(f"  ✅ Would build dynamic model with {len(fields)} fields")
            for field in fields:
                print(f"    - {field.get('name', 'unnamed')}: {field.get('type', 'unknown')}")
        else:
            print(f"  ❌ Would use generic schema")

def test_empty_configuration():
    """Test what happens with empty/missing configuration"""
    
    print("\n\n=== TESTING EMPTY CONFIGURATION ===")
    
    # This simulates what happens when no configuration is passed
    empty_config = None
    
    # System dispatcher logic
    configuration = empty_config
    stages = configuration.get('stages', {}) if configuration else {}
    
    print(f"Configuration: {configuration}")
    print(f"Stages: {stages}")
    print(f"Number of stages: {len(stages)}")
    
    # Custom consensus visual logic
    for stage in ['structure', 'products']:
        stage_config = stages.get(stage, {})
        condition = stage_config and 'fields' in stage_config
        print(f"Stage {stage}: condition = {condition}")

def test_partial_configuration():
    """Test configuration without fields"""
    
    print("\n\n=== TESTING PARTIAL CONFIGURATION ===")
    
    # Configuration with stages but no fields (old format)
    partial_config = {
        'system': 'custom_consensus',
        'stages': {
            'structure': {
                'prompt_text': 'Analyze the shelf structure...'
                # NO fields!
            }
        }
    }
    
    stages = partial_config.get('stages', {})
    
    for stage_id, stage_config in stages.items():
        print(f"Stage {stage_id}:")
        print(f"  Keys: {list(stage_config.keys())}")
        print(f"  Has fields: {'fields' in stage_config}")
        condition = stage_config and 'fields' in stage_config
        print(f"  Condition: {condition}")

if __name__ == "__main__":
    test_configuration_flow()
    test_empty_configuration()
    test_partial_configuration()
    
    print("\n=== SUMMARY ===")
    print("✅ Configuration flow works when fields are present")
    print("❌ Problem occurs when:")
    print("  1. No configuration is passed (None)")
    print("  2. Configuration has stages but no 'fields' key")
    print("  3. Fields are stored separately and not attached to stage config")
    
    print("\n🔍 Check:")
    print("  1. Are queue items saving configurations with fields?")
    print("  2. Are saved configurations being loaded for extractions?")
    print("  3. Are fields being attached when loading configurations?")