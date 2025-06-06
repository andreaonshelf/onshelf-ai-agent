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
        # Query for all active prompts
        response = supabase.table('prompt_templates') \
            .select('name, prompt_type, stage_type, is_active') \
            .eq('is_active', True) \
            .order('prompt_type', desc=False) \
            .order('stage_type', desc=False) \
            .order('name', desc=False) \
            .execute()
        
        if response.data:
            # Group by prompt_type
            prompts_by_type = {}
            for prompt in response.data:
                ptype = prompt.get('prompt_type', 'unknown')
                if ptype not in prompts_by_type:
                    prompts_by_type[ptype] = []
                prompts_by_type[ptype].append(prompt)
            
            print("Active Prompts by Type:")
            print("=" * 80)
            
            for ptype, prompts in sorted(prompts_by_type.items()):
                print(f"\n{ptype.upper()} PROMPTS ({len(prompts)}):")
                print("-" * 40)
                for prompt in prompts:
                    print(f"  - {prompt.get('name')} (stage: {prompt.get('stage_type')})")
            
            print("\n" + "=" * 80)
            print(f"Total active prompts: {len(response.data)}")
        else:
            print("No active prompts found")
            
    except Exception as e:
        print(f"Error: {e}")