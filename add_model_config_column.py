#!/usr/bin/env python3
"""Add model_config column to ai_extraction_queue table."""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    exit(1)

# SQL to add the model_config column
sql = """
-- Add model_config column to ai_extraction_queue table if it doesn't exist
ALTER TABLE ai_extraction_queue
ADD COLUMN IF NOT EXISTS model_config JSONB DEFAULT '{}'::jsonb;

-- Add comment to explain the column
COMMENT ON COLUMN ai_extraction_queue.model_config IS 'Model configuration including temperature, orchestrator model/prompt, and stage-specific model selections';
"""

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    print("Adding model_config column to ai_extraction_queue table...")
    
    # Execute the SQL
    cur.execute(sql)
    
    print("✓ Successfully added model_config column")
    
    # Verify the column was added
    cur.execute("""
        SELECT column_name, data_type, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'ai_extraction_queue' 
        AND column_name = 'model_config'
    """)
    
    result = cur.fetchone()
    if result:
        print(f"✓ Verified: Column '{result[0]}' of type '{result[1]}' with default '{result[2]}'")
    else:
        print("⚠️  Warning: Could not verify column was added")
    
    # Close connections
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"ERROR: Failed to add model_config column: {e}")
    exit(1)

print("\nMigration completed successfully!")