"""
Fix script to ensure all extraction stages use dynamic models from user configurations
"""

import asyncio
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_and_fix_dynamic_models():
    """Verify that stages are using dynamic models"""
    
    # Check the current implementation
    print("=== CURRENT ISSUE ===")
    print("1. Structure stage: Uses hardcoded 'ShelfStructure' schema")
    print("2. Products stage: Uses hardcoded 'List[ProductExtraction]' schema")
    print("3. Details stage: Uses hardcoded 'List[ProductExtraction]' schema")
    print("\nNONE of the stages are using the user-configured fields!")
    print("\n=== WHAT NEEDS TO BE FIXED ===")
    print("1. Check if stage_fields[stage_name] exists and has fields")
    print("2. Use DynamicModelBuilder.build_model_from_config() to create dynamic models")
    print("3. Pass the dynamic model to extraction engine instead of hardcoded strings")
    
    # Connect to database
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    
    # Check a recent configuration
    result = supabase.table("ai_extraction_queue") \
        .select("id, model_config") \
        .not_.is_("model_config", "null") \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute()
    
    if result.data and result.data[0].get("model_config"):
        config = result.data[0]["model_config"]
        stages = config.get("stages", {})
        
        print(f"\n=== SAMPLE CONFIGURATION (Queue ID: {result.data[0]['id']}) ===")
        for stage_name, stage_config in stages.items():
            if isinstance(stage_config, dict) and "fields" in stage_config:
                print(f"\n{stage_name.upper()} stage has {len(stage_config['fields'])} configured fields:")
                for field in stage_config['fields'][:3]:  # Show first 3 fields
                    print(f"  - {field.get('name')}: {field.get('type')}")
                if len(stage_config['fields']) > 3:
                    print(f"  ... and {len(stage_config['fields']) - 3} more fields")
    
    print("\n=== PROPOSED FIX ===")
    print("""
The fix needs to be applied in extraction_orchestrator.py:

1. In _execute_structure_stage():
   - Check if self.stage_fields.get('structure') exists
   - Build dynamic model: DynamicModelBuilder.build_model_from_config(fields, 'ShelfStructureV1')
   - Pass model instance instead of "ShelfStructure" string

2. In _execute_shelf_by_shelf_extraction():
   - Check if self.stage_fields.get('products') exists  
   - Build dynamic model: DynamicModelBuilder.build_model_from_config(fields, 'ProductExtractionV1')
   - Create List type: List[DynamicProductModel]
   - Pass model instance instead of "List[ProductExtraction]" string

3. In _execute_details_stage():
   - Check if self.stage_fields.get('details') exists
   - Build dynamic model: DynamicModelBuilder.build_model_from_config(fields, 'DetailExtractionV1')
   - Create List type: List[DynamicDetailModel]
   - Pass model instance instead of "List[ProductExtraction]" string
""")

if __name__ == "__main__":
    asyncio.run(verify_and_fix_dynamic_models())