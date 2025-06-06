#!/usr/bin/env python3
"""Check the current schema of ai_extraction_queue table."""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("📋 Checking ai_extraction_queue table schema...")
        
        # Get a sample row to see all columns
        result = supabase.table('ai_extraction_queue').select('*').limit(1).execute()
        
        if result.data and len(result.data) > 0:
            print("\n✅ Current columns in ai_extraction_queue:")
            for column in result.data[0].keys():
                value = result.data[0][column]
                value_type = type(value).__name__
                print(f"  - {column}: {value_type}")
        else:
            print("\n⚠️  Table is empty, fetching schema differently...")
            # Try to get column info using a dummy insert that we'll rollback
            try:
                # This will fail but give us column info in the error
                supabase.table('ai_extraction_queue').select('*').limit(0).execute()
                print("✅ Table exists but is empty")
            except Exception as e:
                print(f"Schema check error: {e}")
        
        # Check specifically for model_config column
        print("\n🔍 Checking for model_config column...")
        try:
            result = supabase.table('ai_extraction_queue').select('model_config').limit(1).execute()
            print("✅ model_config column EXISTS")
        except Exception as e:
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                print("❌ model_config column DOES NOT EXIST")
                print("\n⚠️  You need to run the migration SQL to add this column")
            else:
                print(f"⚠️  Error checking model_config: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()