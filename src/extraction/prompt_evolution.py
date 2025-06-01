"""
Prompt Evolution Engine
Uses AI to evolve and improve prompts based on performance data and human feedback
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import asyncio
import uuid
from anthropic import AsyncAnthropic
import openai

from ..config import SystemConfig
from ..utils import logger
from supabase import create_client

# Initialize clients
config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key) if config.supabase_url and config.supabase_service_key else None
anthropic_client = AsyncAnthropic(api_key=config.anthropic_api_key) if config.anthropic_api_key else None


class PromptEvolutionEngine:
    """Evolves prompts based on performance data and feedback"""
    
    def __init__(self):
        self.config = config
        self.supabase = supabase
        self.anthropic = anthropic_client
        self.evolution_threshold = 0.7  # Evolve prompts below 70% accuracy
        self.min_samples = 20  # Minimum usage before evolution
        self.safety_checks = True
    
    async def check_and_evolve_prompts(self):
        """Check all prompts and evolve those that need improvement"""
        
        if not self.supabase or not self.anthropic:
            logger.warning("Required services not configured for prompt evolution")
            return
        
        try:
            # Get prompts that need evolution
            prompts_to_evolve = await self._get_prompts_needing_evolution()
            
            for prompt in prompts_to_evolve:
                try:
                    await self._evolve_prompt(prompt)
                    await asyncio.sleep(2)  # Rate limiting
                except Exception as e:
                    logger.error(f"Failed to evolve prompt {prompt['prompt_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed in prompt evolution check: {e}", component="prompt_evolution")
    
    async def _get_prompts_needing_evolution(self) -> List[Dict[str, Any]]:
        """Get prompts that need evolution based on performance"""
        
        result = self.supabase.table("prompt_templates")\
            .select("*")\
            .eq("is_active", True)\
            .eq("is_user_created", True)\
            .lte("performance_score", self.evolution_threshold)\
            .gte("usage_count", self.min_samples)\
            .order("performance_score", asc=True)\
            .limit(5)\
            .execute()
        
        return result.data if result.data else []
    
    async def _evolve_prompt(self, prompt: Dict[str, Any]):
        """Evolve a single prompt based on its performance data"""
        
        logger.info(
            f"Evolving prompt: {prompt['name']}",
            component="prompt_evolution",
            prompt_id=prompt['prompt_id'],
            current_score=prompt['performance_score']
        )
        
        # Get performance history and feedback
        performance_data = await self._get_prompt_performance_data(prompt['prompt_id'])
        common_errors = await self._analyze_common_errors(prompt['prompt_id'])
        
        # Generate evolution using AI
        evolved_prompt = await self._generate_evolved_prompt(
            prompt, performance_data, common_errors
        )
        
        if not evolved_prompt:
            return
        
        # Validate evolved prompt
        if self.safety_checks and not await self._validate_evolved_prompt(evolved_prompt):
            logger.warning(f"Evolved prompt failed validation for {prompt['prompt_id']}")
            return
        
        # Save evolved prompt
        await self._save_evolved_prompt(prompt, evolved_prompt)
    
    async def _get_prompt_performance_data(self, prompt_id: str) -> Dict[str, Any]:
        """Get detailed performance data for a prompt"""
        
        # Get performance records
        perf_result = self.supabase.table("prompt_performance")\
            .select("*")\
            .eq("prompt_id", prompt_id)\
            .order("created_at", desc=True)\
            .limit(50)\
            .execute()
        
        if not perf_result.data:
            return {}
        
        # Analyze performance patterns
        performances = perf_result.data
        
        return {
            "avg_accuracy": sum(p["accuracy_score"] for p in performances) / len(performances),
            "accuracy_trend": self._calculate_trend([p["accuracy_score"] for p in performances]),
            "correction_patterns": self._analyze_corrections(performances),
            "processing_times": [p["processing_time_ms"] for p in performances],
            "sample_count": len(performances)
        }
    
    async def _analyze_common_errors(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Analyze common errors from human corrections"""
        
        # Get extractions that used this prompt
        context_result = self.supabase.table("extraction_contexts")\
            .select("upload_id")\
            .eq("extraction_config->prompt_id", prompt_id)\
            .execute()
        
        if not context_result.data:
            return []
        
        upload_ids = [c["upload_id"] for c in context_result.data]
        
        # Get human corrections for these extractions
        corrections_result = self.supabase.table("human_corrections")\
            .select("*")\
            .in_("upload_id", upload_ids)\
            .execute()
        
        if not corrections_result.data:
            return []
        
        # Analyze correction patterns
        error_patterns = {}
        for correction in corrections_result.data:
            error_type = correction["correction_type"]
            if error_type not in error_patterns:
                error_patterns[error_type] = {
                    "count": 0,
                    "examples": []
                }
            
            error_patterns[error_type]["count"] += 1
            if len(error_patterns[error_type]["examples"]) < 3:
                error_patterns[error_type]["examples"].append({
                    "original": correction["original_ai_result"],
                    "corrected": correction["human_correction"]
                })
        
        return [
            {
                "type": error_type,
                "frequency": data["count"],
                "examples": data["examples"]
            }
            for error_type, data in error_patterns.items()
        ]
    
    async def _generate_evolved_prompt(
        self,
        original_prompt: Dict[str, Any],
        performance_data: Dict[str, Any],
        common_errors: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate an evolved version of the prompt using AI"""
        
        # Get meta-prompt for evolution
        meta_prompt = await self._get_evolution_meta_prompt()
        
        # Prepare context for AI
        evolution_context = {
            "original_prompt": original_prompt["prompt_content"],
            "field_definitions": original_prompt["field_definitions"],
            "current_performance": performance_data,
            "common_errors": common_errors,
            "improvement_goals": self._generate_improvement_goals(performance_data, common_errors)
        }
        
        try:
            # Generate evolved prompt using Claude
            response = await self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": meta_prompt.format(**evolution_context)
                    }
                ]
            )
            
            # Parse response
            evolved_content = response.content[0].text
            
            # Extract JSON if response is formatted
            try:
                evolved_data = json.loads(evolved_content)
                return evolved_data
            except:
                # If not JSON, create structured response
                return {
                    "prompt_content": evolved_content,
                    "field_definitions": original_prompt["field_definitions"],
                    "evolution_reasoning": "AI-generated improvement based on performance data"
                }
                
        except Exception as e:
            logger.error(f"Failed to generate evolved prompt: {e}", component="prompt_evolution")
            return None
    
    async def _get_evolution_meta_prompt(self) -> str:
        """Get the meta-prompt for prompt evolution"""
        
        # Try to get from database
        result = self.supabase.table("meta_prompts")\
            .select("template")\
            .eq("category", "evolution")\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if result.data:
            return result.data["template"]
        
        # Default evolution meta-prompt
        return """You are an expert at optimizing extraction prompts for retail shelf images.

Original Prompt:
{original_prompt}

Field Definitions:
{field_definitions}

Current Performance:
- Average Accuracy: {current_performance[avg_accuracy]:.2%}
- Accuracy Trend: {current_performance[accuracy_trend]}
- Sample Count: {current_performance[sample_count]}

Common Errors:
{common_errors}

Improvement Goals:
{improvement_goals}

Generate an improved version of this prompt that:
1. Addresses the common errors identified
2. Maintains clarity and specificity
3. Includes helpful examples where appropriate
4. Improves accuracy while maintaining efficiency

Format your response as JSON:
{{
    "prompt_content": "The improved prompt text",
    "field_definitions": [updated field definitions if needed],
    "key_improvements": ["List of key improvements made"],
    "evolution_reasoning": "Explanation of why these changes will improve performance"
}}"""
    
    def _generate_improvement_goals(
        self,
        performance_data: Dict[str, Any],
        common_errors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate specific improvement goals based on performance data"""
        
        goals = []
        
        # Accuracy improvement
        current_accuracy = performance_data.get("avg_accuracy", 0)
        if current_accuracy < 0.9:
            goals.append(f"Improve accuracy from {current_accuracy:.1%} to at least 90%")
        
        # Address common errors
        for error in common_errors[:3]:  # Top 3 error types
            if error["frequency"] > 5:
                goals.append(f"Reduce '{error['type']}' errors (currently {error['frequency']} occurrences)")
        
        # Performance consistency
        if performance_data.get("accuracy_trend") == "declining":
            goals.append("Improve consistency and reverse declining accuracy trend")
        
        return goals
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from a list of values"""
        
        if len(values) < 3:
            return "insufficient_data"
        
        # Simple linear regression
        x = list(range(len(values)))
        y = values
        
        n = len(x)
        slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / \
                (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _analyze_corrections(self, performances: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze correction patterns from performance data"""
        
        corrections = {}
        for perf in performances:
            if perf["human_corrections_count"] > 0:
                # Would need more detailed data here
                corrections["total"] = corrections.get("total", 0) + perf["human_corrections_count"]
        
        return corrections
    
    async def _validate_evolved_prompt(self, evolved_prompt: Dict[str, Any]) -> bool:
        """Validate that the evolved prompt is safe and appropriate"""
        
        prompt_content = evolved_prompt.get("prompt_content", "")
        
        # Basic safety checks
        if len(prompt_content) < 50:
            return False
        
        if len(prompt_content) > 5000:
            return False
        
        # Check for required elements
        required_keywords = ["extract", "product", "shelf", "image"]
        if not any(keyword in prompt_content.lower() for keyword in required_keywords):
            return False
        
        # Check field definitions are valid
        field_defs = evolved_prompt.get("field_definitions", [])
        if not field_defs or not isinstance(field_defs, list):
            return False
        
        return True
    
    async def _save_evolved_prompt(
        self,
        original_prompt: Dict[str, Any],
        evolved_data: Dict[str, Any]
    ):
        """Save the evolved prompt to the database"""
        
        new_version = f"{float(original_prompt['prompt_version']) + 0.1:.1f}"
        
        evolved_prompt = {
            "prompt_id": str(uuid.uuid4()),
            "template_id": f"{original_prompt['template_id']}_evolved_v{new_version}",
            "name": f"{original_prompt['name']} (AI Evolved)",
            "description": evolved_data.get("evolution_reasoning", "AI-evolved for better performance"),
            "prompt_type": original_prompt["prompt_type"],
            "model_type": original_prompt["model_type"],
            "prompt_version": new_version,
            "prompt_content": evolved_data["prompt_content"],
            "field_definitions": evolved_data.get("field_definitions", original_prompt["field_definitions"]),
            "tags": original_prompt["tags"] + ["ai-evolved", "automated"],
            "is_user_created": False,
            "is_active": False,  # Start inactive for testing
            "parent_prompt_id": original_prompt["prompt_id"],
            "performance_score": 0.0,
            "usage_count": 0,
            "correction_rate": 0.0,
            "created_from_feedback": True,
            "autonomy_level": 1  # Start at lowest autonomy
        }
        
        # Save to database
        result = self.supabase.table("prompt_templates").insert(evolved_prompt).execute()
        
        if result.data:
            logger.info(
                f"Saved evolved prompt",
                component="prompt_evolution",
                original_prompt_id=original_prompt["prompt_id"],
                evolved_prompt_id=evolved_prompt["prompt_id"],
                improvements=evolved_data.get("key_improvements", [])
            )
            
            # Schedule A/B test
            await self._schedule_ab_test(original_prompt["prompt_id"], evolved_prompt["prompt_id"])
    
    async def _schedule_ab_test(self, original_id: str, evolved_id: str):
        """Schedule an A/B test between original and evolved prompts"""
        
        ab_test = {
            "test_name": f"Evolution test {datetime.utcnow().strftime('%Y%m%d')}",
            "variant_a_id": original_id,
            "variant_b_id": evolved_id,
            "status": "scheduled",
            "target_samples": 50,
            "current_samples_a": 0,
            "current_samples_b": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.supabase.table("prompt_ab_tests").insert(ab_test).execute()


# Create singleton instance
prompt_evolution_engine = PromptEvolutionEngine()