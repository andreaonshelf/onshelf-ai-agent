"""
Model Usage Tracker
Tracks model usage for analytics and cost optimization
"""

import time
from typing import Optional, Dict, Any
from datetime import datetime
import os

from supabase import create_client
from ..utils import logger


class ModelUsageTracker:
    """Tracks model usage and performance metrics"""
    
    def __init__(self):
        self.supabase = None
        try:
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
    
    async def log_model_usage(
        self,
        queue_item_id: int,
        extraction_run_id: str,
        stage: str,
        model_id: str,
        model_provider: str,
        iteration_number: int,
        temperature: float,
        prompt_tokens: int,
        completion_tokens: int,
        response_time_ms: int,
        api_cost: float,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> Optional[int]:
        """Log a model usage event"""
        
        if not self.supabase:
            logger.warning("Supabase client not initialized, skipping model usage logging")
            return None
            
        try:
            result = self.supabase.rpc(
                'log_model_usage',
                {
                    'p_queue_item_id': queue_item_id,
                    'p_extraction_run_id': extraction_run_id,
                    'p_stage': stage,
                    'p_model_id': model_id,
                    'p_model_provider': model_provider,
                    'p_iteration_number': iteration_number,
                    'p_temperature': temperature,
                    'p_prompt_tokens': prompt_tokens,
                    'p_completion_tokens': completion_tokens,
                    'p_response_time_ms': response_time_ms,
                    'p_api_cost': api_cost,
                    'p_success': success,
                    'p_error_message': error_message
                }
            ).execute()
            
            logger.info(
                f"Logged model usage for {model_id} in stage {stage}",
                component="model_usage_tracker",
                queue_item_id=queue_item_id,
                model_id=model_id,
                stage=stage,
                cost=api_cost
            )
            
            return result.data
            
        except Exception as e:
            logger.error(f"Failed to log model usage: {e}", component="model_usage_tracker")
            return None
    
    async def log_configuration_usage(
        self,
        configuration_name: str,
        configuration_id: str,
        system: str,
        orchestrator_model: str,
        orchestrator_prompt: str,
        temperature: float,
        max_budget: float,
        stage_models: Dict[str, list]
    ) -> bool:
        """Log or update configuration usage"""
        
        if not self.supabase:
            return False
            
        try:
            # Check if configuration already exists
            existing = self.supabase.table("configuration_usage").select("id").eq(
                "configuration_name", configuration_name
            ).execute()
            
            if existing.data:
                # Update existing
                result = self.supabase.table("configuration_usage").update({
                    "times_used": self.supabase.raw("times_used + 1"),
                    "last_used_at": datetime.utcnow().isoformat()
                }).eq("configuration_name", configuration_name).execute()
            else:
                # Insert new
                result = self.supabase.table("configuration_usage").insert({
                    "configuration_name": configuration_name,
                    "configuration_id": configuration_id,
                    "system": system,
                    "orchestrator_model": orchestrator_model,
                    "orchestrator_prompt": orchestrator_prompt,
                    "temperature": temperature,
                    "max_budget": max_budget,
                    "stage_models": stage_models
                }).execute()
            
            logger.info(
                f"Logged configuration usage for {configuration_name}",
                component="model_usage_tracker"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to log configuration usage: {e}", component="model_usage_tracker")
            return False
    
    async def update_configuration_stats(
        self,
        configuration_name: str,
        accuracy: float,
        cost: float,
        duration_seconds: int,
        success: bool
    ) -> bool:
        """Update configuration performance statistics"""
        
        if not self.supabase:
            return False
            
        try:
            result = self.supabase.rpc(
                'update_configuration_stats',
                {
                    'p_configuration_name': configuration_name,
                    'p_accuracy': accuracy,
                    'p_cost': cost,
                    'p_duration_seconds': duration_seconds,
                    'p_success': success
                }
            ).execute()
            
            logger.info(
                f"Updated configuration stats for {configuration_name}",
                component="model_usage_tracker",
                accuracy=accuracy,
                cost=cost
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration stats: {e}", component="model_usage_tracker")
            return False
    
    def get_model_provider(self, model_id: str) -> str:
        """Determine provider from model ID"""
        if model_id.startswith('gpt') or model_id.startswith('o'):
            return 'openai'
        elif model_id.startswith('claude'):
            return 'anthropic'
        elif model_id.startswith('gemini'):
            return 'google'
        else:
            return 'unknown'


# Global instance
_tracker = None

def get_model_usage_tracker() -> ModelUsageTracker:
    """Get or create the global model usage tracker"""
    global _tracker
    if _tracker is None:
        _tracker = ModelUsageTracker()
    return _tracker