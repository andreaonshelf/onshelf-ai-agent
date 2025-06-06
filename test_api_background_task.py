#!/usr/bin/env python3
"""
Test API background task execution
"""

import requests
import time
import sys

def test_api_process():
    """Test the API process endpoint"""
    
    # Test parameters
    item_id = 7
    api_url = "http://localhost:8000/api/queue/process"
    
    print(f"Testing API process endpoint for item {item_id}...")
    
    # Call the process endpoint
    response = requests.post(
        f"{api_url}/{item_id}",
        json={
            "system": "custom_consensus",
            "max_budget": 2.0,
            "configuration": {}
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API call successful: {result}")
        
        # Monitor the progress
        print("\nMonitoring extraction progress...")
        for i in range(30):  # Monitor for up to 30 seconds
            time.sleep(1)
            
            # Get monitoring data
            monitor_response = requests.get(f"http://localhost:8000/api/queue/monitor/{item_id}")
            if monitor_response.status_code == 200:
                data = monitor_response.json()
                status = data.get("status", "unknown")
                stage = data.get("current_stage", "unknown")
                print(f"\r[{i+1}s] Status: {status}, Stage: {stage}", end="", flush=True)
                
                if status in ["completed", "failed"]:
                    print(f"\n\nExtraction {status}!")
                    break
            else:
                print(f"\nFailed to get monitoring data: {monitor_response.status_code}")
    else:
        print(f"❌ API call failed: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_api_process()