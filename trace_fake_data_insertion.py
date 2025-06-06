#!/usr/bin/env python3
"""
TRACE HOW THE FAKE 91% GOT INTO THE DATABASE
"""

import os
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 TRACING FAKE DATA INSERTION")
print("=" * 60)

# 1. Check all items with suspiciously round accuracy values
print("\n1️⃣ ALL SUSPICIOUS ACCURACY VALUES:")
result = supabase.table("ai_extraction_queue").select("*").not_.is_("final_accuracy", None).execute()

suspicious_items = []
for item in result.data:
    acc = item.get('final_accuracy')
    if acc:
        # Check for suspiciously round numbers (like 0.91, 0.80, 0.95)
        if acc in [0.91, 0.80, 0.85, 0.90, 0.95, 0.75, 0.70]:
            suspicious_items.append(item)
            print(f"\n   ID {item['id']}: {acc} ({acc*100}%)")
            print(f"   Status: {item['status']}")
            print(f"   Created: {item['created_at']}")
            print(f"   Completed: {item.get('completed_at', 'Never')}")

# 2. Check if mock data initialization is still enabled
print("\n\n2️⃣ CHECKING FOR MOCK DATA CODE:")
# Search for mock data initialization in main.py
import subprocess
try:
    result = subprocess.run(['grep', '-n', 'initialize_mock_data\|mock.*accuracy\|0.91\|91', 'main.py'], 
                          capture_output=True, text=True)
    if result.stdout:
        print("   Found in main.py:")
        print(result.stdout)
    else:
        print("   No mock data code found in main.py")
except:
    pass

# 3. Check when this item was last updated
print("\n\n3️⃣ ITEM #9 TIMELINE:")
result = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()
if result.data:
    item = result.data[0]
    print(f"   Created: {item['created_at']}")
    print(f"   Updated: {item.get('updated_at', 'Never')}")
    print(f"   Completed: {item.get('completed_at', 'Never')}")
    print(f"   Has extraction result: {'YES' if item.get('extraction_result') else 'NO'}")
    print(f"   Has planogram result: {'YES' if item.get('planogram_result') else 'NO'}")

# 4. Clean up the fake data
print("\n\n4️⃣ CLEANUP RECOMMENDATION:")
print("   To remove all fake accuracy data, run:")
print("   UPDATE ai_extraction_queue SET final_accuracy = NULL WHERE final_accuracy IN (0.91, 0.80, 0.85, 0.90, 0.95, 0.75, 0.70);")
print("\n   Or just for item #9:")
print("   UPDATE ai_extraction_queue SET final_accuracy = NULL WHERE id = 9;")

# 5. Find when extraction is actually happening
print("\n\n5️⃣ CHECKING IF EXTRACTION IS HAPPENING:")
# Check logs for actual extraction activity
try:
    with open('logs/onshelf_ai_20250606.log', 'r') as f:
        lines = f.readlines()
        last_100 = lines[-100:]
        
        extraction_lines = [line for line in last_100 if 'extraction' in line.lower() and 'started' in line.lower()]
        if extraction_lines:
            print("   Recent extraction activity:")
            for line in extraction_lines[-5:]:
                print(f"   {line.strip()}")
        else:
            print("   No recent extraction starts found in logs")
except:
    print("   Could not read logs")