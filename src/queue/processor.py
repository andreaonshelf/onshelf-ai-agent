"""
AI Extraction Queue Processor
Monitors ai_extraction_queue table and automatically processes ready items
"""

import asyncio
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..config import SystemConfig
from ..agent.agent import OnShelfAIAgent
from ..utils import logger
from supabase import create_client, Client


class AIExtractionQueueProcessor:
    """Processes items from ai_extraction_queue table automatically"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.supabase = create_client(config.supabase_url, config.supabase_service_key)
        self.agent = OnShelfAIAgent(config)
        self.is_running = False
        self.processing_count = 0
        
        logger.info(
            "AI Extraction Queue Processor initialized",
            component="queue_processor",
            polling_interval=30
        )
    
    async def start_processing(self, polling_interval: int = 30):
        """Start the queue processing loop"""
        self.is_running = True
        
        logger.info(
            "🚀 Starting AI extraction queue processing",
            component="queue_processor",
            polling_interval=polling_interval
        )
        
        while self.is_running:
            try:
                await self._process_pending_items()
                await asyncio.sleep(polling_interval)
                
            except Exception as e:
                logger.error(
                    f"Error in queue processing loop: {e}",
                    component="queue_processor",
                    error=str(e)
                )
                await asyncio.sleep(5)  # Brief pause before retrying
    
    def stop_processing(self):
        """Stop the queue processing loop"""
        self.is_running = False
        logger.info(
            "Queue processing stopped",
            component="queue_processor"
        )
    
    async def _process_pending_items(self):
        """Find and process pending items from the queue"""
        
        # Query for pending extraction items
        try:
            result = self.supabase.table("ai_extraction_queue") \
                .select("*") \
                .eq("status", "pending") \
                .order("created_at", desc=False) \
                .limit(5) \
                .execute()
            
            pending_items = result.data or []
            
            if pending_items:
                logger.info(
                    f"Found {len(pending_items)} pending extraction items",
                    component="queue_processor",
                    pending_count=len(pending_items)
                )
                
                # Process each item
                for item in pending_items:
                    await self._process_queue_item(item)
            
        except Exception as e:
            logger.error(
                f"Failed to query extraction queue: {e}",
                component="queue_processor",
                error=str(e)
            )
    
    async def _process_queue_item(self, queue_item: Dict):
        """Process a single queue item"""
        queue_id = queue_item['id']
        ready_media_id = queue_item['ready_media_id']
        
        try:
            # Mark as processing
            await self._update_queue_status(queue_id, "processing")
            
            logger.info(
                f"🔥 Processing queue item {queue_id} with ready_media_id {ready_media_id}",
                component="queue_processor",
                queue_id=queue_id,
                ready_media_id=ready_media_id
            )
            
            # Process with enhanced AI agent
            start_time = time.time()
            result = await self.agent.achieve_target_accuracy_enhanced(ready_media_id)
            processing_duration = time.time() - start_time
            
            # Update queue with results
            await self._update_queue_with_results(queue_id, result, processing_duration)
            
            logger.info(
                f"✅ Successfully processed queue item {queue_id}",
                component="queue_processor",
                queue_id=queue_id,
                ready_media_id=ready_media_id,
                final_accuracy=result.accuracy,
                duration=processing_duration
            )
            
            self.processing_count += 1
            
        except Exception as e:
            # Mark as failed
            await self._update_queue_status(queue_id, "failed", str(e))
            
            logger.error(
                f"❌ Failed to process queue item {queue_id}: {e}",
                component="queue_processor",
                queue_id=queue_id,
                ready_media_id=ready_media_id,
                error=str(e)
            )
    
    async def _update_queue_status(self, queue_id: str, status: str, error_message: str = None):
        """Update queue item status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if status == "processing":
                update_data["started_at"] = datetime.utcnow().isoformat()
            elif status == "completed":
                update_data["completed_at"] = datetime.utcnow().isoformat()
            elif status == "failed":
                update_data["error_message"] = error_message
                update_data["failed_at"] = datetime.utcnow().isoformat()
            
            self.supabase.table("ai_extraction_queue") \
                .update(update_data) \
                .eq("id", queue_id) \
                .execute()
                
        except Exception as e:
            logger.error(
                f"Failed to update queue status: {e}",
                component="queue_processor",
                queue_id=queue_id,
                error=str(e)
            )
    
    async def _update_queue_with_results(self, queue_id: str, result, processing_duration: float):
        """Update queue item with extraction results"""
        try:
            update_data = {
                "status": "completed",
                "agent_id": result.agent_id,
                "final_accuracy": result.accuracy,
                "iterations_completed": result.iterations_completed,
                "processing_duration_seconds": int(processing_duration),
                "api_cost": result.total_api_cost,
                "human_review_required": result.human_review_required,
                "completed_at": datetime.utcnow().isoformat(),
                "extraction_result": result.extraction,
                "planogram_result": result.planogram,
                "escalation_reason": result.escalation_reason
            }
            
            self.supabase.table("ai_extraction_queue") \
                .update(update_data) \
                .eq("id", queue_id) \
                .execute()
                
            logger.info(
                f"Queue item {queue_id} updated with results",
                component="queue_processor",
                queue_id=queue_id,
                accuracy=result.accuracy
            )
                
        except Exception as e:
            logger.error(
                f"Failed to update queue with results: {e}",
                component="queue_processor",
                queue_id=queue_id,
                error=str(e)
            )
    
    def get_stats(self) -> Dict:
        """Get processor statistics"""
        return {
            "is_running": self.is_running,
            "items_processed": self.processing_count,
            "uptime_seconds": time.time() if self.is_running else 0
        } 