import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
database_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
if not database_url:
    print("DATABASE_URL not found in environment variables")
    exit(1)

try:
    # Connect to database
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # First, check the structure of prompt_templates table
    print("=== CHECKING PROMPT_TEMPLATES TABLE STRUCTURE ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'prompt_templates' 
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print("\nColumns in prompt_templates:")
    for col in columns:
        print(f"  - {col['column_name']}: {col['data_type']}")
    
    # Now check the field_schema content for each prompt
    print("\n=== CHECKING FIELD_SCHEMA CONTENT ===")
    cur.execute("""
        SELECT 
            template_id,
            name,
            prompt_type,
            stage_type,
            field_schema
        FROM prompt_templates
        WHERE field_schema IS NOT NULL
        ORDER BY name, stage_type
    """)
    
    prompts = cur.fetchall()
    
    if not prompts:
        print("\nNo prompts found with field_schema!")
    else:
        print(f"\nFound {len(prompts)} prompts with field_schema:")
        
        for prompt in prompts:
            print(f"\n--- {prompt['name']} ({prompt['stage_type']}) ---")
            print(f"Template ID: {prompt['template_id']}")
            print(f"Prompt Type: {prompt['prompt_type']}")
            
            if prompt['field_schema']:
                try:
                    # Parse and pretty print the schema
                    schema = json.loads(prompt['field_schema'])
                    print("Field Schema:")
                    print(json.dumps(schema, indent=2))
                except json.JSONDecodeError as e:
                    print(f"Error parsing field_schema: {e}")
                    print(f"Raw field_schema: {prompt['field_schema']}")
            else:
                print("Field Schema: NULL")
    
    # Also check for prompts without field_schema
    print("\n=== CHECKING PROMPTS WITHOUT FIELD_SCHEMA ===")
    cur.execute("""
        SELECT 
            template_id,
            name,
            prompt_type,
            stage_type
        FROM prompt_templates
        WHERE field_schema IS NULL
        ORDER BY name, stage_type
    """)
    
    empty_prompts = cur.fetchall()
    if empty_prompts:
        print(f"\nFound {len(empty_prompts)} prompts without field_schema:")
        for prompt in empty_prompts:
            print(f"  - {prompt['name']} ({prompt['stage_type']}) - {prompt['prompt_type']}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()