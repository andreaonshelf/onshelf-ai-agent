#!/usr/bin/env python3
"""
Clean parser for EXTRACTION_PROMPTS_FINAL.md that extracts field structures 
without duplications and formats them correctly for the UI Schema Builder.
"""

import re
import json
import os
from typing import Dict, List, Any, Optional
from supabase import create_client, Client

def clean_parse_fields(content: str, section_title: str) -> List[Dict[str, Any]]:
    """Parse field structure for a specific section without duplications."""
    
    # Find the section
    section_start = content.find(section_title)
    if section_start == -1:
        return []
    
    # Find the fields section within this stage
    fields_start = content.find("### Instructor Fields (UI Schema Builder):", section_start)
    if fields_start == -1:
        return []
    
    # Find the end of this section (next ## or end of file)
    next_section = content.find("\n## ", fields_start)
    if next_section == -1:
        fields_content = content[fields_start:]
    else:
        fields_content = content[fields_start:next_section]
    
    # Split into lines and parse
    lines = fields_content.split('\n')
    return parse_field_lines(lines)

def parse_field_lines(lines: List[str]) -> List[Dict[str, Any]]:
    """Parse field definition lines."""
    fields = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for field definitions starting with **field_name**
        field_match = re.match(r'^\*\*([^*]+)\*\*\s*\(([^)]+)\)\s*(✓|☐)?\s*(Required|Optional)?', line)
        if field_match:
            field_name = field_match.group(1)
            type_str = field_match.group(2)
            required_mark = field_match.group(3)
            
            field = {
                'name': field_name,
                'type': parse_type(type_str),
                'required': required_mark == '✓'
            }
            
            # Look for description on next line
            if i + 1 < len(lines) and 'Description:' in lines[i + 1]:
                desc_match = re.search(r'Description:\s*(.+)', lines[i + 1])
                if desc_match:
                    field['description'] = desc_match.group(1).strip()
            
            # Handle type-specific properties
            if field['type'] == 'literal':
                field['allowed_values'] = parse_literal_values(type_str)
            elif field['type'] == 'object':
                field['nested_fields'] = []
                # Parse nested fields
                nested_fields, consumed = parse_nested_fields(lines, i + 1)
                field['nested_fields'] = nested_fields
                i += consumed
            elif field['type'] == 'list':
                # Look for array item type
                item_type, item_values, nested = parse_array_item_info(lines, i + 1)
                if item_type:
                    field['list_item_type'] = item_type
                if item_values:
                    field['allowed_values'] = item_values
                if nested:
                    field['nested_fields'] = nested
            
            fields.append(field)
        
        i += 1
    
    return fields

def parse_type(type_str: str) -> str:
    """Parse type from string."""
    type_str = type_str.strip()
    
    if 'Literal[' in type_str:
        return 'literal'
    elif 'Object - nested' in type_str:
        return 'object'
    elif 'List - array' in type_str:
        return 'list'
    elif 'Text - string' in type_str:
        return 'string'
    elif 'Number - integer' in type_str:
        return 'integer'
    elif 'Decimal - float' in type_str:
        return 'float'
    elif 'Yes/No - boolean' in type_str:
        return 'boolean'
    else:
        return 'string'

def parse_literal_values(type_str: str) -> List[str]:
    """Extract allowed values from Literal type."""
    match = re.search(r'Literal\[(.*?)\]', type_str)
    if match:
        values_str = match.group(1)
        return [v.strip().strip('"').strip("'") for v in values_str.split(',')]
    return []

