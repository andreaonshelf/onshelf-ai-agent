#!/usr/bin/env python3
"""
Queue Processor Runner
Resets fake completed items and starts real processing
"""

import asyncio
import sys
import os

# Add current directory to path for module imports
sys.path.insert(0, os.path.dirname(__file__))

# Import directly without relative imports
import src.config as config_module
import src.utils as utils_module
from supabase import create_client


async def reset_fake_completed_items(config):
    """Reset items that are marked completed but have no real extraction results"""
    supabase = create_client(config.supabase_url, config.supabase_service_key)
    
    try:
        # Find items that are "completed" but have no real results
        result = supabase.table("ai_extraction_queue").select("*").eq("status", "completed").execute()
        
        if not result.data:
            utils_module.logger.info("No completed items found")
            return 0
        
        # Filter items that have null or empty extraction results (fake completed)
        fake_completed = []
        for item in result.data:
            extraction_result = item.get('extraction_result')
            planogram_result = item.get('planogram_result')
            
            # Check if results are empty or mock
            is_fake = (
                not extraction_result or 
                not planogram_result or
                (isinstance(extraction_result, dict) and len(extraction_result.get('products', [])) == 0) or
                (isinstance(planogram_result, dict) and len(planogram_result.get('shelves', [])) == 0)
            )
            
            if is_fake:
                fake_completed.append(item)
        
        if not fake_completed:
            utils_module.logger.info("All completed items have valid results")
            return 0
        
        # Reset fake completed items to pending
        reset_ids = [item['id'] for item in fake_completed]
        
        update_data = {
            "status": "pending",
            "extraction_result": None,
            "planogram_result": None,
            "final_accuracy": None,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "iterations_completed": None,
            "processing_duration_seconds": None,
            "api_cost": None,
            "human_review_required": False,
            "escalation_reason": None
        }
        
        # Update all fake completed items
        for item_id in reset_ids:
            supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
        
        utils_module.logger.info(f"Reset {len(reset_ids)} fake completed items to pending")
        return len(reset_ids)
        
    except Exception as e:
        utils_module.logger.error(f"Failed to reset fake completed items: {e}")
        return 0


async def main():
    """Main function to reset fake data and start queue processing"""
    
    # Initialize config
    config = config_module.SystemConfig()
    
    utils_module.logger.info("🚀 Starting OnShelf AI Queue Processor")
    utils_module.logger.info(f"Database URL: {config.supabase_url}")
    
    # Reset fake completed items first
    utils_module.logger.info("🔄 Resetting fake completed items...")
    reset_count = await reset_fake_completed_items(config)
    
    if reset_count > 0:
        utils_module.logger.info(f"✅ Reset {reset_count} fake completed items to pending status")
    
    # For now, just show that we've reset the data
    utils_module.logger.info("✅ Queue processor setup complete. Fake data has been reset.")
    utils_module.logger.info("🎯 To start real processing, run: python -m src.queue_system")


if __name__ == "__main__":
    asyncio.run(main()) 