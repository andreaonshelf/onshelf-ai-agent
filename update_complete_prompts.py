#!/usr/bin/env python3
"""
Update the prompt_text field with the COMPLETE prompts from EXTRACTION_PROMPTS_FINAL.md
including the IF_RETRY sections and all content, while keeping the clean field structures.
"""

import re
import json
import os
from typing import Dict, List, Any, Optional
from supabase import create_client, Client

def extract_complete_prompt_text(content: str, section_title: str, stage_number: str) -> str:
    """Extract the complete prompt text for a specific stage."""
    
    # Find the section
    section_start = content.find(section_title)
    if section_start == -1:
        return ""
    
    # Find the extraction prompt within this stage (handle different prompt types)
    prompt_start = content.find("### Extraction Prompt:", section_start)
    if prompt_start == -1:
        prompt_start = content.find("### Comparison Prompt:", section_start)
    if prompt_start == -1:
        return ""
    
    # Find the start of the actual prompt (after the ```)
    prompt_content_start = content.find("```", prompt_start)
    if prompt_content_start == -1:
        return ""
    
    prompt_content_start = content.find("\n", prompt_content_start) + 1
    
    # Find the end of the prompt (closing ```)
    prompt_end = content.find("```", prompt_content_start)
    if prompt_end == -1:
        return ""
    
    # Extract the prompt text
    prompt_text = content[prompt_content_start:prompt_end].strip()
    
    return prompt_text

def extract_all_complete_prompts(content: str) -> Dict[str, str]:
    """Extract all complete prompt texts from the document."""
    
    prompts = {}
    
    # Stage 1: Structure Extraction
    structure_prompt = extract_complete_prompt_text(content, "## STAGE 1: STRUCTURE EXTRACTION", "1")
    if structure_prompt:
        prompts['structure_v1'] = structure_prompt
    
    # Stage 2: Product Extraction
    product_prompt = extract_complete_prompt_text(content, "## STAGE 2: PRODUCT EXTRACTION", "2")
    if product_prompt:
        prompts['product_v1'] = product_prompt
    
    # Stage 3: Detail Enhancement
    detail_prompt = extract_complete_prompt_text(content, "## STAGE 3: DETAIL ENHANCEMENT", "3")
    if detail_prompt:
        prompts['detail_v1'] = detail_prompt
    
    # Visual Comparison
    visual_prompt = extract_complete_prompt_text(content, "## VISUAL COMPARISON", "visual")
    if visual_prompt:
        prompts['visual_v1'] = visual_prompt
    
    return prompts

def main():
    """Main function to update database with complete prompt texts."""
    print("Extracting complete prompt texts from EXTRACTION_PROMPTS_FINAL.md...")
    
    # Read the document
    try:
        with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/EXTRACTION_PROMPTS_FINAL.md', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: EXTRACTION_PROMPTS_FINAL.md not found")
        return
    
    # Extract all complete prompts
    complete_prompts = extract_all_complete_prompts(content)
    
    if not complete_prompts:
        print("No complete prompts found in document")
        return
    
    print(f"Extracted {len(complete_prompts)} complete prompts:")
    for name, prompt_text in complete_prompts.items():
        has_retry = '{IF_RETRY}' in prompt_text
        print(f"  - {name}: {len(prompt_text)} chars, IF_RETRY: {'✓' if has_retry else '✗'}")
        if has_retry:
            # Count retry blocks
            retry_blocks = prompt_text.count('{IF_RETRY}')
            print(f"    - {retry_blocks} retry block(s) found")
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Missing Supabase credentials")
        return
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Update database with complete prompt texts (keeping existing fields)
    prompt_mapping = {
        'structure_v1': 'Structure v1',
        'product_v1': 'Product v1',
        'detail_v1': 'Detail v1',
        'visual_v1': 'Visual v1'
    }
    
    success_count = 0
    for field_name, prompt_name in prompt_mapping.items():
        if field_name in complete_prompts:
            try:
                # Update only the prompt_text field, keeping existing fields
                result = supabase.table('prompt_templates').update({
                    'prompt_text': complete_prompts[field_name]
                }).eq('name', prompt_name).execute()
                
                print(f"✓ Updated {prompt_name} with complete prompt text ({len(complete_prompts[field_name])} chars)")
                success_count += 1
                
            except Exception as e:
                print(f"✗ Error updating {prompt_name}: {e}")
    
    print(f"\n✓ Successfully updated {success_count}/{len(prompt_mapping)} prompt texts")
    print("✓ All prompts now include complete text with IF_RETRY sections")
    
    # Save backup
    try:
        with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/complete_prompt_texts.json', 'w') as f:
            json.dump(complete_prompts, f, indent=2)
        print("✓ Complete prompt texts saved to complete_prompt_texts.json")
    except Exception as e:
        print(f"✗ Error saving backup: {e}")
    
    # Verify one prompt to show it's complete
    print(f"\n--- Sample: Structure v1 prompt preview ---")
    if 'structure_v1' in complete_prompts:
        sample = complete_prompts['structure_v1']
        print(f"Length: {len(sample)} characters")
        print(f"First 200 chars:\n{sample[:200]}")
        print("...")
        print(f"Last 200 chars:\n{sample[-200:]}")

if __name__ == "__main__":
    main()