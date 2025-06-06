#!/usr/bin/env python3
"""
Parse EXTRACTION_PROMPTS_FINAL.md and extract the EXACT field structures
"""

import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from supabase import create_client, Client

def parse_literal_type(type_str: str) -> Tuple[str, Optional[List[str]]]:
    """Parse Literal[...] types and return type and allowed values"""
    literal_match = re.match(r'Literal\[(.*?)\]', type_str)
    if literal_match:
        values_str = literal_match.group(1)
        # Extract quoted values
        values = re.findall(r'"([^"]+)"', values_str)
        return 'literal', values
    return None, None

def parse_field_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a field definition line"""
    # Match: - **field_name** (Type) ✓/☐ Required/Optional
    pattern = r'^(\s*)-\s*\*\*(\w+)\*\*\s*\((.*?)\)\s*(✓|☐)?\s*(Required|Optional)?'
    match = re.match(pattern, line)
    
    if match:
        indent = len(match.group(1))
        field_name = match.group(2)
        type_info = match.group(3)
        required_mark = match.group(4)
        
        # Determine field type
        field_type = 'string'  # default
        allowed_values = None
        list_item_type = None
        
        # Check for Literal type
        lit_type, lit_values = parse_literal_type(type_info)
        if lit_type:
            field_type = 'literal'
            allowed_values = lit_values
        elif 'Object - nested' in type_info or 'Object (nested)' in type_info:
            field_type = 'object'
        elif 'List - array' in type_info or 'List (array)' in type_info:
            field_type = 'list'
        elif 'Text - string' in type_info or 'Text (string)' in type_info:
            field_type = 'string'
        elif 'Number - integer' in type_info or 'Number (integer)' in type_info:
            field_type = 'integer'
        elif 'Decimal - float' in type_info or 'Decimal (float)' in type_info:
            field_type = 'float'
        elif 'Yes/No - boolean' in type_info or 'Yes/No (boolean)' in type_info:
            field_type = 'boolean'
        
        field = {
            'name': field_name,
            'type': field_type,
            'required': required_mark == '✓' if required_mark else True,
            'indent': indent
        }
        
        if allowed_values:
            field['allowed_values'] = allowed_values
            
        return field
    
    return None

def parse_fields_section(lines: List[str], start_idx: int, section_name: str) -> List[Dict[str, Any]]:
    """Parse a complete fields section"""
    fields = []
    field_stack = []  # Stack to track nesting
    current_idx = start_idx
    
    while current_idx < len(lines):
        line = lines[current_idx]
        
        # Stop at next section or document end
        if line.startswith('---') or line.startswith('##'):
            break
            
        # Parse field line
        field_data = parse_field_line(line)
        if field_data:
            indent = field_data.pop('indent')
            
            # Get description from next line if present
            if current_idx + 1 < len(lines) and '- Description:' in lines[current_idx + 1]:
                desc_match = re.search(r'Description:\s*(.+)', lines[current_idx + 1])
                if desc_match:
                    field_data['description'] = desc_match.group(1).strip()
                    current_idx += 1
            
            # Handle list item type
            if field_data['type'] == 'list' and current_idx + 1 < len(lines):
                next_line = lines[current_idx + 1]
                if 'Array item type:' in next_line:
                    if 'Object' in next_line:
                        field_data['list_item_type'] = 'object'
                        field_data['nested_fields'] = []
                    else:
                        # Check for Literal in array item type
                        lit_type, lit_values = parse_literal_type(next_line)
                        if lit_type:
                            field_data['list_item_type'] = 'literal'
                            field_data['allowed_values'] = lit_values
                        elif 'Text' in next_line or 'string' in next_line:
                            field_data['list_item_type'] = 'string'
                        elif 'Number' in next_line or 'integer' in next_line:
                            field_data['list_item_type'] = 'integer'
                    current_idx += 1
            
            # Initialize nested fields for objects
            if field_data['type'] == 'object':
                field_data['nested_fields'] = []
            
            # Determine where to add this field based on indentation
            if indent == 0 or not field_stack:
                # Top level field
                fields.append(field_data)
                field_stack = [(indent, field_data)]
            else:
                # Find parent based on indentation
                while field_stack and field_stack[-1][0] >= indent:
                    field_stack.pop()
                
                if field_stack:
                    parent = field_stack[-1][1]
                    # Add to parent's nested fields
                    if parent['type'] == 'object' and 'nested_fields' in parent:
                        parent['nested_fields'].append(field_data)
                    elif parent['type'] == 'list' and parent.get('list_item_type') == 'object':
                        if 'nested_fields' not in parent:
                            parent['nested_fields'] = []
                        parent['nested_fields'].append(field_data)
                
                field_stack.append((indent, field_data))
        
        current_idx += 1
    
    return fields

# Read the document
try:
    with open('EXTRACTION_PROMPTS_FINAL.md', 'r') as f:
        content = f.read()
        lines = content.split('\n')
    print(f"Read document: {len(lines)} lines")
except FileNotFoundError:
    print("ERROR: EXTRACTION_PROMPTS_FINAL.md not found")
    print("Looking for it...")
    import glob
    files = glob.glob("**/EXTRACTION_PROMPTS_FINAL.md", recursive=True)
    if files:
        print(f"Found at: {files[0]}")
        with open(files[0], 'r') as f:
            content = f.read()
            lines = content.split('\n')
    else:
        print("Could not find EXTRACTION_PROMPTS_FINAL.md")
        exit(1)

# Find sections
sections = {
    'Structure v1': None,
    'Product v1': None,
    'Detail v1': None,
    'Visual v1': None
}

# Parse each section
for i, line in enumerate(lines):
    if '### Instructor Fields (UI Schema Builder):' in line:
        print(f"Found Instructor Fields section at line {i}")
        # Look back to find which stage this is for
        stage_name = None
        for j in range(i-1, max(0, i-100), -1):
            if '## STAGE 1: STRUCTURE EXTRACTION' in lines[j]:
                stage_name = 'Structure v1'
                break
            elif '## STAGE 2: PRODUCT EXTRACTION' in lines[j]:
                stage_name = 'Product v1'
                break
            elif '## STAGE 3: DETAIL ENHANCEMENT' in lines[j]:
                stage_name = 'Detail v1'
                break
            elif '## VISUAL COMPARISON' in lines[j]:
                stage_name = 'Visual v1'
                break
        
        if stage_name:
            print(f"Parsing {stage_name} fields...")
            # Parse fields starting from next line
            fields = parse_fields_section(lines, i + 2, stage_name)
            sections[stage_name] = fields
            print(f"Found {len(fields)} top-level fields for {stage_name}")
        else:
            print(f"Could not determine stage name for section at line {i}")

# Save parsed structures
for stage, fields in sections.items():
    if fields:
        with open(f'parsed_{stage.lower().replace(" ", "_")}_fields.json', 'w') as f:
            json.dump(fields, f, indent=2)
        print(f"Parsed {stage}: {len(fields)} top-level fields")

# Update database
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
    
    for stage_name, fields in sections.items():
        if fields:
            try:
                # Update the prompt template
                result = supabase.table('prompt_templates').update({
                    'fields': json.dumps(fields)
                }).eq('name', stage_name).execute()
                print(f"✓ Updated {stage_name} in database")
            except Exception as e:
                print(f"✗ Error updating {stage_name}: {e}")
else:
    print("\n⚠️  No database credentials - only parsed to JSON files")