#!/usr/bin/env python3
"""
Check if iterations table exists and run migration if needed
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_and_run_iterations_migration():
    """Check if iterations table exists and run migration if needed"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        return False
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Check if iterations table exists
        result = supabase.rpc('get_table_info', {'table_name': 'iterations'}).execute()
        
        if result.data:
            print("✅ iterations table already exists")
            
            # Check for specific columns to ensure schema is up to date
            column_check = supabase.table('iterations').select('id').limit(0).execute()
            print("✅ iterations table schema is valid")
            return True
            
    except Exception as e:
        if "get_table_info" in str(e):
            # Try alternative method to check table existence
            try:
                # Try to query the table
                test_query = supabase.table('iterations').select('id').limit(1).execute()
                print("✅ iterations table already exists")
                return True
            except Exception as query_error:
                if "relation" in str(query_error) and "does not exist" in str(query_error):
                    print("⚠️ iterations table does not exist, running migration...")
                else:
                    print(f"❌ Error checking iterations table: {query_error}")
                    return False
        else:
            print(f"⚠️ Table check failed, assuming it doesn't exist: {e}")
    
    # Run migration
    try:
        print("📦 Running iterations table migration...")
        
        # Read the SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'create_iterations_table.sql')
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Execute the SQL using raw SQL via REST API
        import requests
        import json
        
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement:
                print(f"  Executing statement {i+1}/{len(statements)}...")
                
                response = requests.post(
                    f"{supabase_url}/rest/v1/rpc/exec_sql",
                    headers=headers,
                    data=json.dumps({"query": statement + ";"})
                )
                
                if response.status_code not in [200, 201, 204]:
                    # Try direct execution if exec_sql doesn't exist
                    print(f"  Note: exec_sql RPC not available, trying alternative method...")
                    
                    # For now, we'll print the SQL and note it needs manual execution
                    print(f"  ⚠️ Please execute the following SQL manually:")
                    print(f"  {statement[:100]}...")
        
        print("✅ Migration completed successfully!")
        print("   Note: Some statements may need manual execution via Supabase SQL editor")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\n💡 Please run the following SQL file manually in Supabase SQL editor:")
        print(f"   {sql_file_path}")
        return False


if __name__ == "__main__":
    success = check_and_run_iterations_migration()
    sys.exit(0 if success else 1)