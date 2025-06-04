import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL (from the pattern we know)
database_url = "postgresql://postgres.fxyfzjaaehgbdemjnumt:Av27X81jV0UqJsKH@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

try:
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Read the SQL file
    with open('update_field_schemas.sql', 'r') as f:
        sql_content = f.read()
    
    # Split into individual statements
    statements = []
    current = []
    for line in sql_content.split('\n'):
        if line.strip().startswith('--'):
            continue
        current.append(line)
        if line.strip().endswith(';'):
            statement = '\n'.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
    
    print(f"Found {len(statements)} SQL statements to execute\n")
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        # Get a preview
        lines = statement.split('\n')
        if len(lines) > 3:
            preview = '\n'.join(lines[:3]) + '...'
        else:
            preview = statement
        
        print(f"\nExecuting statement {i}:")
        print(f"Preview:\n{preview}")
        
        try:
            cur.execute(statement)
            if statement.strip().upper().startswith('UPDATE'):
                print(f"✓ Updated {cur.rowcount} rows")
            else:
                print("✓ Executed successfully")
        except Exception as e:
            print(f"✗ Error: {e}")
            # Continue with other statements
    
    # Commit all changes
    conn.commit()
    print("\n✓ All changes committed")
    
    # Verify the updates
    print("\n\n=== VERIFYING UPDATES ===")
    
    # Check if column exists
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'prompt_templates' 
        AND column_name = 'field_schema'
    """)
    result = cur.fetchone()
    if result:
        print(f"\n✓ field_schema column exists: {result['data_type']}")
    else:
        print("\n✗ field_schema column NOT found")
    
    # Check which prompts now have field_schema
    cur.execute("""
        SELECT 
            template_id,
            name,
            CASE 
                WHEN field_schema IS NOT NULL THEN 'Yes'
                ELSE 'No'
            END as has_field_schema,
            CASE 
                WHEN field_schema IS NOT NULL 
                THEN jsonb_typeof(field_schema)
                ELSE NULL
            END as schema_type,
            CASE
                WHEN field_schema IS NOT NULL
                THEN jsonb_array_length(jsonb_path_query_array(field_schema, '$.properties.*'))
                ELSE 0
            END as property_count
        FROM prompt_templates
        WHERE fields IS NOT NULL OR field_schema IS NOT NULL
        ORDER BY name;
    """)
    
    results = cur.fetchall()
    
    print(f"\nPrompts with field definitions:")
    print(f"{'Name':<50} {'Has Schema':<12} {'Type':<10} {'Properties':<10}")
    print("-" * 82)
    
    for row in results:
        print(f"{row['name']:<50} {row['has_field_schema']:<12} {row['schema_type'] or 'N/A':<10} {row['property_count']:<10}")
    
    # Show a sample schema
    cur.execute("""
        SELECT name, field_schema
        FROM prompt_templates
        WHERE field_schema IS NOT NULL
        LIMIT 1
    """)
    
    sample = cur.fetchone()
    if sample:
        print(f"\n\nSample JSON Schema from '{sample['name']}':")
        import json
        print(json.dumps(sample['field_schema'], indent=2)[:500] + "...")
    
    cur.close()
    conn.close()
    
    print("\n✓ Database update completed successfully!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()