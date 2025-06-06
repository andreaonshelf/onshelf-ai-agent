import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=== CHECKING CURRENT PROMPTS TO UPDATE ===")

# Look for the prompts we need to update
prompt_types_to_update = ['structure', 'product', 'detail', 'visual']

for prompt_type in prompt_types_to_update:
    print(f"\n--- Checking {prompt_type} prompts ---")
    try:
        result = supabase.table('prompt_templates').select('*').eq('prompt_type', prompt_type).execute()
        
        if result.data:
            for prompt in result.data:
                print(f"\nFound: {prompt.get('name', 'No name')}")
                print(f"ID: {prompt.get('prompt_id')}")
                print(f"Type: {prompt.get('prompt_type')}")
                print(f"Active: {prompt.get('is_active')}")
                
                # Check fields structure
                fields = prompt.get('fields')
                if fields:
                    if isinstance(fields, str):
                        try:
                            fields = json.loads(fields)
                        except:
                            pass
                    print(f"Fields structure: {json.dumps(fields, indent=2) if isinstance(fields, (dict, list)) else fields[:100] + '...' if len(str(fields)) > 100 else fields}")
                else:
                    print("No fields defined")
        else:
            print(f"No prompts found for type: {prompt_type}")
            
    except Exception as e:
        print(f"Error checking {prompt_type}: {e}")

# Also check for 'position' type which might be the product extraction
print(f"\n--- Checking position prompts (might be product) ---")
try:
    result = supabase.table('prompt_templates').select('*').eq('prompt_type', 'position').execute()
    
    if result.data:
        for prompt in result.data:
            print(f"\nFound: {prompt.get('name', 'No name')}")
            print(f"ID: {prompt.get('prompt_id')}")
            print(f"Type: {prompt.get('prompt_type')}")
            print(f"Active: {prompt.get('is_active')}")
            
            # Check fields structure
            fields = prompt.get('fields')
            if fields:
                if isinstance(fields, str):
                    try:
                        fields = json.loads(fields)
                    except:
                        pass
                print(f"Fields structure: {json.dumps(fields, indent=2) if isinstance(fields, (dict, list)) else fields[:100] + '...' if len(str(fields)) > 100 else fields}")
            else:
                print("No fields defined")
except Exception as e:
    print(f"Error checking position: {e}")