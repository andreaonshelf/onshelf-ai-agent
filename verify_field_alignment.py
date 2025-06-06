import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Dict, List, Any, Optional

# Load environment variables
load_dotenv()

# Create Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Define expected fields from EXTRACTION_PROMPTS_FINAL.md
EXPECTED_FIELDS = {
    "Structure v1": {
        "root_name": "structure_extraction",
        "fields": [{
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
                            {"name": "shelf_number", "type": "integer", "description": "Shelf identifier (1=bottom, counting up)", "required": True},
                            {"name": "has_price_rail", "type": "boolean", "description": "Whether shelf has price label strip/rail", "required": True},
                            {"name": "special_features", "type": "string", "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)", "required": False},
                            {"name": "has_empty_spaces", "type": "boolean", "description": "Whether significant gaps exist on this shelf", "required": True},
                            {
                                "name": "empty_space_details",
                                "type": "object",
                                "description": "Details about empty spaces",
                                "required": False,
                                "nested_fields": [
                                    {"name": "sections_with_gaps", "type": "list", "description": "Sections with gaps", "required": True, "list_item_type": "literal", "allowed_values": ["left", "center", "right"]},
                                    {"name": "estimated_total_gap_cm", "type": "float", "description": "Total empty space in centimeters", "required": True}
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
                                    {"name": "type", "type": "string", "description": "Type of security device", "required": True},
                                    {"name": "location", "type": "string", "description": "Where on shelf it's located", "required": True}
                                ]
                            },
                            {
                                "name": "promotional_materials",
                                "type": "list",
                                "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                                "required": False,
                                "list_item_type": "object",
                                "nested_fields": [
                                    {"name": "type", "type": "string", "description": "Type of promotional material", "required": True},
                                    {"name": "location", "type": "string", "description": "Where positioned", "required": True},
                                    {"name": "text_visible", "type": "string", "description": "Any readable promotional text", "required": True}
                                ]
                            },
                            {
                                "name": "shelf_equipment",
                                "type": "list",
                                "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                                "required": False,
                                "list_item_type": "object",
                                "nested_fields": [
                                    {"name": "type", "type": "string", "description": "Type of equipment", "required": True},
                                    {"name": "location", "type": "string", "description": "Where installed", "required": True}
                                ]
                            }
                        ]
                    }
                ]
            }]
        }]
    },
    "Product v1": {
        "root_name": "product_extraction",
        "fields": [{
            "name": "product_extraction",
            "type": "object",
            "description": "Complete product extraction for ALL shelves in the fixture",
            "required": True,
            "nested_fields": [
                {"name": "fixture_id", "type": "string", "description": "Unique identifier for this extraction (e.g., \"store123_aisle5_bay2\")", "required": True},
                {"name": "total_shelves", "type": "integer", "description": "Total number of shelves being extracted (MUST equal {TOTAL_SHELVES} from Stage 1)", "required": True},
                {
                    "name": "shelves",
                    "type": "list",
                    "description": "Product data for each shelf (MUST have exactly total_shelves entries)",
                    "required": True,
                    "list_item_type": "object",
                    "nested_fields": [
                        {"name": "shelf_number", "type": "integer", "description": "Which shelf this is (MUST match position in array + 1)", "required": True},
                        {"name": "extraction_status", "type": "literal", "description": "Status of this shelf extraction", "required": True, "allowed_values": ["has_products", "empty_shelf", "not_visible", "blocked"]},
                        {
                            "name": "products",
                            "type": "list",
                            "description": "All products found on this specific shelf",
                            "required": True,  # Note: actually conditional on extraction_status="has_products"
                            "list_item_type": "object",
                            "nested_fields": [
                                {"name": "position", "type": "integer", "description": "Sequential position from left to right on THIS shelf", "required": True},
                                {"name": "section", "type": "literal", "description": "Which third of the shelf this product is in", "required": True, "allowed_values": ["left", "center", "right"]},
                                {"name": "brand", "type": "string", "description": "Product brand name", "required": True},
                                {"name": "name", "type": "string", "description": "Product name or variant", "required": True},
                                {"name": "product_type", "type": "literal", "description": "Package type", "required": True, "allowed_values": ["can", "bottle", "box", "pouch", "jar", "other"]},
                                {"name": "facings", "type": "integer", "description": "Number of units visible from front", "required": True},
                                {"name": "stack", "type": "integer", "description": "Number of units stacked vertically", "required": True}
                            ]
                        },
                        {
                            "name": "gaps",
                            "type": "list",
                            "description": "Empty spaces between products on this shelf",
                            "required": False,
                            "list_item_type": "object",
                            "nested_fields": [
                                {"name": "after_position", "type": "integer", "description": "Gap appears after this position number", "required": True},
                                {"name": "gap_size", "type": "literal", "description": "Approximate size of the gap", "required": True, "allowed_values": ["small", "medium", "large"]},
                                {"name": "estimated_product_spaces", "type": "integer", "description": "How many products could fit in this gap", "required": True}
                            ]
                        },
                        {"name": "extraction_notes", "type": "string", "description": "Any issues or observations about this shelf", "required": False}
                    ]
                }
            ]
        }]
    },
    "Detail v1": {
        "root_name": "detail_enhancement",
        "fields": [{
            "name": "detail_enhancement",
            "type": "object",
            "description": "Enhanced details for ALL products from Stage 2, maintaining exact structure",
            "required": True,
            "nested_fields": [
                {"name": "fixture_id", "type": "string", "description": "Must match Stage 2's fixture_id exactly", "required": True},
                {"name": "total_shelves", "type": "integer", "description": "Must match Stage 2's total_shelves exactly", "required": True},
                {
                    "name": "shelves_enhanced",
                    "type": "list",
                    "description": "Enhanced details for each shelf (MUST have same length as Stage 2's shelves array)",
                    "required": True,
                    "list_item_type": "object",
                    "nested_fields": [
                        {"name": "shelf_number", "type": "integer", "description": "Must match Stage 2's shelf_number for this array position", "required": True},
                        {
                            "name": "products_enhanced",
                            "type": "list",
                            "description": "Required only when Stage 2's extraction_status=\"has_products\"",
                            "required": False,
                            "list_item_type": "object",
                            "nested_fields": [
                                {
                                    "name": "product_reference",
                                    "type": "object",
                                    "description": "Identifies which Stage 2 product this enhances",
                                    "required": True,
                                    "nested_fields": [
                                        {"name": "shelf_index", "type": "integer", "description": "Index in Stage 2's shelves array (0-based)", "required": True},
                                        {"name": "product_index", "type": "integer", "description": "Index in that shelf's products array (0-based)", "required": True},
                                        {"name": "position", "type": "integer", "description": "Position from Stage 2 (for validation)", "required": True},
                                        {"name": "brand", "type": "string", "description": "Brand from Stage 2 (for validation)", "required": True},
                                        {"name": "name", "type": "string", "description": "Name from Stage 2 (for validation)", "required": True}
                                    ]
                                },
                                {
                                    "name": "pricing",
                                    "type": "object",
                                    "description": "Price information",
                                    "required": True,
                                    "nested_fields": [
                                        {"name": "regular_price", "type": "float", "description": "Regular price", "required": False},
                                        {"name": "promotional_price", "type": "float", "description": "Sale price if any", "required": False},
                                        {"name": "promotion_text", "type": "string", "description": "Promotion text", "required": False},
                                        {"name": "currency", "type": "literal", "description": "Currency code", "required": True, "allowed_values": ["GBP", "EUR", "USD", "other"]},
                                        {"name": "price_visible", "type": "boolean", "description": "Whether price is visible", "required": True},
                                        {"name": "price_not_visible_reason", "type": "string", "description": "Why price couldn't be extracted", "required": False},
                                        {"name": "price_tag_location", "type": "literal", "description": "Where the price tag is positioned", "required": True, "allowed_values": ["directly_below", "left_of_product", "right_of_product", "distant", "not_visible"]},
                                        {"name": "price_attribution_confidence", "type": "literal", "description": "How confident that this price belongs to this product", "required": True, "allowed_values": ["certain", "likely", "uncertain"]},
                                        {"name": "possible_price_owner", "type": "string", "description": "If uncertain, which product might this price belong to", "required": False}
                                    ]
                                },
                                {
                                    "name": "package_info",
                                    "type": "object",
                                    "description": "Package details",
                                    "required": True,
                                    "nested_fields": [
                                        {"name": "size", "type": "string", "description": "Package size", "required": False},
                                        {"name": "unit_count", "type": "integer", "description": "Units in pack", "required": False},
                                        {"name": "unit_size", "type": "string", "description": "Size per unit", "required": False},
                                        {"name": "total_volume", "type": "string", "description": "Total volume", "required": False},
                                        {"name": "size_visible", "type": "boolean", "description": "Whether size is visible", "required": True},
                                        {"name": "size_not_visible_reason", "type": "string", "description": "Why size couldn't be read", "required": False},
                                        {"name": "size_read_location", "type": "literal", "description": "Where on package size was read", "required": True, "allowed_values": ["front_label", "side_visible", "cap_lid", "not_visible"]},
                                        {"name": "size_read_confidence", "type": "literal", "description": "Confidence in size reading", "required": True, "allowed_values": ["certain", "likely", "uncertain"]},
                                        {"name": "multiple_units_visible", "type": "boolean", "description": "Can see multiple units", "required": True}
                                    ]
                                },
                                {
                                    "name": "physical",
                                    "type": "object",
                                    "description": "Physical characteristics",
                                    "required": True,
                                    "nested_fields": [
                                        {"name": "width_relative", "type": "literal", "description": "Width relative to neighbors", "required": True, "allowed_values": ["narrow", "normal", "wide"]},
                                        {"name": "height_relative", "type": "literal", "description": "Height relative to shelf", "required": True, "allowed_values": ["short", "medium", "tall"]},
                                        {"name": "width_cm", "type": "float", "description": "Estimated width in cm", "required": True},
                                        {"name": "height_cm", "type": "float", "description": "Estimated height in cm", "required": True},
                                        {"name": "dimension_confidence", "type": "literal", "description": "Confidence in dimensions", "required": True, "allowed_values": ["measured", "estimated", "rough_guess"]}
                                    ]
                                },
                                {
                                    "name": "visual",
                                    "type": "object",
                                    "description": "Visual appearance",
                                    "required": True,
                                    "nested_fields": [
                                        {"name": "primary_color", "type": "string", "description": "Most dominant color", "required": True},
                                        {"name": "secondary_color", "type": "string", "description": "Second most prominent color", "required": True},
                                        {"name": "finish", "type": "literal", "description": "Package finish", "required": True, "allowed_values": ["metallic", "matte", "glossy", "transparent", "mixed"]}
                                    ]
                                },
                                {
                                    "name": "quality",
                                    "type": "object",
                                    "description": "Extraction quality",
                                    "required": True,
                                    "nested_fields": [
                                        {"name": "visibility", "type": "literal", "description": "Product visibility", "required": True, "allowed_values": ["clearly_visible", "partially_obscured", "mostly_hidden"]},
                                        {"name": "confidence", "type": "literal", "description": "Overall confidence", "required": True, "allowed_values": ["high", "medium", "low"]},
                                        {"name": "issues", "type": "list", "description": "List of issues", "required": False, "list_item_type": "string"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }]
    },
    "Visual v1": {
        "root_name": "visual_comparison",
        "fields": [{
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
                        {"name": "total_products_photo", "type": "integer", "description": "Total products counted in original photo", "required": True},
                        {"name": "total_products_planogram", "type": "integer", "description": "Total products shown in planogram", "required": True},
                        {"name": "overall_alignment", "type": "literal", "description": "Overall quality assessment", "required": True, "allowed_values": ["good", "moderate", "poor"]}
                    ]
                },
                {
                    "name": "shelf_mismatches",
                    "type": "list",
                    "description": "Specific products with placement or quantity issues",
                    "required": False,
                    "list_item_type": "object",
                    "nested_fields": [
                        {"name": "product", "type": "string", "description": "Product name", "required": True},
                        {"name": "issue_type", "type": "literal", "description": "Type of mismatch", "required": True, "allowed_values": ["wrong_shelf", "wrong_quantity", "wrong_position", "missing", "extra"]},
                        {
                            "name": "photo_location",
                            "type": "object",
                            "description": "Where product appears in photo",
                            "required": True,
                            "nested_fields": [
                                {"name": "shelf", "type": "integer", "description": "Shelf number in photo", "required": True},
                                {"name": "position", "type": "integer", "description": "Position number in photo", "required": True}
                            ]
                        },
                        {
                            "name": "planogram_location",
                            "type": "object",
                            "description": "Where product appears in planogram",
                            "required": True,
                            "nested_fields": [
                                {"name": "shelf", "type": "integer", "description": "Shelf number in planogram", "required": True},
                                {"name": "position", "type": "integer", "description": "Position number in planogram", "required": True}
                            ]
                        },
                        {"name": "confidence", "type": "literal", "description": "Confidence in this mismatch", "required": True, "allowed_values": ["high", "medium", "low"]},
                        {"name": "details", "type": "string", "description": "Additional context about the mismatch", "required": False}
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
    }
}

def parse_db_fields(fields_json: List[Dict]) -> Dict[str, Any]:
    """Convert database field format to a comparable structure"""
    result = {}
    for field in fields_json:
        field_dict = {
            "name": field["name"],
            "type": field["type"],
            "description": field.get("description", ""),
            "required": field.get("required", False)
        }
        
        # Handle type-specific properties
        if field["type"] == "enum":
            field_dict["allowed_values"] = field.get("allowed_values", [])
        elif field["type"] == "literal":
            field_dict["allowed_values"] = field.get("allowed_values", [])
        elif field["type"] == "list":
            field_dict["list_item_type"] = field.get("list_item_type", "string")
            
        # Handle nested fields
        if "nested_fields" in field:
            field_dict["nested_fields"] = parse_db_fields(field["nested_fields"])
            
        result[field["name"]] = field_dict
    
    return result

def compare_fields(expected: Dict, actual: Dict, path: str = "") -> List[str]:
    """Compare expected fields with actual database fields"""
    issues = []
    
    # Check for missing fields
    for field_name, field_spec in expected.items():
        if field_name not in actual:
            issues.append(f"Missing field at {path}/{field_name}")
            continue
            
        actual_field = actual[field_name]
        field_path = f"{path}/{field_name}"
        
        # Check field type
        expected_type = field_spec["type"]
        actual_type = actual_field["type"]
        
        # Map database types to expected types
        type_mapping = {
            "number": "float",
            "decimal": "float",
            "enum": "literal",
            "text": "string"
        }
        
        normalized_actual = type_mapping.get(actual_type, actual_type)
        normalized_expected = type_mapping.get(expected_type, expected_type)
        
        if normalized_actual != normalized_expected:
            issues.append(f"Wrong type at {field_path}: expected {expected_type}, got {actual_type}")
            
        # Check required flag
        if field_spec.get("required", False) != actual_field.get("required", False):
            issues.append(f"Wrong required flag at {field_path}: expected {field_spec.get('required')}, got {actual_field.get('required')}")
            
        # Check allowed values for enums/literals
        if expected_type in ["literal", "enum"]:
            expected_values = set(field_spec.get("allowed_values", []))
            actual_values = set(actual_field.get("allowed_values", []))
            
            if expected_values != actual_values:
                missing = expected_values - actual_values
                extra = actual_values - expected_values
                if missing:
                    issues.append(f"Missing allowed values at {field_path}: {missing}")
                if extra:
                    issues.append(f"Extra allowed values at {field_path}: {extra}")
                    
        # Check list item type
        if expected_type == "list":
            expected_item_type = field_spec.get("list_item_type", "string")
            actual_item_type = actual_field.get("list_item_type", "string")
            
            # Normalize item types
            normalized_actual_item = type_mapping.get(actual_item_type, actual_item_type)
            normalized_expected_item = type_mapping.get(expected_item_type, expected_item_type)
            
            if normalized_actual_item != normalized_expected_item:
                issues.append(f"Wrong list item type at {field_path}: expected {expected_item_type}, got {actual_item_type}")
                
        # Check nested fields
        if "nested_fields" in field_spec:
            if "nested_fields" not in actual_field:
                issues.append(f"Missing nested fields at {field_path}")
            else:
                expected_nested = {f["name"]: f for f in field_spec["nested_fields"]}
                actual_nested = parse_db_fields(actual_field["nested_fields"])
                nested_issues = compare_fields(expected_nested, actual_nested, field_path)
                issues.extend(nested_issues)
                
    # Check for extra fields in database
    for field_name in actual:
        if field_name not in expected:
            issues.append(f"Extra field in database at {path}/{field_name}")
            
    return issues

def main():
    # Query database
    results = supabase.table('prompt_templates').select('*').execute()
    
    prompt_mapping = {
        'structure': 'Structure v1',
        'position': 'Product v1',  # Note: database uses 'position' for Product
        'detail': 'Detail v1',
        'comparison': 'Visual v1'   # Note: database uses 'comparison' for Visual
    }
    
    print("Field Verification Report")
    print("=" * 80)
    print()
    
    for row in results.data:
        prompt_type = row.get('prompt_type', '')
        
        # Find matching expected prompt
        display_name = prompt_mapping.get(prompt_type.lower())
        if not display_name:
            continue
            
        print(f"\n{display_name} ({prompt_type})")
        print("-" * 60)
        
        if not row.get('fields'):
            print("❌ NO FIELDS DEFINED IN DATABASE")
            continue
            
        # Parse database fields - the fields are already a JSON string
        try:
            if isinstance(row['fields'], str):
                fields_data = json.loads(row['fields'])
            else:
                fields_data = row['fields']
                
            db_fields = parse_db_fields(fields_data)
        except Exception as e:
            print(f"❌ Error parsing fields: {e}")
            print(f"   Raw fields: {row['fields'][:200]}...")
            continue
        
        # Get expected fields
        expected_spec = EXPECTED_FIELDS[display_name]
        expected_fields = {f["name"]: f for f in expected_spec["fields"]}
        
        # Compare
        issues = compare_fields(expected_fields, db_fields)
        
        if issues:
            print(f"❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("✅ All fields match specification")
            
    print("\n" + "=" * 80)
    print("\nSummary:")
    print("- Structure v1: Should have nested structure_extraction > shelf_structure")
    print("- Product v1: Should have nested product_extraction > fixture_id, total_shelves, shelves")
    print("- Detail v1: Should have nested detail_enhancement > fixture_id, total_shelves, shelves_enhanced")
    print("- Visual v1: Should have nested visual_comparison > overview, shelf_mismatches, critical_issues")

if __name__ == "__main__":
    main()