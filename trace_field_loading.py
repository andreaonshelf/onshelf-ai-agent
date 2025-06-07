#!/usr/bin/env python3
"""Trace where fields are getting lost in the extraction pipeline."""

import os
import json
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

print("=" * 80)
print("TRACING FIELD LOADING IN EXTRACTION PIPELINE")
print("=" * 80)

# 1. Check a recent queue item with extraction_config
print("\n1. CHECKING QUEUE ITEM WITH EXTRACTION CONFIG:")
print("-" * 40)

queue_items = supabase.table('ai_extraction_queue').select('*').eq('status', 'ready').limit(1).execute()

if queue_items.data:
    queue_item = queue_items.data[0]
    queue_id = queue_item['id']
    
    print(f"Queue ID: {queue_id}")
    print(f"Status: {queue_item.get('status')}")
    
    # Check extraction_config
    extraction_config = queue_item.get('extraction_config')
    if extraction_config:
        if isinstance(extraction_config, str):
            extraction_config = json.loads(extraction_config)
        
        print(f"\nExtraction Config Keys: {list(extraction_config.keys())}")
        
        # Check for stages with fields
        if 'stages' in extraction_config:
            print(f"\nStages found: {list(extraction_config['stages'].keys())}")
            
            for stage_id, stage_config in extraction_config['stages'].items():
                if isinstance(stage_config, dict):
                    print(f"\n  Stage '{stage_id}':")
                    print(f"    Config keys: {list(stage_config.keys())}")
                    
                    if 'fields' in stage_config:
                        fields = stage_config['fields']
                        if isinstance(fields, list) and fields:
                            print(f"    Fields: {len(fields)} field definitions")
                            # Show first field as example
                            if isinstance(fields[0], dict):
                                print(f"    First field keys: {list(fields[0].keys())}")
                        else:
                            print(f"    Fields: {type(fields)} - {fields}")
                    else:
                        print(f"    Fields: NOT FOUND")
                        
                    if 'prompt_text' in stage_config:
                        print(f"    Prompt: {len(stage_config['prompt_text'])} chars")
    else:
        print("No extraction_config found")
        
    # Check model_config 
    model_config = queue_item.get('model_config')
    if model_config:
        if isinstance(model_config, str):
            model_config = json.loads(model_config)
        print(f"\nModel Config Keys: {list(model_config.keys())}")
    else:
        print("\nNo model_config found")

# 2. Show how the orchestrator loads config
print("\n\n2. ORCHESTRATOR LOADING LOGIC:")
print("-" * 40)

print("""
The extraction orchestrator (_load_model_config) looks for:
1. model_config from ai_extraction_queue table
2. Extracts temperature, orchestrator_model, stage_models
3. Looks for 'stages' in model_config for prompts and fields

But the queue processor passes:
1. extraction_config (which has the fields) if it has 'stages'
2. Falls back to model_config if extraction_config has no 'stages'

The issue: ExtractionOrchestrator always loads from database directly,
ignoring the configuration passed by the system dispatcher!
""")

# 3. Show the fix needed
print("\n3. FIX NEEDED:")
print("-" * 40)

print("""
The ExtractionOrchestrator should:
1. Accept configuration parameter in __init__
2. Use passed configuration instead of loading from database
3. Only load from database if no configuration is passed

OR

The orchestrator should load extraction_config instead of model_config
when loading from the database.
""")

# 4. Check prompt templates for fields
print("\n\n4. CHECKING PROMPT TEMPLATES FOR EXTRACTION FIELDS:")
print("-" * 40)

prompts = supabase.table('prompt_templates').select('*').eq('is_active', True).limit(5).execute()

if prompts.data:
    for prompt in prompts.data:
        print(f"\nPrompt: {prompt.get('name', 'Unnamed')}")
        print(f"  Type: {prompt.get('prompt_type')}")
        print(f"  Stage: {prompt.get('stage_type')}")
        
        # Check extraction_fields column
        extraction_fields = prompt.get('extraction_fields')
        if extraction_fields:
            print(f"  Extraction Fields: Found - {type(extraction_fields)}")
            if isinstance(extraction_fields, str):
                try:
                    extraction_fields = json.loads(extraction_fields)
                except:
                    pass
            
            if isinstance(extraction_fields, list):
                print(f"    Field count: {len(extraction_fields)}")
            elif isinstance(extraction_fields, dict):
                print(f"    Field keys: {list(extraction_fields.keys())}")
        else:
            print(f"  Extraction Fields: None")