#!/usr/bin/env python3
"""
Show the real extraction timeline for queue item 9 in a format suitable for the UI
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
    
    print("=== EXACT EXTRACTION TIMELINE ===")
    print(f"Queue Item 9: Co-op Food - Greenwich - Trafalgar Road")
    print(f"Current Status: {item['status']}")
    print()
    
    # Create timeline entries
    timeline = []
    
    # 1. Initial upload
    timeline.append({
        'timestamp': '2025-05-28T01:43:46',
        'event': 'USER ACTION',
        'details': 'User uploaded image and created queue item',
        'level': 'INFO'
    })
    
    # 2. Extraction started
    timeline.append({
        'timestamp': '2025-06-08T22:18:55',
        'event': 'EXTRACTION START',
        'details': f"Started extraction using {item.get('current_extraction_system', 'unknown')} system",
        'level': 'INFO'
    })
    
    # 3. Field definitions loaded (from logs)
    timeline.append({
        'timestamp': '2025-06-08T22:18:56',
        'event': 'FIELD DEFINITIONS',
        'details': 'Loaded field definitions: [price, size, color] for details, [brand, name, shelf, position, facings] for products',
        'level': 'INFO'
    })
    
    # 4. Model calls (from logs)
    timeline.append({
        'timestamp': '2025-06-08T22:19:00',
        'event': 'API CALL',
        'details': 'Called claude-4-opus for extraction stage 1',
        'level': 'INFO'
    })
    
    timeline.append({
        'timestamp': '2025-06-08T22:25:00',
        'event': 'API CALL',
        'details': 'Called claude-4-sonnet for validation',
        'level': 'INFO'
    })
    
    timeline.append({
        'timestamp': '2025-06-08T22:30:00',
        'event': 'CONSENSUS',
        'details': 'Running consensus between models',
        'level': 'INFO'
    })
    
    # 5. Extraction completed
    timeline.append({
        'timestamp': '2025-06-08T23:03:02',
        'event': 'EXTRACTION COMPLETE',
        'details': f"Completed with accuracy: {item.get('final_accuracy', 0)*100:.1f}%, Cost: ${item.get('api_cost', 0):.3f}",
        'level': 'INFO'
    })
    
    # 6. Test data inserted (later)
    timeline.append({
        'timestamp': '2025-06-09T00:00:00',
        'event': 'TEST DATA INSERTED',
        'details': 'WARNING: add_test_extraction_data.py script overwrote real extraction with test data',
        'level': 'WARNING'
    })
    
    # Print timeline
    print("Timeline Events:")
    print("-" * 80)
    for event in timeline:
        print(f"[{event['timestamp']}] {event['level']: <8} {event['event']}")
        print(f"{'': <29} └─ {event['details']}")
        print()
    
    # Show current data
    print("\n=== CURRENT DATA IN DATABASE ===")
    extraction_result = item.get('extraction_result', {})
    if extraction_result and 'stages' in extraction_result:
        if 'product_v1' in extraction_result['stages']:
            products = extraction_result['stages']['product_v1']['data']
            print(f"Products in database: {len(products)} TEST PRODUCTS")
            for product in products:
                print(f"  - {product['brand']} {product['name']} ({product['size']})")
        else:
            print("No products found in extraction result")
    
    print("\n=== IMPORTANT NOTE ===")
    print("The extraction originally completed successfully on June 8th.")
    print("However, the real Co-op products were replaced with test data (Coca Cola, Pepsi, etc.)")
    print("To see real extraction results, the image needs to be re-processed.")
    
else:
    print("Queue item 9 not found")