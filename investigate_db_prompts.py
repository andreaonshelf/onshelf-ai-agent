import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=== 1. CHECKING PROMPT_TEMPLATES TABLE STRUCTURE ===")
try:
    # Get table structure using raw SQL
    result = supabase.rpc('get_table_columns', {
        'table_name': 'prompt_templates'
    }).execute()
    print(f"Table structure query result: {result}")
except Exception as e:
    # Fallback: just query the table to see what columns exist
    try:
        result = supabase.table('prompt_templates').select('*').limit(1).execute()
        if result.data and len(result.data) > 0:
            print("Columns found in prompt_templates:")
            for col in result.data[0].keys():
                print(f"  - {col}")
        else:
            print("No data found, trying to insert and rollback to discover schema...")
    except Exception as e2:
        print(f"Error checking table structure: {e2}")

print("\n=== 2. CHECKING CURRENT PROMPTS IN DATABASE ===")
try:
    result = supabase.table('prompt_templates').select('*').execute()
    print(f"Total prompts found: {len(result.data)}")
    
    if result.data:
        # Group by field_name to see what fields we have
        fields = {}
        for prompt in result.data:
            field = prompt.get('field_name', 'Unknown')
            if field not in fields:
                fields[field] = []
            fields[field].append({
                'id': prompt.get('id'),
                'name': prompt.get('name'),
                'prompt_type': prompt.get('prompt_type'),
                'is_active': prompt.get('is_active'),
                'version': prompt.get('version'),
                'has_template': 'template' in prompt and prompt['template'] is not None
            })
        
        print("\nPrompts by field:")
        for field, prompts in fields.items():
            print(f"\n{field}: {len(prompts)} prompts")
            for p in prompts[:3]:  # Show first 3
                print(f"  - {p['name']} (type: {p['prompt_type']}, active: {p['is_active']}, version: {p['version']})")
            if len(prompts) > 3:
                print(f"  ... and {len(prompts) - 3} more")
                
        # Check for orchestrator-specific fields
        print("\n=== 3. CHECKING FOR ORCHESTRATOR SUPPORT ===")
        sample = result.data[0] if result.data else {}
        orchestrator_fields = ['context', 'variables', 'retry_config', 'meta_prompt_id', 'extraction_config']
        print("Orchestrator-related columns found:")
        for field in orchestrator_fields:
            if field in sample:
                print(f"  ✓ {field}")
            else:
                print(f"  ✗ {field} (missing)")
                
except Exception as e:
    print(f"Error querying prompts: {e}")

print("\n=== 4. CHECKING DISTINCT PROMPT TYPES ===")
try:
    result = supabase.table('prompt_templates').select('prompt_type').execute()
    prompt_types = set(p['prompt_type'] for p in result.data if p.get('prompt_type'))
    print(f"Distinct prompt types found: {sorted(prompt_types)}")
except Exception as e:
    print(f"Error checking prompt types: {e}")