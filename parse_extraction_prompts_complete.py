#!/usr/bin/env python3
"""
Parse the EXTRACTION_PROMPTS_FINAL.md document and extract ALL field structures
to update the database with properly formatted fields for the UI Schema Builder.
This version properly extracts all four field structures without duplications.
"""

import re
import json
import os
from typing import Dict, List, Any, Optional
from supabase import create_client, Client

def parse_field_definition(content: str, start_marker: str, end_marker: str) -> List[Dict[str, Any]]:
    """Extract field definitions between start and end markers."""
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    
    # Find start and end indices
    for i, line in enumerate(lines):
        if start_marker in line:
            start_idx = i + 1
        elif end_marker in line and start_idx is not None:
            end_idx = i
            break
    
    if start_idx is None:
        return []
    
    if end_idx is None:
        end_idx = len(lines)
    
    # Parse the field section
    fields = []
    field_lines = lines[start_idx:end_idx]
    
    i = 0
    while i < len(field_lines):
        line = field_lines[i]
        
        # Skip empty lines and non-field lines
        if not line.strip() or not line.strip().startswith('**') or not line.strip().startswith('-'):
            i += 1
            continue
            
        # Parse field definition
        field = parse_single_field(field_lines, i)
        if field:
            fields.append(field)
            # Skip ahead by the number of lines consumed
            i += field.get('_lines_consumed', 1)
        else:
            i += 1
    
    return fields

def parse_single_field(field_lines: List[str], start_idx: int) -> Optional[Dict[str, Any]]:
    """Parse a single field definition starting at the given index."""
    if start_idx >= len(field_lines):
        return None
        
    line = field_lines[start_idx]
    
    # Match field pattern: - **field_name** (Type) ✓/☐ Required/Optional
    pattern = r'^\s*-\s*\*\*([^*]+)\*\*\s*\(([^)]+)\)\s*(✓|☐)?\s*(Required|Optional)?'
    match = re.match(pattern, line)
    
    if not match:
        return None
    
    field_name = match.group(1).strip()
    type_str = match.group(2).strip()
    required_mark = match.group(3)
    required_text = match.group(4)
    
    field = {
        'name': field_name,
        'required': required_mark == '✓' or required_text == 'Required',
        '_lines_consumed': 1
    }
    
    # Parse type information
    field.update(parse_type_info(type_str))
    
    # Look for description on next line
    if start_idx + 1 < len(field_lines):
        next_line = field_lines[start_idx + 1]
        desc_match = re.search(r'^\s*-\s*Description:\s*(.+)', next_line)
        if desc_match:
            field['description'] = desc_match.group(1).strip()
            field['_lines_consumed'] += 1
    
    # Handle nested fields and array types
    consumed_lines = parse_nested_content(field_lines, start_idx + field['_lines_consumed'], field)
    field['_lines_consumed'] += consumed_lines
    
    return field

def parse_type_info(type_str: str) -> Dict[str, Any]:
    """Parse type string and return type information."""
    type_str = type_str.strip()
    
    # Handle Literal types
    literal_match = re.match(r'Literal\[(.*?)\]', type_str)
    if literal_match:
        values_str = literal_match.group(1)
        values = [v.strip().strip('"').strip("'") for v in values_str.split(',')]
        return {
            'type': 'literal',
            'allowed_values': values
        }
    
    # Handle specific type mappings
    type_mapping = {
        'Object - nested': 'object',
        'List - array': 'list',
        'Text - string': 'string',
        'Number - integer': 'integer',
        'Decimal - float': 'float',
        'Yes/No - boolean': 'boolean'
    }
    
    for doc_type, ui_type in type_mapping.items():
        if doc_type in type_str:
            result = {'type': ui_type}
            if ui_type == 'object':
                result['nested_fields'] = []
            return result
    
    # Default to string
    return {'type': 'string'}

