#!/usr/bin/env python3
"""
Update field_definitions in the database based on the agreed "OnShelf AI Extraction Prompts - Refined Complete Set" document.
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

# Define the correct field definitions based on the agreed document
# These will be stored in the field_definitions column as JSON

FIELD_DEFINITIONS = {
    "structure": [
        {
            "name": "shelves",
            "type": "array",
            "required": True,
            "description": "Array of shelf objects in the fixture",
            "items": {
                "type": "object",
                "properties": {
                    "shelf_number": {"type": "integer", "description": "Shelf number counting from top (1) to bottom"},
                    "height_cm": {"type": "number", "description": "Estimated height of the shelf in centimeters"},
                    "width_cm": {"type": "number", "description": "Estimated width of the shelf in centimeters"},
                    "depth_cm": {"type": "number", "description": "Estimated depth of the shelf in centimeters"},
                    "is_divided": {"type": "boolean", "description": "Whether the shelf has vertical dividers"},
                    "sections": {
                        "type": "array",
                        "description": "Array of sections if shelf is divided",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section_number": {"type": "integer", "description": "Section number from left to right"},
                                "width_cm": {"type": "number", "description": "Width of this section"},
                                "has_products": {"type": "boolean", "description": "Whether this section contains products"}
                            }
                        }
                    },
                    "rail_type": {"type": "string", "enum": ["none", "standard", "gravity_feed", "push_system"], "description": "Type of rail or product feeding system"}
                }
            }
        },
        {
            "name": "total_height_cm",
            "type": "number",
            "required": True,
            "description": "Total height of the shelving unit"
        },
        {
            "name": "total_width_cm",
            "type": "number",
            "required": True,
            "description": "Total width of the shelving unit"
        },
        {
            "name": "fixture_type",
            "type": "string",
            "required": True,
            "description": "Type of shelving fixture (e.g., 'gondola', 'wall unit', 'end cap')"
        },
        {
            "name": "metadata",
            "type": "object",
            "required": False,
            "description": "Additional metadata about the fixture",
            "properties": {
                "lighting_type": {"type": "string", "description": "Type of lighting (e.g., 'overhead', 'under-shelf', 'none')"},
                "material": {"type": "string", "description": "Shelf material (e.g., 'metal', 'wood', 'wire')"},
                "condition": {"type": "string", "description": "Overall condition (e.g., 'good', 'worn', 'damaged')"}
            }
        }
    ],
    
    "products": [
        {
            "name": "products",
            "type": "array",
            "required": True,
            "description": "Array of product objects found on shelves",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Unique identifier for this product instance"},
                    "shelf_number": {"type": "integer", "description": "Which shelf the product is on (1 = top)"},
                    "section_number": {"type": "integer", "description": "Which section of the shelf (1 = leftmost)"},
                    "position_in_section": {"type": "integer", "description": "Position within the section (1 = leftmost)"},
                    "position_x_cm": {"type": "number", "description": "Horizontal position from left edge of shelf in cm"},
                    "position_y_cm": {"type": "number", "description": "Vertical position from top of shelf in cm"},
                    "facing_count": {"type": "integer", "description": "Number of product facings visible"},
                    "product_name": {"type": "string", "description": "Product name visible on packaging"},
                    "brand": {"type": "string", "description": "Brand name if visible"},
                    "size": {"type": "string", "description": "Product size/weight if visible"},
                    "upc": {"type": "string", "description": "UPC code if visible"},
                    "price": {"type": "string", "description": "Price if visible on shelf tag"},
                    "orientation": {"type": "string", "enum": ["front", "side", "back", "angled"], "description": "How the product is facing"}
                }
            }
        },
        {
            "name": "total_products",
            "type": "integer",
            "required": True,
            "description": "Total number of unique products identified"
        },
        {
            "name": "total_facings",
            "type": "integer",
            "required": True,
            "description": "Total number of product facings across all products"
        }
    ],
    
    "position": [
        {
            "name": "products",
            "type": "array",
            "required": True,
            "description": "Array of products with precise positioning data",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Unique identifier matching products extraction"},
                    "shelf_number": {"type": "integer", "description": "Shelf number from top to bottom"},
                    "section_number": {"type": "integer", "description": "Section number from left to right"},
                    "position_in_section": {"type": "integer", "description": "Position within section from left"},
                    "position_x_cm": {"type": "number", "description": "Precise horizontal position from left edge"},
                    "position_y_cm": {"type": "number", "description": "Precise vertical position from shelf top"},
                    "width_cm": {"type": "number", "description": "Product width on shelf"},
                    "height_cm": {"type": "number", "description": "Product height"},
                    "depth_cm": {"type": "number", "description": "Product depth if determinable"},
                    "facing_count": {"type": "integer", "description": "Number of facings"},
                    "stacking": {
                        "type": "object",
                        "properties": {
                            "is_stacked": {"type": "boolean", "description": "Whether products are stacked"},
                            "stack_count": {"type": "integer", "description": "Number in stack if stacked"},
                            "stack_orientation": {"type": "string", "enum": ["vertical", "horizontal", "none"]}
                        }
                    },
                    "adjacency": {
                        "type": "object",
                        "properties": {
                            "left_product_id": {"type": "string", "nullable": True},
                            "right_product_id": {"type": "string", "nullable": True},
                            "above_product_id": {"type": "string", "nullable": True},
                            "below_product_id": {"type": "string", "nullable": True}
                        }
                    }
                }
            }
        },
        {
            "name": "shelf_occupancy",
            "type": "array",
            "required": True,
            "description": "Occupancy data for each shelf",
            "items": {
                "type": "object",
                "properties": {
                    "shelf_number": {"type": "integer"},
                    "total_width_cm": {"type": "number"},
                    "used_width_cm": {"type": "number"},
                    "occupancy_percentage": {"type": "number"}
                }
            }
        }
    ],
    
    "detail": [
        {
            "name": "products",
            "type": "array",
            "required": True,
            "description": "Array of products with detailed information",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Matching ID from products extraction"},
                    "product_name": {"type": "string", "description": "Full product name"},
                    "brand": {"type": "string", "description": "Brand name"},
                    "manufacturer": {"type": "string", "description": "Manufacturer if different from brand"},
                    "category": {"type": "string", "description": "Product category"},
                    "subcategory": {"type": "string", "description": "Product subcategory"},
                    "size": {"type": "string", "description": "Package size"},
                    "unit_of_measure": {"type": "string", "description": "Unit (oz, ml, count, etc.)"},
                    "upc": {"type": "string", "description": "UPC code if visible"},
                    "sku": {"type": "string", "description": "SKU if visible on tag"},
                    "price": {
                        "type": "object",
                        "properties": {
                            "regular_price": {"type": "number", "description": "Regular price"},
                            "sale_price": {"type": "number", "nullable": True, "description": "Sale price if on sale"},
                            "unit_price": {"type": "string", "description": "Price per unit if shown"},
                            "currency": {"type": "string", "default": "USD"}
                        }
                    },
                    "packaging": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "description": "Package type (box, bottle, can, etc.)"},
                            "material": {"type": "string", "description": "Package material if identifiable"},
                            "colors": {"type": "array", "items": {"type": "string"}, "description": "Main package colors"},
                            "shape": {"type": "string", "description": "Package shape"}
                        }
                    },
                    "visual_attributes": {
                        "type": "object",
                        "properties": {
                            "logo_visible": {"type": "boolean"},
                            "promotional_tags": {"type": "array", "items": {"type": "string"}},
                            "shelf_tag_color": {"type": "string"},
                            "condition": {"type": "string", "enum": ["perfect", "good", "damaged", "obscured"]}
                        }
                    }
                }
            }
        }
    ],
    
    "validation": [
        {
            "name": "overall_accuracy",
            "type": "number",
            "required": True,
            "description": "Overall accuracy percentage (0-100)"
        },
        {
            "name": "structure_validation",
            "type": "object",
            "required": True,
            "description": "Validation results for shelf structure",
            "properties": {
                "shelf_count_correct": {"type": "boolean"},
                "dimensions_reasonable": {"type": "boolean"},
                "issues": {"type": "array", "items": {"type": "string"}}
            }
        },
        {
            "name": "product_validation",
            "type": "object",
            "required": True,
            "description": "Validation results for product extraction",
            "properties": {
                "product_count_reasonable": {"type": "boolean"},
                "positions_logical": {"type": "boolean"},
                "no_overlaps": {"type": "boolean"},
                "issues": {"type": "array", "items": {"type": "string"}}
            }
        },
        {
            "name": "visual_comparison",
            "type": "object",
            "required": True,
            "description": "Results of visual comparison with original image",
            "properties": {
                "layout_matches": {"type": "boolean"},
                "products_correctly_placed": {"type": "boolean"},
                "density_appropriate": {"type": "boolean"},
                "notes": {"type": "string"}
            }
        },
        {
            "name": "recommendations",
            "type": "array",
            "required": False,
            "description": "Suggestions for improving extraction accuracy",
            "items": {"type": "string"}
        }
    ]
}

def update_field_definitions():
    """Update the database with correct field definitions."""
    
    # Define which prompts should have field definitions
    prompts_with_definitions = {
        "structure": "Initial prompt for extracting shelf physical structure with Pydantic schema",
        "products": "Initial extraction of all products visible on shelves",
        "position": "Extract products with planogram context explanation",
        "detail": "Extract detailed product information for all identified products",
        "validation": "Compare generated planogram with original shelf photo for validation"
    }
    
    for prompt_type, field_defs in FIELD_DEFINITIONS.items():
        print(f"\nUpdating field definitions for prompt type: {prompt_type}")
        
        try:
            # First, check if the prompt exists
            response = supabase.table('prompt_templates').select('*').eq('prompt_type', prompt_type).execute()
            
            if not response.data:
                print(f"  - No prompt found for type '{prompt_type}', skipping...")
                continue
            
            # If multiple prompts exist, we'll update the one with the matching description or the first one
            prompt_to_update = None
            if prompt_type in prompts_with_definitions:
                for prompt in response.data:
                    if prompts_with_definitions[prompt_type] in (prompt.get('description') or ''):
                        prompt_to_update = prompt
                        break
            
            if not prompt_to_update:
                prompt_to_update = response.data[0]  # Default to first one
            
            # Update with the correct field definitions
            update_response = supabase.table('prompt_templates').update({
                'field_definitions': field_defs
            }).eq('prompt_id', prompt_to_update['prompt_id']).execute()
            
            print(f"  - Updated field definitions for prompt ID {prompt_to_update['prompt_id']}")
            
            # If there are duplicates, log them
            if len(response.data) > 1:
                print(f"  - Warning: Found {len(response.data)} prompts for type '{prompt_type}'")
                for i, prompt in enumerate(response.data):
                    print(f"    {i+1}. ID: {prompt['prompt_id']}, Description: {prompt.get('description', 'No description')}")
            
        except Exception as e:
            print(f"  - Error updating prompt type '{prompt_type}': {e}")
    
    print("\n\nField definitions update complete!")
    
    # Verify the updates
    print("\nVerifying updates...")
    response = supabase.table('prompt_templates').select('prompt_type, description, field_definitions').order('prompt_type').execute()
    
    for prompt in response.data:
        if prompt.get('field_definitions'):
            print(f"\n✓ {prompt['prompt_type']} - Has {len(prompt['field_definitions'])} field definitions")
        else:
            print(f"\n✗ {prompt['prompt_type']} - No field definitions")

if __name__ == "__main__":
    update_field_definitions()