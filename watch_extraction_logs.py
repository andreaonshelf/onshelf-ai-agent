#!/usr/bin/env python3
"""
Real-time extraction log watcher
Shows exactly what's happening when you process an item
"""

import subprocess
import sys
import os
from datetime import datetime

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def watch_logs(item_id=None):
    """Watch logs in real-time with filtering"""
    
    log_file = f"/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/logs/onshelf_ai_{datetime.now().strftime('%Y%m%d')}.log"
    
    print(f"{BLUE}=== REAL-TIME EXTRACTION LOGS ==={RESET}")
    print(f"Watching: {log_file}")
    if item_id:
        print(f"Filtering for item ID: {item_id}")
    print(f"{BLUE}{'='*50}{RESET}\n")
    
    # Build grep pattern
    patterns = []
    if item_id:
        patterns.extend([
            f"item {item_id}",
            f"item_id.*{item_id}",
            f"queue_item_id.*{item_id}"
        ])
    
    # Always include error patterns
    patterns.extend([
        "ERROR",
        "Failed",
        "failed",
        "Exception",
        "Starting extraction",
        "Processing stage",
        "Executing with model",
        "monitor"
    ])
    
    # Create grep pattern
    grep_pattern = "|".join(patterns)
    
    try:
        # Use tail -f with grep to filter
        cmd = f"tail -f {log_file} | grep -E '{grep_pattern}'"
        
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        print(f"{GREEN}Watching logs... Press Ctrl+C to stop{RESET}\n")
        
        for line in process.stdout:
            # Color code the output
            if "ERROR" in line or "Failed" in line or "Exception" in line:
                print(f"{RED}{line.strip()}{RESET}")
            elif "Starting" in line or "Processing" in line:
                print(f"{GREEN}{line.strip()}{RESET}")
            elif "WARNING" in line:
                print(f"{YELLOW}{line.strip()}{RESET}")
            else:
                print(line.strip())
                
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Stopped watching logs{RESET}")
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")

if __name__ == "__main__":
    item_id = sys.argv[1] if len(sys.argv) > 1 else None
    watch_logs(item_id)