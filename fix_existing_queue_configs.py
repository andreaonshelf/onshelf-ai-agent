#!/usr/bin/env python3
"""Fix existing queue items that have extraction_config without stages"""

from src.config import SystemConfig
from supabase import create_client
import json

config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key)

print("🔧 Fixing existing queue configurations...")

# Get all queue items with extraction_config but no stages
result = supabase.table("ai_extraction_queue").select("*").execute()

items_to_fix = []
for item in result.data:
    extraction_config = item.get('extraction_config')
    if extraction_config and not extraction_config.get('stages'):
        items_to_fix.append(item)

print(f"\nFound {len(items_to_fix)} items with incomplete configurations")

# Fix each item
fixed_count = 0
for item in items_to_fix:
    queue_id = item['id']
    extraction_config = item['extraction_config']
    system = extraction_config.get('system', 'custom_consensus')
    
    print(f"\nFixing item {queue_id} (system: {system})...")
    
    # Build stages
    stages = {}
    prompt_types = ['structure', 'products', 'details', 'visual']
    
    for prompt_type in prompt_types:
        # Try to get prompt from database
        prompt_result = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type).eq("is_active", True).limit(1).execute()
        
        if prompt_result.data:
            prompt_data = prompt_result.data[0]
            stages[prompt_type] = {
                "prompt_text": prompt_data.get('prompt_text', f"Extract {prompt_type} from the image"),
                "fields": prompt_data.get('extraction_fields', [])
            }
            print(f"  ✓ Loaded {prompt_type} prompt from database")
        else:
            # Use defaults
            if prompt_type == 'structure':
                stages[prompt_type] = {
                    "prompt_text": "Extract the shelf structure from this retail shelf image. Identify shelf levels and sections.",
                    "fields": []
                }
            elif prompt_type == 'products':
                stages[prompt_type] = {
                    "prompt_text": "Extract all products from this retail shelf image. Include brand, name, price, and position.",
                    "fields": []
                }
            elif prompt_type == 'visual':
                stages[prompt_type] = {
                    "prompt_text": "Compare the extracted data with the original image to verify accuracy.",
                    "fields": []
                }
            else:
                stages[prompt_type] = {
                    "prompt_text": f"Extract {prompt_type} information from the retail shelf image.",
                    "fields": []
                }
            print(f"  ⚠ Using default for {prompt_type}")
    
    # Update the configuration
    extraction_config['stages'] = stages
    
    # Save back to database
    update_result = supabase.table("ai_extraction_queue").update({
        "extraction_config": extraction_config
    }).eq("id", queue_id).execute()
    
    if update_result.data:
        print(f"  ✅ Fixed configuration for item {queue_id}")
        fixed_count += 1
    else:
        print(f"  ❌ Failed to update item {queue_id}")

print(f"\n✅ Fixed {fixed_count} out of {len(items_to_fix)} items")
print("\nQueue items are now ready for processing with complete configurations!")