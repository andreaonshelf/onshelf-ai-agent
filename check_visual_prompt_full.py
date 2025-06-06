import os
from supabase import create_client, Client

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Supabase credentials not found in environment variables")
else:
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Query for the Visual v1 prompt specifically
        response = supabase.table('prompt_templates') \
            .select('*') \
            .eq('name', 'Visual v1') \
            .execute()
        
        if response.data and len(response.data) > 0:
            prompt = response.data[0]
            print("Visual v1 Prompt Details:")
            print("-" * 80)
            print(f"Name: {prompt.get('name')}")
            print(f"Prompt Type: {prompt.get('prompt_type')}")
            print(f"Stage Type: {prompt.get('stage_type')}")
            print(f"Is Active: {prompt.get('is_active')}")
            print(f"Model Config: {prompt.get('model_config')}")
            print(f"\nFull Prompt Text:")
            print("-" * 80)
            print(prompt.get('prompt_text'))
            print("-" * 80)
            print(f"\nExtraction Fields: {prompt.get('extraction_fields')}")
        else:
            print("Visual v1 prompt not found")
            
    except Exception as e:
        print(f"Error: {e}")