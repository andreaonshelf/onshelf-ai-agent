#!/usr/bin/env python3
"""
Correctly parse EXTRACTION_PROMPTS_FINAL.md with proper nesting
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

def get_field_type(type_info: str) -> Tuple[str, Optional[List[str]]]:
    """Parse type info and return field type and allowed values if any"""
    # Check for Literal type first
    lit_type, lit_values = parse_literal_type(type_info)
    if lit_type:
        return 'literal', lit_values
    
    # Map document types to UI types
    if 'Object - nested' in type_info or 'Object (nested)' in type_info:
        return 'object', None
    elif 'List - array' in type_info or 'List (array)' in type_info:
        return 'list', None
    elif 'Text - string' in type_info or 'Text (string)' in type_info:
        return 'string', None
    elif 'Number - integer' in type_info or 'Number (integer)' in type_info:
        return 'integer', None
    elif 'Decimal - float' in type_info or 'Decimal (float)' in type_info:
        return 'float', None
    elif 'Yes/No - boolean' in type_info or 'Yes/No (boolean)' in type_info:
        return 'boolean', None
    else:
        return 'string', None  # default

def parse_instructor_section(lines: List[str], start_idx: int) -> List[Dict[str, Any]]:
    """Parse an Instructor Fields section starting from the given index"""
    fields = []
    i = start_idx
    
    # First, look for the root field definition
    # Format: **field_name** (Type) ✓/☐ Required/Optional
    root_pattern = r'^\*\*(\w+)\*\*\s*\((.*?)\)\s*(✓|☐)?\s*(Required|Optional)?'
    
    if i < len(lines):
        match = re.match(root_pattern, lines[i])
        if match:
            field_name = match.group(1)
            type_info = match.group(2)
            required_mark = match.group(3)
            
            field_type, allowed_values = get_field_type(type_info)
            
            root_field = {
                'name': field_name,
                'type': field_type,
                'required': required_mark == '✓'  # Only required if explicitly marked with ✓
            }
            
            if allowed_values:
                root_field['allowed_values'] = allowed_values
            
            # Get description
            if i + 1 < len(lines) and '- Description:' in lines[i + 1]:
                desc_match = re.search(r'Description:\s*(.+)', lines[i + 1])
                if desc_match:
                    root_field['description'] = desc_match.group(1).strip()
                i += 1
            
            # Initialize nested fields for objects
            if field_type == 'object':
                root_field['nested_fields'] = []
                
                # Look for "Nested fields within" marker
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('Nested fields within'):
                    i += 1
                
                if i < len(lines):
                    i += 1  # Skip the "Nested fields within" line
                    # Parse all nested fields
                    root_field['nested_fields'] = parse_nested_fields(lines, i, 0)
            
            fields.append(root_field)
    
    return fields

def parse_nested_fields(lines: List[str], start_idx: int, parent_indent: int) -> List[Dict[str, Any]]:
    """Parse nested fields with proper indentation handling"""
    fields = []
    i = start_idx
    
    while i < len(lines):
        line = lines[i]
        
        # Stop conditions
        if line.startswith('---') or line.startswith('##'):
            break
        
        # Skip empty lines
        if not line.strip():
            i += 1
            continue
        
        # Calculate indentation
        indent = len(line) - len(line.lstrip())
        
        # If we've dedented past our parent level, we're done
        if indent <= parent_indent and line.strip() and not line.strip().startswith('-'):
            break
        
        # Look for field definition
        # Format: - **field_name** (Type) ✓/☐ Required/Optional
        field_pattern = r'^(\s*)-\s*\*\*(\w+)\*\*\s*\((.*?)\)\s*(✓|☐)?\s*(Required|Optional)?'
        match = re.match(field_pattern, line)
        
        if match:
            field_indent = len(match.group(1))
            field_name = match.group(2)
            type_info = match.group(3)
            required_mark = match.group(4)
            
            field_type, allowed_values = get_field_type(type_info)
            
            # Default to required=true for fields without markers (common for nested fields)
            # Only set to false if explicitly marked with ☐
            field = {
                'name': field_name,
                'type': field_type,
                'required': required_mark != '☐'  # Required unless explicitly marked as optional with ☐
            }
            
            if allowed_values:
                field['allowed_values'] = allowed_values
            
            # Look for description on next line
            if i + 1 < len(lines) and 'Description:' in lines[i + 1]:
                desc_match = re.search(r'Description:\s*(.+)', lines[i + 1])
                if desc_match:
                    field['description'] = desc_match.group(1).strip()
                i += 1
            
            # Handle list item types
            if field_type == 'list':
                j = i + 1
                while j < len(lines) and lines[j].strip():
                    if 'Array item type:' in lines[j]:
                        item_line = lines[j]
                        if 'Object' in item_line:
                            field['list_item_type'] = 'object'
                            field['nested_fields'] = []
                        else:
                            # Check for Literal in array item type
                            lit_type, lit_values = parse_literal_type(item_line)
                            if lit_type:
                                field['list_item_type'] = 'literal'
                                field['allowed_values'] = lit_values
                            elif 'string' in item_line.lower() or 'text' in item_line.lower():
                                field['list_item_type'] = 'string'
                            elif 'integer' in item_line.lower() or 'number' in item_line.lower():
                                field['list_item_type'] = 'integer'
                            elif 'float' in item_line.lower() or 'decimal' in item_line.lower():
                                field['list_item_type'] = 'float'
                        break
                    j += 1
            
            # Handle nested fields for objects and object lists
            if field_type == 'object' or (field_type == 'list' and field.get('list_item_type') == 'object'):
                # Look for nested field definitions
                j = i + 1
                # Skip until we find "Nested fields:" or field definitions with deeper indent
                while j < len(lines):
                    if 'Nested fields:' in lines[j] or (lines[j].strip().startswith('-') and len(lines[j]) - len(lines[j].lstrip()) > field_indent):
                        if 'Nested fields:' in lines[j]:
                            j += 1
                        nested = parse_nested_fields(lines, j, field_indent)
                        if field_type == 'object':
                            field['nested_fields'] = nested
                        else:  # list with object items
                            field['nested_fields'] = nested
                        break
                    j += 1
            
            fields.append(field)
        
        i += 1
    
    return fields

# Read the document
with open('EXTRACTION_PROMPTS_FINAL.md', 'r') as f:
    content = f.read()
    lines = content.split('\n')

print(f"Read document: {len(lines)} lines")

# Find and parse each section
results = {}

for i, line in enumerate(lines):
    if '### Instructor Fields (UI Schema Builder):' in line:
        # Determine which stage this is for
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
            print(f"\nParsing {stage_name}...")
            # Skip blank line after section header
            start_idx = i + 2
            fields = parse_instructor_section(lines, start_idx)
            results[stage_name] = fields
            
            # Save to JSON for inspection
            with open(f'correct_{stage_name.lower().replace(" ", "_")}_fields.json', 'w') as f:
                json.dump(fields, f, indent=2)
            
            print(f"✓ Parsed {stage_name}: {len(fields)} root fields")
            if fields and fields[0].get('nested_fields'):
                print(f"  └─ Contains {len(fields[0]['nested_fields'])} nested fields")

# Update database
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if supabase_url and supabase_key:
    print("\nUpdating database...")
    supabase: Client = create_client(supabase_url, supabase_key)
    
    for stage_name, fields in results.items():
        if fields:
            try:
                result = supabase.table('prompt_templates').update({
                    'fields': json.dumps(fields)
                }).eq('name', stage_name).execute()
                print(f"✓ Updated {stage_name} in database")
            except Exception as e:
                print(f"✗ Error updating {stage_name}: {e}")
else:
    print("\n⚠️  No database credentials - only saved to JSON files")

print("\nDone! All fields have been parsed with correct nesting structure.")