def parse_nested_content(field_lines: List[str], start_idx: int, parent_field: Dict[str, Any]) -> int:
    """Parse nested fields and array item types."""
    if start_idx >= len(field_lines):
        return 0
    
    lines_consumed = 0
    current_idx = start_idx
    
    # Look for nested fields section
    while current_idx < len(field_lines):
        line = field_lines[current_idx]
        
        # Check for "Nested fields" marker
        if 'Nested fields' in line:
            lines_consumed += 1
            current_idx += 1
            
            # Parse nested fields
            nested_consumed = parse_nested_fields(field_lines, current_idx, parent_field)
            lines_consumed += nested_consumed
            current_idx += nested_consumed
            break
            
        # Check for array item type
        elif 'Array item type:' in line:
            lines_consumed += 1
            current_idx += 1
            
            # Parse array item type
            array_consumed = parse_array_item_type(field_lines, current_idx - 1, parent_field)
            lines_consumed += array_consumed
            current_idx += array_consumed
            break
        
        # If we hit another field definition or section, stop
        elif (line.strip().startswith('- **') or 
              line.strip().startswith('##') or 
              line.strip().startswith('---')):
            break
        
        current_idx += 1
        if current_idx == start_idx:  # Prevent infinite loop
            break
    
    return lines_consumed

def parse_nested_fields(field_lines: List[str], start_idx: int, parent_field: Dict[str, Any]) -> int:
    """Parse nested fields within an object."""
    lines_consumed = 0
    current_idx = start_idx
    
    if 'nested_fields' not in parent_field:
        parent_field['nested_fields'] = []
    
    while current_idx < len(field_lines):
        line = field_lines[current_idx]
        
        # Stop at next major section or end of nesting
        if (line.strip().startswith('##') or 
            line.strip().startswith('---') or
            (line.strip().startswith('- **') and not line.strip().startswith('  '))):
            break
        
        # Parse nested field
        if line.strip().startswith('- **'):
            nested_field = parse_single_field(field_lines, current_idx)
            if nested_field:
                parent_field['nested_fields'].append(nested_field)
                lines_consumed += nested_field.get('_lines_consumed', 1)
                current_idx += nested_field.get('_lines_consumed', 1)
            else:
                current_idx += 1
                lines_consumed += 1
        else:
            current_idx += 1
            lines_consumed += 1
    
    return lines_consumed

def parse_array_item_type(field_lines: List[str], array_line_idx: int, parent_field: Dict[str, Any]) -> int:
    """Parse array item type information."""
    if array_line_idx >= len(field_lines):
        return 0
        
    line = field_lines[array_line_idx]
    lines_consumed = 0
    
    # Extract array item type
    if 'Object' in line:
        parent_field['list_item_type'] = 'object'
        parent_field['nested_fields'] = []
        
        # Look for nested fields in the following lines
        current_idx = array_line_idx + 1
        while current_idx < len(field_lines):
            next_line = field_lines[current_idx]
            
            if next_line.strip().startswith('- **'):
                nested_field = parse_single_field(field_lines, current_idx)
                if nested_field:
                    parent_field['nested_fields'].append(nested_field)
                    lines_consumed += nested_field.get('_lines_consumed', 1)
                    current_idx += nested_field.get('_lines_consumed', 1)
                else:
                    current_idx += 1
                    lines_consumed += 1
            elif (next_line.strip().startswith('##') or 
                  next_line.strip().startswith('---') or
                  next_line.strip().startswith('- **') and not next_line.strip().startswith('  ')):
                break
            else:
                current_idx += 1
                lines_consumed += 1
    
    elif 'Literal' in line:
        literal_match = re.search(r'Literal\[(.*?)\]', line)
        if literal_match:
            values = [v.strip().strip('"').strip("'") for v in literal_match.group(1).split(',')]
            parent_field['list_item_type'] = 'literal'
            parent_field['allowed_values'] = values
    
    else:
        # Try to extract simple type
        type_match = re.search(r'Array item type:\s*(\w+)', line)
        if type_match:
            parent_field['list_item_type'] = type_match.group(1).lower()
    
    return lines_consumed

