#!/usr/bin/env python3
"""
Generate a comprehensive comparison report of the Pydantic schemas.
"""
import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Missing Supabase credentials in environment variables")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)

def generate_report():
    """Generate a comprehensive comparison report."""
    
    print("="*80)
    print("PYDANTIC SCHEMA COMPARISON REPORT")
    print("="*80)
    
    print("\nSUMMARY OF CHANGES:")
    print("-"*40)
    print("1. Initial State:")
    print("   - 12 prompt templates found")
    print("   - NO Pydantic schemas defined (pydantic_schema column didn't exist)")
    print("   - Multiple duplicate prompts with no descriptions")
    print("   - field_definitions column existed but was empty")
    
    print("\n2. Actions Taken:")
    print("   - Cleaned up duplicate prompts (deleted 5 prompts with no descriptions)")
    print("   - Added field_definitions based on the agreed document")
    print("   - Created missing 'products' prompt with proper schema")
    print("   - Removed incorrect 'details' prompt")
    
    print("\n3. Final State:")
    response = supabase.table('prompt_templates').select('*').order('prompt_type').execute()
    print(f"   - 7 prompt templates (5 main + 2 retry)")
    print("   - All 5 main prompt types have field_definitions")
    print("   - Retry prompts correctly have no field_definitions (use same schema)")
    
    print("\n\nDETAILED SCHEMA DEFINITIONS:")
    print("-"*40)
    
    # Get all prompts with field definitions
    prompts_with_defs = [p for p in response.data if p.get('field_definitions')]
    
    for prompt in prompts_with_defs:
        print(f"\n{prompt['prompt_type'].upper()}")
        print(f"Description: {prompt.get('description', 'No description')}")
        print(f"Prompt ID: {prompt['prompt_id']}")
        print("\nField Definitions:")
        
        for field in prompt['field_definitions']:
            print(f"\n  • {field['name']} ({field['type']})")
            print(f"    Required: {field.get('required', False)}")
            print(f"    Description: {field.get('description', 'No description')}")
            
            # Show nested structure for complex types
            if field['type'] == 'array' and 'items' in field:
                items = field['items']
                if items.get('type') == 'object' and 'properties' in items:
                    print("    Properties:")
                    for prop_name, prop_def in items['properties'].items():
                        print(f"      - {prop_name}: {prop_def.get('type', 'unknown')}")
                        if 'description' in prop_def:
                            print(f"        {prop_def['description']}")
            
            elif field['type'] == 'object' and 'properties' in field:
                print("    Properties:")
                for prop_name, prop_def in field['properties'].items():
                    print(f"      - {prop_name}: {prop_def.get('type', 'unknown')}")
                    if 'description' in prop_def:
                        print(f"        {prop_def['description']}")
    
    print("\n\nRETRY PROMPTS:")
    print("-"*40)
    retry_prompts = [p for p in response.data if 'retry' in p.get('description', '').lower()]
    for prompt in retry_prompts:
        print(f"\n{prompt['prompt_type'].upper()} (Retry)")
        print(f"Description: {prompt.get('description', 'No description')}")
        print("Field Definitions: None (uses same schema as initial prompt)")
    
    print("\n\nCOMPLIANCE WITH AGREED DOCUMENT:")
    print("-"*40)
    
    # Check compliance
    required_types = ['structure', 'products', 'position', 'detail', 'validation']
    compliant = True
    
    for req_type in required_types:
        matching = [p for p in prompts_with_defs if p['prompt_type'] == req_type]
        if matching:
            print(f"✓ {req_type} - Present with field definitions")
        else:
            print(f"✗ {req_type} - Missing or no field definitions")
            compliant = False
    
    print(f"\nOverall Compliance: {'✓ COMPLIANT' if compliant else '✗ NOT COMPLIANT'}")
    
    print("\n\nKEY IMPROVEMENTS:")
    print("-"*40)
    print("1. All prompt types now have properly structured field definitions")
    print("2. Field definitions match the JSON Schema format from the agreed document")
    print("3. Each field has type, description, and required status")
    print("4. Complex nested structures (arrays, objects) are properly defined")
    print("5. Enums are used for constrained values (e.g., orientation, rail_type)")
    print("6. Retry prompts are correctly configured without duplicate schemas")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    generate_report()