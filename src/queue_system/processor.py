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
        ready_media_id = queue_item.get('ready_media_id')
        enhanced_image_path = queue_item.get('enhanced_image_path')
        
        try:
            # Mark as processing
            await self._update_queue_status(queue_id, "processing")
            
            logger.info(
                f"🔥 Processing queue item {queue_id} with ready_media_id {ready_media_id}",
                component="queue_processor",
                queue_id=queue_id,
                ready_media_id=ready_media_id
            )
            
            # Process with master orchestrator (it handles image loading)
            start_time = time.time()
            
            # Use the master orchestrator for real processing
            from ..orchestrator.master_orchestrator import MasterOrchestrator
            orchestrator = MasterOrchestrator(self.config)
            
            # Process with master orchestrator using upload_id
            upload_id = queue_item['upload_id']
            
            # Extract configuration from queue item
            extraction_config = queue_item.get('extraction_config', {})
            system = extraction_config.get('system', 'custom_consensus')
            
            # Pass configuration to orchestrator
            result = await orchestrator.achieve_target_accuracy(
                upload_id, 
                queue_item_id=queue_id,
                system=system,
                configuration=extraction_config
            )
            
            processing_duration = time.time() - start_time
            
            # Update queue with results
            await self._update_queue_with_results(queue_id, result, processing_duration)
            
            logger.info(
                f"✅ Successfully processed queue item {queue_id}",
                component="queue_processor",
                queue_id=queue_id,
                ready_media_id=ready_media_id,
                final_accuracy=result.final_accuracy if hasattr(result, 'final_accuracy') else 0.0,
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
            # Extract results from the master orchestrator result
            extraction_result = {
                "products": [],
                "shelf_structure": {},
                "accuracy_score": 0.0,
                "models_used": [],
                "iterations": 1,
                "processing_time": processing_duration
            }
            
            planogram_result = {
                "planogram_id": f"planogram_{queue_id}",
                "shelves": [],
                "canvas_data": None,
                "svg_data": None
            }
            
            final_accuracy = 0.0
            iterations_completed = 1
            api_cost = 0.0
            
            # Extract data based on result type
            if hasattr(result, 'final_accuracy'):
                final_accuracy = result.final_accuracy
            elif hasattr(result, 'accuracy'):
                final_accuracy = result.accuracy
                
            if hasattr(result, 'iterations_completed'):
                iterations_completed = result.iterations_completed
            elif hasattr(result, 'iterations'):
                iterations_completed = result.iterations
                
            if hasattr(result, 'total_api_cost'):
                api_cost = result.total_api_cost
            elif hasattr(result, 'cost'):
                api_cost = result.cost
                
            # Extract extraction data
            if hasattr(result, 'best_extraction'):
                best_extraction = result.best_extraction
                if hasattr(best_extraction, 'products'):
                    # Use model_dump() for Pydantic v2 compatibility
                    extraction_result["products"] = [
                        p.model_dump() if hasattr(p, 'model_dump') else (p.dict() if hasattr(p, 'dict') else p) 
                        for p in best_extraction.products
                    ]
                if hasattr(best_extraction, 'shelf_structure'):
                    # Use model_dump() for Pydantic v2 compatibility
                    if hasattr(best_extraction.shelf_structure, 'model_dump'):
                        extraction_result["shelf_structure"] = best_extraction.shelf_structure.model_dump()
                    elif hasattr(best_extraction.shelf_structure, 'dict'):
                        extraction_result["shelf_structure"] = best_extraction.shelf_structure.dict()
                    else:
                        extraction_result["shelf_structure"] = best_extraction.shelf_structure
                extraction_result["accuracy_score"] = final_accuracy
                
            # Extract planogram data
            if hasattr(result, 'best_planogram'):
                best_planogram = result.best_planogram
                if hasattr(best_planogram, 'shelves'):
                    # Use model_dump() for Pydantic v2 compatibility
                    planogram_result["shelves"] = [
                        s.model_dump() if hasattr(s, 'model_dump') else (s.dict() if hasattr(s, 'dict') else s)
                        for s in best_planogram.shelves
                    ]
                if hasattr(best_planogram, 'canvas_data'):
                    planogram_result["canvas_data"] = best_planogram.canvas_data
                if hasattr(best_planogram, 'svg_data'):
                    planogram_result["svg_data"] = best_planogram.svg_data
            
            update_data = {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "extraction_result": extraction_result,
                "planogram_result": planogram_result,
                "final_accuracy": final_accuracy,
                "iterations_completed": iterations_completed,
                "processing_duration_seconds": int(processing_duration),
                "api_cost": api_cost,
                "human_review_required": final_accuracy < 0.85
            }
            
            self.supabase.table("ai_extraction_queue") \
                .update(update_data) \
                .eq("id", queue_id) \
                .execute()
                
            logger.info(
                f"Queue item {queue_id} updated with results",
                component="queue_processor",
                queue_id=queue_id,
                accuracy=final_accuracy
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