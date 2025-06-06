#!/usr/bin/env python3
"""Apply model_config column migration to ai_extraction_queue table."""

import subprocess
import sys

def main():
    print("Applying model_config column migration...")
    
    # Read the SQL file
    with open('add_model_config_column.sql', 'r') as f:
        sql_content = f.read()
    
    print("\nSQL to execute:")
    print("-" * 50)
    print(sql_content)
    print("-" * 50)
    
    print("\n✅ SQL file created: add_model_config_column.sql")
    print("\nTo apply this migration, please:")
    print("1. Go to your Supabase Dashboard")
    print("2. Navigate to the SQL Editor")
    print("3. Copy and paste the contents of add_model_config_column.sql")
    print("4. Click 'Run' to execute the migration")
    
    print("\nAlternatively, if you have the Supabase CLI installed:")
    print("  supabase db push add_model_config_column.sql")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)