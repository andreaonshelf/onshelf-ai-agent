import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Find all "completed" items with suspicious data
    result = supabase.table("ai_extraction_queue").select("*").eq("status", "completed").execute()
    
    print(f"Found {len(result.data)} completed items, checking for fake data...\n")
    
    fake_items = []
    for item in result.data:
        # Check if this looks like fake data
        is_fake = False
        reasons = []
        
        # Check for suspicious patterns
        if item.get('final_accuracy') == 0.91:
            is_fake = True
            reasons.append("Exact 91% accuracy (common mock value)")
            
        if item.get('api_cost') == 0.0 and item.get('iterations_completed') == 1:
            is_fake = True
            reasons.append("Zero cost with only 1 iteration")
            
        extraction = item.get('extraction_result', {})
        if isinstance(extraction, dict) and len(extraction.get('products', [])) == 0:
            is_fake = True
            reasons.append("No products extracted")
            
        if is_fake:
            fake_items.append(item['id'])
            print(f"Item {item['id']} - FAKE DATA:")
            for reason in reasons:
                print(f"  - {reason}")
    
    if fake_items:
        print(f"\nResetting {len(fake_items)} fake completed items to pending...")
        
        for item_id in fake_items:
            result = supabase.table("ai_extraction_queue").update({
                "status": "pending",
                "final_accuracy": None,
                "extraction_result": None,
                "planogram_result": None,
                "completed_at": None,
                "started_at": None,
                "error_message": None,
                "api_cost": None,
                "iterations_completed": None
            }).eq("id", item_id).execute()
            
            if result.data:
                print(f"✓ Reset item {item_id} to pending")
    else:
        print("No fake completed items found")