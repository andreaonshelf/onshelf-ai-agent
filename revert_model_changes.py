#!/usr/bin/env python3
"""
Revert the model ID changes - restore original user selections
The backend should adapt to UI models, not the other way around!
"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# These were the ORIGINAL user selections that should be restored
REVERT_MAP = {
    # Queue ID 9 (Co-op Food) original selections
    9: {
        'extraction_config': {
            'stage_models': {
                'details': ['gpt-4.1', 'gemini-2.5-pro'],
                'products': ['gpt-4.1', 'claude-3-5-sonnet-v2', 'gemini-2.5-pro'],
                'structure': ['gpt-4.1', 'claude-3-5-sonnet-v2'],
                'comparison': ['gpt-4.1', 'claude-4-opus', 'gemini-2.5-pro']
            }
        }
    },
    # Queue ID 6 original selections
    6: {
        'extraction_config': {
            'stage_models': {
                'details': ['gpt-4.1', 'gemini-2.5-pro'],
                'products': ['gpt-4.1', 'claude-3-5-sonnet-v2', 'gemini-2.5-pro'],
                'structure': ['gpt-4.1', 'claude-3-5-sonnet-v2'],
                'comparison': ['gpt-4.1', 'claude-4-opus', 'gemini-2.5-pro']
            }
        }
    }
}

def main():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("🔄 Reverting model changes - restoring user's original selections...")
    print("📝 The backend should adapt to UI models, not change user selections!\n")
    
    for queue_id, original_config in REVERT_MAP.items():
        print(f"Reverting Queue ID {queue_id}...")
        
        # Get current item
        result = supabase.table('ai_extraction_queue').select('*').eq('id', queue_id).execute()
        
        if result.data:
            item = result.data[0]
            
            # Get current extraction_config
            current_config = item.get('extraction_config', {})
            if isinstance(current_config, str):
                current_config = json.loads(current_config)
            
            # Restore original stage_models
            if 'stage_models' in original_config['extraction_config']:
                current_config['stage_models'] = original_config['extraction_config']['stage_models']
                
                # Update in database
                update_response = supabase.table('ai_extraction_queue').update({
                    'extraction_config': current_config
                }).eq('id', queue_id).execute()
                
                if update_response.data:
                    print(f"✅ Restored original selections for Queue ID {queue_id}")
                    for stage, models in original_config['extraction_config']['stage_models'].items():
                        print(f"   {stage}: {models}")
                else:
                    print(f"❌ Failed to update Queue ID {queue_id}")
        print()
    
    print("\n✅ User selections have been restored!")
    print("\n📌 Next step: Update the backend extraction engine to support these UI models:")
    print("   - gpt-4.1 (map to appropriate API model)")
    print("   - claude-3-5-sonnet-v2 (map to appropriate API model)")
    print("   - claude-4-sonnet (map to appropriate API model)")
    print("   - gemini-2.5-pro (map to appropriate API model)")

if __name__ == "__main__":
    main()