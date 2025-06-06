"""
Base System Interface
Common interface for all strategic extraction systems
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from ..config import SystemConfig
from ..utils import logger


class CostBreakdown(BaseModel):
    """Cost breakdown for system comparison"""
    total_cost: float = Field(description="Total API cost in USD")
    model_costs: Dict[str, float] = Field(description="Cost per model")
    api_calls: Dict[str, int] = Field(description="Number of API calls per model")
    tokens_used: Dict[str, int] = Field(description="Tokens used per model")
    cost_per_accuracy_point: float = Field(description="Cost efficiency metric")


class PerformanceMetrics(BaseModel):
    """Performance metrics for system comparison"""
    accuracy: float = Field(description="Overall extraction accuracy")
    processing_time: float = Field(description="Total processing time in seconds")
    consensus_rate: float = Field(description="Percentage of stages reaching consensus")
    iteration_count: int = Field(description="Number of iterations required")
    human_escalation_rate: float = Field(description="Rate of human escalation needed")
    spatial_accuracy: float = Field(description="Product positioning accuracy")
    
    # System-specific metrics
    complexity_rating: str = Field(description="Low/Medium/High")
    control_level: str = Field(description="Maximum/Framework-Limited/Selective")
    debugging_ease: str = Field(description="Easy/Medium/Complex")


class ExtractionResult(BaseModel):
    """Unified extraction result across all systems"""
    system_type: str = Field(description="Which system generated this result")
    upload_id: str = Field(description="Unique identifier for this extraction")
    extraction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Core extraction data
    structure: Dict[str, Any] = Field(description="Shelf structure analysis")
    positions: Dict[str, Any] = Field(description="Product position mapping")
    quantities: Dict[str, Any] = Field(description="Product quantity analysis")
    details: Dict[str, Any] = Field(description="Product detail extraction")
    
    # Quality metrics
    overall_accuracy: float = Field(description="End-to-end accuracy score")
    consensus_reached: bool = Field(description="Whether consensus was achieved")
    validation_result: Dict[str, Any] = Field(description="End-to-end validation")
    
    # Processing metadata
    processing_time: float = Field(description="Total processing time")
    iteration_count: int = Field(description="Number of iterations")
    cost_breakdown: CostBreakdown
    performance_metrics: PerformanceMetrics
    
    # Human feedback preparation
    ready_for_human_review: bool = Field(default=False)
    human_review_priority: str = Field(default="normal")  # low/normal/high
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseExtractionSystem(ABC):
    """Common interface for all strategic extraction systems"""
    
    def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None):
        self.config = config
        self.queue_item_id = queue_item_id
        self.system_type = self.__class__.__name__.replace('System', '').lower()
        
        logger.info(
            f"Initialized {self.system_type} extraction system",
            component="base_system",
            system_type=self.system_type
        )
    
    @abstractmethod
    async def extract_with_consensus(self, image_data: bytes, upload_id: str, extraction_data: Optional[Dict] = None) -> ExtractionResult:
        """
        Main extraction method - all systems must implement this with identical output format
        
        Args:
            image_data: Raw image bytes
            upload_id: Unique identifier for this extraction
            extraction_data: Optional dict containing iteration context, configuration, etc.
            
        Returns:
            ExtractionResult with unified format across all systems
        """
        pass
    
    async def extract_with_iterations(self, 
                                    image_data: bytes, 
                                    upload_id: str,
                                    target_accuracy: float = 0.95,
                                    max_iterations: int = 5,
                                    configuration: Optional[Dict] = None) -> ExtractionResult:
        """
        Extract with iteration loop until target accuracy achieved
        This is the REAL orchestration - iterations, visual feedback, decisions
        """
        best_result = None
        best_accuracy = 0.0
        iteration_history = []
        
        for iteration in range(1, max_iterations + 1):
            logger.info(
                f"Extraction iteration {iteration}/{max_iterations}",
                component="base_system",
                system_type=self.system_type,
                current_accuracy=best_accuracy
            )
            
            # Prepare extraction data
            extraction_data = {
                'configuration': configuration,
                'iteration': iteration,
                'previous_attempts': iteration_history,
                'target_accuracy': target_accuracy
            }
            
            # Extract using system's consensus method
            result = await self.extract_with_consensus(
                image_data=image_data,
                upload_id=upload_id,
                extraction_data=extraction_data
            )
            
            # Check accuracy
            if hasattr(result, 'overall_accuracy'):
                current_accuracy = result.overall_accuracy
                if current_accuracy > best_accuracy:
                    best_accuracy = current_accuracy
                    best_result = result
                
                # Stop if target reached
                if current_accuracy >= target_accuracy:
                    logger.info(
                        f"Target accuracy reached: {current_accuracy:.2%}",
                        component="base_system",
                        iterations_used=iteration
                    )
                    break
            
            iteration_history.append(result)
        
        return best_result or result
    
    @abstractmethod
    async def get_cost_breakdown(self) -> CostBreakdown:
        """Get detailed cost breakdown for comparison between systems"""
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics for A/B testing and comparison"""
        pass
    
    @abstractmethod
    def get_architecture_benefits(self) -> List[str]:
        """Get key architectural benefits of this system"""
        pass
    
    @abstractmethod
    def get_complexity_rating(self) -> str:
        """Get complexity rating: Low/Medium/High"""
        pass
    
    @abstractmethod
    def get_control_level(self) -> str:
        """Get control level: Maximum/Framework-Limited/Selective"""
        pass
    
    # Common utility methods
    def _calculate_cost_efficiency(self, total_cost: float, accuracy: float) -> float:
        """Calculate cost per accuracy point for comparison"""
        if accuracy == 0:
            return float('inf')
        return total_cost / accuracy
    
    def _should_escalate_to_human(self, accuracy: float, iteration_count: int) -> bool:
        """Determine if human escalation is needed"""
        return accuracy < 0.85 or iteration_count >= 5
    
    def _get_human_review_priority(self, accuracy: float, consensus_rate: float) -> str:
        """Determine human review priority"""
        if accuracy < 0.7 or consensus_rate < 0.5:
            return "high"
        elif accuracy < 0.85 or consensus_rate < 0.7:
            return "normal"
        else:
            return "low"


