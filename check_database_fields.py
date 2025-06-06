import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Get Supabase configuration
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# First check the structure of the table
print("Checking prompt_templates table structure...")
results = supabase.table('prompt_templates').select('*').limit(1).execute()
if results.data:
    print("Available columns:", list(results.data[0].keys()))
    print()

# Query to get field definitions for the specific prompts
# Using prompt_type and version fields based on the error hint
results = supabase.table('prompt_templates').select('*').execute()

print("All prompts in database:\n")

# Filter for our specific prompts
target_prompts = {
    'structure': 'Structure v1',
    'product': 'Product v1', 
    'detail': 'Detail v1',
    'visual': 'Visual v1'
}

for row in results.data:
    # Try to match based on prompt_type and version
    prompt_type = row.get('prompt_type', '')
    version = row.get('version', '')
    
    # Check if this is one of our target prompts
    for key, display_name in target_prompts.items():
        if (prompt_type.lower() == key and version == 'v1') or \
           (row.get('name') == display_name) or \
           (f"{prompt_type} {version}" == display_name):
            print(f"\n{'='*60}")
            print(f"Prompt: {display_name}")
            print(f"Type: {prompt_type}, Version: {version}")
            print(f"{'='*60}")
            if row.get('fields'):
                # Pretty print the JSON fields
                fields = json.dumps(row['fields'], indent=2)
                print(fields)
            else:
                print("No fields defined")
            break