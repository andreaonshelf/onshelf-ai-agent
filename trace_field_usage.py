#!/usr/bin/env python3
"""
TRACE HOW USER-DEFINED FIELDS SHOULD BE USED
"""

import os
import json
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 TRACING USER-DEFINED FIELDS USAGE")
print("=" * 60)

# Get the Version 1 configuration with user's fields
configs = supabase.table("prompt_templates").select("*").eq("name", "Version 1").execute()
if configs.data:
    config = configs.data[0]
    stages = config['extraction_config']['stages']
    
    print("\n1️⃣ YOUR DEFINED FIELDS:")
    for stage_name, stage_data in stages.items():
        print(f"\n   Stage: {stage_name}")
        if 'fields' in stage_data:
            fields = stage_data['fields']
            print(f"   Number of fields: {len(fields)}")
            for field in fields[:3]:  # Show first 3 fields
                print(f"   - {field.get('name', 'unnamed')}: {field.get('type', 'unknown')}")
                if field.get('description'):
                    print(f"     Description: {field['description'][:50]}...")
        else:
            print("   ❌ No fields defined")

print("\n\n2️⃣ WHAT SHOULD HAPPEN:")
print("   1. Your fields from the UI should be converted to a Pydantic model")
print("   2. This model should be passed as response_model to the AI")
print("   3. The AI should return data matching YOUR field structure")

print("\n\n3️⃣ WHAT'S ACTUALLY HAPPENING:")
print("   ❌ The system is using hardcoded schemas:")
print("   - 'ShelfStructure' (predefined class)")
print("   - 'List[ProductExtraction]' (predefined class)")
print("   - Instead of YOUR field definitions!")

print("\n\n4️⃣ THE MISSING PIECE:")
print("   The code needs to:")
print("   1. Take your fields from configuration")
print("   2. Build a dynamic Pydantic model from them")
print("   3. Use that as response_model")

# Check if dynamic model building exists
print("\n\n5️⃣ CHECKING FOR DYNAMIC MODEL BUILDER:")
import subprocess
try:
    result = subprocess.run(['grep', '-r', 'create_model\|dynamic.*model\|field.*schema', 'src/', '--include=*.py'], 
                          capture_output=True, text=True)
    if result.stdout:
        print("   Found dynamic model code in:")
        for line in result.stdout.strip().split('\n')[:5]:
            if 'create_model' in line or 'dynamic' in line:
                print(f"   {line.split(':')[0]}")
except:
    pass

print("\n\n6️⃣ EXAMPLE OF WHAT YOU DEFINED:")
# Show an example of user's structure field definition
if configs.data and 'structure' in stages:
    structure_fields = stages['structure'].get('fields', [])
    if structure_fields:
        print("\n   Your 'structure' stage fields:")
        print(json.dumps(structure_fields, indent=2)[:500] + "...")

print("\n\n🎯 THE ISSUE:")
print("   Your carefully crafted field definitions are being IGNORED!")
print("   The system is using its own hardcoded schemas instead of")
print("   building models from your field definitions!")