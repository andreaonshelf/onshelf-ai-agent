#!/usr/bin/env python3
"""
CHECK WHAT'S ACTUALLY STORED IN THE DATABASE
"""

import os
import json
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 CHECKING ACTUAL DATABASE CONTENT")
print("=" * 60)

# Check prompt_templates for the actual prompt text
print("\n1️⃣ CHECKING PROMPT_TEMPLATES TABLE:")
prompts = supabase.table("prompt_templates").select("*").eq("stage_type", "structure").limit(5).execute()

for prompt in prompts.data:
    print(f"\n   Prompt: {prompt['name']}")
    print(f"   Stage: {prompt.get('stage_type', 'unknown')}")
    
    # Check if there are Pydantic models in the prompt text
    prompt_text = prompt.get('prompt_text', '')
    if 'class ' in prompt_text and 'BaseModel' in prompt_text:
        print("   ✅ Contains Pydantic class definition!")
        # Extract the class definition
        lines = prompt_text.split('\n')
        in_class = False
        class_lines = []
        for line in lines:
            if 'class ' in line and '(BaseModel)' in line:
                in_class = True
            if in_class:
                class_lines.append(line)
                if line.strip() == '' and len(class_lines) > 5:
                    break
        
        if class_lines:
            print("   Pydantic model found:")
            for line in class_lines[:20]:  # Show first 20 lines
                print(f"      {line}")
    else:
        print("   ❌ No Pydantic class found in prompt text")
        print(f"   First 200 chars: {prompt_text[:200]}...")

# Check if there's a separate field for the model
print("\n\n2️⃣ CHECKING FOR MODEL FIELDS:")
if prompts.data:
    first_prompt = prompts.data[0]
    print(f"   All columns in prompt_templates:")
    for key in first_prompt.keys():
        if 'model' in key.lower() or 'schema' in key.lower() or 'field' in key.lower():
            print(f"   - {key}: {type(first_prompt[key])}")
            if isinstance(first_prompt[key], (dict, list)):
                print(f"     Content: {json.dumps(first_prompt[key])[:200]}...")

# Check field_definitions table if it exists
print("\n\n3️⃣ CHECKING FIELD_DEFINITIONS TABLE:")
try:
    field_defs = supabase.table("field_definitions").select("*").limit(5).execute()
    for field_def in field_defs.data:
        print(f"\n   Field: {field_def.get('field_name', 'unnamed')}")
        print(f"   Stage: {field_def.get('stage', 'unknown')}")
        if field_def.get('pydantic_model'):
            print(f"   ✅ Has pydantic_model field!")
            print(f"   Model: {field_def['pydantic_model'][:200]}...")
except Exception as e:
    print(f"   ❌ Could not access field_definitions: {e}")

print("\n\n4️⃣ LOOKING FOR PYDANTIC MODELS IN PROMPTS:")
# Search all prompts for Pydantic class definitions
all_prompts = supabase.table("prompt_templates").select("name, stage_type, prompt_text").execute()
pydantic_prompts = []

for prompt in all_prompts.data:
    if 'class ' in prompt.get('prompt_text', '') and 'BaseModel' in prompt.get('prompt_text', ''):
        pydantic_prompts.append(prompt['name'])

if pydantic_prompts:
    print(f"   Found {len(pydantic_prompts)} prompts with Pydantic models:")
    for name in pydantic_prompts[:10]:
        print(f"   - {name}")
else:
    print("   No Pydantic models found in prompt_text fields")