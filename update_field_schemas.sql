-- Add field_schema column if it doesn't exist
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS field_schema JSONB;

-- Update each prompt with its JSON Schema
-- Update Structure Extraction - Standard v2
UPDATE prompt_templates
SET field_schema = '{
  "type": "object",
  "properties": {
    "structure_extraction": {
      "type": "object",
      "description": "Complete shelf structure analysis",
      "properties": {
        "shelf_structure": {
          "type": "object",
          "description": "Physical structure of the shelf fixture",
          "properties": {
            "total_shelves": {
              "type": "integer",
              "description": "Total number of horizontal shelves"
            },
            "shelf_type": {
              "type": "string",
              "description": "Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)"
            },
            "width_meters": {
              "type": "number",
              "description": "Estimated width of fixture in meters"
            },
            "height_meters": {
              "type": "number",
              "description": "Estimated height of fixture in meters"
            },
            "shelves": {
              "type": "array",
              "description": "Detailed information for each shelf level",
              "items": {
                "type": "object",
                "properties": {
                  "shelf_number": {
                    "type": "integer",
                    "description": "Shelf identifier (1=bottom, counting up)"
                  },
                  "has_price_rail": {
                    "type": "boolean",
                    "description": "Whether shelf has price label strip/rail"
                  },
                  "special_features": {
                    "type": "string",
                    "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)"
                  }
                },
                "required": [
                  "shelf_number",
                  "has_price_rail"
                ]
              }
            },
            "non_product_elements": {
              "type": "object",
              "description": "Items on shelves that are not products",
              "properties": {
                "security_devices": {
                  "type": "array",
                  "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": {
                        "type": "string",
                        "description": "Type of security device"
                      },
                      "location": {
                        "type": "string",
                        "description": "Where on shelf it''s located"
                      }
                    },
                    "required": []
                  }
                },
                "promotional_materials": {
                  "type": "array",
                  "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": {
                        "type": "string",
                        "description": "Type of promotional material"
                      },
                      "location": {
                        "type": "string",
                        "description": "Where positioned"
                      },
                      "text_visible": {
                        "type": "string",
                        "description": "Any readable promotional text"
                      }
                    },
                    "required": []
                  }
                },
                "shelf_equipment": {
                  "type": "array",
                  "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": {
                        "type": "string",
                        "description": "Type of equipment"
                      },
                      "location": {
                        "type": "string",
                        "description": "Where installed"
                      }
                    },
                    "required": []
                  }
                },
                "empty_spaces": {
                  "type": "array",
                  "description": "Significant gaps or out-of-stock areas",
                  "items": {
                    "type": "object",
                    "properties": {
                      "shelf_number": {
                        "type": "integer",
                        "description": "Which shelf has the gap"
                      },
                      "section": {
                        "type": "string",
                        "description": "left, center, or right section"
                      },
                      "estimated_width_cm": {
                        "type": "number",
                        "description": "Approximate gap width"
                      }
                    },
                    "required": []
                  }
                }
              },
              "required": []
            }
          },
          "required": [
            "total_shelves",
            "shelf_type",
            "width_meters",
            "height_meters",
            "shelves",
            "non_product_elements"
          ]
        }
      },
      "required": [
        "shelf_structure"
      ]
    }
  },
  "required": [
    "structure_extraction"
  ]
}'::jsonb
WHERE template_id = 'structure_extraction_standard_v2';

