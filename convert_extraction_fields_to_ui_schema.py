#!/usr/bin/env python3
"""
Convert EXTRACTION_PROMPTS_FINAL.md field definitions to UI Schema Builder format
"""

import json
from typing import Dict, List, Any

def create_field_structure(
    name: str,
    field_type: str,
    description: str,
    required: bool = True,
    nested_fields: List[Dict] = None,
    list_item_type: str = None,
    allowed_values: List[str] = None,
    sort_order: int = 0,
    min_value: float = None,
    max_value: float = None
) -> Dict[str, Any]:
    """Create a field in the exact format the UI expects"""
    field = {
        "name": name,
        "type": field_type,
        "description": description,
        "required": required,
        "sort_order": sort_order
    }
    
    if nested_fields:
        field["nested_fields"] = nested_fields
    
    if list_item_type:
        field["list_item_type"] = list_item_type
    
    if allowed_values:
        field["allowed_values"] = allowed_values
    
    # Include min/max in description if provided
    if min_value is not None or max_value is not None:
        constraints = []
        if min_value is not None:
            constraints.append(f"Min: {min_value}")
        if max_value is not None:
            constraints.append(f"Max: {max_value}")
        field["description"] += f" ({', '.join(constraints)})"
    
    return field

def convert_structure_v1_fields():
    """Convert Structure v1 fields to UI format"""
    
    # Define shelf equipment sub-object fields
    equipment_fields = [
        create_field_structure("type", "string", "Type of equipment", True, sort_order=0),
        create_field_structure("location", "string", "Where installed", True, sort_order=1)
    ]
    
    # Define promotional materials sub-object fields
    promo_fields = [
        create_field_structure("type", "string", "Type of promotional material", True, sort_order=0),
        create_field_structure("location", "string", "Where positioned", True, sort_order=1),
        create_field_structure("text_visible", "string", "Any readable promotional text", False, sort_order=2)
    ]
    
    # Define security devices sub-object fields
    security_fields = [
        create_field_structure("type", "string", "Type of security device", True, sort_order=0),
        create_field_structure("location", "string", "Where on shelf it's located", True, sort_order=1)
    ]
    
    # Define non_product_elements nested fields
    non_product_elements_fields = [
        create_field_structure(
            "security_devices", "list", 
            "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
            False, list_item_type="object", nested_fields=security_fields, sort_order=0
        ),
        create_field_structure(
            "promotional_materials", "list",
            "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
            False, list_item_type="object", nested_fields=promo_fields, sort_order=1
        ),
        create_field_structure(
            "shelf_equipment", "list",
            "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
            False, list_item_type="object", nested_fields=equipment_fields, sort_order=2
        )
    ]
    
    # Define empty_space_details nested fields
    empty_space_details_fields = [
        create_field_structure(
            "sections_with_gaps", "list",
            "Which sections have gaps", True,
            list_item_type="literal",
            allowed_values=["left", "center", "right"],
            sort_order=0
        ),
        create_field_structure(
            "estimated_total_gap_cm", "float",
            "Total empty space in centimeters", True, sort_order=1
        )
    ]
    
    # Define shelf item fields
    shelf_item_fields = [
        create_field_structure("shelf_number", "integer", "Shelf identifier (1=bottom, counting up)", True, sort_order=0, min_value=1),
        create_field_structure("has_price_rail", "boolean", "Whether shelf has price label strip/rail", True, sort_order=1),
        create_field_structure("special_features", "string", "Unusual characteristics (slanted, wire mesh, divided sections, damaged)", False, sort_order=2),
        create_field_structure("has_empty_spaces", "boolean", "Whether significant gaps exist on this shelf", True, sort_order=3),
        create_field_structure(
            "empty_space_details", "object",
            "Details about empty spaces", False,
            nested_fields=empty_space_details_fields, sort_order=4
        )
    ]
    
    # Define shelf_structure nested fields
    shelf_structure_fields = [
        create_field_structure("total_shelves", "integer", "Total number of horizontal shelves", True, sort_order=0),
        create_field_structure("fixture_id", "string", "Unique identifier for this shelf fixture (e.g., \"store123_aisle5_bay2\")", True, sort_order=1),
        create_field_structure("shelf_numbers", "list", "List of shelf numbers from bottom to top (must have length = total_shelves). Example: [1, 2, 3] for 3 shelves", True, list_item_type="integer", sort_order=2),
        create_field_structure(
            "shelf_type", "literal",
            "Type of fixture", True,
            allowed_values=["wall_shelf", "gondola", "end_cap", "cooler", "freezer", "bin", "pegboard", "other"],
            sort_order=3
        ),
        create_field_structure("width_meters", "float", "Estimated width of fixture in meters", True, sort_order=4),
        create_field_structure("height_meters", "float", "Estimated height of fixture in meters", True, sort_order=5),
        create_field_structure(
            "shelves", "list",
            "Detailed information for each shelf level", True,
            list_item_type="object", nested_fields=shelf_item_fields, sort_order=6
        ),
        create_field_structure(
            "non_product_elements", "object",
            "Items on shelves that are not products", True,
            nested_fields=non_product_elements_fields, sort_order=7
        )
    ]
    
    # Define root structure_extraction field
    structure_extraction = create_field_structure(
        "structure_extraction", "object",
        "Complete shelf structure analysis", True,
        nested_fields=[
            create_field_structure(
                "shelf_structure", "object",
                "Physical structure of the shelf fixture", True,
                nested_fields=shelf_structure_fields, sort_order=0
            )
        ],
        sort_order=0
    )
    
    return structure_extraction

