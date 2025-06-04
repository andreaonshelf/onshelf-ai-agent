#!/usr/bin/env python3
"""
Clean up duplicate prompts and verify all prompts have correct field definitions.
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

def cleanup_duplicates():
    """Remove duplicate prompts, keeping only the ones with proper descriptions and field definitions."""
    
    # Define the correct prompts we want to keep
    correct_prompts = {
        "structure": "Initial prompt for extracting shelf physical structure with Pydantic schema",
        "products": "Initial extraction of all products visible on shelves",
        "position": "Extract products with planogram context explanation",
        "detail": "Extract detailed product information for all identified products",
        "validation": "Compare generated planogram with original shelf photo for validation"
    }
    
    # Also keep retry prompts
    retry_prompts = {
        "structure": "Retry prompt for structure extraction with context from previous attempt",
        "position": "Retry product extraction with previous attempt context and visual feedback"
    }
    
    print("Cleaning up duplicate prompts...")
    
    # Get all prompts
    all_prompts = supabase.table('prompt_templates').select('*').order('prompt_type').execute()
    
    # Group by prompt_type
    prompts_by_type = {}
    for prompt in all_prompts.data:
        prompt_type = prompt['prompt_type']
        if prompt_type not in prompts_by_type:
            prompts_by_type[prompt_type] = []
        prompts_by_type[prompt_type].append(prompt)
    
    # Process each type
    for prompt_type, prompts in prompts_by_type.items():
        if len(prompts) > 1:
            print(f"\nProcessing {prompt_type} - found {len(prompts)} prompts")
            
            # Find the correct ones to keep
            to_keep = []
            to_delete = []
            
            for prompt in prompts:
                desc = prompt.get('description', '')
                has_field_defs = bool(prompt.get('field_definitions'))
                
                # Keep if it matches our correct descriptions or is a retry prompt
                if (prompt_type in correct_prompts and correct_prompts[prompt_type] in desc) or \
                   (prompt_type in retry_prompts and retry_prompts[prompt_type] in desc):
                    to_keep.append(prompt)
                    print(f"  ✓ Keeping: {prompt['prompt_id'][:8]}... - {desc[:50]}")
                else:
                    to_delete.append(prompt)
                    print(f"  ✗ Deleting: {prompt['prompt_id'][:8]}... - {desc[:50] if desc else 'No description'}")
            
            # Delete the duplicates
            for prompt in to_delete:
                try:
                    supabase.table('prompt_templates').delete().eq('prompt_id', prompt['prompt_id']).execute()
                    print(f"    Deleted {prompt['prompt_id']}")
                except Exception as e:
                    print(f"    Error deleting {prompt['prompt_id']}: {e}")
    
    print("\nCleanup complete!")

def verify_final_state():
    """Verify the final state of prompts in the database."""
    
    print("\n\nFinal verification of prompt templates:")
    print("="*80)
    
    # Get all remaining prompts
    response = supabase.table('prompt_templates').select('*').order('prompt_type').execute()
    
    print(f"\nTotal prompts remaining: {len(response.data)}")
    
    # Group by type for better display
    prompts_by_type = {}
    for prompt in response.data:
        prompt_type = prompt['prompt_type']
        if prompt_type not in prompts_by_type:
            prompts_by_type[prompt_type] = []
        prompts_by_type[prompt_type].append(prompt)
    
    # Display each type
    for prompt_type in sorted(prompts_by_type.keys()):
        prompts = prompts_by_type[prompt_type]
        print(f"\n{prompt_type.upper()} ({len(prompts)} prompt{'s' if len(prompts) > 1 else ''}):")
        
        for prompt in prompts:
            desc = prompt.get('description', 'No description')
            has_fields = bool(prompt.get('field_definitions'))
            field_count = len(prompt.get('field_definitions', [])) if has_fields else 0
            
            print(f"  - {desc[:60]}")
            print(f"    ID: {prompt['prompt_id']}")
            print(f"    Field definitions: {'✓' if has_fields else '✗'} ({field_count} fields)")
            
            # Show field names if they exist
            if has_fields:
                field_names = [f['name'] for f in prompt['field_definitions']]
                print(f"    Fields: {', '.join(field_names[:3])}{' ...' if len(field_names) > 3 else ''}")

if __name__ == "__main__":
    cleanup_duplicates()
    verify_final_state()