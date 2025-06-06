#!/usr/bin/env python3
"""Simple test to save a prompt"""

import os
import requests
from datetime import datetime

# Test the API endpoint
API_BASE = "http://localhost:8000/api"

def test_save_prompt():
    """Test saving a prompt via API"""
    print("=== Testing Save Prompt API ===\n")
    
    test_prompt = {
        "name": f"Test API Prompt {datetime.now().strftime('%H:%M:%S')}",
        "stage": "products",
        "content": "Extract all products from this retail shelf image.",
        "fields": [
            {"name": "brand", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True}
        ],
        "version": "1.0",
        "tags": ["test", "api"]
    }
    
    print(f"Sending POST to {API_BASE}/prompts")
    print(f"Data: {test_prompt}")
    
    try:
        response = requests.post(f"{API_BASE}/prompts", json=test_prompt)
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.ok:
            data = response.json()
            prompt_id = data.get('prompt_id')
            print(f"\n✓ Success! Prompt ID: {prompt_id}")
            
            # Now try to fetch prompts
            print("\n=== Testing Fetch Prompts ===")
            fetch_response = requests.get(f"{API_BASE}/prompts/by-stage/products")
            print(f"Status: {fetch_response.status_code}")
            
            if fetch_response.ok:
                prompts = fetch_response.json().get('prompts', [])
                print(f"Found {len(prompts)} prompts")
                
                # Look for our saved prompt
                saved_prompt = next((p for p in prompts if p['id'] == prompt_id), None)
                if saved_prompt:
                    print(f"✓ Found our saved prompt: {saved_prompt['name']}")
                else:
                    print("✗ Could not find our saved prompt in the list")
                    print("\nAll prompts:")
                    for p in prompts:
                        print(f"  - {p['name']} (ID: {p['id']})")
            else:
                print(f"Error fetching: {fetch_response.text}")
        else:
            print(f"\n✗ Error saving prompt")
            
    except Exception as e:
        print(f"\nException: {e}")
        print("\nMake sure the server is running: python main.py")

if __name__ == "__main__":
    test_save_prompt()