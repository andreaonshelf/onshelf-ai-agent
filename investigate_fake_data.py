import os
from supabase import create_client
import json

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Check the "completed" items
    result = supabase.table("ai_extraction_queue").select("*").eq("status", "completed").execute()
    
    print(f"Found {len(result.data)} 'completed' items\n")
    
    for item in result.data:
        print(f"=== Item {item['id']} - {item.get('upload_id')} ===")
        print(f"  Status: {item['status']}")
        print(f"  Final accuracy: {item.get('final_accuracy')}")
        print(f"  Completed at: {item.get('completed_at')}")
        print(f"  API cost: {item.get('api_cost')}")
        print(f"  Iterations: {item.get('iterations_completed')}")
        
        # Check if there's actual extraction data
        extraction_result = item.get('extraction_result')
        planogram_result = item.get('planogram_result')
        
        print(f"\n  Extraction result: {'Present' if extraction_result else 'MISSING'}")
        if extraction_result:
            if isinstance(extraction_result, str):
                try:
                    extraction_result = json.loads(extraction_result)
                except:
                    pass
            if isinstance(extraction_result, dict):
                print(f"    - Products found: {len(extraction_result.get('products', []))}")
                print(f"    - Has structure: {'structure' in extraction_result}")
        
        print(f"\n  Planogram result: {'Present' if planogram_result else 'MISSING'}")
        if planogram_result:
            if isinstance(planogram_result, str):
                try:
                    planogram_result = json.loads(planogram_result)
                except:
                    pass
            if isinstance(planogram_result, dict):
                print(f"    - Shelves: {len(planogram_result.get('shelves', []))}")
        
        print(f"\n  🚨 This looks like {'REAL' if extraction_result else 'FAKE'} data\n")