"""
Extraction Orchestrator
Manages cumulative agent learning and extraction strategy
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

from ..config import SystemConfig
from ..models.extraction_models import (
    ExtractionResult, CumulativeExtractionContext, ValidationFlag
)
from ..extraction.models import (
    ProductExtraction, Position, SectionCoordinates, Quantity, 
    AIModelType, ConfidenceLevel
)
# ShelfStructure removed - using dynamic models from database
from ..utils import logger
from ..utils.extraction_analytics import get_extraction_analytics


class ExtractionOrchestrator:
    """Orchestrates extraction with cumulative learning between agents"""
    
    def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None, 
                 extraction_run_id: Optional[str] = None):
        self.config = config
        self.queue_item_id = queue_item_id
        self.extraction_run_id = extraction_run_id
        
        # Initialize model configuration defaults
        self.model_config = {}
        self.temperature = 0.7
        self.orchestrator_model = 'claude-4-opus'
        self.orchestrator_prompt = ''
        self.stage_models = {}
        
        # Load model configuration if queue item provided
        if queue_item_id:
            self._load_model_config()
        
        # Initialize real extraction engine with temperature
        from ..extraction.engine import ModularExtractionEngine
        self.extraction_engine = ModularExtractionEngine(config, temperature=self.temperature)
        
        # Pass queue context to engine if available
        if queue_item_id:
            self.extraction_engine.queue_item_id = queue_item_id
        
        # Initialize analytics if extraction_run_id provided
        self.analytics = None
        if extraction_run_id and queue_item_id:
            from .analytics_integration import OrchestrationAnalytics
            self.analytics = OrchestrationAnalytics(extraction_run_id, queue_item_id)
            logger.info(
                "Analytics tracking initialized",
                component="extraction_orchestrator",
                run_id=extraction_run_id,
                queue_id=queue_item_id
            )
        
        logger.info(
            "Extraction Orchestrator initialized with real extraction engine",
            component="extraction_orchestrator",
            has_model_config=bool(self.model_config)
        )
    
    async def extract_with_cumulative_learning(self, 
                                             image: bytes,
                                             iteration: int = 1,
                                             previous_attempts: List[ExtractionResult] = None,
                                             focus_areas: List[Dict] = None,
                                             locked_positions: List[Dict] = None,
                                             agent_id: str = None,
                                             extraction_run_id: str = None) -> ExtractionResult:
        """Execute extraction with cumulative learning from previous attempts"""
        
        logger.info(
            f"Starting cumulative extraction - Iteration {iteration}",
            component="extraction_orchestrator",
            agent_id=agent_id,
            iteration=iteration,
            has_previous=previous_attempts is not None
        )
        
        # Pass extraction run ID to engine if provided
        if extraction_run_id and hasattr(self.extraction_engine, 'extraction_run_id'):
            self.extraction_engine.extraction_run_id = extraction_run_id
        
        # Phase 0: Structure analysis (only on first iteration)
        if iteration == 1:
            # Use the stage-based structure extraction with UI prompts
            model_id = self._select_model_for_agent(1, None, 'structure')
            structure = await self._execute_structure_stage(
                images={'main': image},
                model_id=model_id,
                previous_attempts=[],
                agent_id=agent_id
            )
            previous_attempts = []
        else:
            structure = previous_attempts[0].structure  # Use structure from first attempt
        
        # Phase 1: Design extraction strategy with cumulative context
        extraction_context = self._build_cumulative_context(
            structure=structure,
            previous_attempts=previous_attempts,
            focus_areas=focus_areas,
            locked_positions=locked_positions,
            iteration=iteration
        )
        
        # Phase 2: Execute agent with cumulative learning
        current_agent_result = await self._execute_agent_with_context(
            image=image,
            agent_number=iteration,
            context=extraction_context,
            agent_id=agent_id
        )
        
        # Phase 3: Analyze improvements
        if previous_attempts:
            improvements = self._analyze_improvements(current_agent_result, previous_attempts[-1])
            current_agent_result.improvements_from_previous = improvements
        
        logger.info(
            f"Cumulative extraction complete - Agent {iteration}",
            component="extraction_orchestrator",
            agent_id=agent_id,
            products_found=current_agent_result.total_products,
            confidence=current_agent_result.overall_confidence.value
        )
        
        return current_agent_result
    
    def _build_cumulative_context(self, 
                                structure: Any,
                                previous_attempts: List[ExtractionResult],
                                focus_areas: Optional[List[Dict]],
                                locked_positions: Optional[List[Dict]],
                                iteration: int) -> CumulativeExtractionContext:
        """Build context that includes learning from ALL previous agents"""
        
        context = CumulativeExtractionContext(
            structure=structure,
            iteration=iteration,
            successful_extractions=[],
            failed_extractions=[],
            confidence_trends={},
            locked_positions=locked_positions or [],
            focus_areas=focus_areas or []
        )
        
        # Analyze all previous attempts for cumulative learning
        for attempt_num, attempt in enumerate(previous_attempts, 1):
            for product in attempt.products:
                position_key = f"shelf_{product.section.horizontal}_pos_{product.position.l_position_on_section}"
                
                if product.extraction_confidence >= 0.95:
                    # High confidence - add to successful extractions
                    context.successful_extractions.append({
                        "position": position_key,
                        "data": product.dict(),
                        "source_agent": attempt_num,
                        "confidence": product.extraction_confidence
                    })
                elif product.extraction_confidence < 0.75:
                    # Low confidence - add to failed extractions for focus
                    context.failed_extractions.append({
                        "position": position_key,
                        "issues": [flag.value for flag in product.validation_flags],
                        "source_agent": attempt_num,
                        "confidence": product.extraction_confidence
                    })
                
                # Track confidence trends
                if position_key not in context.confidence_trends:
                    context.confidence_trends[position_key] = []
                context.confidence_trends[position_key].append({
                    "agent": attempt_num,
                    "confidence": product.extraction_confidence
                })
        
        return context
    
    async def _execute_agent_with_context(self, 
                                        image: bytes,
                                        agent_number: int,
                                        context: CumulativeExtractionContext,
                                        agent_id: str) -> ExtractionResult:
        """Execute agent with full cumulative context"""
        
        # Build agent-specific prompt with cumulative learning
        prompt = self._build_cumulative_prompt(agent_number, context)
        
        # Select appropriate model for agent
        model = self._select_model_for_agent(agent_number, context, stage="products")
        
        logger.info(
            f"Executing Agent {agent_number} with {model}",
            component="extraction_orchestrator",
            agent_id=agent_id,
            agent_number=agent_number,
            model=model,
            locked_positions=len(context.locked_positions),
            focus_areas=len(context.focus_areas)
        )
        
        # Execute REAL extraction using the extraction engine
        start_time = datetime.utcnow()
        
        # Prepare images dict for extraction engine
        images = {"main": image}
        
        # Use shelf-by-shelf extraction for better accuracy
        products = await self._execute_shelf_by_shelf_extraction(
            image=image,
            context=context,
            model=model,
            agent_number=agent_number,
            agent_id=agent_id
        )
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Build result
        result = ExtractionResult(
            agent_number=agent_number,
            structure=context.structure,
            products=products,
            total_products=len(products),
            overall_confidence=self._calculate_overall_confidence(products),
            accuracy_estimate=self._estimate_accuracy(products),
            extraction_duration_seconds=duration,
            model_used=model,
            api_cost_estimate=0.05 * agent_number  # Mock cost
        )
        
        return result
    
    def _build_cumulative_prompt(self, agent_number: int, context: CumulativeExtractionContext) -> str:
        """Build prompt that includes learning from all previous agents"""
        
        # For shelf-by-shelf extraction, we'll modify this to focus on specific shelves
        # This is a placeholder - the actual implementation will be in _execute_shelf_by_shelf
        base_prompt = f"""
        You are Agent {agent_number} in a cumulative extraction pipeline.
        
        SHELF STRUCTURE:
        - {context.structure.shelf_count} shelves (bottom=1, top={context.structure.shelf_count})
        - Width: {context.structure.estimated_width_meters}m
        - Expected products per shelf: ~{context.structure.products_per_shelf_estimate}
        """
        
        if agent_number == 1:
            # First agent: Clean slate extraction
            return base_prompt + """
            TASK: Perform initial product extraction across all shelves.
            Extract systematically shelf by shelf, left to right.
            Focus on accurate shelf positioning and product identification.
            """
        
        else:
            # Subsequent agents: Build on previous work
            successful_positions = [item["position"] for item in context.successful_extractions]
            failed_positions = [item["position"] for item in context.failed_extractions]
            
            cumulative_prompt = base_prompt + f"""
            CUMULATIVE LEARNING CONTEXT:
            You are building on the work of {agent_number - 1} previous agents.
            
            HIGH CONFIDENCE POSITIONS (preserve these exactly):
            {self._format_successful_positions(context.successful_extractions)}
            
            FOCUS AREAS (improve these):
            {self._format_failed_positions(context.failed_extractions)}
            
            CONFIDENCE TRENDS:
            {self._format_confidence_trends(context.confidence_trends)}
            
            TASK: 
            1. Keep all high-confidence extractions exactly as they are
            2. Focus improvement efforts on low-confidence areas
            3. Look for products that previous agents may have missed
            4. Provide enhanced extraction for focus areas
            
            Build upon previous work - don't start from scratch.
            """
            
            return cumulative_prompt
    
    def _format_successful_positions(self, successful_extractions: List[Dict]) -> str:
        """Format successful extractions for prompt"""
        if not successful_extractions:
            return "None yet - this is the first iteration."
        
        formatted = []
        for item in successful_extractions[:10]:  # Limit to avoid prompt overflow
            product = item['data']
            formatted.append(
                f"- {item['position']}: {product['brand']} {product['name']} "
                f"(confidence: {item['confidence']:.2f})"
            )
        
        if len(successful_extractions) > 10:
            formatted.append(f"... and {len(successful_extractions) - 10} more high-confidence products")
        
        return "\n".join(formatted)
    
    def _format_failed_positions(self, failed_extractions: List[Dict]) -> str:
        """Format failed extractions for prompt"""
        if not failed_extractions:
            return "None - previous agents achieved high confidence everywhere."
        
        formatted = []
        for item in failed_extractions[:10]:  # Limit to avoid prompt overflow
            formatted.append(
                f"- {item['position']}: Issues: {', '.join(item['issues'])} "
                f"(confidence: {item['confidence']:.2f})"
            )
        
        if len(failed_extractions) > 10:
            formatted.append(f"... and {len(failed_extractions) - 10} more areas needing improvement")
        
        return "\n".join(formatted)
    
    def _format_confidence_trends(self, trends: Dict[str, List]) -> str:
        """Format confidence trends for prompt"""
        if not trends:
            return "No trends yet."
        
        improving = []
        declining = []
        
        for position, history in trends.items():
            if len(history) > 1:
                trend = history[-1]['confidence'] - history[0]['confidence']
                if trend > 0.1:
                    improving.append(f"{position}: {trend:+.2f}")
                elif trend < -0.1:
                    declining.append(f"{position}: {trend:+.2f}")
        
        result = []
        if improving:
            result.append(f"Improving: {', '.join(improving[:5])}")
        if declining:
            result.append(f"Declining: {', '.join(declining[:5])}")
        
        return "\n".join(result) if result else "Stable confidence across positions"
    
    def process_retry_blocks(self, prompt: str, attempt_number: int, context: dict = None) -> str:
        """Process {IF_RETRY} blocks in prompts based on attempt number and fill context variables
        
        Args:
            prompt: The prompt text containing {IF_RETRY} blocks and {VARIABLES}
            attempt_number: Current attempt number (1-based)
            context: Dictionary of variables to replace in the prompt
            
        Returns:
            Processed prompt with retry blocks included/excluded and variables filled
        """
        import re
        
        # First, process {IF_RETRY} blocks
        pattern = r'\{IF_RETRY\}(.*?)\{/IF_RETRY\}'
        
        def replace_block(match):
            # Include content only if this is a retry (attempt > 1)
            if attempt_number > 1:
                return match.group(1)
            else:
                return ''
        
        # Process all {IF_RETRY} blocks
        processed = re.sub(pattern, replace_block, prompt, flags=re.DOTALL)
        
        # Clean up any extra whitespace left from removed blocks
        processed = re.sub(r'\n\s*\n\s*\n', '\n\n', processed)
        
        # Then, fill in context variables
        if context:
            for key, value in context.items():
                # Replace {KEY} with value, handling different types
                placeholder = f"{{{key.upper()}}}"
                if placeholder in processed:
                    # Convert value to string, handling special cases
                    if isinstance(value, list):
                        # Format lists nicely
                        value_str = '\n'.join(f"- {item}" for item in value)
                    elif isinstance(value, dict):
                        # Format dicts as key: value pairs
                        value_str = '\n'.join(f"{k}: {v}" for k, v in value.items())
                    elif value is None:
                        value_str = "Not available"
                    else:
                        value_str = str(value)
                    
                    processed = processed.replace(placeholder, value_str)
        
        # Remove any unfilled variables (optional - or leave them for debugging)
        # processed = re.sub(r'\{[A-Z_]+\}', '[Missing]', processed)
        
        return processed
    
    def _load_model_config(self):
        """Load model configuration from queue item"""
        try:
            from supabase import create_client
            import os
            
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_KEY")
            )
            
            # Get both model_config and extraction_config
            result = supabase.table("ai_extraction_queue").select("model_config, extraction_config").eq("id", self.queue_item_id).single().execute()
            
            if result.data:
                # Prioritize extraction_config if it has stages (contains field definitions)
                extraction_config = result.data.get("extraction_config", {})
                model_config = result.data.get("model_config", {})
                
                # Use extraction_config if it has stages, otherwise fall back to model_config
                if extraction_config and extraction_config.get("stages"):
                    self.model_config = extraction_config
                    logger.info(
                        "Using extraction_config with field definitions",
                        component="extraction_orchestrator",
                        stage_count=len(extraction_config.get("stages", {}))
                    )
                elif model_config:
                    self.model_config = model_config
                    logger.info(
                        "Using model_config (no extraction_config with stages found)",
                        component="extraction_orchestrator"
                    )
                else:
                    self.model_config = {}
                    logger.warning(
                        "No configuration found in queue item",
                        component="extraction_orchestrator"
                    )
                
                # Extract configuration values
                self.temperature = self.model_config.get("temperature", 0.7)
                self.orchestrator_model = self.model_config.get("orchestrator_model", "claude-4-opus")
                self.orchestrator_prompt = self.model_config.get("orchestrator_prompt", "")
                self.stage_models = self.model_config.get("stage_models", {})
                
                # Load stage configurations if available
                self.stage_configs = self.model_config.get("stages", {})
                
                # Initialize stage prompts and fields from configuration
                self.stage_prompts = {}
                self.stage_fields = {}
                
                for stage_id, stage_config in self.stage_configs.items():
                    if isinstance(stage_config, dict):
                        if "prompt_text" in stage_config:
                            self.stage_prompts[stage_id] = stage_config["prompt_text"]
                        if "fields" in stage_config:
                            self.stage_fields[stage_id] = stage_config["fields"]
                            logger.info(
                                f"Loaded {len(stage_config['fields'])} fields for stage {stage_id}",
                                component="extraction_orchestrator",
                                stage=stage_id,
                                field_count=len(stage_config['fields'])
                            )
                
                logger.info(
                    "Loaded model configuration from queue item",
                    component="extraction_orchestrator",
                    queue_item_id=self.queue_item_id,
                    temperature=self.temperature,
                    orchestrator_model=self.orchestrator_model,
                    stages_loaded=list(self.stage_configs.keys()),
                    fields_loaded={k: len(v) for k, v in self.stage_fields.items()}
                )
        except Exception as e:
            logger.error(f"Failed to load model config: {e}", component="extraction_orchestrator")

    def _select_model_for_agent(self, agent_number: int, context: CumulativeExtractionContext, stage: str = "products") -> AIModelType:
        """Select appropriate model based on configuration or defaults"""
        
        # Check if we have configured models for this stage
        if stage in self.stage_models and self.stage_models[stage]:
            models = self.stage_models[stage]
            # Rotate through configured models for different agents
            model_id = models[(agent_number - 1) % len(models)]
            
            # Map frontend model IDs to AIModelType enum
            model_mapping = {
                # OpenAI models
                "gpt-4.1": AIModelType.GPT4O_LATEST,
                "gpt-4.1-mini": AIModelType.GPT4O_LATEST,
                "gpt-4.1-nano": AIModelType.GPT4O_LATEST,
                "gpt-4o": AIModelType.GPT4O_LATEST,
                "gpt-4o-mini": AIModelType.GPT4O_LATEST,
                "o3": AIModelType.GPT4O_LATEST,
                "o4-mini": AIModelType.GPT4O_LATEST,
                
                # Anthropic models
                "claude-3-5-sonnet-v2": AIModelType.CLAUDE_3_SONNET,
                "claude-3-7-sonnet": AIModelType.CLAUDE_3_SONNET,
                "claude-4-sonnet": AIModelType.CLAUDE_3_SONNET,
                "claude-4-opus": AIModelType.CLAUDE_3_SONNET,
                
                # Google models
                "gemini-2.5-flash": AIModelType.GEMINI_PRO,
                "gemini-2.5-flash-thinking": AIModelType.GEMINI_PRO,
                "gemini-2.5-pro": AIModelType.GEMINI_PRO,
            }
            
            return model_mapping.get(model_id, AIModelType.GPT4O_LATEST)
        
        # Fallback to default behavior
        if agent_number == 1:
            return AIModelType.GPT4O_LATEST  # Fast initial extraction
        elif agent_number == 2:
            return AIModelType.CLAUDE_3_SONNET  # Better reasoning for improvements
        else:
            # Use best model for final refinements
            return AIModelType.CLAUDE_3_SONNET
    
    async def _execute_shelf_by_shelf_extraction(self, 
                                               image: bytes,
                                               context: CumulativeExtractionContext,
                                               model: AIModelType,
                                               agent_number: int,
                                               agent_id: str) -> List[ProductExtraction]:
        """Execute extraction shelf by shelf for better accuracy"""
        from ..extraction.prompts import PromptTemplates
        from ..extraction.dynamic_model_builder import DynamicModelBuilder
        
        all_products = []
        prompt_templates = PromptTemplates()
        
        # Check if we have a custom prompt for the products stage
        if hasattr(self, 'stage_prompts') and 'products' in self.stage_prompts:
            shelf_prompt_template = self.stage_prompts['products']
            logger.info(
                "Using custom products prompt from configuration",
                component="extraction_orchestrator",
                prompt_length=len(shelf_prompt_template)
            )
        else:
            shelf_prompt_template = prompt_templates.get_template("shelf_by_shelf_extraction")
        
        logger.info(
            f"Starting shelf-by-shelf extraction for {context.structure.shelf_count} shelves",
            component="extraction_orchestrator",
            agent_id=agent_id,
            total_shelves=context.structure.shelf_count
        )
        
        # Extract products shelf by shelf
        for shelf_num in range(1, context.structure.shelf_count + 1):
            logger.info(
                f"Extracting shelf {shelf_num}/{context.structure.shelf_count}",
                component="extraction_orchestrator",
                agent_id=agent_id,
                shelf_number=shelf_num
            )
            
            # Process {IF_RETRY} blocks based on agent number (which serves as attempt number for products)
            # Build context for variable replacement
            retry_context = {
                'shelf_number': shelf_num,
                'total_shelves': context.structure.shelf_count
            }
            
            # Add previous extraction data if this is a retry
            if agent_number > 1:
                # Find products already extracted for this shelf
                existing_products = [p for p in context.successful_extractions 
                                   if p.get('shelf_level') == shelf_num]
                if existing_products:
                    retry_context['previous_shelf_products'] = '\n'.join(
                        f"Position {p.get('position_on_shelf')}: {p.get('brand')} {p.get('name')}"
                        for p in existing_products[:10]  # Limit to prevent overflow
                    )
                    retry_context['high_confidence_products'] = retry_context['previous_shelf_products']
                
                # Add any visual feedback
                retry_context['planogram_feedback'] = "Check edges and promotional areas for missed products"
                
                # Add alias for consistency with prompt
                retry_context['previous_extraction_data'] = retry_context.get('previous_shelf_products', 'No previous extraction data')
            
            shelf_prompt = self.process_retry_blocks(shelf_prompt_template, agent_number, retry_context)
            
            # Build shelf-specific prompt
            shelf_prompt = shelf_prompt.format(
                shelf_number=shelf_num,
                total_shelves=context.structure.shelf_count
            )
            
            # Add cumulative context for subsequent agents
            if agent_number > 1:
                # Find products already extracted for this shelf
                existing_products = [p for p in context.successful_extractions 
                                   if p.get('shelf_level') == shelf_num]
                if existing_products:
                    shelf_prompt += f"\n\nPREVIOUSLY FOUND ON THIS SHELF (keep these):\n"
                    for p in existing_products:
                        shelf_prompt += f"- Position {p.get('position_on_shelf')}: {p.get('brand')} {p.get('name')}\n"
            
            # Track iteration if analytics enabled
            iteration_id = None
            if self.analytics:
                retry_context = {
                    'shelf_number': shelf_num,
                    'agent_number': agent_number,
                    'existing_products': len([p for p in context.successful_extractions if p.get('shelf_level') == shelf_num])
                }
                
                iteration_id = await self.analytics.track_products_extraction(
                    shelf_num=shelf_num,
                    model_id=model.value if hasattr(model, 'value') else str(model),
                    model_index=agent_number - 1,
                    attempt_number=1,  # Can be enhanced to track retries
                    prompt_template=context.prompts.get('products', ''),
                    processed_prompt=shelf_prompt,
                    retry_context=retry_context
                )
            
            try:
                start_time = datetime.utcnow()
                
                # Execute extraction for this shelf
                # If we have a configured model from stage_models, use it
                if context.structure and hasattr(self, 'stage_models') and 'products' in self.stage_models:
                    models = self.stage_models['products']
                    if models:
                        # Select model based on agent number
                        model_id = models[(agent_number - 1) % len(models)]
                        # Determine output schema - use dynamic model if configured
                        output_schema = "List[ProductExtraction]"  # Default
                        
                        if hasattr(self, 'stage_fields') and 'products' in self.stage_fields:
                            fields = self.stage_fields['products']
                            if fields:
                                logger.info(
                                    f"Building dynamic model for products stage with {len(fields)} fields",
                                    component="extraction_orchestrator",
                                    field_count=len(fields),
                                    shelf_num=shelf_num
                                )
                                # Build dynamic model from configured fields
                                from typing import List
                                ProductModel = DynamicModelBuilder.build_model_from_config('product', {'fields': fields})
                                output_schema = List[ProductModel]
                        
                        shelf_result, api_cost = await self.extraction_engine.execute_with_model_id(
                            model_id=model_id,
                            prompt=shelf_prompt,
                            images={"main": image},
                            output_schema=output_schema,
                            agent_id=f"{agent_id}_shelf_{shelf_num}"
                        )
                    else:
                        # Fallback to default model but still check for dynamic schema
                        output_schema = "List[ProductExtraction]"  # Default
                        
                        if hasattr(self, 'stage_fields') and 'products' in self.stage_fields:
                            fields = self.stage_fields['products']
                            if fields:
                                from typing import List
                                ProductModel = DynamicModelBuilder.build_model_from_config('product', {'fields': fields})
                                output_schema = List[ProductModel]
                        
                        shelf_result, api_cost = await self.extraction_engine._execute_with_fallback(
                            primary_model=model,
                            prompt=shelf_prompt,
                            images={"main": image},
                            output_schema=output_schema,
                            agent_id=f"{agent_id}_shelf_{shelf_num}"
                        )
                else:
                    # Use default fallback but still check for dynamic schema
                    output_schema = "List[ProductExtraction]"  # Default
                    
                    if hasattr(self, 'stage_fields') and 'products' in self.stage_fields:
                        fields = self.stage_fields['products']
                        if fields:
                            from typing import List
                            ProductModel = DynamicModelBuilder.build_model_from_config('product', {'fields': fields})
                            output_schema = List[ProductModel]
                    
                    shelf_result, api_cost = await self.extraction_engine._execute_with_fallback(
                        primary_model=model,
                        prompt=shelf_prompt,
                        images={"main": image},
                        output_schema=output_schema,
                        agent_id=f"{agent_id}_shelf_{shelf_num}"
                    )
                
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Update analytics with results if enabled
                if self.analytics and iteration_id:
                    await self.analytics.analytics.update_iteration_result(
                        iteration_id=iteration_id,
                        extraction_result={'products': [p.dict() if hasattr(p, 'dict') else p for p in shelf_result]},
                        products_found=len(shelf_result),
                        accuracy_score=0.0,  # Can be calculated based on confidence scores
                        api_cost=api_cost,
                        tokens_used=len(shelf_prompt) // 4,  # Rough estimate
                        duration_ms=duration_ms
                    )
                
                # Convert and add products from this shelf
                shelf_products = self._convert_extraction_result(shelf_result, model)
                
                # Ensure all products have the correct shelf number
                for product in shelf_products:
                    product.position.shelf_number = shelf_num
                
                all_products.extend(shelf_products)
                
                logger.info(
                    f"Extracted {len(shelf_products)} products from shelf {shelf_num}",
                    component="extraction_orchestrator",
                    agent_id=agent_id,
                    shelf_number=shelf_num,
                    product_count=len(shelf_products)
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to extract shelf {shelf_num}: {e}",
                    component="extraction_orchestrator",
                    agent_id=agent_id,
                    shelf_number=shelf_num,
                    error=str(e)
                )
                # Continue with next shelf even if one fails
                continue
        
        # Sort products by shelf then position
        all_products.sort(key=lambda p: (p.position.shelf_number, p.position.position_on_shelf))
        
        logger.info(
            f"Shelf-by-shelf extraction complete: {len(all_products)} total products",
            component="extraction_orchestrator",
            agent_id=agent_id,
            total_products=len(all_products),
            shelves_processed=context.structure.shelf_count
        )
        
        return all_products
    
    def _convert_extraction_result(self, extraction_result: List[Any], model: AIModelType) -> List[ProductExtraction]:
        """Convert extraction engine results to our ProductExtraction format"""
        from ..models.extraction_models import ProductExtraction, ProductPosition, ConfidenceLevel
        
        converted_products = []
        for product in extraction_result:
            # The extraction engine returns products with quantity.total_facings
            facing_count = 1  # Default
            if hasattr(product, 'quantity') and product.quantity:
                facing_count = product.quantity.total_facings
            
            # Get section from SectionCoordinates if available
            section = None
            if hasattr(product, 'section') and product.section:
                section = product.section.vertical  # Use vertical section (Left/Center/Right)
            
            # Create ProductPosition from extraction result
            position = ProductPosition(
                shelf_number=product.shelf_level,
                position_on_shelf=product.position_on_shelf,
                facing_count=facing_count,
                section=section,
                confidence=product.extraction_confidence if hasattr(product, 'extraction_confidence') else 0.8
            )
            
            # Create ProductExtraction with updated model
            converted = ProductExtraction(
                brand=product.brand,
                name=product.name,
                price=product.price,
                position=position,
                extraction_confidence=product.extraction_confidence if hasattr(product, 'extraction_confidence') else 0.8,
                confidence_category=product.confidence_category if hasattr(product, 'confidence_category') else ConfidenceLevel.HIGH,
                extracted_by_model=model.value
            )
            converted_products.append(converted)
        
        return converted_products
    
    async def _mock_extraction_with_context(self, 
                                          image: bytes,
                                          context: CumulativeExtractionContext,
                                          agent_number: int) -> List[ProductExtraction]:
        """Mock extraction for testing - replace with actual extraction engine"""
        products = []
        
        # Start with locked positions
        for locked in context.locked_positions:
            if 'data' in locked:
                product_data = locked['data']
                product = ProductExtraction(
                    section=SectionCoordinates(horizontal="1", vertical="Center"),
                    position=Position(
                        l_position_on_section=1,
                        r_position_on_section=1,
                        l_empty=False,
                        r_empty=False
                    ),
                    brand=product_data.get('brand', 'Unknown'),
                    name=product_data.get('name', 'Unknown Product'),
                    price=product_data.get('price'),
                    quantity=Quantity(stack=1, columns=1, total_facings=1),
                    shelf_level=1,
                    position_on_shelf=1,
                    extraction_confidence=0.95,
                    confidence_category=ConfidenceLevel.VERY_HIGH,
                    extracted_by_model=self._select_model_for_agent(agent_number, context)
                )
                products.append(product)
        
        # Add some improvements for focus areas
        if agent_number > 1:
            # Simulate finding missed products
            products.append(ProductExtraction(
                section=SectionCoordinates(horizontal="2", vertical="Center"),
                position=Position(
                    l_position_on_section=3,
                    r_position_on_section=3,
                    l_empty=False,
                    r_empty=False
                ),
                brand="Red Bull",
                name="Energy Drink 250ml",
                price=1.89,
                quantity=Quantity(stack=1, columns=2, total_facings=2),
                shelf_level=2,
                position_on_shelf=3,
                extraction_confidence=0.88,
                confidence_category=ConfidenceLevel.HIGH,
                extracted_by_model=self._select_model_for_agent(agent_number, context)
            ))
        
        return products
    
    def _calculate_overall_confidence(self, products: List[ProductExtraction]) -> ConfidenceLevel:
        """Calculate overall confidence level"""
        if not products:
            return ConfidenceLevel.LOW
        
        avg_confidence = sum(p.extraction_confidence for p in products) / len(products)
        
        if avg_confidence >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 0.70:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _estimate_accuracy(self, products: List[ProductExtraction]) -> float:
        """Estimate extraction accuracy"""
        if not products:
            return 0.0
        
        # Simple accuracy based on confidence
        return sum(p.extraction_confidence for p in products) / len(products)
    
    def _analyze_improvements(self, 
                            current: ExtractionResult,
                            previous: ExtractionResult) -> List[str]:
        """Analyze improvements between iterations"""
        improvements = []
        
        # Product count improvement
        if current.total_products > previous.total_products:
            improvements.append(
                f"Found {current.total_products - previous.total_products} additional products"
            )
        
        # Confidence improvement
        if current.accuracy_estimate > previous.accuracy_estimate:
            improvements.append(
                f"Improved accuracy from {previous.accuracy_estimate:.1%} to "
                f"{current.accuracy_estimate:.1%}"
            )
        
        # Position confidence improvements
        high_conf_current = sum(1 for p in current.products if p.extraction_confidence >= 0.95)
        high_conf_previous = sum(1 for p in previous.products if p.extraction_confidence >= 0.95)
        
        if high_conf_current > high_conf_previous:
            improvements.append(
                f"Increased high-confidence products from {high_conf_previous} to {high_conf_current}"
            )
        
        return improvements
    
    async def execute_stage(self,
                          stage_name: str,
                          model_id: str,
                          images: Dict[str, bytes],
                          locked_context: Dict,
                          previous_attempts: List = None,
                          attempt_number: int = 1,
                          agent_id: str = None) -> Any:
        """Execute a single stage with a specific model"""
        
        logger.info(
            f"Executing stage '{stage_name}' with model {model_id}",
            component="extraction_orchestrator",
            stage=stage_name,
            model=model_id,
            attempt=attempt_number,
            has_locked_context='structure' in locked_context
        )
        
        if stage_name == 'structure':
            return await self._execute_structure_stage(
                images=images,
                model_id=model_id,
                previous_attempts=previous_attempts,
                agent_id=agent_id
            )
        elif stage_name == 'products':
            return await self._execute_products_stage(
                images=images,
                structure=locked_context.get('structure'),
                model_id=model_id,
                previous_attempts=previous_attempts,
                attempt_number=attempt_number,
                agent_id=agent_id
            )
        elif stage_name == 'details':
            return await self._execute_details_stage(
                images=images,
                structure=locked_context.get('structure'),
                products=locked_context.get('products'),
                model_id=model_id,
                previous_attempts=previous_attempts,
                agent_id=agent_id
            )
        else:
            raise ValueError(f"Unknown stage: {stage_name}")
    
    async def _execute_structure_stage(self,
                                     images: Dict[str, bytes],
                                     model_id: str,
                                     previous_attempts: List,
                                     agent_id: str) -> Any:
        """Execute structure extraction stage"""
        from ..extraction.prompts import PromptTemplates
        from ..extraction.dynamic_model_builder import DynamicModelBuilder
        
        analytics = get_extraction_analytics()
        
        # Get custom prompt if configured
        if hasattr(self, 'stage_prompts') and 'structure' in self.stage_prompts:
            prompt_template = self.stage_prompts['structure']
        else:
            # Fallback to default template
            prompt_templates = PromptTemplates()
            prompt_template = prompt_templates.get_template('scaffolding_analysis')
        
        # Process {IF_RETRY} blocks based on attempt number
        attempt_number = len(previous_attempts) + 1 if previous_attempts else 1
        
        # Build context for retry
        retry_context = {}
        if previous_attempts and attempt_number > 1:
            last_attempt = previous_attempts[-1]
            retry_context['shelf_count'] = last_attempt.shelf_count
            retry_context['shelves'] = last_attempt.shelf_count  # Alias for compatibility
            retry_context['problem_areas'] = "Check bottom shelf for floor products, verify top shelf visibility"
            
        prompt = self.process_retry_blocks(prompt_template, attempt_number, retry_context)
        
        # If we have previous attempts, build on them
        if previous_attempts:
            previous_structure = previous_attempts[-1]
            prompt += f"\n\nPrevious analysis found {previous_structure.shelf_count} shelves. Please verify and refine this analysis."
        
        # Track iteration with analytics
        async with analytics.track_iteration(
            extraction_run_id=getattr(self, 'extraction_run_id', agent_id),
            queue_item_id=getattr(self, 'queue_item_id', 0),
            iteration_number=attempt_number,
            stage='structure',
            model_used=model_id,
            model_index=1,
            actual_prompt=prompt,
            retry_context=retry_context if attempt_number > 1 else None
        ) as iteration_id:
            
            # Determine output schema - use dynamic model if configured
            output_schema = "ShelfStructure"  # Default
            
            if hasattr(self, 'stage_fields') and 'structure' in self.stage_fields:
                fields = self.stage_fields['structure']
                if fields:
                    logger.info(
                        f"Building dynamic model for structure stage with {len(fields)} fields",
                        component="extraction_orchestrator",
                        field_count=len(fields)
                    )
                    # Build dynamic model from configured fields
                    output_schema = DynamicModelBuilder.build_model_from_config('structure', {'fields': fields})
            
            # Execute with the model
            result, cost = await self.extraction_engine.execute_with_model_id(
                model_id=model_id,
                prompt=prompt,
                images=images,
                output_schema=output_schema,
                agent_id=agent_id
            )
            
            # Update iteration with results
            await analytics.update_iteration_result(
                iteration_id=iteration_id,
                extraction_result={'shelf_count': result.shelf_count if hasattr(result, 'shelf_count') else 0},
                accuracy_score=getattr(result, 'structure_confidence', 0.8),
                api_cost=cost,
                tokens_used=None  # Would need to get from extraction engine
            )
        
        # Add confidence score
        if not hasattr(result, 'structure_confidence'):
            # Simple confidence based on consistency with previous attempts
            if previous_attempts:
                prev_shelf_counts = [a.shelf_count for a in previous_attempts if hasattr(a, 'shelf_count')]
                if prev_shelf_counts and all(c == result.shelf_count for c in prev_shelf_counts):
                    result.structure_confidence = 0.95
                else:
                    result.structure_confidence = 0.80
            else:
                result.structure_confidence = 0.85
        
        result.api_cost_estimate = cost
        return result
    
    async def _execute_products_stage(self,
                                    images: Dict[str, bytes],
                                    structure: Any,
                                    model_id: str,
                                    previous_attempts: List,
                                    attempt_number: int,
                                    agent_id: str) -> ExtractionResult:
        """Execute products extraction stage with locked structure"""
        
        # Build cumulative context from previous attempts
        context = None
        if previous_attempts:
            context = self._build_cumulative_context(
                structure=structure,
                previous_attempts=previous_attempts,
                focus_areas=None,
                locked_positions=None,
                iteration=attempt_number
            )
        
        # Use existing cumulative learning method but with locked structure
        return await self.extract_with_cumulative_learning(
            image=images.get('enhanced', images.get('main', list(images.values())[0])),
            iteration=attempt_number,
            previous_attempts=previous_attempts,
            focus_areas=context.focus_areas if context else None,
            locked_positions=context.locked_positions if context else None,
            agent_id=agent_id
        )
    
    async def _execute_details_stage(self,
                                   images: Dict[str, bytes],
                                   structure: Any,
                                   products: ExtractionResult,
                                   model_id: str,
                                   previous_attempts: List,
                                   agent_id: str) -> ExtractionResult:
        """Execute details extraction stage with locked products"""
        from ..extraction.prompts import PromptTemplates
        from ..extraction.dynamic_model_builder import DynamicModelBuilder
        
        # Get custom prompt for details
        if hasattr(self, 'stage_prompts') and 'details' in self.stage_prompts:
            prompt = self.stage_prompts['details']
        else:
            # Fallback to default template
            prompt_templates = PromptTemplates()
            prompt = prompt_templates.get_template('details_extraction')
        
        # Process {IF_RETRY} blocks based on attempt number
        attempt_number = len(previous_attempts) + 1 if previous_attempts else 1
        
        # Build context with locked products first (needed for retry context)
        products_list = products.products if hasattr(products, 'products') else []
        
        # Build context for retry
        retry_context = {}
        
        # Always build complete product list for template
        product_strings = []
        current_shelf = 0
        for product in products_list:
            # Add shelf header when we reach a new shelf
            if product.position.shelf_number != current_shelf:
                current_shelf = product.position.shelf_number
                product_strings.append(f"\nShelf {current_shelf}:")
            
            # Add product entry
            facings_text = f"({product.quantity.total_facings} facings)" if hasattr(product.quantity, 'total_facings') else ""
            section = getattr(product.position, 'section_on_shelf', 'center')
            section_text = f"- {section.title()} section"
            product_strings.append(
                f"- Position {product.position.position_on_shelf}: {product.brand} {product.name} {facings_text} {section_text}"
            )
        
        retry_context['complete_product_list'] = '\n'.join(product_strings) if product_strings else "No products extracted yet"
        
        # Add retry-specific context if this is a retry
        if previous_attempts and attempt_number > 1:
            # Analyze what details are missing
            missing_details = []
            for product in products_list:
                missing_items = []
                if not getattr(product, 'price', None):
                    missing_items.append("price")
                if not getattr(product, 'size_variant', None):
                    missing_items.append("size")
                if missing_items:
                    missing_details.append(f"{product.brand} {product.name}: {', '.join(missing_items)} missing")
            
            if missing_details:
                retry_context['missing_details'] = '\n'.join(missing_details[:10])
                retry_context['previous_details_by_product'] = f"Missing details:\n" + '\n'.join(missing_details[:10])
            
        prompt = self.process_retry_blocks(prompt, attempt_number, retry_context)
        
        prompt += f"\n\nExtract details for these {len(products_list)} confirmed products:\n"
        for i, product in enumerate(products_list, 1):
            prompt += f"{i}. Shelf {product.position.shelf_number}, Position {product.position.position_on_shelf}: {product.brand} {product.name}\n"
        
        # Determine output schema - use dynamic model if configured
        output_schema = "List[ProductExtraction]"  # Default
        
        if hasattr(self, 'stage_fields') and 'details' in self.stage_fields:
            fields = self.stage_fields['details']
            if fields:
                logger.info(
                    f"Building dynamic model for details stage with {len(fields)} fields",
                    component="extraction_orchestrator",
                    field_count=len(fields)
                )
                # Build dynamic model from configured fields
                from typing import List
                DetailModel = DynamicModelBuilder.build_model_from_config('detail', {'fields': fields})
                output_schema = List[DetailModel]
        
        # Execute details extraction
        result, cost = await self.extraction_engine.execute_with_model_id(
            model_id=model_id,
            prompt=prompt,
            images=images,
            output_schema=output_schema,
            agent_id=agent_id
        )
        
        # Merge details with existing products
        enhanced_products = []
        for original in products_list:
            # Find matching product in details result
            for detailed in result:
                if (detailed.position.shelf_number == original.position.shelf_number and
                    detailed.position.position_on_shelf == original.position.position_on_shelf):
                    # Merge details
                    original.price = detailed.price or original.price
                    if hasattr(detailed, 'size_variant'):
                        original.size_variant = detailed.size_variant
                    if hasattr(detailed, 'promotional_tags'):
                        original.promotional_tags = detailed.promotional_tags
                    break
            enhanced_products.append(original)
        
        # Create result with enhanced products
        return ExtractionResult(
            agent_number=attempt_number,
            structure=structure,
            products=enhanced_products,
            total_products=len(enhanced_products),
            overall_confidence=self._calculate_overall_confidence(enhanced_products),
            accuracy_estimate=self._estimate_accuracy(enhanced_products),
            extraction_duration_seconds=0,
            model_used=model_id,
            api_cost_estimate=cost
        ) 