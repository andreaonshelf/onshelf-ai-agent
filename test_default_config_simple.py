#!/usr/bin/env python3
"""
Test the default configuration structure directly
"""

def get_default_config():
    """Get the default configuration"""
    return {
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
                        'description': 'Total number of horizontal shelves visible',
                        'required': True
                    },
                    {
                        'name': 'fixture_type',
                        'type': 'literal',
                        'description': 'Type of retail fixture',
                        'required': True,
                        'allowed_values': ['wall_shelf', 'gondola', 'end_cap', 'cooler', 'freezer', 'other']
                    }
                ]
            },
            'products': {
                'prompt_text': 'Extract all products...',
                'fields': [
                    {
                        'name': 'products',
                        'type': 'list',
                        'description': 'List of all products found on the shelves',
                        'required': True,
                        'nested_fields': [
                            {
                                'name': 'brand',
                                'type': 'string',
                                'description': 'Product brand name',
                                'required': True
                            },
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

def test_config():
    """Test the configuration structure"""
    print("=== TESTING DEFAULT CONFIGURATION STRUCTURE ===")
    
    config = get_default_config()
    
    print(f"System: {config['system']}")
    print(f"Stages: {list(config['stages'].keys())}")
    
    for stage_name, stage_config in config['stages'].items():
        print(f"\nStage: {stage_name}")
        print(f"  Has prompt_text: {'prompt_text' in stage_config}")
        print(f"  Has fields: {'fields' in stage_config}")
        
        if 'fields' in stage_config:
            fields = stage_config['fields']
            print(f"  Number of fields: {len(fields)}")
            
            for field in fields:
                print(f"    - {field['name']}: {field['type']}")
                if field['type'] == 'list' and 'nested_fields' in field:
                    for nested in field['nested_fields']:
                        print(f"      └─ {nested['name']}: {nested['type']}")
        
        # Test the condition
        condition = stage_config and 'fields' in stage_config
        print(f"  Condition check: {condition} ({'✅ PASS' if condition else '❌ FAIL'})")
    
    print(f"\n=== SIMULATING QUEUE PROCESSING ===")
    
    # Simulate queue item with no config
    queue_item = {
        'id': 'test-123',
        'upload_id': 'upload-456',
        'status': 'pending'
        # NO extraction_config!
    }
    
    # Simulate processor logic
    extraction_config = queue_item.get('extraction_config') or {}
    
    if not extraction_config:
        print("No config found, loading default...")
        extraction_config = config  # This would be the default config
    
    print(f"Final config has stages: {'stages' in extraction_config}")
    print(f"Final config stages: {list(extraction_config.get('stages', {}).keys())}")
    
    # Simulate system dispatcher
    stages = extraction_config.get('stages', {})
    print(f"System dispatcher receives {len(stages)} stages")
    
    # Simulate custom_consensus_visual
    for stage in ['structure', 'products']:
        stage_config = stages.get(stage, {})
        condition = stage_config and 'fields' in stage_config
        print(f"Stage {stage}: condition = {condition} ({'✅ BUILD DYNAMIC' if condition else '❌ USE GENERIC'})")

if __name__ == "__main__":
    test_config()