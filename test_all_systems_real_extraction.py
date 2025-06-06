#!/usr/bin/env python3
"""
Test script to verify all three extraction systems use real extraction
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemConfig
from src.systems.base_system import ExtractionSystemFactory
from src.utils import logger

async def test_system(system_type: str, image_path: str):
    """Test a single extraction system"""
    print(f"\n{'='*60}")
    print(f"Testing {system_type.upper()} System")
    print(f"{'='*60}")
    
    # Create config
    config = SystemConfig()
    
    # Create system
    system = ExtractionSystemFactory.get_system(system_type, config)
    
    # Set up test configuration
    system.stage_prompts = {
        'structure': 'Analyze this retail shelf image and identify the number of horizontal shelf levels.',
        'products': 'Extract all visible products with their positions, brands, and names.',
        'details': 'Extract prices, sizes, and other details for the products.'
    }
    
    system.stage_models = {
        'structure': ['gpt-4o'],
        'products': ['gpt-4o'],
        'details': ['gpt-4o']
    }
    
    # Read image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    print(f"Image loaded: {len(image_data)} bytes")
    
    # Run extraction
    try:
        print(f"\nStarting extraction...")
        start_time = asyncio.get_event_loop().time()
        
        result = await system.extract_with_consensus(
            image_data=image_data,
            upload_id=f"test_{system_type}_001"
        )
        
        end_time = asyncio.get_event_loop().time()
        processing_time = end_time - start_time
        
        print(f"\nExtraction completed in {processing_time:.1f} seconds")
        
        # Check results
        print(f"\nResults:")
        print(f"- System: {result.system_type}")
        print(f"- Accuracy: {result.overall_accuracy:.2%}")
        print(f"- Products found: {len(result.positions)}")
        print(f"- Total cost: ${result.cost_breakdown.total_cost:.4f}")
        
        # Show sample products (first 3)
        if result.positions:
            print(f"\nSample products extracted:")
            for i, (key, product) in enumerate(list(result.positions.items())[:3], 1):
                if isinstance(product, dict):
                    brand = product.get('brand', 'Unknown')
                    name = product.get('name', product.get('product', 'Unknown'))
                    print(f"  {i}. {brand} - {name}")
        
        # Check if it's real extraction (not mock)
        is_real = False
        if processing_time > 5:  # Real extraction takes time
            is_real = True
        if result.cost_breakdown.total_cost > 0:  # Real extraction has costs
            is_real = True
        if any('mock' in str(p).lower() or 'test' in str(p).lower() 
               for p in result.positions.values()):
            is_real = False
        
        print(f"\n✅ USING REAL EXTRACTION: {is_real}")
        
        return {
            'system': system_type,
            'success': True,
            'is_real_extraction': is_real,
            'processing_time': processing_time,
            'cost': result.cost_breakdown.total_cost,
            'products_found': len(result.positions),
            'accuracy': result.overall_accuracy
        }
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.error(f"Test failed for {system_type}: {e}")
        return {
            'system': system_type,
            'success': False,
            'error': str(e)
        }

async def main():
    """Test all three systems"""
    # Find a test image
    test_images = [
        "/tmp/test_shelf.jpg",
        "test_image.jpg",
        "sample_shelf.jpg"
    ]
    
    image_path = None
    for path in test_images:
        if os.path.exists(path):
            image_path = path
            break
    
    if not image_path:
        print("❌ No test image found. Please provide a shelf image at one of these paths:")
        for path in test_images:
            print(f"  - {path}")
        return
    
    print(f"Using test image: {image_path}")
    
    # Test all systems
    systems = ['custom', 'langgraph', 'hybrid']
    results = []
    
    for system_type in systems:
        result = await test_system(system_type, image_path)
        results.append(result)
        await asyncio.sleep(2)  # Brief pause between systems
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        if result['success']:
            status = "✅ REAL" if result['is_real_extraction'] else "❌ MOCK"
            print(f"\n{result['system'].upper()}: {status}")
            print(f"  - Time: {result['processing_time']:.1f}s")
            print(f"  - Cost: ${result['cost']:.4f}")
            print(f"  - Products: {result['products_found']}")
            print(f"  - Accuracy: {result['accuracy']:.2%}")
        else:
            print(f"\n{result['system'].upper()}: ❌ FAILED")
            print(f"  - Error: {result.get('error', 'Unknown')}")
    
    # Final verdict
    all_real = all(r.get('is_real_extraction', False) for r in results if r['success'])
    print(f"\n{'='*60}")
    if all_real:
        print("✅ ALL SYSTEMS USING REAL EXTRACTION!")
    else:
        print("❌ Some systems still using mock data")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())