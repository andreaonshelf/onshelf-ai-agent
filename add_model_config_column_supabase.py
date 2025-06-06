#!/usr/bin/env python3
"""Add model_config column to ai_extraction_queue table using Supabase."""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase connection
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_KEY not found in environment variables")
    exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL to add the model_config column
sql = """
-- Add model_config column to ai_extraction_queue table if it doesn't exist
ALTER TABLE ai_extraction_queue
ADD COLUMN IF NOT EXISTS model_config JSONB DEFAULT '{}'::jsonb;

-- Add comment to explain the column
COMMENT ON COLUMN ai_extraction_queue.model_config IS 'Model configuration including temperature, orchestrator model/prompt, and stage-specific model selections';
"""

try:
    print("Adding model_config column to ai_extraction_queue table...")
    
    # Execute the SQL using RPC
    result = supabase.rpc('exec_sql', {'query': sql}).execute()
    
    print("✓ Successfully added model_config column")
    
    # Verify the column was added
    verification_sql = """
        SELECT column_name, data_type, column_default 
        FROM information_schema.columns 
        WHERE table_name = 'ai_extraction_queue' 
        AND column_name = 'model_config'
    """
    
    verify_result = supabase.rpc('exec_sql', {'query': verification_sql}).execute()
    
    if verify_result.data and len(verify_result.data) > 0:
        col_info = verify_result.data[0]
        print(f"✓ Verified: Column '{col_info['column_name']}' of type '{col_info['data_type']}' with default '{col_info['column_default']}'")
    else:
        print("⚠️  Warning: Could not verify column was added")
        
except Exception as e:
    print(f"ERROR: Failed to add model_config column: {e}")
    # Try alternative approach - direct SQL execution
    print("\nTrying alternative approach...")
    
    try:
        # Use the SQL editor approach
        from src.config import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(sql)
        conn.commit()
        
        print("✓ Successfully added model_config column using direct connection")
        
        cur.close()
        conn.close()
        
    except Exception as e2:
        print(f"ERROR: Alternative approach also failed: {e2}")
        exit(1)

print("\nMigration completed successfully!")