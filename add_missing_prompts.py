import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get Supabase URL and key
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)
print("Connected to Supabase")

# Additional prompts for missing stages
additional_prompts = [
    # Details extraction
    {
        "template_id": "detail_extraction_standard_v1",
        "prompt_type": "detail",
        "model_type": "universal",
        "prompt_version": "1.0",
        "prompt_text": """Enhance the product details for the extracted items.

CURRENT EXTRACTION:
{extracted_products}

For each product, verify and enhance:
- Exact brand name spelling
- Complete product description
- Package size with units (ml, L, g, kg, oz, etc.)
- Price format (ensure decimal places)
- Special attributes (organic, gluten-free, sugar-free, etc.)
- Promotional details (2-for-1, % off, special offer)
- Barcode if visible
- Any missing information

Focus on accuracy and completeness. Mark uncertain details as 'unclear'.""",
        "name": "Detail Enhancement - Standard",
        "description": "Enhance and verify product details",
        "stage_type": "details",
        "fields": [
            {"name": "enhanced_brand", "type": "string", "description": "Verified brand name"},
            {"name": "full_description", "type": "string", "description": "Complete product description"},
            {"name": "verified_size", "type": "string", "description": "Size with proper units"},
            {"name": "verified_price", "type": "number", "description": "Verified price"},
            {"name": "attributes", "type": "array", "description": "Special attributes", "items": {"type": "string"}},
            {"name": "promotional_details", "type": "string", "description": "Promotion information"},
            {"name": "confidence_score", "type": "number", "description": "Confidence in details 0-1"}
        ],
        "tags": ["details", "enhancement", "verification"],
        "is_active": True,
        "is_user_created": False
    },
    # Validation
    {
        "template_id": "validation_standard_v1",
        "prompt_type": "validation",
        "model_type": "universal",
        "prompt_version": "1.0",
        "prompt_text": """Validate the complete extraction results for consistency and accuracy.

EXTRACTION RESULTS:
{complete_extraction}

VALIDATION CHECKS:
1. Product count matches visible items
2. Positions are logical (no overlaps, sequential)
3. Prices are reasonable for product types
4. Brand names are consistent
5. No duplicate products at same position
6. Shelf assignments are correct
7. Total shelves matches structure analysis

For each issue found:
- Describe the problem
- Suggest correction
- Rate severity (low/medium/high)

Output validation results with overall confidence score.""",
        "name": "Validation - Standard",
        "description": "Validate extraction results for consistency",
        "stage_type": "validation",
        "fields": [
            {"name": "is_valid", "type": "boolean", "description": "Overall validation passed"},
            {"name": "confidence_score", "type": "number", "description": "Overall confidence 0-1"},
            {"name": "total_issues", "type": "integer", "description": "Number of issues found"},
            {"name": "issues", "type": "array", "description": "List of validation issues", "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "suggested_fix": {"type": "string"}
                }
            }}
        ],
        "tags": ["validation", "quality", "consistency"],
        "is_active": True,
        "is_user_created": False
    },
    # Planogram generation
    {
        "template_id": "planogram_generation_v1",
        "prompt_type": "planogram",
        "model_type": "universal",
        "prompt_version": "1.0",
        "prompt_text": """Generate a structured planogram from the extraction results.

EXTRACTION DATA:
{extraction_results}

STRUCTURE:
{shelf_structure}

Create a planogram that:
1. Maps each product to exact shelf and position
2. Includes facing counts and space allocation
3. Preserves the actual layout from the image
4. Notes any gaps or empty spaces
5. Includes all merchandising elements

Output as structured planogram data.""",
        "name": "Planogram Generation - Standard",
        "description": "Generate planogram from extraction results",
        "stage_type": "planogram",
        "fields": [
            {"name": "fixture_id", "type": "string", "description": "Unique fixture identifier"},
            {"name": "total_shelves", "type": "integer", "description": "Number of shelves"},
            {"name": "shelves", "type": "array", "description": "Shelf data", "items": {
                "type": "object",
                "properties": {
                    "shelf_number": {"type": "integer"},
                    "height_cm": {"type": "number"},
                    "products": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "position": {"type": "integer"},
                            "product_id": {"type": "string"},
                            "facings": {"type": "integer"},
                            "width_cm": {"type": "number"}
                        }
                    }}
                }
            }}
        ],
        "tags": ["planogram", "layout", "merchandising"],
        "is_active": True,
        "is_user_created": False
    }
]

# Insert additional prompts
print("\n=== INSERTING ADDITIONAL PROMPTS ===")
success_count = 0
for prompt in additional_prompts:
    try:
        # Ensure required fields
        prompt_data = {
            "template_id": prompt["template_id"],
            "prompt_type": prompt["prompt_type"],
            "model_type": prompt.get("model_type", "universal"),
            "prompt_version": prompt.get("prompt_version", "1.0"),
            "prompt_text": prompt["prompt_text"],
            "name": prompt.get("name", prompt["template_id"]),
            "description": prompt.get("description", ""),
            "stage_type": prompt.get("stage_type", prompt["prompt_type"]),
            "fields": json.dumps(prompt.get("fields", [])) if isinstance(prompt.get("fields", []), list) else prompt.get("fields", []),
            "tags": prompt.get("tags", []),
            "is_active": prompt.get("is_active", True),
            "is_user_created": prompt.get("is_user_created", False),
            "performance_score": 0.0,
            "usage_count": 0,
            "correction_rate": 0.0,
            "created_from_feedback": False
        }
        
        result = supabase.table('prompt_templates').insert(prompt_data).execute()
        print(f"✓ Inserted: {prompt['name']}")
        success_count += 1
        
    except Exception as e:
        print(f"✗ Failed to insert {prompt['name']}: {str(e)}")

print(f"\nInserted {success_count}/{len(additional_prompts)} prompts successfully")

# Verify complete set
print("\n=== VERIFYING COMPLETE PROMPT SET ===")
try:
    all_prompts = supabase.table('prompt_templates').select("name, prompt_type, stage_type, is_active").execute()
    
    print(f"\nTotal prompts in database: {len(all_prompts.data)}")
    
    # Group by stage
    by_stage = {}
    for prompt in all_prompts.data:
        stage = prompt.get('stage_type', prompt.get('prompt_type'))
        if stage not in by_stage:
            by_stage[stage] = []
        by_stage[stage].append(prompt)
    
    print("\nPrompts by stage:")
    for stage in ["structure", "products", "details", "validation", "comparison", "planogram", "orchestrator"]:
        if stage in by_stage:
            print(f"\n{stage.upper()} ({len(by_stage[stage])}):")
            for p in by_stage[stage]:
                active = "✓" if p.get('is_active') else "✗"
                print(f"  {active} {p.get('name')}")
        else:
            print(f"\n{stage.upper()} (0):")
            print("  ✗ No prompts")
            
except Exception as e:
    print(f"Error verifying: {str(e)}")

print("\n✅ Setup complete!")