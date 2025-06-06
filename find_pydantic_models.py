#!/usr/bin/env python3
"""
FIND WHERE THE PYDANTIC MODELS ARE ACTUALLY STORED
"""

import os
import json
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 FINDING THE ACTUAL PYDANTIC MODELS")
print("=" * 60)

# Get the Version 1 configuration
print("\n1️⃣ CHECKING VERSION 1 CONFIGURATION:")
configs = supabase.table("prompt_templates").select("*").eq("name", "Version 1").execute()

if configs.data:
    config = configs.data[0]
    
    # Check extraction_config
    extraction_config = config.get('extraction_config', {})
    stages = extraction_config.get('stages', {})
    
    # Look at structure stage specifically
    if 'structure' in stages:
        structure_stage = stages['structure']
        print("\n   Structure Stage Config:")
        
        # Check prompt_text
        prompt_text = structure_stage.get('prompt_text', '')
        print(f"\n   Prompt Text Length: {len(prompt_text)} chars")
        
        # Look for Pydantic syntax in the prompt
        if 'from pydantic' in prompt_text or 'BaseModel' in prompt_text:
            print("   ✅ Found Pydantic imports in prompt!")
            # Find the class definition
            import re
            class_matches = re.findall(r'class\s+\w+.*?(?=class|\Z)', prompt_text, re.DOTALL)
            for match in class_matches[:2]:  # Show first 2 classes
                print(f"\n   Found class definition:")
                print(f"   {match[:300]}...")
        
        # Check if models are in a separate field
        if 'model' in structure_stage:
            print(f"\n   Has 'model' field: {structure_stage['model'][:200]}...")
        
        if 'schema' in structure_stage:
            print(f"\n   Has 'schema' field: {structure_stage['schema'][:200]}...")
            
        # Check fields structure
        fields = structure_stage.get('fields', [])
        if fields:
            print(f"\n   Fields structure (first field):")
            print(json.dumps(fields[0], indent=2))

# Check all columns in the extraction config
print("\n\n2️⃣ ALL KEYS IN STAGE CONFIG:")
if 'structure' in stages:
    for key in stages['structure'].keys():
        print(f"   - {key}")

# Look for Pydantic models in the actual prompt text more carefully
print("\n\n3️⃣ SEARCHING PROMPT TEXT MORE CAREFULLY:")
if 'structure' in stages:
    prompt_text = stages['structure'].get('prompt_text', '')
    
    # Split into sections
    sections = prompt_text.split('\n\n')
    
    # Look for code blocks
    for i, section in enumerate(sections):
        if '```' in section:
            print(f"\n   Found code block in section {i}:")
            print(section[:300] + "...")
            
    # Look for class-like structures
    if 'class' in prompt_text.lower():
        print("\n   Found 'class' keyword in prompt")
        # Extract context around 'class'
        class_index = prompt_text.lower().find('class')
        context = prompt_text[max(0, class_index-50):class_index+200]
        print(f"   Context: ...{context}...")

print("\n\n4️⃣ CHECKING IF MODELS ARE IN INSTRUCTIONS:")
# The Pydantic models might be embedded in the instructions to the AI
if 'structure' in stages:
    prompt_text = stages['structure'].get('prompt_text', '')
    
    # Common patterns for model definitions in prompts
    patterns = [
        r'Expected output format:.*?```(.*?)```',
        r'Return the following structure:.*?```(.*?)```',
        r'Output schema:.*?```(.*?)```',
        r'JSON structure:.*?```(.*?)```'
    ]
    
    for pattern in patterns:
        import re
        matches = re.findall(pattern, prompt_text, re.DOTALL | re.IGNORECASE)
        if matches:
            print(f"\n   Found model definition with pattern '{pattern.split(':')[0]}':")
            print(matches[0][:300] + "...")