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

print("Checking uploads table structure")
print("=" * 50)

# First, let's just get a sample row to see the columns
try:
    response = supabase.table('uploads')\
        .select('*')\
        .limit(1)\
        .execute()
    
    if response.data:
        print("Columns in uploads table:")
        for key in response.data[0].keys():
            print(f"  - {key}")
    else:
        print("No data in uploads table")
        
except Exception as e:
    print(f"Error querying uploads table: {e}")

print("\n\nChecking all uploads")
print("=" * 50)

# Get all uploads
try:
    response = supabase.table('uploads')\
        .select('*')\
        .order('created_at', desc=True)\
        .execute()
    
    print(f"Found {len(response.data)} uploads total\n")
    
    # Count by status
    status_counts = {}
    approved_count = 0
    
    for item in response.data:
        # Check if there's a status field
        if 'status' in item:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Check if there's an approved field
        if 'approved' in item and item['approved']:
            approved_count += 1
    
    print("Status counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    print(f"\nApproved uploads: {approved_count}")
    
    # Show recent uploads
    print("\nRecent uploads (last 5):")
    for item in response.data[:5]:
        print(f"\nID: {item.get('id', 'N/A')}")
        for key, value in item.items():
            if key != 'id':
                print(f"  {key}: {value}")
        print("-" * 30)
        
except Exception as e:
    print(f"Error: {e}")