def convert_product_v1_fields():
    """Convert Product v1 fields to UI format"""
    
    # Define gap item fields
    gap_fields = [
        create_field_structure("after_position", "integer", "Gap appears after this position number", True, sort_order=0),
        create_field_structure(
            "gap_size", "literal",
            "Approximate size of the gap", True,
            allowed_values=["small", "medium", "large"],
            sort_order=1
        ),
        create_field_structure("estimated_product_spaces", "integer", "How many products could fit in this gap", True, sort_order=2, min_value=1, max_value=10)
    ]
    
    # Define product item fields
    product_fields = [
        create_field_structure("position", "integer", "Sequential position from left to right on THIS shelf", True, sort_order=0, min_value=1),
        create_field_structure(
            "section", "literal",
            "Which third of the shelf this product is in", True,
            allowed_values=["left", "center", "right"],
            sort_order=1
        ),
        create_field_structure("brand", "string", "Product brand name", True, sort_order=2),
        create_field_structure("name", "string", "Product name or variant", True, sort_order=3),
        create_field_structure(
            "product_type", "literal",
            "Package type", True,
            allowed_values=["can", "bottle", "box", "pouch", "jar", "other"],
            sort_order=4
        ),
        create_field_structure("facings", "integer", "Number of units visible from front", True, sort_order=5, min_value=1, max_value=20),
        create_field_structure("stack", "integer", "Number of units stacked vertically", True, sort_order=6, min_value=1, max_value=5)
    ]
    
    # Define shelf item fields
    shelf_fields = [
        create_field_structure("shelf_number", "integer", "Which shelf this is (MUST match position in array + 1)", True, sort_order=0, min_value=1),
        create_field_structure(
            "extraction_status", "literal",
            "Status of this shelf extraction", True,
            allowed_values=["has_products", "empty_shelf", "not_visible", "blocked"],
            sort_order=1
        ),
        create_field_structure(
            "products", "list",
            "All products found on this specific shelf", True,
            list_item_type="object", nested_fields=product_fields, sort_order=2
        ),
        create_field_structure(
            "gaps", "list",
            "Empty spaces between products on this shelf", False,
            list_item_type="object", nested_fields=gap_fields, sort_order=3
        ),
        create_field_structure("extraction_notes", "string", "Any issues or observations about this shelf (e.g., \"products fallen over\", \"heavy shadows on right side\")", False, sort_order=4)
    ]
    
    # Define root product_extraction field
    product_extraction = create_field_structure(
        "product_extraction", "object",
        "Complete product extraction for ALL shelves in the fixture", True,
        nested_fields=[
            create_field_structure("fixture_id", "string", "Unique identifier for this extraction (e.g., \"store123_aisle5_bay2\")", True, sort_order=0),
            create_field_structure("total_shelves", "integer", "Total number of shelves being extracted (MUST equal {TOTAL_SHELVES} from Stage 1)", True, sort_order=1, min_value=1, max_value=10),
            create_field_structure(
                "shelves", "list",
                "Product data for each shelf (MUST have exactly total_shelves entries). VALIDATION: Array length MUST equal total_shelves value", True,
                list_item_type="object", nested_fields=shelf_fields, sort_order=2
            )
        ],
        sort_order=0
    )
    
    return product_extraction

