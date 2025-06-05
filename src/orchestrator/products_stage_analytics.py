"""
Enhanced Products Stage with Full Analytics Tracking
Shows how to integrate comprehensive prompt tracking
"""

async def execute_products_with_analytics(self,
                                         shelf_num: int,
                                         model_id: str,
                                         model_index: int,
                                         attempt_number: int,
                                         shelf_prompt_template: str,
                                         retry_context: Dict,
                                         visual_feedback: Optional[Dict],
                                         analytics: OrchestrationAnalytics):
    """Execute products extraction with full analytics tracking"""
    
    # Process {IF_RETRY} blocks
    processed_prompt = self.process_retry_blocks(
        shelf_prompt_template, 
        attempt_number, 
        retry_context
    )
    
    # Add visual feedback to prompt if available
    if visual_feedback and attempt_number > 1:
        feedback_text = self._format_visual_feedback_for_prompt(visual_feedback)
        processed_prompt += f"\n\nVISUAL FEEDBACK FROM PREVIOUS MODEL:\n{feedback_text}"
    
    # Track the extraction attempt
    iteration_id = await analytics.track_products_extraction(
        shelf_num=shelf_num,
        model_id=model_id,
        model_index=model_index,
        attempt_number=attempt_number,
        prompt_template=shelf_prompt_template,
        processed_prompt=processed_prompt,
        retry_context=retry_context,
        visual_feedback=visual_feedback
    )
    
    try:
        # Execute the extraction
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
        await analytics.analytics.update_iteration_result(
            iteration_id=iteration_id,
            extraction_result={'products': [p.dict() for p in result]},
            products_found=len(result),
            accuracy_score=self._calculate_accuracy(result),
            api_cost=api_cost,
            tokens_used=self._estimate_tokens(processed_prompt, result)
        )
        
        # Generate planogram and get visual feedback (if not last model)
        if model_index < len(models_for_stage):
            planogram = await self._generate_planogram(result)
            
            comparison_result = await self.comparison_agent.compare_image_vs_planogram(
                original_image=images['enhanced'],
                planogram=planogram,
                comparison_model=self.comparison_model,
                comparison_prompt=self.comparison_prompt
            )
            
            # Track visual comparison
            await analytics.track_visual_comparison(
                iteration_id=iteration_id,
                model_result={'products': len(result)},
                planogram_generated=True,
                comparison_result=comparison_result.dict(),
                comparison_model=self.comparison_model
            )
            
            # Return feedback for next model
            return result, comparison_result
        
        return result, None
        
    except Exception as e:
        # Track failure
        await analytics.analytics._complete_iteration(
            iteration_id,
            success=False,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise


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