#!/usr/bin/env python3
"""Test script to verify dashboard backend integration"""

import asyncio
import aiohttp
import json

API_BASE = "http://localhost:8000/api"

async def test_dashboard_integration():
    """Test the dashboard backend integration"""
    
    async with aiohttp.ClientSession() as session:
        print("Testing Dashboard Backend Integration...")
        print("-" * 50)
        
        # Test 1: Save field definitions
        print("\n1. Testing field definitions save...")
        field_def = {
            "name": "products_extraction",
            "stage": "products",
            "fields": [
                {
                    "name": "products",
                    "type": "list",
                    "description": "List of all products found on the shelf",
                    "required": True,
                    "list_item_type": "object",
                    "nested_fields": [
                        {"name": "name", "type": "string", "description": "Product name", "required": True},
                        {"name": "brand", "type": "string", "description": "Brand name", "required": True},
                        {"name": "price", "type": "float", "description": "Price if visible", "required": False}
                    ]
                }
            ],
            "version": "1.0",
            "is_active": True
        }
        
        try:
            async with session.post(f"{API_BASE}/field-definitions", json=field_def) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✓ Field definition saved: ID {result.get('id', 'N/A')}")
                else:
                    print(f"✗ Failed to save field definition: {resp.status}")
        except Exception as e:
            print(f"✗ Error saving field definition: {e}")
        
        # Test 2: Save prompt
        print("\n2. Testing prompt save...")
        prompt_data = {
            "name": "Product Extraction Prompt",
            "stage": "products",
            "content": "Extract all products from the shelf image. For each product, identify the name, brand, and price if visible.",
            "version": "1.0",
            "is_active": True
        }
        
        try:
            async with session.post(f"{API_BASE}/prompts", json=prompt_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✓ Prompt saved: ID {result.get('id', 'N/A')}")
                else:
                    print(f"✗ Failed to save prompt: {resp.status}")
        except Exception as e:
            print(f"✗ Error saving prompt: {e}")
        
        # Test 3: Load active field definitions
        print("\n3. Testing load active field definitions...")
        try:
            async with session.get(f"{API_BASE}/field-definitions/active") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✓ Loaded {len(result)} active field definitions")
                    for def_item in result[:2]:  # Show first 2
                        print(f"  - {def_item.get('name', 'N/A')} (stage: {def_item.get('stage', 'N/A')})")
                else:
                    print(f"✗ Failed to load field definitions: {resp.status}")
        except Exception as e:
            print(f"✗ Error loading field definitions: {e}")
        
        # Test 4: Load active prompts
        print("\n4. Testing load active prompts...")
        try:
            async with session.get(f"{API_BASE}/prompts/active") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✓ Loaded {len(result)} active prompts")
                    for prompt in result[:2]:  # Show first 2
                        print(f"  - {prompt.get('name', 'N/A')} (stage: {prompt.get('stage', 'N/A')})")
                else:
                    print(f"✗ Failed to load prompts: {resp.status}")
        except Exception as e:
            print(f"✗ Error loading prompts: {e}")
        
        # Test 5: Save configuration
        print("\n5. Testing configuration save...")
        config = {
            "system": "custom_consensus",
            "max_budget": 1.50,
            "stages": {
                "structure": {
                    "prompt_id": 1,
                    "prompt_text": "Analyze the shelf structure",
                    "fields": [{"name": "total_shelves", "type": "integer"}],
                    "models": "All 3 models (vote)"
                },
                "products": {
                    "prompt_id": 2,
                    "prompt_text": "Extract all products",
                    "fields": field_def["fields"],
                    "models": "All 3 models (vote)"
                }
            }
        }
        
        try:
            async with session.post(f"{API_BASE}/config/save", json=config) as resp:
                if resp.status == 200:
                    print("✓ Configuration saved successfully")
                else:
                    print(f"✗ Failed to save configuration: {resp.status}")
        except Exception as e:
            print(f"✗ Error saving configuration: {e}")
        
        print("\n" + "-" * 50)
        print("Dashboard Integration Test Complete!")
        print("\nTo use the dashboard:")
        print("1. Open http://localhost:8000/new_dashboard.html")
        print("2. Configure stages and save them individually")
        print("3. Review the configuration preview")
        print("4. Save the full configuration")
        print("5. Use 'Load Previous Config' to restore saved settings")

if __name__ == "__main__":
    asyncio.run(test_dashboard_integration())