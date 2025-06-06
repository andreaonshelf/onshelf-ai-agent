import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get Supabase URL and key
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)
print("Connected to Supabase\n")

# Test the same logic as the API endpoint
stages = ["structure", "products", "details", "validation", "comparison", "orchestrator"]

stage_to_prompt_type = {
    "structure": "structure",
    "products": "position",
    "details": "detail",
    "validation": "validation"
}

print("=== TESTING PROMPT RETRIEVAL BY STAGE ===\n")

for stage in stages:
    print(f"Stage: {stage}")
    prompts = []
    
    try:
        # First try to get by stage_type (v2 prompts)
        result = supabase.table("prompt_templates").select("*").eq("stage_type", stage).eq("is_active", True).execute()
        
        # If no results, try legacy prompt_type
        if not result.data:
            prompt_type = stage_to_prompt_type.get(stage, stage)
            result = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type).eq("is_active", True).execute()
        
        if result.data:
            print(f"  ✓ Found {len(result.data)} prompts")
            for prompt in result.data:
                # Extract name
                prompt_name = prompt.get('name')
                if not prompt_name:
                    template_id = prompt.get('template_id', '')
                    if template_id.startswith('user_'):
                        parts = template_id.split('_')
                        if len(parts) >= 3:
                            prompt_name = ' '.join(parts[1:-2]).replace('_', ' ').title()
                    if not prompt_name:
                        prompt_name = f"{prompt['prompt_type']} v{prompt.get('prompt_version', '1.0')}"
                
                print(f"    - {prompt_name}")
                print(f"      ID: {prompt.get('prompt_id')}")
                print(f"      Template ID: {prompt.get('template_id')}")
                print(f"      Type: {prompt.get('prompt_type')}")
                print(f"      Stage: {prompt.get('stage_type')}")
                print(f"      Content preview: {prompt.get('prompt_text', '')[:100]}...")
                
                # Check fields
                fields = prompt.get('fields', [])
                if fields:
                    print(f"      Fields: {len(fields)} defined")
                    for field in fields[:3]:  # Show first 3
                        print(f"        - {field.get('name')} ({field.get('type')})")
                print()
        else:
            print(f"  ✗ No prompts found")
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
    
    print()

# Also test a specific case to understand the data
print("=== DETAILED CHECK FOR PRODUCTS STAGE ===")
try:
    # Check both methods
    result1 = supabase.table("prompt_templates").select("*").eq("stage_type", "products").execute()
    result2 = supabase.table("prompt_templates").select("*").eq("prompt_type", "position").execute()
    
    print(f"By stage_type='products': {len(result1.data)} results")
    print(f"By prompt_type='position': {len(result2.data)} results")
    
    if result2.data:
        print("\nFirst prompt details:")
        prompt = result2.data[0]
        for key, value in prompt.items():
            if key in ['prompt_text', 'fields']:
                print(f"  {key}: {str(value)[:100]}...")
            else:
                print(f"  {key}: {value}")
                
except Exception as e:
    print(f"Error: {str(e)}")

print("\n✅ Test complete")