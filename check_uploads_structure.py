import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if supabase_url and supabase_key:
    supabase = create_client(supabase_url, supabase_key)
    
    # Get one upload record to see its structure
    result = supabase.table("uploads").select("*").limit(1).execute()
    
    if result.data:
        print("Uploads table structure:")
        for key in result.data[0].keys():
            print(f"  - {key}: {type(result.data[0][key]).__name__}")