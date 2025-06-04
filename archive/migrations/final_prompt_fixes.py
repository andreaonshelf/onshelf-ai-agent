#!/usr/bin/env python3
"""
Final fixes: Add missing products prompt and remove details prompt.
"""
import os
import json
import uuid
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Missing Supabase credentials in environment variables")
    exit(1)

# Create Supabase client
supabase = create_client(supabase_url, supabase_key)

# Products field definitions from our earlier script
PRODUCTS_FIELD_DEFINITIONS = [
    {
        "name": "products",
        "type": "array",
        "required": True,
        "description": "Array of product objects found on shelves",
        "items": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Unique identifier for this product instance"},
                "shelf_number": {"type": "integer", "description": "Which shelf the product is on (1 = top)"},
                "section_number": {"type": "integer", "description": "Which section of the shelf (1 = leftmost)"},
                "position_in_section": {"type": "integer", "description": "Position within the section (1 = leftmost)"},
                "position_x_cm": {"type": "number", "description": "Horizontal position from left edge of shelf in cm"},
                "position_y_cm": {"type": "number", "description": "Vertical position from top of shelf in cm"},
                "facing_count": {"type": "integer", "description": "Number of product facings visible"},
                "product_name": {"type": "string", "description": "Product name visible on packaging"},
                "brand": {"type": "string", "description": "Brand name if visible"},
                "size": {"type": "string", "description": "Product size/weight if visible"},
                "upc": {"type": "string", "description": "UPC code if visible"},
                "price": {"type": "string", "description": "Price if visible on shelf tag"},
                "orientation": {"type": "string", "enum": ["front", "side", "back", "angled"], "description": "How the product is facing"}
            }
        }
    },
    {
        "name": "total_products",
        "type": "integer",
        "required": True,
        "description": "Total number of unique products identified"
    },
    {
        "name": "total_facings",
        "type": "integer",
        "required": True,
        "description": "Total number of product facings across all products"
    }
]

# Products prompt template based on the agreed document
PRODUCTS_PROMPT_TEMPLATE = """You are analyzing a shelf image to identify all visible products.

Extract information about every product you can see on the shelves. For each product, identify:
- Its position on the shelf (shelf number and horizontal position)
- The number of facings (how many of the same product are visible side-by-side)
- Any visible product information (name, brand, size, price)

Important guidelines:
1. Count shelves from top (1) to bottom
2. Measure positions from the left edge of each shelf
3. Each unique product should have a unique product_id
4. Count facings carefully - multiple items of the same product count as multiple facings
5. If you can't see certain details clearly, omit them rather than guessing

Return the data in the specified JSON schema format."""

def final_fixes():
    """Apply final fixes to the prompt templates."""
    
    print("Applying final fixes...")
    
    # 1. Remove the 'details' prompt
    print("\n1. Removing 'details' prompt...")
    try:
        response = supabase.table('prompt_templates').select('*').eq('prompt_type', 'details').execute()
        if response.data:
            for prompt in response.data:
                supabase.table('prompt_templates').delete().eq('prompt_id', prompt['prompt_id']).execute()
                print(f"   Deleted 'details' prompt: {prompt['prompt_id']}")
        else:
            print("   No 'details' prompt found")
    except Exception as e:
        print(f"   Error removing 'details' prompt: {e}")
    
    # 2. Add the missing 'products' prompt
    print("\n2. Adding 'products' prompt with proper definition...")
    
    # Check if a products prompt already exists
    existing = supabase.table('prompt_templates').select('*').eq('prompt_type', 'products').execute()
    
    if not existing.data:
        # Create new products prompt
        new_prompt = {
            "prompt_id": str(uuid.uuid4()),
            "template_id": str(uuid.uuid4()),
            "prompt_type": "products",
            "model_type": "gpt-4o",
            "prompt_version": "1.0.0",
            "prompt_text": PRODUCTS_PROMPT_TEMPLATE,
            "performance_score": 0.85,
            "usage_count": 0,
            "correction_rate": 0.0,
            "is_active": True,
            "created_from_feedback": False,
            "name": "Initial Product Extraction",
            "description": "Initial extraction of all products visible on shelves",
            "fields": ["products", "total_products", "total_facings"],
            "stage_type": "extraction",
            "tags": ["products", "initial", "extraction"],
            "is_system_generated": True,
            "is_public": True,
            "overall_performance_score": 0.85,
            "overall_usage_count": 0,
            "overall_avg_cost": 0.0,
            "field_definitions": PRODUCTS_FIELD_DEFINITIONS,
            "is_user_created": False,
            "autonomy_level": 1,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            result = supabase.table('prompt_templates').insert(new_prompt).execute()
            print(f"   Created new 'products' prompt: {new_prompt['prompt_id']}")
        except Exception as e:
            print(f"   Error creating 'products' prompt: {e}")
    else:
        print("   'products' prompt already exists")
    
    # 3. Verify final state
    print("\n3. Final verification...")
    response = supabase.table('prompt_templates').select('prompt_type, description, field_definitions').order('prompt_type').execute()
    
    print(f"\nTotal prompts: {len(response.data)}")
    
    # Count by type
    type_counts = {}
    for prompt in response.data:
        prompt_type = prompt['prompt_type']
        type_counts[prompt_type] = type_counts.get(prompt_type, 0) + 1
    
    print("\nPrompt types:")
    for prompt_type in sorted(type_counts.keys()):
        count = type_counts[prompt_type]
        print(f"  - {prompt_type}: {count} prompt{'s' if count > 1 else ''}")
    
    # Check field definitions
    print("\nField definitions status:")
    for prompt_type in ['structure', 'products', 'position', 'detail', 'validation']:
        matching = [p for p in response.data if p['prompt_type'] == prompt_type and p.get('field_definitions')]
        if matching:
            print(f"  ✓ {prompt_type} - Has field definitions")
        else:
            print(f"  ✗ {prompt_type} - Missing field definitions")

if __name__ == "__main__":
    final_fixes()