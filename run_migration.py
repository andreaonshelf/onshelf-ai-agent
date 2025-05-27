#!/usr/bin/env python3
"""
Run database migration to add extraction_config column to ai_extraction_queue table.
This script can be run safely multiple times - it will only add the column if it doesn't exist.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the migration SQL file"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")
        sys.exit(1)
    
    # Read the migration SQL
    migration_file = os.path.join(os.path.dirname(__file__), 'add_extraction_config_column.sql')
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    # Get database URL from Supabase URL
    # Supabase URLs are in format: https://[project-ref].supabase.co
    # Database URLs are in format: postgresql://postgres.[project-ref]:[password]@[host]:5432/postgres
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ Error: DATABASE_URL environment variable is required for direct database access")
        print("ℹ️  Note: You can find this in your Supabase project settings under Database > Connection String")
        sys.exit(1)
    
    try:
        # Parse database URL
        parsed = urlparse(db_url)
        
        # Connect to database
        print("🔄 Connecting to database...")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading /
            user=parsed.username,
            password=parsed.password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Execute migration
        print("🔄 Running migration...")
        cursor.execute(migration_sql)
        
        # Check if column exists now
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'ai_extraction_queue' 
            AND column_name = 'extraction_config'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Success! extraction_config column exists with type: {result[1]}")
        else:
            print("⚠️  Warning: Column may not have been created. Please check manually.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 OnShelf Extraction Config Migration")
    print("=====================================")
    run_migration()
    print("\n✨ Migration completed!")