#!/usr/bin/env python3
"""
Run the AI Extraction Queue Processor
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import SystemConfig
from src.queue.processor import AIExtractionQueueProcessor
from src.utils import logger

async def main():
    """Main function to run the queue processor"""
    try:
        # Initialize configuration
        config = SystemConfig()
        
        # Create and start the processor
        processor = AIExtractionQueueProcessor(config)
        
        logger.info("🚀 Starting AI Extraction Queue Processor...")
        
        # Start processing with 10-second polling interval for testing
        await processor.start_processing(polling_interval=10)
        
    except KeyboardInterrupt:
        logger.info("Queue processor stopped by user")
    except Exception as e:
        logger.error(f"Queue processor failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 