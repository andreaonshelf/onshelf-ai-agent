#!/usr/bin/env python3
"""
CHECK WHAT'S HAPPENING WITH EXTRACTION RIGHT NOW
"""

import os
from supabase import create_client
from datetime import datetime, timedelta

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 CHECKING EXTRACTION STATUS")
print("=" * 60)

# Check queue items
print("\n1️⃣ QUEUE ITEMS:")
queue_items = supabase.table("ai_extraction_queue").select("*").order("created_at", desc=True).limit(10).execute()

for item in queue_items.data:
    print(f"\n   ID: {item['id']}")
    print(f"   Status: {item['status']}")
    print(f"   Upload ID: {item['upload_id']}")
    print(f"   Created: {item['created_at']}")
    print(f"   Accuracy: {item.get('accuracy_estimate', 'None')}")
    print(f"   Model Config: {'YES' if item.get('model_config') else 'NO'}")
    
    # Check if there's a fake accuracy
    if item.get('accuracy_estimate') == 91.0:
        print("   ⚠️ FAKE ACCURACY DETECTED!")

# Check extraction runs if table exists
print("\n\n2️⃣ CHECKING EXTRACTION RUNS:")
try:
    runs = supabase.table("extraction_runs").select("*").order("created_at", desc=True).limit(5).execute()
    for run in runs.data:
        print(f"\n   Run ID: {run['run_id']}")
        print(f"   Status: {run['status']}")
        print(f"   Created: {run['created_at']}")
except:
    print("   ❌ extraction_runs table doesn't exist")

# Check recent activity in last 5 minutes
print("\n\n3️⃣ RECENT ACTIVITY (last 5 minutes):")
five_mins_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
recent = supabase.table("ai_extraction_queue").select("*").gte("updated_at", five_mins_ago).execute()

if recent.data:
    print(f"   Found {len(recent.data)} items updated in last 5 minutes:")
    for item in recent.data:
        print(f"   - ID {item['id']}: {item['status']} (updated {item['updated_at']})")
else:
    print("   No items updated in last 5 minutes")

# Check for any processing items
print("\n\n4️⃣ ITEMS IN PROCESSING STATE:")
processing = supabase.table("ai_extraction_queue").select("*").eq("status", "processing").execute()

if processing.data:
    print(f"   Found {len(processing.data)} items in processing state:")
    for item in processing.data:
        print(f"   - ID {item['id']}: {item['upload_id']} (started {item['updated_at']})")
else:
    print("   No items currently processing")

# Check saved configurations
print("\n\n5️⃣ SAVED CONFIGURATIONS:")
configs = supabase.table("prompt_templates").select("prompt_id, name, extraction_config").eq("prompt_type", "configuration").execute()

for config in configs.data:
    print(f"\n   Config: {config['name']}")
    print(f"   ID: {config['prompt_id']}")
    if config.get('extraction_config'):
        ec = config['extraction_config']
        stages = ec.get('stages', {})
        print(f"   Stages configured: {list(stages.keys())}")
        
        # Check if stages have prompts
        for stage_id, stage_data in stages.items():
            if isinstance(stage_data, dict) and 'prompt_text' in stage_data:
                print(f"   ✅ {stage_id} has prompt_text")
            else:
                print(f"   ❌ {stage_id} missing prompt_text")