def convert_detail_v1_fields():
    """Convert Detail v1 fields to UI format"""
    
    # Define product_reference fields
    product_reference_fields = [
        create_field_structure("shelf_index", "integer", "Index in Stage 2's shelves array (0-based)", True, sort_order=0),
        create_field_structure("product_index", "integer", "Index in that shelf's products array (0-based)", True, sort_order=1),
        create_field_structure("position", "integer", "Position from Stage 2 (for validation)", True, sort_order=2),
        create_field_structure("brand", "string", "Brand from Stage 2 (for validation)", True, sort_order=3),
        create_field_structure("name", "string", "Name from Stage 2 (for validation)", True, sort_order=4)
    ]
    
    # Define pricing fields
    pricing_fields = [
        create_field_structure("regular_price", "float", "Regular price", False, sort_order=0, min_value=0, max_value=1000),
        create_field_structure("promotional_price", "float", "Promotional price if different", False, sort_order=1, min_value=0, max_value=1000),
        create_field_structure("promotion_text", "string", "Promotion text (e.g., \"3 for £5\")", False, sort_order=2),
        create_field_structure(
            "currency", "literal",
            "Currency", True,
            allowed_values=["GBP", "EUR", "USD", "other"],
            sort_order=3
        ),
        create_field_structure("price_visible", "boolean", "Whether price is visible", True, sort_order=4),
        create_field_structure("price_not_visible_reason", "string", "Why price couldn't be extracted (only fill if price_visible is false)", False, sort_order=5),
        create_field_structure(
            "price_tag_location", "literal",
            "Where the price tag is positioned relative to this product", True,
            allowed_values=["directly_below", "left_of_product", "right_of_product", "distant", "not_visible"],
            sort_order=6
        ),
        create_field_structure(
            "price_attribution_confidence", "literal",
            "How confident that this price belongs to this specific product", True,
            allowed_values=["certain", "likely", "uncertain"],
            sort_order=7
        ),
        create_field_structure("possible_price_owner", "string", "If uncertain, which nearby product might this price actually belong to", False, sort_order=8)
    ]
    
    # Define package_info fields
    package_info_fields = [
        create_field_structure("size", "string", "Package size (e.g., \"330ml\")", False, sort_order=0),
        create_field_structure("unit_count", "integer", "Number of units in multipack", False, sort_order=1),
        create_field_structure("unit_size", "string", "Size of individual unit", False, sort_order=2),
        create_field_structure("total_volume", "string", "Total volume (e.g., \"6 × 330ml = 1,980ml\")", False, sort_order=3),
        create_field_structure("size_visible", "boolean", "Whether size information is visible", True, sort_order=4),
        create_field_structure("size_not_visible_reason", "string", "Why size couldn't be read (only fill if size_visible is false)", False, sort_order=5),
        create_field_structure(
            "size_read_location", "literal",
            "Where on the package the size information was read from", True,
            allowed_values=["front_label", "side_visible", "cap_lid", "not_visible"],
            sort_order=6
        ),
        create_field_structure(
            "size_read_confidence", "literal",
            "Confidence in the size reading accuracy", True,
            allowed_values=["certain", "likely", "uncertain"],
            sort_order=7
        ),
        create_field_structure("multiple_units_visible", "boolean", "Can you see multiple individual units (helps verify multipack claims)", True, sort_order=8)
    ]
    
    # Define physical fields
    physical_fields = [
        create_field_structure(
            "width_relative", "literal",
            "Width relative to neighbors", True,
            allowed_values=["narrow", "normal", "wide"],
            sort_order=0
        ),
        create_field_structure(
            "height_relative", "literal",
            "Height relative to shelf", True,
            allowed_values=["short", "medium", "tall"],
            sort_order=1
        ),
        create_field_structure("width_cm", "float", "Estimated width in cm", True, sort_order=2, min_value=1, max_value=100),
        create_field_structure("height_cm", "float", "Estimated height in cm", True, sort_order=3, min_value=1, max_value=50),
        create_field_structure(
            "dimension_confidence", "literal",
            "Confidence in dimension estimates", True,
            allowed_values=["measured", "estimated", "rough_guess"],
            sort_order=4
        )
    ]
    
    # Define visual fields
    visual_fields = [
        create_field_structure("primary_color", "string", "Most dominant color", True, sort_order=0),
        create_field_structure("secondary_color", "string", "Second most prominent color", True, sort_order=1),
        create_field_structure(
            "finish", "literal",
            "Package finish", True,
            allowed_values=["metallic", "matte", "glossy", "transparent", "mixed"],
            sort_order=2
        )
    ]
    
    # Define quality fields
    quality_fields = [
        create_field_structure(
            "visibility", "literal",
            "Product visibility", True,
            allowed_values=["clearly_visible", "partially_obscured", "mostly_hidden"],
            sort_order=0
        ),
        create_field_structure(
            "confidence", "literal",
            "Extraction confidence", True,
            allowed_values=["high", "medium", "low"],
            sort_order=1
        ),
        create_field_structure("issues", "list", "Any extraction issues", False, list_item_type="string", sort_order=2)
    ]
    
    # Define product_enhanced fields
    product_enhanced_fields = [
        create_field_structure(
            "product_reference", "object",
            "Identifies which Stage 2 product this enhances", True,
            nested_fields=product_reference_fields, sort_order=0
        ),
        create_field_structure(
            "pricing", "object",
            "Price information", True,
            nested_fields=pricing_fields, sort_order=1
        ),
        create_field_structure(
            "package_info", "object",
            "Package details", True,
            nested_fields=package_info_fields, sort_order=2
        ),
        create_field_structure(
            "physical", "object",
            "Physical characteristics", True,
            nested_fields=physical_fields, sort_order=3
        ),
        create_field_structure(
            "visual", "object",
            "Visual appearance", True,
            nested_fields=visual_fields, sort_order=4
        ),
        create_field_structure(
            "quality", "object",
            "Extraction quality", True,
            nested_fields=quality_fields, sort_order=5
        )
    ]
    
    # Define shelf_enhanced fields
    shelf_enhanced_fields = [
        create_field_structure("shelf_number", "integer", "Must match Stage 2's shelf_number for this array position", True, sort_order=0),
        create_field_structure(
            "products_enhanced", "list",
            "Required only when Stage 2's extraction_status=\"has_products\". When shelf was empty, this array should be omitted or empty", False,
            list_item_type="object", nested_fields=product_enhanced_fields, sort_order=1
        )
    ]
    
    # Define root detail_enhancement field
    detail_enhancement = create_field_structure(
        "detail_enhancement", "object",
        "Enhanced details for ALL products from Stage 2, maintaining exact structure", True,
        nested_fields=[
            create_field_structure("fixture_id", "string", "Must match Stage 2's fixture_id exactly", True, sort_order=0),
            create_field_structure("total_shelves", "integer", "Must match Stage 2's total_shelves exactly", True, sort_order=1),
            create_field_structure(
                "shelves_enhanced", "list",
                "Enhanced details for each shelf (MUST have same length as Stage 2's shelves array)", True,
                list_item_type="object", nested_fields=shelf_enhanced_fields, sort_order=2
            )
        ],
        sort_order=0
    )
    
    return detail_enhancement

