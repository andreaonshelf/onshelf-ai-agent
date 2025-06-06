#!/usr/bin/env python3
"""
TRACE WHY WE'RE SEEING 91% FAKE DATA
"""

import os
import requests
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 TRACING QUEUE DISPLAY ISSUE")
print("=" * 60)

# 1. Check what's in the database
print("\n1️⃣ DATABASE VALUES:")
result = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()

if result.data:
    item = result.data[0]
    print(f"   ID: {item['id']}")
    print(f"   Status: {item['status']}")
    print(f"   Accuracy Estimate: {item.get('accuracy_estimate', 'NULL')}")
    print(f"   Final Accuracy: {item.get('final_accuracy', 'NULL')}")
    
    # Check all columns that might contain 91
    for key, value in item.items():
        if value == 91 or value == 91.0 or value == 0.91:
            print(f"   ⚠️ FOUND 91 in column '{key}': {value}")

# 2. Check what the API returns
print("\n\n2️⃣ API RESPONSE:")
try:
    response = requests.get("http://localhost:8000/api/queue/items")
    if response.ok:
        data = response.json()
        items = data.get('items', [])
        
        # Find item with ID 9
        for item in items:
            if item['id'] == 9:
                print(f"   ID: {item['id']}")
                print(f"   Status: {item['status']}")
                print(f"   Store: {item.get('store_name', 'Unknown')}")
                print(f"   Category: {item.get('category', 'Unknown')}")
                print(f"   Final Accuracy: {item.get('final_accuracy', 'NULL')}")
                print(f"   Accuracy Estimate: {item.get('accuracy_estimate', 'NULL')}")
                
                # Check all fields for 91
                for key, value in item.items():
                    if value == 91 or value == 91.0 or value == 0.91:
                        print(f"   ⚠️ FOUND 91 in field '{key}': {value}")
                        
                # Check if there's a display field
                if 'accuracy_display' in item:
                    print(f"   Accuracy Display: {item['accuracy_display']}")
                        
except Exception as e:
    print(f"   ❌ Failed to fetch from API: {e}")

# 3. Check where 91% might be coming from
print("\n\n3️⃣ POSSIBLE SOURCES:")
print("   - Not in database (all accuracy fields are NULL)")
print("   - Not in API response (if nothing found above)")
print("   - Must be in frontend display logic!")

# 4. Check if there's any legacy data
print("\n\n4️⃣ CHECKING LEGACY FIELDS:")
result = supabase.table("ai_extraction_queue").select("*").limit(1).execute()
if result.data:
    columns = list(result.data[0].keys())
    print(f"   All columns in table: {', '.join(columns)}")
    
    # Check if any column contains "accuracy" or "score"
    accuracy_cols = [col for col in columns if 'accuracy' in col.lower() or 'score' in col.lower()]
    if accuracy_cols:
        print(f"   Accuracy-related columns: {', '.join(accuracy_cols)}")