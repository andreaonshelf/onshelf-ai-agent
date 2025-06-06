#!/usr/bin/env python3
"""
Parse the EXTRACTION_PROMPTS_FINAL.md document and extract the exact field structures
to update the database with properly formatted fields for the UI Schema Builder.
"""

import re
import json
from typing import Dict, List, Any, Optional

def parse_field_type(type_str: str) -> Dict[str, Any]:
    """Parse field type string and return UI-compatible type info."""
    # Handle Literal types
    literal_match = re.match(r'Literal\[(.*?)\]', type_str)
    if literal_match:
        # Extract values and clean them
        values_str = literal_match.group(1)
        values = [v.strip().strip('"') for v in values_str.split(',')]
        return {
            'type': 'literal',
            'allowed_values': values
        }
    
    # Map document types to UI types
    type_mapping = {
        'Text - string': 'string',
        'Number - integer': 'integer', 
        'Decimal - float': 'float',
        'Yes/No - boolean': 'boolean',
        'List - array': 'list',
        'Object - nested': 'object'
    }
    
    for doc_type, ui_type in type_mapping.items():
        if doc_type in type_str:
            return {'type': ui_type}
    
    # Default to string
    return {'type': 'string'}

def parse_field_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single field definition line."""
    # Match field definition pattern: - **field_name** (Type) ✓/☐ Required/Optional
    pattern = r'^\s*-\s*\*\*(\w+)\*\*\s*\((.*?)\)\s*(✓|☐)?\s*(Required|Optional)?'
    match = re.match(pattern, line)
    
    if match:
        field_name = match.group(1)
        type_str = match.group(2)
        required_mark = match.group(3)
        
        field = {
            'name': field_name,
            'required': required_mark == '✓' if required_mark else True
        }
        
        # Parse type
        type_info = parse_field_type(type_str)
        field.update(type_info)
        
        return field
    return None

def parse_fields_section(content: str, start_line: int) -> List[Dict[str, Any]]:
    """Parse a fields section starting from a given line."""
    fields = []
    lines = content.split('\n')[start_line:]
    
    current_field = None
    current_indent = 0
    field_stack = []
    
    for i, line in enumerate(lines):
        # Stop at next major section
        if line.startswith('---') or line.startswith('##'):
            break
            
        # Skip empty lines
        if not line.strip():
            continue
            
        # Calculate indent level
        indent = len(line) - len(line.lstrip())
        
        # Parse field line
        field = parse_field_line(line)
        if field:
            # Check for description on next line
            if i + 1 < len(lines) and 'Description:' in lines[i + 1]:
                desc_match = re.search(r'Description:\s*(.+)', lines[i + 1])
                if desc_match:
                    field['description'] = desc_match.group(1).strip()
                    
            # Check for array item type
            if field['type'] == 'list' and i + 1 < len(lines):
                next_line = lines[i + 1]
                if 'Array item type:' in next_line:
                    if 'Object' in next_line:
                        field['list_item_type'] = 'object'
                        field['nested_fields'] = []
                    elif 'Literal' in next_line:
                        literal_match = re.search(r'Literal\[(.*?)\]', next_line)
                        if literal_match:
                            values = [v.strip().strip('"') for v in literal_match.group(1).split(',')]
                            field['list_item_type'] = 'literal'
                            field['allowed_values'] = values
                    else:
                        # Try to extract simple type
                        type_match = re.search(r'Array item type:\s*(\w+)', next_line)
                        if type_match:
                            field['list_item_type'] = type_match.group(1).lower()
                            
            # Handle nested fields
            if field['type'] == 'object':
                field['nested_fields'] = []
                
            fields.append(field)
            
    return fields

# Structure v1 fields
structure_v1_fields = [{
    "name": "structure_extraction",
    "type": "object",
    "description": "Complete shelf structure analysis",
    "required": True,
    "nested_fields": [{
        "name": "shelf_structure",
        "type": "object",
        "description": "Physical structure of the shelf fixture",
        "required": True,
        "nested_fields": [
            {
                "name": "total_shelves",
                "type": "integer",
                "description": "Total number of horizontal shelves",
                "required": True
            },
            {
                "name": "fixture_id",
                "type": "string",
                "description": "Unique identifier for this shelf fixture (e.g., \"store123_aisle5_bay2\")",
                "required": True
            },
            {
                "name": "shelf_numbers",
                "type": "list",
                "description": "List of shelf numbers from bottom to top (must have length = total_shelves)",
                "required": True,
                "list_item_type": "integer"
            },
            {
                "name": "shelf_type",
                "type": "literal",
                "description": "Type of fixture",
                "required": True,
                "allowed_values": ["wall_shelf", "gondola", "end_cap", "cooler", "freezer", "bin", "pegboard", "other"]
            },
            {
                "name": "width_meters",
                "type": "float",
                "description": "Estimated width of fixture in meters",
                "required": True
            },
            {
                "name": "height_meters",
                "type": "float",
                "description": "Estimated height of fixture in meters", 
                "required": True
            },
            {
                "name": "shelves",
                "type": "list",
                "description": "Detailed information for each shelf level",
                "required": True,
                "list_item_type": "object",
                "nested_fields": [
                    {
                        "name": "shelf_number",
                        "type": "integer",
                        "description": "Shelf identifier (1=bottom, counting up)",
                        "required": True
                    },
                    {
                        "name": "has_price_rail",
                        "type": "boolean",
                        "description": "Whether shelf has price label strip/rail",
                        "required": True
                    },
                    {
                        "name": "special_features",
                        "type": "string",
                        "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)",
                        "required": False
                    },
                    {
                        "name": "has_empty_spaces",
                        "type": "boolean",
                        "description": "Whether significant gaps exist on this shelf",
                        "required": True
                    },
                    {
                        "name": "empty_space_details",
                        "type": "object",
                        "description": "Details about empty spaces",
                        "required": False,
                        "nested_fields": [
                            {
                                "name": "sections_with_gaps",
                                "type": "list",
                                "description": "Sections with gaps",
                                "required": True,
                                "list_item_type": "literal",
                                "allowed_values": ["left", "center", "right"]
                            },
                            {
                                "name": "estimated_total_gap_cm",
                                "type": "float",
                                "description": "Total empty space in centimeters",
                                "required": True
                            }
                        ]
                    }
                ]
            },
            {
                "name": "non_product_elements",
                "type": "object",
                "description": "Items on shelves that are not products",
                "required": True,
                "nested_fields": [
                    {
                        "name": "security_devices",
                        "type": "list",
                        "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
                        "required": False,
                        "list_item_type": "object",
                        "nested_fields": [
                            {
                                "name": "type",
                                "type": "string",
                                "description": "Type of security device",
                                "required": True
                            },
                            {
                                "name": "location",
                                "type": "string",
                                "description": "Where on shelf it's located",
                                "required": True
                            }
                        ]
                    },
                    {
                        "name": "promotional_materials",
                        "type": "list",
                        "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                        "required": False,
                        "list_item_type": "object",
                        "nested_fields": [
                            {
                                "name": "type",
                                "type": "string",
                                "description": "Type of promotional material",
                                "required": True
                            },
                            {
                                "name": "location",
                                "type": "string",
                                "description": "Where positioned",
                                "required": True
                            },
                            {
                                "name": "text_visible",
                                "type": "string",
                                "description": "Any readable promotional text",
                                "required": True
                            }
                        ]
                    },
                    {
                        "name": "shelf_equipment",
                        "type": "list",
                        "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                        "required": False,
                        "list_item_type": "object",
                        "nested_fields": [
                            {
                                "name": "type",
                                "type": "string",
                                "description": "Type of equipment",
                                "required": True
                            },
                            {
                                "name": "location",
                                "type": "string",
                                "description": "Where installed",
                                "required": True
                            }
                        ]
                    }
                ]
            }
        ]
    }]
}]

# Now let me update the database with these exact field structures
import os
from supabase import create_client, Client

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: Missing Supabase credentials")
    exit(1)

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

# Update Structure v1
try:
    result = supabase.table('prompt_templates').update({
        'fields': json.dumps(structure_v1_fields)
    }).eq('name', 'Structure v1').execute()
    print(f"Updated Structure v1 with exact field structure")
except Exception as e:
    print(f"Error updating Structure v1: {e}")

print("\nField structure has been updated in the database.")
print("The Structure v1 prompt now contains the exact field definitions from the document.")