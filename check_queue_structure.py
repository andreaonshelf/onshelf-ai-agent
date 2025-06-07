#!/usr/bin/env python3
"""
Check the structure of the processing_queue table
"""

import os
from supabase import create_client

def main():
    url = 'https://fxyfzjaaehgbdemjnumt.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU'
    
    supabase = create_client(url, key)
    
    # Get queue items
    response = supabase.table('processing_queue').select('*').execute()
    
    print(f"Found {len(response.data)} queue items")
    
    if response.data:
        print("\nFirst item structure:")
        for key, value in response.data[0].items():
            print(f"  {key}: {type(value).__name__} = {value}")
    
    # Get just the configs
    print("\nExtraction configs:")
    for i, item in enumerate(response.data):
        config = item.get('extraction_config')
        print(f"\nItem {i} config ({type(config).__name__}):")
        if isinstance(config, str):
            print(f"  String: {config[:200]}...")
        else:
            print(f"  Other: {config}")

if __name__ == "__main__":
    main()