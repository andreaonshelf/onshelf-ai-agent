"""
Analytics Integration for Extraction Orchestrator
Provides detailed tracking of prompts, retry contexts, and visual feedback
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..utils import logger
from ..utils.extraction_analytics import get_extraction_analytics


class OrchestrationAnalytics:
    """Enhanced analytics tracking for extraction orchestration"""
    
    def __init__(self, extraction_run_id: str, queue_item_id: int):
        self.extraction_run_id = extraction_run_id
        self.queue_item_id = queue_item_id
        self.analytics = get_extraction_analytics()
        self._active_iterations = {}
        
    async def track_products_extraction(self,
                                      shelf_num: int,
                                      model_id: str,
                                      model_index: int,
                                      attempt_number: int,
                                      prompt_template: str,
                                      processed_prompt: str,
                                      retry_context: Dict,
                                      visual_feedback: Optional[Dict] = None) -> int:
        """Track a products extraction attempt with full prompt details"""
        
        # Identify which retry blocks were activated
        retry_blocks_activated = self._identify_retry_blocks(
            prompt_template, 
            processed_prompt, 
            attempt_number
        )
        
        # Start tracking
        iteration_data = {
            'extraction_run_id': self.extraction_run_id,
            'queue_item_id': self.queue_item_id,
            'iteration_number': attempt_number,
            'stage': 'products',
            'model_used': model_id,
            'model_index': model_index,
            'actual_prompt': processed_prompt,
            'retry_context': retry_context,
            'visual_feedback_received': visual_feedback,
            
            # Enhanced tracking
            'prompt_metadata': {
                'template_length': len(prompt_template),
                'processed_length': len(processed_prompt),
                'retry_blocks_activated': retry_blocks_activated,
                'shelf_number': shelf_num,
                'has_visual_feedback': visual_feedback is not None
            }
        }
        
        # Store for detailed analysis
        iteration_id = await self._store_iteration(iteration_data)
        
        logger.info(
            f"Tracking products extraction",
            component="orchestration_analytics",
            iteration_id=iteration_id,
            model=model_id,
            shelf=shelf_num,
            retry_blocks=len(retry_blocks_activated),
            prompt_length=len(processed_prompt)
        )
        
        return iteration_id
    
    def _identify_retry_blocks(self, 
                              template: str, 
                              processed: str, 
                              attempt: int) -> List[str]:
        """Identify which {IF_RETRY} blocks were activated"""
        
        activated = []
        
        # Check for retry 2 blocks
        if attempt >= 2 and "{IF_RETRY 2}" in template:
            if "Focus on edges" in processed or "missing items" in processed:
                activated.append("retry_2_edges")
                
        # Check for retry 3 blocks
        if attempt >= 3 and "{IF_RETRY 3}" in template:
            if "previous attempts" in processed.lower():
                activated.append("retry_3_cumulative")
                
        # Check for visual feedback insertion
        if "VISUAL FEEDBACK FROM PREVIOUS" in processed:
            activated.append("visual_feedback_context")
            
        return activated
    
    async def track_visual_comparison(self,
                                    iteration_id: int,
                                    model_result: Dict,
                                    planogram_generated: bool,
                                    comparison_result: Dict,
                                    comparison_model: str):
        """Track visual comparison after model extraction"""
        
        comparison_data = {
            'comparison_model': comparison_model,
            'planogram_generated': planogram_generated,
            'comparison_result': comparison_result,
            'issues_found': len(comparison_result.get('shelf_mismatches', [])),
            'critical_issues': comparison_result.get('critical_issues', []),
            'overall_alignment': comparison_result.get('overall_alignment', 'unknown')
        }
        
        await self.analytics.log_visual_comparison(
            iteration_id,
            comparison_data,
            planogram_generated
        )
        
        logger.info(
            f"Tracked visual comparison",
            component="orchestration_analytics",
            iteration_id=iteration_id,
            issues_found=comparison_data['issues_found'],
            alignment=comparison_data['overall_alignment']
        )
    
    async def track_orchestrator_decision(self,
                                        iteration_id: int,
                                        decision_type: str,
                                        reasoning: Dict,
                                        retry_reason: Optional[str] = None):
        """Track orchestrator's decision-making process"""
        
        decision = {
            'timestamp': datetime.utcnow().isoformat(),
            'decision_type': decision_type,  # 'retry', 'continue', 'stop'
            'reasoning': reasoning,
            'factors_considered': {
                'current_accuracy': reasoning.get('accuracy'),
                'target_threshold': reasoning.get('threshold'),
                'attempts_made': reasoning.get('attempts'),
                'cost_so_far': reasoning.get('cost'),
                'time_elapsed': reasoning.get('duration_ms')
            }
        }
        
        await self.analytics.log_orchestrator_decision(
            iteration_id,
            decision,
            retry_reason
        )
    
    async def _store_iteration(self, iteration_data: Dict) -> int:
        """Store iteration with enhanced prompt tracking"""
        
        async with self.analytics.db_pool.acquire() as conn:
            # Store the full iteration data
            iteration_id = await conn.fetchval("""
                INSERT INTO iterations (
                    extraction_run_id, queue_item_id, iteration_number,
                    stage, model_used, model_index, 
                    actual_prompt, retry_context, visual_feedback_received,
                    status, started_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'started', NOW())
                RETURNING id
            """, 
                iteration_data['extraction_run_id'],
                iteration_data['queue_item_id'],
                iteration_data['iteration_number'],
                iteration_data['stage'],
                iteration_data['model_used'],
                iteration_data['model_index'],
                iteration_data['actual_prompt'],
                json.dumps(iteration_data['retry_context']),
                json.dumps(iteration_data['visual_feedback_received']) if iteration_data['visual_feedback_received'] else None
            )
            
            # Store additional prompt metadata separately for analysis
            await conn.execute("""
                INSERT INTO prompt_execution_log (
                    iteration_id,
                    prompt_template_hash,
                    retry_blocks_activated,
                    prompt_metadata
                ) VALUES ($1, $2, $3, $4)
            """, 
                iteration_id,
                hash(iteration_data.get('prompt_template', '')),
                iteration_data['prompt_metadata']['retry_blocks_activated'],
                json.dumps(iteration_data['prompt_metadata'])
            )
            
        return iteration_id
    
    async def get_prompt_execution_history(self, 
                                         stage: Optional[str] = None,
                                         model: Optional[str] = None) -> List[Dict]:
        """Get detailed prompt execution history for analysis"""
        
        query = """
            SELECT 
                i.id,
                i.stage,
                i.model_used,
                i.model_index,
                i.iteration_number,
                i.actual_prompt,
                i.retry_context,
                i.visual_feedback_received,
                i.accuracy_score,
                i.products_found,
                i.duration_ms,
                i.api_cost,
                pel.retry_blocks_activated,
                pel.prompt_metadata
            FROM iterations i
            LEFT JOIN prompt_execution_log pel ON i.id = pel.iteration_id
            WHERE i.extraction_run_id = $1
        """
        
        params = [self.extraction_run_id]
        
        if stage:
            query += " AND i.stage = $2"
            params.append(stage)
            
        if model:
            query += f" AND i.model_used = ${len(params) + 1}"
            params.append(model)
            
        query += " ORDER BY i.created_at"
        
        async with self.analytics.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
        return [dict(row) for row in rows]


# Additional table for detailed prompt tracking
PROMPT_EXECUTION_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS prompt_execution_log (
    id SERIAL PRIMARY KEY,
    iteration_id INTEGER REFERENCES iterations(id),
    prompt_template_hash BIGINT,
    retry_blocks_activated TEXT[],
    prompt_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_prompt_execution_iteration (iteration_id),
    INDEX idx_prompt_execution_blocks (retry_blocks_activated)
);
"""