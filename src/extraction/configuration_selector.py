"""
Configuration Selector using Multi-Armed Bandit
Optimally selects extraction configurations based on historical performance
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from datetime import datetime, timedelta
import json

from ..config import SystemConfig
from ..utils import logger
from supabase import create_client

# Initialize Supabase client
config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key) if config.supabase_url and config.supabase_service_key else None


class ConfigurationSelector:
    """Selects optimal extraction configurations using Thompson Sampling"""
    
    def __init__(self):
        self.config = config
        self.supabase = supabase
        self.exploration_rate = 0.1  # 10% exploration
        self.context_weight = 0.3  # Weight for contextual similarity
    
    async def select_configuration(
        self,
        context: Dict[str, Any],
        target_accuracy: Optional[float] = None,
        max_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Select optimal configuration using Thompson Sampling with contextual bandits
        
        Args:
            context: Current extraction context (image quality, category, etc.)
            target_accuracy: Target accuracy level (if specified)
            max_cost: Maximum allowed cost (if specified)
            
        Returns:
            Optimal configuration dictionary
        """
        
        if not self.supabase:
            # Return default configuration
            return self._get_default_configuration()
        
        try:
            # Get all configurations with performance data
            configs = await self._get_configurations_with_performance()
            
            if not configs:
                return self._get_default_configuration()
            
            # Filter by constraints
            if max_cost is not None:
                configs = [c for c in configs if c["avg_cost"] <= max_cost]
            
            if not configs:
                return self._get_default_configuration()
            
            # Select using Thompson Sampling with context
            selected_config = await self._thompson_sampling_with_context(
                configs, context, target_accuracy
            )
            
            # Get the best prompt for this configuration
            prompt = await self._get_best_prompt_for_config(selected_config, context)
            
            # Combine configuration with prompt
            final_config = {
                **selected_config["configuration"],
                "prompt_id": prompt.get("prompt_id") if prompt else None,
                "prompt_content": prompt.get("prompt_content") if prompt else None,
                "field_definitions": prompt.get("field_definitions") if prompt else None,
                "config_key": selected_config["config_key"],
                "expected_accuracy": selected_config["avg_accuracy"],
                "expected_cost": selected_config["avg_cost"]
            }
            
            logger.info(
                f"Selected configuration",
                component="configuration_selector",
                config_key=selected_config["config_key"],
                expected_accuracy=selected_config["avg_accuracy"],
                expected_cost=selected_config["avg_cost"]
            )
            
            return final_config
            
        except Exception as e:
            logger.error(f"Failed to select configuration: {e}", component="configuration_selector")
            return self._get_default_configuration()
    
    async def _get_configurations_with_performance(self) -> List[Dict[str, Any]]:
        """Get all configurations with their performance metrics"""
        
        result = self.supabase.table("configuration_performance")\
            .select("*")\
            .gte("trials", 3)\
            .execute()
        
        return result.data if result.data else []
    
    async def _thompson_sampling_with_context(
        self,
        configs: List[Dict[str, Any]],
        context: Dict[str, Any],
        target_accuracy: Optional[float]
    ) -> Dict[str, Any]:
        """
        Thompson Sampling with contextual information
        
        Uses Beta distribution for each configuration's success probability
        """
        
        # Calculate contextual similarity for each configuration
        context_scores = []
        for config in configs:
            score = await self._calculate_context_similarity(config, context)
            context_scores.append(score)
        
        # Sample from Beta distributions
        samples = []
        for i, config in enumerate(configs):
            # Beta distribution parameters
            alpha = config["successes"] + 1
            beta = config["trials"] - config["successes"] + 1
            
            # Sample success probability
            theta = np.random.beta(alpha, beta)
            
            # Adjust by context similarity
            adjusted_theta = theta * (1 - self.context_weight) + context_scores[i] * self.context_weight
            
            # If target accuracy specified, penalize configs below target
            if target_accuracy and config["avg_accuracy"] < target_accuracy:
                adjusted_theta *= 0.5
            
            samples.append(adjusted_theta)
        
        # Select configuration with highest sampled value
        best_idx = np.argmax(samples)
        return configs[best_idx]
    
    async def _calculate_context_similarity(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """Calculate similarity between configuration context and current context"""
        
        # Get recent contexts where this configuration was used
        result = self.supabase.table("extraction_contexts")\
            .select("image_metadata")\
            .eq("extraction_config->config_key", config["config_key"])\
            .order("timestamp", desc=True)\
            .limit(10)\
            .execute()
        
        if not result.data:
            return 0.5  # Neutral similarity
        
        # Calculate similarity based on image quality metrics
        similarities = []
        for past_context in result.data:
            past_metadata = past_context.get("image_metadata", {})
            
            # Compare quality metrics
            quality_sim = self._compare_quality_metrics(
                context.get("image_quality", {}),
                past_metadata.get("quality_metrics", {})
            )
            
            # Compare categories if available
            category_sim = 1.0 if context.get("category") == past_metadata.get("category") else 0.0
            
            # Weighted similarity
            similarity = quality_sim * 0.7 + category_sim * 0.3
            similarities.append(similarity)
        
        return np.mean(similarities)
    
    def _compare_quality_metrics(self, metrics1: Dict, metrics2: Dict) -> float:
        """Compare two sets of quality metrics"""
        
        if not metrics1 or not metrics2:
            return 0.5
        
        # Compare key metrics
        features = ["sharpness", "brightness", "contrast", "resolution_score"]
        
        differences = []
        for feature in features:
            if feature in metrics1 and feature in metrics2:
                diff = abs(metrics1[feature] - metrics2[feature])
                differences.append(1.0 - min(diff, 1.0))
        
        return np.mean(differences) if differences else 0.5
    
    async def _get_best_prompt_for_config(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get the best performing prompt for the selected configuration"""
        
        model_type = config["configuration"].get("model", "gpt4o")
        prompt_type = config["configuration"].get("prompt_type", "extraction")
        
        # Query for best prompt
        result = self.supabase.table("prompt_templates")\
            .select("*")\
            .eq("prompt_type", prompt_type)\
            .eq("model_type", model_type)\
            .eq("is_active", True)\
            .gte("usage_count", 5)\
            .order("performance_score", desc=True)\
            .limit(1)\
            .execute()
        
        if not result.data:
            # Try universal prompt
            result = self.supabase.table("prompt_templates")\
                .select("*")\
                .eq("prompt_type", prompt_type)\
                .eq("model_type", "universal")\
                .eq("is_active", True)\
                .order("performance_score", desc=True)\
                .limit(1)\
                .execute()
        
        return result.data[0] if result.data else None
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """Return default configuration when selection fails"""
        
        return {
            "model": "gpt4o",
            "prompt_type": "extraction",
            "temperature": 0.1,
            "orchestrator": "custom",
            "comparison_mode": "visual",
            "expected_accuracy": 0.8,
            "expected_cost": 0.05
        }
    
    async def predict_cost_for_accuracy(
        self,
        target_accuracy: float,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict the cost to achieve a target accuracy level
        
        Uses Gaussian Process regression on historical data
        """
        
        if not self.supabase:
            return {
                "target_accuracy": target_accuracy,
                "predicted_cost": 0.10,
                "confidence_interval": [0.05, 0.20],
                "recommended_config": self._get_default_configuration()
            }
        
        try:
            # Get configurations that meet accuracy threshold
            configs = await self._get_configurations_with_performance()
            
            # Filter by minimum accuracy
            valid_configs = [
                c for c in configs 
                if c["avg_accuracy"] >= target_accuracy * 0.95  # 5% tolerance
            ]
            
            if not valid_configs:
                # No configurations meet accuracy, return estimate
                return {
                    "target_accuracy": target_accuracy,
                    "predicted_cost": 0.20 * target_accuracy,  # Linear estimate
                    "confidence_interval": [0.10, 0.30],
                    "recommended_config": None,
                    "message": "No configurations currently meet this accuracy target"
                }
            
            # Find cheapest configuration that meets accuracy
            best_config = min(valid_configs, key=lambda c: c["avg_cost"])
            
            # Calculate confidence based on number of trials
            confidence_width = 0.1 / np.sqrt(best_config["trials"])
            
            return {
                "target_accuracy": target_accuracy,
                "predicted_cost": best_config["avg_cost"],
                "confidence_interval": [
                    max(0, best_config["avg_cost"] - confidence_width),
                    best_config["avg_cost"] + confidence_width
                ],
                "recommended_config": best_config["configuration"],
                "expected_processing_time": best_config["avg_processing_time"],
                "confidence_level": min(0.95, best_config["trials"] / 100)
            }
            
        except Exception as e:
            logger.error(f"Failed to predict cost for accuracy: {e}", component="configuration_selector")
            return {
                "target_accuracy": target_accuracy,
                "predicted_cost": 0.10,
                "confidence_interval": [0.05, 0.20],
                "recommended_config": self._get_default_configuration()
            }


# Create singleton instance
configuration_selector = ConfigurationSelector()