#!/usr/bin/env python3
"""Debug queue item 9 processing with actual system creation"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import json
from src.config import SystemConfig
from src.orchestrator.system_dispatcher import SystemDispatcher
from src.systems import ExtractionSystemFactory
from src.systems.langgraph_system import LangGraphConsensusSystem

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

async def debug_queue_item_9():
    print("Debug: Queue Item 9 Processing Pipeline")
    print("=" * 60)
    
    # Get queue item 9
    response = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()
    if not response.data:
        print("❌ Queue item 9 not found")
        return
    
    queue_item = response.data[0]
    
    # Extract configuration like the queue processor does
    extraction_config = queue_item.get('extraction_config', {})
    model_config = queue_item.get('model_config', {})
    
    # Use extraction_config if it has stages, otherwise fall back to model_config
    configuration = extraction_config if extraction_config.get('stages') else model_config
    
    # Determine system to use
    system = configuration.get('system') or queue_item.get('current_extraction_system', 'custom_consensus')
    
    print(f"Configuration type: {'extraction_config' if extraction_config.get('stages') else 'model_config'}")
    print(f"System: {system}")
    print(f"Has stages: {bool(configuration.get('stages'))}")
    print(f"Stages: {list(configuration.get('stages', {}).keys())}")
    
    # Create system config
    config = SystemConfig()
    
    # Test 1: Direct system creation
    print(f"\n" + "=" * 60)
    print("Test 1: Direct LangGraph System Creation")
    print("=" * 60)
    
    try:
        # Create LangGraph system directly
        langgraph_system = LangGraphConsensusSystem(config, queue_item_id=9)
        
        # Manually set the configuration like SystemDispatcher does
        langgraph_system.configuration = configuration
        stages = configuration.get('stages', {})
        langgraph_system.stage_configs = stages
        
        print(f"✅ LangGraph system created successfully")
        print(f"System has stage_configs: {hasattr(langgraph_system, 'stage_configs')}")
        print(f"Stage configs: {getattr(langgraph_system, 'stage_configs', {}).keys()}")
        
        # Test the specific method that's failing
        print(f"\nTesting _get_output_schema_for_stage('structure')...")
        
        structure_schema = langgraph_system._get_output_schema_for_stage('structure')
        print(f"✅ Structure schema created: {structure_schema}")
        print(f"Schema name: {structure_schema.__name__}")
        
    except Exception as e:
        print(f"❌ Direct system creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: SystemDispatcher creation
    print(f"\n" + "=" * 60)
    print("Test 2: SystemDispatcher Creation")
    print("=" * 60)
    
    try:
        # Create SystemDispatcher like the queue processor does
        dispatcher = SystemDispatcher(config, queue_item_id=9)
        
        # Test extraction system creation through ExtractionSystemFactory
        system_type_map = {
            'custom_consensus': 'custom',
            'custom_consensus_visual': 'custom_visual',
            'langgraph': 'langgraph',
            'langgraph_based': 'langgraph',
            'hybrid': 'hybrid'
        }
        
        system_type = system_type_map.get(system, 'custom')
        
        print(f"Creating {system_type} system through factory...")
        
        extraction_system = ExtractionSystemFactory.get_system(
            system_type=system_type,
            config=config,
            queue_item_id=9
        )
        
        print(f"✅ Extraction system created: {type(extraction_system)}")
        
        # Set configuration like SystemDispatcher does
        extraction_system.configuration = configuration
        stages = configuration.get('stages', {})
        extraction_system.stage_configs = stages
        
        print(f"Set stage_configs: {list(extraction_system.stage_configs.keys())}")
        
        # Test schema generation
        if hasattr(extraction_system, '_get_output_schema_for_stage'):
            print(f"\nTesting schema generation for structure...")
            structure_schema = extraction_system._get_output_schema_for_stage('structure')
            print(f"✅ Structure schema: {structure_schema}")
        else:
            print(f"❌ System doesn't have _get_output_schema_for_stage method")
            
    except Exception as e:
        print(f"❌ SystemDispatcher creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Check if there's a timing or attribute access issue
    print(f"\n" + "=" * 60)
    print("Test 3: Check Attribute Access Pattern")
    print("=" * 60)
    
    try:
        # Create system
        system_obj = LangGraphConsensusSystem(config, queue_item_id=9)
        
        # Check default state
        print(f"Initial stage_configs: {getattr(system_obj, 'stage_configs', 'NOT_SET')}")
        
        # Set configuration
        system_obj.configuration = configuration
        system_obj.stage_configs = configuration.get('stages', {})
        
        print(f"After setting stage_configs: {getattr(system_obj, 'stage_configs', 'NOT_SET')}")
        print(f"Stage configs keys: {list(system_obj.stage_configs.keys())}")
        
        # Test the exact access pattern used in _get_output_schema_for_stage
        stage_config = getattr(system_obj, 'stage_configs', {}).get('structure', {})
        print(f"Retrieved structure config: {bool(stage_config)}")
        print(f"Has fields: {'fields' in stage_config}")
        if 'fields' in stage_config:
            print(f"Fields count: {len(stage_config['fields'])}")
            
    except Exception as e:
        print(f"❌ Attribute access test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_queue_item_9())