#!/usr/bin/env python3
"""Run database migration for model usage tracking tables"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the model usage tracking migration"""
    
    # Initialize Supabase client
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    print("Running model usage tracking migration...")
    
    try:
        # Read the SQL files
        with open('add_model_config_column.sql', 'r') as f:
            add_column_sql = f.read()
            
        with open('create_model_usage_tables.sql', 'r') as f:
            create_tables_sql = f.read()
        
        # Execute the migrations
        # Note: Supabase doesn't directly support executing raw SQL through the Python client
        # You'll need to run these through the Supabase SQL editor or use psycopg2
        
        print("\nPlease execute the following SQL scripts in your Supabase SQL editor:")
        print("\n1. First, add the model_config column:")
        print("-" * 60)
        print(add_column_sql)
        print("\n2. Then, create the model usage tracking tables:")
        print("-" * 60)
        print(create_tables_sql[:500] + "...\n[truncated for display]")
        
        print("\nAlternatively, you can run these commands using psql:")
        print(f"psql {os.getenv('DATABASE_URL')} < add_model_config_column.sql")
        print(f"psql {os.getenv('DATABASE_URL')} < create_model_usage_tables.sql")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)