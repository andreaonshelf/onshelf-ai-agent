"""
Monitoring hooks for the orchestrator to provide real-time updates
"""

from typing import Dict, Any, Optional, Callable
import asyncio
from datetime import datetime

from ..extraction.state_tracker import ExtractionStage
from ..utils import logger
from ..websocket.manager import websocket_manager


class MonitoringHooks:
    """Provides hooks for real-time monitoring of extraction progress"""
    
    def __init__(self):
        self.monitors: Dict[int, Dict[str, Any]] = {}
        self.update_callbacks: Dict[int, Callable] = {}
    
    def register_monitor(self, queue_item_id: int, initial_data: Dict[str, Any]):
        """Register a new monitoring session"""
        self.monitors[queue_item_id] = {
            **initial_data,
            "started_at": datetime.utcnow(),
            "last_update": datetime.utcnow()
        }
        logger.info(f"Registered monitor for queue item {queue_item_id}")
    
    def update_monitor(self, queue_item_id: int, updates: Dict[str, Any]):
        """Update monitoring data"""
        if queue_item_id in self.monitors:
            self.monitors[queue_item_id].update(updates)
            self.monitors[queue_item_id]["last_update"] = datetime.utcnow()
            
            # Call any registered callbacks
            if queue_item_id in self.update_callbacks:
                try:
                    self.update_callbacks[queue_item_id](self.monitors[queue_item_id])
                except Exception as e:
                    logger.error(f"Error in monitor callback: {e}")
            
            # Broadcast via WebSocket
            asyncio.create_task(
                websocket_manager.broadcast_to_agent(
                    str(queue_item_id),
                    {
                        "type": "monitoring_update",
                        **self.monitors[queue_item_id]
                    }
                )
            )
    
    def get_monitor_data(self, queue_item_id: int) -> Optional[Dict[str, Any]]:
        """Get current monitoring data"""
        return self.monitors.get(queue_item_id)
    
    def clear_monitor(self, queue_item_id: int):
        """Clear monitoring data for completed item"""
        if queue_item_id in self.monitors:
            del self.monitors[queue_item_id]
        if queue_item_id in self.update_callbacks:
            del self.update_callbacks[queue_item_id]
    
    def register_callback(self, queue_item_id: int, callback: Callable):
        """Register a callback for monitor updates"""
        self.update_callbacks[queue_item_id] = callback
    
    async def update_extraction_stage(self, queue_item_id: int, stage: str, details: Dict[str, Any] = None):
        """Update extraction stage with details"""
        updates = {
            "current_stage": stage,
            "stage_details": details or {}
        }
        
        # Map stages to completion flags
        if stage == "Structure Analysis":
            updates["structure_started"] = True
        elif stage == "Structure Complete":
            updates["structure_complete"] = True
        elif stage == "Product Extraction":
            updates["products_started"] = True
        elif stage == "Products Complete":
            updates["products_complete"] = True
        elif stage == "Detail Enhancement":
            updates["details_started"] = True
        elif stage == "Validation":
            updates["validation_started"] = True
        
        self.update_monitor(queue_item_id, updates)
    
    async def update_iteration(self, queue_item_id: int, iteration: int, locked_items: list = None):
        """Update iteration information"""
        updates = {
            "current_iteration": iteration,
            "locked_items": locked_items or []
        }
        self.update_monitor(queue_item_id, updates)
    
    async def update_models_status(self, queue_item_id: int, model_statuses: list):
        """Update model processing status"""
        updates = {
            "models_status": model_statuses
        }
        self.update_monitor(queue_item_id, updates)
    
    async def update_processing_detail(self, queue_item_id: int, detail: str):
        """Update current processing detail"""
        updates = {
            "current_processing": detail
        }
        self.update_monitor(queue_item_id, updates)


# Global monitoring instance
monitoring_hooks = MonitoringHooks()