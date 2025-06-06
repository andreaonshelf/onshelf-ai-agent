#!/usr/bin/env python3
"""
Stop the queue processor from automatically processing items
"""

import os

# Set environment variable to disable automatic processing
os.environ['PROCESSING_MODE'] = 'manual'

print("✅ Queue processor set to MANUAL mode")
print("   Items will only process when you click Process")
print("\nRestart the server for this to take effect:")
print("   1. Kill current server: pkill -f 'python main.py'")
print("   2. Start with manual mode: PROCESSING_MODE=manual python main.py")