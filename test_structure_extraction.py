#!/usr/bin/env python3
"""
Test structure extraction specifically to reproduce the error
"""

import asyncio
import os
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import SystemConfig
from src.systems.custom_consensus_visual import CustomConsensusVisualSystem

async def test_structure_extraction():
    print("🔍 TESTING STRUCTURE EXTRACTION")
    print("=" * 60)
    
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    image_data = img_bytes.getvalue()
    
    # Initialize system
    config = SystemConfig()
    system = CustomConsensusVisualSystem(config)
    
    # Set up empty stage configs to trigger fallback to generic schemas
    system.stage_configs = {
        'structure': {},  # No fields, should trigger fallback
        'products': {},
        'details': {}
    }
    
    # Set up minimal prompts to avoid the prompt check
    system.stage_prompts = {
        'structure': "Analyze the shelf structure in this image.",
        'products': "Extract products from this image.",
        'details': "Extract detailed product information."
    }
    
    print("📋 Testing structure extraction with fallback schema")
    
    try:
        # Call the specific method that processes structure stage
        result = await system._extract_with_model(
            model="gpt-4o",
            prompt="Analyze the shelf structure in this image.",
            image_data=image_data,
            stage="structure",
            previous_stages={}
        )
        
        print(f"✅ Structure extraction succeeded!")
        print(f"   Result type: {type(result)}")
        print(f"   Result: {result}")
        
    except Exception as e:
        print(f"❌ Structure extraction failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        if "response_model" in str(e):
            print("   ⚠️  This is the response_model error we're looking for!")
            
            # Print traceback for debugging
            import traceback
            print("\n   Traceback:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_structure_extraction())