def extract_all_field_structures(content: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract all field structures from the document."""
    field_structures = {}
    
    # Define the sections to extract
    sections = [
        {
            'name': 'structure_v1',
            'start_marker': '### Instructor Fields (UI Schema Builder):',
            'section_start': '## STAGE 1: STRUCTURE EXTRACTION',
            'section_end': '## STAGE 2: PRODUCT EXTRACTION'
        },
        {
            'name': 'product_v1',
            'start_marker': '### Instructor Fields (UI Schema Builder):',
            'section_start': '## STAGE 2: PRODUCT EXTRACTION',
            'section_end': '## STAGE 3: DETAIL ENHANCEMENT'
        },
        {
            'name': 'detail_v1',
            'start_marker': '### Instructor Fields (UI Schema Builder):',
            'section_start': '## STAGE 3: DETAIL ENHANCEMENT',
            'section_end': '## VISUAL COMPARISON'
        },
        {
            'name': 'visual_v1',
            'start_marker': '### Instructor Fields (UI Schema Builder):',
            'section_start': '## VISUAL COMPARISON',
            'section_end': '## ORCHESTRATOR PROMPTS'
        }
    ]
    
    for section in sections:
        # Extract the relevant section content
        section_content = extract_section_content(content, section['section_start'], section['section_end'])
        
        # Find the field definitions within this section
        fields = parse_field_definition(section_content, section['start_marker'], '---')
        
        if fields:
            field_structures[section['name']] = fields
    
    return field_structures

def extract_section_content(content: str, start_marker: str, end_marker: str) -> str:
    """Extract content between two section markers."""
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if start_marker in line and start_idx is None:
            start_idx = i
        elif end_marker in line and start_idx is not None:
            end_idx = i
            break
    
    if start_idx is None:
        return ""
    
    if end_idx is None:
        end_idx = len(lines)
    
    return '\n'.join(lines[start_idx:end_idx])

def clean_field_structure(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean up field structure by removing internal parsing artifacts."""
    cleaned = []
    
    for field in fields:
        clean_field = {k: v for k, v in field.items() if not k.startswith('_')}
        
        # Recursively clean nested fields
        if 'nested_fields' in clean_field and clean_field['nested_fields']:
            clean_field['nested_fields'] = clean_field_structure(clean_field['nested_fields'])
        
        cleaned.append(clean_field)
    
    return cleaned

def main():
    """Main execution function."""
    print("Parsing EXTRACTION_PROMPTS_FINAL.md for all field structures...")
    
    # Read the document
    try:
        with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/EXTRACTION_PROMPTS_FINAL.md', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: EXTRACTION_PROMPTS_FINAL.md not found")
        return
    
    # Extract all field structures
    field_structures = extract_all_field_structures(content)
    
    if not field_structures:
        print("No field structures found in document")
        return
    
    print(f"Found {len(field_structures)} field structure sections:")
    for name in field_structures.keys():
        print(f"  - {name}")
    
    # Clean up the structures
    for name, fields in field_structures.items():
        field_structures[name] = clean_field_structure(fields)
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Missing Supabase credentials")
        return
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Update database with clean field structures
    prompt_mapping = {
        'structure_v1': 'Structure v1',
        'product_v1': 'Product v1',
        'detail_v1': 'Detail v1', 
        'visual_v1': 'Visual v1'
    }
    
    for field_name, prompt_name in prompt_mapping.items():
        if field_name in field_structures:
            try:
                # Convert to JSON string
                fields_json = json.dumps(field_structures[field_name], indent=2)
                
                # Update the database
                result = supabase.table('prompt_templates').update({
                    'fields': fields_json
                }).eq('name', prompt_name).execute()
                
                print(f"✓ Updated {prompt_name} with {len(field_structures[field_name])} field(s)")
                
                # Debug: Show first level fields
                for field in field_structures[field_name]:
                    print(f"  - {field['name']} ({field['type']})")
                    
            except Exception as e:
                print(f"✗ Error updating {prompt_name}: {e}")
    
    print("\nField structure extraction and database update completed.")
    
    # Save a backup to file for verification
    try:
        with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/extracted_field_structures.json', 'w') as f:
            json.dump(field_structures, f, indent=2)
        print("✓ Backup saved to extracted_field_structures.json")
    except Exception as e:
        print(f"✗ Error saving backup: {e}")

if __name__ == "__main__":
    main()