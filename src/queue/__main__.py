"""
Queue Processor Main Entry Point
Run with: python -m src.queue.processor
"""

import asyncio
import signal
import sys
from src.config import SystemConfig
from src.queue.processor import AIExtractionQueueProcessor


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Received shutdown signal, stopping queue processor...")
    sys.exit(0)


async def main():
    """Main entry point for queue processor"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize configuration
    config = SystemConfig()
    
    # Validate configuration
    if not config.validate():
        print("❌ Configuration validation failed. Please check your environment variables.")
        sys.exit(1)
    
    # Initialize and start processor
    processor = AIExtractionQueueProcessor(config)
    
    print("🚀 Starting AI Extraction Queue Processor...")
    print("📊 Monitoring ai_extraction_queue table for pending items...")
    print("⏱️  Polling every 30 seconds...")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        await processor.start_processing(polling_interval=30)
    except KeyboardInterrupt:
        print("\n🛑 Stopping queue processor...")
        processor.stop_processing()
    except Exception as e:
        print(f"❌ Queue processor error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 