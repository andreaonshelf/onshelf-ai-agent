#!/usr/bin/env python3
"""Reset queue item 8 to pending status so we can see actual processing logs"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Reset queue item status
def reset_queue_item():
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("🔄 Resetting queue item 8 status to 'pending'...")
    
    result = supabase.table("ai_extraction_queue").update({
        "status": "pending",
        "started_at": None,
        "completed_at": None
    }).eq("id", 8).execute()
    
    print(f"✅ Reset complete: {result.data}")

if __name__ == "__main__":
    reset_queue_item()