class ExtractionSystemFactory:
    """Factory for switching between different strategic implementation approaches"""
    
    AVAILABLE_SYSTEMS = {
        "custom": "Lightweight Custom (Full Control)",
        "langgraph": "LangGraph Framework (Professional)", 
        "hybrid": "Custom + LangChain Hybrid (Best of Both Worlds)"
    }
    
    @staticmethod
    def get_system(system_type: str, config: SystemConfig, queue_item_id: Optional[int] = None) -> BaseExtractionSystem:
        """Get extraction system by type"""
        
        logger.info(
            f"Creating extraction system: {system_type}",
            component="system_factory",
            system_type=system_type
        )
        
        if system_type == "custom":
            from .custom_consensus_visual import CustomConsensusVisualSystem
            return CustomConsensusVisualSystem(config, queue_item_id)
        elif system_type == "langgraph":
            from .langgraph_system import LangGraphConsensusSystem
            return LangGraphConsensusSystem(config)
        elif system_type == "hybrid":
            from .hybrid_system import HybridConsensusSystem
            return HybridConsensusSystem(config)
        else:
            raise ValueError(f"Unknown system type: {system_type}. Available: {list(ExtractionSystemFactory.AVAILABLE_SYSTEMS.keys())}")
    
    @staticmethod
    def get_available_systems() -> Dict[str, str]:
        """Get all available systems with descriptions"""
        return ExtractionSystemFactory.AVAILABLE_SYSTEMS.copy()
    
    @staticmethod
    async def run_strategic_comparison(image_data: bytes, upload_id: str, config: SystemConfig) -> Dict[str, Any]:
        """Run strategic comparison across all three systems"""
        
        logger.info(
            f"Starting strategic comparison for upload {upload_id}",
            component="system_factory",
            upload_id=upload_id
        )
        
        results = {}
        
        for system_type in ExtractionSystemFactory.AVAILABLE_SYSTEMS.keys():
            try:
                system = ExtractionSystemFactory.get_system(system_type, config)
                
                start_time = datetime.utcnow()
                result = await system.extract_with_consensus(image_data, upload_id)
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                results[system_type] = {
                    'result': result,
                    'processing_time': processing_time,
                    'cost': await system.get_cost_breakdown(),
                    'performance': await system.get_performance_metrics(),
                    'architecture_benefits': system.get_architecture_benefits(),
                    'complexity_rating': system.get_complexity_rating(),
                    'control_level': system.get_control_level(),
                    'success': True
                }
                
                logger.info(
                    f"System {system_type} completed successfully",
                    component="system_factory",
                    system_type=system_type,
                    accuracy=result.overall_accuracy,
                    processing_time=processing_time
                )
                
            except Exception as e:
                logger.error(
                    f"System {system_type} failed: {e}",
                    component="system_factory",
                    system_type=system_type,
                    error=str(e)
                )
                results[system_type] = {
                    'error': str(e),
                    'success': False
                }
        
        # Calculate comparison metrics
        successful_results = {k: v for k, v in results.items() if v.get('success', False)}
        
        if successful_results:
            comparison_summary = ExtractionSystemFactory._generate_comparison_summary(successful_results)
            results['comparison_summary'] = comparison_summary
        
        logger.info(
            f"Strategic comparison completed: {len(successful_results)}/{len(results)} systems succeeded",
            component="system_factory",
            successful_systems=len(successful_results),
            total_systems=len(results)
        )
        
        return results
    
    @staticmethod
    def _generate_comparison_summary(successful_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary comparing successful systems"""
        
        summary = {
            'best_accuracy': {'system': None, 'score': 0},
            'fastest_processing': {'system': None, 'time': float('inf')},
            'most_cost_effective': {'system': None, 'efficiency': float('inf')},
            'highest_consensus': {'system': None, 'rate': 0},
            'architectural_comparison': {}
        }
        
        for system_type, data in successful_results.items():
            result = data['result']
            performance = data['performance']
            cost = data['cost']
            
            # Best accuracy
            if result.overall_accuracy > summary['best_accuracy']['score']:
                summary['best_accuracy'] = {
                    'system': system_type,
                    'score': result.overall_accuracy
                }
            
            # Fastest processing
            if data['processing_time'] < summary['fastest_processing']['time']:
                summary['fastest_processing'] = {
                    'system': system_type,
                    'time': data['processing_time']
                }
            
            # Most cost effective
            if cost.cost_per_accuracy_point < summary['most_cost_effective']['efficiency']:
                summary['most_cost_effective'] = {
                    'system': system_type,
                    'efficiency': cost.cost_per_accuracy_point
                }
            
            # Highest consensus rate
            if performance.consensus_rate > summary['highest_consensus']['rate']:
                summary['highest_consensus'] = {
                    'system': system_type,
                    'rate': performance.consensus_rate
                }
            
            # Architectural comparison
            summary['architectural_comparison'][system_type] = {
                'benefits': data['architecture_benefits'],
                'complexity': data['complexity_rating'],
                'control': data['control_level'],
                'accuracy': result.overall_accuracy,
                'cost': cost.total_cost,
                'time': data['processing_time']
            }
        
        return summary 