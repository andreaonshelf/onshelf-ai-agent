#!/usr/bin/env python3
"""Check actual database schemas and field names."""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

print("=" * 80)
print("CHECKING ACTUAL DATABASE SCHEMAS")
print("=" * 80)

# Check media_files columns
print("\n1. MEDIA_FILES TABLE COLUMNS:")
print("-" * 40)
try:
    # Get one row to see all columns
    result = supabase.table('media_files').select('*').limit(1).execute()
    if result.data:
        columns = list(result.data[0].keys())
        print(f"Columns: {sorted(columns)}")
        
        # Check for image-related columns
        image_cols = [col for col in columns if 'image' in col.lower() or 'path' in col.lower() or 'file' in col.lower()]
        print(f"Image-related columns: {image_cols}")
        
except Exception as e:
    print(f"Error: {e}")

# Check processing_queue columns
print("\n\n2. PROCESSING_QUEUE TABLE COLUMNS:")
print("-" * 40)
try:
    result = supabase.table('processing_queue').select('*').limit(1).execute()
    if result.data:
        columns = list(result.data[0].keys())
        print(f"Columns: {sorted(columns)}")
        
        # Check for config-related columns
        config_cols = [col for col in columns if 'config' in col.lower() or 'extraction' in col.lower()]
        print(f"Config-related columns: {config_cols}")
        
        # Show a sample row
        print("\nSample row:")
        for key, value in result.data[0].items():
            if isinstance(value, (dict, list)):
                print(f"  {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"  {key}: {value}")
        
except Exception as e:
    print(f"Error: {e}")

# Check if there's a configuration column in processing_queue
print("\n\n3. PROCESSING_QUEUE CONFIGURATION DATA:")
print("-" * 40)
try:
    # Try different potential column names
    config_columns = ['configuration', 'config', 'extraction_config', 'settings']
    
    for col_name in config_columns:
        try:
            result = supabase.table('processing_queue').select(col_name).not_.is_(col_name, 'null').limit(1).execute()
            if result.data and result.data[0].get(col_name):
                print(f"\nFound configuration in column '{col_name}':")
                config = result.data[0][col_name]
                if isinstance(config, str):
                    config = json.loads(config)
                print(json.dumps(config, indent=2))
                break
        except:
            continue
            
except Exception as e:
    print(f"Error: {e}")

# Check how UI sends data
print("\n\n4. CHECK UI API ENDPOINTS:")
print("-" * 40)
print("Looking for queue processing endpoints...")

# Check queue_processing.py to see how UI sends config
import_path = "/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src/api/queue_processing.py"
if os.path.exists(import_path):
    with open(import_path, 'r') as f:
        content = f.read()
        
        # Find process_queue_item function
        if 'process_queue_item' in content:
            start = content.find('async def process_queue_item')
            if start > -1:
                # Get the function and some context
                end = content.find('\n\n@', start)
                if end == -1:
                    end = start + 1000
                function_snippet = content[start:end]
                
                # Look for how configuration is handled
                if 'configuration' in function_snippet:
                    print("Found process_queue_item function - checking configuration handling...")
                    
                    # Find configuration usage
                    config_lines = [line for line in function_snippet.split('\n') if 'configuration' in line.lower()]
                    for line in config_lines[:5]:  # Show first 5 relevant lines
                        print(f"  {line.strip()}")