-- Update Product Extraction - Retry with Context v2
UPDATE prompt_templates
SET field_schema = '{
  "type": "object",
  "properties": {
    "shelf_extraction": {
      "type": "object",
      "description": "Products extracted from a single shelf",
      "properties": {
        "shelf_number": {
          "type": "integer",
          "description": "Which shelf this extraction is for (1=bottom)"
        },
        "products": {
          "type": "array",
          "description": "All products found on this shelf",
          "items": {
            "type": "object",
            "properties": {
              "position": {
                "type": "integer",
                "description": "Sequential position from left to right"
              },
              "section": {
                "type": "string",
                "description": "Shelf section (left, center, or right)"
              },
              "brand": {
                "type": "string",
                "description": "Product brand name"
              },
              "name": {
                "type": "string",
                "description": "Product name or variant"
              },
              "product_type": {
                "type": "string",
                "description": "Package type (can, bottle, box, pouch, jar, other)"
              },
              "facings": {
                "type": "integer",
                "description": "Number of units visible from front"
              },
              "stack": {
                "type": "integer",
                "description": "Vertical stacking count (usually 1)"
              }
            },
            "required": [
              "position",
              "section",
              "brand",
              "name",
              "product_type",
              "facings",
              "stack"
            ]
          }
        },
        "empty_positions": {
          "type": "array",
          "description": "Position numbers where gaps exist",
          "items": {
            "type": "integer"
          }
        }
      },
      "required": [
        "shelf_number",
        "products"
      ]
    }
  },
  "required": [
    "shelf_extraction"
  ]
}'::jsonb
WHERE template_id = 'product_extraction_retry_v2';

-- Update Visual Comparison Agent v2
UPDATE prompt_templates
SET field_schema = '{
  "type": "object",
  "properties": {
    "comparison_result": {
      "type": "object",
      "description": "Visual comparison analysis result",
      "properties": {
        "overall_accuracy": {
          "type": "number",
          "description": "Overall accuracy percentage (0-100)"
        },
        "shelf_count_match": {
          "type": "boolean",
          "description": "Whether shelf count matches between images"
        },
        "confidence_level": {
          "type": "string",
          "description": "Confidence in comparison (HIGH, MEDIUM, LOW)"
        },
        "visual_mismatches": {
          "type": "array",
          "description": "List of visual discrepancies found",
          "items": {
            "type": "object",
            "properties": {
              "issue_type": {
                "type": "string",
                "description": "Type of mismatch"
              },
              "description": {
                "type": "string",
                "description": "Detailed description of the mismatch"
              },
              "location": {
                "type": "string",
                "description": "Where the issue occurs"
              }
            },
            "required": [
              "issue_type",
              "description",
              "location"
            ]
          }
        },
        "suggested_corrections": {
          "type": "array",
          "description": "Specific corrections to improve accuracy",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "overall_accuracy",
        "shelf_count_match",
        "confidence_level",
        "visual_mismatches",
        "suggested_corrections"
      ]
    }
  },
  "required": [
    "comparison_result"
  ]
}'::jsonb
WHERE template_id = 'visual_comparison_agent_v2';

-- Update Product Extraction - Planogram Aware v2
UPDATE prompt_templates
SET field_schema = '{
  "type": "object",
  "properties": {
    "shelf_extraction": {
      "type": "object",
      "description": "Products extracted from a single shelf",
      "properties": {
        "shelf_number": {
          "type": "integer",
          "description": "Which shelf this extraction is for (1=bottom)"
        },
        "products": {
          "type": "array",
          "description": "All products found on this shelf",
          "items": {
            "type": "object",
            "properties": {
              "position": {
                "type": "integer",
                "description": "Sequential position from left to right"
              },
              "section": {
                "type": "string",
                "description": "Shelf section (left, center, or right)"
              },
              "brand": {
                "type": "string",
                "description": "Product brand name"
              },
              "name": {
                "type": "string",
                "description": "Product name or variant"
              },
              "product_type": {
                "type": "string",
                "description": "Package type (can, bottle, box, pouch, jar, other)"
              },
              "facings": {
                "type": "integer",
                "description": "Number of units visible from front"
              },
              "stack": {
                "type": "integer",
                "description": "Vertical stacking count (usually 1)"
              }
            },
            "required": [
              "position",
              "section",
              "brand",
              "name",
              "product_type",
              "facings",
              "stack"
            ]
          }
        },
        "empty_positions": {
          "type": "array",
          "description": "Position numbers where gaps exist",
          "items": {
            "type": "integer"
          }
        }
      },
      "required": [
        "shelf_number",
        "products"
      ]
    }
  },
  "required": [
    "shelf_extraction"
  ]
}'::jsonb
WHERE template_id = 'product_extraction_planogram_v2';

