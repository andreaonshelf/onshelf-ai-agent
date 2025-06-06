#!/usr/bin/env python3
"""
Simple test of dynamic model building
"""

import sys
import os
sys.path.insert(0, '/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src')

# Test data similar to what should come from UI
test_stage_config = {
    'prompt_text': 'Analyze the shelf structure and count shelves...',
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

def test_dynamic_model_building():
    """Test the dynamic model builder directly"""
    
    print("=== TESTING DYNAMIC MODEL BUILDER ===")
    print(f"Stage config keys: {list(test_stage_config.keys())}")
    print(f"Has fields: {'fields' in test_stage_config}")
    print(f"Number of fields: {len(test_stage_config.get('fields', []))}")
    
    # Import and test the dynamic model builder
    try:
        from extraction.dynamic_model_builder import DynamicModelBuilder
        
        print("\n=== Building Dynamic Model ===")
        dynamic_model = DynamicModelBuilder.build_model_from_config('structure', test_stage_config)
        
        if dynamic_model:
            print(f"✅ Dynamic model built successfully: {dynamic_model.__name__}")
            
            # Test creating an instance
            try:
                test_data = {
                    'shelf_count': 4,
                    'fixture_type': 'gondola'
                }
                instance = dynamic_model(**test_data)
                print(f"✅ Model instance created: {instance.model_dump()}")
                return True
            except Exception as e:
                print(f"❌ Failed to create instance: {e}")
                return False
        else:
            print("❌ Dynamic model builder returned None")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_stage_config_format():
    """Test what format stage configs should have"""
    
    print("\n=== STAGE CONFIG ANALYSIS ===")
    
    # Test with fields
    config_with_fields = {
        'prompt_text': 'Test prompt',
        'fields': [
            {'name': 'test_field', 'type': 'string', 'description': 'Test', 'required': True}
        ]
    }
    
    # Test without fields
    config_without_fields = {
        'prompt_text': 'Test prompt'
    }
    
    print("Config with fields:", 'fields' in config_with_fields and len(config_with_fields['fields']) > 0)
    print("Config without fields:", 'fields' in config_without_fields and len(config_without_fields.get('fields', [])) > 0)
    
    # This is the check that custom_consensus_visual.py does
    for config_name, config in [('with_fields', config_with_fields), ('without_fields', config_without_fields)]:
        condition = config and 'fields' in config
        print(f"Condition '{config_name}': stage_config and 'fields' in stage_config = {condition}")

if __name__ == "__main__":
    test_stage_config_format()
    success = test_dynamic_model_building()
    
    if success:
        print("\n✅ Dynamic model building works correctly")
        print("🔍 The issue is likely that stage configs don't contain 'fields' in production")
    else:
        print("\n❌ Dynamic model building failed")