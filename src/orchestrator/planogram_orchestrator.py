"""
Planogram Orchestrator
Manages planogram generation with multiple abstraction levels and quality evaluation
"""

from typing import List, Dict, Optional
from datetime import datetime

from ..config import SystemConfig
from ..models.extraction_models import ExtractionResult, ProductExtraction
from ..models.shelf_structure import ShelfStructure
from ..planogram.abstraction_manager import PlanogramAbstractionManager
from ..planogram.quality_evaluator import PlanogramQualityEvaluator
from ..planogram.generator import PlanogramGenerator
from ..planogram.models import VisualPlanogram
from ..utils import logger


class AgentPlanogramResult:
    """Result from planogram generation for a specific agent iteration"""
    def __init__(self, 
                 agent_number: int,
                 planogram: VisualPlanogram,
                 extraction_data: ExtractionResult,
                 quality_assessment: Dict,
                 abstraction_level: str,
                 generation_timestamp: datetime):
        self.agent_number = agent_number
        self.planogram = planogram
        self.extraction_data = extraction_data
        self.quality_assessment = quality_assessment
        self.abstraction_level = abstraction_level
        self.generation_timestamp = generation_timestamp


class PlanogramComparisonSet:
    """Set of planograms for comparison across iterations"""
    def __init__(self,
                 agent_planograms: List[AgentPlanogramResult],
                 progression_analysis: Dict,
                 best_iteration: int,
                 improvement_trend: str):
        self.agent_planograms = agent_planograms
        self.progression_analysis = progression_analysis
        self.best_iteration = best_iteration
        self.improvement_trend = improvement_trend


