#!/usr/bin/env python3
"""
Run database migration to create extraction_runs table.
This table tracks the state and progress of extraction pipeline runs.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def run_migration():
    """Execute the extraction_runs table creation"""
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ Error: DATABASE_URL environment variable is required")
        print("ℹ️  Note: You can find this in your Supabase project settings under Database > Connection String")
        sys.exit(1)
    
    # Read the migration SQL
    migration_file = os.path.join(os.path.dirname(__file__), 'create_extraction_runs_table.sql')
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        sys.exit(1)
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
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
        print("🔄 Creating extraction_runs table...")
        cursor.execute(migration_sql)
        
        # Verify table creation
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'extraction_runs'
        """)
        
        if cursor.fetchone():
            print("✅ Success! extraction_runs table created")
            
            # Show table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'extraction_runs'
                ORDER BY ordinal_position
            """)
            
            print("\n📋 Table structure:")
            print("-" * 50)
            for col in cursor.fetchall():
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"  {col[0]:<20} {col[1]:<20} {nullable}")
            
            # Show indexes
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'extraction_runs'
            """)
            
            indexes = cursor.fetchall()
            if indexes:
                print("\n🔍 Indexes:")
                for idx in indexes:
                    print(f"  - {idx[0]}")
            
        else:
            print("⚠️  Warning: Table creation may have failed. Please check manually.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 OnShelf Extraction Runs Table Migration")
    print("==========================================")
    run_migration()
    print("\n✨ Migration completed!")