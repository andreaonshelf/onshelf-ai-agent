#!/usr/bin/env python3
"""
Check the actual extraction data for queue item 9
"""
import os
import json
from datetime import datetime
from supabase import create_client

# Get Supabase credentials
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')

if not url or not key:
    print("Missing Supabase credentials")
    exit(1)

# Initialize client
supabase = create_client(url, key)

# Get queue item 9 with its extraction result
result = supabase.table('ai_extraction_queue').select('*').eq('id', 9).execute()

if result.data:
    item = result.data[0]
    print(f"Queue Item 9 - Status: {item['status']}")
    print(f"Store: {item.get('store_name', 'N/A')}")
    print(f"Category: {item.get('category', 'N/A')}")
    print(f"Started at: {item.get('started_at', 'N/A')}")
    print(f"Completed at: {item.get('completed_at', 'N/A')}")
    print(f"Extraction System: {item.get('current_extraction_system', 'N/A')}")
    print(f"Iterations: {item.get('iterations_completed', 0)}")
    print(f"Final Accuracy: {item.get('final_accuracy', 0)}")
    print(f"API Cost: ${item.get('api_cost', 0)}")
    
    extraction_result = item.get('extraction_result', {})
    if extraction_result:
        print("\n=== EXTRACTION RESULT STRUCTURE ===")
        # Print the keys at the top level
        print(f"Top-level keys: {list(extraction_result.keys())}")
        
        # Check for stages
        if 'stages' in extraction_result:
            print(f"\nStages found: {list(extraction_result['stages'].keys())}")
            
            # Check each stage
            for stage_name, stage_data in extraction_result['stages'].items():
                print(f"\n--- Stage: {stage_name} ---")
                if isinstance(stage_data, dict):
                    print(f"Keys: {list(stage_data.keys())}")
                    if 'data' in stage_data:
                        data = stage_data['data']
                        if isinstance(data, dict):
                            print(f"Data keys: {list(data.keys())}")
                            # Print first few items if it contains products
                            if 'products' in data:
                                products = data['products']
                                print(f"Products found: {len(products)} items")
                                if products and len(products) > 0:
                                    print("\nFirst 3 products:")
                                    for i, product in enumerate(products[:3]):
                                        print(f"\nProduct {i+1}:")
                                        print(json.dumps(product, indent=2))
                        elif isinstance(data, list):
                            print(f"Data is a list with {len(data)} items")
                            if data and len(data) > 0:
                                print("First item:")
                                print(json.dumps(data[0], indent=2))
        
        # Check for direct products
        if 'products' in extraction_result:
            products = extraction_result['products']
            print(f"\nDirect products found: {len(products)} items")
            if products and len(products) > 0:
                print("Sample products:")
                for i, product in enumerate(products[:3]):
                    print(f"\nProduct {i+1}:")
                    print(json.dumps(product, indent=2))
        
        # Check for results
        if 'results' in extraction_result:
            results = extraction_result['results']
            print(f"\nResults found: {type(results)}")
            if isinstance(results, dict):
                print(f"Results keys: {list(results.keys())}")
    
    # Check extraction metadata
    extraction_metadata = item.get('extraction_metadata', {})
    if extraction_metadata:
        print("\n=== EXTRACTION METADATA ===")
        print(f"Metadata keys: {list(extraction_metadata.keys())}")
        
        if 'iterations' in extraction_metadata:
            iterations = extraction_metadata['iterations']
            print(f"\nIterations found: {len(iterations)}")
            for i, iteration in enumerate(iterations):
                print(f"\nIteration {i+1}:")
                print(f"  Model: {iteration.get('model', 'N/A')}")
                print(f"  Accuracy: {iteration.get('accuracy', 0)}")
                print(f"  Products found: {iteration.get('products_found', 0)}")
                print(f"  Stage: {iteration.get('stage', 'N/A')}")
    
    # Also check planogram result
    planogram_result = item.get('planogram_result')
    if planogram_result:
        print("\n=== PLANOGRAM RESULT ===")
        if isinstance(planogram_result, dict):
            print(f"Planogram keys: {list(planogram_result.keys())}")
            if 'svg' in planogram_result:
                print(f"SVG length: {len(planogram_result['svg'])} characters")
else:
    print("Queue item 9 not found")