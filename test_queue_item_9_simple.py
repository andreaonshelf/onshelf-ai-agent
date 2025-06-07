#!/usr/bin/env python3
"""Test queue item 9 processing directly using queue processor."""

import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemConfig
from src.queue_system.processor import AIExtractionQueueProcessor
from src.utils import logger

async def test_item():
    """Test processing queue item 9"""
    
    config = SystemConfig()
    processor = AIExtractionQueueProcessor(config)
    
    # Get queue item 9
    result = processor.supabase.table("ai_extraction_queue").select("*").eq("id", 9).single().execute()
    
    if not result.data:
        print("❌ Queue item 9 not found!")
        return
    
    queue_item = result.data
    print(f"Processing queue item {queue_item['id']}")
    print(f"Status: {queue_item['status']}")
    print(f"Upload ID: {queue_item['upload_id']}")
    
    # Process the item directly
    try:
        await processor._process_queue_item(queue_item)
        print("✅ Processing completed!")
        
        # Check final status
        result = processor.supabase.table("ai_extraction_queue").select("status, error_message").eq("id", 9).single().execute()
        if result.data:
            print(f"Final status: {result.data['status']}")
            if result.data.get('error_message'):
                print(f"Error: {result.data['error_message']}")
                
    except Exception as e:
        logger.error(f"Failed to process queue item 9: {e}", component="test")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_item())