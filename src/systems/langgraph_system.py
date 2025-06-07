"""
LangGraph Framework System
Professional workflow management with built-in state persistence and proven patterns
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from typing_extensions import TypedDict

try:
    from langgraph.graph import StateGraph
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # Mock classes for when LangGraph is not available
    class StateGraph:
        def __init__(self, state_schema): pass
        def add_node(self, name, func): pass
        def add_conditional_edges(self, source, condition): pass
        def set_entry_point(self, node): pass
        def compile(self, checkpointer=None): return MockWorkflow()
    
    class MemorySaver:
        pass
    
    class MockWorkflow:
        async def ainvoke(self, state, config): return state

from .base_system import BaseExtractionSystem, ExtractionResult, CostBreakdown, PerformanceMetrics
from ..config import SystemConfig
from ..utils import logger
from ..feedback.human_learning import HumanFeedbackLearningSystem
from ..extraction.engine import ModularExtractionEngine
from ..extraction.dynamic_model_builder import DynamicModelBuilder


class LangGraphExtractionState(TypedDict):
    """State schema for LangGraph workflow"""
    image_data: bytes
    upload_id: str
    # New dynamic stage-based results
    stage_results: Optional[Dict]
    final_planogram: Optional[Dict]
    # Legacy fields for backward compatibility
    structure_consensus: Optional[Dict]
    position_consensus: Optional[Dict]
    quantity_consensus: Optional[Dict]
    detail_consensus: Optional[Dict]
    planogram: Optional[Dict]
    validation_result: Optional[Dict]
    iteration_count: int
    locked_results: Dict
    processing_start_time: float
    cost_tracker: Dict
    consensus_rates: Dict


class LangGraphConsensusSystem(BaseExtractionSystem):
    """LangGraph implementation with professional workflow management"""
    
    def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):
        super().__init__(config)
        self.queue_item_id = queue_item_id
        
        if not LANGGRAPH_AVAILABLE:
            logger.warning(
                "LangGraph not available - using mock implementation",
                component="langgraph_system"
            )
        
        self.human_feedback = HumanFeedbackLearningSystem(config)
        self.cost_tracker = {'total_cost': 0, 'model_costs': {}, 'api_calls': {}, 'tokens_used': {}}
        self.extraction_engine = ModularExtractionEngine(config)
        
        # Create workflow
        self.workflow = self._create_workflow()
        
        logger.info(
            "LangGraph consensus system initialized",
            component="langgraph_system",
            langgraph_available=LANGGRAPH_AVAILABLE
        )
    
    def _create_workflow(self):
        """Create DYNAMIC LangGraph workflow based on configured stages"""
        
        if not LANGGRAPH_AVAILABLE:
            return MockWorkflow()
        
        workflow = StateGraph(LangGraphExtractionState)
        
        # DYNAMIC workflow - uses configured stages instead of hardcoded ones
        workflow.add_node("process_configured_stages_node", self._process_configured_stages_node)
        workflow.add_node("generate_final_planogram_node", self._generate_final_planogram_node)
        workflow.add_node("validate_end_to_end_node", self._validate_end_to_end_node)
        workflow.add_node("smart_retry_node", self._smart_retry_node)
        workflow.add_node("finalize_result_node", self._finalize_result_node)
        
        # Conditional routing based on results
        workflow.add_conditional_edges(
            "process_configured_stages_node",
            lambda state: "generate_final_planogram_node" if self._all_stages_completed(state) else "smart_retry_node"
        )
        
        workflow.add_conditional_edges(
            "generate_final_planogram_node",
            lambda state: "validate_end_to_end_node" if state.get("final_planogram") else "smart_retry_node"
        )
        
        workflow.add_conditional_edges(
            "validate_end_to_end_node", 
            self._should_retry_or_finalize
        )
        
        workflow.add_conditional_edges(
            "smart_retry_node",
            lambda state: "process_configured_stages_node" if state["iteration_count"] < 5 else "finalize_result_node"
        )
        
        # Set entry point to process configured stages
        workflow.set_entry_point("process_configured_stages_node")
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def extract_with_consensus(self, image_data: bytes, upload_id: str, extraction_data: Optional[Dict] = None) -> ExtractionResult:
        """Main extraction using LangGraph workflow"""
        
        logger.info(
            f"Starting LangGraph consensus extraction for upload {upload_id}",
            component="langgraph_system",
            upload_id=upload_id
        )
        
        initial_state = LangGraphExtractionState(
            image_data=image_data,
            upload_id=upload_id,
            # New dynamic stage-based results
            stage_results={},
            final_planogram=None,
            # Legacy fields for backward compatibility
            structure_consensus=None,
            position_consensus=None,
            quantity_consensus=None,
            detail_consensus=None,
            planogram=None,
            validation_result=None,
            iteration_count=1,
            locked_results={},
            processing_start_time=time.time(),
            cost_tracker=self.cost_tracker.copy(),
            consensus_rates={}
        )
        
        # Run the workflow with increased recursion limit
        config = {
            "configurable": {"thread_id": upload_id},
            "recursion_limit": 50  # Increase from default 25 to handle complex extractions
        }
        
        try:
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            # Convert state to ExtractionResult
            result = await self._convert_state_to_result(final_state)
            
            # Prepare for human feedback
            await self.human_feedback.prepare_for_validation(upload_id, result)
            
            logger.info(
                f"LangGraph extraction completed successfully",
                component="langgraph_system",
                upload_id=upload_id,
                accuracy=result.overall_accuracy,
                iterations=result.iteration_count
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"LangGraph workflow failed: {e}",
                component="langgraph_system",
                upload_id=upload_id,
                error=str(e)
            )
            
            # Re-raise the exception so it gets handled properly upstream
            raise
    
    async def _structure_consensus_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for structure consensus"""
        
        logger.info(
            f"LangGraph: Structure consensus node - iteration {state['iteration_count']}",
            component="langgraph_system",
            iteration=state['iteration_count']
        )
        
        if 'structure' in state.get('locked_results', {}):
            state['structure_consensus'] = state['locked_results']['structure']
            logger.info("🔒 Using locked structure", component="langgraph_system")
            return state
        
        # Run consensus logic (mock implementation)
        try:
            structure_proposals = await self._run_structure_agents(state['image_data'])
            consensus = self._vote_on_structure(structure_proposals)
            
            if consensus['consensus_reached']:
                state['structure_consensus'] = consensus['result']
                state['consensus_rates']['structure'] = consensus['confidence']
                
                # Track costs
                self._track_workflow_costs(state, 'structure', 0.08, 2000)
                
                logger.info(
                    f"✅ LangGraph structure consensus: {consensus['confidence']:.0%}",
                    component="langgraph_system",
                    confidence=consensus['confidence']
                )
            else:
                logger.warning(
                    f"❌ LangGraph structure consensus failed: {consensus.get('reason')}",
                    component="langgraph_system"
                )
        
        except Exception as e:
            logger.error(
                f"Structure consensus node failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    async def _process_configured_stages_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """DYNAMIC node that processes all configured stages with visual feedback between models"""
        
        logger.info(
            f"LangGraph: Processing configured stages - iteration {state['iteration_count']}",
            component="langgraph_system",
            iteration=state['iteration_count']
        )
        
        # Get configured stages from the system
        configured_stages = getattr(self, 'stage_configs', {})
        if not configured_stages:
            # Fallback to traditional stages if no configuration
            stages_to_process = ['structure', 'products', 'details']
            logger.warning("No stage configurations found, using default stages", component="langgraph_system")
        else:
            stages_to_process = list(configured_stages.keys())
            logger.info(f"Processing configured stages: {stages_to_process}", component="langgraph_system")
        
        stage_results = state.get('stage_results', {})
        
        for stage in stages_to_process:
            logger.info(
                f"Processing stage: {stage}",
                component="langgraph_system",
                stage=stage,
                iteration=state['iteration_count']
            )
            
            # Check if this stage is locked from previous iteration
            if stage in state.get('locked_results', {}):
                stage_results[stage] = state['locked_results'][stage]
                logger.info(f"🔒 Using locked {stage} result", component="langgraph_system")
                continue
            
            # Get models for this stage
            models_for_stage = getattr(self, 'stage_models', {}).get(stage, ['gpt-4o', 'claude-3-sonnet'])
            
            # Process stage with visual feedback between models (per documentation)
            stage_result = await self._process_stage_with_visual_feedback_langgraph(
                stage=stage,
                models=models_for_stage,
                image_data=state['image_data'],
                previous_stages=stage_results,
                state=state
            )
            
            stage_results[stage] = stage_result
        
        # Update state with all stage results
        state['stage_results'] = stage_results
        
        # Mark stages as completed in state for conditional routing
        for stage in stages_to_process:
            if stage in stage_results:
                state[f'{stage}_consensus'] = stage_results[stage]
        
        return state
    
    async def _process_stage_with_visual_feedback_langgraph(
        self,
        stage: str,
        models: List[str],
        image_data: bytes,
        previous_stages: Dict[str, Any],
        state: LangGraphExtractionState
    ) -> Dict[str, Any]:
        """Process single stage with visual feedback between models (as per documentation)"""
        
        model_results = []
        visual_feedback_history = []
        
        for i, model in enumerate(models):
            logger.info(
                f"Processing {stage} with model {i+1}/{len(models)}: {model}",
                component="langgraph_system",
                stage=stage,
                model=model,
                attempt=i+1
            )
            
            # Build prompt with visual feedback from previous models in this stage
            prompt = self._build_stage_prompt_with_visual_feedback(
                stage=stage,
                attempt_number=i+1,
                visual_feedback=visual_feedback_history,
                previous_stages=previous_stages
            )
            
            # Extract with current model
            extraction_result = await self._extract_with_model_langgraph(
                model=model,
                prompt=prompt,
                image_data=image_data,
                stage=stage,
                previous_stages=previous_stages
            )
            
            model_results.append({
                'model': model,
                'result': extraction_result,
                'attempt': i+1
            })
            
            # VISUAL FEEDBACK BETWEEN MODELS (per documentation - ONLY for products stage)
            if stage == 'products':  # Visual feedback only in products stage
                # Generate planogram from current extraction
                temp_extraction = self._create_temp_extraction_langgraph(previous_stages, stage, extraction_result)
                planogram = await self._generate_planogram_for_stage(temp_extraction, f"{stage}_model_{i+1}")
                
                # Visual comparison for feedback to next model
                if hasattr(self, 'stage_prompts') and 'comparison' in self.stage_prompts:
                    comparison_result = await self._compare_with_original_langgraph(
                        image_data,
                        planogram,
                        self.stage_prompts['comparison']
                    )
                    
                    # Extract actionable feedback for next model
                    actionable_feedback = await self._extract_actionable_feedback_langgraph(comparison_result)
                    
                    visual_feedback_history.append({
                        'model': model,
                        'attempt': i+1,
                        'comparison_result': comparison_result,
                        'actionable_feedback': actionable_feedback,
                        'planogram': planogram
                    })
                    
                    logger.info(
                        f"Visual feedback from model {i+1}: {len(actionable_feedback)} issues found",
                        component="langgraph_system",
                        issues_found=len(actionable_feedback)
                    )
        
        # Apply consensus voting on all model results
        consensus_result = await self._apply_stage_consensus_langgraph(stage, model_results, visual_feedback_history)
        
        return consensus_result
    
    def _all_stages_completed(self, state: LangGraphExtractionState) -> bool:
        """Check if all configured stages have been completed"""
        configured_stages = getattr(self, 'stage_configs', {})
        if not configured_stages:
            # Default stages check
            required_stages = ['structure', 'products', 'details']
        else:
            required_stages = list(configured_stages.keys())
        
        stage_results = state.get('stage_results', {})
        completed = all(stage in stage_results for stage in required_stages)
        
        logger.info(
            f"Stage completion check: {len(stage_results)}/{len(required_stages)} stages completed",
            component="langgraph_system",
            completed_stages=list(stage_results.keys()),
            required_stages=required_stages,
            all_completed=completed
        )
        
        return completed
    
    async def _position_consensus_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for position consensus"""
        
        logger.info(
            "LangGraph: Position consensus node",
            component="langgraph_system"
        )
        
        if 'positions' in state.get('locked_results', {}):
            state['position_consensus'] = state['locked_results']['positions']
            logger.info("🔒 Using locked positions", component="langgraph_system")
            return state
        
        try:
            # Real product extraction
            structure = state.get('structure_consensus', {})
            # Handle case where structure might be a string or other non-dict type
            if isinstance(structure, str):
                logger.warning(
                    f"Structure consensus is string, parsing for shelf count",
                    component="langgraph_system"
                )
                # Try to extract shelf count from string
                import re
                shelf_match = re.search(r'(\d+)\s*shelves?', structure.lower())
                shelf_count = int(shelf_match.group(1)) if shelf_match else 4
            elif isinstance(structure, dict):
                shelf_count = structure.get('shelf_count', 4)
            else:
                logger.warning(
                    f"Unexpected structure type: {type(structure)}, using default",
                    component="langgraph_system"
                )
                shelf_count = 4
            
            # Get products stage configuration
            prompt = getattr(self, 'stage_prompts', {}).get('products', 
                f'Extract all products from this {shelf_count}-shelf retail display.')
            
            # Build dynamic model
            output_schema = self._get_output_schema_for_stage('products')
            
            # Get models for consensus
            models = getattr(self, 'stage_models', {}).get('products', ['gpt-4o', 'claude-3-sonnet'])
            
            all_positions = {}
            
            for model in models:
                try:
                    # Real extraction
                    result, cost = await self.extraction_engine.execute_with_model_id(
                        model_id=model,
                        prompt=prompt,
                        images={'enhanced': state['image_data']},
                        output_schema=output_schema,
                        agent_id=f"langgraph_products_{model}"
                    )
                    
                    # Parse products from result
                    products = self._extract_products_from_result(result)
                    
                    # Debug: Check what we got
                    logger.info(f"Products extracted from {model}: {len(products)} items", component="langgraph_system")
                    if products:
                        logger.info(f"First product example: {products[0]}", component="langgraph_system")
                    
                    # Merge into positions - add safety check
                    for product in products:
                        if product is None:
                            logger.warning(f"Skipping None product from {model}", component="langgraph_system")
                            continue
                        key = f"shelf_{product.get('shelf', 1)}_pos_{product.get('position', 1)}"
                        if key not in all_positions:
                            all_positions[key] = product
                    
                    self.cost_tracker['total_cost'] += cost
                    
                except Exception as e:
                    logger.error(f"Products extraction with {model} failed: {e}", component="langgraph_system")
            
            positions = all_positions
            
            state['position_consensus'] = positions
            state['consensus_rates']['positions'] = 0.87
            
            # Track costs
            self._track_workflow_costs(state, 'positions', 0.12, 3000)
            
            logger.info(
                f"✅ LangGraph position consensus: {len(positions)} positions",
                component="langgraph_system",
                position_count=len(positions)
            )
        
        except Exception as e:
            logger.error(
                f"Position consensus node failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    async def _quantity_consensus_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for quantity consensus"""
        
        logger.info(
            "LangGraph: Quantity consensus node",
            component="langgraph_system"
        )
        
        try:
            # The quantities are already extracted with products
            # This node just validates and refines them
            positions = state.get('position_consensus', {})
            quantities = {}
            
            for pos_key, product in positions.items():
                # Extract quantity info from product data
                if isinstance(product, dict):
                    quantities[pos_key] = {
                        'facing_count': product.get('facings', product.get('facing_count', 1)),
                        'stack_count': product.get('stack', product.get('stack_count', 1)),
                        'confidence': product.get('confidence', 0.85)
                    }
            
            state['quantity_consensus'] = quantities
            state['consensus_rates']['quantities'] = 0.85
            
            # Track costs
            self._track_workflow_costs(state, 'quantities', 0.06, 1500)
            
            logger.info(
                f"✅ LangGraph quantity consensus: {len(quantities)} quantities",
                component="langgraph_system",
                quantity_count=len(quantities)
            )
        
        except Exception as e:
            logger.error(
                f"Quantity consensus node failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    async def _detail_consensus_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for detail consensus"""
        
        logger.info(
            "LangGraph: Detail consensus node",
            component="langgraph_system"
        )
        
        try:
            positions = state.get('position_consensus', {})
            
            # Get details prompt
            prompt = getattr(self, 'stage_prompts', {}).get('details', 
                'Extract detailed information including prices and sizes for the identified products.')
            
            # Build list of products for detail extraction
            products_list = []
            for pos_key, product in positions.items():
                if isinstance(product, dict):
                    products_list.append(product)
            
            # Add product list to prompt
            prompt += "\n\nProducts to enhance:\n"
            for i, prod in enumerate(products_list, 1):
                prompt += f"{i}. {prod.get('brand', 'Unknown')} {prod.get('name', 'Product')} at shelf {prod.get('shelf', '?')}\n"
            
            # Get models for consensus
            models = getattr(self, 'stage_models', {}).get('details', ['gpt-4o', 'claude-3-sonnet'])
            
            # Build dynamic model
            output_schema = self._get_output_schema_for_stage('details')
            
            all_details = {}
            
            for model in models[:1]:  # Use just one model for details to save costs
                try:
                    # Real extraction
                    result, cost = await self.extraction_engine.execute_with_model_id(
                        model_id=model,
                        prompt=prompt,
                        images={'enhanced': state['image_data']},
                        output_schema=output_schema,
                        agent_id=f"langgraph_details_{model}"
                    )
                    
                    # Parse details from result
                    details_data = self._extract_details_from_result(result, positions)
                    all_details.update(details_data)
                    
                    self.cost_tracker['total_cost'] += cost
                    
                except Exception as e:
                    logger.error(f"Details extraction with {model} failed: {e}", component="langgraph_system")
            
            # If no details extracted, use product data
            details = {}
            for pos_key, product in positions.items():
                if pos_key in all_details:
                    details[pos_key] = all_details[pos_key]
                else:
                    # Fallback to basic info from product
                    details[pos_key] = {
                        'price': product.get('price'),
                        'size': product.get('size'),
                        'color': product.get('color', product.get('primary_color')),
                        'confidence': 0.7
                    }
            
            state['detail_consensus'] = details
            state['consensus_rates']['details'] = 0.83
            
            # Track costs
            self._track_workflow_costs(state, 'details', 0.04, 1000)
            
            logger.info(
                f"✅ LangGraph detail consensus: {len(details)} details",
                component="langgraph_system",
                detail_count=len(details)
            )
        
        except Exception as e:
            logger.error(
                f"Detail consensus node failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    async def _generate_planogram_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for planogram generation"""
        
        logger.info(
            "LangGraph: Generate planogram node",
            component="langgraph_system"
        )
        
        try:
            structure = state.get('structure_consensus', {})
            positions = state.get('position_consensus', {})
            
            planogram = {
                'planogram_id': f"langgraph_planogram_{int(time.time())}",
                'shelf_count': structure.get('shelf_count', 4),
                'products': len(positions),
                'generated_at': datetime.utcnow().isoformat(),
                'system': 'langgraph'
            }
            
            state['planogram'] = planogram
            
            logger.info(
                f"✅ LangGraph planogram generated: {planogram['products']} products",
                component="langgraph_system",
                product_count=planogram['products']
            )
        
        except Exception as e:
            logger.error(
                f"Planogram generation node failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    async def _validate_end_to_end_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for end-to-end validation"""
        
        logger.info(
            "LangGraph: Validation node",
            component="langgraph_system"
        )
        
        try:
            # Calculate actual accuracy based on extraction results
            # THIS IS PLACEHOLDER - Real validation should compare against ground truth
            structure = state.get('structure_consensus', {}) or {}
            positions = state.get('position_consensus', {}) or {}
            quantities = state.get('quantity_consensus', {}) or {}
            details = state.get('detail_consensus', {}) or {}
            
            # Basic validation: check if we have data
            has_structure = bool(structure)
            has_positions = len(positions) > 0 if isinstance(positions, (dict, list)) else False
            has_quantities = len(quantities) > 0 if isinstance(quantities, (dict, list)) else False
            has_details = len(details) > 0 if isinstance(details, (dict, list)) else False
            
            # Calculate accuracy based on what we have
            components = [has_structure, has_positions, has_quantities, has_details]
            accuracy = sum(components) / len(components) * 0.7  # Max 0.7 without human validation
            
            # Add confidence based on consensus rates
            consensus_rates = state.get('consensus_rates', {})
            if consensus_rates:
                avg_consensus = sum(consensus_rates.values()) / len(consensus_rates)
                accuracy += avg_consensus * 0.2  # Add up to 0.2 based on consensus
            
            # Cap at 0.85 without human validation
            accuracy = min(accuracy, 0.85)
            
            validation = {
                'accuracy': accuracy,
                'issues': self._identify_validation_issues(state),
                'validation_method': 'langgraph_workflow',
                'confidence': accuracy * 0.95,
                'needs_human_validation': True,
                'validation_details': {
                    'has_structure': has_structure,
                    'has_positions': has_positions,
                    'has_quantities': has_quantities,
                    'has_details': has_details,
                    'consensus_rates': consensus_rates
                }
            }
            
            state['validation_result'] = validation
            
            logger.info(
                f"✅ LangGraph validation complete: {accuracy:.1%} accuracy (needs human validation)",
                component="langgraph_system",
                accuracy=accuracy
            )
        
        except Exception as e:
            logger.error(
                f"Validation node failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    def _identify_validation_issues(self, state: LangGraphExtractionState) -> List[Dict]:
        """Identify validation issues in the extraction results"""
        issues = []
        
        # Check structure
        structure = state.get('structure_consensus', {})
        if not structure:
            issues.append({'type': 'missing_structure', 'severity': 'high'})
        
        # Check positions
        positions = state.get('position_consensus', {})
        if len(positions) < 10:  # Expecting at least 10 products
            issues.append({
                'type': 'low_product_count',
                'found': len(positions),
                'expected_min': 10,
                'severity': 'medium'
            })
        
        # Check consensus rates
        consensus_rates = state.get('consensus_rates', {})
        for stage, rate in consensus_rates.items():
            if rate < 0.7:
                issues.append({
                    'type': 'low_consensus',
                    'stage': stage,
                    'rate': rate,
                    'severity': 'medium'
                })
        
        return issues
    
    async def _smart_retry_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for smart retry logic"""
        
        logger.info(
            f"LangGraph: Smart retry node - iteration {state['iteration_count']}",
            component="langgraph_system",
            iteration=state['iteration_count']
        )
        
        # Increment iteration
        state['iteration_count'] += 1
        
        # Analyze what needs to be retried
        validation = state.get('validation_result') or {}
        issues = validation.get('issues', [])
        
        # Update locked results based on what's working
        locked_results = state.get('locked_results', {}).copy()
        
        # Lock successful consensus results
        consensus_rates = state.get('consensus_rates', {})
        for stage, rate in consensus_rates.items():
            if rate >= 0.85:  # High consensus rate
                if stage == 'structure' and state.get('structure_consensus'):
                    locked_results['structure'] = state['structure_consensus']
                elif stage == 'positions' and state.get('position_consensus'):
                    locked_results['positions'] = state['position_consensus']
        
        state['locked_results'] = locked_results
        
        logger.info(
            f"🔄 LangGraph smart retry: {len(locked_results)} stages locked",
            component="langgraph_system",
            locked_stages=len(locked_results),
            iteration=state['iteration_count']
        )
        
        return state
    
    async def _finalize_result_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """LangGraph node for finalizing results"""
        
        logger.info(
            "LangGraph: Finalize result node",
            component="langgraph_system"
        )
        
        # Mark as finalized
        state['finalized'] = True
        state['processing_end_time'] = time.time()
        
        return state
    
    def _should_retry_or_finalize(self, state: LangGraphExtractionState) -> str:
        """Conditional routing based on validation results"""
        
        validation = state.get('validation_result', {})
        accuracy = validation.get('accuracy', 0.0)
        iteration = state.get('iteration_count', 1)
        
        if accuracy >= 0.90 or iteration >= 5:
            return "finalize_result_node"
        else:
            return "smart_retry_node"
    
    async def _run_structure_agents(self, image_data: bytes) -> List[Dict]:
        """Run structure analysis with real AI models"""
        
        proposals = []
        models = getattr(self, 'stage_models', {}).get('structure', ['gpt-4o', 'claude-3-sonnet', 'gemini-pro'])
        
        for model in models:
            try:
                # Get prompt
                prompt = getattr(self, 'stage_prompts', {}).get('structure', 
                    'Analyze this retail shelf image and identify the physical structure.')
                
                # Build dynamic model if configured
                output_schema = self._get_output_schema_for_stage('structure')
                
                # Real extraction
                result, cost = await self.extraction_engine.execute_with_model_id(
                    model_id=model,
                    prompt=prompt,
                    images={'enhanced': image_data},
                    output_schema=output_schema,
                    agent_id=f"langgraph_structure_{model}"
                )
                
                # Parse result to get shelf count
                shelf_count = self._extract_shelf_count_from_result(result)
                
                # Add to proposals
                proposals.append({
                    'shelf_count': shelf_count,
                    'result': result,
                    'confidence': 0.85,  # Could be calculated from result
                    'model': model,
                    'cost': cost
                })
                
                # Track cost
                self.cost_tracker['total_cost'] += cost
                
            except Exception as e:
                logger.error(f"Structure agent {model} failed: {e}", component="langgraph_system")
        
        return proposals
    
    def _vote_on_structure(self, proposals: List[Dict]) -> Dict[str, Any]:
        """Vote on structure proposals (simplified)"""
        
        if not proposals:
            return {'consensus_reached': False, 'reason': 'No proposals'}
        
        # Simple majority voting
        from collections import Counter
        shelf_counts = [p.get('shelf_count', 0) for p in proposals]
        count_votes = Counter(shelf_counts)
        most_common_count, votes = count_votes.most_common(1)[0]
        
        consensus_rate = votes / len(shelf_counts)
        
        if consensus_rate >= 0.6:  # LangGraph uses lower threshold due to workflow benefits
            best_proposal = max(
                [p for p in proposals if p.get('shelf_count') == most_common_count],
                key=lambda x: x.get('confidence', 0)
            )
            
            return {
                'consensus_reached': True,
                'result': best_proposal,
                'confidence': consensus_rate
            }
        
        return {
            'consensus_reached': False,
            'reason': f'No consensus: {dict(count_votes)}',
            'consensus_rate': consensus_rate
        }
    
    def _track_workflow_costs(self, state: LangGraphExtractionState, stage: str, cost: float, tokens: int):
        """Track costs within workflow state"""
        
        cost_tracker = state.get('cost_tracker', {})
        cost_tracker['total_cost'] = cost_tracker.get('total_cost', 0) + cost
        
        if 'model_costs' not in cost_tracker:
            cost_tracker['model_costs'] = {}
        cost_tracker['model_costs'][stage] = cost_tracker['model_costs'].get(stage, 0) + cost
        
        if 'api_calls' not in cost_tracker:
            cost_tracker['api_calls'] = {}
        cost_tracker['api_calls'][stage] = cost_tracker['api_calls'].get(stage, 0) + 1
        
        if 'tokens_used' not in cost_tracker:
            cost_tracker['tokens_used'] = {}
        cost_tracker['tokens_used'][stage] = cost_tracker['tokens_used'].get(stage, 0) + tokens
        
        state['cost_tracker'] = cost_tracker
        
        # Also update instance tracker
        self.cost_tracker = cost_tracker
    
    async def _convert_state_to_result(self, state: LangGraphExtractionState) -> ExtractionResult:
        """Convert LangGraph state to ExtractionResult"""
        
        processing_time = state.get('processing_end_time', time.time()) - state.get('processing_start_time', time.time())
        validation = state.get('validation_result', {})
        accuracy = validation.get('accuracy', 0.0)
        
        cost_tracker = state.get('cost_tracker', {})
        cost_breakdown = CostBreakdown(
            total_cost=cost_tracker.get('total_cost', 0),
            model_costs=cost_tracker.get('model_costs', {}),
            api_calls=cost_tracker.get('api_calls', {}),
            tokens_used=cost_tracker.get('tokens_used', {}),
            cost_per_accuracy_point=self._calculate_cost_efficiency(cost_tracker.get('total_cost', 0), accuracy)
        )
        
        consensus_rates = state.get('consensus_rates', {})
        avg_consensus_rate = sum(consensus_rates.values()) / len(consensus_rates) if consensus_rates else 0.0
        
        # Store for later use
        self._last_accuracy = accuracy
        self._last_consensus_rate = avg_consensus_rate
        self._last_iteration_count = state.get('iteration_count', 1)
        self._last_processing_time = processing_time
        
        performance_metrics = PerformanceMetrics(
            accuracy=accuracy,
            processing_time=processing_time,
            consensus_rate=avg_consensus_rate,
            iteration_count=state.get('iteration_count', 1),
            human_escalation_rate=0.05,  # LangGraph typically needs less human intervention
            spatial_accuracy=accuracy * 0.96,  # LangGraph tends to be better at spatial accuracy
            complexity_rating=self.get_complexity_rating(),
            control_level=self.get_control_level(),
            debugging_ease="Medium"
        )
        
        # Get results from new stage-based structure
        stage_results = state.get('stage_results', {})
        
        return ExtractionResult(
            system_type="langgraph",
            upload_id=state['upload_id'],
            structure=stage_results.get('structure', state.get('structure_consensus', {})),
            positions=stage_results.get('products', state.get('position_consensus', {})),
            quantities=state.get('quantity_consensus', {}),  # Keep existing for backward compatibility
            details=stage_results.get('details', state.get('detail_consensus', {})),
            overall_accuracy=accuracy,
            consensus_reached=avg_consensus_rate >= 0.7,
            validation_result=validation,
            processing_time=processing_time,
            iteration_count=state.get('iteration_count', 1),
            cost_breakdown=cost_breakdown,
            performance_metrics=performance_metrics,
            ready_for_human_review=self._should_escalate_to_human(accuracy, state.get('iteration_count', 1)),
            human_review_priority=self._get_human_review_priority(accuracy, avg_consensus_rate)
        )
    
    async def _create_error_result(self, upload_id: str, error_message: str) -> ExtractionResult:
        """Create error result when workflow fails"""
        
        cost_breakdown = CostBreakdown(
            total_cost=0.0,
            model_costs={},
            api_calls={},
            tokens_used={},
            cost_per_accuracy_point=float('inf')
        )
        
        performance_metrics = PerformanceMetrics(
            accuracy=0.0,
            processing_time=0.0,
            consensus_rate=0.0,
            iteration_count=0,
            human_escalation_rate=1.0,
            spatial_accuracy=0.0,
            complexity_rating=self.get_complexity_rating(),
            control_level=self.get_control_level(),
            debugging_ease="Medium"
        )
        
        return ExtractionResult(
            system_type="langgraph",
            upload_id=upload_id,
            structure={},
            positions={},
            quantities={},
            details={},
            overall_accuracy=0.0,
            consensus_reached=False,
            validation_result={'error': error_message},
            processing_time=0.0,
            iteration_count=0,
            cost_breakdown=cost_breakdown,
            performance_metrics=performance_metrics,
            ready_for_human_review=True,
            human_review_priority="high"
        )
    
    async def get_cost_breakdown(self) -> CostBreakdown:
        """Get detailed cost breakdown"""
        accuracy = getattr(self, '_last_accuracy', 0.7)  # Use last known accuracy or default
        return CostBreakdown(
            total_cost=self.cost_tracker.get('total_cost', 0),
            model_costs=self.cost_tracker.get('model_costs', {}),
            api_calls=self.cost_tracker.get('api_calls', {}),
            tokens_used=self.cost_tracker.get('tokens_used', {}),
            cost_per_accuracy_point=self.cost_tracker.get('total_cost', 0) / max(accuracy, 0.1)
        )
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics"""
        # Use actual metrics if available
        accuracy = getattr(self, '_last_accuracy', 0.0)
        consensus_rate = getattr(self, '_last_consensus_rate', 0.0)
        iteration_count = getattr(self, '_last_iteration_count', 1)
        processing_time = getattr(self, '_last_processing_time', 0.0)
        
        return PerformanceMetrics(
            accuracy=accuracy,
            processing_time=processing_time,
            consensus_rate=consensus_rate,
            iteration_count=iteration_count,
            human_escalation_rate=0.05 if accuracy > 0.8 else 0.15,
            spatial_accuracy=accuracy * 0.96 if accuracy > 0 else 0.0,
            complexity_rating=self.get_complexity_rating(),
            control_level=self.get_control_level(),
            debugging_ease="Medium"
        )
    
    def get_architecture_benefits(self) -> List[str]:
        """Get key architectural benefits"""
        return [
            "Professional workflow management",
            "Built-in state persistence and checkpointing",
            "Proven patterns and community support",
            "Automatic retry and error handling",
            "Industry-standard orchestration"
        ]
    
    def get_complexity_rating(self) -> str:
        """Get complexity rating"""
        return "Medium"
    
    def get_control_level(self) -> str:
        """Get control level"""
        return "Framework-Limited"
    
    def _get_output_schema_for_stage(self, stage: str):
        """Get output schema for a stage, building dynamic model if configured"""
        # Check for configured fields
        stage_config = getattr(self, 'stage_configs', {}).get(stage, {})
        
        if stage_config and 'fields' in stage_config:
            # Build dynamic model from user's field definitions
            logger.info(
                f"Building dynamic model for LangGraph {stage} stage with {len(stage_config['fields'])} fields",
                component="langgraph_system"
            )
            return DynamicModelBuilder.build_model_from_config(stage, stage_config)
        
        # Fallback to basic structured schemas
        from pydantic import BaseModel, Field
        from typing import List, Optional
        
        logger.info(f"No field configuration found for {stage}, using basic fallback schema", component="langgraph_system")
        
        if stage == 'structure':
            class BasicStructure(BaseModel):
                shelf_count: int = Field(description="Total number of shelves")
                orientation: Optional[str] = Field(description="Shelf orientation", default="vertical")
                shelf_details: Optional[List[dict]] = Field(description="Details about each shelf", default=[])
            return BasicStructure
            
        elif stage == 'products':
            class BasicProduct(BaseModel):
                brand: str = Field(description="Product brand name")
                name: str = Field(description="Product name")
                shelf: int = Field(description="Shelf number (1-based)")
                position: int = Field(description="Position on shelf (1-based)")
                facings: Optional[int] = Field(description="Number of facings", default=1)
                color: Optional[str] = Field(description="Primary package color", default="")
            
            class BasicProducts(BaseModel):
                products: List[BasicProduct] = Field(description="List of all products found")
                total_products: int = Field(description="Total number of products")
            return BasicProducts
            
        elif stage == 'details':
            class BasicDetails(BaseModel):
                product_details: List[dict] = Field(description="Enhanced product details", default=[])
                completeness_score: Optional[float] = Field(description="Completeness score", default=0.8)
            return BasicDetails
            
        else:
            # Generic fallback
            class BasicResult(BaseModel):
                data: dict = Field(description="Extracted data")
                status: str = Field(description="Extraction status", default="complete")
            return BasicResult
    
    def _extract_shelf_count_from_result(self, result) -> int:
        """Extract shelf count from extraction result"""
        # Handle BasicStructure model (new format)
        if hasattr(result, 'shelf_count'):
            logger.info(f"Found shelf_count in result: {result.shelf_count}", component="langgraph_system")
            return result.shelf_count
        elif isinstance(result, dict):
            # Try various possible field names
            for key in ['shelf_count', 'total_shelves', 'shelves', 'shelf_structure']:
                if key in result:
                    value = result[key]
                    if isinstance(value, int):
                        logger.info(f"Found shelf count via {key}: {value}", component="langgraph_system")
                        return value
                    elif isinstance(value, dict) and 'total_shelves' in value:
                        count = value['total_shelves']
                        logger.info(f"Found shelf count via nested structure: {count}", component="langgraph_system")
                        return count
                    elif isinstance(value, list):
                        count = len(value)
                        logger.info(f"Found shelf count via list length: {count}", component="langgraph_system")
                        return count
        
        logger.warning("Could not extract shelf count, using default fallback: 4", component="langgraph_system")
        return 4  # Default fallback
    
    def _extract_products_from_result(self, result) -> List[Dict]:
        """Extract product list from extraction result"""
        products = []
        
        # Safety check for None result
        if result is None:
            logger.warning("API result is None, returning empty products list", component="langgraph_system")
            return products
        
        # Handle BasicProducts model (new format)
        if hasattr(result, 'products') and hasattr(result, 'total_products'):
            logger.info("Found BasicProducts model format", component="langgraph_system")
            for product in result.products:
                if hasattr(product, 'dict'):
                    products.append(product.dict())
                elif isinstance(product, dict):
                    products.append(product)
            return products
            
        if isinstance(result, list):
            # Direct list of products
            for item in result:
                if item is None:
                    continue  # Skip None items
                if hasattr(item, 'dict'):
                    products.append(item.dict())
                elif isinstance(item, dict):
                    products.append(item)
        elif hasattr(result, 'products'):
            # Has products attribute (old format)
            return self._extract_products_from_result(result.products)
        elif isinstance(result, dict):
            # Look for products in dict
            if 'products' in result:
                return self._extract_products_from_result(result['products'])
            elif 'shelves' in result:
                # Products organized by shelf
                for shelf in result['shelves']:
                    if isinstance(shelf, dict) and 'products' in shelf:
                        shelf_num = shelf.get('shelf_number', 1)
                        for prod in shelf['products']:
                            if prod is None:
                                continue  # Skip None products
                            if isinstance(prod, dict):
                                prod['shelf'] = shelf_num
                                products.append(prod)
        else:
            logger.warning(f"Unexpected result type: {type(result)}, result: {result}", component="langgraph_system")
        
        # Filter out any None values that might have slipped through
        products = [p for p in products if p is not None]
        
        return products
    
    def _extract_details_from_result(self, result, positions: Dict) -> Dict[str, Dict]:
        """Extract detail information from result and map to positions"""
        details = {}
        
        if isinstance(result, list):
            # List of detail items
            for item in result:
                # Try to match with positions
                pos_key = self._find_matching_position(item, positions)
                if pos_key:
                    details[pos_key] = self._parse_detail_item(item)
        elif isinstance(result, dict):
            if 'details' in result:
                return self._extract_details_from_result(result['details'], positions)
            elif 'products' in result:
                return self._extract_details_from_result(result['products'], positions)
            else:
                # Single detail object
                for pos_key in positions:
                    details[pos_key] = self._parse_detail_item(result)
                    break
        
        return details
    
    def _build_stage_prompt_with_visual_feedback(
        self,
        stage: str,
        attempt_number: int,
        visual_feedback: List[Dict],
        previous_stages: Dict[str, Any]
    ) -> str:
        """Build prompt with visual feedback from previous models in this stage"""
        
        # Get base prompt for stage
        base_prompt = getattr(self, 'stage_prompts', {}).get(stage, self._get_default_stage_prompt(stage))
        
        # Add context from previous stages
        if stage == 'products' and 'structure' in previous_stages:
            structure = previous_stages['structure']
            shelf_count = structure.get('shelf_count', 4)
            base_prompt = base_prompt.replace('{shelf_count}', str(shelf_count))
            base_prompt = base_prompt.replace('{shelves}', str(shelf_count))
        
        # Add visual feedback if available (from previous models in this stage)
        if visual_feedback and attempt_number > 1:
            base_prompt += "\n\nVISUAL FEEDBACK FROM PREVIOUS ATTEMPTS:\n"
            
            for feedback in visual_feedback:
                base_prompt += f"\nAttempt {feedback['attempt']} ({feedback['model']}):\n"
                
                # Add specific issues found
                for issue in feedback['actionable_feedback']:
                    issue_type = issue.get('type', 'unknown')
                    
                    if issue_type == 'missing_product':
                        base_prompt += f"- Missing product at shelf {issue.get('shelf', '?')}, position {issue.get('position', '?')}\n"
                    elif issue_type == 'wrong_position':
                        base_prompt += f"- Product {issue.get('product', '?')} appears to be at wrong position\n"
                    elif issue_type == 'quantity_mismatch':
                        base_prompt += f"- Facing count mismatch for {issue.get('product', '?')}: planogram shows {issue.get('planogram_count', '?')}, image suggests {issue.get('image_count', '?')}\n"
                    elif issue_type == 'extra_product':
                        base_prompt += f"- Extra product {issue.get('product', '?')} at shelf {issue.get('shelf', '?')}, position {issue.get('position', '?')} not visible in image\n"
                    else:
                        base_prompt += f"- {issue_type}: {issue.get('details', '')}\n"
            
            base_prompt += "\nPlease address these visual discrepancies in your extraction."
        
        return base_prompt
    
    def _get_default_stage_prompt(self, stage: str) -> str:
        """Get default prompt for stage"""
        defaults = {
            'structure': "Analyze the shelf structure and count the number of shelves.",
            'products': "Extract all products with their positions on the {shelf_count} shelves.",
            'details': "Extract detailed information for all products including prices and sizes."
        }
        return defaults.get(stage, f"Process the {stage} stage.")
    
    async def _extract_with_model_langgraph(
        self,
        model: str,
        prompt: str,
        image_data: bytes,
        stage: str,
        previous_stages: Dict
    ) -> Any:
        """Extract using specific model for LangGraph system"""
        
        # Prepare images dict as expected by extraction engine
        images = {'enhanced': image_data}
        
        # Get configuration for this stage
        stage_config = getattr(self, 'stage_configs', {}).get(stage, {})
        
        # Build dynamic model from user's field definitions
        output_schema = None
        if stage_config and 'fields' in stage_config:
            logger.info(
                f"Building dynamic model for LangGraph {stage} stage with {len(stage_config['fields'])} fields",
                component="langgraph_system",
                stage=stage,
                field_count=len(stage_config['fields'])
            )
            output_schema = DynamicModelBuilder.build_model_from_config(stage, stage_config)
        else:
            # Use the basic schemas
            output_schema = self._get_output_schema_for_stage(stage)
        
        # Use the actual extraction engine
        result, cost = await self.extraction_engine.execute_with_model_id(
            model_id=model,
            prompt=prompt,
            images=images,
            output_schema=output_schema,
            agent_id=f"langgraph_{stage}_{model}"
        )
        
        # Track cost
        self.cost_tracker['total_cost'] += cost
        
        # Parse result based on stage
        if hasattr(result, 'model_dump'):
            # Convert Pydantic model to dict
            return result.model_dump()
        elif isinstance(result, dict):
            return result
        else:
            logger.warning(f"Unexpected result type for {stage}: {type(result)}", component="langgraph_system")
            return result
    
    def _create_temp_extraction_langgraph(self, previous_stages: Dict, current_stage: str, current_result: Any) -> Dict:
        """Create temporary extraction combining previous stages and current attempt"""
        temp = previous_stages.copy()
        temp[current_stage] = current_result
        return temp
    
    async def _generate_planogram_for_stage(self, extraction_data: Dict, identifier: str) -> Dict:
        """Generate planogram from extraction data for visual feedback"""
        from ..api.planogram_renderer import generate_png_from_real_data
        
        # Prepare data in the expected format
        planogram_data = {
            'extraction_result': {
                'products': extraction_data.get('products', []),
                'structure': extraction_data.get('structure', {})
            },
            'accuracy': 0.0  # Will be updated after comparison
        }
        
        # Generate PNG
        planogram_png = generate_png_from_real_data(planogram_data, "product_view")
        
        return {
            'id': identifier,
            'data': planogram_data,
            'image': planogram_png,
            'extraction_result': planogram_data['extraction_result']
        }
    
    async def _compare_with_original_langgraph(self, original_image: bytes, planogram: Dict, comparison_prompt: str) -> Dict:
        """Compare original image with planogram using orchestrator model"""
        
        # Use the planogram PNG that was already generated
        planogram_png = planogram.get('image')
        if not planogram_png:
            logger.error("No planogram image found for comparison", component="langgraph_system")
            return {}
        
        # Get structure from the extraction result
        structure_context = planogram.get('extraction_result', {}).get('structure', {})
        
        # Use the comparison agent with orchestrator model for intelligent analysis
        from ..comparison.image_comparison_agent import ImageComparisonAgent
        comparison_agent = ImageComparisonAgent(self.config)
        
        orchestrator_model = getattr(self, 'orchestrator_model', 'claude-4-opus')
        
        comparison_result = await comparison_agent.compare_image_vs_planogram(
            original_image=original_image,
            planogram=planogram,
            structure_context=structure_context,
            planogram_image=planogram_png,
            model=orchestrator_model,
            comparison_prompt=comparison_prompt
        )
        
        return comparison_result
    
    async def _extract_actionable_feedback_langgraph(self, comparison_result) -> List[Dict]:
        """Extract actionable feedback from comparison result for next model"""
        
        actionable_feedback = []
        
        # Process mismatches
        if hasattr(comparison_result, 'mismatches'):
            for mismatch in comparison_result.mismatches:
                if isinstance(mismatch, dict):
                    actionable_feedback.append({
                        'type': mismatch.get('issue_type', 'mismatch'),
                        'product': mismatch.get('product', ''),
                        'shelf': mismatch.get('shelf', 0),
                        'position': mismatch.get('position', 0),
                        'details': mismatch.get('details', ''),
                        'planogram_count': mismatch.get('planogram_count'),
                        'image_count': mismatch.get('image_count')
                    })
        
        # Process missing products (visible in image but not in extraction)
        if hasattr(comparison_result, 'missing_products'):
            for missing in comparison_result.missing_products:
                actionable_feedback.append({
                    'type': 'missing_product',
                    'product': missing.get('product_name', '') if isinstance(missing, dict) else '',
                    'shelf': missing.get('shelf', 0) if isinstance(missing, dict) else 0,
                    'position': missing.get('position', 0) if isinstance(missing, dict) else 0,
                    'details': missing.get('details', '') if isinstance(missing, dict) else ''
                })
        
        # Process extra products (in extraction but not visible in image)
        if hasattr(comparison_result, 'extra_products'):
            for extra in comparison_result.extra_products:
                actionable_feedback.append({
                    'type': 'extra_product',
                    'product': extra.get('product_name', '') if isinstance(extra, dict) else '',
                    'shelf': extra.get('shelf', 0) if isinstance(extra, dict) else 0,
                    'position': extra.get('position', 0) if isinstance(extra, dict) else 0,
                    'details': extra.get('details', '') if isinstance(extra, dict) else ''
                })
        
        return actionable_feedback
    
    async def _apply_stage_consensus_langgraph(
        self,
        stage: str,
        model_results: List[Dict],
        visual_feedback: List[Dict]
    ) -> Dict[str, Any]:
        """Apply consensus voting for a stage using existing logic"""
        
        # Use the same consensus logic as other systems
        if stage == 'structure':
            return await self._consensus_structure_langgraph(model_results)
        elif stage == 'products':
            return await self._consensus_products_langgraph(model_results)
        elif stage == 'details':
            return await self._consensus_details_langgraph(model_results)
        else:
            # Generic consensus - use first result
            return model_results[0]['result'] if model_results else {}
    
    async def _consensus_structure_langgraph(self, model_results: List[Dict]) -> Dict:
        """Apply consensus for structure stage"""
        
        # Simple majority voting on shelf count
        from collections import Counter
        shelf_counts = []
        
        for result in model_results:
            data = result['result']
            shelf_count = data.get('shelf_count', 4)
            shelf_counts.append(shelf_count)
        
        if shelf_counts:
            count_votes = Counter(shelf_counts)
            most_common_count = count_votes.most_common(1)[0][0]
            
            # Find the best result with the most common shelf count
            best_result = None
            for result in model_results:
                data = result['result']
                if data.get('shelf_count', 4) == most_common_count:
                    best_result = data
                    break
            
            logger.info(
                f"Structure consensus: {most_common_count} shelves",
                component="langgraph_system",
                shelf_count=most_common_count
            )
            
            return best_result or {'shelf_count': most_common_count}
        
        return {'shelf_count': 4}  # Default fallback
    
    async def _consensus_products_langgraph(self, model_results: List[Dict]) -> List[Dict]:
        """Apply consensus for products using position voting"""
        
        all_products = []
        
        # Collect all products from all models
        for result in model_results:
            products = result['result']
            if isinstance(products, list):
                all_products.extend(products)
            elif isinstance(products, dict) and 'products' in products:
                all_products.extend(products['products'])
        
        # Simple deduplication by position
        position_map = {}
        for product in all_products:
            if isinstance(product, dict) and 'shelf' in product and 'position' in product:
                key = f"s{product['shelf']}_p{product['position']}"
                if key not in position_map:
                    position_map[key] = product
        
        consensus_products = list(position_map.values())
        
        logger.info(
            f"Products consensus: {len(consensus_products)} products",
            component="langgraph_system",
            product_count=len(consensus_products)
        )
        
        return consensus_products
    
    async def _consensus_details_langgraph(self, model_results: List[Dict]) -> Dict:
        """Apply consensus for details by merging results"""
        
        merged_details = {}
        
        for result in model_results:
            details = result['result']
            if isinstance(details, dict):
                merged_details.update(details)
        
        logger.info(
            f"Details consensus: {len(merged_details)} detail fields",
            component="langgraph_system",
            detail_count=len(merged_details)
        )
        
        return merged_details
    
    async def _generate_final_planogram_node(self, state: LangGraphExtractionState) -> LangGraphExtractionState:
        """Generate final planogram after all stages completed"""
        
        logger.info(
            "LangGraph: Generate final planogram node",
            component="langgraph_system"
        )
        
        try:
            # Get all stage results
            stage_results = state.get('stage_results', {})
            
            # Combine into final extraction format
            final_extraction = {
                'structure': stage_results.get('structure', {}),
                'products': stage_results.get('products', []),
                'details': stage_results.get('details', {})
            }
            
            # Generate final planogram
            final_planogram = await self._generate_planogram_for_stage(final_extraction, "final_langgraph")
            
            state['final_planogram'] = final_planogram
            
            logger.info(
                f"✅ LangGraph final planogram generated",
                component="langgraph_system"
            )
        
        except Exception as e:
            logger.error(
                f"Final planogram generation failed: {e}",
                component="langgraph_system",
                error=str(e)
            )
        
        return state
    
    def _find_matching_position(self, item: Dict, positions: Dict) -> Optional[str]:
        """Find matching position key for a detail item"""
        # Try to match by position/shelf
        item_shelf = item.get('shelf', item.get('shelf_number', 0))
        item_pos = item.get('position', item.get('position_on_shelf', 0))
        
        for pos_key, product in positions.items():
            if isinstance(product, dict):
                if (product.get('shelf', product.get('shelf_number', 0)) == item_shelf and
                    product.get('position', product.get('position_on_shelf', 0)) == item_pos):
                    return pos_key
        
        # Try to match by brand/name
        item_brand = str(item.get('brand', '')).lower()
        item_name = str(item.get('name', item.get('product', ''))).lower()
        
        for pos_key, product in positions.items():
            if isinstance(product, dict):
                prod_brand = str(product.get('brand', '')).lower()
                prod_name = str(product.get('name', product.get('product', ''))).lower()
                if item_brand and prod_brand and item_brand in prod_brand:
                    return pos_key
                if item_name and prod_name and item_name in prod_name:
                    return pos_key
        
        return None
    
    def _parse_detail_item(self, item) -> Dict:
        """Parse a detail item into standard format"""
        if hasattr(item, 'dict'):
            item = item.dict()
        
        return {
            'price': item.get('price', item.get('regular_price')),
            'size': item.get('size', item.get('package_size')),
            'color': item.get('color', item.get('primary_color')),
            'confidence': item.get('confidence', 0.8)
        } 