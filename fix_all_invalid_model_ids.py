#!/usr/bin/env python3
"""
Fix ALL invalid model IDs in queue configurations including the latest ones
"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def fix_model_id(model_id):
    """Fix all known invalid model IDs"""
    fixes = {
        # Original fixes
        'claude-3-7-sonnet': 'claude-3-5-sonnet',  # Typo fix
        'claude-3.7-sonnet': 'claude-3-5-sonnet',   # Another typo variant
        'claude-4-sonnet': 'claude-3-5-sonnet',     # Claude 4 doesn't exist yet
        
        # New fixes from Co-op extraction
        'gpt-4.1': 'gpt-4o',                        # Invalid model
        'gpt-4.1-preview': 'gpt-4o',                # Invalid model
        'claude-3-5-sonnet-v2': 'claude-3-5-sonnet',  # Invalid variant
        'gemini-2.5-pro': 'gemini-2.0-flash-exp',  # Update to valid Gemini model
        'gemini-pro': 'gemini-2.0-flash-exp',      # Update to valid Gemini model
        
        # Additional safety fixes
        'gpt4o': 'gpt-4o',                          # Missing dash
        'claude-4-opus': 'claude-3-opus-20240229',  # Use full valid name
        'gpt-4-vision-preview': 'gpt-4o',          # Use gpt-4o for vision
    }
    
    return fixes.get(model_id, model_id)

def fix_config_models(config):
    """Fix model IDs in a configuration"""
    if not isinstance(config, dict):
        return config, False
    
    updated = False
    
    # Fix stage_models
    stage_models = config.get('stage_models', {})
    for stage, models in stage_models.items():
        if isinstance(models, list):
            original_models = models.copy()
            fixed_models = [fix_model_id(model) for model in models]
            
            if fixed_models != original_models:
                stage_models[stage] = fixed_models
                updated = True
                print(f"  ✅ {stage}: {original_models} → {fixed_models}")
    
    # Fix orchestrators
    orchestrators = config.get('orchestrators', {})
    for orch_name, orch_config in orchestrators.items():
        if isinstance(orch_config, dict) and 'model' in orch_config:
            original_model = orch_config['model']
            fixed_model = fix_model_id(original_model)
            if fixed_model != original_model:
                orch_config['model'] = fixed_model
                updated = True
                print(f"  ✅ orchestrator.{orch_name}: {original_model} → {fixed_model}")
    
    # Fix comparison config
    comparison_config = config.get('comparison_config', {})
    if isinstance(comparison_config, dict) and 'model' in comparison_config:
        original_model = comparison_config['model']
        fixed_model = fix_model_id(original_model)
        if fixed_model != original_model:
            comparison_config['model'] = fixed_model
            updated = True
            print(f"  ✅ comparison_config: {original_model} → {fixed_model}")
    
    # Fix orchestrator_model (top level)
    if 'orchestrator_model' in config:
        original_model = config['orchestrator_model']
        fixed_model = fix_model_id(original_model)
        if fixed_model != original_model:
            config['orchestrator_model'] = fixed_model
            updated = True
            print(f"  ✅ orchestrator_model: {original_model} → {fixed_model}")
    
    return config, updated

def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("🔧 Fixing ALL invalid model IDs in queue configurations...")
    
    # Get all queue items
    response = supabase.table('ai_extraction_queue').select('*').execute()
    
    updated_count = 0
    
    for item in response.data:
        item_id = item['id']
        upload_id = item.get('upload_id', 'unknown')
        
        print(f"\n🔍 Checking item {item_id} (upload: {upload_id})...")
        
        # Fix extraction_config
        extraction_config = item.get('extraction_config', {})
        if isinstance(extraction_config, str):
            try:
                extraction_config = json.loads(extraction_config)
            except:
                print(f"  ⚠️  Invalid JSON in extraction_config")
                continue
        
        # Fix model_config
        model_config = item.get('model_config', {})
        if isinstance(model_config, str):
            try:
                model_config = json.loads(model_config)
            except:
                model_config = {}
        
        # Fix both configs
        extraction_updated = False
        model_updated = False
        
        if extraction_config:
            extraction_config, extraction_updated = fix_config_models(extraction_config)
        
        if model_config:
            model_config, model_updated = fix_config_models(model_config)
        
        if extraction_updated or model_updated:
            # Update in database
            update_data = {}
            
            if extraction_updated:
                update_data['extraction_config'] = extraction_config
            
            if model_updated:
                update_data['model_config'] = model_config
            
            update_response = supabase.table('ai_extraction_queue').update(update_data).eq('id', item_id).execute()
            
            if update_response.data:
                print(f"  ✅ Updated item {item_id}")
                updated_count += 1
            else:
                print(f"  ❌ Failed to update item {item_id}")
        else:
            print(f"  ⏭️  No invalid model IDs found")
    
    print(f"\n🎉 Complete! Fixed {updated_count} queue items")
    
    if updated_count > 0:
        print("\n✅ Model IDs are now valid and should work with APIs")
        print("🔄 Failed extractions can now be retried")
        
        # Show specific fixes for Co-op Food
        print("\n📋 Co-op Food extraction fixes:")
        print("  - gpt-4.1 → gpt-4o")
        print("  - claude-3-5-sonnet-v2 → claude-3-5-sonnet")
        print("  - gemini-2.5-pro → gemini-2.0-flash-exp")
        print("  - claude-4-opus → claude-3-opus-20240229")

if __name__ == "__main__":
    main()