#!/usr/bin/env python3
"""
Check if extraction_config column exists in ai_extraction_queue table
and show current table structure.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

def check_column():
    """Check if extraction_config column exists"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY environment variables are required")
        sys.exit(1)
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔄 Checking ai_extraction_queue table structure...")
        
        # Try to query with extraction_config column
        try:
            result = supabase.table("ai_extraction_queue").select("id, extraction_config").limit(1).execute()
            print("✅ extraction_config column EXISTS!")
            
            if result.data and result.data[0].get('extraction_config'):
                print(f"\n📋 Sample extraction_config data:")
                print(json.dumps(result.data[0]['extraction_config'], indent=2))
        except Exception as e:
            if "extraction_config" in str(e):
                print("❌ extraction_config column DOES NOT EXIST")
                print(f"   Error: {e}")
            else:
                raise e
        
        # Try to get a sample row to see what columns exist
        print("\n📊 Checking available columns...")
        result = supabase.table("ai_extraction_queue").select("*").limit(1).execute()
        
        if result.data:
            columns = list(result.data[0].keys())
            print(f"Available columns: {', '.join(sorted(columns))}")
            
            # Check for related columns
            config_columns = [col for col in columns if 'config' in col.lower() or 'prompt' in col.lower()]
            if config_columns:
                print(f"\n🔍 Found related columns: {', '.join(config_columns)}")
                for col in config_columns:
                    value = result.data[0].get(col)
                    if value:
                        print(f"\n{col}:")
                        if isinstance(value, dict):
                            print(json.dumps(value, indent=2))
                        else:
                            print(value)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔍 OnShelf Extraction Config Column Check")
    print("=========================================")
    check_column()