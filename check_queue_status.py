import os
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from environment
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
    exit(1)

# Create Supabase client
supabase: Client = create_client(url, key)

print("Query 1: Count items by status")
print("=" * 50)

# Query 1: Count items grouped by status
try:
    response = supabase.table('ai_extraction_queue').select('status').execute()
    
    # Manual grouping since Supabase doesn't support GROUP BY in select
    status_counts = {}
    for item in response.data:
        status = item['status']
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    total_items = len(response.data)
    print(f"Total items in queue: {total_items}")
    print("\nBreakdown by status:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
        
except Exception as e:
    print(f"Error executing query 1: {e}")

print("\n\nQuery 2: Recently added items (last 10)")
print("=" * 50)

# Query 2: Get recent items
try:
    response = supabase.table('ai_extraction_queue')\
        .select('id, upload_id, status, created_at, completed_at')\
        .order('created_at', desc=True)\
        .limit(10)\
        .execute()
    
    print(f"Found {len(response.data)} recent items:\n")
    for item in response.data:
        print(f"ID: {item['id']}")
        print(f"  Upload ID: {item['upload_id']}")
        print(f"  Status: {item['status']}")
        print(f"  Created: {item['created_at']}")
        print(f"  Completed: {item['completed_at']}")
        print("-" * 30)
        
except Exception as e:
    print(f"Error executing query 2: {e}")

print("\n\nQuery 3: Check for pending items specifically")
print("=" * 50)

# Query 3: Get all pending items
try:
    response = supabase.table('ai_extraction_queue')\
        .select('id, upload_id, created_at')\
        .eq('status', 'pending')\
        .order('created_at', desc=True)\
        .execute()
    
    print(f"Found {len(response.data)} pending items")
    if response.data:
        print("\nFirst 5 pending items:")
        for item in response.data[:5]:
            print(f"  ID: {item['id']}, Upload: {item['upload_id']}, Created: {item['created_at']}")
        
except Exception as e:
    print(f"Error executing query 3: {e}")