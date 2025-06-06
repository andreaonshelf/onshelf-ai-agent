#!/usr/bin/env python3
"""
CHECK THE CORRECT SYNTAX FOR INSTRUCTOR WITH GPT-4O
"""

print("🔍 CHECKING INSTRUCTOR SYNTAX")
print("=" * 60)

print("\n📖 INSTRUCTOR DOCUMENTATION:")
print("   With instructor, the correct syntax is:")
print("   ")
print("   # OLD WAY (without instructor):")
print("   response = openai.chat.completions.create(")
print("       model='gpt-4o',")
print("       messages=messages")
print("   )")
print("   ")
print("   # NEW WAY (with instructor):")
print("   response = instructor_client.chat.completions.create(")
print("       model='gpt-4o',")
print("       messages=messages,")
print("       response_model=MyPydanticModel  # <-- This is the key parameter")
print("   )")

print("\n🐛 THE BUG:")
print("   The error 'create() missing 1 required positional argument: response_model'")
print("   means instructor REQUIRES response_model to be passed")
print("   ")
print("   But wait... the code IS passing response_model=ShelfStructure")
print("   So why is it failing?")

print("\n💡 POSSIBLE ISSUES:")
print("   1. The instructor version might be outdated")
print("   2. The openai client might not be properly patched")
print("   3. There might be a different code path being executed")

print("\n🔍 CHECKING ERROR PATTERN:")
import subprocess
try:
    # Check which items are failing
    result = subprocess.run(['grep', '-A', '2', 'response_model', 'logs/onshelf_ai_errors_20250606.log'], 
                          capture_output=True, text=True)
    if result.stdout:
        print("   Recent errors mentioning response_model:")
        lines = result.stdout.strip().split('\n')
        for i in range(0, len(lines), 3):
            if 'response_model' in lines[i]:
                print(f"   {lines[i][:150]}...")
except:
    pass

print("\n🎯 SOLUTION:")
print("   The issue might be that when output_schema is not one of the")
print("   predefined cases, it falls through to a generic handler")
print("   that doesn't pass response_model correctly.")