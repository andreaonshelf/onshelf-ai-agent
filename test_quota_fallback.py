#!/usr/bin/env python3
"""
Test Quota Fallback Functionality
Diagnose why the quota fallback isn't working for the Co-op extraction
"""

import asyncio
import sys
sys.path.append('src')

from src.extraction.engine import ModularExtractionEngine
from src.config import SystemConfig
from src.utils import logger

async def test_quota_fallback():
    """Test the quota-aware fallback mechanism"""
    
    print("🔍 Testing Quota Fallback Mechanism")
    print("=" * 50)
    
    # Initialize the extraction engine
    config = SystemConfig()
    if not config.validate():
        print("❌ Config validation failed")
        return
    
    engine = ModularExtractionEngine(config, temperature=0.7)
    
    # Test the mapping functions
    print("\n1. Testing Model ID Mappings:")
    test_models = ["gemini-2.5-pro", "gemini-2.5-flash", "claude-4-opus", "gpt-4o"]
    
    for model_id in test_models:
        provider, api_model = engine._get_api_model_name(model_id)
        fallback = engine._get_quota_fallback(model_id, provider)
        print(f"   {model_id} -> {provider}:{api_model} (fallback: {fallback})")
    
    # Test the quota error detection
    print("\n2. Testing Quota Error Detection:")
    test_errors = [
        "429 You exceeded your current quota",
        "resource_exhausted",
        "quota exceeded", 
        "usage limit reached",
        "Some other API error"
    ]
    
    for error_msg in test_errors:
        is_quota_error = any(phrase in error_msg.lower() for phrase in [
            "429", "quota", "rate limit", "exceeded", "insufficient_quota",
            "billing", "usage limit", "resource_exhausted"
        ])
        print(f"   '{error_msg[:30]}...' -> Quota Error: {is_quota_error}")
    
    # Test actual model execution with a simple prompt (should fail gracefully)
    print("\n3. Testing Model Execution:")
    print("   Attempting gemini-2.5-pro (likely to hit quota)...")
    
    try:
        # Create a minimal test image
        test_image = b"fake_image_data"  # This will fail, but we can see the error handling
        
        result, cost = await engine.execute_with_model_id(
            model_id="gemini-2.5-pro",
            prompt="Test prompt",
            images={"test": test_image},
            output_schema="Dict[str, Any]",
            agent_id="test_agent"
        )
        print(f"   ✅ Success: {result}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Expected error: {error_msg[:100]}...")
        
        # Check if quota detection would work
        is_quota_error = any(phrase in error_msg.lower() for phrase in [
            "429", "quota", "rate limit", "exceeded", "insufficient_quota",
            "billing", "usage limit", "resource_exhausted"
        ])
        print(f"   📊 Would trigger quota fallback: {is_quota_error}")

if __name__ == "__main__":
    asyncio.run(test_quota_fallback())