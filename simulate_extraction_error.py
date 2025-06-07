#!/usr/bin/env python3
"""Simulate the extraction to find where NoneType error occurs"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

async def test_extraction():
    """Test the extraction pipeline to find the error"""
    
    from src.config import SystemConfig
    from src.orchestrator.system_dispatcher import SystemDispatcher
    from supabase import create_client
    
    config = SystemConfig()
    supabase = create_client(config.supabase_url, config.supabase_service_key)
    
    # Test with the failed upload
    upload_id = "upload-1748342011996-y1y6yk"
    queue_item_id = 9
    
    # Create dispatcher
    dispatcher = SystemDispatcher(config, supabase_client=supabase, queue_item_id=queue_item_id)
    
    # Configuration from the failed attempt
    configuration = {
        "system": "langgraph",
        "max_budget": 3,
        "temperature": 0.1,
        "stage_models": {
            "details": ["gpt-4.1", "gemini-2.5-pro"],
            "products": ["gpt-4.1", "claude-3-7-sonnet", "gemini-2.5-pro"],
            "structure": ["gpt-4.1", "claude-3-7-sonnet"],
            "comparison": ["gpt-4.1", "claude-4-opus", "gemini-2.5-pro"]
        },
        "orchestrators": {
            "master": {"model": "claude-4-opus", "prompt": ""},
            "planogram": {"model": "gpt-4o-mini", "prompt": ""},
            "extraction": {"model": "claude-4-sonnet", "prompt": ""}
        }
    }
    
    try:
        print(f"Testing extraction for upload {upload_id}")
        
        # Try to achieve target accuracy
        result = await dispatcher.achieve_target_accuracy(
            upload_id=upload_id,
            target_accuracy=0.95,
            max_iterations=1,  # Just one iteration to see the error
            queue_item_id=queue_item_id,
            system="langgraph",
            configuration=configuration
        )
        
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {type(e).__name__}: {e}")
        
        # Print full traceback
        import traceback
        traceback.print_exc()
        
        # Try to get more details
        print("\n\nDebugging info:")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args if hasattr(e, 'args') else 'No args'}")

if __name__ == "__main__":
    asyncio.run(test_extraction())