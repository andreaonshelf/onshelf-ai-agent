#!/usr/bin/env python3
"""Test the data parsing logic for extraction results"""

import os
import json
from supabase import create_client

# Get Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

print("Testing extraction result parsing...")

# Get a completed item
result = supabase.table('ai_extraction_queue').select('id, status, extraction_result').eq('id', 9).execute()
if result.data:
    item = result.data[0]
    print(f"\nItem {item['id']} - Status: {item['status']}")
    
    extraction_result = item.get("extraction_result")
    if extraction_result and isinstance(extraction_result, dict):
        print(f"Extraction result type: {type(extraction_result)}")
        print(f"Top-level keys: {list(extraction_result.keys())}")
        
        # Check for stages
        if "stages" in extraction_result:
            stages = extraction_result["stages"]
            print(f"\nStages found: {list(stages.keys())}")
            
            # Check each stage
            for stage_name, stage_data in stages.items():
                print(f"\nStage '{stage_name}':")
                if isinstance(stage_data, dict):
                    print(f"  Keys: {list(stage_data.keys())}")
                    if "data" in stage_data:
                        data = stage_data["data"]
                        if isinstance(data, list):
                            print(f"  Data: List with {len(data)} items")
                            if data:
                                print(f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                        else:
                            print(f"  Data type: {type(data)}")
        
        # Check for products at root
        if "products" in extraction_result:
            products = extraction_result["products"]
            print(f"\nProducts at root: {type(products)}")
            if isinstance(products, list):
                print(f"  Count: {len(products)}")
                if products:
                    print(f"  First product: {products[0]}")
    else:
        print("No extraction result found")
else:
    print("Item not found")

# Also check what the parsing logic would extract
print("\n\n=== Testing parsing logic ===")

# Simulate the parsing from the API endpoint
def parse_extraction_result(extraction_result):
    products = []
    
    if extraction_result and isinstance(extraction_result, dict):
        # Check if we have stages with products
        if "stages" in extraction_result:
            stages = extraction_result.get("stages", {})
            # Look for products in different possible locations
            if "products" in stages and isinstance(stages["products"], dict):
                products_data = stages["products"].get("data", [])
                if isinstance(products_data, list):
                    products = products_data
            elif "product_v1" in stages and isinstance(stages["product_v1"], dict):
                products_data = stages["product_v1"].get("data", [])
                if isinstance(products_data, list):
                    products = products_data
        # Also check for products at root level
        elif "products" in extraction_result:
            if isinstance(extraction_result["products"], list):
                products = extraction_result["products"]
    
    return products

# Test with actual data
if result.data and result.data[0].get("extraction_result"):
    parsed_products = parse_extraction_result(result.data[0]["extraction_result"])
    print(f"Parsed {len(parsed_products)} products")
    if parsed_products:
        print(f"First product: {json.dumps(parsed_products[0], indent=2)}")