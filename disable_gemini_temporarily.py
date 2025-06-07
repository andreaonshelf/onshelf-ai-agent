#!/usr/bin/env python3
"""Temporarily disable Gemini in stage models due to quota issues"""

from src.config import SystemConfig
from supabase import create_client
import json

config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key)

# Get all pending queue items
result = supabase.table("ai_extraction_queue").select("*").eq("status", "pending").execute()

print(f"Found {len(result.data)} pending items")

for item in result.data:
    queue_id = item['id']
    extraction_config = item.get('extraction_config', {})
    
    # Remove gemini from stage_models
    if 'stage_models' in extraction_config:
        for stage, models in extraction_config['stage_models'].items():
            if isinstance(models, list):
                # Remove any gemini models
                filtered_models = [m for m in models if 'gemini' not in m.lower()]
                extraction_config['stage_models'][stage] = filtered_models
                
                # If no models left, add claude and gpt
                if not filtered_models:
                    if stage == 'structure':
                        extraction_config['stage_models'][stage] = ['gpt-4.1', 'claude-3-7-sonnet']
                    elif stage == 'products':
                        extraction_config['stage_models'][stage] = ['gpt-4.1', 'claude-3-7-sonnet']
                    elif stage == 'details':
                        extraction_config['stage_models'][stage] = ['gpt-4.1', 'claude-3-opus']
    
    # Update the item
    update_result = supabase.table("ai_extraction_queue").update({
        "extraction_config": extraction_config
    }).eq("id", queue_id).execute()
    
    if update_result.data:
        print(f"✅ Updated item {queue_id} - removed Gemini from stage models")

print("\nGemini has been temporarily disabled in all pending queue items.")