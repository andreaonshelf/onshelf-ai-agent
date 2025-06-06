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

print("=== SEARCHING FOR VISUAL PROMPTS ===")

# Search for prompts that might be visual analysis
try:
    # Get all prompts and search for ones containing 'visual' or 'planogram' in name or description
    result = supabase.table('prompt_templates').select('*').execute()
    
    visual_related = []
    for prompt in result.data:
        name = (prompt.get('name') or '').lower()
        desc = (prompt.get('description') or '').lower()
        prompt_type = prompt.get('prompt_type', '')
        
        if any(keyword in name or keyword in desc for keyword in ['visual', 'planogram', 'layout', 'rendering']):
            visual_related.append(prompt)
            
    print(f"Found {len(visual_related)} visual-related prompts:")
    for prompt in visual_related:
        print(f"\nName: {prompt.get('name')}")
        print(f"ID: {prompt.get('prompt_id')}")
        print(f"Type: {prompt.get('prompt_type')}")
        print(f"Description: {prompt.get('description', 'No description')}")
        
        # Check fields
        fields = prompt.get('fields')
        if fields:
            if isinstance(fields, str):
                try:
                    fields = json.loads(fields)
                except:
                    pass
            print(f"Has fields: {'Yes' if fields else 'No'}")
            
except Exception as e:
    print(f"Error searching: {e}")