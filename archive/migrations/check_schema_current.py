import psycopg2
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get database URL from various possible sources
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Try to get from Supabase URL
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if SUPABASE_URL:
        # Extract project ref from URL
        import re
        match = re.search(r'https://([^.]+)\.supabase\.co', SUPABASE_URL)
        if match:
            project_ref = match.group(1)
            # Use the service role key for authentication
            DATABASE_URL = f"postgresql://postgres:{SUPABASE_SERVICE_ROLE_KEY}@db.{project_ref}.supabase.co:5432/postgres"

if not DATABASE_URL:
    print("ERROR: No database connection found!")
    exit(1)

print(f"Connecting to database...")

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1. Check prompt_templates structure
    print("\n=== PROMPT_TEMPLATES TABLE STRUCTURE ===")
    cur.execute("""
        SELECT 
            column_name, 
            data_type, 
            is_nullable, 
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = 'prompt_templates'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()
    if columns:
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    else:
        print("  Table not found or no columns")

    # 2. Check if meta_prompts table exists
    print("\n=== META_PROMPTS TABLE ===")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'meta_prompts'
        );
    """)
    exists = cur.fetchone()[0]
    if exists:
        print("Table exists. Structure:")
        cur.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'meta_prompts'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    else:
        print("Table does not exist")

    # 3. Check field_definitions structure
    print("\n=== FIELD_DEFINITIONS TABLE STRUCTURE ===")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'field_definitions'
        );
    """)
    exists = cur.fetchone()[0]
    if exists:
        print("Table exists. Structure:")
        cur.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' 
            AND table_name = 'field_definitions'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
        # Also check sample data to understand instructor_fields format
        print("\n  Sample instructor_fields data:")
        cur.execute("""
            SELECT field_key, instructor_fields 
            FROM field_definitions 
            WHERE instructor_fields IS NOT NULL
            LIMIT 3;
        """)
        samples = cur.fetchall()
        for sample in samples:
            print(f"    {sample[0]}:")
            if sample[1]:
                try:
                    # Try to pretty print if it's JSON
                    fields = json.loads(sample[1]) if isinstance(sample[1], str) else sample[1]
                    print(f"      {json.dumps(fields, indent=6)}")
                except:
                    print(f"      {sample[1]}")
    else:
        print("Table does not exist")

    # 4. Also check for any constraints or indexes
    print("\n=== CONSTRAINTS AND INDEXES ===")
    cur.execute("""
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            tc.table_name,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name IN ('prompt_templates', 'meta_prompts', 'field_definitions')
        AND tc.table_schema = 'public'
        ORDER BY tc.table_name, tc.constraint_type;
    """)
    constraints = cur.fetchall()
    for constraint in constraints:
        print(f"  {constraint[2]}.{constraint[3]}: {constraint[1]} ({constraint[0]})")

    # Clean up
    cur.close()
    conn.close()

    print("\nDatabase check complete!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()