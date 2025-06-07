#!/usr/bin/env python3
"""
Find where extraction_config is stored
"""

from supabase import create_client

def main():
    url = 'https://fxyfzjaaehgbdemjnumt.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU'
    
    supabase = create_client(url, key)
    
    # Common table names to check
    tables = [
        'extraction_results',
        'uploads', 
        'media_files',
        'processing_queue',
        'queue_items',
        'extraction_queue',
        'approval_queue'
    ]
    
    for table_name in tables:
        try:
            print(f"\n🔍 Checking table: {table_name}")
            
            # Try to get the structure
            response = supabase.table(table_name).select('*').limit(1).execute()
            
            if response.data:
                item = response.data[0]
                print(f"  ✅ Found {len(response.data)} records")
                
                # Check for extraction_config
                if 'extraction_config' in item:
                    print(f"  🎯 HAS extraction_config!")
                    
                    # Show the structure
                    print(f"  Fields: {list(item.keys())}")
                    
                    # If it has an ID field, check if it's ID 9
                    if 'id' in item:
                        # Get record with ID 9
                        id9_response = supabase.table(table_name).select('*').eq('id', 9).execute()
                        if id9_response.data:
                            print(f"  🎯 Found ID 9 in this table!")
                            return table_name
                    
                    # Check for other ID fields
                    id_fields = [k for k in item.keys() if 'id' in k.lower()]
                    print(f"  ID fields: {id_fields}")
                else:
                    print(f"  No extraction_config field")
            else:
                print(f"  ❌ Empty or not accessible")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    table = main()
    if table:
        print(f"\n🎉 Found extraction_config in table: {table}")
    else:
        print(f"\n❌ Could not find extraction_config table")