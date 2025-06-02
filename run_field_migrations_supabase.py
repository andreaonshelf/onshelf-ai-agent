#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment variables")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)

# Read SQL file
with open('add_field_definition_organization.sql', 'r') as f:
    sql_content = f.read()

try:
    print("Running field definition organization migration...")
    
    # Execute the SQL directly using RPC or raw SQL execution
    # Since we're adding columns, we'll do it step by step
    
    # Check and add category column
    result = supabase.rpc('run_sql', {'query': """
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'field_definitions' AND column_name = 'category'
    """}).execute()
    
    if not result.data:
        print("Adding category column...")
        supabase.rpc('run_sql', {'query': """
            ALTER TABLE field_definitions ADD COLUMN category VARCHAR(100)
        """}).execute()
        
        # Update categories
        supabase.rpc('run_sql', {'query': """
            UPDATE field_definitions 
            SET category = CASE
                WHEN field_name IN ('product_name', 'brand', 'variant', 'size', 'flavor') THEN 'Product Info'
                WHEN field_name IN ('price', 'promotion', 'discount') THEN 'Pricing'
                WHEN field_name IN ('facings', 'shelf_position', 'section', 'row', 'column') THEN 'Shelf Layout'
                WHEN field_name IN ('stock_level', 'out_of_stock') THEN 'Inventory'
                ELSE 'Other'
            END
            WHERE category IS NULL
        """}).execute()
    
    # Check and add sort_order column
    result = supabase.rpc('run_sql', {'query': """
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'field_definitions' AND column_name = 'sort_order'
    """}).execute()
    
    if not result.data:
        print("Adding sort_order column...")
        supabase.rpc('run_sql', {'query': """
            ALTER TABLE field_definitions ADD COLUMN sort_order INTEGER DEFAULT 999
        """}).execute()
        
        # Update sort orders
        supabase.rpc('run_sql', {'query': """
            UPDATE field_definitions 
            SET sort_order = CASE
                WHEN field_name = 'product_name' THEN 1
                WHEN field_name = 'brand' THEN 2
                WHEN field_name = 'variant' THEN 3
                WHEN field_name = 'size' THEN 4
                WHEN field_name = 'price' THEN 5
                WHEN field_name = 'facings' THEN 1
                WHEN field_name = 'shelf_position' THEN 2
                WHEN field_name = 'section' THEN 3
                ELSE 99
            END
            WHERE sort_order = 999
        """}).execute()
    
    # Check and add parent_field column
    result = supabase.rpc('run_sql', {'query': """
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'field_definitions' AND column_name = 'parent_field'
    """}).execute()
    
    if not result.data:
        print("Adding parent_field column...")
        supabase.rpc('run_sql', {'query': """
            ALTER TABLE field_definitions ADD COLUMN parent_field VARCHAR(100)
        """}).execute()
    
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error: Supabase may not have the 'run_sql' RPC function.")
    print("Please run the SQL migration directly in the Supabase SQL editor:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the contents of 'add_field_definition_organization.sql'")
    print("4. Execute the query")
    print(f"\nDetailed error: {e}")