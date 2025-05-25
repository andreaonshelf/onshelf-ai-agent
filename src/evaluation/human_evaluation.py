"""
Human Evaluation System
Manages human grading and feedback collection
"""

import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np

from ..config import SystemConfig
from ..orchestrator.models import MasterResult
from ..utils import logger


class EvaluationSession(BaseModel):
    """Human evaluation session for grading"""
    session_id: str
    upload_id: str
    created_at: datetime
    status: str
    
    # Evaluation areas
    extraction_accuracy_grade: Optional[int] = None
    planogram_accuracy_grade: Optional[int] = None
    overall_satisfaction_grade: Optional[int] = None
    
    # Detailed feedback
    position_corrections: List[Dict] = Field(default_factory=list)
    product_corrections: List[Dict] = Field(default_factory=list)
    planogram_edits: List[Dict] = Field(default_factory=list)
    comments: str = ""


class HumanEvaluation(BaseModel):
    """Completed human evaluation"""
    session_id: str
    evaluator_id: str
    timestamp: datetime
    
    # Grading (1-5 stars)
    extraction_accuracy: int = Field(description="1-5 star rating")
    planogram_accuracy: int = Field(description="1-5 star rating")
    overall_satisfaction: int = Field(description="1-5 star rating")
    
    # Specific corrections
    position_corrections: List[Dict]
    product_name_corrections: List[Dict]
    price_corrections: List[Dict]
    
    # Planogram feedback
    planogram_edits: List[Dict]
    layout_suggestions: List[Dict]
    
    # Open feedback
    what_worked_well: str
    what_needs_improvement: str
    suggestions: str


class EvaluationTrends(BaseModel):
    """Trends in human evaluations over time"""
    total_evaluations: int
    average_extraction_accuracy: float
    average_planogram_accuracy: float
    average_overall_satisfaction: float
    
    # Improvement areas
    common_extraction_issues: List[Dict]
    common_planogram_issues: List[Dict]
    
    # Trend direction
    accuracy_trend: str
    satisfaction_trend: str


