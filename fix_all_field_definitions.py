#!/usr/bin/env python3

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    exit(1)

supabase: Client = create_client(url, key)

# Complete field definitions as specified in the original instructions
FIELD_DEFINITIONS = {
    "structure_extraction_standard_v2": {
        "total_shelves": {
            "type": "integer",
            "description": "Total number of shelves visible in the planogram"
        },
        "shelves": {
            "type": "array",
            "description": "Array of shelf objects",
            "items": {
                "type": "object",
                "properties": {
                    "shelf_number": {
                        "type": "integer",
                        "description": "Shelf number from top (1) to bottom"
                    },
                    "has_price_rail": {
                        "type": "boolean",
                        "description": "Whether shelf has a visible price rail"
                    },
                    "special_features": {
                        "type": "array",
                        "description": "Special features like 'dividers', 'pushers', 'end caps'",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "non_product_elements": {
            "type": "object",
            "description": "Non-product elements in the planogram",
            "properties": {
                "security_devices": {
                    "type": "array",
                    "description": "Security devices with location",
                    "items": {"type": "string"}
                },
                "promotional_materials": {
                    "type": "array",
                    "description": "Promotional signage with location",
                    "items": {"type": "string"}
                },
                "shelf_equipment": {
                    "type": "array",
                    "description": "Equipment like dividers, pushers with location",
                    "items": {"type": "string"}
                },
                "empty_spaces": {
                    "type": "array",
                    "description": "Significant gaps or out-of-stock areas",
                    "items": {"type": "string"}
                }
            }
        }
    },
    "product_extraction_position_v2": {
        "products": {
            "type": "array",
            "description": "Array of product objects extracted from the planogram",
            "items": {
                "type": "object",
                "properties": {
                    "position_index": {
                        "type": "integer",
                        "description": "Product position from left to right, top to bottom (starts at 1)"
                    },
                    "shelf_number": {
                        "type": "integer",
                        "description": "Shelf number from top (1) to bottom"
                    },
                    "position_on_shelf": {
                        "type": "integer",
                        "description": "Position from left (1) to right on this shelf"
                    },
                    "brand": {
                        "type": "string",
                        "description": "Brand name if visible"
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Product name if visible"
                    },
                    "variant": {
                        "type": "string",
                        "description": "Flavor, scent, or variant if visible"
                    },
                    "size": {
                        "type": "string",
                        "description": "Size/volume/weight if visible"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of facings (identical products side by side)"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score 0-1 for this product identification"
                    },
                    "visibility_issues": {
                        "type": "array",
                        "description": "Issues like 'partially_hidden', 'blurry', 'too_small'",
                        "items": {"type": "string"}
                    }
                }
            }
        }
    },
    "detail_enhancement_category_v2": {
        "products": {
            "type": "array",
            "description": "Enhanced product details for category-specific extraction",
            "items": {
                "type": "object",
                "properties": {
                    "position_index": {
                        "type": "integer",
                        "description": "Matches position from previous extraction"
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category/type"
                    },
                    "subcategory": {
                        "type": "string",
                        "description": "Product subcategory if applicable"
                    },
                    "price": {
                        "type": "string",
                        "description": "Price if visible on price rail or product"
                    },
                    "promo_tag": {
                        "type": "string",
                        "description": "Promotional messaging if present"
                    },
                    "packaging_type": {
                        "type": "string",
                        "description": "Box, bottle, can, pouch, etc."
                    },
                    "special_attributes": {
                        "type": "array",
                        "description": "Organic, gluten-free, sugar-free, etc.",
                        "items": {"type": "string"}
                    },
                    "enhanced_confidence": {
                        "type": "number",
                        "description": "Updated confidence after enhancement"
                    }
                }
            }
        }
    },
    "planogram_summary": {
        "compliance_score": {
            "type": "number",
            "description": "Overall planogram compliance score 0-100"
        },
        "total_products": {
            "type": "integer",
            "description": "Total number of unique products"
        },
        "total_facings": {
            "type": "integer",
            "description": "Total number of product facings"
        },
        "out_of_stock_count": {
            "type": "integer",
            "description": "Number of OOS positions"
        },
        "category_distribution": {
            "type": "object",
            "description": "Distribution of products by category",
            "additionalProperties": {
                "type": "integer"
            }
        },
        "brand_distribution": {
            "type": "object",
            "description": "Distribution of facings by brand",
            "additionalProperties": {
                "type": "integer"
            }
        },
        "issues_found": {
            "type": "array",
            "description": "List of compliance or visibility issues",
            "items": {"type": "string"}
        }
    }
}

# Orchestrator prompts don't have structured fields, they use free-form user input
ORCHESTRATOR_FIELDS = {
    "user_instructions": {
        "type": "string",
        "description": "Custom extraction instructions from user"
    }
}

def update_prompt_fields():
    """Update all v2 prompts with complete field definitions"""
    
    # First check what's currently stored
    print("Checking current field definitions...")
    result = supabase.table("prompt_templates")\
        .select("template_id, name, fields")\
        .like("template_id", "%_v2")\
        .execute()
    
    print(f"\nFound {len(result.data)} v2 prompts to update")
    
    updates_made = 0
    
    for prompt in result.data:
        template_id = prompt['template_id']
        current_fields = prompt.get('fields') or {}
        
        # Determine which field definition to use
        if template_id in FIELD_DEFINITIONS:
            new_fields = FIELD_DEFINITIONS[template_id]
        elif "orchestrator" in template_id:
            new_fields = ORCHESTRATOR_FIELDS
        else:
            print(f"Warning: No field definition found for {template_id}")
            continue
        
        # Check if update is needed
        if json.dumps(current_fields, sort_keys=True) != json.dumps(new_fields, sort_keys=True):
            print(f"\nUpdating fields for: {template_id}")
            print(f"  Current fields: {list(current_fields.keys()) if current_fields else 'None'}")
            print(f"  New fields: {list(new_fields.keys())}")
            
            # Update the fields
            try:
                supabase.table("prompt_templates")\
                    .update({"fields": new_fields})\
                    .eq("template_id", template_id)\
                    .execute()
                updates_made += 1
                print(f"  ✓ Updated successfully")
            except Exception as e:
                print(f"  ✗ Error updating: {e}")
        else:
            print(f"\n{template_id} already has correct fields")
    
    print(f"\n{'='*60}")
    print(f"Summary: Updated {updates_made} prompts")
    
    # Verify the updates
    print(f"\n{'='*60}")
    print("Verifying updates...")
    
    result = supabase.table("prompt_templates")\
        .select("template_id, name, fields")\
        .eq("template_id", "structure_extraction_standard_v2")\
        .execute()
    
    if result.data:
        fields = result.data[0]['fields']
        print(f"\nstructure_extraction_standard_v2 now has fields:")
        print(json.dumps(fields, indent=2))

if __name__ == "__main__":
    update_prompt_fields()