#!/usr/bin/env python3
"""
Script to save all prompts from EXTRACTION_PROMPTS_FINAL.md to the database
"""

import json
import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Define the prompts and their fields
prompts_data = [
    {
        "name": "Structure Extraction - Refined Complete",
        "stage_type": "structure",
        "prompt_template": """Analyze this retail shelf image to identify the physical structure.

COUNT:
□ Number of horizontal shelves (bottom = 1, count up)
□ Each product display level = one shelf
□ Include floor level only if products are placed there

MEASURE:
□ Fixture width: _____ meters (estimate)
□ Fixture height: _____ meters (estimate)
□ Fixture type: wall_shelf | gondola | end_cap | cooler | freezer | bin | pegboard | other

IDENTIFY NON-PRODUCT ELEMENTS:
□ Security devices: grids, magnetic tags, plastic cases, bottle locks
□ Promotional materials: shelf wobblers, hanging signs, price cards, banners
□ Shelf equipment: dividers, pushers, price rails, shelf strips
□ Display accessories: hooks, clip strips, shelf talkers
□ Fixtures: end panels, header boards, base decks

Output the total shelf count and all fixture details.

{IF_RETRY}
PREVIOUS ATTEMPT: {SHELVES} shelves found
Uncertainty areas: {PROBLEM_AREAS}

Common issues to verify:
- Is the bottom/floor level actually holding products?
- Are there partial shelves at the top?
- Did they count dividers as separate shelves?

NOTE: Trust your own analysis over previous attempts.
{/IF_RETRY}""",
        "fields": {
            "structure_extraction": {
                "type": "object",
                "required": True,
                "description": "Complete shelf structure analysis",
                "properties": {
                    "shelf_structure": {
                        "type": "object",
                        "required": True,
                        "description": "Physical structure of the shelf fixture",
                        "properties": {
                            "total_shelves": {
                                "type": "integer",
                                "required": True,
                                "description": "Total number of horizontal shelves"
                            },
                            "fixture_id": {
                                "type": "string",
                                "required": True,
                                "description": "Unique identifier for this shelf fixture (e.g., \"store123_aisle5_bay2\")"
                            },
                            "shelf_numbers": {
                                "type": "array",
                                "required": True,
                                "description": "List of shelf numbers from bottom to top (must have length = total_shelves)",
                                "example": "[1, 2, 3] for 3 shelves"
                            },
                            "shelf_type": {
                                "type": "literal",
                                "required": True,
                                "description": "Type of fixture",
                                "enum": ["wall_shelf", "gondola", "end_cap", "cooler", "freezer", "bin", "pegboard", "other"]
                            },
                            "width_meters": {
                                "type": "float",
                                "required": True,
                                "description": "Estimated width of fixture in meters"
                            },
                            "height_meters": {
                                "type": "float",
                                "required": True,
                                "description": "Estimated height of fixture in meters"
                            },
                            "shelves": {
                                "type": "array",
                                "required": True,
                                "description": "Detailed information for each shelf level",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "shelf_number": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Shelf identifier (1=bottom, counting up)"
                                        },
                                        "has_price_rail": {
                                            "type": "boolean",
                                            "required": True,
                                            "description": "Whether shelf has price label strip/rail"
                                        },
                                        "special_features": {
                                            "type": "string",
                                            "required": False,
                                            "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)"
                                        },
                                        "has_empty_spaces": {
                                            "type": "boolean",
                                            "required": True,
                                            "description": "Whether significant gaps exist on this shelf"
                                        },
                                        "empty_space_details": {
                                            "type": "object",
                                            "required": False,
                                            "description": "Details about empty spaces",
                                            "properties": {
                                                "sections_with_gaps": {
                                                    "type": "array",
                                                    "required": True,
                                                    "items": {
                                                        "type": "literal",
                                                        "enum": ["left", "center", "right"]
                                                    }
                                                },
                                                "estimated_total_gap_cm": {
                                                    "type": "float",
                                                    "required": True,
                                                    "description": "Total empty space in centimeters"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "non_product_elements": {
                                "type": "object",
                                "required": True,
                                "description": "Items on shelves that are not products",
                                "properties": {
                                    "security_devices": {
                                        "type": "array",
                                        "required": False,
                                        "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "description": "Type of security device"},
                                                "location": {"type": "string", "description": "Where on shelf it's located"}
                                            }
                                        }
                                    },
                                    "promotional_materials": {
                                        "type": "array",
                                        "required": False,
                                        "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "description": "Type of promotional material"},
                                                "location": {"type": "string", "description": "Where positioned"},
                                                "text_visible": {"type": "string", "description": "Any readable promotional text"}
                                            }
                                        }
                                    },
                                    "shelf_equipment": {
                                        "type": "array",
                                        "required": False,
                                        "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "description": "Type of equipment"},
                                                "location": {"type": "string", "description": "Where installed"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "is_active": True,
        "is_user_created": True
    },
    {
        "name": "Product Extraction - Refined Complete",
        "stage_type": "product",
        "prompt_template": """STAGE 2: PRODUCT EXTRACTION

Analyze this retail shelf image to identify the products present on the shelf. 

We have already identified that {TOTAL_SHELVES} horizontal shelves exist, numbered from bottom (1) to top ({TOTAL_SHELVES}).

WHAT YOU'RE BUILDING:
You are extracting product data that will be converted into a planogram. A planogram is a visual diagram showing product placement on shelves - like a map of the shelf. Your data will become a grid where each product facing gets its own cell.

HOW YOUR EXTRACTION BECOMES VISUAL:
- Each product facing (unit visible from front) = one cell in the grid
- Position 1,2,3 = left-to-right order in the planogram
- Gaps in position numbers = empty space in the visual
- Example: If you extract positions 1,2,5, the planogram shows: [Prod1][Prod2][Empty][Empty][Prod5]

EXTRACT:
1. Scan left to right, identify each distinct product
2. Count facings (units visible from front only)
3. Number products sequentially: 1, 2, 3, 4... (continuous numbering)
4. Track significant gaps between products separately (will be recorded in gaps array)
5. Note section: Left | Center | Right (divide shelf in thirds)

CRITICAL: Missing positions create gaps in the planogram. Only skip numbers if there's actual empty space on the shelf.

HANDLE THESE SITUATIONS:
- Shelf completely blocked: Mark extraction_status as "blocked"
- Shelf not visible: Mark extraction_status as "not_visible"
- Products knocked over/pile: Note in extraction_notes
- Bottom shelf cut off: Extract visible shelves only

{IF_RETRY}
PREVIOUS FOUND ON THIS SHELF:
{PREVIOUS_SHELF_PRODUCTS}

VISUAL FEEDBACK:
{PLANOGRAM_FEEDBACK}
Example: "Shelf looks too sparse - check for missed products"

NOTE: Trust what you see. Add/correct products as needed.
You can disagree with the previous extraction completely.
{/IF_RETRY}""",
        "fields": {
            "product_extraction": {
                "type": "object",
                "required": True,
                "description": "Complete product extraction for ALL shelves in the fixture",
                "properties": {
                    "fixture_id": {
                        "type": "string",
                        "required": True,
                        "description": "Unique identifier for this extraction (e.g., \"store123_aisle5_bay2\")"
                    },
                    "total_shelves": {
                        "type": "integer",
                        "required": True,
                        "description": "Total number of shelves being extracted (MUST equal {TOTAL_SHELVES} from Stage 1)",
                        "min": 1,
                        "max": 10
                    },
                    "shelves": {
                        "type": "array",
                        "required": True,
                        "description": "Product data for each shelf (MUST have exactly total_shelves entries)",
                        "validation": "Array length MUST equal total_shelves value",
                        "items": {
                            "type": "object",
                            "properties": {
                                "shelf_number": {
                                    "type": "integer",
                                    "required": True,
                                    "description": "Which shelf this is (MUST match position in array + 1)",
                                    "min": 1
                                },
                                "extraction_status": {
                                    "type": "literal",
                                    "required": True,
                                    "description": "Status of this shelf extraction",
                                    "enum": ["has_products", "empty_shelf", "not_visible", "blocked"]
                                },
                                "products": {
                                    "type": "array",
                                    "required": "when extraction_status=\"has_products\"",
                                    "description": "All products found on this specific shelf",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "position": {
                                                "type": "integer",
                                                "required": True,
                                                "description": "Sequential position from left to right on THIS shelf",
                                                "min": 1
                                            },
                                            "section": {
                                                "type": "literal",
                                                "required": True,
                                                "description": "Which third of the shelf this product is in",
                                                "enum": ["left", "center", "right"]
                                            },
                                            "brand": {
                                                "type": "string",
                                                "required": True,
                                                "description": "Product brand name"
                                            },
                                            "name": {
                                                "type": "string",
                                                "required": True,
                                                "description": "Product name or variant"
                                            },
                                            "product_type": {
                                                "type": "literal",
                                                "required": True,
                                                "description": "Package type",
                                                "enum": ["can", "bottle", "box", "pouch", "jar", "other"]
                                            },
                                            "facings": {
                                                "type": "integer",
                                                "required": True,
                                                "description": "Number of units visible from front",
                                                "min": 1,
                                                "max": 20
                                            },
                                            "stack": {
                                                "type": "integer",
                                                "required": True,
                                                "description": "Number of units stacked vertically",
                                                "min": 1,
                                                "max": 5
                                            }
                                        }
                                    }
                                },
                                "gaps": {
                                    "type": "array",
                                    "required": False,
                                    "description": "Empty spaces between products on this shelf",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "after_position": {
                                                "type": "integer",
                                                "required": True,
                                                "description": "Gap appears after this position number"
                                            },
                                            "gap_size": {
                                                "type": "literal",
                                                "required": True,
                                                "description": "Approximate size of the gap",
                                                "enum": ["small", "medium", "large"]
                                            },
                                            "estimated_product_spaces": {
                                                "type": "integer",
                                                "required": True,
                                                "description": "How many products could fit in this gap",
                                                "min": 1,
                                                "max": 10
                                            }
                                        }
                                    }
                                },
                                "extraction_notes": {
                                    "type": "string",
                                    "required": False,
                                    "description": "Any issues or observations about this shelf (e.g., \"products fallen over\", \"heavy shadows on right side\")"
                                }
                            }
                        }
                    }
                }
            }
        },
        "is_active": True,
        "is_user_created": True
    },
    {
        "name": "Detail Enhancement - Refined Complete",
        "stage_type": "detail",
        "prompt_template": """STAGE 3: DETAIL ENHANCEMENT

Look at this retail shelf image.

We have already identified and located these products:

{COMPLETE_PRODUCT_LIST}
Example format:
=== FIXTURE: store123_aisle5_bay2 ===
Total Shelves: 3

SHELF 1 (Bottom):
- Product 1: Coca-Cola Zero (6 facings) - Left section
- Product 2: [Gap - 2 product spaces]
- Product 3: Pepsi Max (4 facings) - Center section
- Product 4: Fanta Orange (3 facings) - Center section

SHELF 2:
- Product 1: Budweiser (8 facings) - Left section
- Product 2: Heineken (6 facings) - Center section

SHELF 3 (Top):
[Empty shelf - no products]

YOUR TASK:
Add details to EACH product above IN ORDER. You cannot skip, add, or remove products.

For each product, find it in the image and extract:

PRICING (check shelf edge labels):
□ Regular price: £_____ 
□ Price tag location: directly_below | left_of_product | right_of_product | distant | not_visible
□ Confidence this price belongs to THIS product: certain | likely | uncertain
□ If uncertain, which product might this price belong to: _____
□ Promotional price: £_____ (if different)
□ Promotion text: _____ (e.g., "3 for £5")
□ Currency: GBP | EUR | USD | other

VERIFICATION NOTES:
- If price tag is between two products, note which product it's closer to
- If no direct price visible, note where you looked
- Multi-packs often share one price tag for the group

PACKAGE DETAILS (read from product):
□ Package size: _____ (e.g., "330ml", "750ml", "6-pack")
□ Size location on package: front_label | side_visible | cap/lid | not_visible
□ Confidence in size reading: certain | likely | uncertain
□ If multipack: unit size and count
□ Multiple units visible: Yes/No (helps verify if truly multipack)
□ Total volume: _____ (e.g., "6 × 330ml = 1,980ml")

PHYSICAL CHARACTERISTICS:
□ Width relative to neighbors: narrow | normal | wide
□ Height relative to shelf: short | medium | tall
□ Estimated dimensions: width ___cm, height ___cm

VISUAL APPEARANCE:
□ Primary color: _____ (most dominant)
□ Secondary color: _____ (second most prominent)
□ Package finish: metallic | matte | glossy | transparent

EXTRACTION QUALITY:
□ Visibility: clearly_visible | partially_obscured | mostly_hidden
□ Confidence: high | medium | low
□ Issues: _____ (e.g., "price tag torn")

Process EVERY product systematically.

{IF_RETRY}
PREVIOUS ATTEMPT RESULTS:
{PREVIOUS_DETAILS_BY_PRODUCT}

Issues identified:
- Missing details for: {INCOMPLETE_PRODUCTS}
- Low confidence items: {LOW_CONFIDENCE_PRODUCTS}

Fill in missing information and verify previous extractions.
{/IF_RETRY}""",
        "fields": {
            "detail_enhancement": {
                "type": "object",
                "required": True,
                "description": "Enhanced details for ALL products from Stage 2, maintaining exact structure",
                "properties": {
                    "fixture_id": {
                        "type": "string",
                        "required": True,
                        "description": "Must match Stage 2's fixture_id exactly"
                    },
                    "total_shelves": {
                        "type": "integer",
                        "required": True,
                        "description": "Must match Stage 2's total_shelves exactly"
                    },
                    "shelves_enhanced": {
                        "type": "array",
                        "required": True,
                        "description": "Enhanced details for each shelf (MUST have same length as Stage 2's shelves array)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "shelf_number": {
                                    "type": "integer",
                                    "required": True,
                                    "description": "Must match Stage 2's shelf_number for this array position"
                                },
                                "products_enhanced": {
                                    "type": "array",
                                    "required": False,
                                    "description": "Required only when Stage 2's extraction_status=\"has_products\". When shelf was empty, this array should be omitted or empty",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "product_reference": {
                                                "type": "object",
                                                "required": True,
                                                "description": "Identifies which Stage 2 product this enhances",
                                                "properties": {
                                                    "shelf_index": {
                                                        "type": "integer",
                                                        "required": True,
                                                        "description": "Index in Stage 2's shelves array (0-based)"
                                                    },
                                                    "product_index": {
                                                        "type": "integer",
                                                        "required": True,
                                                        "description": "Index in that shelf's products array (0-based)"
                                                    },
                                                    "position": {
                                                        "type": "integer",
                                                        "required": True,
                                                        "description": "Position from Stage 2 (for validation)"
                                                    },
                                                    "brand": {
                                                        "type": "string",
                                                        "required": True,
                                                        "description": "Brand from Stage 2 (for validation)"
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "required": True,
                                                        "description": "Name from Stage 2 (for validation)"
                                                    }
                                                }
                                            },
                                            "pricing": {
                                                "type": "object",
                                                "required": True,
                                                "description": "Price information",
                                                "properties": {
                                                    "regular_price": {"type": "float", "required": False, "min": 0, "max": 1000},
                                                    "promotional_price": {"type": "float", "required": False, "min": 0, "max": 1000},
                                                    "promotion_text": {"type": "string", "required": False},
                                                    "currency": {"type": "literal", "required": True, "enum": ["GBP", "EUR", "USD", "other"]},
                                                    "price_visible": {"type": "boolean", "required": True},
                                                    "price_not_visible_reason": {"type": "string", "required": False, "description": "Why price couldn't be extracted (only fill if price_visible is false)"},
                                                    "price_tag_location": {"type": "literal", "required": True, "enum": ["directly_below", "left_of_product", "right_of_product", "distant", "not_visible"], "description": "Where the price tag is positioned relative to this product"},
                                                    "price_attribution_confidence": {"type": "literal", "required": True, "enum": ["certain", "likely", "uncertain"], "description": "How confident that this price belongs to this specific product"},
                                                    "possible_price_owner": {"type": "string", "required": False, "description": "If uncertain, which nearby product might this price actually belong to"}
                                                }
                                            },
                                            "package_info": {
                                                "type": "object",
                                                "required": True,
                                                "description": "Package details",
                                                "properties": {
                                                    "size": {"type": "string", "required": False},
                                                    "unit_count": {"type": "integer", "required": False},
                                                    "unit_size": {"type": "string", "required": False},
                                                    "total_volume": {"type": "string", "required": False},
                                                    "size_visible": {"type": "boolean", "required": True},
                                                    "size_not_visible_reason": {"type": "string", "required": False, "description": "Why size couldn't be read (only fill if size_visible is false)"},
                                                    "size_read_location": {"type": "literal", "required": True, "enum": ["front_label", "side_visible", "cap_lid", "not_visible"], "description": "Where on the package the size information was read from"},
                                                    "size_read_confidence": {"type": "literal", "required": True, "enum": ["certain", "likely", "uncertain"], "description": "Confidence in the size reading accuracy"},
                                                    "multiple_units_visible": {"type": "boolean", "required": True, "description": "Can you see multiple individual units (helps verify multipack claims)"}
                                                }
                                            },
                                            "physical": {
                                                "type": "object",
                                                "required": True,
                                                "description": "Physical characteristics",
                                                "properties": {
                                                    "width_relative": {"type": "literal", "required": True, "enum": ["narrow", "normal", "wide"]},
                                                    "height_relative": {"type": "literal", "required": True, "enum": ["short", "medium", "tall"]},
                                                    "width_cm": {"type": "float", "required": True, "min": 1, "max": 100},
                                                    "height_cm": {"type": "float", "required": True, "min": 1, "max": 50},
                                                    "dimension_confidence": {"type": "literal", "required": True, "enum": ["measured", "estimated", "rough_guess"], "description": "Confidence in dimension estimates"}
                                                }
                                            },
                                            "visual": {
                                                "type": "object",
                                                "required": True,
                                                "description": "Visual appearance",
                                                "properties": {
                                                    "primary_color": {"type": "string", "required": True},
                                                    "secondary_color": {"type": "string", "required": True},
                                                    "finish": {"type": "literal", "required": True, "enum": ["metallic", "matte", "glossy", "transparent", "mixed"]}
                                                }
                                            },
                                            "quality": {
                                                "type": "object",
                                                "required": True,
                                                "description": "Extraction quality",
                                                "properties": {
                                                    "visibility": {"type": "literal", "required": True, "enum": ["clearly_visible", "partially_obscured", "mostly_hidden"]},
                                                    "confidence": {"type": "literal", "required": True, "enum": ["high", "medium", "low"]},
                                                    "issues": {"type": "array", "required": False}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "is_active": True,
        "is_user_created": True
    },
    {
        "name": "Visual Comparison - Refined Complete",
        "stage_type": "comparison",
        "prompt_template": """Compare the original shelf photo with the generated planogram visualization.

CHECK THESE SPECIFIC THINGS:

1. SHELF ASSIGNMENT: Do all products appear on the correct shelf?
   - List any products that are on a different shelf in the photo vs planogram
   
2. QUANTITY CHECK: Are the facing counts roughly correct?
   - List any products where quantity is significantly off (±3 or more)
   
3. POSITION CHECK: Are products in the right general area of each shelf?
   - List any products that are in wrong section (left/center/right)
   
4. MISSING PRODUCTS: Any obvious products in photo but not in planogram?
   - List only if clearly visible and significant
   
5. EXTRA PRODUCTS: Any products in planogram but not visible in photo?
   - List only if you're confident they're not there

For each issue found, specify:
- What: [Product name]
- Where in photo: [Shelf X, Position Y]
- Where in planogram: [Shelf X, Position Y]
- Confidence: [High/Medium/Low]""",
        "fields": {
            "visual_comparison": {
                "type": "object",
                "required": True,
                "description": "Comparison between original photo and generated planogram",
                "properties": {
                    "overview": {
                        "type": "object",
                        "required": True,
                        "description": "Overall comparison metrics",
                        "properties": {
                            "total_products_photo": {
                                "type": "integer",
                                "required": True,
                                "description": "Total products counted in original photo"
                            },
                            "total_products_planogram": {
                                "type": "integer",
                                "required": True,
                                "description": "Total products shown in planogram"
                            },
                            "overall_alignment": {
                                "type": "literal",
                                "required": True,
                                "description": "Overall quality assessment",
                                "enum": ["good", "moderate", "poor"]
                            }
                        }
                    },
                    "shelf_mismatches": {
                        "type": "array",
                        "required": False,
                        "description": "Specific products with placement or quantity issues",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product": {
                                    "type": "string",
                                    "required": True,
                                    "description": "Product name"
                                },
                                "issue_type": {
                                    "type": "literal",
                                    "required": True,
                                    "description": "Type of mismatch",
                                    "enum": ["wrong_shelf", "wrong_quantity", "wrong_position", "missing", "extra"]
                                },
                                "photo_location": {
                                    "type": "object",
                                    "required": True,
                                    "description": "Where product appears in photo",
                                    "properties": {
                                        "shelf": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Shelf number in photo"
                                        },
                                        "position": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Position number in photo"
                                        }
                                    }
                                },
                                "planogram_location": {
                                    "type": "object",
                                    "required": True,
                                    "description": "Where product appears in planogram",
                                    "properties": {
                                        "shelf": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Shelf number in planogram"
                                        },
                                        "position": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Position number in planogram"
                                        }
                                    }
                                },
                                "confidence": {
                                    "type": "literal",
                                    "required": True,
                                    "description": "Confidence in this mismatch",
                                    "enum": ["high", "medium", "low"]
                                },
                                "details": {
                                    "type": "string",
                                    "required": False,
                                    "description": "Additional context about the mismatch"
                                }
                            }
                        }
                    },
                    "critical_issues": {
                        "type": "array",
                        "required": False,
                        "description": "Major structural problems",
                        "items": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "is_active": True,
        "is_user_created": True
    },
    {
        "name": "Master Orchestrator - User Customization",
        "stage_type": "orchestrator",
        "prompt_template": """Guide the extraction pipeline with these priorities:

{USER_PRIORITIES}

Examples:
- "Prioritize accuracy over cost for alcohol products"
- "Use faster models after 3 iterations"
- "Focus on price accuracy for promotional items"
- "Stop if accuracy plateaus for 2 iterations"
- "Premium spirits need 95%+ accuracy\"""",
        "fields": {
            "user_priorities": {
                "type": "string",
                "required": True,
                "description": "User-defined priorities and rules for the extraction pipeline"
            }
        },
        "is_active": True,
        "is_user_created": True
    },
    {
        "name": "Extraction Orchestrator - User Guidelines",
        "stage_type": "orchestrator",
        "prompt_template": """Apply these extraction guidelines:

{USER_GUIDELINES}

Examples:
- "Pay extra attention to promotional pricing"
- "Beverage shelves often have security devices"
- "This store uses digital price tags"
- "Products are tightly packed on bottom shelves"
- "Watch for multipack vs single unit confusion\"""",
        "fields": {
            "user_guidelines": {
                "type": "string",
                "required": True,
                "description": "User-defined guidelines and context for extraction"
            }
        },
        "is_active": True,
        "is_user_created": True
    }
]

def save_prompts():
    """Save all prompts to the database"""
    print("Saving prompts to database...")
    
    for prompt_data in prompts_data:
        try:
            # Generate a unique template_id
            template_id = str(uuid.uuid4())
            
            # Insert prompt
            result = supabase.table("prompt_templates").insert({
                "template_id": template_id,
                "name": prompt_data["name"],
                "stage_type": prompt_data["stage_type"],
                "prompt_text": prompt_data["prompt_template"],
                "fields": json.dumps(prompt_data["fields"]),
                "is_active": prompt_data["is_active"],
                "is_user_created": prompt_data["is_user_created"],
                "prompt_type": prompt_data["stage_type"],  # Set prompt_type same as stage_type
                "model_type": "gpt-4o-2024-11-20",  # Default model
                "prompt_version": 1  # Initial version
            }).execute()
            
            print(f"✅ Saved: {prompt_data['name']} (stage: {prompt_data['stage_type']})")
            
        except Exception as e:
            print(f"❌ Error saving {prompt_data['name']}: {str(e)}")
    
    print("\n✅ All prompts saved successfully!")
    
    # Verify what was saved
    print("\nVerifying saved prompts:")
    result = supabase.table("prompt_templates").select("name, stage_type, is_user_created").eq("is_user_created", True).execute()
    
    for prompt in result.data:
        print(f"  - {prompt['name']} ({prompt['stage_type']})")

if __name__ == "__main__":
    save_prompts()