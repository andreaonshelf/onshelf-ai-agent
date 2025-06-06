import requests
import json

# Test the prompt management API endpoints
base_url = "http://localhost:8000/api/prompts"

stages = ["structure", "products", "details", "validation", "comparison", "orchestrator"]

print("=== TESTING PROMPT API ENDPOINTS ===\n")

for stage in stages:
    print(f"Testing stage: {stage}")
    try:
        response = requests.get(f"{base_url}/by-stage/{stage}")
        if response.status_code == 200:
            data = response.json()
            prompts = data.get('prompts', [])
            print(f"  ✓ Success - Found {len(prompts)} prompts")
            for prompt in prompts:
                print(f"    - {prompt['name']} (type: {prompt['prompt_type']}, stage: {prompt.get('stage_type')})")
        else:
            print(f"  ✗ Failed - Status code: {response.status_code}")
            print(f"    Response: {response.text}")
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
    print()

# Test active prompts endpoint
print("Testing active prompts endpoint:")
try:
    response = requests.get(f"{base_url}/active")
    if response.status_code == 200:
        data = response.json()
        print(f"  ✓ Success - Active prompts:")
        for key, prompt in data.items():
            print(f"    - {key}: {prompt.get('template_id')}")
    else:
        print(f"  ✗ Failed - Status code: {response.status_code}")
except Exception as e:
    print(f"  ✗ Error: {str(e)}")

print("\n✅ API test complete")