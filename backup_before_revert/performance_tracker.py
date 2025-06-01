"""
Performance Tracking for Extraction Results
Tracks accuracy, costs, and performance metrics for continuous improvement
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid

from ..config import SystemConfig
from ..utils import logger
from supabase import create_client

# Initialize Supabase client
config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key) if config.supabase_url and config.supabase_service_key else None


class PerformanceTracker:
    """Tracks extraction performance and updates prompt metrics"""
    
    def __init__(self):
        self.config = config
        self.supabase = supabase
    
    async def track_extraction_performance(
        self,
        upload_id: str,
        extraction_config: Dict[str, Any],
        extraction_results: Dict[str, Any],
        human_feedback: Optional[Dict[str, Any]] = None
    ):
        """Track performance metrics for an extraction run"""
        
        if not self.supabase:
            logger.warning("Supabase not configured, skipping performance tracking")
            return
        
        try:
            # Extract key metrics
            prompt_id = extraction_config.get("prompt_id")
            model_type = extraction_config.get("model", "gpt4o")
            prompt_type = extraction_config.get("prompt_type", "extraction")
            
            # Calculate accuracy based on human feedback if available
            accuracy_score = self._calculate_accuracy(extraction_results, human_feedback)
            had_corrections = bool(human_feedback and human_feedback.get("corrections"))
            
            # Extract cost and performance metrics
            total_cost = extraction_results.get("total_cost", 0.0)
            processing_time_ms = int(extraction_results.get("processing_time", 0) * 1000)
            total_tokens = extraction_results.get("total_tokens", 0)
            
            # Track prompt performance if prompt_id is available
            if prompt_id:
                await self._track_prompt_performance(
                    prompt_id=prompt_id,
                    accuracy_score=accuracy_score,
                    had_corrections=had_corrections,
                    processing_time_ms=processing_time_ms,
                    token_usage=total_tokens,
                    api_cost=total_cost
                )
            
            # Store extraction context for learning
            context_data = {
                "upload_id": upload_id,
                "extraction_config": extraction_config,
                "model_type": model_type,
                "prompt_type": prompt_type,
                "accuracy_score": accuracy_score,
                "had_corrections": had_corrections,
                "processing_time_ms": processing_time_ms,
                "token_usage": total_tokens,
                "api_cost": total_cost,
                "image_metadata": extraction_results.get("image_metadata", {}),
                "extraction_summary": {
                    "total_products": len(extraction_results.get("products", [])),
                    "confidence_scores": extraction_results.get("confidence_scores", {}),
                    "consensus_reached": extraction_results.get("consensus_reached", False)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in extraction_contexts table
            self.supabase.table("extraction_contexts").insert(context_data).execute()
            
            # Update configuration performance
            await self._update_configuration_performance(
                extraction_config, accuracy_score, total_cost, processing_time_ms
            )
            
            logger.info(
                f"Tracked extraction performance",
                component="performance_tracker",
                upload_id=upload_id,
                accuracy_score=accuracy_score,
                had_corrections=had_corrections,
                cost=total_cost
            )
            
        except Exception as e:
            logger.error(f"Failed to track extraction performance: {e}", component="performance_tracker")
    
    def _calculate_accuracy(
        self, 
        extraction_results: Dict[str, Any], 
        human_feedback: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate accuracy score based on extraction results and human feedback"""
        
        # If no human feedback, use confidence scores
        if not human_feedback:
            confidence_scores = extraction_results.get("confidence_scores", {})
            if confidence_scores:
                return sum(confidence_scores.values()) / len(confidence_scores)
            return 0.8  # Default confidence
        
        # Calculate based on human corrections
        corrections = human_feedback.get("corrections", [])
        total_items = len(extraction_results.get("products", []))
        
        if total_items == 0:
            return 1.0
        
        # Count different types of corrections
        missed_items = len([c for c in corrections if c["type"] == "missed"])
        wrong_items = len([c for c in corrections if c["type"] == "wrong"])
        partial_items = len([c for c in corrections if c["type"] == "partial"])
        
        # Calculate weighted accuracy
        accuracy = 1.0 - (
            (missed_items * 1.0 + wrong_items * 1.0 + partial_items * 0.5) / 
            (total_items + missed_items)
        )
        
        return max(0.0, min(1.0, accuracy))
    
    async def _track_prompt_performance(
        self,
        prompt_id: str,
        accuracy_score: float,
        had_corrections: bool,
        processing_time_ms: int,
        token_usage: int,
        api_cost: float
    ):
        """Update prompt performance metrics"""
        
        try:
            # Get current prompt data
            prompt_result = self.supabase.table("prompt_templates")\
                .select("*")\
                .eq("prompt_id", prompt_id)\
                .single()\
                .execute()
            
            if not prompt_result.data:
                return
            
            prompt_data = prompt_result.data
            
            # Calculate new performance score
            current_score = prompt_data["performance_score"]
            current_count = prompt_data["usage_count"]
            new_score = (current_score * current_count + accuracy_score) / (current_count + 1)
            
            # Calculate new correction rate
            current_correction_rate = prompt_data["correction_rate"]
            new_correction_rate = (
                (current_correction_rate * current_count + (1.0 if had_corrections else 0.0)) / 
                (current_count + 1)
            )
            
            # Update prompt performance
            update_data = {
                "performance_score": new_score,
                "correction_rate": new_correction_rate,
                "usage_count": current_count + 1,
                "avg_token_cost": (
                    (prompt_data.get("avg_token_cost", 0) * current_count + api_cost) / 
                    (current_count + 1)
                )
            }
            
            self.supabase.table("prompt_templates")\
                .update(update_data)\
                .eq("prompt_id", prompt_id)\
                .execute()
            
            # Insert performance record
            performance_data = {
                "prompt_id": prompt_id,
                "accuracy_score": accuracy_score,
                "human_corrections_count": 1 if had_corrections else 0,
                "processing_time_ms": processing_time_ms,
                "token_usage": token_usage,
                "api_cost": api_cost,
                "model_type": prompt_data["model_type"],
                "prompt_type": prompt_data["prompt_type"]
            }
            
            self.supabase.table("prompt_performance").insert(performance_data).execute()
            
        except Exception as e:
            logger.error(f"Failed to track prompt performance: {e}", component="performance_tracker")
    
    async def _update_configuration_performance(
        self,
        extraction_config: Dict[str, Any],
        accuracy_score: float,
        total_cost: float,
        processing_time_ms: int
    ):
        """Update configuration performance in the multi-armed bandit table"""
        
        try:
            # Create configuration key
            config_key = self._create_config_key(extraction_config)
            
            # Check if configuration exists
            result = self.supabase.table("configuration_performance")\
                .select("*")\
                .eq("config_key", config_key)\
                .single()\
                .execute()
            
            if result.data:
                # Update existing configuration
                config_data = result.data
                trials = config_data["trials"] + 1
                successes = config_data["successes"] + accuracy_score
                
                update_data = {
                    "trials": trials,
                    "successes": successes,
                    "avg_accuracy": successes / trials,
                    "avg_cost": (config_data["avg_cost"] * (trials - 1) + total_cost) / trials,
                    "avg_processing_time": (
                        config_data["avg_processing_time"] * (trials - 1) + processing_time_ms
                    ) / trials,
                    "last_used": datetime.utcnow().isoformat()
                }
                
                self.supabase.table("configuration_performance")\
                    .update(update_data)\
                    .eq("config_key", config_key)\
                    .execute()
            else:
                # Create new configuration entry
                insert_data = {
                    "config_key": config_key,
                    "configuration": extraction_config,
                    "trials": 1,
                    "successes": accuracy_score,
                    "avg_accuracy": accuracy_score,
                    "avg_cost": total_cost,
                    "avg_processing_time": processing_time_ms,
                    "last_used": datetime.utcnow().isoformat()
                }
                
                self.supabase.table("configuration_performance").insert(insert_data).execute()
                
        except Exception as e:
            logger.error(f"Failed to update configuration performance: {e}", component="performance_tracker")
    
    def _create_config_key(self, extraction_config: Dict[str, Any]) -> str:
        """Create a unique key for the extraction configuration"""
        
        # Include key configuration parameters
        key_parts = [
            extraction_config.get("model", "gpt4o"),
            extraction_config.get("prompt_type", "extraction"),
            extraction_config.get("temperature", "0.1"),
            extraction_config.get("orchestrator", "custom"),
            extraction_config.get("comparison_mode", "visual")
        ]
        
        return "_".join(str(p) for p in key_parts)


# Create singleton instance
performance_tracker = PerformanceTracker()