-- Update Structure Extraction - Retry v2
UPDATE prompt_templates
SET field_schema = '{
  "type": "object",
  "properties": {
    "structure_extraction": {
      "type": "object",
      "description": "Complete shelf structure analysis",
      "properties": {
        "shelf_structure": {
          "type": "object",
          "description": "Physical structure of the shelf fixture",
          "properties": {
            "total_shelves": {
              "type": "integer",
              "description": "Total number of horizontal shelves"
            },
            "shelf_type": {
              "type": "string",
              "description": "Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)"
            },
            "width_meters": {
              "type": "number",
              "description": "Estimated width of fixture in meters"
            },
            "height_meters": {
              "type": "number",
              "description": "Estimated height of fixture in meters"
            },
            "shelves": {
              "type": "array",
              "description": "Detailed information for each shelf level",
              "items": {
                "type": "object",
                "properties": {
                  "shelf_number": {
                    "type": "integer",
                    "description": "Shelf identifier (1=bottom, counting up)"
                  },
                  "has_price_rail": {
                    "type": "boolean",
                    "description": "Whether shelf has price label strip/rail"
                  },
                  "special_features": {
                    "type": "string",
                    "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)"
                  }
                },
                "required": [
                  "shelf_number",
                  "has_price_rail"
                ]
              }
            },
            "non_product_elements": {
              "type": "object",
              "description": "Items on shelves that are not products",
              "properties": {
                "security_devices": {
                  "type": "array",
                  "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": {
                        "type": "string",
                        "description": "Type of security device"
                      },
                      "location": {
                        "type": "string",
                        "description": "Where on shelf it''s located"
                      }
                    },
                    "required": []
                  }
                },
                "promotional_materials": {
                  "type": "array",
                  "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": {
                        "type": "string",
                        "description": "Type of promotional material"
                      },
                      "location": {
                        "type": "string",
                        "description": "Where positioned"
                      },
                      "text_visible": {
                        "type": "string",
                        "description": "Any readable promotional text"
                      }
                    },
                    "required": []
                  }
                },
                "shelf_equipment": {
                  "type": "array",
                  "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                  "items": {
                    "type": "object",
                    "properties": {
                      "type": {
                        "type": "string",
                        "description": "Type of equipment"
                      },
                      "location": {
                        "type": "string",
                        "description": "Where installed"
                      }
                    },
                    "required": []
                  }
                },
                "empty_spaces": {
                  "type": "array",
                  "description": "Significant gaps or out-of-stock areas",
                  "items": {
                    "type": "object",
                    "properties": {
                      "shelf_number": {
                        "type": "integer",
                        "description": "Which shelf has the gap"
                      },
                      "section": {
                        "type": "string",
                        "description": "left, center, or right section"
                      },
                      "estimated_width_cm": {
                        "type": "number",
                        "description": "Approximate gap width"
                      }
                    },
                    "required": []
                  }
                }
              },
              "required": []
            }
          },
          "required": [
            "total_shelves",
            "shelf_type",
            "width_meters",
            "height_meters",
            "shelves",
            "non_product_elements"
          ]
        }
      },
      "required": [
        "shelf_structure"
      ]
    }
  },
  "required": [
    "structure_extraction"
  ]
}'::jsonb
WHERE template_id = 'structure_extraction_retry_v2';

