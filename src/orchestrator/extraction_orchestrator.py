"""
Extraction Orchestrator
Manages cumulative agent learning and extraction strategy
"""

import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

from ..config import SystemConfig
from ..agents.structure_agent import StructureAnalysisAgent
from ..models.extraction_models import (
    ExtractionResult, CumulativeExtractionContext, ValidationFlag
)
from ..extraction.models import (
    ProductExtraction, Position, SectionCoordinates, Quantity, 
    AIModelType, ConfidenceLevel
)
from ..models.shelf_structure import ShelfStructure
from ..utils import logger


class ExtractionOrchestrator:
    """Orchestrates extraction with cumulative learning between agents"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.structure_agent = StructureAnalysisAgent(config)
        
        # Initialize real extraction engine
        from ..extraction.engine import ModularExtractionEngine
        self.extraction_engine = ModularExtractionEngine(config)
        
        logger.info(
            "Extraction Orchestrator initialized with real extraction engine",
            component="extraction_orchestrator"
        )
    
    async def extract_with_cumulative_learning(self, 
                                             image: bytes,
                                             iteration: int = 1,
                                             previous_attempts: List[ExtractionResult] = None,
                                             focus_areas: List[Dict] = None,
                                             locked_positions: List[Dict] = None,
                                             agent_id: str = None) -> ExtractionResult:
        """Execute extraction with cumulative learning from previous attempts"""
        
        logger.info(
            f"Starting cumulative extraction - Iteration {iteration}",
            component="extraction_orchestrator",
            agent_id=agent_id,
            iteration=iteration,
            has_previous=previous_attempts is not None
        )
        
        # Phase 0: Structure analysis (only on first iteration)
        if iteration == 1:
            structure = await self.structure_agent.analyze_structure(image, agent_id)
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
                                structure: ShelfStructure,
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
        model = self._select_model_for_agent(agent_number, context)
        
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
    
    def _select_model_for_agent(self, agent_number: int, context: CumulativeExtractionContext) -> AIModelType:
        """Select appropriate model based on agent number and context"""
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
        
        all_products = []
        prompt_templates = PromptTemplates()
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
            
            # Build shelf-specific prompt
            shelf_prompt = shelf_prompt_template.format(
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
            
            try:
                # Execute extraction for this shelf
                shelf_result, api_cost = await self.extraction_engine._execute_with_fallback(
                    primary_model=model,
                    prompt=shelf_prompt,
                    images={"main": image},
                    output_schema="List[ProductExtraction]",
                    agent_id=f"{agent_id}_shelf_{shelf_num}"
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