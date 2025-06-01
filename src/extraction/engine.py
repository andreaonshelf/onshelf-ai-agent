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
from pydantic import BaseModel

from ..config import SystemConfig
from ..utils import (
    logger, CostTracker, CostLimitExceededException, ErrorHandler,
    with_retry, RetryConfig, GracefulDegradation, MultiImageCoordinator
)
from .models import (
    ExtractionStep, AIModelType, ShelfStructure, ProductExtraction,
    CompleteShelfExtraction, ConfidenceLevel, ValidationFlag, NonProductElements
)
from .prompts import PromptTemplates


class ModularExtractionEngine:
    """Extraction system with sequential, modular steps that build on each other"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
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
            models_configured=len(self.config.models)
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
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
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
    
    async def _execute_with_fallback(self, primary_model: AIModelType, prompt: str, images: Dict[str, bytes], output_schema: str, agent_id: str = None) -> tuple[Any, float]:
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
    
    @with_retry(RetryConfig(max_retries=2, base_delay=1.0))
    async def _execute_with_claude(self, prompt: str, images: Dict[str, bytes], output_schema: str, agent_id: str = None) -> tuple[Any, float]:
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
            
            # Execute based on schema
            if output_schema == "ShelfStructure":
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=messages,
                    response_model=ShelfStructure,
                    temperature=self.config.model_temperature
                )
            elif output_schema == "List[ProductExtraction]":
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=6000,
                    messages=messages,
                    response_model=List[ProductExtraction],
                    temperature=self.config.model_temperature
                )
            elif output_schema == "CompleteShelfExtraction":
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=8000,
                    messages=messages,
                    response_model=CompleteShelfExtraction,
                    temperature=self.config.model_temperature
                )
            else:
                # Generic text response
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=messages,
                    temperature=self.config.model_temperature
                )
            
            # Estimate API cost (Claude 3 Sonnet pricing)
            duration = time.time() - start_time
            estimated_cost = self._estimate_claude_cost(len(prompt), 4000, len(images))
            
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
    async def _execute_with_gpt4o(self, prompt: str, images: Dict[str, bytes], output_schema: str, agent_id: str = None) -> tuple[Any, float]:
        """Execute extraction step with GPT-4o"""
        
        # Use primary image or first available
        if "overview" in images:
            image_data = images["overview"]
            image_type = "overview"
        else:
            image_data = list(images.values())[0]
            image_type = list(images.keys())[0]
        
        logger.debug(
            f"Executing GPT-4o step with {image_type} image",
            component="extraction_engine",
            agent_id=agent_id,
            model="gpt-4o",
            image_type=image_type
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
            
            if output_schema == "List[ProductExtraction]":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages,
                    response_model=List[ProductExtraction],
                    max_tokens=6000,
                    temperature=self.config.model_temperature
                )
            elif output_schema == "CompleteShelfExtraction":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages,
                    response_model=CompleteShelfExtraction,
                    max_tokens=8000,
                    temperature=self.config.model_temperature
                )
            else:
                # Generic response
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages,
                    max_tokens=4000,
                    temperature=self.config.model_temperature
                )
            
            # Estimate API cost
            duration = time.time() - start_time
            estimated_cost = self._estimate_gpt4o_cost(len(prompt), 4000, len(images))
            
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
    async def _execute_with_gemini(self, prompt: str, images: Dict[str, bytes], output_schema: str, agent_id: str = None) -> tuple[Any, float]:
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
        
        total_confidence = sum(p.extraction_confidence for p in products)
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
            if product.confidence_category == ConfidenceLevel.VERY_HIGH:
                summary['high_confidence'] += 1
            elif product.confidence_category in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]:
                summary['medium_confidence'] += 1
            else:
                summary['low_confidence'] += 1
            
            summary['validation_flags'] += len(product.validation_flags)
        
        return summary 