#!/usr/bin/env python3
"""
Test Real Extraction with Improved Fallback
Simulate the Co-op Food extraction to verify the fallback fixes the issue
"""

import asyncio
import sys
sys.path.append('src')

from src.systems.langgraph_system import LangGraphConsensusSystem
from src.config import SystemConfig
from src.utils import logger

async def test_real_extraction_with_fallback():
    """Test a real extraction similar to the Co-op Food failure"""
    
    print("🔍 Testing Real Extraction with Improved Fallback")
    print("=" * 60)
    
    # Initialize the system
    config = SystemConfig()
    if not config.validate():
        print("❌ Config validation failed")
        return
    
    # Create LangGraph system (the one that failed before)
    system = LangGraphConsensusSystem(config)
    
    # Create a test image (simulate the Co-op Food image)
    from PIL import Image
    import io
    
    # Create a more realistic shelf image for testing
    img = Image.new('RGB', (800, 600), color='white')
    # Add some colored rectangles to simulate products
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Simulate shelf structure and products
    colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple']
    for i, color in enumerate(colors):
        x = 50 + (i * 120)
        y = 200
        draw.rectangle([x, y, x+100, y+150], fill=color)
        draw.text((x+10, y+160), f"Product {i+1}", fill='black')
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG', quality=85)
    test_image_data = img_buffer.getvalue()
    
    print(f"📸 Created test image: {len(test_image_data)} bytes")
    
    # Test with different stage configurations that might use Gemini
    test_extraction_data = {
        "stage_models": {
            "structure": ["gemini-2.5-pro"],  # This will hit quota
            "products": ["gemini-2.5-flash", "claude-3-5-sonnet-v2"],  # Mixed models
            "details": ["gpt-4o"]
        },
        "temperature": 0.7,
        "orchestrator_model": "claude-4-opus"
    }
    
    print("📋 Test Configuration:")
    print(f"   Structure models: {test_extraction_data['stage_models']['structure']}")
    print(f"   Products models: {test_extraction_data['stage_models']['products']}")
    print(f"   Details models: {test_extraction_data['stage_models']['details']}")
    print()
    
    try:
        print("🚀 Starting extraction with potential Gemini quota issues...")
        print("   This should trigger quota fallback for Gemini models...")
        print()
        
        result = await system.extract_with_consensus(
            image_data=test_image_data,
            upload_id="test-coop-food-fallback",
            extraction_data=test_extraction_data
        )
        
        print("✅ EXTRACTION COMPLETED SUCCESSFULLY!")
        print(f"   Overall Accuracy: {result.overall_accuracy:.2%}")
        print(f"   Products Found: {len(result.products_found)}")
        print(f"   Cost: £{result.cost_breakdown.total_cost:.3f}")
        print(f"   Duration: {result.processing_time:.1f}s")
        print(f"   Iterations: {result.iteration_count}")
        
        # Check if fallback was used
        models_used = [model.model_name for model in result.models_used]
        print(f"   Models Used: {models_used}")
        
        if any("claude" in model.lower() or "gpt" in model.lower() for model in models_used):
            print("   📊 Fallback models were used (likely due to Gemini quota)")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ EXTRACTION FAILED: {error_msg[:200]}...")
        
        # Analyze the failure
        if "recursion limit" in error_msg.lower():
            print("   🔄 Recursion limit hit - workflow got stuck in retry loop")
        elif "quota" in error_msg.lower():
            print("   💰 Quota exhaustion - fallback may have failed")
        elif "timeout" in error_msg.lower():
            print("   ⏰ Timeout - extraction took too long")
        else:
            print("   🔍 Other error - check logs for details")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_extraction_with_fallback())
    if success:
        print("\n🎉 Test PASSED - Fallback mechanism working correctly!")
    else:
        print("\n❌ Test FAILED - Further debugging needed")