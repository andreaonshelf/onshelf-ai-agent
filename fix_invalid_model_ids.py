#!/usr/bin/env python3
"""
Fix invalid model IDs in queue configurations
"""

import json
from supabase import create_client

def fix_model_id(model_id):
    """Fix common model ID issues"""
    fixes = {
        'claude-3-7-sonnet': 'claude-3-5-sonnet',  # Typo fix
        'gpt-4.1': 'gpt-4o',  # Non-existent model fix
        'gpt-4.1-preview': 'gpt-4o',
        'claude-3.7-sonnet': 'claude-3.5-sonnet',
        'gemini-2.5-pro': 'gpt-4o',  # Remove Gemini
        'gemini-pro': 'gpt-4o',  # Remove Gemini
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
    
    return config, updated

def main():
    url = 'https://fxyfzjaaehgbdemjnumt.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU'
    
    supabase = create_client(url, key)
    
    print("🔧 Fixing invalid model IDs in queue configurations...")
    
    response = supabase.table('ai_extraction_queue').select('*').execute()
    
    updated_count = 0
    
    for item in response.data:
        item_id = item['id']
        upload_id = item.get('upload_id', 'unknown')
        
        print(f"\n🔍 Checking item {item_id} ({upload_id})...")
        
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
        print("🔄 Extractions should now succeed")

if __name__ == "__main__":
    main()