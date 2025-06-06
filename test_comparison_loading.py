#!/usr/bin/env python3
"""Test if comparison prompt is being loaded properly"""

import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_comparison_loading():
    """Test the current-config endpoint to see what's loaded"""
    
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        # Get current configuration
        response = await client.get(f"{base_url}/api/extraction/current-config")
        
        if response.status_code == 200:
            config = response.json()
            
            print("📊 Extraction Configuration:")
            print(f"Total stages: {len(config.get('stages', {}))}")
            print(f"Stages loaded: {list(config.get('stages', {}).keys())}")
            
            # Check if comparison stage exists
            if 'comparison' in config.get('stages', {}):
                comparison_config = config['stages']['comparison']
                print("\n✅ Comparison stage found!")
                print(f"   Prompt length: {len(comparison_config.get('prompt_text', ''))}")
                print(f"   Prompt preview: {comparison_config.get('prompt_text', '')[:100]}...")
                print(f"   Has fields: {'fields' in comparison_config}")
            else:
                print("\n❌ Comparison stage NOT found in configuration!")
                print("   Available stages:", list(config.get('stages', {}).keys()))
            
            # Check stage models
            stage_models = config.get('stage_models', {})
            print(f"\n📊 Stage models configured:")
            for stage, models in stage_models.items():
                print(f"   {stage}: {models}")
                
        else:
            print(f"❌ Failed to get config: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test_comparison_loading())