class HumanEvaluationSystem:
    """Manages human grading and feedback collection"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        # In production, this would use Supabase
        self.evaluations_db = []
        self.sessions_db = []
        
        logger.info(
            "Human Evaluation System initialized",
            component="human_evaluation"
        )
    
    async def create_evaluation_session(self, 
                                      master_result: MasterResult,
                                      upload_id: str) -> EvaluationSession:
        """Create human evaluation session for grading"""
        
        session = EvaluationSession(
            session_id=str(uuid.uuid4()),
            upload_id=upload_id,
            created_at=datetime.utcnow(),
            status="pending_evaluation"
        )
        
        # Store session
        self.sessions_db.append(session)
        
        logger.info(
            f"Created evaluation session {session.session_id}",
            component="human_evaluation",
            session_id=session.session_id,
            upload_id=upload_id,
            final_accuracy=master_result.final_accuracy
        )
        
        return session
    
    async def submit_human_evaluation(self, 
                                    session_id: str,
                                    evaluation_data: Dict) -> HumanEvaluation:
        """Process submitted human evaluation"""
        
        evaluation = HumanEvaluation(
            session_id=session_id,
            evaluator_id=evaluation_data.get('evaluator_id', 'anonymous'),
            timestamp=datetime.utcnow(),
            
            # Grading (1-5 stars)
            extraction_accuracy=evaluation_data.get('extraction_accuracy', 3),
            planogram_accuracy=evaluation_data.get('planogram_accuracy', 3),
            overall_satisfaction=evaluation_data.get('overall_satisfaction', 3),
            
            # Specific corrections
            position_corrections=evaluation_data.get('position_corrections', []),
            product_name_corrections=evaluation_data.get('product_corrections', []),
            price_corrections=evaluation_data.get('price_corrections', []),
            
            # Planogram feedback
            planogram_edits=evaluation_data.get('planogram_edits', []),
            layout_suggestions=evaluation_data.get('layout_suggestions', []),
            
            # Open feedback
            what_worked_well=evaluation_data.get('what_worked_well', ''),
            what_needs_improvement=evaluation_data.get('what_needs_improvement', ''),
            suggestions=evaluation_data.get('suggestions', '')
        )
        
        # Save evaluation
        self.evaluations_db.append(evaluation)
        
        # Update session status
        for session in self.sessions_db:
            if session.session_id == session_id:
                session.status = "evaluated"
                session.extraction_accuracy_grade = evaluation.extraction_accuracy
                session.planogram_accuracy_grade = evaluation.planogram_accuracy
                session.overall_satisfaction_grade = evaluation.overall_satisfaction
                break
        
        # Generate improvement recommendations
        recommendations = self._generate_improvement_recommendations(evaluation)
        
        logger.info(
            f"Human evaluation submitted for session {session_id}",
            component="human_evaluation",
            session_id=session_id,
            overall_rating=(evaluation.extraction_accuracy + evaluation.planogram_accuracy + evaluation.overall_satisfaction) / 3
        )
        
        return evaluation
    
    def get_evaluation_trends(self, days: int = 30) -> EvaluationTrends:
        """Analyze human evaluation trends over time"""
        
        # Filter recent evaluations
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_evaluations = [e for e in self.evaluations_db if e.timestamp >= cutoff_date]
        
        if not recent_evaluations:
            return EvaluationTrends(
                total_evaluations=0,
                average_extraction_accuracy=0,
                average_planogram_accuracy=0,
                average_overall_satisfaction=0,
                common_extraction_issues=[],
                common_planogram_issues=[],
                accuracy_trend="no_data",
                satisfaction_trend="no_data"
            )
        
        trends = EvaluationTrends(
            total_evaluations=len(recent_evaluations),
            average_extraction_accuracy=np.mean([e.extraction_accuracy for e in recent_evaluations]),
            average_planogram_accuracy=np.mean([e.planogram_accuracy for e in recent_evaluations]),
            average_overall_satisfaction=np.mean([e.overall_satisfaction for e in recent_evaluations]),
            
            # Improvement areas
            common_extraction_issues=self._analyze_common_issues(recent_evaluations, 'extraction'),
            common_planogram_issues=self._analyze_common_issues(recent_evaluations, 'planogram'),
            
            # Trend direction
            accuracy_trend=self._calculate_trend(recent_evaluations, 'extraction_accuracy'),
            satisfaction_trend=self._calculate_trend(recent_evaluations, 'overall_satisfaction')
        )
        
        logger.info(
            f"Evaluation trends analyzed for {days} days",
            component="human_evaluation",
            total_evaluations=trends.total_evaluations,
            avg_satisfaction=trends.average_overall_satisfaction
        )
        
        return trends
    
    def _generate_improvement_recommendations(self, evaluation: HumanEvaluation) -> List[str]:
        """Generate recommendations based on evaluation"""
        recommendations = []
        
        if evaluation.extraction_accuracy <= 2:
            recommendations.append("Focus on improving product detection accuracy")
        
        if evaluation.planogram_accuracy <= 2:
            recommendations.append("Review planogram generation algorithms")
        
        if len(evaluation.position_corrections) > 5:
            recommendations.append("Enhance shelf position detection logic")
        
        if len(evaluation.price_corrections) > 3:
            recommendations.append("Improve price extraction and OCR capabilities")
        
        return recommendations
    
    def _analyze_common_issues(self, evaluations: List[HumanEvaluation], issue_type: str) -> List[Dict]:
        """Analyze common issues from evaluations"""
        issue_counts = {}
        
        for eval in evaluations:
            if issue_type == 'extraction':
                # Count position corrections
                if len(eval.position_corrections) > 0:
                    issue_counts['position_errors'] = issue_counts.get('position_errors', 0) + 1
                
                # Count product corrections
                if len(eval.product_name_corrections) > 0:
                    issue_counts['product_name_errors'] = issue_counts.get('product_name_errors', 0) + 1
                
                # Count price corrections
                if len(eval.price_corrections) > 0:
                    issue_counts['price_errors'] = issue_counts.get('price_errors', 0) + 1
            
            elif issue_type == 'planogram':
                # Count planogram edits
                if len(eval.planogram_edits) > 0:
                    issue_counts['layout_issues'] = issue_counts.get('layout_issues', 0) + 1
                
                # Count layout suggestions
                if len(eval.layout_suggestions) > 0:
                    issue_counts['spacing_issues'] = issue_counts.get('spacing_issues', 0) + 1
        
        # Convert to sorted list
        common_issues = [
            {'issue': issue, 'count': count, 'percentage': count / len(evaluations) * 100}
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return common_issues[:5]  # Top 5 issues
    
    def _calculate_trend(self, evaluations: List[HumanEvaluation], metric: str) -> str:
        """Calculate trend direction for a metric"""
        if len(evaluations) < 2:
            return "insufficient_data"
        
        # Sort by timestamp
        sorted_evals = sorted(evaluations, key=lambda x: x.timestamp)
        
        # Compare first half to second half
        mid_point = len(sorted_evals) // 2
        first_half = sorted_evals[:mid_point]
        second_half = sorted_evals[mid_point:]
        
        first_avg = np.mean([getattr(e, metric) for e in first_half])
        second_avg = np.mean([getattr(e, metric) for e in second_half])
        
        if second_avg > first_avg + 0.1:
            return "improving"
        elif second_avg < first_avg - 0.1:
            return "declining"
        else:
            return "stable"
    
    async def get_pending_evaluations(self) -> List[EvaluationSession]:
        """Get evaluation sessions pending human review"""
        pending = [s for s in self.sessions_db if s.status == "pending_evaluation"]
        
        logger.info(
            f"Found {len(pending)} pending evaluations",
            component="human_evaluation",
            pending_count=len(pending)
        )
        
        return pending 