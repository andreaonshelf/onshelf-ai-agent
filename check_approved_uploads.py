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
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")
    exit(1)

# Create Supabase client
supabase: Client = create_client(url, key)

print("Checking uploads table for approved items")
print("=" * 50)

# Check uploads table for approved items
try:
    response = supabase.table('uploads')\
        .select('id, upload_id, status, approved, created_at')\
        .eq('approved', True)\
        .order('created_at', desc=True)\
        .execute()
    
    print(f"Found {len(response.data)} approved uploads\n")
    
    approved_upload_ids = set()
    for item in response.data:
        approved_upload_ids.add(item['upload_id'])
        print(f"Upload ID: {item['upload_id']}")
        print(f"  ID: {item['id']}")
        print(f"  Status: {item['status']}")
        print(f"  Approved: {item['approved']}")
        print(f"  Created: {item['created_at']}")
        print("-" * 30)
        
except Exception as e:
    print(f"Error querying uploads table: {e}")
    approved_upload_ids = set()

print("\n\nCross-checking with extraction queue")
print("=" * 50)

# Get all items from extraction queue
try:
    response = supabase.table('ai_extraction_queue')\
        .select('upload_id')\
        .execute()
    
    queue_upload_ids = set(item['upload_id'] for item in response.data)
    
    # Find approved uploads not in queue
    missing_from_queue = approved_upload_ids - queue_upload_ids
    
    print(f"Approved uploads: {len(approved_upload_ids)}")
    print(f"Items in queue: {len(queue_upload_ids)}")
    print(f"Missing from queue: {len(missing_from_queue)}")
    
    if missing_from_queue:
        print("\nApproved uploads missing from extraction queue:")
        for upload_id in missing_from_queue:
            print(f"  - {upload_id}")
    else:
        print("\nAll approved uploads are in the extraction queue")
        
except Exception as e:
    print(f"Error cross-checking: {e}")

print("\n\nChecking for any uploads with status='approved' not in queue")
print("=" * 50)

# Alternative check - look for uploads with status='approved'
try:
    response = supabase.table('uploads')\
        .select('id, upload_id, status, approved, created_at')\
        .eq('status', 'approved')\
        .order('created_at', desc=True)\
        .execute()
    
    print(f"Found {len(response.data)} uploads with status='approved'")
    
    if response.data:
        print("\nFirst 5:")
        for item in response.data[:5]:
            print(f"  Upload ID: {item['upload_id']}, Approved flag: {item['approved']}, Created: {item['created_at']}")
            
except Exception as e:
    print(f"Error checking status='approved': {e}")