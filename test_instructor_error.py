#!/usr/bin/env python3
"""
Test instructor error scenarios
"""

import os
from dotenv import load_dotenv
import instructor
import openai

# Load environment variables
load_dotenv()

# Initialize clients
raw_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
instructor_client = instructor.from_openai(raw_client)

# Test different scenarios
print("🔍 TESTING INSTRUCTOR ERROR SCENARIOS")
print("=" * 60)

# Test 1: Calling instructor client without response_model
print("\n📋 Test 1: Instructor client without response_model")
try:
    response = instructor_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=100
    )
    print("   ✅ Success (unexpected!)")
except Exception as e:
    print(f"   ❌ Error: {e}")
    if "response_model" in str(e):
        print("   ⚠️  This is the response_model error!")

# Test 2: Calling with response_model as string
print("\n📋 Test 2: Instructor client with string response_model")
try:
    response = instructor_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        response_model="Dict[str, Any]",  # String instead of actual model
        max_tokens=100
    )
    print("   ✅ Success (unexpected!)")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")

# Test 3: Check if we can detect instructor vs raw client
print("\n📋 Test 3: Client type detection")
print(f"   Raw client type: {type(raw_client)}")
print(f"   Instructor client type: {type(instructor_client)}")
print(f"   Has 'chat' attribute: {hasattr(instructor_client, 'chat')}")
print(f"   Chat type: {type(instructor_client.chat) if hasattr(instructor_client, 'chat') else 'N/A'}")

# Test 4: See what happens when we accidentally use instructor syntax on raw client
print("\n📋 Test 4: Using instructor syntax on raw client")
try:
    # This mimics what might happen if client initialization fails
    response = raw_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        response_model=dict,  # This parameter doesn't exist for raw client
        max_tokens=100
    )
    print("   ✅ Success (unexpected!)")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print(f"   Error type: {type(e).__name__}")
    if "response_model" in str(e):
        print("   ⚠️  This could be our issue!")