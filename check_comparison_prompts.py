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
    
    # Execute the SQL query
    query = """
    SELECT 
        name, 
        prompt_type, 
        stage_type, 
        is_active,
        LENGTH(prompt_text) as text_length,
        SUBSTRING(prompt_text, 1, 150) as prompt_preview
    FROM prompt_templates 
    WHERE is_active = true 
    AND (prompt_type = 'comparison' OR stage_type = 'comparison' OR name LIKE '%Visual%')
    ORDER BY name;
    """
    
    try:
        # Execute raw SQL query using RPC
        result = supabase.rpc('execute_sql', {'query': query}).execute()
        
        if result.data:
            print("Found comparison/visual prompts:")
            print("-" * 80)
            for row in result.data:
                print(f"Name: {row.get('name')}")
                print(f"Prompt Type: {row.get('prompt_type')}")
                print(f"Stage Type: {row.get('stage_type')}")
                print(f"Is Active: {row.get('is_active')}")
                print(f"Text Length: {row.get('text_length')}")
                print(f"Preview: {row.get('prompt_preview')[:100]}...")
                print("-" * 80)
        else:
            print("No comparison/visual prompts found")
            
    except Exception as e:
        print(f"Error executing query: {e}")
        
        # Try alternative approach - direct table query
        print("\nTrying alternative approach...")
        try:
            # Query using the table API with filters
            response = supabase.table('prompt_templates') \
                .select('name, prompt_type, stage_type, is_active, prompt_text') \
                .eq('is_active', True) \
                .execute()
            
            # Filter for comparison/visual prompts
            comparison_prompts = []
            for row in response.data:
                if (row.get('prompt_type') == 'comparison' or 
                    row.get('stage_type') == 'comparison' or 
                    'Visual' in row.get('name', '')):
                    comparison_prompts.append(row)
            
            if comparison_prompts:
                print(f"\nFound {len(comparison_prompts)} comparison/visual prompts:")
                print("-" * 80)
                for row in comparison_prompts:
                    print(f"Name: {row.get('name')}")
                    print(f"Prompt Type: {row.get('prompt_type')}")
                    print(f"Stage Type: {row.get('stage_type')}")
                    print(f"Is Active: {row.get('is_active')}")
                    print(f"Text Length: {len(row.get('prompt_text', ''))}")
                    print(f"Preview: {row.get('prompt_text', '')[:150]}...")
                    print("-" * 80)
            else:
                print("No comparison/visual prompts found")
                
        except Exception as e2:
            print(f"Alternative approach also failed: {e2}")