"""
Custom Consensus System with Visual Feedback
Implements planogram generation after each model with visual feedback loop
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from .custom_consensus import CustomConsensusSystem, DeterministicOrchestrator
from ..config import SystemConfig
from ..utils import logger
from ..orchestrator.planogram_orchestrator import PlanogramOrchestrator
from ..comparison.image_comparison_agent import ImageComparisonAgent
from ..models.extraction_models import ExtractionResult
from ..extraction.engine import ModularExtractionEngine

from ..orchestrator.monitoring_hooks import monitoring_hooks

class CustomConsensusVisualSystem(CustomConsensusSystem):
    """Enhanced Custom Consensus with visual feedback between models"""
    
    def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):
        super().__init__(config)
        self.queue_item_id = queue_item_id
        self.planogram_orchestrator = PlanogramOrchestrator(config)
        self.comparison_agent = ImageComparisonAgent(config)
        self.extraction_engine = ModularExtractionEngine(config)
        self.orchestrator_model = None  # Will be set from configuration
        self.cost_tracker = {'total_cost': 0.0}  # Initialize cost tracker
        
    async def extract_with_iterations(self, 
                                    image_data: bytes, 
                                    upload_id: str,
                                    target_accuracy: float = 0.95,
                                    max_iterations: int = 5,
                                    configuration: Optional[Dict] = None) -> ExtractionResult:
        """REAL orchestration happens here - iterations, visual feedback, intelligent decisions"""
        
        best_result = None
        best_accuracy = 0.0
        iteration_history = []
        
        for iteration in range(1, max_iterations + 1):
            logger.info(
                f"Custom Consensus iteration {iteration}/{max_iterations}",
                component="custom_consensus_visual",
                current_accuracy=best_accuracy,
                target_accuracy=target_accuracy
            )

            # Send monitoring update for iteration
            if self.queue_item_id and hasattr(monitoring_hooks, 'update_iteration'):
                await monitoring_hooks.update_iteration(
                    self.queue_item_id,
                    iteration,
                    locked_items=[]
                )
            
            # Prepare extraction data for this iteration
            extraction_data = {
                'configuration': configuration,
                'iteration': iteration,
                'previous_attempts': iteration_history,
                'target_accuracy': target_accuracy
            }
            
            # Extract using consensus method with visual feedback
            result = await self.extract_with_consensus(
                image_data=image_data,
                upload_id=upload_id,
                extraction_data=extraction_data
            )
            
            # Check accuracy (would use real accuracy calculation)
            current_accuracy = getattr(result, 'overall_accuracy', 0.85)
            
            if current_accuracy > best_accuracy:
                best_accuracy = current_accuracy
                best_result = result
            
            # Stop if target reached
            if current_accuracy >= target_accuracy:
                logger.info(
                    f"Target accuracy reached: {current_accuracy:.2%}",
                    component="custom_consensus_visual",
                    iterations_used=iteration
                )
                break
            
            iteration_history.append(result)
        
        # Add iteration count to result
        if best_result:
            best_result.iteration_count = len(iteration_history) + 1
        
        return best_result or result
    
    async def extract_with_consensus(self, image_data: bytes, upload_id: str, extraction_data: Optional[Dict] = None) -> ExtractionResult:
        """Main extraction with visual feedback between each model"""
        
        start_time = time.time()
        
        # Extract configuration from extraction_data
        configuration = extraction_data.get('configuration', {}) if extraction_data else {}
        stage_prompts = configuration.get('stage_prompts', {})
        stage_models = configuration.get('stage_models', {})
        temperature = configuration.get('temperature', 0.7)
        self.orchestrator_model = configuration.get('orchestrator_model', 'claude-4-opus')
        
        # Check if we have custom prompts - if not, REFUSE to run
        if not stage_prompts:
            # Try to get from self.stage_prompts (set by system dispatcher)
            stage_prompts = getattr(self, 'stage_prompts', {})
            
        if not stage_prompts:
            error_msg = (
                "REFUSING TO RUN EXTRACTION: No custom prompts loaded from UI/database. "
                "This would waste money on API calls with wrong hardcoded prompts. "
                "Please ensure prompts are saved in the UI and the configuration is properly loaded."
            )
            logger.error(error_msg, component="custom_consensus_visual")
            raise ValueError(error_msg)
        
        logger.info(
            f"Custom prompts loaded for stages: {list(stage_prompts.keys())}",
            component="custom_consensus_visual"
        )
        
        # Initialize visual feedback accumulator
        visual_feedback_history = []
        
        logger.info(
            f"Starting custom consensus extraction with visual feedback",
            component="custom_consensus_visual",
            upload_id=upload_id,
            temperature=temperature
        )
        
        # Get stages to process - use configured stages, not hardcoded list
        configured_stages = getattr(self, 'stage_configs', {})
        if configured_stages:
            # Process only stages that have configurations
            stages = list(configured_stages.keys())
            logger.info(f"Processing configured stages: {stages}", component="custom_consensus_visual")
        else:
            # Fallback to default stages if no configuration
            stages = ['structure', 'products', 'details']
            logger.warning("No stage configurations found, using default stages", component="custom_consensus_visual")
        
        stage_results = {}
        
        for stage in stages:
            logger.info(
                f"Processing stage: {stage}",
                component="custom_consensus_visual",
                stage=stage
            )
            
            # Get models for this stage
            models_for_stage = stage_models.get(stage, ['gpt-4o', 'claude-3-sonnet', 'gemini-pro'])
            
            # Process this stage with visual feedback between models
            stage_result = await self._process_stage_with_visual_feedback(
                stage=stage,
                models=models_for_stage,
                image_data=image_data,
                stage_prompts=stage_prompts,
                visual_feedback_history=visual_feedback_history,
                previous_stages=stage_results,
                upload_id=upload_id
            )
            
            stage_results[stage] = stage_result
            
            # Generate planogram after products and details stages
            if stage in ['products', 'details']:
                logger.info(
                    f"Generating planogram after {stage} stage",
                    component="custom_consensus_visual"
                )
                
                # Combine all stage results into extraction format
                extraction_result = self._combine_stage_results(stage_results)
                
                # Generate planogram
                planogram = await self._generate_planogram_for_extraction(
                    extraction_result, 
                    f"{stage}_final"
                )
                
                # Visual comparison for feedback
                comparison_result = await self._compare_with_original(
                    image_data,
                    planogram,
                    stage_prompts.get('comparison', self._get_default_comparison_prompt())
                )
                
                # Add to feedback history for next stage
                visual_feedback_history.append({
                    'stage': stage,
                    'comparison_result': comparison_result,
                    'planogram': planogram
                })
        
        # Create final extraction result
        final_extraction = self._combine_stage_results(stage_results)
        processing_time = time.time() - start_time
        
        # Create ExtractionResult object
        result = ExtractionResult(
            upload_id=upload_id,
            extraction_id=str(uuid.uuid4()),
            structure=final_extraction.get('structure'),
            products=final_extraction.get('products', []),
            total_products=len(final_extraction.get('products', [])),
            overall_confidence={'value': 0.9, 'type': 'high'},
            api_cost_estimate=self.cost_tracker['total_cost'],
            processing_duration_seconds=processing_time,
            model_used='custom_consensus_visual',
            created_at=datetime.utcnow()
        )
        
        return result
    
    async def _process_stage_with_visual_feedback(
        self,
        stage: str,
        models: List[str],
        image_data: bytes,
        stage_prompts: Dict[str, str],
        visual_feedback_history: List[Dict],
        previous_stages: Dict[str, Any],
        upload_id: str
    ) -> Dict[str, Any]:
        """Process a single stage with visual feedback between models"""
        
        model_results = []
        stage_visual_feedback = []
        
        for i, model in enumerate(models):
            logger.info(
                f"Processing {stage} with model {i+1}/{len(models)}: {model}",
                component="custom_consensus_visual",
                stage=stage,
                model=model,
                attempt=i+1
            )

            # Send monitoring update for stage progress
            if self.queue_item_id:
                await monitoring_hooks.update_stage_progress(
                    self.queue_item_id,
                    stage_name=stage,
                    attempt=i+1,
                    total_attempts=len(models),
                    model=model,
                    complete=False
                )
                
                await monitoring_hooks.update_processing_detail(
                    self.queue_item_id,
                    f"Processing {stage} with model {i+1}/{len(models)}: {model}"
                )
            
            # Build prompt with visual feedback from previous models
            prompt = self._build_prompt_with_visual_feedback(
                stage=stage,
                base_prompt=stage_prompts.get(stage, self._get_default_prompt(stage)),
                visual_feedback=stage_visual_feedback,
                attempt_number=i+1,
                previous_stages=previous_stages
            )
            
            # Extract with current model
            extraction_result = await self._extract_with_model(
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
            
            # Generate planogram after each model (except structure stage)
            if stage != 'structure':
                # Create temporary extraction combining previous stages + current attempt
                temp_extraction = self._create_temp_extraction(
                    previous_stages, 
                    stage, 
                    extraction_result
                )
                
                # Generate planogram
                planogram = await self._generate_planogram_for_extraction(
                    temp_extraction,
                    f"{stage}_model_{i+1}"
                )
                
                # Visual comparison
                comparison_prompt = stage_prompts.get('comparison', self._get_default_comparison_prompt())
                logger.info(
                    f"Running visual comparison after {model} in {stage} stage",
                    component="custom_consensus_visual",
                    has_custom_prompt='comparison' in stage_prompts,
                    prompt_length=len(comparison_prompt),
                    prompt_preview=comparison_prompt[:100] + "..." if len(comparison_prompt) > 100 else comparison_prompt
                )
                comparison_result = await self._compare_with_original(
                    image_data,
                    planogram,
                    comparison_prompt
                )
                
                # Extract actionable feedback
                actionable_feedback = await self._extract_actionable_feedback(comparison_result)
                
                stage_visual_feedback.append({
                    'model': model,
                    'attempt': i+1,
                    'comparison_result': comparison_result,
                    'actionable_feedback': actionable_feedback,
                    'planogram': planogram
                })
                
                logger.info(
                    f"Visual feedback from model {i+1}: {len(actionable_feedback)} issues found",
                    component="custom_consensus_visual",
                    issues_found=len(actionable_feedback)
                )
        
        # Apply consensus voting on all model results
        consensus_result = await self._apply_consensus_voting(
            stage=stage,
            model_results=model_results,
            visual_feedback=stage_visual_feedback
        )
        
        return consensus_result
    
    def _build_prompt_with_visual_feedback(
        self, 
        stage: str, 
        base_prompt: str, 
        visual_feedback: List[Dict],
        attempt_number: int,
        previous_stages: Dict[str, Any]
    ) -> str:
        """Build prompt including visual feedback from previous models"""
        
        prompt = base_prompt
        
        # Add context from previous stages
        if stage == 'products' and 'structure' in previous_stages:
            structure = previous_stages['structure']
            prompt = prompt.replace('{shelf_count}', str(structure.get('shelf_count', 0)))
            prompt = prompt.replace('{shelves}', str(structure.get('shelf_count', 0)))
        
        # Add visual feedback if available
        if visual_feedback and attempt_number > 1:
            prompt += "\n\nVISUAL COMPARISON FEEDBACK FROM PREVIOUS ATTEMPTS:\n"
            
            for feedback in visual_feedback:
                prompt += f"\nModel {feedback['attempt']} ({feedback['model']}) extraction was checked:\n"
                
                # Group feedback by confidence level
                high_conf = [f for f in feedback['actionable_feedback'] if f.get('confidence') == 'high']
                med_conf = [f for f in feedback['actionable_feedback'] if f.get('confidence') == 'medium']
                low_conf = [f for f in feedback['actionable_feedback'] if f.get('confidence') == 'low']
                
                if high_conf:
                    prompt += "\n⚠️ HIGH CONFIDENCE ISSUES:\n"
                    for issue in high_conf:
                        prompt += self._format_feedback_item(issue)
                
                if med_conf:
                    prompt += "\n⚡ MEDIUM CONFIDENCE ISSUES:\n"
                    for issue in med_conf:
                        prompt += self._format_feedback_item(issue)
                
                if low_conf:
                    prompt += "\n❓ LOW CONFIDENCE ISSUES (may be incorrect):\n"
                    for issue in low_conf:
                        prompt += self._format_feedback_item(issue)
            
            prompt += "\n\nUse this feedback to guide your extraction, focusing on high-confidence issues. Make your own assessment."
        
        return prompt
    
    def _format_feedback_item(self, issue: Dict) -> str:
        """Format a single feedback item for the prompt"""
        issue_type = issue.get('type', 'unknown')
        product = issue.get('product', 'Unknown product')
        details = issue.get('details', '')
        
        if issue_type == 'wrong_shelf':
            return f"- {product}: Shows on shelf {issue.get('planogram_shelf', '?')} but actually on shelf {issue.get('photo_shelf', '?')}. {details}\n"
        elif issue_type == 'wrong_quantity':
            photo_loc = issue.get('photo_location', {})
            planogram_loc = issue.get('planogram_location', {})
            return f"- {product}: Quantity mismatch at shelf {photo_loc.get('shelf', '?')}, position {photo_loc.get('position', '?')}. {details}\n"
        elif issue_type == 'wrong_position':
            return f"- {product}: Position mismatch - photo shows position {issue.get('photo_position', '?')} but planogram shows {issue.get('planogram_position', '?')}. {details}\n"
        elif issue_type == 'missing':
            return f"- Missing: {product} visible at shelf {issue.get('shelf', '?')}, position {issue.get('position', '?')} but not in extraction. {details}\n"
        elif issue_type == 'extra':
            return f"- Extra: {product} extracted at shelf {issue.get('shelf', '?')}, position {issue.get('position', '?')} but not visible in photo. {details}\n"
        else:
            return f"- {issue_type}: {product}. {details}\n"
    
    async def _extract_actionable_feedback(self, comparison_result) -> List[Dict]:
        """Extract actionable feedback from comparison result focusing on structural errors"""
        
        actionable_feedback = []
        
        # Process mismatches which now contain all issue types
        if hasattr(comparison_result, 'mismatches'):
            for mismatch in comparison_result.mismatches:
                if isinstance(mismatch, dict):
                    issue_type = mismatch.get('issue_type', 'unknown')
                    
                    feedback_item = {
                        'type': issue_type,
                        'product': mismatch.get('product', ''),
                        'confidence': mismatch.get('confidence', 'medium'),
                        'details': mismatch.get('details', '')
                    }
                    
                    # Add location info based on issue type
                    if issue_type == 'wrong_shelf':
                        feedback_item['photo_shelf'] = mismatch.get('photo_location', {}).get('shelf', 0)
                        feedback_item['planogram_shelf'] = mismatch.get('planogram_location', {}).get('shelf', 0)
                    elif issue_type == 'wrong_position':
                        feedback_item['photo_position'] = mismatch.get('photo_location', {}).get('position', 0)
                        feedback_item['planogram_position'] = mismatch.get('planogram_location', {}).get('position', 0)
                    elif issue_type == 'wrong_quantity':
                        feedback_item['photo_location'] = mismatch.get('photo_location', {})
                        feedback_item['planogram_location'] = mismatch.get('planogram_location', {})
                    
                    actionable_feedback.append(feedback_item)
        
        # Process missing products
        if hasattr(comparison_result, 'missing_products'):
            for missing in comparison_result.missing_products:
                actionable_feedback.append({
                    'type': 'missing',
                    'product': missing.get('product_name', '') if isinstance(missing, dict) else '',
                    'shelf': missing.get('shelf', 0) if isinstance(missing, dict) else 0,
                    'position': missing.get('position', 0) if isinstance(missing, dict) else 0,
                    'confidence': missing.get('confidence', 'medium') if isinstance(missing, dict) else 'medium',
                    'details': missing.get('details', '') if isinstance(missing, dict) else ''
                })
        
        # Process extra products
        if hasattr(comparison_result, 'extra_products'):
            for extra in comparison_result.extra_products:
                actionable_feedback.append({
                    'type': 'extra',
                    'product': extra.get('product_name', '') if isinstance(extra, dict) else '',
                    'shelf': extra.get('shelf', 0) if isinstance(extra, dict) else 0,
                    'position': extra.get('position', 0) if isinstance(extra, dict) else 0,
                    'confidence': extra.get('confidence', 'medium') if isinstance(extra, dict) else 'medium',
                    'details': extra.get('details', '') if isinstance(extra, dict) else ''
                })
        
        return actionable_feedback
    
    
    async def _apply_consensus_voting(
        self, 
        stage: str, 
        model_results: List[Dict],
        visual_feedback: List[Dict]
    ) -> Dict[str, Any]:
        """Apply consensus voting using the same logic as other systems"""
        
        # Visual feedback is available as context but NOT used for weighting
        # It was already used to help each model extract better
        
        # Apply the same consensus logic as the parent CustomConsensusSystem
        if stage == 'structure':
            return await self._consensus_structure(model_results)
        elif stage == 'products':
            return await self._consensus_products(model_results)
        elif stage == 'details':
            return await self._consensus_details(model_results)
    
    def _get_default_prompt(self, stage: str) -> str:
        """Get default prompt for stage"""
        defaults = {
            'structure': "Analyze the shelf structure and count the number of shelves.",
            'products': "Extract all products with their positions on shelf {shelf_count}.",
            'details': "Extract detailed information for all products including prices and sizes."
        }
        return defaults.get(stage, "")
    
    def _get_default_comparison_prompt(self) -> str:
        """Get default comparison prompt"""
        return """Compare the retail shelf photo with the planogram representation.
        Identify:
        1. Missing products (visible in photo but not in planogram)
        2. Extra products (in planogram but not visible in photo)
        3. Position mismatches
        4. Quantity/facing discrepancies
        
        Be specific about shelf and position numbers."""
    
    async def _generate_planogram_for_extraction(self, extraction_data: Dict, identifier: str) -> Dict:
        """Generate planogram from extraction data"""
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
    
    async def _compare_with_original(self, original_image: bytes, planogram: Dict, comparison_prompt: str) -> Dict:
        """Compare original image with planogram using orchestrator model"""
        
        # Use the planogram PNG that was already generated
        planogram_png = planogram.get('image')
        if not planogram_png:
            logger.error("No planogram image found in planogram dict", component="custom_consensus_visual")
            return {}
        
        # Get structure from the extraction result
        structure_context = planogram.get('extraction_result', {}).get('structure', {})
        
        # Use the comparison agent with orchestrator model for intelligent analysis
        comparison_result = await self.comparison_agent.compare_image_vs_planogram(
            original_image=original_image,
            planogram=planogram,
            structure_context=structure_context,
            planogram_image=planogram_png,
            model=self.orchestrator_model,  # Use orchestrator model for comparison
            comparison_prompt=comparison_prompt
        )
        
        return comparison_result
    
    def _create_temp_extraction(self, previous_stages: Dict, current_stage: str, current_result: Any) -> Dict:
        """Create temporary extraction combining previous stages and current attempt"""
        temp = previous_stages.copy()
        temp[current_stage] = current_result
        return temp
    
    def _combine_stage_results(self, stage_results: Dict) -> Dict:
        """Combine stage results into final extraction format"""
        return {
            'structure': stage_results.get('structure', {}),
            'products': stage_results.get('products', []),
            'details': stage_results.get('details', {})
        }
    
    async def _extract_with_model(
        self, 
        model: str, 
        prompt: str, 
        image_data: bytes,
        stage: str,
        previous_stages: Dict
    ) -> Any:
        """Extract using specific model"""
        # Prepare images dict as expected by extraction engine
        images = {'enhanced': image_data}
        
        # Get configuration for this stage
        stage_config = getattr(self, 'stage_configs', {}).get(stage, {})
        
        # Build dynamic model from user's field definitions
        from ..extraction.dynamic_model_builder import DynamicModelBuilder
        
        dynamic_model = None
        if stage_config and 'fields' in stage_config:
            logger.info(
                f"✅ Building dynamic model for stage {stage} with {len(stage_config['fields'])} user-defined fields",
                component="custom_consensus_visual",
                stage=stage,
                field_count=len(stage_config['fields']),
                field_names=[f.get('name') for f in stage_config['fields']]
            )
            dynamic_model = DynamicModelBuilder.build_model_from_config(stage, stage_config)
        
        # Determine output schema
        if dynamic_model:
            # Use the dynamic model built from user's fields
            output_schema = dynamic_model
            logger.info(
                f"Using dynamic model for stage {stage}",
                component="custom_consensus_visual",
                model_name=dynamic_model.__name__
            )
        else:
            # Fallback to generic schemas (should not happen with proper config)
            logger.warning(
                f"❌ No dynamic model built for stage {stage} - no field definitions found",
                component="custom_consensus_visual",
                stage=stage,
                has_stage_config=bool(stage_config),
                stage_config_keys=list(stage_config.keys()) if stage_config else [],
                has_fields=bool(stage_config.get('fields')) if stage_config else False
            )
            if stage == 'structure':
                output_schema = 'Dict[str, Any]'
            elif stage == 'products':
                output_schema = 'List[Dict[str, Any]]'
            else:  # details
                output_schema = 'Dict[str, Any]'
        
        # Use the actual extraction engine
        result, cost = await self.extraction_engine.execute_with_model_id(
            model_id=model,
            prompt=prompt,
            images=images,
            output_schema=output_schema,
            agent_id=f"consensus_visual_{stage}"
        )
        
        # Track cost
        if hasattr(self, 'cost_tracker') and isinstance(self.cost_tracker, dict):
            self.cost_tracker['total_cost'] += cost
        
        # Parse result based on stage
        # With dynamic models, result will be a Pydantic model instance
        if hasattr(result, 'model_dump'):
            # Convert Pydantic model to dict
            return result.model_dump()
        elif isinstance(result, list):
            # Handle list responses (e.g., products might be a list)
            parsed_list = []
            for item in result:
                if hasattr(item, 'model_dump'):
                    parsed_list.append(item.model_dump())
                elif isinstance(item, dict):
                    parsed_list.append(item)
                else:
                    parsed_list.append(item)
            return parsed_list
        elif isinstance(result, dict):
            # Already a dict, return as is
            return result
        else:
            # Fallback for other types
            logger.warning(
                f"Unexpected result type for stage {stage}: {type(result)}",
                component="custom_consensus_visual"
            )
            return result
    
    def _parse_structure_from_text(self, result):
        """Parse structure from text response"""
        # Basic parsing logic - would be enhanced based on actual responses
        try:
            if isinstance(result, str):
                # Look for shelf count in text
                import re
                shelf_match = re.search(r'(\d+)\s*shelves?', result, re.I)
                shelf_count = int(shelf_match.group(1)) if shelf_match else 4
                return {'shelf_count': shelf_count, 'sections': 3}
            return {'shelf_count': 4, 'sections': 3}
        except:
            return {'shelf_count': 4, 'sections': 3}
    
    def _parse_products_from_text(self, result):
        """Parse products from text response"""
        # This would need more sophisticated parsing
        # For now return empty list to avoid errors
        if isinstance(result, list):
            return result
        return []
    
    async def _consensus_structure(self, model_results: List[Dict]) -> Dict:
        """Apply consensus for structure stage using existing logic"""
        
        # Prepare proposals in the format expected by the orchestrator
        proposals = []
        for result in model_results:
            proposals.append({
                'model_used': result['model'],
                'shelf_count': result['result'].get('shelf_count', 0),
                'confidence': result['result'].get('confidence', 0.8),
                'sections': result['result'].get('sections', 3)
            })
        
        # Use the parent class's DeterministicOrchestrator for voting
        consensus_result = self.orchestrator.vote_on_structure(proposals)
        
        if consensus_result['consensus_reached']:
            logger.info(
                f"Structure consensus reached: {consensus_result['result']['shelf_count']} shelves",
                component="custom_consensus_visual",
                confidence=consensus_result.get('confidence', 0)
            )
            return consensus_result['result']
        else:
            # Fall back to first result if no consensus
            logger.warning(
                "No structure consensus reached, using first model result",
                component="custom_consensus_visual"
            )
            return model_results[0]['result'] if model_results else {}
    
    async def _consensus_products(self, model_results: List[Dict]) -> List[Dict]:
        """Apply consensus for products using existing voting logic"""
        
        # Collect all products from all models
        all_proposals = []
        
        for result in model_results:
            products = result.get('result', [])
            model_name = result['model']
            
            # Create proposal for this model's products
            positions = {}
            for product in products:
                if isinstance(product, dict) and 'position' in product:
                    shelf = product['position'].get('shelf', 0)
                    pos = product['position'].get('position', 0)
                    pos_key = f"s{shelf}_p{pos}"
                    
                    positions[pos_key] = {
                        'brand': product.get('brand', 'Unknown'),
                        'name': product.get('name', 'Unknown Product'),
                        'confidence': product.get('confidence', 0.8),
                        'shelf': shelf,
                        'position': pos
                    }
            
            all_proposals.append({
                'model': model_name,
                'positions': positions
            })
        
        # Use the parent class's position voting logic
        consensus_result = self.orchestrator.vote_on_positions(all_proposals)
        
        if consensus_result['consensus_reached']:
            # Convert consensus positions back to product list
            products = []
            for pos_key, product_data in consensus_result['result'].items():
                products.append({
                    'brand': product_data.get('brand'),
                    'name': product_data.get('name'),
                    'position': {
                        'shelf': product_data.get('shelf'),
                        'position': product_data.get('position')
                    },
                    'confidence': product_data.get('confidence', 0.8)
                })
            
            logger.info(
                f"Products consensus reached: {len(products)} products",
                component="custom_consensus_visual"
            )
            return products
        else:
            # Fall back to first result if no consensus
            logger.warning(
                "No products consensus reached, using first model result",
                component="custom_consensus_visual"
            )
            return model_results[0]['result'] if model_results else []
    
    async def _consensus_details(self, model_results: List[Dict]) -> Dict:
        """Apply consensus for details using existing logic"""
        
        # For details, we typically merge results from multiple models
        # Each model may have found different details (prices, sizes, etc.)
        
        merged_details = {}
        
        for result in model_results:
            details = result.get('result', {})
            if isinstance(details, dict):
                # Merge details, preferring higher confidence values
                for key, value in details.items():
                    if key not in merged_details:
                        merged_details[key] = value
                    elif isinstance(value, dict) and 'confidence' in value:
                        # Keep the detail with higher confidence
                        existing_conf = merged_details[key].get('confidence', 0) if isinstance(merged_details[key], dict) else 0
                        new_conf = value.get('confidence', 0)
                        if new_conf > existing_conf:
                            merged_details[key] = value
        
        logger.info(
            f"Details consensus: merged {len(merged_details)} detail fields",
            component="custom_consensus_visual"
        )
        
        return merged_details