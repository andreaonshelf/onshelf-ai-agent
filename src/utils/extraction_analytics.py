"""
Extraction Analytics Module
Provides detailed tracking of extraction pipeline execution
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncpg
from contextlib import asynccontextmanager

from ..utils import logger
from ..config import SystemConfig


class ExtractionAnalytics:
    """Detailed analytics tracking for extraction pipeline"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.db_pool = None
        self._current_iterations = {}  # Track active iterations
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.config.database_url,
                min_size=2,
                max_size=10
            )
            logger.info("Analytics module initialized", component="extraction_analytics")
        except Exception as e:
            logger.error(f"Failed to initialize analytics: {e}", component="extraction_analytics")
    
    async def close(self):
        """Close database connections"""
        if self.db_pool:
            await self.db_pool.close()
    
    @asynccontextmanager
    async def track_iteration(self,
                            extraction_run_id: str,
                            queue_item_id: int,
                            iteration_number: int,
                            stage: str,
                            model_used: str,
                            model_index: int,
                            prompt_template_id: Optional[str] = None,
                            actual_prompt: Optional[str] = None,
                            retry_context: Optional[Dict] = None,
                            visual_feedback: Optional[Dict] = None):
        """Context manager for tracking an iteration"""
        
        iteration_id = None
        start_time = datetime.utcnow()
        
        try:
            # Start iteration tracking
            async with self.db_pool.acquire() as conn:
                iteration_id = await conn.fetchval("""
                    INSERT INTO iterations (
                        extraction_run_id, queue_item_id, iteration_number,
                        stage, model_used, model_index, prompt_template_id,
                        actual_prompt, retry_context, visual_feedback_received,
                        status, started_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'started', NOW())
                    RETURNING id
                """, extraction_run_id, queue_item_id, iteration_number,
                    stage, model_used, model_index, prompt_template_id,
                    actual_prompt, json.dumps(retry_context) if retry_context else None,
                    json.dumps(visual_feedback) if visual_feedback else None)
            
            self._current_iterations[iteration_id] = {
                'start_time': start_time,
                'stage': stage,
                'model': model_used
            }
            
            logger.info(
                f"Started tracking iteration {iteration_id}",
                component="extraction_analytics",
                stage=stage,
                model=model_used,
                iteration_number=iteration_number
            )
            
            yield iteration_id
            
            # Mark as completed on successful exit
            await self._complete_iteration(iteration_id, success=True)
            
        except Exception as e:
            # Mark as failed on exception
            if iteration_id:
                await self._complete_iteration(
                    iteration_id, 
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
            raise
    
    async def _complete_iteration(self,
                                iteration_id: int,
                                success: bool,
                                error_type: Optional[str] = None,
                                error_message: Optional[str] = None):
        """Mark an iteration as completed"""
        
        if iteration_id not in self._current_iterations:
            return
        
        iteration_data = self._current_iterations[iteration_id]
        duration_ms = int((datetime.utcnow() - iteration_data['start_time']).total_seconds() * 1000)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE iterations 
                SET status = $1, success = $2, completed_at = NOW(),
                    duration_ms = $3, error_type = $4, error_message = $5
                WHERE id = $6
            """, 'completed' if success else 'failed', success,
                duration_ms, error_type, error_message, iteration_id)
        
        del self._current_iterations[iteration_id]
        
        logger.info(
            f"Completed iteration {iteration_id}",
            component="extraction_analytics",
            success=success,
            duration_ms=duration_ms,
            stage=iteration_data['stage']
        )
    
    async def update_iteration_result(self,
                                    iteration_id: int,
                                    extraction_result: Optional[Dict] = None,
                                    products_found: Optional[int] = None,
                                    accuracy_score: Optional[float] = None,
                                    confidence_scores: Optional[Dict] = None,
                                    api_cost: Optional[float] = None,
                                    tokens_used: Optional[int] = None):
        """Update iteration with extraction results"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE iterations 
                SET extraction_result = $1, products_found = $2,
                    accuracy_score = $3, confidence_scores = $4,
                    api_cost = $5, tokens_used = $6
                WHERE id = $7
            """, json.dumps(extraction_result) if extraction_result else None,
                products_found, accuracy_score,
                json.dumps(confidence_scores) if confidence_scores else None,
                api_cost, tokens_used, iteration_id)
    
    async def log_visual_comparison(self,
                                  iteration_id: int,
                                  comparison_result: Dict,
                                  planogram_generated: bool = True):
        """Log visual comparison results"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE iterations 
                SET visual_comparison_result = $1, planogram_generated = $2
                WHERE id = $3
            """, json.dumps(comparison_result), planogram_generated, iteration_id)
        
        logger.info(
            f"Logged visual comparison for iteration {iteration_id}",
            component="extraction_analytics",
            issues_found=len(comparison_result.get('shelf_mismatches', []))
        )
    
    async def log_orchestrator_decision(self,
                                      iteration_id: int,
                                      decision: Dict,
                                      retry_reason: Optional[str] = None,
                                      improvements: Optional[Dict] = None):
        """Log orchestrator's decision-making process"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE iterations 
                SET orchestrator_decision = $1, retry_reason = $2,
                    improvements_from_previous = $3
                WHERE id = $4
            """, json.dumps(decision), retry_reason,
                json.dumps(improvements) if improvements else None,
                iteration_id)
        
        logger.info(
            f"Logged orchestrator decision for iteration {iteration_id}",
            component="extraction_analytics",
            decision_type=decision.get('action', 'unknown'),
            retry_reason=retry_reason
        )
    
    async def get_stage_performance(self, 
                                  days: int = 7,
                                  system: Optional[str] = None) -> Dict:
        """Get real stage performance metrics"""
        
        async with self.db_pool.acquire() as conn:
            # Get stage success rates
            stage_stats = await conn.fetch("""
                SELECT 
                    i.stage,
                    COUNT(*) as total_attempts,
                    AVG(CASE WHEN i.success THEN 1 ELSE 0 END) * 100 as success_rate,
                    AVG(i.accuracy_score) * 100 as avg_accuracy,
                    AVG(i.duration_ms) as avg_duration_ms,
                    AVG(i.api_cost) as avg_cost,
                    COUNT(DISTINCT i.extraction_run_id) as unique_runs
                FROM iterations i
                JOIN extraction_runs er ON i.extraction_run_id = er.run_id
                WHERE i.created_at > NOW() - INTERVAL '%s days'
                AND ($1::text IS NULL OR er.system = $1)
                GROUP BY i.stage
                ORDER BY 
                    CASE i.stage 
                        WHEN 'structure' THEN 1 
                        WHEN 'products' THEN 2 
                        WHEN 'details' THEN 3 
                        ELSE 4 
                    END
            """ % days, system)
            
            return {
                'stages': [row['stage'] for row in stage_stats],
                'success_rates': [float(row['success_rate']) for row in stage_stats],
                'avg_accuracy': [float(row['avg_accuracy']) if row['avg_accuracy'] else 0 for row in stage_stats],
                'avg_duration_ms': [int(row['avg_duration_ms']) if row['avg_duration_ms'] else 0 for row in stage_stats],
                'avg_cost': [float(row['avg_cost']) if row['avg_cost'] else 0 for row in stage_stats],
                'total_attempts': [row['total_attempts'] for row in stage_stats]
            }
    
    async def get_retry_patterns(self, stage: Optional[str] = None) -> Dict:
        """Analyze retry patterns and effectiveness"""
        
        async with self.db_pool.acquire() as conn:
            retry_data = await conn.fetch("""
                SELECT 
                    stage,
                    retry_reason,
                    COUNT(*) as retry_count,
                    AVG(CASE WHEN success THEN 1 ELSE 0 END) * 100 as success_rate,
                    AVG(accuracy_score) as avg_accuracy_after_retry
                FROM iterations
                WHERE retry_reason IS NOT NULL
                AND ($1::text IS NULL OR stage = $1)
                AND created_at > NOW() - INTERVAL '7 days'
                GROUP BY stage, retry_reason
                ORDER BY retry_count DESC
                LIMIT 20
            """, stage)
            
            return [{
                'stage': row['stage'],
                'reason': row['retry_reason'],
                'count': row['retry_count'],
                'success_rate': float(row['success_rate']),
                'avg_accuracy': float(row['avg_accuracy_after_retry']) if row['avg_accuracy_after_retry'] else 0
            } for row in retry_data]
    
    async def get_visual_feedback_impact(self) -> Dict:
        """Analyze impact of visual feedback on extraction quality"""
        
        async with self.db_pool.acquire() as conn:
            impact_data = await conn.fetch("""
                WITH feedback_analysis AS (
                    SELECT 
                        stage,
                        model_index,
                        CASE WHEN visual_feedback_received IS NOT NULL THEN 'with_feedback' 
                             ELSE 'without_feedback' END as feedback_status,
                        AVG(accuracy_score) as avg_accuracy,
                        AVG(products_found) as avg_products,
                        COUNT(*) as count
                    FROM iterations
                    WHERE stage IN ('products', 'details')
                    AND created_at > NOW() - INTERVAL '7 days'
                    GROUP BY stage, model_index, feedback_status
                )
                SELECT * FROM feedback_analysis
                ORDER BY stage, model_index
            """)
            
            return {
                'data': [{
                    'stage': row['stage'],
                    'model_index': row['model_index'],
                    'feedback_status': row['feedback_status'],
                    'avg_accuracy': float(row['avg_accuracy']) if row['avg_accuracy'] else 0,
                    'avg_products': float(row['avg_products']) if row['avg_products'] else 0,
                    'count': row['count']
                } for row in impact_data]
            }
    
    async def get_prompt_performance_with_retry(self) -> Dict:
        """Get prompt performance including retry block effectiveness"""
        
        async with self.db_pool.acquire() as conn:
            prompt_data = await conn.fetch("""
                SELECT 
                    i.prompt_template_id,
                    pt.prompt_type,
                    pt.model_type,
                    COUNT(*) as usage_count,
                    AVG(i.accuracy_score) as avg_accuracy,
                    SUM(CASE WHEN i.retry_context IS NOT NULL THEN 1 ELSE 0 END) as retry_uses,
                    AVG(CASE WHEN i.retry_context IS NOT NULL THEN i.accuracy_score ELSE NULL END) as retry_accuracy
                FROM iterations i
                JOIN prompt_templates pt ON i.prompt_template_id = pt.prompt_id
                WHERE i.created_at > NOW() - INTERVAL '7 days'
                GROUP BY i.prompt_template_id, pt.prompt_type, pt.model_type
                ORDER BY usage_count DESC
                LIMIT 20
            """)
            
            return [{
                'prompt_id': str(row['prompt_template_id']),
                'type': row['prompt_type'],
                'model': row['model_type'],
                'usage_count': row['usage_count'],
                'avg_accuracy': float(row['avg_accuracy']) if row['avg_accuracy'] else 0,
                'retry_uses': row['retry_uses'],
                'retry_accuracy': float(row['retry_accuracy']) if row['retry_accuracy'] else 0
            } for row in prompt_data]


# Global instance
_analytics_instance = None

def get_extraction_analytics() -> ExtractionAnalytics:
    """Get global analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        from ..config import get_config
        _analytics_instance = ExtractionAnalytics(get_config())
        # Initialize in background
        asyncio.create_task(_analytics_instance.initialize())
    return _analytics_instance