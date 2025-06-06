import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get ALL items
    result = supabase.table("ai_extraction_queue").select("*").execute()
    
    print(f"Checking all {len(result.data)} items for fake data...\n")
    
    reset_count = 0
    for item in result.data:
        reset_this = False
        reasons = []
        
        # Check for fake patterns
        if item.get('final_accuracy') == 0.91:
            reset_this = True
            reasons.append("91% fake accuracy")
            
        if item.get('status') == 'completed' and item.get('api_cost', 0) == 0:
            reset_this = True
            reasons.append("Completed with zero cost")
            
        extraction = item.get('extraction_result', {})
        if item.get('status') == 'completed' and isinstance(extraction, dict) and len(extraction.get('products', [])) == 0:
            reset_this = True
            reasons.append("Completed with no products")
            
        if reset_this:
            print(f"Resetting item {item['id']} - {reasons}")
            
            # Reset to pending
            update_result = supabase.table("ai_extraction_queue").update({
                "status": "pending",
                "final_accuracy": None,
                "extraction_result": None,
                "planogram_result": None,
                "completed_at": None,
                "started_at": None,
                "error_message": None,
                "api_cost": None,
                "iterations_completed": None,
                "processing_duration_seconds": None
            }).eq("id", item['id']).execute()
            
            if update_result.data:
                reset_count += 1
    
    print(f"\n✓ Reset {reset_count} fake items to pending")
    
    # Also reset stuck processing items
    processing_result = supabase.table("ai_extraction_queue").select("*").eq("status", "processing").execute()
    
    stuck_count = 0
    for item in processing_result.data:
        # Reset to pending so they can be reprocessed
        update_result = supabase.table("ai_extraction_queue").update({
            "status": "pending",
            "started_at": None,
            "error_message": "Reset from stuck processing state"
        }).eq("id", item['id']).execute()
        
        if update_result.data:
            stuck_count += 1
            print(f"✓ Reset stuck processing item {item['id']} to pending")
    
    print(f"\n✓ Reset {stuck_count} stuck processing items")