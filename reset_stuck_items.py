#!/usr/bin/env python3
"""
Reset stuck processing items
"""

import os
from supabase import create_client
from datetime import datetime, timedelta

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    print("🔄 Resetting stuck items...")
    
    # Reset ALL processing items to pending
    result = supabase.table("ai_extraction_queue").select("*").eq("status", "processing").execute()
    
    if result.data:
        print(f"\nFound {len(result.data)} stuck processing items")
        
        for item in result.data:
            # Check how long it's been processing
            duration_str = "unknown"
            if item.get('started_at'):
                started = datetime.fromisoformat(item['started_at'].replace('Z', '+00:00'))
                duration = datetime.utcnow().replace(tzinfo=started.tzinfo) - started
                duration_str = str(duration)
            
            print(f"  - Item {item['id']} (processing for {duration_str})")
            
            # Reset to pending
            update_result = supabase.table("ai_extraction_queue").update({
                "status": "pending",
                "started_at": None,
                "current_extraction_system": None,
                "error_message": "Reset from stuck processing state"
            }).eq("id", item['id']).execute()
            
            if update_result.data:
                print(f"    ✓ Reset to pending")
    else:
        print("✓ No stuck items found")
    
    # Also clean up any fake completed items
    print("\n🔄 Checking for fake completed items...")
    
    completed = supabase.table("ai_extraction_queue").select("*").eq("status", "completed").execute()
    
    fake_count = 0
    for item in completed.data:
        is_fake = False
        
        # Check for fake patterns
        if item.get('final_accuracy') == 0.91:
            is_fake = True
        elif item.get('api_cost', 0) == 0 and item.get('iterations_completed', 0) > 0:
            is_fake = True
        elif not item.get('extraction_result'):
            is_fake = True
            
        if is_fake:
            print(f"  - Resetting fake item {item['id']}")
            supabase.table("ai_extraction_queue").update({
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
            fake_count += 1
    
    if fake_count > 0:
        print(f"\n✓ Reset {fake_count} fake completed items")
    else:
        print("✓ No fake completed items found")
    
    print("\n✅ Cleanup complete!")
else:
    print("❌ Missing Supabase credentials")