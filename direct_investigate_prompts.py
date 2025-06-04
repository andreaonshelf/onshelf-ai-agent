import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

def get_db_connection():
    """Get database connection from environment variables"""
    db_url = os.environ.get("SUPABASE_DB_URL", os.environ.get("DATABASE_URL"))
    if not db_url:
        raise ValueError("No database URL found in environment variables")
    return psycopg2.connect(db_url)

def investigate_prompts():
    """Investigate prompt_templates table structure and duplicates"""
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Check current table structure
        print("1. Checking prompt_templates structure:")
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = 'prompt_templates'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        print("\nTable Columns:")
        for col in columns:
            print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        
        # 2. Check for duplicates
        print("\n2. Checking for duplicate names:")
        cur.execute("""
            SELECT 
                name, 
                stage_type,
                COUNT(*) as count,
                string_agg(template_id::text, ', ' ORDER BY created_at) as template_ids
            FROM prompt_templates
            WHERE name IS NOT NULL
            GROUP BY name, stage_type
            HAVING COUNT(*) > 1
            ORDER BY count DESC, name
            LIMIT 10;
        """)
        duplicates = cur.fetchall()
        if duplicates:
            print("\nDuplicates Found:")
            for dup in duplicates:
                print(f"  - {dup['name']} (stage: {dup['stage_type']}) - {dup['count']} copies")
                print(f"    Template IDs: {dup['template_ids']}")
        else:
            print("  No duplicates found")
        
        # 3. Look at the specific problematic prompt
        print("\n3. Examining 'custom_structure_gpt4o_v2.0' prompts:")
        cur.execute("""
            SELECT 
                prompt_id,
                template_id,
                name,
                prompt_type,
                stage_type,
                model_type,
                created_at
            FROM prompt_templates
            WHERE name = 'custom_structure_gpt4o_v2.0'
            OR template_id = 'custom_structure_gpt4o_v2.0'
            ORDER BY created_at;
        """)
        prompts = cur.fetchall()
        print(f"\nFound {len(prompts)} prompts:")
        for p in prompts:
            print(f"  - ID: {p['prompt_id'][:8]}...")
            print(f"    Template ID: {p['template_id']}")
            print(f"    Name: {p['name']}")
            print(f"    Stage Type: {p['stage_type']}")
            print(f"    Created: {p['created_at']}")
            print()
        
        # 4. Check name population status
        print("4. Checking name column status:")
        cur.execute("""
            SELECT 
                COUNT(*) as total_prompts,
                COUNT(name) as prompts_with_names,
                COUNT(DISTINCT name) as unique_names,
                COUNT(*) FILTER (WHERE name IS NULL) as prompts_without_names,
                COUNT(*) FILTER (WHERE stage_type IS NULL) as prompts_without_stage
            FROM prompt_templates;
        """)
        stats = cur.fetchone()
        print(f"  Total prompts: {stats['total_prompts']}")
        print(f"  With names: {stats['prompts_with_names']}")
        print(f"  Unique names: {stats['unique_names']}")
        print(f"  Without names: {stats['prompts_without_names']}")
        print(f"  Without stage_type: {stats['prompts_without_stage']}")
        
        # 5. Check existing constraints
        print("\n5. Checking existing constraints:")
        cur.execute("""
            SELECT 
                conname as constraint_name,
                contype as constraint_type,
                pg_get_constraintdef(oid) as definition
            FROM pg_constraint
            WHERE conrelid = 'prompt_templates'::regclass
            ORDER BY conname;
        """)
        constraints = cur.fetchall()
        for con in constraints:
            print(f"  - {con['constraint_name']} ({con['constraint_type']}): {con['definition']}")
        
        # 6. Suggest fix
        print("\n6. Suggested fix:")
        print("Since you have duplicate names, you need to make them unique before adding the constraint.")
        print("Here's what we'll do:")
        
        # Show what the fix would do
        cur.execute("""
            WITH duplicates_ranked AS (
                SELECT 
                    prompt_id,
                    name,
                    stage_type,
                    template_id,
                    ROW_NUMBER() OVER (PARTITION BY name, stage_type ORDER BY created_at, prompt_id) as rn
                FROM prompt_templates
                WHERE name IS NOT NULL
            )
            SELECT 
                prompt_id,
                template_id,
                name,
                stage_type,
                CASE 
                    WHEN rn = 1 THEN name
                    ELSE name || ' (v' || rn || ')'
                END as new_name
            FROM duplicates_ranked
            WHERE rn > 1
            ORDER BY name, rn;
        """)
        fixes = cur.fetchall()
        if fixes:
            print("\nWill rename these duplicates:")
            for fix in fixes:
                print(f"  - {fix['name']} → {fix['new_name']}")
                print(f"    Template ID: {fix['template_id']}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    investigate_prompts()