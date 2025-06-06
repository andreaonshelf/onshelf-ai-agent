#!/usr/bin/env python3
"""
Update all v1 prompts with the EXACT field structures from EXTRACTION_PROMPTS_FINAL.md
"""

import json
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

# Product v1 fields - EXACT structure from document
product_v1_fields = [{
    "name": "product_extraction",
    "type": "object",
    "description": "Complete product extraction for ALL shelves in the fixture",
    "required": True,
    "nested_fields": [
        {
            "name": "fixture_id",
            "type": "string",
            "description": "Unique identifier for this extraction (e.g., \"store123_aisle5_bay2\")",
            "required": True
        },
        {
            "name": "total_shelves",
            "type": "integer",
            "description": "Total number of shelves being extracted (MUST equal {TOTAL_SHELVES} from Stage 1)",
            "required": True
        },
        {
            "name": "shelves",
            "type": "list",
            "description": "Product data for each shelf (MUST have exactly total_shelves entries)",
            "required": True,
            "list_item_type": "object",
            "nested_fields": [
                {
                    "name": "shelf_number",
                    "type": "integer",
                    "description": "Which shelf this is (MUST match position in array + 1)",
                    "required": True
                },
                {
                    "name": "extraction_status",
                    "type": "literal",
                    "description": "Status of this shelf extraction",
                    "required": True,
                    "allowed_values": ["has_products", "empty_shelf", "not_visible", "blocked"]
                },
                {
                    "name": "products",
                    "type": "list",
                    "description": "All products found on this specific shelf",
                    "required": False,
                    "list_item_type": "object",
                    "nested_fields": [
                        {
                            "name": "position",
                            "type": "integer",
                            "description": "Sequential position from left to right on THIS shelf",
                            "required": True
                        },
                        {
                            "name": "section",
                            "type": "literal",
                            "description": "Which third of the shelf this product is in",
                            "required": True,
                            "allowed_values": ["left", "center", "right"]
                        },
                        {
                            "name": "brand",
                            "type": "string",
                            "description": "Product brand name",
                            "required": True
                        },
                        {
                            "name": "name",
                            "type": "string",
                            "description": "Product name or variant",
                            "required": True
                        },
                        {
                            "name": "product_type",
                            "type": "literal",
                            "description": "Package type",
                            "required": True,
                            "allowed_values": ["can", "bottle", "box", "pouch", "jar", "other"]
                        },
                        {
                            "name": "facings",
                            "type": "integer",
                            "description": "Number of units visible from front",
                            "required": True
                        },
                        {
                            "name": "stack",
                            "type": "integer",
                            "description": "Number of units stacked vertically",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "gaps",
                    "type": "list",
                    "description": "Empty spaces between products on this shelf",
                    "required": False,
                    "list_item_type": "object",
                    "nested_fields": [
                        {
                            "name": "after_position",
                            "type": "integer",
                            "description": "Gap appears after this position number",
                            "required": True
                        },
                        {
                            "name": "gap_size",
                            "type": "literal",
                            "description": "Approximate size of the gap",
                            "required": True,
                            "allowed_values": ["small", "medium", "large"]
                        },
                        {
                            "name": "estimated_product_spaces",
                            "type": "integer",
                            "description": "How many products could fit in this gap",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "extraction_notes",
                    "type": "string",
                    "description": "Any issues or observations about this shelf (e.g., \"products fallen over\", \"heavy shadows on right side\")",
                    "required": False
                }
            ]
        }
    ]
}]

# Detail v1 fields - EXACT structure from document
detail_v1_fields = [{
    "name": "detail_enhancement",
    "type": "object",
    "description": "Enhanced details for ALL products from Stage 2, maintaining exact structure",
    "required": True,
    "nested_fields": [
        {
            "name": "fixture_id",
            "type": "string",
            "description": "Must match Stage 2's fixture_id exactly",
            "required": True
        },
        {
            "name": "total_shelves",
            "type": "integer",
            "description": "Must match Stage 2's total_shelves exactly",
            "required": True
        },
        {
            "name": "shelves_enhanced",
            "type": "list",
            "description": "Enhanced details for each shelf (MUST have same length as Stage 2's shelves array)",
            "required": True,
            "list_item_type": "object",
            "nested_fields": [
                {
                    "name": "shelf_number",
                    "type": "integer",
                    "description": "Must match Stage 2's shelf_number for this array position",
                    "required": True
                },
                {
                    "name": "products_enhanced",
                    "type": "list",
                    "description": "Required only when Stage 2's extraction_status=\"has_products\". When shelf was empty, this array should be omitted or empty",
                    "required": False,
                    "list_item_type": "object",
                    "nested_fields": [
                        {
                            "name": "product_reference",
                            "type": "object",
                            "description": "Identifies which Stage 2 product this enhances",
                            "required": True,
                            "nested_fields": [
                                {
                                    "name": "shelf_index",
                                    "type": "integer",
                                    "description": "Index in Stage 2's shelves array (0-based)",
                                    "required": True
                                },
                                {
                                    "name": "product_index",
                                    "type": "integer",
                                    "description": "Index in that shelf's products array (0-based)",
                                    "required": True
                                },
                                {
                                    "name": "position",
                                    "type": "integer",
                                    "description": "Position from Stage 2 (for validation)",
                                    "required": True
                                },
                                {
                                    "name": "brand",
                                    "type": "string",
                                    "description": "Brand from Stage 2 (for validation)",
                                    "required": True
                                },
                                {
                                    "name": "name",
                                    "type": "string",
                                    "description": "Name from Stage 2 (for validation)",
                                    "required": True
                                }
                            ]
                        },
                        {
                            "name": "pricing",
                            "type": "object",
                            "description": "Price information",
                            "required": True,
                            "nested_fields": [
                                {
                                    "name": "regular_price",
                                    "type": "float",
                                    "description": "Regular price",
                                    "required": False
                                },
                                {
                                    "name": "promotional_price",
                                    "type": "float",
                                    "description": "Promotional price if different",
                                    "required": False
                                },
                                {
                                    "name": "promotion_text",
                                    "type": "string",
                                    "description": "Promotion text (e.g., \"3 for £5\")",
                                    "required": False
                                },
                                {
                                    "name": "currency",
                                    "type": "literal",
                                    "description": "Currency",
                                    "required": True,
                                    "allowed_values": ["GBP", "EUR", "USD", "other"]
                                },
                                {
                                    "name": "price_visible",
                                    "type": "boolean",
                                    "description": "Whether price is visible",
                                    "required": True
                                },
                                {
                                    "name": "price_not_visible_reason",
                                    "type": "string",
                                    "description": "Why price couldn't be extracted (only fill if price_visible is false)",
                                    "required": False
                                },
                                {
                                    "name": "price_tag_location",
                                    "type": "literal",
                                    "description": "Where the price tag is positioned relative to this product",
                                    "required": True,
                                    "allowed_values": ["directly_below", "left_of_product", "right_of_product", "distant", "not_visible"]
                                },
                                {
                                    "name": "price_attribution_confidence",
                                    "type": "literal",
                                    "description": "How confident that this price belongs to this specific product",
                                    "required": True,
                                    "allowed_values": ["certain", "likely", "uncertain"]
                                },
                                {
                                    "name": "possible_price_owner",
                                    "type": "string",
                                    "description": "If uncertain, which nearby product might this price actually belong to",
                                    "required": False
                                }
                            ]
                        },
                        {
                            "name": "package_info",
                            "type": "object",
                            "description": "Package details",
                            "required": True,
                            "nested_fields": [
                                {
                                    "name": "size",
                                    "type": "string",
                                    "description": "Package size (e.g., \"330ml\", \"750ml\")",
                                    "required": False
                                },
                                {
                                    "name": "unit_count",
                                    "type": "integer",
                                    "description": "Number of units in multipack",
                                    "required": False
                                },
                                {
                                    "name": "unit_size",
                                    "type": "string",
                                    "description": "Size of individual unit",
                                    "required": False
                                },
                                {
                                    "name": "total_volume",
                                    "type": "string",
                                    "description": "Total volume (e.g., \"6 × 330ml = 1,980ml\")",
                                    "required": False
                                },
                                {
                                    "name": "size_visible",
                                    "type": "boolean",
                                    "description": "Whether size information is visible",
                                    "required": True
                                },
                                {
                                    "name": "size_not_visible_reason",
                                    "type": "string",
                                    "description": "Why size couldn't be read (only fill if size_visible is false)",
                                    "required": False
                                },
                                {
                                    "name": "size_read_location",
                                    "type": "literal",
                                    "description": "Where on the package the size information was read from",
                                    "required": True,
                                    "allowed_values": ["front_label", "side_visible", "cap_lid", "not_visible"]
                                },
                                {
                                    "name": "size_read_confidence",
                                    "type": "literal",
                                    "description": "Confidence in the size reading accuracy",
                                    "required": True,
                                    "allowed_values": ["certain", "likely", "uncertain"]
                                },
                                {
                                    "name": "multiple_units_visible",
                                    "type": "boolean",
                                    "description": "Can you see multiple individual units (helps verify multipack claims)",
                                    "required": True
                                }
                            ]
                        },
                        {
                            "name": "physical",
                            "type": "object",
                            "description": "Physical characteristics",
                            "required": True,
                            "nested_fields": [
                                {
                                    "name": "width_relative",
                                    "type": "literal",
                                    "description": "Width relative to neighbors",
                                    "required": True,
                                    "allowed_values": ["narrow", "normal", "wide"]
                                },
                                {
                                    "name": "height_relative",
                                    "type": "literal",
                                    "description": "Height relative to shelf",
                                    "required": True,
                                    "allowed_values": ["short", "medium", "tall"]
                                },
                                {
                                    "name": "width_cm",
                                    "type": "float",
                                    "description": "Estimated width in cm",
                                    "required": True
                                },
                                {
                                    "name": "height_cm",
                                    "type": "float",
                                    "description": "Estimated height in cm",
                                    "required": True
                                },
                                {
                                    "name": "dimension_confidence",
                                    "type": "literal",
                                    "description": "Confidence in dimension estimates",
                                    "required": True,
                                    "allowed_values": ["measured", "estimated", "rough_guess"]
                                }
                            ]
                        },
                        {
                            "name": "visual",
                            "type": "object",
                            "description": "Visual appearance",
                            "required": True,
                            "nested_fields": [
                                {
                                    "name": "primary_color",
                                    "type": "string",
                                    "description": "Most dominant color",
                                    "required": True
                                },
                                {
                                    "name": "secondary_color",
                                    "type": "string",
                                    "description": "Second most prominent color",
                                    "required": True
                                },
                                {
                                    "name": "finish",
                                    "type": "literal",
                                    "description": "Package finish type",
                                    "required": True,
                                    "allowed_values": ["metallic", "matte", "glossy", "transparent", "mixed"]
                                }
                            ]
                        },
                        {
                            "name": "quality",
                            "type": "object",
                            "description": "Extraction quality",
                            "required": True,
                            "nested_fields": [
                                {
                                    "name": "visibility",
                                    "type": "literal",
                                    "description": "Product visibility in image",
                                    "required": True,
                                    "allowed_values": ["clearly_visible", "partially_obscured", "mostly_hidden"]
                                },
                                {
                                    "name": "confidence",
                                    "type": "literal",
                                    "description": "Overall confidence in extraction",
                                    "required": True,
                                    "allowed_values": ["high", "medium", "low"]
                                },
                                {
                                    "name": "issues",
                                    "type": "list",
                                    "description": "Any extraction issues",
                                    "required": False,
                                    "list_item_type": "string"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}]

# Visual v1 fields - EXACT structure from document
visual_v1_fields = [{
    "name": "visual_comparison",
    "type": "object",
    "description": "Comparison between original photo and generated planogram",
    "required": True,
    "nested_fields": [
        {
            "name": "overview",
            "type": "object",
            "description": "Overall comparison metrics",
            "required": True,
            "nested_fields": [
                {
                    "name": "total_products_photo",
                    "type": "integer",
                    "description": "Total products counted in original photo",
                    "required": True
                },
                {
                    "name": "total_products_planogram",
                    "type": "integer",
                    "description": "Total products shown in planogram",
                    "required": True
                },
                {
                    "name": "overall_alignment",
                    "type": "literal",
                    "description": "Overall quality assessment",
                    "required": True,
                    "allowed_values": ["good", "moderate", "poor"]
                }
            ]
        },
        {
            "name": "shelf_mismatches",
            "type": "list",
            "description": "Specific products with placement or quantity issues",
            "required": False,
            "list_item_type": "object",
            "nested_fields": [
                {
                    "name": "product",
                    "type": "string",
                    "description": "Product name",
                    "required": True
                },
                {
                    "name": "issue_type",
                    "type": "literal",
                    "description": "Type of mismatch",
                    "required": True,
                    "allowed_values": ["wrong_shelf", "wrong_quantity", "wrong_position", "missing", "extra"]
                },
                {
                    "name": "photo_location",
                    "type": "object",
                    "description": "Where product appears in photo",
                    "required": True,
                    "nested_fields": [
                        {
                            "name": "shelf",
                            "type": "integer",
                            "description": "Shelf number in photo",
                            "required": True
                        },
                        {
                            "name": "position",
                            "type": "integer",
                            "description": "Position number in photo",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "planogram_location",
                    "type": "object",
                    "description": "Where product appears in planogram",
                    "required": True,
                    "nested_fields": [
                        {
                            "name": "shelf",
                            "type": "integer",
                            "description": "Shelf number in planogram",
                            "required": True
                        },
                        {
                            "name": "position",
                            "type": "integer",
                            "description": "Position number in planogram",
                            "required": True
                        }
                    ]
                },
                {
                    "name": "confidence",
                    "type": "literal",
                    "description": "Confidence in this mismatch",
                    "required": True,
                    "allowed_values": ["high", "medium", "low"]
                },
                {
                    "name": "details",
                    "type": "string",
                    "description": "Additional context about the mismatch",
                    "required": False
                }
            ]
        },
        {
            "name": "critical_issues",
            "type": "list",
            "description": "Major structural problems",
            "required": False,
            "list_item_type": "string"
        }
    ]
}]

# Update all prompts
prompts_to_update = [
    ("Structure v1", structure_v1_fields),
    ("Product v1", product_v1_fields),
    ("Detail v1", detail_v1_fields),
    ("Visual v1", visual_v1_fields)
]

for prompt_name, fields in prompts_to_update:
    try:
        result = supabase.table('prompt_templates').update({
            'fields': json.dumps(fields)
        }).eq('name', prompt_name).execute()
        print(f"✓ Updated {prompt_name} with exact field structure from document")
    except Exception as e:
        print(f"✗ Error updating {prompt_name}: {e}")

print("\nAll v1 prompts have been updated with the EXACT field structures from EXTRACTION_PROMPTS_FINAL.md")