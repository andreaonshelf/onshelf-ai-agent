import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(url, key)

print("Examining Product v1 prompt in detail...")
print("="*80)

# Get the Product v1 prompt
response = supabase.table('prompt_templates').select('*').eq('name', 'Product v1').execute()

if not response.data:
    print("Product v1 prompt not found!")
    exit(1)

prompt = response.data[0]

print(f"\nPrompt ID: {prompt['prompt_id']}")
print(f"Name: {prompt['name']}")
print(f"Type: {prompt['prompt_type']}")
print(f"Description: {prompt.get('description', 'N/A')}")

# Check all fields that might contain the actual prompt text
text_fields = ['prompt_text', 'template', 'fields', 'context', 'variables']

for field_name in text_fields:
    if prompt.get(field_name):
        print(f"\n{'='*80}")
        print(f"{field_name}:")
        print("="*80)
        
        content = prompt[field_name]
        if isinstance(content, str):
            # Show first 2000 characters
            print(content[:2000])
            if len(content) > 2000:
                print(f"\n... (truncated, total length: {len(content)} characters)")
                
                # Look for field definitions in the text
                if 'dimensions' in content or 'nutrition' in content or 'product_name' in content:
                    print("\n\nSearching for field definitions in text...")
                    
                    # Find all occurrences of common field patterns
                    import re
                    
                    # Pattern to find field definitions
                    patterns = [
                        r'"(\w+)":\s*{[^}]+}',  # JSON-like field definitions
                        r'(\w+):\s*{[^}]+}',    # YAML-like field definitions
                        r'- (\w+):',            # List-style definitions
                        r'\*\*(\w+)\*\*:',      # Markdown bold definitions
                    ]
                    
                    found_fields = set()
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        found_fields.update(matches)
                    
                    if found_fields:
                        print(f"Found {len(found_fields)} potential field names:")
                        sorted_fields = sorted(found_fields)
                        for i in range(0, len(sorted_fields), 5):
                            print(f"  {', '.join(sorted_fields[i:i+5])}")
                            
        elif isinstance(content, list):
            print(f"List with {len(content)} items")
            if content:
                print("First item:", json.dumps(content[0], indent=2)[:500])
        elif isinstance(content, dict):
            print(f"Dictionary with keys: {list(content.keys())}")
            print(json.dumps(content, indent=2)[:1000])

# Check field_definitions specifically
print(f"\n{'='*80}")
print("field_definitions:")
print("="*80)
if prompt.get('field_definitions') is None:
    print("field_definitions is None/null")
elif prompt.get('field_definitions') == []:
    print("field_definitions is an empty list")
elif prompt.get('field_definitions') == {}:
    print("field_definitions is an empty dict")
else:
    print(f"field_definitions type: {type(prompt['field_definitions'])}")
    print(f"field_definitions content: {prompt['field_definitions']}")

# Let's also check if there are other prompts with similar names
print(f"\n{'='*80}")
print("Checking for other Product-related prompts:")
print("="*80)

response = supabase.table('prompt_templates').select('prompt_id, name, prompt_type, field_definitions').execute()

product_related = []
for p in response.data:
    name = (p.get('name') or '').lower()
    ptype = (p.get('prompt_type') or '').lower()
    
    if 'product' in name or 'product' in ptype:
        has_fields = bool(p.get('field_definitions'))
        product_related.append((p['name'], p['prompt_type'], has_fields))

print(f"\nFound {len(product_related)} product-related prompts:")
for name, ptype, has_fields in sorted(product_related):
    fields_status = "✓ has fields" if has_fields else "✗ no fields"
    print(f"  - {name} (type: {ptype}) - {fields_status}")