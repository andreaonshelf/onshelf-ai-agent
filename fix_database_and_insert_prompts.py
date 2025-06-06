import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from datetime import datetime
import uuid

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

# First, clear existing prompts to start fresh
print("\n=== CLEARING EXISTING PROMPTS ===")
try:
    delete_result = supabase.table('prompt_templates').delete().neq('prompt_id', '00000000-0000-0000-0000-000000000000').execute()
    print(f"Cleared {len(delete_result.data)} existing prompts")
except Exception as e:
    print(f"Error clearing prompts: {str(e)}")

# Default prompts to insert
default_prompts = [
    # Orchestrator prompts
    {
        "template_id": "orchestrator_main_v1",
        "prompt_type": "orchestrator",
        "model_type": "universal",
        "prompt_version": "1.0",
        "prompt_text": """You are the Master Orchestrator for an AI extraction pipeline analyzing retail shelf images.

OBJECTIVE: Direct the extraction pipeline to accurately identify all products, positions, prices, and metadata.

CURRENT STATE:
{current_state}

EXTRACTION HISTORY:
{history}

CONFIDENCE SCORES:
{confidence_scores}

AVAILABLE ACTIONS:
1. run_structure_analysis - Analyze shelf structure and layout
2. run_product_extraction - Extract product information
3. run_detail_enhancement - Enhance product details
4. run_comparison - Compare with reference data
5. mark_complete - Finalize extraction
6. request_human_review - Escalate for human input

{IF_RETRY}
PREVIOUS ATTEMPT FAILED:
{retry_context}
- Previous error: {error_message}
- Attempted action: {failed_action}

You must try a different approach or use different parameters.
{/IF_RETRY}

Based on the current state and confidence scores, decide the next best action to improve extraction accuracy.

Output your decision as JSON:
{
    "action": "action_name",
    "reasoning": "why this action will help",
    "parameters": {...},
    "expected_improvement": "what this will achieve"
}""",
        "name": "Master Orchestrator - Main",
        "description": "Main orchestrator prompt for directing the extraction pipeline",
        "stage_type": "orchestrator",
        "fields": [],
        "tags": ["orchestrator", "main", "system"],
        "is_active": True,
        "is_user_created": False
    },
    # Structure prompts
    {
        "template_id": "structure_extraction_standard_v1",
        "prompt_type": "structure",
        "model_type": "universal",
        "prompt_version": "1.0",
        "prompt_text": """Analyze this retail shelf image to identify the physical structure.

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
□ Empty spaces: gaps between products, out-of-stock sections
□ Fixtures: end panels, header boards, base decks

Output the total shelf count and all fixture details.""",
        "name": "Structure Extraction - Standard",
        "description": "Initial prompt for extracting shelf physical structure",
        "stage_type": "structure",
        "fields": [
            {"name": "shelf_count", "type": "integer", "description": "Total number of shelves"},
            {"name": "fixture_width", "type": "number", "description": "Width in meters"},
            {"name": "fixture_height", "type": "number", "description": "Height in meters"},
            {"name": "fixture_type", "type": "string", "description": "Type of fixture"}
        ],
        "tags": ["structure", "shelves", "layout"],
        "is_active": True,
        "is_user_created": False
    },
    # Product extraction prompts
    {
        "template_id": "product_extraction_standard_v1",
        "prompt_type": "position",
        "model_type": "universal", 
        "prompt_version": "1.0",
        "prompt_text": """Extract all visible products from this retail shelf image.

For each product, identify:
- Brand name
- Product name/description
- Size/volume if visible
- Price if visible
- Number of facings (units visible side by side)
- Shelf position (counting from left)
- Shelf number (counting from bottom)
- Any promotional tags

Focus on accuracy and only extract clearly visible products. If uncertain about any detail, mark it as unclear rather than guessing.""",
        "name": "Product Extraction - Standard",
        "description": "Standard prompt for extracting product information",
        "stage_type": "products",
        "fields": [
            {"name": "brand", "type": "string", "description": "Product brand name", "required": True},
            {"name": "name", "type": "string", "description": "Product name or description", "required": True},
            {"name": "size", "type": "string", "description": "Product size or volume", "required": False},
            {"name": "price", "type": "number", "description": "Product price", "required": False},
            {"name": "facing_count", "type": "integer", "description": "Number of facings", "required": True, "default": 1},
            {"name": "position_x", "type": "integer", "description": "Position on shelf from left", "required": True},
            {"name": "shelf_number", "type": "integer", "description": "Shelf number from bottom", "required": True},
            {"name": "promotional", "type": "boolean", "description": "Has promotional tag", "required": False, "default": False}
        ],
        "tags": ["products", "extraction", "standard"],
        "is_active": True,
        "is_user_created": False
    },
    # Comparison prompts
    {
        "template_id": "comparison_standard_v1",
        "prompt_type": "comparison",
        "model_type": "universal",
        "prompt_version": "1.0",
        "prompt_text": """Compare the extracted products with reference data to verify accuracy.

EXTRACTED PRODUCTS:
{extracted_products}

REFERENCE DATA:
{reference_data}

For each extracted product:
1. Find the best match in reference data
2. Calculate confidence score (0-100%)
3. Note any discrepancies
4. Flag products not found in reference

Output comparison results with confidence scores and any issues found.""",
        "name": "Comparison - Standard",
        "description": "Standard prompt for comparing extracted data with reference",
        "stage_type": "comparison",
        "fields": [
            {"name": "match_confidence", "type": "number", "description": "Overall match confidence %"},
            {"name": "matched_products", "type": "integer", "description": "Number of matched products"},
            {"name": "unmatched_products", "type": "integer", "description": "Number of unmatched products"},
            {"name": "discrepancies", "type": "array", "description": "List of discrepancies found"}
        ],
        "tags": ["comparison", "validation", "accuracy"],
        "is_active": True,
        "is_user_created": False
    }
]

# Insert default prompts
print("\n=== INSERTING DEFAULT PROMPTS ===")
success_count = 0
for prompt in default_prompts:
    try:
        # Ensure required fields - only use columns that exist
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

print(f"\nInserted {success_count}/{len(default_prompts)} prompts successfully")

# Verify what's in the database
print("\n=== VERIFYING DATABASE CONTENTS ===")
try:
    all_prompts = supabase.table('prompt_templates').select("template_id, name, prompt_type, stage_type, is_active").execute()
    
    print(f"\nTotal prompts in database: {len(all_prompts.data)}")
    
    # Group by type
    by_type = {}
    for prompt in all_prompts.data:
        ptype = prompt.get('prompt_type', 'unknown')
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(prompt)
    
    print("\nPrompts by type:")
    for ptype, prompts in by_type.items():
        print(f"\n{ptype.upper()} ({len(prompts)}):")
        for p in prompts:
            active = "✓" if p.get('is_active') else "✗"
            print(f"  {active} {p.get('name')} (stage: {p.get('stage_type')})")
            
except Exception as e:
    print(f"Error verifying database: {str(e)}")

print("\n✅ Database setup complete!")
print("\nThe dashboard should now be able to:")
print("1. Load prompts for each stage")
print("2. Display them in the sidebar")
print("3. Allow creating and saving new prompts")
print("4. Switch between different prompt versions")