#!/usr/bin/env python3
"""Run field definitions migration using Supabase client."""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def run_migration():
    """Run the field definitions table migration."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment variables")
        return
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read SQL file
        with open("create_field_definitions_table.sql", "r") as f:
            sql = f.read()
        
        # Execute raw SQL using RPC (if available) or just check if table exists
        # Note: Supabase doesn't directly support raw SQL execution via client
        # So we'll just verify the table and insert sample data
        
        print("Checking if field_definitions table exists...")
        
        # Try to query the table
        try:
            result = supabase.table("field_definitions").select("*").limit(1).execute()
            print("✅ field_definitions table already exists!")
            print(f"📊 Table contains {len(result.data)} field definitions")
            
            # If empty, insert sample definitions
            if len(result.data) == 0:
                print("Inserting sample field definitions...")
                
                sample_definitions = [
                    {
                        "field_name": "facings",
                        "display_name": "Facings",
                        "definition": "The number of identical products placed side by side on the shelf. Count each visible product face as one facing.",
                        "examples": "If you see 3 Coca-Cola bottles next to each other, that's 3 facings",
                        "data_type": "integer",
                        "is_required": True,
                        "is_active": True
                    },
                    {
                        "field_name": "stack",
                        "display_name": "Stack/Depth",
                        "definition": "The number of products stacked behind the front-facing product. Only count what's visible or can be reasonably inferred.",
                        "examples": "If products are stacked 2 deep, stack=2",
                        "data_type": "integer",
                        "is_required": True,
                        "is_active": True
                    },
                    {
                        "field_name": "position",
                        "display_name": "Shelf Position",
                        "definition": "The location of the product on the shelf, including shelf number and horizontal position.",
                        "examples": "Shelf 1, Position 3 from left",
                        "data_type": "object",
                        "is_required": True,
                        "is_active": True
                    }
                ]
                
                for definition in sample_definitions:
                    supabase.table("field_definitions").insert(definition).execute()
                
                print("✅ Sample field definitions inserted successfully!")
                
        except Exception as e:
            if "relation" in str(e) and "does not exist" in str(e):
                print("❌ field_definitions table does not exist!")
                print("Please run the SQL migration manually in Supabase SQL Editor:")
                print("\n" + "="*60)
                with open("create_field_definitions_table.sql", "r") as f:
                    print(f.read())
                print("="*60 + "\n")
            else:
                raise e
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_migration()