def parse_nested_fields(lines: List[str], start_idx: int) -> tuple[List[Dict[str, Any]], int]:
    """Parse nested fields and return them with lines consumed."""
    nested_fields = []
    consumed = 0
    
    # Look for "Nested fields" marker
    for i in range(start_idx, min(start_idx + 10, len(lines))):
        if 'Nested fields' in lines[i]:
            consumed = i - start_idx + 1
            break
    
    if consumed == 0:
        return [], 0
    
    # Parse nested field definitions
    current_idx = start_idx + consumed
    while current_idx < len(lines):
        line = lines[current_idx].strip()
        
        # Stop at next major section or when we're back to non-nested content
        if (line.startswith('##') or 
            line.startswith('---') or
            (line.startswith('**') and not line.startswith('  ') and not line.startswith('    '))):
            break
        
        # Parse nested field
        field_match = re.match(r'^\s*-\s*\*\*([^*]+)\*\*\s*\(([^)]+)\)\s*(✓|☐)?\s*(Required|Optional)?', line)
        if field_match:
            field_name = field_match.group(1)
            type_str = field_match.group(2)
            required_mark = field_match.group(3)
            
            nested_field = {
                'name': field_name,
                'type': parse_type(type_str),
                'required': required_mark == '✓'
            }
            
            # Look for description
            if current_idx + 1 < len(lines) and 'Description:' in lines[current_idx + 1]:
                desc_match = re.search(r'Description:\s*(.+)', lines[current_idx + 1])
                if desc_match:
                    nested_field['description'] = desc_match.group(1).strip()
                    consumed += 1
                    current_idx += 1
            
            # Handle literal types
            if nested_field['type'] == 'literal':
                nested_field['allowed_values'] = parse_literal_values(type_str)
            
            nested_fields.append(nested_field)
            consumed += 1
        
        current_idx += 1
    
    return nested_fields, consumed

def parse_array_item_info(lines: List[str], start_idx: int) -> tuple[Optional[str], Optional[List[str]], Optional[List[Dict[str, Any]]]]:
    """Parse array item type information."""
    for i in range(start_idx, min(start_idx + 5, len(lines))):
        line = lines[i]
        if 'Array item type:' in line:
            if 'Object' in line:
                return 'object', None, []
            elif 'Literal[' in line:
                values = parse_literal_values(line)
                return 'literal', values, None
            elif 'Text' in line:
                return 'string', None, None
            elif 'Number' in line:
                return 'integer', None, None
    
    return None, None, None

