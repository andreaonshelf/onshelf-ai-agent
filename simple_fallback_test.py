#!/usr/bin/env python3
"""
Simple Fallback Test
Quick test to verify the core fallback mechanism works
"""

import asyncio
import sys
sys.path.append('src')

from src.extraction.engine import ModularExtractionEngine
from src.config import SystemConfig
from PIL import Image
import io

async def simple_fallback_test():
    """Quick test of fallback mechanism with real image"""
    
    print("🧪 Simple Fallback Test")
    print("=" * 30)
    
    config = SystemConfig()
    engine = ModularExtractionEngine(config, temperature=0.7)
    
    # Create small test image
    img = Image.new('RGB', (200, 150), color='lightblue')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    test_image = buffer.getvalue()
    
    print("Testing gemini-2.5-pro (should fallback to Claude)...")
    
    try:
        result, cost = await engine.execute_with_model_id(
            model_id="gemini-2.5-pro",
            prompt="What do you see in this image?",
            images={"test": test_image},
            output_schema="Dict[str, Any]",
            agent_id="simple_test"
        )
        
        print(f"✅ Success: {str(result)[:50]}...")
        print(f"💰 Cost: £{cost}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}...")
        return False

if __name__ == "__main__":
    success = asyncio.run(simple_fallback_test())
    print(f"\nResult: {'PASS' if success else 'FAIL'}")