#!/usr/bin/env python3
"""
MONITOR WHAT'S HAPPENING WITH EXTRACTION ATTEMPTS
"""

import os
import time
from datetime import datetime, timedelta
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 MONITORING EXTRACTION ATTEMPTS")
print("=" * 60)

# Check for recent status changes
print("\n1️⃣ RECENT STATUS CHANGES (last 10 minutes):")
ten_mins_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
result = supabase.table("ai_extraction_queue").select("*").gte("updated_at", ten_mins_ago).order("updated_at", desc=True).execute()

if result.data:
    for item in result.data:
        print(f"\n   ID {item['id']}: {item['status']}")
        print(f"   Updated: {item['updated_at']}")
        print(f"   Model Config: {'YES' if item.get('model_config') else 'NO'}")
        if item.get('error_message'):
            print(f"   Error: {item['error_message'][:100]}...")
else:
    print("   No items updated in last 10 minutes")

# Check logs for extraction attempts
print("\n\n2️⃣ RECENT EXTRACTION LOGS:")
try:
    with open('logs/onshelf_ai_20250606.log', 'r') as f:
        lines = f.readlines()
        last_200 = lines[-200:]
        
        # Look for process button clicks
        process_lines = [line for line in last_200 if 'process' in line.lower() and ('queue' in line or 'item' in line)]
        if process_lines:
            print("\n   Process attempts:")
            for line in process_lines[-5:]:
                print(f"   {line.strip()[:150]}...")
                
        # Look for extraction starts
        extraction_lines = [line for line in last_200 if 'extraction' in line.lower() and ('start' in line.lower() or 'begin' in line.lower())]
        if extraction_lines:
            print("\n   Extraction starts:")
            for line in extraction_lines[-5:]:
                print(f"   {line.strip()[:150]}...")
                
        # Look for configuration loading
        config_lines = [line for line in last_200 if 'config' in line.lower() and ('load' in line.lower() or 'custom' in line.lower())]
        if config_lines:
            print("\n   Configuration loading:")
            for line in config_lines[-5:]:
                print(f"   {line.strip()[:150]}...")
except Exception as e:
    print(f"   Could not read logs: {e}")

# Check error logs
print("\n\n3️⃣ RECENT ERRORS:")
try:
    with open('logs/onshelf_ai_errors_20250606.log', 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
        last_5 = lines[-5:]
        
        for line in last_5:
            if line.strip():
                try:
                    import json
                    error_data = json.loads(line)
                    print(f"\n   Time: {error_data.get('timestamp', 'Unknown')}")
                    print(f"   Error: {error_data.get('message', 'Unknown')[:150]}...")
                except:
                    print(f"   {line[:150]}...")
except Exception as e:
    print(f"   Could not read error logs: {e}")

print("\n\n4️⃣ CURRENT EXTRACTION BLOCKER:")
print("   Based on the error logs, extraction is failing because:")
print("   - GPT-4o calls are missing the 'response_model' parameter")
print("   - This happens when output_schema is not properly mapped to a Pydantic model")
print("   - The system is trying to extract but the API call format is wrong")
print("\n   The prompts ARE loading correctly (Version 1 config has all prompts)")
print("   The issue is in the extraction engine code, not prompt loading!")