-- Update Detail Enhancement - Standard v2
UPDATE prompt_templates
SET field_schema = '{
  "type": "object",
  "properties": {
    "detail_extraction": {
      "type": "object",
      "description": "Detailed product information extraction",
      "properties": {
        "product_details_list": {
          "type": "array",
          "description": "Detailed information for all products",
          "items": {
            "type": "object",
            "properties": {
              "product_identification": {
                "type": "object",
                "description": "Product location and identity",
                "properties": {
                  "shelf_number": {
                    "type": "integer",
                    "description": "Which shelf the product is on"
                  },
                  "position": {
                    "type": "integer",
                    "description": "Product position on shelf"
                  },
                  "brand": {
                    "type": "string",
                    "description": "Product brand name"
                  },
                  "name": {
                    "type": "string",
                    "description": "Product name or variant"
                  }
                },
                "required": [
                  "shelf_number",
                  "position",
                  "brand",
                  "name"
                ]
              },
              "pricing": {
                "type": "object",
                "description": "Price information",
                "properties": {
                  "regular_price": {
                    "type": "number",
                    "description": "Standard price"
                  },
                  "promotional_price": {
                    "type": "number",
                    "description": "Sale or discounted price"
                  },
                  "promotion_text": {
                    "type": "string",
                    "description": "Promotional offer text"
                  },
                  "currency": {
                    "type": "string",
                    "description": "Currency code (GBP, EUR, USD)"
                  },
                  "price_visible": {
                    "type": "boolean",
                    "description": "Whether price is visible in image"
                  }
                },
                "required": [
                  "currency",
                  "price_visible"
                ]
              },
              "package_info": {
                "type": "object",
                "description": "Package details",
                "properties": {
                  "package_type": {
                    "type": "string",
                    "description": "Type of container"
                  },
                  "size": {
                    "type": "string",
                    "description": "Package size"
                  },
                  "unit_count": {
                    "type": "integer",
                    "description": "Number of units in multipack"
                  },
                  "unit_size": {
                    "type": "string",
                    "description": "Size of individual units"
                  },
                  "total_volume": {
                    "type": "string",
                    "description": "Total volume calculation"
                  }
                },
                "required": [
                  "package_type"
                ]
              },
              "dimensions": {
                "type": "object",
                "description": "Physical size characteristics",
                "properties": {
                  "width_relative": {
                    "type": "string",
                    "description": "Width compared to shelf average"
                  },
                  "height_relative": {
                    "type": "string",
                    "description": "Height compared to shelf average"
                  },
                  "width_cm": {
                    "type": "number",
                    "description": "Estimated width in centimeters"
                  },
                  "height_cm": {
                    "type": "number",
                    "description": "Estimated height in centimeters"
                  }
                },
                "required": [
                  "width_relative",
                  "height_relative"
                ]
              },
              "visual_info": {
                "type": "object",
                "description": "Visual appearance",
                "properties": {
                  "primary_color": {
                    "type": "string",
                    "description": "Most dominant package color"
                  },
                  "secondary_color": {
                    "type": "string",
                    "description": "Second most prominent color"
                  },
                  "finish": {
                    "type": "string",
                    "description": "Surface finish"
                  }
                },
                "required": [
                  "primary_color",
                  "secondary_color"
                ]
              },
              "extraction_quality": {
                "type": "object",
                "description": "Quality assessment",
                "properties": {
                  "visibility": {
                    "type": "string",
                    "description": "How well product is visible"
                  },
                  "confidence": {
                    "type": "string",
                    "description": "Extraction confidence level"
                  },
                  "issues": {
                    "type": "array",
                    "description": "Any extraction problems encountered",
                    "items": {
                      "type": "string"
                    }
                  }
                },
                "required": [
                  "visibility",
                  "confidence"
                ]
              }
            },
            "required": [
              "product_identification",
              "pricing",
              "package_info",
              "dimensions",
              "visual_info",
              "extraction_quality"
            ]
          }
        }
      },
      "required": [
        "product_details_list"
      ]
    }
  },
  "required": [
    "detail_extraction"
  ]
}'::jsonb
WHERE template_id = 'detail_enhancement_standard_v2';