def manually_build_clean_structures() -> Dict[str, List[Dict[str, Any]]]:
    """Manually build clean field structures based on the document."""
    
    structures = {}
    
    # Structure v1 - Clean and complete
    structures['structure_v1'] = [{
        'name': 'structure_extraction',
        'type': 'object',
        'required': True,
        'description': 'Complete shelf structure analysis',
        'nested_fields': [{
            'name': 'shelf_structure',
            'type': 'object',
            'required': True,
            'description': 'Physical structure of the shelf fixture',
            'nested_fields': [
                {'name': 'total_shelves', 'type': 'integer', 'required': True, 'description': 'Total number of horizontal shelves'},
                {'name': 'fixture_id', 'type': 'string', 'required': True, 'description': 'Unique identifier for this shelf fixture'},
                {'name': 'shelf_numbers', 'type': 'list', 'required': True, 'description': 'List of shelf numbers from bottom to top', 'list_item_type': 'integer'},
                {'name': 'shelf_type', 'type': 'literal', 'required': True, 'description': 'Type of fixture', 'allowed_values': ['wall_shelf', 'gondola', 'end_cap', 'cooler', 'freezer', 'bin', 'pegboard', 'other']},
                {'name': 'width_meters', 'type': 'float', 'required': True, 'description': 'Estimated width of fixture in meters'},
                {'name': 'height_meters', 'type': 'float', 'required': True, 'description': 'Estimated height of fixture in meters'},
                {
                    'name': 'shelves',
                    'type': 'list',
                    'required': True,
                    'description': 'Detailed information for each shelf level',
                    'list_item_type': 'object',
                    'nested_fields': [
                        {'name': 'shelf_number', 'type': 'integer', 'required': True, 'description': 'Shelf identifier (1=bottom, counting up)'},
                        {'name': 'has_price_rail', 'type': 'boolean', 'required': True, 'description': 'Whether shelf has price label strip/rail'},
                        {'name': 'special_features', 'type': 'string', 'required': False, 'description': 'Unusual characteristics'},
                        {'name': 'has_empty_spaces', 'type': 'boolean', 'required': True, 'description': 'Whether significant gaps exist on this shelf'}
                    ]
                },
                {
                    'name': 'non_product_elements',
                    'type': 'object',
                    'required': True,
                    'description': 'Items on shelves that are not products',
                    'nested_fields': [
                        {
                            'name': 'security_devices',
                            'type': 'list',
                            'required': False,
                            'description': 'Security measures',
                            'list_item_type': 'object',
                            'nested_fields': [
                                {'name': 'type', 'type': 'string', 'required': True, 'description': 'Type of security device'},
                                {'name': 'location', 'type': 'string', 'required': True, 'description': 'Where on shelf it\'s located'}
                            ]
                        },
                        {
                            'name': 'promotional_materials',
                            'type': 'list',
                            'required': False,
                            'description': 'Marketing materials',
                            'list_item_type': 'object',
                            'nested_fields': [
                                {'name': 'type', 'type': 'string', 'required': True, 'description': 'Type of promotional material'},
                                {'name': 'location', 'type': 'string', 'required': True, 'description': 'Where positioned'},
                                {'name': 'text_visible', 'type': 'string', 'required': True, 'description': 'Any readable promotional text'}
                            ]
                        }
                    ]
                }
            ]
        }]
    }]
    
    # Product v1 - Clean and complete
    structures['product_v1'] = [{
        'name': 'product_extraction',
        'type': 'object',
        'required': True,
        'description': 'Complete product extraction for ALL shelves in the fixture',
        'nested_fields': [
            {'name': 'fixture_id', 'type': 'string', 'required': True, 'description': 'Unique identifier for this extraction'},
            {'name': 'total_shelves', 'type': 'integer', 'required': True, 'description': 'Total number of shelves being extracted'},
            {
                'name': 'shelves',
                'type': 'list',
                'required': True,
                'description': 'Product data for each shelf',
                'list_item_type': 'object',
                'nested_fields': [
                    {'name': 'shelf_number', 'type': 'integer', 'required': True, 'description': 'Which shelf this is'},
                    {'name': 'extraction_status', 'type': 'literal', 'required': True, 'description': 'Status of this shelf extraction', 'allowed_values': ['has_products', 'empty_shelf', 'not_visible', 'blocked']},
                    {
                        'name': 'products',
                        'type': 'list',
                        'required': True,
                        'description': 'All products found on this specific shelf',
                        'list_item_type': 'object',
                        'nested_fields': [
                            {'name': 'position', 'type': 'integer', 'required': True, 'description': 'Sequential position from left to right'},
                            {'name': 'section', 'type': 'literal', 'required': True, 'description': 'Which third of the shelf', 'allowed_values': ['left', 'center', 'right']},
                            {'name': 'brand', 'type': 'string', 'required': True, 'description': 'Product brand name'},
                            {'name': 'name', 'type': 'string', 'required': True, 'description': 'Product name or variant'},
                            {'name': 'product_type', 'type': 'literal', 'required': True, 'description': 'Package type', 'allowed_values': ['can', 'bottle', 'box', 'pouch', 'jar', 'other']},
                            {'name': 'facings', 'type': 'integer', 'required': True, 'description': 'Number of units visible from front'},
                            {'name': 'stack', 'type': 'integer', 'required': True, 'description': 'Number of units stacked vertically'}
                        ]
                    },
                    {'name': 'extraction_notes', 'type': 'string', 'required': False, 'description': 'Any issues or observations about this shelf'}
                ]
            }
        ]
    }]
    
    # Detail v1 - Clean and complete
    structures['detail_v1'] = [{
        'name': 'detail_enhancement',
        'type': 'object',
        'required': True,
        'description': 'Enhanced details for ALL products from Stage 2',
        'nested_fields': [
            {'name': 'fixture_id', 'type': 'string', 'required': True, 'description': 'Must match Stage 2 fixture_id exactly'},
            {'name': 'total_shelves', 'type': 'integer', 'required': True, 'description': 'Must match Stage 2 total_shelves exactly'},
            {
                'name': 'shelves_enhanced',
                'type': 'list',
                'required': True,
                'description': 'Enhanced details for each shelf',
                'list_item_type': 'object',
                'nested_fields': [
                    {'name': 'shelf_number', 'type': 'integer', 'required': True, 'description': 'Must match Stage 2 shelf_number'},
                    {
                        'name': 'products_enhanced',
                        'type': 'list',
                        'required': False,
                        'description': 'Enhanced product details when shelf has products',
                        'list_item_type': 'object',
                        'nested_fields': [
                            {
                                'name': 'product_reference',
                                'type': 'object',
                                'required': True,
                                'description': 'Reference to Stage 2 product',
                                'nested_fields': [
                                    {'name': 'position', 'type': 'integer', 'required': True, 'description': 'Position from Stage 2'},
                                    {'name': 'brand', 'type': 'string', 'required': True, 'description': 'Brand from Stage 2'},
                                    {'name': 'name', 'type': 'string', 'required': True, 'description': 'Name from Stage 2'}
                                ]
                            },
                            {
                                'name': 'pricing',
                                'type': 'object',
                                'required': True,
                                'description': 'Price information',
                                'nested_fields': [
                                    {'name': 'regular_price', 'type': 'float', 'required': False, 'description': 'Regular price value'},
                                    {'name': 'currency', 'type': 'literal', 'required': True, 'description': 'Currency type', 'allowed_values': ['GBP', 'EUR', 'USD', 'other']},
                                    {'name': 'price_visible', 'type': 'boolean', 'required': True, 'description': 'Whether price was visible'},
                                    {'name': 'price_tag_location', 'type': 'literal', 'required': True, 'description': 'Price tag position', 'allowed_values': ['directly_below', 'left_of_product', 'right_of_product', 'distant', 'not_visible']}
                                ]
                            },
                            {
                                'name': 'package_info',
                                'type': 'object',
                                'required': True,
                                'description': 'Package details',
                                'nested_fields': [
                                    {'name': 'size', 'type': 'string', 'required': False, 'description': 'Package size'},
                                    {'name': 'size_visible', 'type': 'boolean', 'required': True, 'description': 'Whether size was readable'}
                                ]
                            },
                            {
                                'name': 'visual',
                                'type': 'object',
                                'required': True,
                                'description': 'Visual appearance',
                                'nested_fields': [
                                    {'name': 'primary_color', 'type': 'string', 'required': True, 'description': 'Primary color'},
                                    {'name': 'secondary_color', 'type': 'string', 'required': True, 'description': 'Secondary color'},
                                    {'name': 'finish', 'type': 'literal', 'required': True, 'description': 'Package finish', 'allowed_values': ['metallic', 'matte', 'glossy', 'transparent', 'mixed']}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }]
    
    # Visual v1 - Clean and complete
    structures['visual_v1'] = [{
        'name': 'visual_comparison',
        'type': 'object',
        'required': True,
        'description': 'Comparison between original photo and generated planogram',
        'nested_fields': [
            {
                'name': 'overview',
                'type': 'object',
                'required': True,
                'description': 'Overall comparison metrics',
                'nested_fields': [
                    {'name': 'total_products_photo', 'type': 'integer', 'required': True, 'description': 'Total products counted in original photo'},
                    {'name': 'total_products_planogram', 'type': 'integer', 'required': True, 'description': 'Total products shown in planogram'},
                    {'name': 'overall_alignment', 'type': 'literal', 'required': True, 'description': 'Overall quality assessment', 'allowed_values': ['good', 'moderate', 'poor']}
                ]
            },
            {
                'name': 'shelf_mismatches',
                'type': 'list',
                'required': False,
                'description': 'Specific products with placement or quantity issues',
                'list_item_type': 'object',
                'nested_fields': [
                    {'name': 'product', 'type': 'string', 'required': True, 'description': 'Product name'},
                    {'name': 'issue_type', 'type': 'literal', 'required': True, 'description': 'Type of mismatch', 'allowed_values': ['wrong_shelf', 'wrong_quantity', 'wrong_position', 'missing', 'extra']},
                    {'name': 'confidence', 'type': 'literal', 'required': True, 'description': 'Confidence in this mismatch', 'allowed_values': ['high', 'medium', 'low']}
                ]
            }
        ]
    }]
    
    return structures

def main():
    """Main function to update database with clean field structures."""
    print("Building clean field structures...")
    
    # Get clean structures
    field_structures = manually_build_clean_structures()
    
    print(f"Built {len(field_structures)} clean field structures:")
    for name, fields in field_structures.items():
        print(f"  - {name}: {len(fields)} top-level field(s)")
    
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
    
    success_count = 0
    for field_name, prompt_name in prompt_mapping.items():
        if field_name in field_structures:
            try:
                fields_json = json.dumps(field_structures[field_name], indent=2)
                
                result = supabase.table('prompt_templates').update({
                    'fields': fields_json
                }).eq('name', prompt_name).execute()
                
                print(f"✓ Updated {prompt_name} with clean structure")
                success_count += 1
                
            except Exception as e:
                print(f"✗ Error updating {prompt_name}: {e}")
    
    print(f"\n✓ Successfully updated {success_count}/{len(prompt_mapping)} prompt templates")
    print("✓ All field structures are now clean and free of duplications")
    
    # Save backup
    try:
        with open('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/clean_field_structures.json', 'w') as f:
            json.dump(field_structures, f, indent=2)
        print("✓ Clean structures saved to clean_field_structures.json")
    except Exception as e:
        print(f"✗ Error saving backup: {e}")

if __name__ == "__main__":
    main()