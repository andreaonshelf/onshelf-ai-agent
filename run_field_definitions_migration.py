#!/usr/bin/env python3
"""Run field definitions migration script."""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_migration():
    """Run the field definitions table migration."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try to construct from Supabase URL
        supabase_url = os.getenv("SUPABASE_URL")
        if supabase_url and "supabase.co" in supabase_url:
            # Extract project ID from URL
            project_id = supabase_url.split("//")[1].split(".")[0]
            database_url = f"postgresql://postgres.{project_id}:postgres@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    if not database_url:
        print("ERROR: No database URL found in environment variables")
        return
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Read SQL file
        with open("create_field_definitions_table.sql", "r") as f:
            sql = f.read()
        
        # Execute migration
        await conn.execute(sql)
        print("✅ Field definitions table created successfully!")
        
        # Check if table was created
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'field_definitions'
            )
        """)
        
        if exists:
            print("✅ Verified: field_definitions table exists")
            
            # Get row count
            count = await conn.fetchval("SELECT COUNT(*) FROM field_definitions")
            print(f"📊 Table contains {count} field definitions")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")

if __name__ == "__main__":
    asyncio.run(run_migration())