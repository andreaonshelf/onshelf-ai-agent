import os
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Define the complete field structures for each prompt type
FIELD_STRUCTURES = {
    "structure": {
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
                            "description": "Unique identifier for this shelf fixture"
                        },
                        "shelf_numbers": {
                            "type": "array",
                            "required": True,
                            "description": "List of shelf numbers from bottom to top",
                            "items": {"type": "integer"}
                        },
                        "shelf_type": {
                            "type": "string",
                            "required": True,
                            "description": "Type of fixture",
                            "enum": ["wall_shelf", "gondola", "end_cap", "cooler", "freezer", "bin", "pegboard", "other"]
                        },
                        "width_meters": {
                            "type": "number",
                            "required": True,
                            "description": "Estimated width of fixture in meters"
                        },
                        "height_meters": {
                            "type": "number",
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
                                        "description": "Shelf identifier (1=bottom)"
                                    },
                                    "has_price_rail": {
                                        "type": "boolean",
                                        "required": True,
                                        "description": "Whether shelf has price label strip"
                                    },
                                    "special_features": {
                                        "type": "string",
                                        "required": False,
                                        "description": "Unusual characteristics"
                                    },
                                    "has_empty_spaces": {
                                        "type": "boolean",
                                        "required": True,
                                        "description": "Whether gaps exist on this shelf"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "product": {
        "product_extraction": {
            "type": "object",
            "required": True,
            "description": "Complete product extraction for all shelves",
            "properties": {
                "fixture_id": {
                    "type": "string",
                    "required": True,
                    "description": "Unique identifier matching Stage 1"
                },
                "total_shelves": {
                    "type": "integer",
                    "required": True,
                    "description": "Total shelves (must match Stage 1)"
                },
                "shelves": {
                    "type": "array",
                    "required": True,
                    "description": "Product data for each shelf",
                    "items": {
                        "type": "object",
                        "properties": {
                            "shelf_number": {
                                "type": "integer",
                                "required": True,
                                "description": "Which shelf this is"
                            },
                            "extraction_status": {
                                "type": "string",
                                "required": True,
                                "description": "Status of this shelf extraction",
                                "enum": ["has_products", "empty_shelf", "not_visible", "blocked"]
                            },
                            "products": {
                                "type": "array",
                                "required": False,
                                "description": "All products on this shelf",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "position": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Position from left to right"
                                        },
                                        "section": {
                                            "type": "string",
                                            "required": True,
                                            "description": "Which third of shelf",
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
                                            "type": "string",
                                            "required": True,
                                            "description": "Package type",
                                            "enum": ["can", "bottle", "box", "pouch", "jar", "other"]
                                        },
                                        "facings": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Number of units visible"
                                        },
                                        "stack": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Units stacked vertically"
                                        }
                                    }
                                }
                            },
                            "gaps": {
                                "type": "array",
                                "required": False,
                                "description": "Empty spaces between products",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "after_position": {
                                            "type": "integer",
                                            "required": True,
                                            "description": "Gap after this position"
                                        },
                                        "gap_size": {
                                            "type": "string",
                                            "required": True,
                                            "description": "Size of gap",
                                            "enum": ["small", "medium", "large"]
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
    "detail": {
        "detail_enhancement": {
            "type": "object",
            "required": True,
            "description": "Enhanced details for all products",
            "properties": {
                "fixture_id": {
                    "type": "string",
                    "required": True,
                    "description": "Must match Stage 2's fixture_id"
                },
                "total_shelves": {
                    "type": "integer",
                    "required": True,
                    "description": "Must match Stage 2's total_shelves"
                },
                "shelves_enhanced": {
                    "type": "array",
                    "required": True,
                    "description": "Enhanced details for each shelf",
                    "items": {
                        "type": "object",
                        "properties": {
                            "shelf_number": {
                                "type": "integer",
                                "required": True,
                                "description": "Must match Stage 2's shelf_number"
                            },
                            "products_enhanced": {
                                "type": "array",
                                "required": False,
                                "description": "Enhanced product details",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "product_reference": {
                                            "type": "object",
                                            "required": True,
                                            "description": "Links to Stage 2 product",
                                            "properties": {
                                                "position": {
                                                    "type": "integer",
                                                    "required": True,
                                                    "description": "Position from Stage 2"
                                                },
                                                "brand": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Brand from Stage 2"
                                                },
                                                "name": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Name from Stage 2"
                                                }
                                            }
                                        },
                                        "pricing": {
                                            "type": "object",
                                            "required": True,
                                            "description": "Price information",
                                            "properties": {
                                                "regular_price": {
                                                    "type": "number",
                                                    "required": False,
                                                    "description": "Regular price"
                                                },
                                                "promotional_price": {
                                                    "type": "number",
                                                    "required": False,
                                                    "description": "Sale price if any"
                                                },
                                                "currency": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Currency code",
                                                    "enum": ["GBP", "EUR", "USD", "other"]
                                                },
                                                "price_visible": {
                                                    "type": "boolean",
                                                    "required": True,
                                                    "description": "Whether price is visible"
                                                }
                                            }
                                        },
                                        "package_info": {
                                            "type": "object",
                                            "required": True,
                                            "description": "Package details",
                                            "properties": {
                                                "size": {
                                                    "type": "string",
                                                    "required": False,
                                                    "description": "Product size"
                                                },
                                                "unit_count": {
                                                    "type": "integer",
                                                    "required": False,
                                                    "description": "Units in pack"
                                                },
                                                "size_visible": {
                                                    "type": "boolean",
                                                    "required": True,
                                                    "description": "Whether size is visible"
                                                }
                                            }
                                        },
                                        "visual": {
                                            "type": "object",
                                            "required": True,
                                            "description": "Visual appearance",
                                            "properties": {
                                                "primary_color": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Main package color"
                                                },
                                                "secondary_color": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Secondary color"
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
        }
    },
    "visual": {
        "visual_comparison": {
            "type": "object",
            "required": True,
            "description": "Visual comparison and planogram generation",
            "properties": {
                "fixture_id": {
                    "type": "string",
                    "required": True,
                    "description": "Fixture identifier for planogram"
                },
                "planogram_layout": {
                    "type": "object",
                    "required": True,
                    "description": "Visual layout structure",
                    "properties": {
                        "total_shelves": {
                            "type": "integer",
                            "required": True,
                            "description": "Number of shelves in planogram"
                        },
                        "fixture_dimensions": {
                            "type": "object",
                            "required": True,
                            "description": "Physical dimensions",
                            "properties": {
                                "width_cm": {
                                    "type": "number",
                                    "required": True,
                                    "description": "Width in centimeters"
                                },
                                "height_cm": {
                                    "type": "number",
                                    "required": True,
                                    "description": "Height in centimeters"
                                }
                            }
                        },
                        "shelves": {
                            "type": "array",
                            "required": True,
                            "description": "Visual layout per shelf",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "shelf_number": {
                                        "type": "integer",
                                        "required": True,
                                        "description": "Shelf level"
                                    },
                                    "shelf_height_cm": {
                                        "type": "number",
                                        "required": True,
                                        "description": "Height from ground"
                                    },
                                    "products": {
                                        "type": "array",
                                        "required": True,
                                        "description": "Product placements",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "position": {
                                                    "type": "integer",
                                                    "required": True,
                                                    "description": "Position index"
                                                },
                                                "x_position_cm": {
                                                    "type": "number",
                                                    "required": True,
                                                    "description": "X coordinate from left"
                                                },
                                                "width_cm": {
                                                    "type": "number",
                                                    "required": True,
                                                    "description": "Product width"
                                                },
                                                "height_cm": {
                                                    "type": "number",
                                                    "required": True,
                                                    "description": "Product height"
                                                },
                                                "brand": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Brand name"
                                                },
                                                "name": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Product name"
                                                },
                                                "facings": {
                                                    "type": "integer",
                                                    "required": True,
                                                    "description": "Number of facings"
                                                },
                                                "color": {
                                                    "type": "string",
                                                    "required": True,
                                                    "description": "Primary package color"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "comparison_results": {
                    "type": "object",
                    "required": False,
                    "description": "Comparison with reference planogram",
                    "properties": {
                        "compliance_score": {
                            "type": "number",
                            "required": True,
                            "description": "Overall compliance percentage"
                        },
                        "discrepancies": {
                            "type": "array",
                            "required": True,
                            "description": "List of differences found",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "required": True,
                                        "description": "Type of discrepancy",
                                        "enum": ["missing_product", "wrong_position", "incorrect_facings", "extra_product"]
                                    },
                                    "description": {
                                        "type": "string",
                                        "required": True,
                                        "description": "Details of the issue"
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

# Update prompts with new names and field structures
updates = [
    {
        "prompt_id": "b9024ed7-019a-4bef-982d-ae9f0dcc0d74",  # Structure Extraction - Standard
        "new_name": "Structure v1",
        "prompt_type": "structure",
        "fields": FIELD_STRUCTURES["structure"]
    },
    {
        "prompt_id": "851199e3-da16-4d51-898d-21ca58909125",  # Product Extraction - Standard (position type)
        "new_name": "Product v1",
        "prompt_type": "position",  # Keep original type
        "fields": FIELD_STRUCTURES["product"]
    },
    {
        "prompt_id": "e70a9e95-acd5-4281-8a11-d1478a7a8078",  # Detail Enhancement - Standard
        "new_name": "Detail v1",
        "prompt_type": "detail",
        "fields": FIELD_STRUCTURES["detail"]
    },
    {
        "prompt_id": "21599f20-9cb0-4dcb-a519-7a2ed0ff059e",  # Visual Comparison - Refined Complete
        "new_name": "Visual v1",
        "prompt_type": "comparison",  # Keep original type
        "fields": FIELD_STRUCTURES["visual"]
    }
]

print("=== UPDATING PROMPTS TO V1 WITH COMPLETE FIELD STRUCTURES ===\n")

for update in updates:
    try:
        # Update the prompt
        result = supabase.table('prompt_templates').update({
            'name': update['new_name'],
            'fields': json.dumps(update['fields']),  # Ensure it's stored as JSON string
            'description': f"Version 1 of {update['prompt_type']} extraction prompt with complete field schema",
            'is_active': True,
            'is_public': True,
            'tags': [update['prompt_type'], 'v1', 'production']
        }).eq('prompt_id', update['prompt_id']).execute()
        
        if result.data:
            print(f"✓ Updated {update['new_name']} (ID: {update['prompt_id']})")
            print(f"  - Fields structure: {len(json.dumps(update['fields']))} chars")
            print(f"  - Type: {update['prompt_type']}")
        else:
            print(f"✗ Failed to update {update['new_name']}")
            
    except Exception as e:
        print(f"✗ Error updating {update['new_name']}: {e}")

print("\n=== VERIFICATION ===")
# Verify the updates
for update in updates:
    try:
        result = supabase.table('prompt_templates').select('name, prompt_type, fields').eq('prompt_id', update['prompt_id']).single().execute()
        if result.data:
            print(f"\n{result.data['name']}:")
            print(f"  Type: {result.data['prompt_type']}")
            fields = result.data.get('fields')
            if fields:
                if isinstance(fields, str):
                    fields = json.loads(fields)
                print(f"  Fields: {'✓ Valid structure' if isinstance(fields, dict) else '✗ Invalid structure'}")
            else:
                print(f"  Fields: ✗ None")
    except Exception as e:
        print(f"Error verifying {update['new_name']}: {e}")

print("\nUpdate complete!")