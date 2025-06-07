#!/usr/bin/env python3
"""
Fix the specific queue item with Gemini model issues
"""

import os
import json
from supabase import create_client

def main():
    url = 'https://fxyfzjaaehgbdemjnumt.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU'
    
    supabase = create_client(url, key)
    
    # Get the failed item
    print("🔧 Fixing queue item with Gemini models...")
    
    # The failing item has ID 9
    response = supabase.table('ai_extraction_queue').select('*').eq('id', 9).execute()
    
    if not response.data:
        print("❌ Queue item 9 not found")
        return
    
    item = response.data[0]
    print(f"📊 Found item: {item['upload_id']}")
    
    # Get current extraction config
    current_config = item.get('extraction_config', {})
    if isinstance(current_config, str):
        current_config = json.loads(current_config)
    
    print("🔍 Current stage models:")
    stage_models = current_config.get('stage_models', {})
    for stage, models in stage_models.items():
        print(f"  {stage}: {models}")
    
    # Remove Gemini models
    updated = False
    for stage, models in stage_models.items():
        if isinstance(models, list):
            original_models = models.copy()
            # Remove Gemini models
            models = [m for m in models if not m.lower().startswith('gemini')]
            
            # Ensure we have at least one model
            if not models:
                models = ['gpt-4o', 'claude-3-sonnet']
            
            if models != original_models:
                stage_models[stage] = models
                updated = True
                print(f"✅ {stage}: {original_models} → {models}")
    
    # Also check orchestrators for Gemini
    orchestrators = current_config.get('orchestrators', {})
    for orch_name, orch_config in orchestrators.items():
        if isinstance(orch_config, dict) and 'model' in orch_config:
            if orch_config['model'].lower().startswith('gemini'):
                orch_config['model'] = 'claude-3-sonnet'
                updated = True
                print(f"✅ orchestrator.{orch_name}: Changed to claude-3-sonnet")
    
    # Check comparison config
    comparison_config = current_config.get('comparison_config', {})
    if isinstance(comparison_config, dict) and 'model' in comparison_config:
        if comparison_config['model'].lower().startswith('gemini'):
            comparison_config['model'] = 'gpt-4-vision-preview'
            updated = True
            print(f"✅ comparison_config: Changed to gpt-4-vision-preview")
    
    # Also update model_config if it exists
    model_config = item.get('model_config', {})
    if isinstance(model_config, str):
        model_config = json.loads(model_config)
    
    if isinstance(model_config, dict):
        mc_stage_models = model_config.get('stage_models', {})
        for stage, models in mc_stage_models.items():
            if isinstance(models, list):
                original_models = models.copy()
                models = [m for m in models if not m.lower().startswith('gemini')]
                if not models:
                    models = ['gpt-4o', 'claude-3-sonnet']
                if models != original_models:
                    mc_stage_models[stage] = models
                    updated = True
    
    if updated:
        # Update the database
        update_data = {
            'extraction_config': current_config,
            'status': 'pending'  # Reset to pending so it can be processed again
        }
        
        if model_config:
            update_data['model_config'] = model_config
        
        update_response = supabase.table('ai_extraction_queue').update(update_data).eq('id', 9).execute()
        
        if update_response.data:
            print("✅ Updated queue item 9 successfully")
            print("🔄 Status reset to 'pending' - ready for processing")
        else:
            print("❌ Failed to update queue item")
    else:
        print("ℹ️  No Gemini models found to remove")

if __name__ == "__main__":
    main()