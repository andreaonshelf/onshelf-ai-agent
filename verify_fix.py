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

print("=== VERIFYING PRODUCT V1 FIX ===")

try:
    # Query Product v1 prompt
    result = supabase.table('prompt_templates').select('template_id, name, fields').eq('name', 'Product v1').execute()
    
    if result.data and len(result.data) > 0:
        prompt = result.data[0]
        print(f"\nPrompt: {prompt['name']} ({prompt['template_id']})")
        
        if prompt.get('fields'):
            fields_str = prompt['fields']
            print(f"\nFields type: {type(fields_str)}")
            
            try:
                parsed = json.loads(fields_str)
                print(f"Parsed type: {type(parsed)}")
                
                if isinstance(parsed, list):
                    print(f"✅ SUCCESS: Fields are now an array with {len(parsed)} items")
                    print("\nFirst field:")
                    print(json.dumps(parsed[0], indent=2))
                else:
                    print(f"❌ ERROR: Fields are still {type(parsed)}, not an array")
                    
            except json.JSONDecodeError as e:
                print(f"❌ ERROR: Failed to parse fields: {e}")
                
    else:
        print("Product v1 prompt not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()