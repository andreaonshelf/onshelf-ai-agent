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

print("=== CHECKING ALL PROMPTS FOR FIELD FORMAT ISSUES ===")

try:
    # Query all prompts with fields
    result = supabase.table('prompt_templates').select('prompt_id, template_id, name, fields').not_.is_('fields', 'null').execute()
    
    prompts_to_fix = []
    
    if result.data:
        print(f"\nFound {len(result.data)} prompts with fields defined\n")
        
        for prompt in result.data:
            name = prompt.get('name', prompt.get('template_id', 'Unknown'))
            
            if prompt.get('fields'):
                try:
                    parsed = json.loads(prompt['fields'])
                    
                    if isinstance(parsed, dict):
                        # Check if it's a JSON schema format (has properties or a single top-level key)
                        if 'properties' in parsed or (len(parsed) == 1 and isinstance(list(parsed.values())[0], dict)):
                            print(f"❌ {name}: Fields are in JSON schema format (dict)")
                            prompts_to_fix.append(prompt)
                        else:
                            print(f"⚠️  {name}: Fields are dict but not clear schema format")
                    elif isinstance(parsed, list):
                        print(f"✅ {name}: Fields are already in array format")
                    else:
                        print(f"⚠️  {name}: Fields are {type(parsed)}")
                        
                except json.JSONDecodeError:
                    print(f"❌ {name}: Failed to parse fields JSON")
                except Exception as e:
                    print(f"❌ {name}: Error checking fields: {e}")
                    
        print(f"\n\nSummary: Found {len(prompts_to_fix)} prompts that need field format conversion")
        
        if prompts_to_fix:
            print("\nPrompts that need fixing:")
            for prompt in prompts_to_fix:
                print(f"  - {prompt.get('name', prompt.get('template_id'))}")
                
    else:
        print("No prompts with fields found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()