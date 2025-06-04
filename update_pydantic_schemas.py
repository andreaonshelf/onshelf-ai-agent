#!/usr/bin/env python3
"""
Update Pydantic schemas in the database based on the agreed "OnShelf AI Extraction Prompts - Refined Complete Set" document.
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

# Define the correct Pydantic schemas based on the agreed document
PYDANTIC_SCHEMAS = {
    "structure": {
        "type": "object",
        "properties": {
            "shelves": {
                "type": "array",
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
                            "items": {
                                "type": "object",
                                "properties": {
                                    "section_number": {"type": "integer", "description": "Section number from left to right"},
                                    "width_cm": {"type": "number", "description": "Width of this section"},
                                    "has_products": {"type": "boolean", "description": "Whether this section contains products"}
                                },
                                "required": ["section_number", "width_cm", "has_products"]
                            }
                        },
                        "rail_type": {"type": "string", "enum": ["none", "standard", "gravity_feed", "push_system"], "description": "Type of rail or product feeding system"}
                    },
                    "required": ["shelf_number", "height_cm", "width_cm", "is_divided", "rail_type"]
                }
            },
            "total_height_cm": {"type": "number", "description": "Total height of the shelving unit"},
            "total_width_cm": {"type": "number", "description": "Total width of the shelving unit"},
            "fixture_type": {"type": "string", "description": "Type of shelving fixture (e.g., 'gondola', 'wall unit', 'end cap')"},
            "metadata": {
                "type": "object",
                "properties": {
                    "lighting_type": {"type": "string", "description": "Type of lighting (e.g., 'overhead', 'under-shelf', 'none')"},
                    "material": {"type": "string", "description": "Shelf material (e.g., 'metal', 'wood', 'wire')"},
                    "condition": {"type": "string", "description": "Overall condition (e.g., 'good', 'worn', 'damaged')"}
                }
            }
        },
        "required": ["shelves", "total_height_cm", "total_width_cm", "fixture_type"]
    },
    
    "products": {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
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
                    },
                    "required": ["product_id", "shelf_number", "position_x_cm", "facing_count"]
                }
            },
            "total_products": {"type": "integer", "description": "Total number of unique products identified"},
            "total_facings": {"type": "integer", "description": "Total number of product facings across all products"}
        },
        "required": ["products", "total_products", "total_facings"]
    },
    
    "position": {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
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
                    },
                    "required": ["product_id", "shelf_number", "position_x_cm", "position_y_cm", "width_cm", "height_cm", "facing_count"]
                }
            },
            "shelf_occupancy": {
                "type": "array",
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
        },
        "required": ["products", "shelf_occupancy"]
    },
    
    "detail": {
        "type": "object",
        "properties": {
            "products": {
                "type": "array",
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
                    },
                    "required": ["product_id", "product_name", "brand", "category", "size"]
                }
            }
        },
        "required": ["products"]
    },
    
    "validation": {
        "type": "object",
        "properties": {
            "overall_accuracy": {"type": "number", "minimum": 0, "maximum": 100, "description": "Overall accuracy percentage"},
            "structure_validation": {
                "type": "object",
                "properties": {
                    "shelf_count_correct": {"type": "boolean"},
                    "dimensions_reasonable": {"type": "boolean"},
                    "issues": {"type": "array", "items": {"type": "string"}}
                }
            },
            "product_validation": {
                "type": "object",
                "properties": {
                    "product_count_reasonable": {"type": "boolean"},
                    "positions_logical": {"type": "boolean"},
                    "no_overlaps": {"type": "boolean"},
                    "issues": {"type": "array", "items": {"type": "string"}}
                }
            },
            "visual_comparison": {
                "type": "object",
                "properties": {
                    "layout_matches": {"type": "boolean"},
                    "products_correctly_placed": {"type": "boolean"},
                    "density_appropriate": {"type": "boolean"},
                    "notes": {"type": "string"}
                }
            },
            "recommendations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Suggestions for improving extraction accuracy"
            }
        },
        "required": ["overall_accuracy", "structure_validation", "product_validation", "visual_comparison"]
    }
}

def update_schemas():
    """Update the database with correct Pydantic schemas."""
    
    # First, let's clean up duplicates and ensure we have the right prompts
    print("Cleaning up duplicate prompts...")
    
    # Define which prompts should have schemas
    prompts_with_schemas = {
        "structure": "Initial prompt for extracting shelf physical structure with Pydantic schema",
        "products": "Initial extraction of all products visible on shelves",
        "position": "Extract products with planogram context explanation",
        "detail": "Extract detailed product information for all identified products",
        "validation": "Compare generated planogram with original shelf photo for validation"
    }
    
    for prompt_type, schema in PYDANTIC_SCHEMAS.items():
        print(f"\nUpdating schema for prompt type: {prompt_type}")
        
        try:
            # First, check if the prompt exists
            response = supabase.table('prompt_templates').select('*').eq('prompt_type', prompt_type).execute()
            
            if not response.data:
                print(f"  - No prompt found for type '{prompt_type}', skipping...")
                continue
            
            # If multiple prompts exist, we'll update the one with the matching description or the first one
            prompt_to_update = None
            if prompt_type in prompts_with_schemas:
                for prompt in response.data:
                    if prompts_with_schemas[prompt_type] in (prompt.get('description') or ''):
                        prompt_to_update = prompt
                        break
            
            if not prompt_to_update:
                prompt_to_update = response.data[0]  # Default to first one
            
            # Update with the correct schema
            update_response = supabase.table('prompt_templates').update({
                'pydantic_schema': json.dumps(schema)
            }).eq('id', prompt_to_update['id']).execute()
            
            print(f"  - Updated schema for prompt ID {prompt_to_update['id']}")
            
            # If there are duplicates, log them
            if len(response.data) > 1:
                print(f"  - Warning: Found {len(response.data)} prompts for type '{prompt_type}'")
                for i, prompt in enumerate(response.data):
                    print(f"    {i+1}. ID: {prompt['id']}, Description: {prompt.get('description', 'No description')}")
            
        except Exception as e:
            print(f"  - Error updating prompt type '{prompt_type}': {e}")
    
    print("\n\nSchema update complete!")
    
    # Verify the updates
    print("\nVerifying updates...")
    response = supabase.table('prompt_templates').select('prompt_type, description, pydantic_schema').order('prompt_type').execute()
    
    for prompt in response.data:
        if prompt.get('pydantic_schema'):
            print(f"\n✓ {prompt['prompt_type']} - Has schema")
        else:
            print(f"\n✗ {prompt['prompt_type']} - No schema")

if __name__ == "__main__":
    update_schemas()