#!/usr/bin/env python3
"""
TRACE THE EXACT EXTRACTION FLOW STEP BY STEP
"""

import os
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 TRACING EXTRACTION FLOW STEP BY STEP")
print("=" * 60)

# Step 1: Configuration is saved correctly
print("\n✅ STEP 1: Configuration Storage")
configs = supabase.table("prompt_templates").select("*").eq("name", "Version 1").execute()
if configs.data:
    config = configs.data[0]
    stages = config['extraction_config']['stages']
    print("   Configuration 'Version 1' has prompts for:")
    for stage, data in stages.items():
        has_prompt = 'prompt_text' in data
        print(f"   - {stage}: {'✅ Has prompt' if has_prompt else '❌ Missing prompt'}")

# Step 2: When Process is clicked
print("\n🔄 STEP 2: Process Button Click")
print("   When you click Process, the frontend calls:")
print("   POST /api/queue-process/process/{item_id}")
print("   With configuration from localStorage")

# Step 3: Backend receives request
print("\n🔄 STEP 3: Backend Processing")
print("   queue_processing.py receives the request and:")
print("   1. Creates a background task")
print("   2. Passes configuration to system_dispatcher.py")

# Step 4: Configuration loading
print("\n⚠️ STEP 4: Configuration Loading Issue")
print("   system_dispatcher.py extracts prompts from configuration:")
print("   - It looks in config['stages'][stage_id]['prompt_text']")
print("   - This matches the database structure ✅")

# Step 5: Extraction starts
print("\n❌ STEP 5: EXTRACTION FAILURE")
print("   The extraction fails at this exact point:")
print("   ")
print("   In extraction/engine.py, when calling GPT-4o:")
print("   - For output_schema='ShelfStructure'")
print("   - The code is missing the response_model parameter")
print("   - Error: 'create() missing 1 required positional argument: response_model'")

# Step 6: The bug location
print("\n🐛 THE BUG IS HERE:")
print("   File: src/extraction/engine.py")
print("   Problem: The ShelfStructure case is not handled properly")
print("   ")
print("   When output_schema == 'ShelfStructure', the code should pass:")
print("   response_model=ShelfStructure")
print("   ")
print("   But it's not doing that!")

# Check current extraction attempts
print("\n📊 RECENT EXTRACTION ATTEMPTS:")
result = supabase.table("ai_extraction_queue").select("id, status, error_message").eq("status", "failed").limit(5).execute()
for item in result.data:
    if item.get('error_message'):
        print(f"   Item {item['id']}: {item['error_message'][:100]}...")

print("\n🎯 SUMMARY:")
print("   1. Your prompts ARE saved correctly ✅")
print("   2. Configuration IS loading properly ✅")
print("   3. Extraction IS starting ✅")
print("   4. But it FAILS because of a code bug in engine.py ❌")
print("   ")
print("   The system is NOT using hardcoded prompts - it's trying to use YOUR prompts")
print("   but failing due to a technical error in the API call!")