def convert_visual_v1_fields():
    """Convert Visual v1 fields to UI format"""
    
    # Define overview fields
    overview_fields = [
        create_field_structure("total_products_photo", "integer", "Total products counted in original photo", True, sort_order=0),
        create_field_structure("total_products_planogram", "integer", "Total products shown in planogram", True, sort_order=1),
        create_field_structure(
            "overall_alignment", "literal",
            "Overall quality assessment", True,
            allowed_values=["good", "moderate", "poor"],
            sort_order=2
        )
    ]
    
    # Define location fields
    location_fields = [
        create_field_structure("shelf", "integer", "Shelf number", True, sort_order=0),
        create_field_structure("position", "integer", "Position number", True, sort_order=1)
    ]
    
    # Define shelf_mismatch fields
    mismatch_fields = [
        create_field_structure("product", "string", "Product name", True, sort_order=0),
        create_field_structure(
            "issue_type", "literal",
            "Type of mismatch", True,
            allowed_values=["wrong_shelf", "wrong_quantity", "wrong_position", "missing", "extra"],
            sort_order=1
        ),
        create_field_structure(
            "photo_location", "object",
            "Where product appears in photo", True,
            nested_fields=location_fields, sort_order=2
        ),
        create_field_structure(
            "planogram_location", "object",
            "Where product appears in planogram", True,
            nested_fields=location_fields, sort_order=3
        ),
        create_field_structure(
            "confidence", "literal",
            "Confidence in this mismatch", True,
            allowed_values=["high", "medium", "low"],
            sort_order=4
        ),
        create_field_structure("details", "string", "Additional context about the mismatch", False, sort_order=5)
    ]
    
    # Define root visual_comparison field
    visual_comparison = create_field_structure(
        "visual_comparison", "object",
        "Comparison between original photo and generated planogram", True,
        nested_fields=[
            create_field_structure(
                "overview", "object",
                "Overall comparison metrics", True,
                nested_fields=overview_fields, sort_order=0
            ),
            create_field_structure(
                "shelf_mismatches", "list",
                "Specific products with placement or quantity issues", False,
                list_item_type="object", nested_fields=mismatch_fields, sort_order=1
            ),
            create_field_structure(
                "critical_issues", "list",
                "Major structural problems", False,
                list_item_type="string", sort_order=2
            )
        ],
        sort_order=0
    )
    
    return visual_comparison

def main():
    """Convert all stage fields and save to files"""
    
    # Convert each stage
    stages = {
        "structure_v1": convert_structure_v1_fields(),
        "product_v1": convert_product_v1_fields(),
        "detail_v1": convert_detail_v1_fields(),
        "visual_v1": convert_visual_v1_fields()
    }
    
    # Save each stage to a separate JSON file
    for stage_name, fields in stages.items():
        filename = f"ui_schema_{stage_name}.json"
        with open(filename, 'w') as f:
            json.dump(fields, f, indent=2)
        print(f"Saved {stage_name} fields to {filename}")
    
    # Also save all stages in one file for reference
    all_stages = {
        "stages": stages,
        "metadata": {
            "description": "UI Schema Builder field definitions for all extraction stages",
            "source": "EXTRACTION_PROMPTS_FINAL.md",
            "version": "1.0"
        }
    }
    
    with open("ui_schema_all_stages.json", 'w') as f:
        json.dump(all_stages, f, indent=2)
    print("\nSaved all stages to ui_schema_all_stages.json")

if __name__ == "__main__":
    main()