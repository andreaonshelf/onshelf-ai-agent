#!/usr/bin/env python3
"""Process queue item 9 directly with the fixed configuration."""

import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemConfig
from src.orchestrator.system_dispatcher import SystemDispatcher
from src.utils import logger

async def process_item():
    """Process queue item 9"""
    
    config = SystemConfig()
    dispatcher = SystemDispatcher(config)
    
    queue_item_id = 9
    
    logger.info(f"Processing queue item {queue_item_id} manually", component="manual_processor")
    
    try:
        # Process the item
        result = await dispatcher.process_queue_item(queue_item_id)
        
        logger.info(
            f"Processing completed for queue item {queue_item_id}",
            component="manual_processor",
            success=result.get('success', False)
        )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to process queue item {queue_item_id}: {e}",
            component="manual_processor",
            error=str(e),
            error_type=type(e).__name__
        )
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(process_item())
    print(f"\nResult: {result}")