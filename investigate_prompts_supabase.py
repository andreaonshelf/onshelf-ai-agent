import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Get Supabase URL and key
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    exit(1)

print(f"Supabase URL: {supabase_url}")
print("Service key present: Yes")

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)
print("Successfully connected to Supabase")

try:
    # 1. Check what tables exist related to prompts
    print("\n=== 1. CHECKING PROMPT-RELATED TABLES ===")
    
    # Get all tables (using a workaround since Supabase doesn't directly expose table list)
    # We'll try to query known prompt tables
    prompt_tables = ['prompt_templates', 'prompt_library', 'meta_prompts']
    existing_tables = []
    
    for table in prompt_tables:
        try:
            result = supabase.table(table).select("*").limit(1).execute()
            existing_tables.append(table)
            print(f"✓ Table '{table}' exists")
        except Exception as e:
            print(f"✗ Table '{table}' does not exist or error: {str(e)}")
    
    # 2. Check prompt_templates table
    print("\n=== 2. PROMPT_TEMPLATES TABLE ===")
    try:
        # Get count
        count_result = supabase.table('prompt_templates').select("*", count='exact').execute()
        print(f"Total prompts: {count_result.count}")
        
        # Get recent prompts
        prompts = supabase.table('prompt_templates').select("*").order('created_at', desc=True).limit(10).execute()
        
        if prompts.data:
            print("\nRecent prompts:")
            for prompt in prompts.data:
                print(f"  - ID: {prompt.get('id')}, Name: {prompt.get('name')}, "
                      f"Type: {prompt.get('prompt_type')}, System: {prompt.get('system_name')}, "
                      f"Version: {prompt.get('version')}")
        
        # Get schema from first record
        if prompts.data and len(prompts.data) > 0:
            print("\nColumns in prompt_templates:")
            for key in prompts.data[0].keys():
                print(f"  - {key}")
    
    except Exception as e:
        print(f"Error accessing prompt_templates: {str(e)}")
    
    # 3. Check for user-saved prompts
    print("\n=== 3. USER-SAVED PROMPTS ===")
    try:
        # Get all prompts
        all_prompts = supabase.table('prompt_templates').select("*").execute()
        
        user_prompts = []
        system_prompts = []
        
        for prompt in all_prompts.data:
            name = prompt.get('name', '')
            if (name.startswith('orchestrator_') or 
                name.startswith('planogram_') or 
                name.startswith('comparison_') or 
                name.startswith('structure_')):
                system_prompts.append(prompt)
            else:
                user_prompts.append(prompt)
        
        print(f"\nTotal prompts: {len(all_prompts.data)}")
        print(f"System prompts: {len(system_prompts)}")
        print(f"User prompts: {len(user_prompts)}")
        
        if user_prompts:
            print("\nUser-saved prompts:")
            for prompt in user_prompts[:10]:
                print(f"  - {prompt.get('name')} (Type: {prompt.get('prompt_type')}, "
                      f"System: {prompt.get('system_name')})")
                
        # Show sample content
        if user_prompts:
            print("\n=== SAMPLE USER PROMPT CONTENT ===")
            for i, prompt in enumerate(user_prompts[:3], 1):
                print(f"\n{i}. {prompt.get('name')} ({prompt.get('prompt_type')} - {prompt.get('system_name')})")
                content = prompt.get('content', '')
                print(f"   Content preview: {content[:200]}...")
                if prompt.get('fields'):
                    print(f"   Fields: {json.dumps(prompt.get('fields'), indent=2)}")
    
    except Exception as e:
        print(f"Error checking user prompts: {str(e)}")
    
    # 4. Check prompt_library if it exists
    if 'prompt_library' in existing_tables:
        print("\n=== 4. PROMPT_LIBRARY TABLE ===")
        try:
            lib_result = supabase.table('prompt_library').select("*", count='exact').execute()
            print(f"Total entries: {lib_result.count}")
            
            if lib_result.data:
                print("\nSample entries:")
                for entry in lib_result.data[:5]:
                    print(f"  - {entry}")
        except Exception as e:
            print(f"Error accessing prompt_library: {str(e)}")
    
    # 5. Check meta_prompts if it exists
    if 'meta_prompts' in existing_tables:
        print("\n=== 5. META_PROMPTS TABLE ===")
        try:
            meta_result = supabase.table('meta_prompts').select("*", count='exact').execute()
            print(f"Total entries: {meta_result.count}")
            
            if meta_result.data:
                print("\nSample entries:")
                for entry in meta_result.data[:5]:
                    print(f"  - {entry}")
        except Exception as e:
            print(f"Error accessing meta_prompts: {str(e)}")
    
    # 6. Check for prompts by prompt_type
    print("\n=== 6. PROMPTS BY TYPE ===")
    try:
        prompt_types = ['orchestrator', 'structure', 'position', 'detail', 'validation', 'comparison', 'planogram']
        
        for ptype in prompt_types:
            type_result = supabase.table('prompt_templates').select("id, name, system_name").eq('prompt_type', ptype).execute()
            if type_result.data:
                print(f"\n{ptype.upper()} prompts ({len(type_result.data)}):")
                for prompt in type_result.data[:3]:
                    print(f"  - {prompt.get('name')} (System: {prompt.get('system_name')})")
    
    except Exception as e:
        print(f"Error checking prompts by type: {str(e)}")
    
    print("\n✅ Investigation complete")
    
except Exception as e:
    print(f"\nERROR during investigation: {str(e)}")
    import traceback
    traceback.print_exc()