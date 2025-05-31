#!/usr/bin/env python3
"""
Test script for comparison configuration implementation
"""

import asyncio
from src.comparison.image_comparison_agent import ImageComparisonAgent
from src.config import SystemConfig
from src.planogram.models import VisualPlanogram
from src.models.shelf_structure import ShelfStructure

async def test_comparison_config():
    """Test the comparison configuration implementation"""
    
    # Initialize config
    config = SystemConfig()
    
    # Create comparison agent
    agent = ImageComparisonAgent(config)
    
    # Create mock data
    planogram = VisualPlanogram(
        total_products=10,
        svg_data="<svg>Mock planogram SVG</svg>"
    )
    
    structure = ShelfStructure(
        shelf_count=3,
        products_per_shelf_estimate=5,
        estimated_width_meters=2.0
    )
    
    # Mock image data
    mock_image = b"fake_image_data"
    
    print("Testing comparison configuration...")
    
    # Test 1: Default comparison (text-based)
    print("\n1. Testing default text-based comparison...")
    try:
        result = await agent.compare_image_vs_planogram(
            original_image=mock_image,
            planogram=planogram,
            structure_context=structure
        )
        print("✓ Default comparison works")
    except Exception as e:
        print(f"✗ Default comparison failed: {e}")
    
    # Test 2: Custom model selection
    print("\n2. Testing custom model selection...")
    try:
        result = await agent.compare_image_vs_planogram(
            original_image=mock_image,
            planogram=planogram,
            structure_context=structure,
            model_id="claude-3-opus"
        )
        print("✓ Custom model selection works (with fallback)")
    except Exception as e:
        print(f"✗ Custom model selection failed: {e}")
    
    # Test 3: Custom prompt
    print("\n3. Testing custom prompt...")
    custom_prompt = """
    Compare the shelf image to this planogram:
    {planogram_description}
    
    Structure: {shelf_count} shelves, ~{products_per_shelf_estimate} products per shelf.
    
    Return JSON with matches, mismatches, missing_products, extra_products.
    """
    try:
        result = await agent.compare_image_vs_planogram(
            original_image=mock_image,
            planogram=planogram,
            structure_context=structure,
            custom_prompt=custom_prompt
        )
        print("✓ Custom prompt works")
    except Exception as e:
        print(f"✗ Custom prompt failed: {e}")
    
    # Test 4: Visual comparison mode
    print("\n4. Testing visual comparison mode...")
    try:
        result = await agent.compare_image_vs_planogram(
            original_image=mock_image,
            planogram=planogram,
            structure_context=structure,
            use_visual_comparison=True
        )
        print("✓ Visual comparison mode works (or falls back gracefully)")
    except Exception as e:
        print(f"✗ Visual comparison mode failed: {e}")
    
    # Test 5: Full configuration
    print("\n5. Testing full configuration...")
    try:
        result = await agent.compare_image_vs_planogram(
            original_image=mock_image,
            planogram=planogram,
            structure_context=structure,
            model_id="gpt-4-vision-preview",
            custom_prompt=custom_prompt,
            use_visual_comparison=True,
            abstraction_layers=[
                {"id": "confidence", "label": "Confidence Levels", "enabled": True},
                {"id": "brand", "label": "Brand Grouping", "enabled": True}
            ]
        )
        print("✓ Full configuration works")
    except Exception as e:
        print(f"✗ Full configuration failed: {e}")
    
    print("\n✅ Comparison configuration testing complete!")

if __name__ == "__main__":
    asyncio.run(test_comparison_config())