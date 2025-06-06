import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv('DATABASE_URL')

if not database_url:
    print("ERROR: DATABASE_URL not found in environment variables")
    exit(1)

print("Database URL found, connecting...")

try:
    # Connect to database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("Successfully connected to database")
    
    # 1. Check what tables exist related to prompts
    print("\n=== 1. TABLES RELATED TO PROMPTS ===")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%prompt%'
        ORDER BY table_name;
    """)
    prompt_tables = cur.fetchall()
    print(f"Found {len(prompt_tables)} prompt-related tables:")
    for table in prompt_tables:
        print(f"  - {table['table_name']}")
    
    # 2. Check if there are any saved prompts in prompt_templates table
    print("\n=== 2. SAVED PROMPTS IN prompt_templates ===")
    cur.execute("""
        SELECT COUNT(*) as count FROM prompt_templates;
    """)
    count = cur.fetchone()
    print(f"Total prompts in prompt_templates: {count['count']}")
    
    # Get a sample of prompts
    cur.execute("""
        SELECT id, name, prompt_type, system_name, created_at, version
        FROM prompt_templates
        ORDER BY created_at DESC
        LIMIT 10;
    """)
    prompts = cur.fetchall()
    if prompts:
        print("\nRecent prompts:")
        for prompt in prompts:
            print(f"  - ID: {prompt['id']}, Name: {prompt['name']}, Type: {prompt['prompt_type']}, System: {prompt['system_name']}, Version: {prompt['version']}")
    
    # 3. Get the actual schema of prompt_templates table
    print("\n=== 3. SCHEMA OF prompt_templates TABLE ===")
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'prompt_templates'
        ORDER BY ordinal_position;
    """)
    columns = cur.fetchall()
    print("Columns in prompt_templates:")
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
        max_len = f"({col['character_maximum_length']})" if col['character_maximum_length'] else ""
        print(f"  - {col['column_name']}: {col['data_type']}{max_len} {nullable} {default}")
    
    # 4. Check other prompt-related tables
    print("\n=== 4. OTHER PROMPT-RELATED TABLES ===")
    
    # Check prompt_library if it exists
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'prompt_library'
        );
    """)
    if cur.fetchone()['exists']:
        cur.execute("SELECT COUNT(*) as count FROM prompt_library;")
        count = cur.fetchone()
        print(f"prompt_library table exists with {count['count']} entries")
        
        # Get schema
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'prompt_library'
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        print("  Columns:", [f"{c['column_name']} ({c['data_type']})" for c in cols])
    
    # Check meta_prompts if it exists
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'meta_prompts'
        );
    """)
    if cur.fetchone()['exists']:
        cur.execute("SELECT COUNT(*) as count FROM meta_prompts;")
        count = cur.fetchone()
        print(f"\nmeta_prompts table exists with {count['count']} entries")
        
        # Get schema
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'meta_prompts'
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        print("  Columns:", [f"{c['column_name']} ({c['data_type']})" for c in cols])
    
    # 5. Check for user-saved prompts specifically
    print("\n=== 5. USER-SAVED PROMPTS ===")
    
    # Check for prompts that are not system prompts (assuming system prompts have specific names)
    cur.execute("""
        SELECT 
            id, name, prompt_type, system_name, created_at, version,
            CASE 
                WHEN name LIKE 'orchestrator_%' THEN 'System'
                WHEN name LIKE 'planogram_%' THEN 'System'
                WHEN name LIKE 'comparison_%' THEN 'System'
                WHEN name LIKE 'structure_%' THEN 'System'
                ELSE 'User'
            END as prompt_source
        FROM prompt_templates
        ORDER BY created_at DESC;
    """)
    all_prompts = cur.fetchall()
    
    user_prompts = [p for p in all_prompts if p['prompt_source'] == 'User']
    system_prompts = [p for p in all_prompts if p['prompt_source'] == 'System']
    
    print(f"\nTotal prompts: {len(all_prompts)}")
    print(f"System prompts: {len(system_prompts)}")
    print(f"User prompts: {len(user_prompts)}")
    
    if user_prompts:
        print("\nUser-saved prompts:")
        for prompt in user_prompts[:10]:  # Show first 10
            print(f"  - {prompt['name']} (Type: {prompt['prompt_type']}, System: {prompt['system_name']})")
    
    # Check for any constraints or indexes
    print("\n=== CONSTRAINTS AND INDEXES ===")
    cur.execute("""
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_name = 'prompt_templates'
        ORDER BY tc.constraint_type, tc.constraint_name;
    """)
    constraints = cur.fetchall()
    if constraints:
        print("Constraints on prompt_templates:")
        for c in constraints:
            print(f"  - {c['constraint_name']} ({c['constraint_type']}) on {c['column_name']}")
    
    # Get sample of actual prompt content
    print("\n=== SAMPLE PROMPT CONTENT ===")
    cur.execute("""
        SELECT name, prompt_type, system_name, content, fields
        FROM prompt_templates
        WHERE name NOT LIKE 'orchestrator_%' 
        AND name NOT LIKE 'planogram_%'
        AND name NOT LIKE 'comparison_%'
        AND name NOT LIKE 'structure_%'
        LIMIT 3;
    """)
    user_samples = cur.fetchall()
    if user_samples:
        print("\nUser prompt samples:")
        for i, prompt in enumerate(user_samples, 1):
            print(f"\n{i}. {prompt['name']} ({prompt['prompt_type']} - {prompt['system_name']})")
            print(f"   Content preview: {prompt['content'][:200]}...")
            if prompt['fields']:
                print(f"   Fields: {json.dumps(prompt['fields'], indent=2)}")
    
    conn.close()
    print("\n✅ Database investigation complete")
    
except Exception as e:
    print(f"ERROR connecting to database: {str(e)}")
    import traceback
    traceback.print_exc()