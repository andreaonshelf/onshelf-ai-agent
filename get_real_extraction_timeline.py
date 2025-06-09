#!/usr/bin/env python3
"""
Get the real extraction timeline for queue item 9
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
    
    print("=== EXTRACTION TIMELINE FOR QUEUE ITEM 9 ===")
    print(f"Store: Co-op Food - Greenwich - Trafalgar Road")
    print(f"Image: {item.get('media_url', 'N/A')}")
    print()
    
    # Timeline events
    events = []
    
    # 1. User uploaded and pressed extract
    created_at = item.get('created_at')
    if created_at:
        events.append({
            'time': created_at,
            'event': 'User uploaded image and pressed Extract button',
            'details': f"Queue item created with status: {item.get('status_on_create', 'pending')}"
        })
    
    # 2. Extraction started
    started_at = item.get('started_at')
    if started_at:
        events.append({
            'time': started_at,
            'event': 'Extraction processing started',
            'details': f"System: {item.get('current_extraction_system', 'unknown')}"
        })
    
    # 3. Extraction metadata events
    metadata = item.get('extraction_metadata', {})
    if metadata:
        # Field definitions loaded
        if 'field_definitions' in metadata:
            events.append({
                'time': started_at,
                'event': 'Field definitions loaded',
                'details': f"Fields: {', '.join(metadata['field_definitions']) if isinstance(metadata['field_definitions'], list) else 'Unknown'}"
            })
        
        # Iterations
        if 'iterations' in metadata:
            for i, iteration in enumerate(metadata['iterations']):
                iter_time = iteration.get('timestamp', started_at)
                events.append({
                    'time': iter_time,
                    'event': f'Iteration {i+1} - {iteration.get("stage", "extraction")}',
                    'details': f"Model: {iteration.get('model', 'unknown')}, Accuracy: {iteration.get('accuracy', 0)*100:.1f}%"
                })
    
    # 4. Test data was inserted (this happened later)
    if 'test_data_inserted' in str(item.get('extraction_result', {})):
        events.append({
            'time': '2025-06-09T00:00:00+00:00',  # Approximate
            'event': 'TEST DATA INSERTED (replaced real extraction)',
            'details': 'add_test_extraction_data.py script overwrote the original extraction'
        })
    
    # 5. Extraction completed
    completed_at = item.get('completed_at')
    if completed_at:
        events.append({
            'time': completed_at,
            'event': 'Extraction completed',
            'details': f"Final accuracy: {item.get('final_accuracy', 0)*100:.1f}%, Cost: ${item.get('api_cost', 0):.3f}"
        })
    
    # Sort events by time
    events.sort(key=lambda x: x['time'])
    
    # Print timeline
    for event in events:
        time_str = datetime.fromisoformat(event['time'].replace('+00:00', '')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{time_str}] {event['event']}")
        if event['details']:
            print(f"  └─ {event['details']}")
    
    print("\n=== ACTUAL EXTRACTION DATA (CURRENT) ===")
    result = item.get('extraction_result', {})
    if result and 'stages' in result:
        if 'product_v1' in result['stages']:
            products = result['stages']['product_v1']['data']
            print(f"\nProducts extracted: {len(products)}")
            for i, product in enumerate(products):
                print(f"\n{i+1}. {product['brand']} {product['name']} {product['size']}")
                print(f"   Price: ${product['price']}, Shelf: {product['shelf']}, Position: {product['position']}")
    
    print("\n=== ISSUE IDENTIFIED ===")
    print("The real extraction data from June 8th was overwritten by test data.")
    print("The test data contains fake products (Coca Cola, Pepsi, etc.) instead of the actual Co-op products.")
    print("\nTo see real extraction results, the image needs to be re-processed.")
    
else:
    print("Queue item 9 not found")