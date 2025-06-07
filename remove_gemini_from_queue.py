#!/usr/bin/env python3
"""
Remove Gemini models from all queue item configurations to allow extractions to proceed
without hitting Gemini quota limits.
"""

import os
import sys
import json
from supabase import create_client

def get_supabase_client():
    """Get Supabase client"""
    url = os.getenv('SUPABASE_URL', 'https://fxyfzjaaehgbdemjnumt.supabase.co')
    key = os.getenv('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU')
    
    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        sys.exit(1)
    
    return create_client(url, key)

def remove_gemini_from_config(config):
    """Remove Gemini models from stage_models configuration"""
    if not isinstance(config, dict):
        return config
    
    stage_models = config.get('stage_models', {})
    updated = False
    
    for stage, models in stage_models.items():
        if isinstance(models, list):
            # Remove Gemini models
            original_count = len(models)
            models = [m for m in models if not m.lower().startswith('gemini')]
            
            # Ensure we still have at least one model
            if not models:
                models = ['gpt-4o', 'claude-3-sonnet']  # Default fallback
                print(f"⚠️  Stage '{stage}' had only Gemini models, adding fallback models")
            
            if len(models) != original_count:
                stage_models[stage] = models
                updated = True
                print(f"✅ Stage '{stage}': Removed Gemini, now using {models}")
    
    if updated:
        config['stage_models'] = stage_models
    
    return config, updated

def main():
    """Main function to remove Gemini from all queue configurations"""
    
    print("🔧 Removing Gemini models from queue configurations...")
    
    try:
        supabase = get_supabase_client()
        
        # Get all queue items with configurations
        print("📡 Fetching queue items...")
        response = supabase.table('processing_queue').select('*').execute()
        
        if not response.data:
            print("ℹ️  No queue items found")
            return
        
        print(f"📊 Found {len(response.data)} queue items")
        
        updated_count = 0
        
        for item in response.data:
            item_id = item['id']
            config = item.get('extraction_config')
            
            if not config:
                print(f"⏭️  Item {item_id}: No extraction config")
                continue
            
            # Parse config if it's a string
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except json.JSONDecodeError:
                    print(f"⚠️  Item {item_id}: Invalid JSON config")
                    continue
            
            # Remove Gemini models
            updated_config, was_updated = remove_gemini_from_config(config)
            
            if was_updated:
                # Convert back to string if needed
                if isinstance(item.get('extraction_config'), str):
                    updated_config = json.dumps(updated_config)
                
                # Update in database
                update_response = supabase.table('processing_queue').update({
                    'extraction_config': updated_config
                }).eq('id', item_id).execute()
                
                if update_response.data:
                    print(f"✅ Item {item_id}: Updated configuration")
                    updated_count += 1
                else:
                    print(f"❌ Item {item_id}: Failed to update")
            else:
                print(f"⏭️  Item {item_id}: No Gemini models found")
        
        print(f"\n🎉 Complete! Updated {updated_count} queue items")
        
        if updated_count > 0:
            print("\n✅ Extractions should now proceed without Gemini quota issues")
            print("🔄 You can now try processing queue items again")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()