"""
Modular Extraction Engine
Sequential extraction system with steps that build on each other
Enhanced with logging, cost tracking, error handling, and multi-image support
"""

import asyncio
import json
import base64
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import instructor
import openai
import anthropic
import google.generativeai as genai
from pydantic import BaseModel, ValidationError

from ..config import SystemConfig
from ..utils import (
    logger, CostTracker, CostLimitExceededException, ErrorHandler,
    with_retry, RetryConfig, GracefulDegradation, MultiImageCoordinator
)
from .models import (
    ExtractionStep, AIModelType, ProductExtraction,
    CompleteShelfExtraction, ConfidenceLevel, ValidationFlag, NonProductElements
)
from .prompts import PromptTemplates


class ModularExtractionEngine:
    """Extraction system with sequential, modular steps that build on each other"""
    
    def __init__(self, config: SystemConfig, temperature: float = 0.1):
        self.config = config
        self.temperature = temperature
        self._initialize_ai_clients()
        self.prompt_templates = PromptTemplates()
        self.step_history = []
        
        # Enhanced capabilities
        self.cost_tracker: Optional[CostTracker] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.image_coordinator: Optional[MultiImageCoordinator] = None
        
        logger.info(
            "Modular Extraction Engine initialized",
            component="extraction_engine",
            models_configured=len(self.config.models),
            temperature=temperature
        )
    
    def _initialize_ai_clients(self):
        """Initialize AI model clients with Instructor for structured outputs"""
        try:
            self.openai_client = instructor.from_openai(
                openai.OpenAI(api_key=self.config.openai_api_key)
            )
            self.anthropic_client = instructor.from_anthropic(
                anthropic.Anthropic(api_key=self.config.anthropic_api_key)
            )
            genai.configure(api_key=self.config.google_api_key)
            # Configure generation with temperature
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                top_p=1,
                top_k=1,
                max_output_tokens=8000,
            )
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp', generation_config=generation_config)
            
            logger.info(
                "AI clients initialized successfully",
                component="extraction_engine",
                clients=["openai", "anthropic", "gemini"]
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize AI clients: {e}",
                component="extraction_engine"
            )
            raise
    
    def initialize_for_agent(self, agent_id: str, cost_limit: float):
        """Initialize engine for a specific agent run"""
        self.cost_tracker = CostTracker(cost_limit, agent_id)
        self.error_handler = ErrorHandler(agent_id)
        self.image_coordinator = MultiImageCoordinator(agent_id)
        
        logger.info(
            f"Extraction engine initialized for agent {agent_id}",
            component="extraction_engine",
            agent_id=agent_id,
            cost_limit=cost_limit
        )
    
    async def design_extraction_sequence(self, 
                                       images: Dict[str, bytes],
                                       previous_failures: List = None,
                                       agent_id: str = None) -> List[ExtractionStep]:
        """Design extraction sequence based on context and previous failures"""
        
        if agent_id and not self.cost_tracker:
            self.initialize_for_agent(agent_id, self.config.max_api_cost_per_extraction)
        
        # Setup multi-image coordination
        if self.image_coordinator:
            self.image_coordinator.add_images(images)
        
        if previous_failures is None:
            previous_failures = []
        
        # Default sequence for first attempt
        if not previous_failures:
            sequence = self._get_default_sequence()
            logger.info(
                f"Designed default extraction sequence with {len(sequence)} steps",
                component="extraction_engine",
                agent_id=agent_id,
                sequence_length=len(sequence)
            )
            return sequence
        
        # Adaptive sequence based on previous failures
        sequence = self._get_adaptive_sequence(previous_failures)
        logger.info(
            f"Designed adaptive extraction sequence with {len(sequence)} steps",
            component="extraction_engine",
            agent_id=agent_id,
            sequence_length=len(sequence),
            failure_count=len(previous_failures)
        )
        return sequence
    
    def _get_default_sequence(self) -> List[ExtractionStep]:
        """Default extraction sequence for first attempt"""
        return [
            ExtractionStep(
                step_id="scaffolding",
                model=AIModelType.CLAUDE_3_SONNET,
                prompt_template="scaffolding_analysis",
                input_dependencies=[],
                output_schema="ShelfStructure"
            ),
            ExtractionStep(
                step_id="products",
                model=AIModelType.GPT4O_LATEST,
                prompt_template="product_identification",
                input_dependencies=["scaffolding"],
                output_schema="List[ProductExtraction]"
            ),
            ExtractionStep(
                step_id="validation",
                model=AIModelType.CLAUDE_3_SONNET,
                prompt_template="cross_validation",
                input_dependencies=["scaffolding", "products"],
                output_schema="CompleteShelfExtraction"
            )
        ]
    
    def _get_adaptive_sequence(self, previous_failures: List) -> List[ExtractionStep]:
        """Adaptive sequence based on previous failures"""
        sequence = []
        
        # Check for structure errors
        structure_issues = [f for f in previous_failures if "structure" in f.get("root_cause", "")]
        if structure_issues:
            sequence.append(ExtractionStep(
                step_id="enhanced_scaffolding",
                model=AIModelType.CLAUDE_3_SONNET,
                prompt_template="scaffolding_enhanced",
                input_dependencies=[],
                output_schema="ShelfStructure"
            ))
            logger.debug(
                "Added enhanced scaffolding step due to structure issues",
                component="extraction_engine"
            )
        else:
            sequence.append(ExtractionStep(
                step_id="scaffolding",
                model=AIModelType.CLAUDE_3_SONNET,
                prompt_template="scaffolding_analysis",
                input_dependencies=[],
                output_schema="ShelfStructure"
            ))
        
        # Product identification
        sequence.append(ExtractionStep(
            step_id="products",
            model=AIModelType.GPT4O_LATEST,
            prompt_template="product_identification",
            input_dependencies=["scaffolding"] if "enhanced_scaffolding" not in [s.step_id for s in sequence] else ["enhanced_scaffolding"],
            output_schema="List[ProductExtraction]"
        ))
        
        # Check for price errors
        price_issues = [f for f in previous_failures if "price" in f.get("type", "")]
        if price_issues:
            sequence.append(ExtractionStep(
                step_id="specialized_pricing",
                model=AIModelType.GEMINI_2_FLASH,
                prompt_template="price_extraction_specialized",
                input_dependencies=["products"],
                output_schema="Dict[str, float]"
            ))
            logger.debug(
                "Added specialized pricing step due to price issues",
                component="extraction_engine"
            )
        
        # Check for facing count issues
        facing_issues = [f for f in previous_failures if "facing" in f.get("type", "")]
        if facing_issues:
            sequence.append(ExtractionStep(
                step_id="facing_quantification",
                model=AIModelType.CLAUDE_3_SONNET,
                prompt_template="facing_quantification",
                input_dependencies=["products"],
                output_schema="Dict[str, int]"
            ))
            logger.debug(
                "Added facing quantification step due to facing issues",
                component="extraction_engine"
            )
        
        # Always end with validation
        sequence.append(ExtractionStep(
            step_id="final_validation",
            model=AIModelType.CLAUDE_3_SONNET,
            prompt_template="cross_validation",
            input_dependencies=[s.step_id for s in sequence],
            output_schema="CompleteShelfExtraction"
        ))
        
        return sequence
    
    @with_retry(RetryConfig(max_retries=2, base_delay=2.0))
    async def execute_extraction_sequence(self, 
                                        upload_id: str,
                                        images: Dict[str, bytes],
                                        extraction_steps: List[ExtractionStep],
                                        agent_id: str = None) -> CompleteShelfExtraction:
        """Execute the designed extraction sequence step by step"""
        
        if agent_id and not self.cost_tracker:
            self.initialize_for_agent(agent_id, self.config.max_api_cost_per_extraction)
        
        start_time = time.time()
        step_outputs = {}
        api_costs = []
        models_used = set()
        
        logger.info(
            f"Starting extraction sequence with {len(extraction_steps)} steps",
            component="extraction_engine",
            agent_id=agent_id,
            upload_id=upload_id,
            step_count=len(extraction_steps)
        )
        
        for step in extraction_steps:
            logger.info(
                f"Executing step: {step.step_id}",
                component="extraction_engine",
                agent_id=agent_id,
                step_id=step.step_id,
                model=step.model.value
            )
            
            try:
                # Check cost limits before proceeding
                if self.cost_tracker and not self.cost_tracker.check_remaining_budget(step.step_id, 0.10):
                    raise CostLimitExceededException(
                        self.cost_tracker.total_cost, 
                        self.cost_tracker.cost_limit, 
                        step.step_id
                    )
                
                # Prepare inputs for this step
                step_inputs = self._prepare_step_inputs(step, step_outputs, images)
                
                # Execute the step
                step_output, cost = await self._execute_step(step, step_inputs, agent_id)
                
                # Track cost
                if self.cost_tracker:
                    self.cost_tracker.add_cost(step.step_id, cost)
                
                # Store output for next steps
                step_outputs[step.step_id] = step_output
                api_costs.append(cost)
                models_used.add(step.model)
                
                # Store in history for debugging
                # Convert output to serializable format
                serializable_output = step_output
                if hasattr(step_output, 'model_dump'):
                    serializable_output = step_output.model_dump()
                elif isinstance(step_output, list) and step_output and hasattr(step_output[0], 'model_dump'):
                    serializable_output = [item.model_dump() for item in step_output]
                
                self.step_history.append({
                    'step_id': step.step_id,
                    'model': step.model.value,
                    'output': serializable_output,
                    'cost': cost,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                logger.info(
                    f"Step {step.step_id} completed successfully",
                    component="extraction_engine",
                    agent_id=agent_id,
                    step_id=step.step_id,
                    duration=time.time() - start_time,
                    cost=cost
                )
                
            except CostLimitExceededException as e:
                logger.error(
                    f"Cost limit exceeded during step {step.step_id}",
                    component="extraction_engine",
                    agent_id=agent_id,
                    step_id=step.step_id,
                    cost_limit=e.limit,
                    current_cost=e.current_cost
                )
                raise
                
            except Exception as e:
                if self.error_handler:
                    self.error_handler.record_error(e, {
                        'step_id': step.step_id,
                        'model': step.model.value,
                        'upload_id': upload_id
                    })
                
                logger.error(
                    f"Step {step.step_id} failed: {e}",
                    component="extraction_engine",
                    agent_id=agent_id,
                    step_id=step.step_id,
                    error=str(e)
                )
                raise
        
        # The final step should produce CompleteShelfExtraction
        final_step_id = extraction_steps[-1].step_id
        final_output = step_outputs[final_step_id]
        
        # If final output isn't CompleteShelfExtraction, construct it
        if not isinstance(final_output, CompleteShelfExtraction):
            final_output = await self._construct_complete_extraction(
                upload_id, step_outputs, images, models_used, api_costs, start_time, agent_id
            )
        
        total_duration = time.time() - start_time
        total_cost = sum(api_costs)
        
        logger.info(
            f"Extraction sequence completed successfully",
            component="extraction_engine",
            agent_id=agent_id,
            upload_id=upload_id,
            total_duration=total_duration,
            total_cost=total_cost,
            products_found=final_output.total_products_detected
        )
        
        return final_output
    
    def _prepare_step_inputs(self, 
                           step: ExtractionStep, 
                           previous_outputs: Dict, 
                           images: Dict[str, bytes]) -> Dict:
        """Prepare inputs for an extraction step with multi-image support"""
        
        # Get appropriate images for this step
        if self.image_coordinator:
            step_images = self.image_coordinator.get_images_for_step(step.step_id)
            logger.debug(
                f"Selected {len(step_images)} images for step {step.step_id}",
                component="extraction_engine",
                step_id=step.step_id,
                image_types=list(step_images.keys())
            )
        else:
            step_images = images
        
        inputs = {"images": step_images}
        
        # Add outputs from dependency steps
        for dep in step.input_dependencies:
            if dep in previous_outputs:
                inputs[f"{dep}_data"] = previous_outputs[dep]
        
        return inputs
    
    async def _execute_step(self, step: ExtractionStep, inputs: Dict, agent_id: str = None) -> tuple[Any, float]:
        """Execute a single extraction step and return output + cost"""
        
        # Get the prompt template and fill in dependencies
        prompt = self.prompt_templates.get_template(step.prompt_template)
        
        # Enhance prompt with multi-image context if available
        if self.image_coordinator:
            prompt = self.image_coordinator.prepare_multi_image_prompt(prompt, step.step_id)
        
        # Fill in any dependency data
        for key, value in inputs.items():
            if key.endswith("_data"):
                placeholder = "{" + key + "}"
                if placeholder in prompt:
                    # Convert Pydantic models to dicts for serialization
                    serializable_value = value
                    if hasattr(value, 'model_dump'):
                        serializable_value = value.model_dump()
                    elif isinstance(value, list) and value and hasattr(value[0], 'model_dump'):
                        serializable_value = [item.model_dump() for item in value]
                    
                    if isinstance(serializable_value, (dict, list)):
                        # Use default=str to handle datetime and other non-serializable types
                        prompt = prompt.replace(placeholder, json.dumps(serializable_value, indent=2, default=str))
                    else:
                        prompt = prompt.replace(placeholder, str(serializable_value))
        
        # Execute with automatic model fallback for robustness
        return await self._execute_with_fallback(step.model, prompt, inputs["images"], step.output_schema, agent_id)
    
    def _get_api_model_name(self, model_id: str) -> tuple[str, str]:
        """Map frontend model ID to actual API model name and provider"""
        model_mapping = {
            # OpenAI models - Complete mapping from UI
            "gpt-4.1": ("openai", "gpt-4o-2024-11-20"),  # Latest GPT-4o as fallback for GPT-4.1
            "gpt-4.1-mini": ("openai", "gpt-4o-mini"),
            "gpt-4.1-nano": ("openai", "gpt-4o-mini"),   # Using mini as fallback
            "gpt-4o": ("openai", "gpt-4o-2024-11-20"),
            "gpt-4o-mini": ("openai", "gpt-4o-mini"),
            "o3": ("openai", "gpt-4o-2024-11-20"),       # Using GPT-4o as fallback for o3
            "o4-mini": ("openai", "gpt-4o-mini"),        # Using GPT-4o mini as fallback
            
            # Anthropic models - Complete mapping from UI
            "claude-3-5-sonnet-v2": ("anthropic", "claude-3-5-sonnet-20241022"),
            "claude-3-7-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),  # Using 3.5 as fallback
            "claude-4-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),    # Using 3.5 as fallback until Claude 4 available
            "claude-4-opus": ("anthropic", "claude-3-opus-20240229"),      # Most capable Claude model
            
            # Google models - Complete mapping from UI
            "gemini-2.5-flash": ("google", "gemini-2.0-flash-exp"),
            "gemini-2.5-flash-thinking": ("google", "gemini-2.0-flash-thinking-exp-01-21"),  # Thinking model
            "gemini-2.5-pro": ("google", "gemini-2.0-pro-exp"),
            
            # Legacy/common variations
            "claude-3-5-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
            "claude-3-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
            "gemini-pro": ("google", "gemini-2.0-pro-exp"),
            "gemini-flash": ("google", "gemini-2.0-flash-exp"),
        }
        
        return model_mapping.get(model_id, ("openai", "gpt-4o-2024-11-20"))
    
    def _get_quota_fallback_chain(self, model_id: str, provider: str) -> List[str]:
        """Get fallback chain for quota exhaustion - multiple alternatives"""
        fallback_chains = {
            # OpenAI model fallbacks -> Use Claude, then GPT alternatives
            "gpt-4.1": ["claude-4-opus", "gpt-4o", "claude-3-5-sonnet-v2"],
            "gpt-4.1-mini": ["claude-3-5-sonnet-v2", "gpt-4o-mini", "claude-4-opus"],
            "gpt-4.1-nano": ["claude-3-5-sonnet-v2", "gpt-4o-mini"],
            "gpt-4o": ["claude-3-5-sonnet-v2", "claude-4-opus", "gpt-4o-mini"],
            "gpt-4o-mini": ["claude-3-5-sonnet-v2", "gpt-4o"],
            "o3": ["claude-4-opus", "gpt-4o", "claude-3-5-sonnet-v2"],
            "o4-mini": ["claude-3-5-sonnet-v2", "gpt-4o-mini"],
            
            # Anthropic model fallbacks -> Use GPT-4, then alternatives
            "claude-4-opus": ["gpt-4o", "claude-3-5-sonnet-v2", "gpt-4o-mini"],
            "claude-4-sonnet": ["gpt-4o", "claude-3-5-sonnet-v2"], 
            "claude-3-5-sonnet-v2": ["gpt-4o", "gpt-4o-mini", "claude-4-opus"],
            "claude-3-7-sonnet": ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet-v2"],
            "claude-3-5-sonnet": ["gpt-4o", "gpt-4o-mini"],
            "claude-3-sonnet": ["gpt-4o", "claude-3-5-sonnet-v2"],
            
            # Google model fallbacks -> Use Claude and GPT alternatives
            "gemini-2.5-pro": ["claude-4-opus", "gpt-4o", "claude-3-5-sonnet-v2"],
            "gemini-2.5-flash": ["claude-3-5-sonnet-v2", "gpt-4o", "gpt-4o-mini"], 
            "gemini-2.5-flash-thinking": ["gpt-4o", "claude-3-5-sonnet-v2"],
            "gemini-pro": ["claude-4-opus", "gpt-4o"],
            "gemini-flash": ["claude-3-5-sonnet-v2", "gpt-4o-mini"],
        }
        
        return fallback_chains.get(model_id, ["gpt-4o", "claude-3-5-sonnet-v2"])  # Default fallback chain
    
    async def execute_with_model_id(self, model_id: str, prompt: str, images: Dict[str, bytes], output_schema: Any, agent_id: str = None) -> tuple[Any, float]:
        """Execute with specific frontend model ID with quota-aware fallback"""
        provider, api_model = self._get_api_model_name(model_id)
        
        logger.info(
            f"Executing with model {model_id} -> {api_model} ({provider})",
            component="extraction_engine",
            model_id=model_id,
            api_model=api_model,
            provider=provider
        )
        
        try:
            # Try the requested model first
            if provider == "openai":
                return await self._execute_with_gpt4o_model(prompt, images, output_schema, api_model, agent_id)
            elif provider == "anthropic":
                return await self._execute_with_claude_model(prompt, images, output_schema, api_model, agent_id)
            elif provider == "google":
                return await self._execute_with_gemini_model(prompt, images, output_schema, api_model, agent_id)
            else:
                # Fallback to GPT-4o
                return await self._execute_with_gpt4o(prompt, images, output_schema, agent_id)
                
        except Exception as e:
            error_msg = str(e)
            
            # Check if it's a quota/rate limit error (429, quota exceeded, etc.)
            is_quota_error = any(phrase in error_msg.lower() for phrase in [
                "429", "quota", "rate limit", "exceeded", "insufficient_quota",
                "billing", "usage limit", "resource_exhausted"
            ])
            
            if is_quota_error:
                logger.warning(
                    f"Quota exhausted for {model_id}, attempting fallback chain",
                    component="extraction_engine",
                    original_model=model_id,
                    error=error_msg[:100]
                )
                
                # Get fallback chain for smart multi-level fallback
                fallback_chain = self._get_quota_fallback_chain(model_id, provider)
                
                if fallback_chain:
                    logger.info(
                        f"Quota fallback chain: {model_id} -> {fallback_chain}",
                        component="extraction_engine",
                        original_model=model_id,
                        fallback_chain=fallback_chain
                    )
                    
                    # Try each fallback in sequence
                    for i, fallback_model in enumerate(fallback_chain):
                        try:
                            fallback_provider, fallback_api_model = self._get_api_model_name(fallback_model)
                            
                            logger.info(
                                f"Attempting fallback {i+1}/{len(fallback_chain)}: {fallback_model}",
                                component="extraction_engine",
                                fallback_attempt=i+1,
                                fallback_model=fallback_model
                            )
                            
                            if fallback_provider == "openai":
                                result, cost = await self._execute_with_gpt4o_model(prompt, images, output_schema, fallback_api_model, agent_id)
                            elif fallback_provider == "anthropic":
                                result, cost = await self._execute_with_claude_model(prompt, images, output_schema, fallback_api_model, agent_id)
                            elif fallback_provider == "google":
                                result, cost = await self._execute_with_gemini_model(prompt, images, output_schema, fallback_api_model, agent_id)
                            else:
                                result, cost = await self._execute_with_gpt4o(prompt, images, output_schema, agent_id)
                            
                            logger.info(
                                f"✅ Quota fallback successful: {model_id} -> {fallback_model}",
                                component="extraction_engine",
                                original_model=model_id,
                                successful_fallback=fallback_model,
                                fallback_attempt=i+1
                            )
                            
                            return result, cost
                            
                        except Exception as fallback_error:
                            fallback_error_msg = str(fallback_error)
                            
                            # Check if this fallback also has quota issues
                            is_fallback_quota_error = any(phrase in fallback_error_msg.lower() for phrase in [
                                "429", "quota", "rate limit", "exceeded", "insufficient_quota",
                                "billing", "usage limit", "resource_exhausted"
                            ])
                            
                            if is_fallback_quota_error:
                                logger.warning(
                                    f"Fallback {fallback_model} also hit quota, trying next fallback",
                                    component="extraction_engine",
                                    fallback_model=fallback_model,
                                    fallback_attempt=i+1
                                )
                            else:
                                logger.warning(
                                    f"Fallback {fallback_model} failed (non-quota): {str(fallback_error)[:100]}, trying next",
                                    component="extraction_engine",
                                    fallback_model=fallback_model,
                                    fallback_attempt=i+1,
                                    error=str(fallback_error)[:100]
                                )
                            
                            # Continue to next fallback
                            continue
                    
                    # All fallbacks failed
                    logger.error(
                        f"All fallbacks failed for {model_id}",
                        component="extraction_engine",
                        model_id=model_id,
                        tried_fallbacks=fallback_chain
                    )
                    raise e
                else:
                    logger.error(
                        f"No fallback chain available for {model_id}",
                        component="extraction_engine",
                        model_id=model_id
                    )
                    raise e
            else:
                # Non-quota error, re-raise
                raise e
    
    async def _execute_with_fallback(self, primary_model: AIModelType, prompt: str, images: Dict[str, bytes], output_schema: Any, agent_id: str = None) -> tuple[Any, float]:
        """Execute step with automatic model fallback for maximum reliability"""
        
        # Define fallback order: try primary model first, then fallbacks
        fallback_chain = [primary_model]
        
        # Add other models as fallbacks (avoid duplicates)
        all_models = [AIModelType.CLAUDE_3_SONNET, AIModelType.GPT4O_LATEST, AIModelType.GEMINI_2_FLASH]
        for model in all_models:
            if model != primary_model:
                fallback_chain.append(model)
        
        last_error = None
        
        for i, model in enumerate(fallback_chain):
            is_fallback = i > 0
            
            try:
                if model == AIModelType.CLAUDE_3_SONNET:
                    result = await self._execute_with_claude(prompt, images, output_schema, agent_id)
                elif model == AIModelType.GPT4O_LATEST:
                    result = await self._execute_with_gpt4o(prompt, images, output_schema, agent_id)
                elif model == AIModelType.GEMINI_2_FLASH:
                    result = await self._execute_with_gemini(prompt, images, output_schema, agent_id)
                else:
                    continue
                
                # Success! Log if we used a fallback
                if is_fallback:
                    logger.info(
                        f"Fallback successful: {model.value} worked after {primary_model.value} failed",
                        component="extraction_engine",
                        agent_id=agent_id,
                        primary_model=primary_model.value,
                        successful_model=model.value,
                        attempt_number=i+1
                    )
                
                return result
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Check if it's a content moderation or similar policy issue
                is_content_issue = any(phrase in error_msg.lower() for phrase in [
                    "could not process image",
                    "content policy",
                    "safety",
                    "inappropriate",
                    "invalid_request_error"
                ])
                
                if is_fallback:
                    logger.warning(
                        f"Fallback model {model.value} also failed: {error_msg[:100]}",
                        component="extraction_engine",
                        agent_id=agent_id,
                        model=model.value,
                        error_type="content_moderation" if is_content_issue else "api_error"
                    )
                else:
                    logger.warning(
                        f"Primary model {model.value} failed, trying fallbacks: {error_msg[:100]}",
                        component="extraction_engine",
                        agent_id=agent_id,
                        model=model.value,
                        error_type="content_moderation" if is_content_issue else "api_error"
                    )
                
                # Continue to next model in chain
                continue
        
        # All models failed
        logger.error(
            f"All models failed for this step. Last error: {str(last_error)[:200]}",
            component="extraction_engine",
            agent_id=agent_id,
            tried_models=[m.value for m in fallback_chain]
        )
        raise Exception(f"All AI models failed. Last error: {last_error}")
    
    async def _log_model_usage(self, model_id: str, model_provider: str, prompt_length: int, completion_length: int, duration: float, cost: float, stage: str, agent_id: str = None):
        """Log model usage to analytics"""
        try:
            # Only log if we have queue item context
            if hasattr(self, 'queue_item_id') and hasattr(self, 'extraction_run_id'):
                from ..utils.model_usage_tracker import get_model_usage_tracker
                tracker = get_model_usage_tracker()
                
                # Estimate tokens (rough approximation)
                prompt_tokens = prompt_length // 4  # ~4 chars per token
                completion_tokens = completion_length // 4  # Based on max_tokens
                
                # Extract iteration number from agent_id
                iteration_number = 1
                if agent_id and '_' in agent_id:
                    try:
                        iteration_number = int(agent_id.split('_')[-1])
                    except:
                        pass
                
                await tracker.log_model_usage(
                    queue_item_id=self.queue_item_id,
                    extraction_run_id=self.extraction_run_id,
                    stage=stage,
                    model_id=model_id,
                    model_provider=model_provider,
                    iteration_number=iteration_number,
                    temperature=self.temperature,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    response_time_ms=int(duration * 1000),
                    api_cost=cost,
                    success=True
                )
        except Exception as e:
            logger.error(f"Failed to log model usage: {e}", component="extraction_engine")
    
    def _compress_image_for_model(self, img_data: bytes, model_type: str, img_name: str = "image") -> bytes:
        """Compress image only if needed for specific model limits"""
        MODEL_LIMITS = {
            'claude': 5 * 1024 * 1024,      # 5 MB
            'gpt4': 20 * 1024 * 1024,       # 20 MB  
            'gemini': 20 * 1024 * 1024,     # 20 MB
        }
        
        # Base64 encoding increases size by ~33%
        limit = MODEL_LIMITS.get(model_type, 20 * 1024 * 1024)
        safe_limit = limit * 0.75  # Safety margin for base64 encoding
        
        if len(img_data) <= safe_limit:
            return img_data  # No compression needed
        
        # Only compress if necessary
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(img_data))
        
        # Calculate resize ratio to fit within limit
        resize_ratio = (safe_limit / len(img_data)) ** 0.5
        new_size = (int(img.width * resize_ratio), int(img.height * resize_ratio))
        
        logger.info(
            f"Compressing {img_name} for {model_type}: {img.width}x{img.height} -> {new_size[0]}x{new_size[1]}",
            component="extraction_engine",
            original_size=len(img_data),
            target_size=safe_limit,
            model=model_type
        )
        
        # Resize with high quality
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img_resized.save(output, format='JPEG', quality=90, optimize=True)
        
        return output.getvalue()
    
    async def _execute_with_claude_model(self, prompt: str, images: Dict[str, bytes], output_schema: Any, api_model: str, agent_id: str = None) -> tuple[Any, float]:
        """Execute with specific Claude model"""
        return await self._execute_with_claude_internal(prompt, images, output_schema, api_model, agent_id)
    
    async def _execute_with_gpt4o_model(self, prompt: str, images: Dict[str, bytes], output_schema: Any, api_model: str, agent_id: str = None) -> tuple[Any, float]:
        """Execute with specific GPT-4 model"""
        return await self._execute_with_gpt4o_internal(prompt, images, output_schema, api_model, agent_id)
    
    async def _execute_with_gemini_model(self, prompt: str, images: Dict[str, bytes], output_schema: Any, api_model: str, agent_id: str = None) -> tuple[Any, float]:
        """Execute with specific Gemini model"""
        # Recreate Gemini model with specific model name
        generation_config = genai.types.GenerationConfig(
            temperature=self.temperature,
            top_p=1,
            top_k=1,
            max_output_tokens=8000,
        )
        self.gemini_model = genai.GenerativeModel(api_model, generation_config=generation_config)
        return await self._execute_with_gemini(prompt, images, output_schema, agent_id)
    
    @with_retry(RetryConfig(max_retries=2, base_delay=1.0))
    async def _execute_with_claude(self, prompt: str, images: Dict[str, bytes], output_schema: Any, agent_id: str = None) -> tuple[Any, float]:
        """Execute with default Claude model"""
        return await self._execute_with_claude_internal(prompt, images, output_schema, "claude-3-5-sonnet-20241022", agent_id)
    
    async def _execute_with_claude_internal(self, prompt: str, images: Dict[str, bytes], output_schema: Any, api_model: str, agent_id: str = None) -> tuple[Any, float]:
        """Execute extraction step with Claude"""
        
        # Use primary image or first available
        if "overview" in images:
            image_data = images["overview"]
            image_type = "overview"
        else:
            image_data = list(images.values())[0]
            image_type = list(images.keys())[0]
        
        logger.debug(
            f"Executing Claude step with {image_type} image",
            component="extraction_engine",
            agent_id=agent_id,
            model="claude-3-sonnet",
            image_type=image_type
        )
        
        try:
            start_time = time.time()
            
            # Prepare messages with image
            content = [{"type": "text", "text": prompt}]
            
            # Add multiple images if available
            for img_name, img_data in images.items():
                # Compress only for Claude if needed
                compressed_img = self._compress_image_for_model(img_data, 'claude', img_name)
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.b64encode(compressed_img).decode()
                    }
                })
                # For now, limit to 2 images to manage costs
                if len(content) >= 3:  # 1 text + 2 images
                    break
            
            messages = [{"role": "user", "content": content}]
            
            # Check if output_schema is a Pydantic model class (user-defined)
            if isinstance(output_schema, type) and issubclass(output_schema, BaseModel):
                # Dynamic model from user's field definitions
                logger.info(
                    f"Using dynamic Pydantic model: {output_schema.__name__}",
                    component="extraction_engine",
                    model_id=api_model
                )
                
                # Try instructor first, fall back to JSON mode if tool_use error
                try:
                    response = self.anthropic_client.messages.create(
                        model=api_model,
                        max_tokens=4096,  # Claude limit
                        temperature=self.temperature,
                        messages=messages,
                        response_model=output_schema
                    )
                except Exception as e:
                    error_msg = str(e)
                    if "tool_use" in error_msg or "tool_result" in error_msg:
                        logger.warning(
                            f"Instructor tool_use error with dynamic model, falling back to JSON mode",
                            component="extraction_engine",
                            error=error_msg[:200],
                            model_name=output_schema.__name__
                        )
                        
                        # Fall back to raw Claude with JSON parsing
                        raw_client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
                        
                        # Prepare JSON schema instruction
                        schema_json = output_schema.model_json_schema()
                        json_instruction = f"\n\nIMPORTANT: You must return your response as valid JSON that matches this exact schema:\n```json\n{json.dumps(schema_json, indent=2)}\n```"
                        
                        # Add JSON instruction to prompt  
                        json_messages = []
                        for msg in messages:
                            if msg["role"] == "user":
                                new_content = []
                                for item in msg["content"]:
                                    if item["type"] == "text":
                                        # Also add examples of the expected structure for clarity
                                        example_instruction = ""
                                        # Get field names from the schema to show correct structure
                                        schema_properties = schema_json.get('properties', {})
                                        if schema_properties:
                                            # Show example with actual fields from the dynamic model
                                            field_examples = {}
                                            for field_name, field_info in schema_properties.items():
                                                field_type = field_info.get('type', 'string')
                                                if field_type == 'string':
                                                    field_examples[field_name] = "example_value"
                                                elif field_type == 'integer':
                                                    field_examples[field_name] = 1
                                                elif field_type == 'number' or field_type == 'float':
                                                    field_examples[field_name] = 1.0
                                                elif field_type == 'boolean':
                                                    field_examples[field_name] = True
                                                elif field_type == 'array':
                                                    field_examples[field_name] = []
                                            # Check if this is a products extraction (has common product fields)
                                            if all(field in schema_properties for field in ['brand', 'name', 'shelf', 'position']):
                                                # This is products extraction - show array format
                                                example_instruction = f"\n\nIMPORTANT: For products extraction, return a JSON object with a 'products' array:\n```json\n{{\n  \"products\": [\n    {json.dumps(field_examples, indent=6)[:-1]},\n    {json.dumps(field_examples, indent=6)[:-1]},\n    ...\n  ]\n}}\n```"
                                            else:
                                                # Other extractions - show flat structure
                                                example_instruction = f"\n\nIMPORTANT: Return a JSON object with these exact fields at the root level:\n```json\n{json.dumps(field_examples, indent=2)}\n```"
                                        new_content.append({
                                            "type": "text",
                                            "text": item["text"] + json_instruction + example_instruction
                                        })
                                    else:
                                        new_content.append(item)
                                json_messages.append({"role": "user", "content": new_content})
                            else:
                                json_messages.append(msg)
                        
                        raw_response = raw_client.messages.create(
                            model=api_model,
                            max_tokens=4096,
                            temperature=self.temperature,
                            messages=json_messages
                        )
                        
                        # Parse JSON response
                        response_text = raw_response.content[0].text
                        
                        # Extract JSON from response (handle markdown code blocks)
                        if "```json" in response_text:
                            json_start = response_text.find("```json") + 7
                            json_end = response_text.find("```", json_start)
                            response_text = response_text[json_start:json_end].strip()
                        elif "```" in response_text:
                            json_start = response_text.find("```") + 3
                            json_end = response_text.find("```", json_start)
                            response_text = response_text[json_start:json_end].strip()
                        
                        # Parse and validate with the dynamic model
                        try:
                            json_data = json.loads(response_text)
                            
                            # Handle common response structure mismatches
                            # If the model returns a wrapper object, try to unwrap it
                            response = None  # Initialize response
                            
                            if isinstance(json_data, dict):
                                # Check if there's a single key that contains the actual data
                                keys = list(json_data.keys())
                                if len(keys) == 1 and isinstance(json_data[keys[0]], (list, dict)):
                                    # For products stage, if the response is {'products': [...]}
                                    # but we expect fields at root level, handle it specially
                                    if keys[0] == 'products' and isinstance(json_data['products'], list):
                                        # Special handling for products stage
                                        # The dynamic model expects individual product fields, but we got an array
                                        # Return the array directly for the calling code to handle
                                        logger.info(
                                            f"Claude returned array of {len(json_data['products'])} products, "
                                            f"returning list directly for products stage",
                                            component="extraction_engine"
                                        )
                                        # Return the list of products directly
                                        products_list = []
                                        for prod in json_data['products']:
                                            try:
                                                # Validate each product against the schema
                                                validated_prod = output_schema(**prod)
                                                products_list.append(validated_prod)
                                            except ValidationError as e:
                                                logger.warning(f"Skipping invalid product: {e}", component="extraction_engine")
                                        response = products_list  # Return list directly, not wrapped
                                        # Skip normal validation since we already validated each item
                                    elif isinstance(json_data[keys[0]], dict):
                                        # Try unwrapping single-key wrapper
                                        logger.info(
                                            f"Unwrapping single-key JSON response: {keys[0]}",
                                            component="extraction_engine"
                                        )
                                        json_data = json_data[keys[0]]
                            
                            # Only parse if we haven't already handled the response
                            if response is None:
                                response = output_schema(**json_data)
                                logger.info(
                                    f"Successfully parsed JSON response into {output_schema.__name__}",
                                    component="extraction_engine"
                                )
                        except (json.JSONDecodeError, ValidationError) as parse_error:
                            logger.error(
                                f"Failed to parse JSON response: {parse_error}",
                                component="extraction_engine",
                                response_preview=response_text[:500],
                                schema_name=output_schema.__name__,
                                json_structure=str(json_data)[:200] if 'json_data' in locals() else 'N/A'
                            )
                            # Return empty result matching the expected structure instead of raising
                            # This prevents stalling on parse errors
                            logger.warning(
                                f"Returning empty {output_schema.__name__} due to parse error",
                                component="extraction_engine"
                            )
                            try:
                                # Create empty instance with default values
                                response = output_schema()
                            except:
                                # If that fails, return empty dict/list based on expected type
                                if 'products' in output_schema.__name__.lower():
                                    response = []
                                else:
                                    response = {}
                    else:
                        # Re-raise non-tool_use errors
                        raise
            elif output_schema == "ShelfStructure":
                response = self.anthropic_client.messages.create(
                    model=api_model,
                    max_tokens=4000,
                    temperature=self.temperature,
                    messages=messages,
                    response_model=ShelfStructure
                )
            elif output_schema == "List[ProductExtraction]":
                response = self.anthropic_client.messages.create(
                    model=api_model,
                    max_tokens=4096,  # Claude limit
                    temperature=self.temperature,
                    messages=messages,
                    response_model=List[ProductExtraction]
                )
            elif output_schema == "CompleteShelfExtraction":
                response = self.anthropic_client.messages.create(
                    model=api_model,
                    max_tokens=4096,  # Claude limit
                    temperature=self.temperature,
                    messages=messages,
                    response_model=CompleteShelfExtraction
                )
            else:
                # Generic text response - create a raw Anthropic client
                # Instructor wrapper requires response_model, so we bypass it
                raw_client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
                raw_response = raw_client.messages.create(
                    model=api_model,
                    max_tokens=4000,
                    temperature=self.temperature,
                    messages=messages
                )
                response_text = raw_response.content[0].text
                
                # Try to parse as JSON for Dict[str, Any] output schema
                if output_schema == "Dict[str, Any]":
                    try:
                        response = json.loads(response_text)
                    except json.JSONDecodeError:
                        # If not valid JSON, return as dict with 'result' key
                        response = {'result': response_text}
                else:
                    response = response_text
            
            # Estimate API cost (Claude 3 Sonnet pricing)
            duration = time.time() - start_time
            estimated_cost = self._estimate_claude_cost(len(prompt), 4000, len(images))
            
            # Log model usage with the actual model name
            await self._log_model_usage(
                model_id=api_model,
                model_provider="anthropic",
                prompt_length=len(prompt),
                completion_length=4000,
                duration=duration,
                cost=estimated_cost,
                stage="products",
                agent_id=agent_id
            )
            
            logger.debug(
                f"Claude execution completed in {duration:.2f}s, cost: £{estimated_cost:.3f}",
                component="extraction_engine",
                agent_id=agent_id,
                duration=duration,
                cost=estimated_cost
            )
            
            return response, estimated_cost
            
        except Exception as e:
            logger.error(
                f"Claude execution failed: {e}",
                component="extraction_engine",
                agent_id=agent_id,
                model="claude-3-sonnet",
                error=str(e)
            )
            raise
    
    @with_retry(RetryConfig(max_retries=2, base_delay=1.0))
    async def _execute_with_gpt4o(self, prompt: str, images: Dict[str, bytes], output_schema: Any, agent_id: str = None) -> tuple[Any, float]:
        """Execute with default GPT-4o model"""
        return await self._execute_with_gpt4o_internal(prompt, images, output_schema, "gpt-4o-2024-11-20", agent_id)
    
    async def _execute_with_gpt4o_internal(self, prompt: str, images: Dict[str, bytes], output_schema: Any, api_model: str, agent_id: str = None) -> tuple[Any, float]:
        """Execute extraction step with GPT-4o"""
        
        # Use primary image or first available
        if "overview" in images:
            image_data = images["overview"]
            image_type = "overview"
        else:
            image_data = list(images.values())[0]
            image_type = list(images.keys())[0]
        
        logger.debug(
            f"Executing GPT-4o step with {image_type} image, output_schema={output_schema}",
            component="extraction_engine",
            agent_id=agent_id,
            model=api_model,
            image_type=image_type,
            output_schema=output_schema,
            output_schema_type=type(output_schema).__name__
        )
        
        try:
            start_time = time.time()
            
            # Prepare content with multiple images
            content = [{"type": "text", "text": prompt}]
            
            for img_name, img_data in images.items():
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64.b64encode(img_data).decode()}",
                        "detail": "high"
                    }
                })
                # Limit to 2 images for cost management
                if len(content) >= 3:  # 1 text + 2 images
                    break
            
            messages = [{"role": "user", "content": content}]
            
            # Add detailed logging for debugging
            logger.info(
                f"Processing GPT-4o request with output_schema debug info",
                component="extraction_engine",
                agent_id=agent_id,
                output_schema_value=str(output_schema),
                output_schema_type=type(output_schema).__name__,
                output_schema_repr=repr(output_schema),
                openai_client_type=type(self.openai_client).__name__
            )
            
            # Check if output_schema is a Pydantic model class (user-defined)
            if isinstance(output_schema, type) and issubclass(output_schema, BaseModel):
                # Dynamic model from user's field definitions
                logger.info(
                    f"Using dynamic Pydantic model: {output_schema.__name__}",
                    component="extraction_engine",
                    model_id=api_model
                )
                response = self.openai_client.chat.completions.create(
                    model=api_model,
                    messages=messages,
                    response_model=output_schema,
                    max_tokens=4096,  # Claude limit
                    temperature=self.temperature
                )
            elif output_schema == "ShelfStructure":
                logger.info("Using ShelfStructure schema", component="extraction_engine", agent_id=agent_id)
                response = self.openai_client.chat.completions.create(
                    model=api_model,
                    messages=messages,
                    response_model=ShelfStructure,
                    max_tokens=4000,
                    temperature=self.temperature
                )
            elif output_schema == "List[ProductExtraction]":
                logger.info("Using List[ProductExtraction] schema", component="extraction_engine", agent_id=agent_id)
                response = self.openai_client.chat.completions.create(
                    model=api_model,
                    messages=messages,
                    response_model=List[ProductExtraction],
                    max_tokens=4096,  # Claude limit
                    temperature=self.temperature
                )
            elif output_schema == "CompleteShelfExtraction":
                logger.info("Using CompleteShelfExtraction schema", component="extraction_engine", agent_id=agent_id)
                response = self.openai_client.chat.completions.create(
                    model=api_model,
                    messages=messages,
                    response_model=CompleteShelfExtraction,
                    max_tokens=4096,  # Claude limit
                    temperature=self.temperature
                )
            else:
                # Generic response - create a raw OpenAI client for text responses
                # Instructor wrapper requires response_model, so we bypass it
                logger.info(
                    f"Using raw OpenAI client for output_schema: {output_schema} (type: {type(output_schema).__name__})",
                    component="extraction_engine",
                    agent_id=agent_id
                )
                
                raw_client = openai.OpenAI(api_key=self.config.openai_api_key)
                raw_response = raw_client.chat.completions.create(
                    model=api_model,
                    messages=messages,
                    max_tokens=4000,
                    temperature=self.temperature
                )
                response_text = raw_response.choices[0].message.content
                
                # Try to parse as JSON for Dict[str, Any] output schema
                if output_schema == "Dict[str, Any]":
                    try:
                        response = json.loads(response_text)
                    except json.JSONDecodeError:
                        # If not valid JSON, return as dict with 'result' key
                        response = {'result': response_text}
                else:
                    response = response_text
            
            # Estimate API cost and tokens
            duration = time.time() - start_time
            estimated_cost = self._estimate_gpt4o_cost(len(prompt), 4000, len(images))
            
            # Log model usage with the actual model name
            await self._log_model_usage(
                model_id=api_model,
                model_provider="openai",
                prompt_length=len(prompt),
                completion_length=4000,
                duration=duration,
                cost=estimated_cost,
                stage="products",
                agent_id=agent_id
            )
            
            logger.debug(
                f"GPT-4o execution completed in {duration:.2f}s, cost: £{estimated_cost:.3f}",
                component="extraction_engine",
                agent_id=agent_id,
                duration=duration,
                cost=estimated_cost
            )
            
            return response, estimated_cost
            
        except Exception as e:
            logger.error(
                f"GPT-4o execution failed: {e}",
                component="extraction_engine",
                agent_id=agent_id,
                model="gpt-4o",
                error=str(e)
            )
            raise
    
    @with_retry(RetryConfig(max_retries=2, base_delay=1.0))
    async def _execute_with_gemini(self, prompt: str, images: Dict[str, bytes], output_schema: Any, agent_id: str = None) -> tuple[Any, float]:
        """Execute extraction step with Gemini"""
        
        # Use primary image or first available
        if "overview" in images:
            image_data = images["overview"]
            image_type = "overview"
        else:
            image_data = list(images.values())[0]
            image_type = list(images.keys())[0]
        
        logger.debug(
            f"Executing Gemini step with {image_type} image",
            component="extraction_engine",
            agent_id=agent_id,
            model="gemini-2.0-flash",
            image_type=image_type
        )
        
        try:
            start_time = time.time()
            
            # Prepare content (Gemini currently supports single image best)
            content = [prompt, {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_data).decode()
            }]
            
            response = self.gemini_model.generate_content(content)
            
            # Parse Gemini response based on expected schema
            if output_schema == "Dict[str, float]":
                # Parse price extraction from Gemini text response
                parsed_response = self._parse_gemini_price_response(response.text)
            else:
                parsed_response = response.text
            
            # Estimate API cost (Gemini is typically cheaper)
            duration = time.time() - start_time
            estimated_cost = self._estimate_gemini_cost(len(prompt), len(response.text))
            
            # Log model usage
            await self._log_model_usage(
                model_id=self.gemini_model.model_name,
                model_provider="google",
                prompt_length=len(prompt),
                completion_length=len(response.text),
                duration=duration,
                cost=estimated_cost,
                stage="products",
                agent_id=agent_id
            )
            
            logger.debug(
                f"Gemini execution completed in {duration:.2f}s, cost: £{estimated_cost:.3f}",
                component="extraction_engine",
                agent_id=agent_id,
                duration=duration,
                cost=estimated_cost
            )
            
            return parsed_response, estimated_cost
                
        except Exception as e:
            logger.error(
                f"Gemini execution failed: {e}",
                component="extraction_engine",
                agent_id=agent_id,
                model="gemini-2.0-flash",
                error=str(e)
            )
            raise
    
    def _parse_gemini_price_response(self, response_text: str) -> Dict[str, float]:
        """Parse Gemini's text response into structured price data"""
        prices = {}
        
        # Simple parsing logic - can be enhanced
        lines = response_text.strip().split('\n')
        for line in lines:
            if '£' in line or '$' in line:
                # Extract product name and price
                parts = line.split(':')
                if len(parts) == 2:
                    product = parts[0].strip()
                    price_str = parts[1].strip()
                    # Extract numeric value
                    import re
                    price_match = re.search(r'[\d.]+', price_str)
                    if price_match:
                        prices[product] = float(price_match.group())
        
        return prices
    
    def _estimate_claude_cost(self, input_chars: int, output_tokens: int, image_count: int = 1) -> float:
        """Estimate Claude API cost with image pricing"""
        # Claude 3 Sonnet pricing
        input_cost_per_1k = 0.003
        output_cost_per_1k = 0.015
        image_cost = 0.004  # Per image
        
        input_tokens_est = input_chars // 4  # Rough token estimate
        output_tokens_est = output_tokens // 4
        
        cost = (input_tokens_est / 1000 * input_cost_per_1k + 
                output_tokens_est / 1000 * output_cost_per_1k +
                image_count * image_cost)
        
        return round(cost, 4)
    
    def _estimate_gpt4o_cost(self, input_chars: int, output_tokens: int, image_count: int = 1) -> float:
        """Estimate GPT-4o API cost with image pricing"""
        # GPT-4o pricing
        input_cost_per_1k = 0.005
        output_cost_per_1k = 0.015
        image_cost = 0.006  # Per image (high detail)
        
        input_tokens_est = input_chars // 4
        output_tokens_est = output_tokens // 4
        
        cost = (input_tokens_est / 1000 * input_cost_per_1k + 
                output_tokens_est / 1000 * output_cost_per_1k +
                image_count * image_cost)
        
        return round(cost, 4)
    
    def _estimate_gemini_cost(self, input_chars: int, output_chars: int) -> float:
        """Estimate Gemini API cost"""
        # Gemini is typically cheaper
        total_chars = input_chars + output_chars
        cost_per_1k_chars = 0.00025
        
        cost = (total_chars / 1000) * cost_per_1k_chars
        
        return round(cost, 4)
    
    async def _construct_complete_extraction(self,
                                           upload_id: str,
                                           step_outputs: Dict,
                                           images: Dict[str, bytes],
                                           models_used: set,
                                           api_costs: List[float],
                                           start_time: float,
                                           agent_id: str = None) -> CompleteShelfExtraction:
        """Construct CompleteShelfExtraction from step outputs"""
        
        # Get structure and products from steps
        structure = None
        products = []
        
        for step_id, output in step_outputs.items():
            if isinstance(output, ShelfStructure):
                structure = output
            elif isinstance(output, list) and output and isinstance(output[0], ProductExtraction):
                products = output
        
        # Calculate metrics
        accuracy_score = self._calculate_accuracy_score(products)
        overall_confidence = self._calculate_overall_confidence(products)
        
        # Create extraction result
        extraction = CompleteShelfExtraction(
            upload_id=upload_id,
            media_file_ids=list(images.keys()),
            shelf_structure=structure or ShelfStructure(
                picture_height=1000,
                picture_width=1500,
                number_of_shelves=3,
                estimated_width_meters=2.0,
                estimated_height_meters=1.5,
                shelf_coordinates=[],
                structure_confidence=ConfidenceLevel.LOW
            ),
            products=products,
            total_products_detected=len(products),
            non_product_elements=NonProductElements(),
            overall_confidence=overall_confidence,
            requires_human_review=accuracy_score < 0.85,
            accuracy_score=accuracy_score,
            extraction_duration_seconds=time.time() - start_time,
            models_used=list(models_used),
            api_cost_estimate=sum(api_costs),
            validation_summary=self._get_validation_summary(products)
        )
        
        return extraction
    
    def _calculate_accuracy_score(self, products: List[ProductExtraction]) -> float:
        """Calculate overall accuracy score"""
        if not products:
            return 0.0
        
        # Handle both ProductExtraction objects and dynamic models
        total_confidence = sum(
            getattr(p, 'extraction_confidence', 0.85) if hasattr(p, '__dict__') 
            else p.get('extraction_confidence', 0.85) if isinstance(p, dict)
            else 0.85
            for p in products
        )
        return total_confidence / len(products)
    
    def _calculate_overall_confidence(self, products: List[ProductExtraction]) -> ConfidenceLevel:
        """Calculate overall confidence level"""
        avg_confidence = self._calculate_accuracy_score(products)
        
        if avg_confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _get_validation_summary(self, products: List[ProductExtraction]) -> Dict[str, int]:
        """Get validation summary from products"""
        summary = {
            'total_products': len(products),
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'validation_flags': 0
        }
        
        for product in products:
            # Handle dynamic models that may not have confidence_category
            if hasattr(product, 'confidence_category'):
                if product.confidence_category == ConfidenceLevel.VERY_HIGH:
                    summary['high_confidence'] += 1
                elif product.confidence_category in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]:
                    summary['medium_confidence'] += 1
                else:
                    summary['low_confidence'] += 1
            else:
                # Default to medium confidence for dynamic models
                summary['medium_confidence'] += 1
            
            # Handle validation_flags
            if hasattr(product, 'validation_flags'):
                summary['validation_flags'] += len(product.validation_flags)
            elif isinstance(product, dict) and 'validation_flags' in product:
                summary['validation_flags'] += len(product.get('validation_flags', []))
        
        return summary 