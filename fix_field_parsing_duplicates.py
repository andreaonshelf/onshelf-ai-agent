#!/usr/bin/env python3
"""
Fix the field parsing to eliminate duplicates and correctly handle nesting
"""

import json
import os
from supabase import create_client, Client

# Manually define the correct structure based on EXTRACTION_PROMPTS_FINAL.md
# This ensures no parsing errors or duplicates

product_v1_correct = [{
    "name": "product_extraction",
    "type": "object",
    "required": True,
    "description": "Complete product extraction for ALL shelves in the fixture",
    "nested_fields": [
        {
            "name": "fixture_id",
            "type": "string",
            "required": True,
            "description": "Unique identifier for this extraction (e.g., \"store123_aisle5_bay2\")"
        },
        {
            "name": "total_shelves",
            "type": "integer",
            "required": True,
            "description": "Total number of shelves being extracted (MUST equal {TOTAL_SHELVES} from Stage 1)"
        },
        {
            "name": "shelves",
            "type": "list",
            "required": True,
            "description": "Product data for each shelf (MUST have exactly total_shelves entries)",
            "list_item_type": "object",
            "nested_fields": [
                {
                    "name": "shelf_number",
                    "type": "integer",
                    "required": True,
                    "description": "Which shelf this is (MUST match position in array + 1)"
                },
                {
                    "name": "extraction_status",
                    "type": "literal",
                    "required": True,
                    "allowed_values": ["has_products", "empty_shelf", "not_visible", "blocked"],
                    "description": "Status of this shelf extraction"
                },
                {
                    "name": "products",
                    "type": "list",
                    "required": False,  # Only required when extraction_status="has_products"
                    "description": "All products found on this specific shelf",
                    "list_item_type": "object",
                    "nested_fields": [
                        {
                            "name": "position",
                            "type": "integer",
                            "required": True,
                            "description": "Sequential position from left to right on THIS shelf"
                        },
                        {
                            "name": "section",
                            "type": "literal",
                            "required": True,
                            "allowed_values": ["left", "center", "right"],
                            "description": "Which third of the shelf this product is in"
                        },
                        {
                            "name": "brand",
                            "type": "string",
                            "required": True,
                            "description": "Product brand name"
                        },
                        {
                            "name": "name",
                            "type": "string",
                            "required": True,
                            "description": "Product name or variant"
                        },
                        {
                            "name": "product_type",
                            "type": "literal",
                            "required": True,
                            "allowed_values": ["can", "bottle", "box", "pouch", "jar", "other"],
                            "description": "Package type"
                        },
                        {
                            "name": "facings",
                            "type": "integer",
                            "required": True,
                            "description": "Number of units visible from front"
                        },
                        {
                            "name": "stack",
                            "type": "integer",
                            "required": True,
                            "description": "Number of units stacked vertically"
                        }
                    ]
                },
                {
                    "name": "gaps",
                    "type": "list",
                    "required": False,
                    "description": "Empty spaces between products on this shelf",
                    "list_item_type": "object",
                    "nested_fields": [
                        {
                            "name": "after_position",
                            "type": "integer",
                            "required": True,
                            "description": "Gap appears after this position number"
                        },
                        {
                            "name": "gap_size",
                            "type": "literal",
                            "required": True,
                            "allowed_values": ["small", "medium", "large"],
                            "description": "Approximate size of the gap"
                        },
                        {
                            "name": "estimated_product_spaces",
                            "type": "integer",
                            "required": True,
                            "description": "How many products could fit in this gap"
                        }
                    ]
                },
                {
                    "name": "extraction_notes",
                    "type": "string",
                    "required": False,
                    "description": "Any issues or observations about this shelf (e.g., \"products fallen over\", \"heavy shadows on right side\")"
                }
            ]
        }
    ]
}]

# Save to file for verification
with open('product_v1_no_duplicates.json', 'w') as f:
    json.dump(product_v1_correct, f, indent=2)

print("Created clean Product v1 structure without duplicates")

# Update database
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if supabase_url and supabase_key:
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        result = supabase.table('prompt_templates').update({
            'fields': json.dumps(product_v1_correct)
        }).eq('name', 'Product v1').execute()
        print("✓ Updated Product v1 in database with clean structure")
    except Exception as e:
        print(f"✗ Error updating Product v1: {e}")
else:
    print("No database credentials - only saved to file")