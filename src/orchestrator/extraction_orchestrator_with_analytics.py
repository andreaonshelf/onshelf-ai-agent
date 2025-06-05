"""
Enhanced Extraction Orchestrator with Full Analytics Integration
This shows how to integrate analytics tracking into the existing orchestrator
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from ..utils import logger
from .analytics_integration import OrchestrationAnalytics
from ..comparison.image_comparison_agent import ImageComparisonAgent
from ..api.planogram_renderer import generate_png_from_real_data


class AnalyticsIntegrationMixin:
    """Mixin to add analytics tracking to ExtractionOrchestrator"""
    
    def _init_analytics(self, extraction_run_id: str, queue_item_id: int):
        """Initialize analytics tracking"""
        self.analytics = OrchestrationAnalytics(extraction_run_id, queue_item_id)
        logger.info(
            "Analytics tracking initialized",
            component="extraction_orchestrator",
            run_id=extraction_run_id,
            queue_id=queue_item_id
        )
    
    async def _execute_shelf_with_analytics(self,
                                           shelf_num: int,
                                           images: Dict[str, bytes],
                                           models_for_stage: List[Dict],
                                           shelf_prompt_template: str,
                                           max_retries: int = 2,
                                           visual_comparison: bool = True) -> Dict:
        """Execute shelf extraction with full analytics tracking"""
        
        extraction_results = []
        visual_feedbacks = []
        
        for model_index, model_config in enumerate(models_for_stage):
            model_id = model_config['model_id']
            
            # Calculate attempt number based on retries
            for attempt in range(1, max_retries + 1):
                try:
                    # Prepare retry context
                    retry_context = {
                        'attempt': attempt,
                        'previous_errors': visual_feedbacks[-1] if visual_feedbacks else None,
                        'shelf_number': shelf_num,
                        'total_models': len(models_for_stage),
                        'model_index': model_index
                    }
                    
                    # Get visual feedback from previous model (if any)
                    visual_feedback = visual_feedbacks[-1] if visual_feedbacks and model_index > 0 else None
                    
                    # Process prompt with retry blocks
                    processed_prompt = self._process_retry_blocks(
                        shelf_prompt_template,
                        attempt,
                        retry_context
                    )
                    
                    # Add visual feedback to prompt if available
                    if visual_feedback and attempt > 1:
                        feedback_text = self._format_visual_feedback_for_prompt(visual_feedback)
                        processed_prompt += f"\n\nVISUAL FEEDBACK FROM PREVIOUS MODEL:\n{feedback_text}"
                    
                    # Track the extraction attempt
                    iteration_id = await self.analytics.track_products_extraction(
                        shelf_num=shelf_num,
                        model_id=model_id,
                        model_index=model_index,
                        attempt_number=attempt,
                        prompt_template=shelf_prompt_template,
                        processed_prompt=processed_prompt,
                        retry_context=retry_context,
                        visual_feedback=visual_feedback
                    )
                    
                    # Execute extraction
                    start_time = datetime.utcnow()
                    
                    result, api_cost = await self.extraction_engine.execute_with_model_id(
                        model_id=model_id,
                        prompt=processed_prompt,
                        images=images,
                        output_schema="List[ProductExtraction]",
                        agent_id=f"products_s{shelf_num}_m{model_index}"
                    )
                    
                    duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    
                    # Update iteration with results
                    await self.analytics.analytics.update_iteration_result(
                        iteration_id=iteration_id,
                        extraction_result={'products': [p.dict() for p in result]},
                        products_found=len(result),
                        accuracy_score=self._calculate_accuracy(result),
                        api_cost=api_cost,
                        tokens_used=self._estimate_tokens(processed_prompt, result),
                        duration_ms=duration_ms
                    )
                    
                    # Store result
                    extraction_results.append({
                        'model_id': model_id,
                        'model_index': model_index,
                        'products': result,
                        'iteration_id': iteration_id
                    })
                    
                    # Generate planogram and get visual feedback (if not last model)
                    if visual_comparison and model_index < len(models_for_stage) - 1:
                        planogram_data = await self._generate_planogram_for_analytics(result, shelf_num)
                        
                        comparison_result = await self.comparison_agent.compare_image_vs_planogram(
                            original_image=images['enhanced'],
                            planogram=planogram_data['image'],
                            comparison_model=self.comparison_model,
                            comparison_prompt=self.comparison_prompt
                        )
                        
                        # Track visual comparison
                        await self.analytics.track_visual_comparison(
                            iteration_id=iteration_id,
                            model_result={'products': len(result), 'shelf': shelf_num},
                            planogram_generated=True,
                            comparison_result=comparison_result.dict(),
                            comparison_model=self.comparison_model
                        )
                        
                        visual_feedbacks.append(comparison_result.dict())
                    
                    # Success - break retry loop
                    break
                    
                except Exception as e:
                    logger.error(
                        f"Model {model_id} failed on attempt {attempt}",
                        component="extraction_orchestrator",
                        error=str(e),
                        shelf=shelf_num
                    )
                    
                    # Track failure
                    await self.analytics.analytics._complete_iteration(
                        iteration_id,
                        success=False,
                        error_type=type(e).__name__,
                        error_message=str(e)
                    )
                    
                    if attempt == max_retries:
                        raise
        
        # Determine best result using existing consensus logic
        best_result = self._determine_best_result(extraction_results)
        
        # Track orchestrator decision
        await self.analytics.track_orchestrator_decision(
            iteration_id=best_result['iteration_id'],
            decision_type='consensus_selection',
            reasoning={
                'total_models': len(extraction_results),
                'selected_model': best_result['model_id'],
                'products_found': len(best_result['products']),
                'visual_feedback_used': len(visual_feedbacks) > 0
            }
        )
        
        return best_result
    
    async def _generate_planogram_for_analytics(self, products: List, shelf_num: int) -> Dict:
        """Generate planogram for visual comparison"""
        planogram_data = {
            'extraction_result': {
                'products': [p.dict() for p in products],
                'structure': {'shelves': [{'number': shelf_num}]}
            },
            'accuracy': 0.0
        }
        
        planogram_png = generate_png_from_real_data(planogram_data, "product_view")
        
        return {
            'data': planogram_data,
            'image': planogram_png
        }
    
    def _format_visual_feedback_for_prompt(self, feedback: Dict) -> str:
        """Format visual feedback for inclusion in prompt"""
        lines = []
        
        # High confidence issues first
        if feedback.get('high_confidence_issues'):
            lines.append("⚠️ HIGH CONFIDENCE ISSUES:")
            for issue in feedback['high_confidence_issues']:
                lines.append(f"- {issue['description']}")
        
        # Specific mismatches
        if feedback.get('shelf_mismatches'):
            lines.append("\n📍 SPECIFIC MISMATCHES:")
            for mismatch in feedback['shelf_mismatches'][:5]:  # Limit to prevent prompt overflow
                if mismatch['issue_type'] == 'missing':
                    lines.append(f"- Missing: {mismatch['product']} at shelf {mismatch['photo_location']['shelf']}, position {mismatch['photo_location']['position']}")
                elif mismatch['issue_type'] == 'wrong_shelf':
                    lines.append(f"- Wrong shelf: {mismatch['product']} shows on shelf {mismatch['planogram_location']['shelf']} but is on shelf {mismatch['photo_location']['shelf']}")
        
        # Overall assessment
        lines.append(f"\nOverall alignment: {feedback.get('overall_alignment', 'unknown')}")
        
        return "\n".join(lines)
    
    def _calculate_accuracy(self, products: List) -> float:
        """Calculate accuracy score for products"""
        if not products:
            return 0.0
        
        total_confidence = sum(p.extraction_confidence for p in products if hasattr(p, 'extraction_confidence'))
        return total_confidence / len(products) if products else 0.0
    
    def _estimate_tokens(self, prompt: str, result: Any) -> int:
        """Estimate token usage"""
        # Rough estimation: 1 token per 4 characters
        prompt_tokens = len(prompt) // 4
        result_tokens = len(json.dumps([r.dict() for r in result])) // 4 if result else 0
        return prompt_tokens + result_tokens