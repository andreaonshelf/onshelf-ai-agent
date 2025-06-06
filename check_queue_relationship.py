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

print("Analyzing relationship between uploads and extraction queue")
print("=" * 60)

# Get all queue items
try:
    queue_response = supabase.table('ai_extraction_queue')\
        .select('*')\
        .order('created_at', desc=True)\
        .execute()
    
    print(f"Found {len(queue_response.data)} items in extraction queue")
    
    # Get corresponding uploads
    queue_upload_ids = [item['upload_id'] for item in queue_response.data]
    
    uploads_response = supabase.table('uploads')\
        .select('id, status, review_status, approval_status, created_at')\
        .in_('id', queue_upload_ids)\
        .execute()
    
    uploads_dict = {u['id']: u for u in uploads_response.data}
    
    print("\nQueue items with corresponding upload info:")
    print("-" * 60)
    
    for queue_item in queue_response.data:
        upload_id = queue_item['upload_id']
        upload_info = uploads_dict.get(upload_id, None)
        
        print(f"\nQueue ID: {queue_item['id']} | Upload ID: {upload_id}")
        print(f"  Queue Status: {queue_item['status']}")
        print(f"  Queue Created: {queue_item['created_at']}")
        
        if upload_info:
            print(f"  Upload Status: {upload_info['status']}")
            print(f"  Review Status: {upload_info['review_status']}")
            print(f"  Approval Status: {upload_info['approval_status']}")
        else:
            print("  [Upload not found in uploads table]")
            
except Exception as e:
    print(f"Error: {e}")

print("\n\nChecking for uploads that should be in queue but aren't")
print("=" * 60)

# Look for uploads that might need to be in the queue
try:
    # Get uploads with completed status that aren't in the queue
    uploads_response = supabase.table('uploads')\
        .select('id, status, review_status, approval_status, created_at')\
        .eq('status', 'completed')\
        .order('created_at', desc=True)\
        .limit(20)\
        .execute()
    
    queue_ids = set(queue_upload_ids)
    
    print(f"Found {len(uploads_response.data)} completed uploads")
    print("\nCompleted uploads not in extraction queue:")
    
    count = 0
    for upload in uploads_response.data:
        if upload['id'] not in queue_ids:
            count += 1
            print(f"\n{count}. Upload ID: {upload['id']}")
            print(f"   Status: {upload['status']}")
            print(f"   Review: {upload['review_status']}")
            print(f"   Approval: {upload['approval_status']}")
            print(f"   Created: {upload['created_at']}")
            
            if count >= 10:  # Limit output
                remaining = len(uploads_response.data) - count
                if remaining > 0:
                    print(f"\n... and {remaining} more")
                break
                
except Exception as e:
    print(f"Error: {e}")

print("\n\nSummary")
print("=" * 60)
print(f"Total items in extraction queue: {len(queue_response.data)}")
print("Queue status breakdown:")
status_counts = {}
for item in queue_response.data:
    status = item['status']
    status_counts[status] = status_counts.get(status, 0) + 1

for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")