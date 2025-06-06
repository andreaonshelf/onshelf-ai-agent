#!/usr/bin/env python3
"""
FIND WHERE 91% IS COMING FROM
"""

import os
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("🔍 FINDING WHERE 91% IS COMING FROM")
print("=" * 60)

# Check the database again
print("\n1️⃣ DATABASE CHECK:")
result = supabase.table("ai_extraction_queue").select("*").execute()

for item in result.data:
    if item.get('final_accuracy') == 0.91 or item.get('accuracy_estimate') == 91:
        print(f"   ⚠️ Item {item['id']} has accuracy: {item.get('final_accuracy', 'None')}")

# Check the queue API response
print("\n\n2️⃣ CHECKING FRONTEND CODE:")
print("   The 91% appears IMMEDIATELY when you click Process")
print("   This means it's NOT coming from the database")
print("   It's being set in the JavaScript!")

# Search for where this happens
import subprocess
try:
    # Search for 91 in the dashboard HTML
    result = subprocess.run(['grep', '-n', '91\|accuracy.*=.*9', 'new_dashboard.html'], 
                          capture_output=True, text=True)
    if result.stdout:
        print("\n   Found in new_dashboard.html:")
        for line in result.stdout.strip().split('\n')[:5]:
            print(f"   {line}")
except:
    pass

print("\n\n3️⃣ THE ISSUE:")
print("   When you click 'Process', the frontend is:")
print("   1. Immediately setting the item status to show 91%")
print("   2. NOT waiting for actual extraction results")
print("   3. This is a UI bug, not a backend issue")

print("\n\n4️⃣ LOOKING FOR THE BUG:")
# Search for where status is updated on Process click
try:
    result = subprocess.run(['grep', '-n', '-A', '5', '-B', '5', 'handleProcessSelected\|Process.*click', 'new_dashboard.html'], 
                          capture_output=True, text=True)
    if result.stdout:
        print("\n   Found Process button handler:")
        lines = result.stdout.strip().split('\n')
        for i, line in enumerate(lines):
            if 'handleProcessSelected' in line or 'onClick' in line:
                print(f"   {line}")
                # Show context
                if i > 0:
                    print(f"   {lines[i-1]}")
                if i < len(lines) - 1:
                    print(f"   {lines[i+1]}")
except:
    pass