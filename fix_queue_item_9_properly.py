#!/usr/bin/env python3
"""
Fix queue item 9 PROPERLY - restore LangGraph configuration with all stages including visual
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def load_field_schema(filename):
    """Load field schema from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load {filename}: {e}")
        return None

def fix_queue_item_9_properly():
    """Restore proper LangGraph configuration for queue item 9"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("=" * 80)
    print("FIXING QUEUE ITEM 9 PROPERLY - RESTORING LANGGRAPH CONFIG")
    print("=" * 80)
    
    # Load field schemas
    print("📥 Loading field schemas...")
    structure_fields = load_field_schema('ui_schema_structure_v1.json')
    products_fields = load_field_schema('ui_schema_product_v1.json')
    details_fields = load_field_schema('ui_schema_detail_v1.json')
    
    if not all([structure_fields, products_fields, details_fields]):
        print("❌ Could not load all field schemas!")
        return
    
    # Build proper LangGraph configuration
    print("🔧 Building proper LangGraph configuration...")
    
    extraction_config = {
        "system": "langgraph",  # CORRECT: Use LangGraph
        "max_budget": 3,
        "temperature": 0.1,
        "stages": {
            "structure": {
                "fields": [structure_fields],
                "prompt_text": "Analyze this retail shelf image to identify the physical structure.\n\nCOUNT:\n□ Number of horizontal shelves (bottom = 1, count up)\n□ Each product display level = one shelf\n□ Include floor level only if products are placed there\n\nMEASURE:\n□ Fixture width: _____ meters (estimate)\n□ Fixture height: _____ meters (estimate)\n□ Fixture type: wall_shelf | gondola | end_cap | cooler | freezer | bin | pegboard | other\n\nIDENTIFY NON-PRODUCT ELEMENTS:\n□ Security devices: grids, magnetic tags, plastic cases, bottle locks\n□ Promotional materials: shelf wobblers, hanging signs, price cards, banners\n□ Shelf equipment: dividers, pushers, price rails, shelf strips\n□ Display accessories: hooks, clip strips, shelf talkers\n□ Fixtures: end panels, header boards, base decks\n\nOutput the total shelf count and all fixture details.\n\n{IF_RETRY}\nPREVIOUS ATTEMPT: {SHELVES} shelves found\nUncertainty areas: {PROBLEM_AREAS}\n\nCommon issues to verify:\n- Is the bottom/floor level actually holding products?\n- Are there partial shelves at the top?\n- Did they count dividers as separate shelves?\n\nNOTE: Trust your own analysis over previous attempts.\n{/IF_RETRY}"
            },
            "products": {
                "fields": [products_fields],
                "prompt_text": "Extract all products from this retail shelf image. Include brand, name, price, and position."
            },
            "details": {
                "fields": [details_fields],
                "prompt_text": "Extract details information from the retail shelf image."
            },
            "visual": {
                "fields": [],
                "prompt_text": "Compare the extracted data with the original image to verify accuracy."
            }
        },
        "stage_models": {
            "structure": ["gpt-4o", "claude-3-sonnet"],
            "products": ["gpt-4o", "claude-3-sonnet", "gemini-2.0-flash-exp"],
            "details": ["gpt-4o", "gemini-2.0-flash-exp"],
            "comparison": ["gpt-4o", "claude-3-opus-20240229", "gemini-2.0-flash-exp"]
        },
        "orchestrators": {
            "master": {
                "model": "claude-3-opus-20240229",
                "prompt": ""
            },
            "planogram": {
                "model": "gpt-4o-mini",
                "prompt": ""
            },
            "extraction": {
                "model": "claude-3-5-sonnet",
                "prompt": ""
            }
        }
    }
    
    # Update the queue item
    print("💾 Saving corrected LangGraph configuration...")
    
    update_result = supabase.table("ai_extraction_queue").update({
        "extraction_config": extraction_config,
        "status": "pending",
        "error_message": None,
        "failed_at": None,
        "started_at": None,
        "completed_at": None
    }).eq("id", 9).execute()
    
    if update_result.data:
        print("✅ Queue item 9 updated with proper LangGraph configuration!")
        print("\n📋 Configuration summary:")
        print(f"  - System: {extraction_config['system']}")
        print(f"  - Stages: {list(extraction_config['stages'].keys())}")
        for stage, config in extraction_config['stages'].items():
            field_count = len(config.get('fields', []))
            models = extraction_config['stage_models'].get(stage, [])
            print(f"  - {stage}: {field_count} field groups, models: {models}")
    else:
        print("❌ Failed to update queue item 9!")

if __name__ == "__main__":
    fix_queue_item_9_properly()