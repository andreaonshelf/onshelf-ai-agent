#!/usr/bin/env python3
"""
Test Improved Multi-Level Quota Fallback
Verify the new fallback chain works correctly
"""

import asyncio
import sys
sys.path.append('src')

from src.extraction.engine import ModularExtractionEngine
from src.config import SystemConfig
from src.utils import logger

async def test_improved_fallback():
    """Test the improved multi-level quota fallback mechanism"""
    
    print("🔍 Testing Improved Multi-Level Quota Fallback")
    print("=" * 60)
    
    # Initialize the extraction engine
    config = SystemConfig()
    if not config.validate():
        print("❌ Config validation failed")
        return
    
    engine = ModularExtractionEngine(config, temperature=0.7)
    
    # Test the fallback chain mappings
    print("\n1. Testing Fallback Chain Mappings:")
    test_models = ["gemini-2.5-pro", "gemini-2.5-flash", "claude-4-opus", "gpt-4o"]
    
    for model_id in test_models:
        provider, api_model = engine._get_api_model_name(model_id)
        fallback_chain = engine._get_quota_fallback_chain(model_id, provider)
        print(f"   {model_id} -> {provider}:{api_model}")
        print(f"     Fallback chain: {fallback_chain}")
        print()
    
    print("2. Testing Real Quota Fallback (will likely trigger):")
    print("   Attempting gemini-2.5-pro -> should fallback through chain...")
    
    # Create minimal valid image data for testing
    from PIL import Image
    import io
    
    # Create a small test image
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='JPEG')
    test_image = img_buffer.getvalue()
    
    try:
        result, cost = await engine.execute_with_model_id(
            model_id="gemini-2.5-pro",
            prompt="Describe this image briefly",
            images={"test": test_image},
            output_schema="Dict[str, Any]",
            agent_id="test_fallback_agent"
        )
        print(f"   ✅ Success with result: {str(result)[:100]}...")
        print(f"   💰 Cost: £{cost}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Final error: {error_msg[:150]}...")
        
        # Check if it went through the fallback process
        if "exhausted" in error_msg or "fallback" in error_msg.lower():
            print(f"   📊 Attempted fallback process - check logs above for details")
        else:
            print(f"   📊 Failed before fallback could be attempted")

if __name__ == "__main__":
    asyncio.run(test_improved_fallback())