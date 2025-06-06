#!/usr/bin/env python3
"""Apply model_config column migration using Supabase client."""

import os
import sys
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
        
        print("📦 Checking ai_extraction_queue table...")
        
        # First, verify the table exists
        try:
            result = supabase.table('ai_extraction_queue').select('id').limit(1).execute()
            print("✅ Table ai_extraction_queue exists")
        except Exception as e:
            print(f"❌ Error: Could not access ai_extraction_queue table: {e}")
            return False
        
        # Check if model_config column already exists
        try:
            # Try to select the model_config column
            result = supabase.table('ai_extraction_queue').select('model_config').limit(1).execute()
            print("✅ Column model_config already exists!")
            return True
        except Exception as e:
            if "column" in str(e).lower() and "does not exist" in str(e).lower():
                print("⚠️  Column model_config does not exist, needs to be added")
            else:
                print(f"⚠️  Could not check for model_config column: {e}")
        
        # SQL to add the column
        sql = """
        -- Add model_config column to ai_extraction_queue table if it doesn't exist
        ALTER TABLE ai_extraction_queue
        ADD COLUMN IF NOT EXISTS model_config JSONB DEFAULT '{}'::jsonb;

        -- Add comment to explain the column
        COMMENT ON COLUMN ai_extraction_queue.model_config IS 'Model configuration including temperature, orchestrator model/prompt, and stage-specific model selections';
        """
        
        print("\n📝 SQL Migration to run:")
        print("-" * 60)
        print(sql)
        print("-" * 60)
        
        print("\n⚠️  IMPORTANT: This SQL needs to be executed manually")
        print("\nPlease follow these steps:")
        print("1. Go to your Supabase Dashboard: " + supabase_url)
        print("2. Navigate to SQL Editor (in the left sidebar)")
        print("3. Create a new query")
        print("4. Copy and paste the SQL above")
        print("5. Click 'Run' to execute")
        
        # Save SQL to file for convenience
        with open('add_model_config_column.sql', 'w') as f:
            f.write(sql)
        
        print("\n✅ SQL has been saved to: add_model_config_column.sql")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)