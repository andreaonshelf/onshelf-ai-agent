"""
AI Agent Models
Data structures for mismatch analysis and agent results
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class MismatchSeverity(str, Enum):
    """Severity levels for mismatches"""
    CRITICAL = "critical"   # Must fix to achieve accuracy
    HIGH = "high"          # Significant impact on accuracy
    MEDIUM = "medium"      # Moderate impact
    LOW = "low"           # Minor issue


class RootCause(str, Enum):
    """Root causes of mismatches"""
    STRUCTURE_ERROR = "structure_error"           # Wrong shelf count/layout
    EXTRACTION_ERROR = "extraction_error"         # Product detection failed
    VISUALIZATION_ERROR = "visualization_error"   # Planogram rendering issue
    COORDINATE_ERROR = "coordinate_error"         # Spatial positioning wrong
    QUANTITY_ERROR = "quantity_error"             # Facing count incorrect
    PRICE_ERROR = "price_error"                   # Price extraction failed


class MismatchIssue(BaseModel):
    """Individual mismatch identified by AI comparison"""
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(description="missing_product, wrong_position, price_error, etc.")
    severity: MismatchSeverity
    location: str = Field(description="Shelf 2, left section")
    description: str = Field(description="Detailed explanation")
    root_cause: RootCause
    confidence: float = Field(description="AI confidence in diagnosis")
    accuracy_impact: float = Field(description="Impact on overall accuracy")
    suggested_fix: str = Field(description="Recommended resolution")
    
    # Additional context
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    visual_evidence: Optional[Dict[str, any]] = None


class MismatchAnalysis(BaseModel):
    """Complete AI analysis of original vs planogram"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    extraction_id: str
    planogram_id: str
    
    # Accuracy metrics
    overall_accuracy: float = Field(description="0.0-1.0 accuracy score")
    structure_accuracy: float
    product_accuracy: float
    spatial_accuracy: float
    price_accuracy: float
    facing_accuracy: float
    
    # Issues found
    issues: List[MismatchIssue] = Field(description="All detected mismatches")
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    
    # Analysis metadata
    analysis_duration_seconds: float
    comparison_method: str = "visual_ai_comparison"
    model_used: str
    
    # Recommendations
    recommendations: List[str] = Field(description="High-level improvements")
    iteration_strategy: Optional[str] = None


class IterationDecision(BaseModel):
    """Agent's decision for next iteration"""
    should_iterate: bool
    reason: str
    strategy_adjustments: List[str]
    focus_areas: List[str]
    expected_improvement: float


class AgentState(str, Enum):
    """Current state of the AI Agent"""
    INITIALIZING = "initializing"
    EXTRACTING = "extracting"
    GENERATING_PLANOGRAM = "generating_planogram"
    COMPARING = "comparing"
    ANALYZING = "analyzing"
    ITERATING = "iterating"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"


class AgentResult(BaseModel):
    """Final result from AI Agent"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    upload_id: str
    
    # Best extraction achieved
    extraction: Dict  # CompleteShelfExtraction as dict
    planogram: Dict   # VisualPlanogram as dict
    mismatch_analysis: MismatchAnalysis
    
    # Performance metrics
    accuracy: float
    iterations_completed: int
    target_achieved: bool
    processing_duration: float
    total_api_cost: float
    
    # Decision
    human_review_required: bool = False
    escalation_reason: Optional[str] = None
    confidence_in_result: float
    
    # Metadata
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    state_history: List[Dict[str, any]] = Field(default_factory=list)


class AgentIteration(BaseModel):
    """Single iteration of the AI Agent"""
    iteration_number: int
    extraction_steps: List[Dict]
    extraction_duration: float
    planogram_generation_duration: float
    comparison_duration: float
    
    # Results
    accuracy_achieved: float
    issues_found: int
    improvements_from_previous: float
    
    # Costs
    api_costs: Dict[str, float]
    total_iteration_cost: float 