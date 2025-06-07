#!/usr/bin/env python3
"""
Fix all queue items with Gemini models
"""

import json
from supabase import create_client

def remove_gemini_from_config(config):
    """Remove Gemini models from configuration"""
    if not isinstance(config, dict):
        return config, False
    
    updated = False
    
    # Fix stage_models
    stage_models = config.get('stage_models', {})
    for stage, models in stage_models.items():
        if isinstance(models, list):
            original_models = models.copy()
            models = [m for m in models if not m.lower().startswith('gemini')]
            
            if not models:
                models = ['gpt-4o', 'claude-3-sonnet']
            
            if models != original_models:
                stage_models[stage] = models
                updated = True
                print(f"  ✅ {stage}: {original_models} → {models}")
    
    # Fix orchestrators
    orchestrators = config.get('orchestrators', {})
    for orch_name, orch_config in orchestrators.items():
        if isinstance(orch_config, dict) and 'model' in orch_config:
            if orch_config['model'].lower().startswith('gemini'):
                orch_config['model'] = 'claude-3-sonnet'
                updated = True
                print(f"  ✅ orchestrator.{orch_name}: Changed to claude-3-sonnet")
    
    # Fix comparison config
    comparison_config = config.get('comparison_config', {})
    if isinstance(comparison_config, dict) and 'model' in comparison_config:
        if comparison_config['model'].lower().startswith('gemini'):
            comparison_config['model'] = 'gpt-4-vision-preview'
            updated = True
            print(f"  ✅ comparison_config: Changed to gpt-4-vision-preview")
    
    return config, updated

def main():
    url = 'https://fxyfzjaaehgbdemjnumt.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU'
    
    supabase = create_client(url, key)
    
    print("🔧 Fixing all queue items with Gemini models...")
    
    # Get all queue items
    response = supabase.table('ai_extraction_queue').select('*').execute()
    
    if not response.data:
        print("ℹ️  No queue items found")
        return
    
    print(f"📊 Found {len(response.data)} queue items")
    
    updated_count = 0
    
    for item in response.data:
        item_id = item['id']
        upload_id = item.get('upload_id', 'unknown')
        
        print(f"\n🔍 Checking item {item_id} ({upload_id})...")
        
        # Check extraction_config
        extraction_config = item.get('extraction_config', {})
        if isinstance(extraction_config, str):
            try:
                extraction_config = json.loads(extraction_config)
            except json.JSONDecodeError:
                print(f"  ⚠️  Invalid JSON in extraction_config")
                continue
        
        # Check model_config
        model_config = item.get('model_config', {})
        if isinstance(model_config, str):
            try:
                model_config = json.loads(model_config)
            except json.JSONDecodeError:
                print(f"  ⚠️  Invalid JSON in model_config")
                model_config = {}
        
        # Fix both configs
        extraction_updated = False
        model_updated = False
        
        if extraction_config:
            extraction_config, extraction_updated = remove_gemini_from_config(extraction_config)
        
        if model_config:
            model_config, model_updated = remove_gemini_from_config(model_config)
        
        if extraction_updated or model_updated:
            # Prepare update data
            update_data = {}
            
            if extraction_updated:
                update_data['extraction_config'] = extraction_config
            
            if model_updated:
                update_data['model_config'] = model_config
            
            # Reset failed items to pending so they can be retried
            current_status = item.get('status', '')
            if current_status == 'failed':
                update_data['status'] = 'pending'
                update_data['error_message'] = None
                print(f"  🔄 Resetting failed item to pending")
            
            # Update in database
            update_response = supabase.table('ai_extraction_queue').update(update_data).eq('id', item_id).execute()
            
            if update_response.data:
                print(f"  ✅ Updated item {item_id}")
                updated_count += 1
            else:
                print(f"  ❌ Failed to update item {item_id}")
        else:
            print(f"  ⏭️  No Gemini models found")
    
    print(f"\n🎉 Complete! Updated {updated_count} queue items")
    
    if updated_count > 0:
        print("\n✅ Extractions should now proceed without Gemini quota issues")
        print("🔄 Failed items have been reset to 'pending' status")

if __name__ == "__main__":
    main()