#!/usr/bin/env python3
"""Reset failed items back to pending so they can be retried with the fix"""

from src.config import SystemConfig
from supabase import create_client

config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key)

# Reset the two failed items
queue_ids = [6, 9]

for queue_id in queue_ids:
    result = supabase.table("ai_extraction_queue").update({
        "status": "pending",
        "error_message": None,
        "failed_at": None,
        "started_at": None,
        "processing_duration_seconds": None
    }).eq("id", queue_id).execute()
    
    if result.data:
        print(f"✅ Reset queue item {queue_id} to pending")
    else:
        print(f"❌ Failed to reset queue item {queue_id}")

print("\nItems have been reset. They can now be reprocessed with the fixed configuration.")