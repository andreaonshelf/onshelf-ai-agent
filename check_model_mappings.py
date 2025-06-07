#!/usr/bin/env python3
"""
Check what model IDs are actually being used vs what should be available
"""

from supabase import create_client

def main():
    url = 'https://fxyfzjaaehgbdemjnumt.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ4eWZ6amFhZWhnYmRlbWpudW10Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEwMDkxNywiZXhwIjoyMDYxNjc2OTE3fQ.Ud0qATx3LuZwMzdsD3HAd98TDthjXzQbsQvAk7RCmyU'
    
    supabase = create_client(url, key)
    
    print("🔍 Checking model mappings in queue configurations...")
    
    # Get all queue items
    response = supabase.table('ai_extraction_queue').select('*').execute()
    
    all_models = set()
    
    for item in response.data:
        print(f"\n📊 Item {item['id']} ({item.get('upload_id', 'unknown')}):")
        
        # Check extraction_config
        extraction_config = item.get('extraction_config', {})
        if isinstance(extraction_config, str):
            import json
            try:
                extraction_config = json.loads(extraction_config)
            except:
                continue
        
        stage_models = extraction_config.get('stage_models', {})
        for stage, models in stage_models.items():
            if isinstance(models, list):
                print(f"  {stage}: {models}")
                all_models.update(models)
        
        # Check orchestrators
        orchestrators = extraction_config.get('orchestrators', {})
        for orch_name, orch_config in orchestrators.items():
            if isinstance(orch_config, dict) and 'model' in orch_config:
                print(f"  orchestrator.{orch_name}: {orch_config['model']}")
                all_models.add(orch_config['model'])
    
    print(f"\n🎯 All unique model IDs found:")
    for model in sorted(all_models):
        print(f"  - {model}")
    
    print(f"\n💭 Expected Claude 4.0 model IDs should be something like:")
    print(f"  - claude-4-opus")
    print(f"  - claude-4-sonnet") 
    print(f"  - claude-4.0")
    print(f"  - claude-3.5-sonnet")
    
    print(f"\n⚠️  Model ID 'claude-3-7-sonnet' looks incorrect!")
    print(f"   Should probably be 'claude-3.5-sonnet' or 'claude-4-opus'")

if __name__ == "__main__":
    main()