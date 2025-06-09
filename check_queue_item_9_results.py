#!/usr/bin/env python3
"""Check the actual extraction results for queue item 9"""

import os
import json
from supabase import create_client, Client
from datetime import datetime

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_key)

def check_queue_item_results():
    """Check extraction results for queue item 9"""
    
    print("=== Checking Queue Item 9 Results ===\n")
    
    # Get queue item 9
    result = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()
    
    if not result.data:
        print("Queue item 9 not found!")
        return
    
    item = result.data[0]
    print(f"Queue Item 9 Status: {item['status']}")
    print(f"Upload ID: {item.get('upload_id')}")
    print(f"Ready Media ID: {item.get('ready_media_id')}")
    print(f"Processing Duration: {item.get('processing_duration_seconds')} seconds")
    print(f"API Cost: ${item.get('api_cost', 0):.4f}")
    print(f"Final Accuracy: {item.get('final_accuracy')}")
    print(f"Iterations Completed: {item.get('iterations_completed')}")
    print(f"Selected Systems: {item.get('selected_systems')}")
    print(f"Current System: {item.get('current_extraction_system')}")
    
    # Check extraction results
    extraction_result = item.get('extraction_result')
    if extraction_result:
        print("\n=== Extraction Result Structure ===")
        print(f"Type: {type(extraction_result)}")
        
        if isinstance(extraction_result, dict):
            print(f"Keys: {list(extraction_result.keys())}")
            
            # Check for stages
            if 'stages' in extraction_result:
                stages = extraction_result['stages']
                print(f"\nStages found: {list(stages.keys())}")
                
                # Check each stage
                for stage_name, stage_data in stages.items():
                    print(f"\n--- Stage: {stage_name} ---")
                    if isinstance(stage_data, dict):
                        print(f"Stage keys: {list(stage_data.keys())}")
                        
                        # Check for data
                        if 'data' in stage_data:
                            data = stage_data['data']
                            if isinstance(data, list):
                                print(f"Data items count: {len(data)}")
                                if data:
                                    print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'not a dict'}")
                                    # Show sample product
                                    if stage_name in ['products', 'product_v1']:
                                        print(f"\nSample product:")
                                        print(json.dumps(data[0], indent=2))
                            else:
                                print(f"Data type: {type(data)}")
                        
                        # Check for fields
                        if 'fields' in stage_data:
                            fields = stage_data['fields']
                            print(f"Fields count: {len(fields) if isinstance(fields, list) else 'not a list'}")
            
            # Check for products at root
            if 'products' in extraction_result:
                products = extraction_result['products']
                print(f"\nProducts at root level: {type(products)}")
                if isinstance(products, list):
                    print(f"Product count: {len(products)}")
            
            # Check for iterations
            if 'iterations' in extraction_result:
                iterations = extraction_result['iterations']
                print(f"\nIterations: {len(iterations) if isinstance(iterations, list) else type(iterations)}")
        
        # Save full extraction result to file for inspection
        with open('queue_item_9_extraction_result.json', 'w') as f:
            json.dump(extraction_result, f, indent=2)
        print("\nFull extraction result saved to queue_item_9_extraction_result.json")
    else:
        print("\nNo extraction result found!")
    
    # Check planogram result
    planogram_result = item.get('planogram_result')
    if planogram_result:
        print("\n=== Planogram Result ===")
        print(f"Type: {type(planogram_result)}")
        if isinstance(planogram_result, dict):
            print(f"Keys: {list(planogram_result.keys())}")
            if 'svg' in planogram_result:
                print(f"SVG length: {len(planogram_result['svg'])} characters")
            if 'planogram_svg' in planogram_result:
                print(f"Planogram SVG length: {len(planogram_result['planogram_svg'])} characters")
    else:
        print("\nNo planogram result found!")
    
    # Check model config
    model_config = item.get('model_config')
    if model_config:
        print("\n=== Model Config ===")
        print(json.dumps(model_config, indent=2))
    
    # Check extraction config
    extraction_config = item.get('extraction_config')
    if extraction_config:
        print("\n=== Extraction Config ===")
        if isinstance(extraction_config, dict) and 'stages' in extraction_config:
            for stage_name, stage_config in extraction_config['stages'].items():
                print(f"\nStage: {stage_name}")
                if 'fields' in stage_config:
                    print(f"  Fields configured: {len(stage_config['fields'])}")
                if 'prompt_text' in stage_config:
                    print(f"  Has prompt: {len(stage_config['prompt_text'])} characters")

if __name__ == "__main__":
    check_queue_item_results()