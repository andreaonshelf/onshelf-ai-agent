#!/usr/bin/env python3
"""Test the results endpoint to ensure it returns data in the expected format"""

import requests
import json
import os
from supabase import create_client

# API base URL
API_BASE = "http://localhost:8000/api"

# Get Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

# First, find a queue item to test with
print("Finding queue items to test...")
result = supabase.table('ai_extraction_queue').select('id, status').limit(10).execute()
if result.data:
    print(f"Found {len(result.data)} queue items")
    for item in result.data:
        print(f"  Item {item['id']}: {item['status']}")
    
    # Test the first item
    item_id = result.data[0]['id']
    print(f"\nTesting results endpoint for item {item_id}...")
    
    # Call the results endpoint
    response = requests.get(f"{API_BASE}/queue/results/{item_id}")
    if response.ok:
        data = response.json()
        print("\nResponse structure:")
        print(f"  ID: {data.get('id')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Store: {data.get('store_name')}")
        print(f"  Category: {data.get('category')}")
        print(f"  Products: {len(data.get('products', []))}")
        print(f"  Total Products: {data.get('total_products')}")
        print(f"  Has planogram SVG: {bool(data.get('planogram_svg'))}")
        print(f"  Has image URL: {bool(data.get('original_image_url'))}")
        
        if data.get('products'):
            print("\nFirst product:")
            product = data['products'][0]
            for key, value in product.items():
                print(f"    {key}: {value}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
    # Also test queue items endpoint
    print("\n\nTesting queue items endpoint...")
    response = requests.get(f"{API_BASE}/queue/items?limit=5")
    if response.ok:
        data = response.json()
        print(f"Found {len(data.get('items', []))} items")
        for item in data.get('items', []):
            extraction_results = item.get('extraction_results', {})
            print(f"  Item {item['id']}: {item['status']} - {extraction_results.get('total_products', 0)} products")
    else:
        print(f"Error: {response.status_code} - {response.text}")
else:
    print("No queue items found")