class PlanogramOrchestrator:
    """Manages planogram generation for each agent iteration"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.abstraction_manager = PlanogramAbstractionManager()
        self.quality_evaluator = PlanogramQualityEvaluator()
        self.generator = PlanogramGenerator()
        
        logger.info(
            "Planogram Orchestrator initialized",
            component="planogram_orchestrator"
        )
    
    async def generate_for_agent_iteration(self,
                                         agent_number: int,
                                         extraction_result: ExtractionResult,
                                         structure_context: ShelfStructure,
                                         abstraction_level: str = "product_view",
                                         original_image: bytes = None) -> AgentPlanogramResult:
        """Generate planogram for specific agent iteration"""
        
        logger.info(
            f"Generating planogram for Agent {agent_number}",
            component="planogram_orchestrator",
            agent_number=agent_number,
            products=extraction_result.total_products,
            abstraction_level=abstraction_level
        )
        
        # Generate planogram using current extraction data
        planogram = await self._generate_planogram_from_extraction(
            extraction_result=extraction_result,
            structure_context=structure_context,
            abstraction_level=abstraction_level
        )
        
        # Evaluate generation quality
        quality_assessment = self.quality_evaluator.evaluate_generation_quality(
            original_image=original_image,
            json_data=extraction_result.to_dict(),
            generated_planogram=planogram
        )
        
        result = AgentPlanogramResult(
            agent_number=agent_number,
            planogram=planogram,
            extraction_data=extraction_result,
            quality_assessment=quality_assessment,
            abstraction_level=abstraction_level,
            generation_timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Planogram generated for Agent {agent_number}",
            component="planogram_orchestrator",
            agent_number=agent_number,
            quality_score=quality_assessment.get('overall_quality', 0),
            generation_issues=len(quality_assessment.get('issues', []))
        )
        
        return result
    
    async def generate_comparison_set(self,
                                    agent_results: List[ExtractionResult],
                                    structure_context: ShelfStructure,
                                    abstraction_level: str = "product_view",
                                    original_image: bytes = None) -> PlanogramComparisonSet:
        """Generate planograms for all agent iterations for side-by-side comparison"""
        
        logger.info(
            f"Generating comparison set for {len(agent_results)} agents",
            component="planogram_orchestrator",
            agent_count=len(agent_results),
            abstraction_level=abstraction_level
        )
        
        comparison_planograms = []
        
        for i, agent_result in enumerate(agent_results, 1):
            agent_planogram = await self.generate_for_agent_iteration(
                agent_number=i,
                extraction_result=agent_result,
                structure_context=structure_context,
                abstraction_level=abstraction_level,
                original_image=original_image
            )
            comparison_planograms.append(agent_planogram)
        
        # Generate comparison analysis
        comparison_analysis = self._analyze_planogram_progression(comparison_planograms)
        
        comparison_set = PlanogramComparisonSet(
            agent_planograms=comparison_planograms,
            progression_analysis=comparison_analysis,
            best_iteration=comparison_analysis['highest_quality_iteration'],
            improvement_trend=comparison_analysis['quality_trend']
        )
        
        return comparison_set
    
    async def _generate_planogram_from_extraction(self,
                                                extraction_result: ExtractionResult,
                                                structure_context: ShelfStructure,
                                                abstraction_level: str) -> VisualPlanogram:
        """Generate planogram with specified abstraction level"""
        
        # For product view, use the new extraction-based renderer
        if abstraction_level == "product_view":
            planogram = await self.generator.generate_from_extraction_result(
                extraction_result,
                structure_context
            )
        else:
            # For other abstraction levels, use the existing method
            if abstraction_level == "brand_view":
                planogram_data = self.abstraction_manager.generate_brand_view(extraction_result.products)
            elif abstraction_level == "sku_view":
                planogram_data = self.abstraction_manager.generate_sku_view(extraction_result.products)
            else:
                planogram_data = self.abstraction_manager.generate_product_view(extraction_result.products)
            
            # Generate visual planogram
            planogram = await self.generator.generate_from_abstraction(
                planogram_data,
                structure_context,
                abstraction_level
            )
        
        return planogram
    
    def _analyze_planogram_progression(self, planograms: List[AgentPlanogramResult]) -> Dict:
        """Analyze how planogram quality improves across iterations"""
        
        quality_scores = [p.quality_assessment.get('overall_quality', 0) for p in planograms]
        
        # Calculate improvements
        improvements_per_iteration = []
        for i in range(1, len(quality_scores)):
            improvement = quality_scores[i] - quality_scores[i-1]
            improvements_per_iteration.append(improvement)
        
        # Determine trend
        if len(quality_scores) > 1:
            if quality_scores[-1] > quality_scores[0]:
                quality_trend = "improving"
            elif quality_scores[-1] < quality_scores[0]:
                quality_trend = "declining"
            else:
                quality_trend = "stable"
        else:
            quality_trend = "single_iteration"
        
        # Find significant improvements
        significant_improvements = []
        for i, improvement in enumerate(improvements_per_iteration):
            if improvement > 0.1:  # 10% improvement threshold
                significant_improvements.append(i + 2)  # Agent number
        
        return {
            'quality_scores': quality_scores,
            'highest_quality_iteration': quality_scores.index(max(quality_scores)) + 1,
            'improvement_per_iteration': improvements_per_iteration,
            'quality_trend': quality_trend,
            'significant_improvements': significant_improvements,
            'average_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0
        }
    
    async def switch_abstraction_level(self,
                                     agent_planogram: AgentPlanogramResult,
                                     new_abstraction_level: str) -> AgentPlanogramResult:
        """Switch planogram to different abstraction level"""
        
        logger.info(
            f"Switching abstraction level from {agent_planogram.abstraction_level} to {new_abstraction_level}",
            component="planogram_orchestrator",
            agent_number=agent_planogram.agent_number,
            from_level=agent_planogram.abstraction_level,
            to_level=new_abstraction_level
        )
        
        # Generate new planogram with different abstraction
        new_planogram = await self._generate_planogram_from_extraction(
            extraction_result=agent_planogram.extraction_data,
            structure_context=agent_planogram.extraction_data.structure,
            abstraction_level=new_abstraction_level
        )
        
        # Create new result with updated abstraction
        new_result = AgentPlanogramResult(
            agent_number=agent_planogram.agent_number,
            planogram=new_planogram,
            extraction_data=agent_planogram.extraction_data,
            quality_assessment=agent_planogram.quality_assessment,
            abstraction_level=new_abstraction_level,
            generation_timestamp=datetime.utcnow()
        )
        
        return new_result 