#!/usr/bin/env python3
"""Test the queue API results endpoint"""

import requests
import json

# Test getting queue items
response = requests.get("http://localhost:8000/api/queue/items")
if response.status_code == 200:
    data = response.json()
    print(f"Total items: {data['total']}")
    
    # Find item 9
    item_9 = None
    for item in data['items']:
        if item['id'] == 9:
            item_9 = item
            break
    
    if item_9:
        print(f"\nQueue Item 9:")
        print(f"Status: {item_9['status']}")
        print(f"Store: {item_9.get('store_name', 'Unknown')}")
        print(f"Category: {item_9.get('category', 'Unknown')}")
        
        # Check extraction results summary
        if 'extraction_results' in item_9:
            print(f"Total Products (from summary): {item_9['extraction_results'].get('total_products', 0)}")
        else:
            print("No extraction_results summary found")
        
        # Check if extraction_result is included
        if 'extraction_result' in item_9:
            print("extraction_result field is included in response")
            er = item_9['extraction_result']
            if er and isinstance(er, dict):
                print(f"extraction_result keys: {list(er.keys())}")
        else:
            print("extraction_result field NOT included in list response")
    else:
        print("Queue item 9 not found in list")
else:
    print(f"Failed to get queue items: {response.status_code}")
    print(response.text)

print("\n" + "="*50 + "\n")

# Test getting specific results for item 9
print("Testing /api/queue/results/9 endpoint:")
response = requests.get("http://localhost:8000/api/queue/results/9")
if response.status_code == 200:
    data = response.json()
    print(f"Item ID: {data['id']}")
    print(f"Status: {data['status']}")
    print(f"Store: {data.get('store_name', 'Unknown')}")
    print(f"Category: {data.get('category', 'Unknown')}")
    print(f"Total Products: {data.get('total_products', 0)}")
    print(f"Final Accuracy: {data.get('final_accuracy')}")
    print(f"API Cost: ${data.get('api_cost', 0):.4f}")
    
    # Check products
    if 'products' in data and data['products']:
        print(f"\nProducts found: {len(data['products'])}")
        for i, product in enumerate(data['products'][:3]):  # Show first 3
            print(f"\nProduct {i+1}:")
            print(f"  Name: {product.get('name')}")
            print(f"  Brand: {product.get('brand')}")
            print(f"  Price: ${product.get('price', 0):.2f}")
            print(f"  Shelf: {product.get('shelf')}")
            print(f"  Category: {product.get('category')}")
    else:
        print("\nNo products found in response")
    
    # Check planogram
    if 'planogram_svg' in data and data['planogram_svg']:
        print(f"\nPlanogram SVG: {len(data['planogram_svg'])} characters")
    else:
        print("\nNo planogram SVG found")
    
    # Check iterations
    if 'iterations_data' in data and data['iterations_data']:
        print(f"\nIterations: {len(data['iterations_data'])}")
        for iteration in data['iterations_data']:
            print(f"  Iteration {iteration.get('iteration', '?')}: "
                  f"Cost=${iteration.get('cost', 0):.4f}, "
                  f"Accuracy={iteration.get('accuracy', 0):.2f}, "
                  f"Products={iteration.get('products_found', 0)}")
else:
    print(f"Failed to get results: {response.status_code}")
    print(response.text)