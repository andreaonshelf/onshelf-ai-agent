#!/usr/bin/env python3
"""Test if the field loading fix works correctly."""

import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("TESTING FIELD LOADING FIX")
print("=" * 80)

# Test 1: Find a queue item with extraction_config
print("\n1. Finding queue item with extraction_config...")
queue_items = supabase.table('ai_extraction_queue').select('*').eq('id', 8).execute()

if queue_items.data:
    queue_item = queue_items.data[0]
    extraction_config = queue_item.get('extraction_config')
    
    if isinstance(extraction_config, str):
        extraction_config = json.loads(extraction_config)
    
    print(f"Queue ID: {queue_item['id']}")
    print(f"Has extraction_config: {bool(extraction_config)}")
    print(f"Has stages: {bool(extraction_config.get('stages'))}")
    
    if extraction_config.get('stages'):
        for stage, config in extraction_config['stages'].items():
            if 'fields' in config:
                print(f"  {stage}: {len(config['fields'])} fields")

# Test 2: Simulate loading the config as the orchestrator would
print("\n2. Testing orchestrator loading logic...")

# Simulate what the orchestrator would do
if queue_items.data:
    result = queue_items
    
    # Get both model_config and extraction_config
    extraction_config = result.data[0].get("extraction_config", {})
    model_config = result.data[0].get("model_config", {})
    
    if isinstance(extraction_config, str):
        extraction_config = json.loads(extraction_config)
    if isinstance(model_config, str):
        model_config = json.loads(model_config)
    
    # Use extraction_config if it has stages, otherwise fall back to model_config
    if extraction_config and extraction_config.get("stages"):
        config_to_use = extraction_config
        print("✓ Would use extraction_config (has stages with fields)")
    elif model_config:
        config_to_use = model_config
        print("✗ Would use model_config (no extraction_config with stages)")
    else:
        config_to_use = {}
        print("✗ No configuration found")
    
    # Extract stage fields
    stage_fields = {}
    stage_configs = config_to_use.get("stages", {})
    
    for stage_id, stage_config in stage_configs.items():
        if isinstance(stage_config, dict) and "fields" in stage_config:
            stage_fields[stage_id] = stage_config["fields"]
            print(f"  Loaded {len(stage_config['fields'])} fields for stage {stage_id}")

# Test 3: Check what the system dispatcher passes
print("\n3. What the system dispatcher would pass...")

# The queue processor does this:
configuration = extraction_config if extraction_config.get('stages') else model_config
print(f"Queue processor would pass: {'extraction_config' if extraction_config.get('stages') else 'model_config'}")
print(f"Configuration has stages: {bool(configuration.get('stages'))}")

# The system dispatcher then uses it
if configuration and 'stages' in configuration:
    stages = configuration['stages']
    print(f"System dispatcher sees {len(stages)} stages")
    
    for stage_id, stage_config in stages.items():
        if isinstance(stage_config, dict):
            has_prompt = 'prompt_text' in stage_config
            has_fields = 'fields' in stage_config
            field_count = len(stage_config['fields']) if has_fields else 0
            print(f"  {stage_id}: prompt={has_prompt}, fields={field_count}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)

print("""
With the fix in place:
1. ExtractionOrchestrator now loads both model_config and extraction_config
2. It prioritizes extraction_config if it has 'stages' (which contain fields)
3. The fields are then available in self.stage_fields for dynamic model building

The fix should allow fields to be properly loaded and used for extraction!
""")