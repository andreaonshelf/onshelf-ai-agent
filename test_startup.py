#!/usr/bin/env python3
"""Test if the server can start properly"""

import subprocess
import time
import requests
import sys

print("Starting server...")
# Start the server in the background
process = subprocess.Popen(
    [sys.executable, "main.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give it some time to start
print("Waiting for server to start...")
time.sleep(5)

# Check if process is still running
if process.poll() is not None:
    stdout, stderr = process.communicate()
    print("Server failed to start!")
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    sys.exit(1)

# Try to access the health endpoint
try:
    print("Testing health endpoint...")
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        print("✅ Server is running successfully!")
        print("Response:", response.json())
    else:
        print(f"❌ Server returned status code: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to connect to server: {e}")
    
# Kill the process
process.terminate()
process.wait()
print("Server stopped.")