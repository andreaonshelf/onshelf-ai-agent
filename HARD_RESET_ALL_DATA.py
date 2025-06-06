#!/usr/bin/env python3
"""
HARD RESET - Remove ALL fake data and reset everything
"""

import os
from supabase import create_client
from datetime import datetime

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Missing Supabase credentials")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

print("🔥 HARD RESET - REMOVING ALL FAKE DATA")
print("=" * 50)

# Get ALL items
result = supabase.table("ai_extraction_queue").select("*").execute()

if not result.data:
    print("No items found")
    exit(0)

print(f"Found {len(result.data)} total items")

# Reset EVERYTHING that looks fake
reset_count = 0
for item in result.data:
    should_reset = False
    reasons = []
    
    # Any 91% accuracy is fake
    if item.get('final_accuracy') == 0.91:
        should_reset = True
        reasons.append("91% fake accuracy")
    
    # Completed with no extraction result
    if item.get('status') == 'completed' and not item.get('extraction_result'):
        should_reset = True
        reasons.append("Completed with no extraction data")
    
    # Completed with zero cost
    if item.get('status') == 'completed' and item.get('api_cost', 0) == 0:
        should_reset = True
        reasons.append("Completed with zero API cost")
    
    # Processing for too long
    if item.get('status') == 'processing':
        if item.get('started_at'):
            started = datetime.fromisoformat(item['started_at'].replace('Z', '+00:00'))
            duration = datetime.utcnow().replace(tzinfo=started.tzinfo) - started
            if duration.total_seconds() > 300:  # 5 minutes
                should_reset = True
                reasons.append(f"Stuck in processing for {duration}")
    
    if should_reset:
        print(f"\n🗑️  Resetting item {item['id']}:")
        print(f"   Store: {item.get('ready_media_id', 'Unknown')}")
        print(f"   Status: {item['status']}")
        print(f"   Reasons: {', '.join(reasons)}")
        
        # HARD RESET - clear everything
        update_data = {
            "status": "pending",
            "final_accuracy": None,
            "extraction_result": None,
            "planogram_result": None,
            "completed_at": None,
            "started_at": None,
            "error_message": None,
            "api_cost": None,
            "iterations_completed": None,
            "processing_duration_seconds": None,
            "human_review_required": False,
            "escalation_reason": None,
            "current_extraction_system": None,
            "selected_systems": ["custom_consensus"],  # Reset to default
            "comparison_group_id": None
        }
        
        result = supabase.table("ai_extraction_queue").update(update_data).eq("id", item['id']).execute()
        
        if result.data:
            reset_count += 1
            print("   ✅ Reset complete")
        else:
            print("   ❌ Reset failed")

print(f"\n{'='*50}")
print(f"✅ HARD RESET COMPLETE")
print(f"   Total items reset: {reset_count}")
print(f"   All fake data removed")
print(f"\n📝 Next steps:")
print(f"   1. Restart the server: python main.py")
print(f"   2. Process items manually in the dashboard")
print(f"   3. Monitor real extraction progress")