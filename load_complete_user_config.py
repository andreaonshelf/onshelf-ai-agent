#!/usr/bin/env python3
"""
Load the user's complete prompt configuration from database
This shows what the system SHOULD be loading automatically
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def load_complete_user_config():
    """Load the user's complete prompt and field configuration"""
    
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    print("🔍 Loading user's complete prompt configuration from database...")
    
    # Get all active prompts
    result = supabase.table("prompt_templates").select("*").eq("is_active", True).execute()
    
    if not result.data:
        print("❌ No active prompts found")
        return None
    
    # Organize by type
    prompts_by_type = {}
    for prompt in result.data:
        prompt_type = prompt.get('prompt_type')
        stage_type = prompt.get('stage_type')
        name = prompt.get('name', 'Unnamed')
        
        key = stage_type or prompt_type
        if key:
            if key not in prompts_by_type:
                prompts_by_type[key] = []
            prompts_by_type[key].append({
                'name': name,
                'prompt_text': prompt.get('prompt_text', ''),
                'extraction_fields': prompt.get('extraction_fields'),
                'prompt_type': prompt_type,
                'stage_type': stage_type
            })
    
    print(f"📊 Found prompts for: {list(prompts_by_type.keys())}")
    
    # Build complete extraction configuration
    extraction_config = {
        "system": "custom_consensus",
        "temperature": 0.1,
        "orchestrator_model": "claude-4-opus",
        "max_budget": 2.0,
        "stages": {},
        "stage_models": {}
    }
    
    # Map database types to stage names
    type_to_stage = {
        'structure': 'structure',
        'product': 'products', 
        'detail': 'details',
        'visual': 'comparison'
    }
    
    for db_type, stage_name in type_to_stage.items():
        if db_type in prompts_by_type:
            # Get the latest/preferred prompt (prefer v1 versions)
            prompts = prompts_by_type[db_type]
            selected_prompt = None
            
            # Prefer prompts with "v1" in the name
            for p in prompts:
                if 'v1' in p['name'].lower():
                    selected_prompt = p
                    break
            
            if not selected_prompt and prompts:
                selected_prompt = prompts[0]
            
            if selected_prompt:
                print(f"✅ {stage_name}: {selected_prompt['name']}")
                
                stage_config = {
                    "prompt_text": selected_prompt['prompt_text']
                }
                
                # Add field definitions if available
                if selected_prompt['extraction_fields']:
                    try:
                        fields = json.loads(selected_prompt['extraction_fields'])
                        stage_config["fields"] = fields
                        print(f"   📝 {len(fields)} field definitions loaded")
                    except:
                        print(f"   ⚠️ Could not parse field definitions")
                
                extraction_config["stages"][stage_name] = stage_config
                
                # Set default models
                if stage_name == 'structure':
                    extraction_config["stage_models"][stage_name] = ["gpt-4o"]
                elif stage_name == 'products':
                    extraction_config["stage_models"][stage_name] = ["gpt-4o", "claude-3-sonnet"]
                elif stage_name == 'details':
                    extraction_config["stage_models"][stage_name] = ["gpt-4o", "claude-3-sonnet"]
    
    print(f"\n🎯 Complete configuration with {len(extraction_config['stages'])} stages:")
    for stage, config in extraction_config['stages'].items():
        field_count = len(config.get('fields', []))
        print(f"   {stage}: {field_count} fields, prompt length: {len(config['prompt_text'])}")
    
    return extraction_config

if __name__ == "__main__":
    config = load_complete_user_config()
    if config:
        print(f"\n📄 Complete configuration:")
        print(json.dumps(config, indent=2))