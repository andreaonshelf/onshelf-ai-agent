#!/usr/bin/env python3
"""
Test extraction directly without API
"""

import asyncio
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from src.api.queue_processing import run_extraction

async def test():
    """Test extraction directly"""
    
    print("Testing direct extraction...")
    
    try:
        await run_extraction(
            item_id=7,
            upload_id="upload-1748283096845-z057h5",
            system='custom_consensus',
            max_budget=2.0,
            configuration={}
        )
        print("✅ Extraction completed!")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())