#!/usr/bin/env python3
"""
Test manual processing of queue item with extraction configuration
This simulates what the queue processor would do but in manual mode
"""

import asyncio
import json
from src.config import SystemConfig
from src.orchestrator.system_dispatcher import SystemDispatcher

async def test_manual_processing():
    """Test processing queue item 8 with COMPLETE configuration including details stage"""
    
    # Complete configuration with all three stages
    extraction_config = {
        "system": "custom_consensus",
        "temperature": 0.1,
        "orchestrator_model": "claude-4-opus",
        "max_budget": 2.0,
        "stages": {
            "structure": {
                "prompt_text": "Analyze the shelf structure. Count horizontal shelves from bottom to top.",
                "fields": [
                    {"name": "shelf_count", "type": "integer", "description": "Number of horizontal shelves", "required": True}
                ]
            },
            "products": {
                "prompt_text": "Extract products with their exact shelf positions.",
                "fields": [
                    {"name": "products", "type": "list", "description": "All products found", "required": True,
                     "nested_fields": [
                         {"name": "brand", "type": "string", "description": "Product brand", "required": True},
                         {"name": "name", "type": "string", "description": "Product name", "required": True},
                         {"name": "shelf_number", "type": "integer", "description": "Shelf number (1=bottom)", "required": True}
                     ]}
                ]
            },
            "details": {
                "prompt_text": "Extract detailed product information including prices, sizes, and promotional elements.",
                "fields": [
                    {"name": "product_details", "type": "list", "description": "Detailed information for each product", "required": True,
                     "nested_fields": [
                         {"name": "product_name", "type": "string", "description": "Product name for reference", "required": True},
                         {"name": "price", "type": "float", "description": "Price if visible", "required": False},
                         {"name": "size_variant", "type": "string", "description": "Product size", "required": False},
                         {"name": "promotional_tags", "type": "list", "description": "Promotional labels", "required": False, "list_item_type": "string"}
                     ]}
                ]
            }
        },
        "stage_models": {
            "structure": ["gpt-4o"],
            "products": ["gpt-4o", "claude-3-sonnet"],
            "details": ["gpt-4o", "claude-3-sonnet"]
        }
    }
    
    upload_id = "upload-1748286333101-c55tow"  # Sainsbury's item
    
    print("🚀 Starting manual processing with full configuration...")
    print(f"📊 Configuration: {extraction_config['system']} system")
    print(f"🔧 Stages configured: {list(extraction_config['stages'].keys())}")
    print(f"🤖 Models: {extraction_config['stage_models']}")
    print()
    
    # Create system config and dispatcher
    config = SystemConfig()
    dispatcher = SystemDispatcher(config, queue_item_id=8)
    
    try:
        # Process with our configuration
        result = await dispatcher.achieve_target_accuracy(
            upload_id=upload_id,
            target_accuracy=0.95,
            max_iterations=5,
            queue_item_id=8,
            system=extraction_config["system"],
            configuration=extraction_config
        )
        
        print("✅ Processing completed successfully!")
        print(f"📈 Final accuracy: {result.final_accuracy:.2%}")
        print(f"🔄 Iterations: {result.iterations_completed}")
        print(f"💰 Cost: ${result.total_cost:.3f}")
        print(f"⏱️ Duration: {result.total_duration:.1f}s")
        
        if hasattr(result, 'structure_analysis') and result.structure_analysis:
            print(f"🏗️ Structure: {result.structure_analysis.shelf_count} shelves")
        
        print("\n🎯 SUCCESS: Extraction ran using user-defined configuration!")
        
        return result
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_manual_processing())