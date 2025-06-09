#!/usr/bin/env python3
"""
Test saving and loading configuration with fields
"""

import os
import json
from supabase import create_client

# Test configuration that mimics what UI should send
test_config_data = {
    "name": "Test Config with Fields",
    "description": "Testing field preservation",
    "system": "custom_consensus",
    "max_budget": 2.0,
    "temperature": 0.7,
    "orchestrator_model": "claude-4-opus",
    "orchestrator_prompt": "Test orchestrator prompt",
    "stages": {
        "structure": {
            "prompt_id": "test_structure_prompt",
            "prompt_text": "Analyze the shelf structure...",
            "fields": [
                {
                    "name": "shelf_count",
                    "type": "integer",
                    "description": "Number of shelves",
                    "required": True
                },
                {
                    "name": "fixture_type", 
                    "type": "string",
                    "description": "Type of fixture",
                    "required": True
                }
            ],
            "models": ["gpt-4o", "claude-3-sonnet"]
        },
        "products": {
            "prompt_id": "test_products_prompt",
            "prompt_text": "Extract all products...",
            "fields": [
                {
                    "name": "products",
                    "type": "list",
                    "description": "List of products",
                    "required": True,
                    "nested_fields": [
                        {
                            "name": "name",
                            "type": "string", 
                            "description": "Product name",
                            "required": True
                        }
                    ]
                }
            ],
            "models": ["gpt-4o", "claude-3-sonnet"]
        }
    }
}

def test_configuration_save_load():
    """Test saving and loading configuration with fields"""
    
    # Initialize Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("=== TESTING CONFIGURATION SAVE/LOAD ===")
    
    try:
        # Save configuration (mimicking the API)
        extraction_config = {
            "system": test_config_data["system"],
            "max_budget": test_config_data["max_budget"],
            "temperature": test_config_data["temperature"],
            "orchestrator_model": test_config_data["orchestrator_model"],
            "orchestrator_prompt": test_config_data["orchestrator_prompt"],
            "stages": test_config_data["stages"]
        }
        
        config_record = {
            "template_id": f"test_config_debug_123",
            "prompt_type": "configuration",
            "model_type": "universal",
            "prompt_version": "1.0",
            "prompt_text": test_config_data["orchestrator_prompt"],
            "name": test_config_data["name"],
            "description": test_config_data["description"],
            "stage_type": "configuration",
            "extraction_config": extraction_config,
            "is_active": True,
            "is_user_created": True,
            "is_public": False,
            "tags": ["test", "debug"]
        }
        
        print("Saving configuration...")
        result = supabase.table("prompt_templates").insert(config_record).execute()
        
        if not result.data:
            print("❌ Failed to save configuration")
            return False
            
        saved_id = result.data[0]["prompt_id"]
        print(f"✅ Configuration saved with ID: {saved_id}")
        
        # Load configuration back (mimicking the API)
        print("Loading configuration...")
        load_result = supabase.table("prompt_templates").select("*").eq("prompt_id", saved_id).execute()
        
        if not load_result.data:
            print("❌ Failed to load configuration")
            return False
            
        loaded_record = load_result.data[0]
        loaded_config = loaded_record.get("extraction_config", {})
        
        print(f"✅ Configuration loaded")
        
        # Check if stages have fields
        loaded_stages = loaded_config.get("stages", {})
        print(f"Number of stages loaded: {len(loaded_stages)}")
        
        for stage_id, stage_config in loaded_stages.items():
            print(f"\nStage: {stage_id}")
            print(f"  Keys: {list(stage_config.keys()) if isinstance(stage_config, dict) else 'Not a dict'}")
            print(f"  Has fields: {'fields' in stage_config if isinstance(stage_config, dict) else False}")
            
            if isinstance(stage_config, dict) and 'fields' in stage_config:
                fields = stage_config['fields']
                print(f"  Number of fields: {len(fields)}")
                for field in fields:
                    print(f"    - {field.get('name', 'unnamed')}: {field.get('type', 'unknown')}")
            else:
                print("  ❌ No fields found!")
        
        # Test the condition that custom_consensus_visual.py uses
        print("\n=== TESTING EXTRACTION CONDITIONS ===")
        for stage_name in ['structure', 'products']:
            stage_config = loaded_stages.get(stage_name, {})
            condition = stage_config and 'fields' in stage_config
            print(f"Stage {stage_name}: condition check = {condition}")
            
            if condition:
                print(f"  ✅ Would build dynamic model for {stage_name}")
            else:
                print(f"  ❌ Would use generic schema for {stage_name}")
        
        # Clean up
        print(f"\nCleaning up test record...")
        supabase.table("prompt_templates").delete().eq("prompt_id", saved_id).execute()
        print("✅ Test record deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_configuration_save_load()
    if success:
        print("\n✅ Configuration save/load test passed")
    else:
        print("\n❌ Configuration save/load test failed")