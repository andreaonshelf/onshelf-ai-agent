#!/usr/bin/env python3
"""
Trace the response_model error in extraction engine
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import SystemConfig
from src.extraction.engine import ModularExtractionEngine
from src.extraction.dynamic_model_builder import DynamicModelBuilder

async def test_extraction():
    print("🔍 TESTING EXTRACTION ENGINE")
    print("=" * 60)
    
    # Initialize config
    config = SystemConfig()
    
    # Initialize extraction engine
    engine = ModularExtractionEngine(config)
    
    # Test with different output schemas
    test_cases = [
        ("Dynamic model", None),  # Will be built
        ("String schema", "Dict[str, Any]"),
        ("ShelfStructure", "ShelfStructure"),
    ]
    
    # Sample image data
    image_data = b"fake_image_data"
    images = {"test": image_data}
    
    # Test prompt
    prompt = "Extract shelf structure from this image."
    
    for name, output_schema in test_cases:
        print(f"\n📋 Testing: {name}")
        print(f"   Output schema: {output_schema}")
        
        try:
            # If dynamic model test, build one
            if name == "Dynamic model":
                stage_config = {
                    "fields": [
                        {"name": "shelf_count", "type": "integer", "description": "Number of shelves"},
                        {"name": "confidence", "type": "float", "description": "Confidence score"}
                    ]
                }
                output_schema = DynamicModelBuilder.build_model_from_config("test", stage_config)
                print(f"   Built dynamic model: {output_schema.__name__}")
            
            # Try to execute
            result, cost = await engine.execute_with_model_id(
                model_id="gpt-4o",
                prompt=prompt,
                images=images,
                output_schema=output_schema,
                agent_id="test_agent"
            )
            
            print(f"   ✅ Success! Result type: {type(result)}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   Error type: {type(e).__name__}")
            
            # Check if it's the response_model error
            if "response_model" in str(e):
                print("   ⚠️  This is the response_model error!")
                
                # Try to trace where it comes from
                import traceback
                print("\n   Traceback:")
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_extraction())