import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Read the SQL file
    with open('fix_queue_trigger.sql', 'r') as f:
        sql = f.read()
    
    # Note: Supabase client doesn't support running raw SQL directly
    # We need to use the REST API or connect via psycopg2
    
    print("To apply this fix, you need to:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to the SQL Editor")
    print("3. Paste and run the following SQL:")
    print("\n" + "="*50 + "\n")
    print(sql)
    print("\n" + "="*50 + "\n")
    print("\nThis will fix the trigger so new queue items automatically get the correct image path.")