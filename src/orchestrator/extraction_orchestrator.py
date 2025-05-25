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
    ExtractionResult, CumulativeExtractionContext, ProductExtraction,
    ConfidenceLevel, ValidationFlag
)
from ..models.shelf_structure import ShelfStructure
from ..utils import logger


class ExtractionOrchestrator:
    """Orchestrates extraction with cumulative learning between agents"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.structure_agent = StructureAnalysisAgent(config)
        
        logger.info(
            "Extraction Orchestrator initialized",
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
                position_key = f"shelf_{product.position.shelf_number}_pos_{product.position.position_on_shelf}"
                
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
        
        # Execute extraction (simplified for now - would call actual extraction engine)
        start_time = datetime.utcnow()
        
        # TODO: Call actual extraction engine with cumulative context
        # For now, create mock result
        products = await self._mock_extraction_with_context(image, context, agent_number)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Build result
        result = ExtractionResult(
            agent_number=agent_number,
            structure=context.structure,
            products=products,
            overall_confidence=self._calculate_overall_confidence(products),
            accuracy_estimate=self._estimate_accuracy(products),
            extraction_duration_seconds=duration,
            model_used=model,
            api_cost_estimate=0.05 * agent_number  # Mock cost
        )
        
        return result
    
    def _build_cumulative_prompt(self, agent_number: int, context: CumulativeExtractionContext) -> str:
        """Build prompt that includes learning from all previous agents"""
        
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
    
    def _select_model_for_agent(self, agent_number: int, context: CumulativeExtractionContext) -> str:
        """Select appropriate model based on agent number and context"""
        if agent_number == 1:
            return "gpt-4o-2024-11-20"  # Fast initial extraction
        elif agent_number == 2:
            return "claude-3-5-sonnet-20241022"  # Better reasoning for improvements
        else:
            # Use best model for final refinements
            return "claude-3-5-sonnet-20241022 + gemini-2.0-flash-exp"
    
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
                    brand=product_data.get('brand', 'Unknown'),
                    name=product_data.get('name', 'Unknown Product'),
                    price=product_data.get('price'),
                    position=product_data.get('position', {
                        'shelf_number': 1,
                        'position_on_shelf': 1,
                        'facing_count': 1,
                        'confidence': 0.95
                    }),
                    extraction_confidence=0.95,
                    confidence_category=ConfidenceLevel.VERY_HIGH,
                    extracted_by_model=self._select_model_for_agent(agent_number, context)
                )
                products.append(product)
        
        # Add some improvements for focus areas
        if agent_number > 1:
            # Simulate finding missed products
            products.append(ProductExtraction(
                brand="Red Bull",
                name="Energy Drink 250ml",
                price=1.89,
                position={
                    'shelf_number': 2,
                    'position_on_shelf': 3,
                    'facing_count': 2,
                    'confidence': 0.88
                },
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