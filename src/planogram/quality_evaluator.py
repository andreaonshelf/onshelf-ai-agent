"""
Planogram Quality Evaluator
Evaluates if planogram generation code is working correctly
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..planogram.models import VisualPlanogram
from ..utils import logger


class GenerationQualityAssessment(BaseModel):
    """Assessment of planogram generation quality"""
    layout_accuracy: float = Field(description="How well layout matches shelf reality")
    visual_clarity: float = Field(description="How clear/readable the planogram is")
    data_faithfulness: float = Field(description="How accurately it represents JSON")
    spacing_logic: float = Field(description="Quality of product spacing algorithm")
    color_coding: float = Field(description="Effectiveness of color system")
    overall_quality: float = Field(description="Overall generation quality")


class GenerationIssue(BaseModel):
    """Specific issue with planogram generation"""
    type: str = Field(description="layout_algorithm, spacing_algorithm, color_system, etc")
    severity: str = Field(description="high, medium, low")
    description: str = Field(description="Human-readable issue description")
    suggested_fix: str = Field(description="Specific code improvement recommendation")


class GenerationFeedback(BaseModel):
    """Human feedback on planogram generation"""
    planogram_id: str
    layout_quality_rating: int = Field(description="1-5 star rating")
    visual_design_rating: int = Field(description="1-5 star rating") 
    json_accuracy_rating: int = Field(description="1-5 star rating")
    specific_issues: List[str]
    suggested_improvements: List[str]
    evaluator_comments: str
    timestamp: datetime


class CodeImprovementPlan(BaseModel):
    """Plan for improving planogram generation code"""
    high_priority_fixes: List[GenerationIssue]
    code_areas_to_review: List[str]
    suggested_experiments: List[str]


class PlanogramQualityEvaluator:
    """Evaluates if planogram generation code is working correctly"""
    
    def __init__(self):
        logger.info(
            "Planogram Quality Evaluator initialized",
            component="quality_evaluator"
        )
    
    def evaluate_generation_quality(self, 
                                   original_image: Optional[bytes],
                                   json_data: Dict,
                                   generated_planogram: VisualPlanogram) -> Dict:
        """Evaluate planogram generation code quality"""
        
        logger.info(
            "Evaluating planogram generation quality",
            component="quality_evaluator",
            planogram_id=generated_planogram.planogram_id if hasattr(generated_planogram, 'planogram_id') else 'unknown'
        )
        
        # Evaluate different aspects
        layout_accuracy = self._evaluate_layout_logic(json_data, generated_planogram)
        visual_clarity = self._evaluate_visual_design(generated_planogram)
        data_faithfulness = self._evaluate_json_representation(json_data, generated_planogram)
        spacing_logic = self._evaluate_spacing_algorithm(generated_planogram)
        color_coding = self._evaluate_color_system(generated_planogram)
        
        # Calculate overall quality
        overall_quality = (
            layout_accuracy * 0.3 +
            visual_clarity * 0.2 +
            data_faithfulness * 0.3 +
            spacing_logic * 0.1 +
            color_coding * 0.1
        )
        
        assessment = GenerationQualityAssessment(
            layout_accuracy=layout_accuracy,
            visual_clarity=visual_clarity,
            data_faithfulness=data_faithfulness,
            spacing_logic=spacing_logic,
            color_coding=color_coding,
            overall_quality=overall_quality
        )
        
        # Identify issues
        issues = self.identify_generation_issues(assessment)
        
        return {
            'assessment': assessment.dict(),
            'issues': [issue.dict() for issue in issues],
            'overall_quality': overall_quality,
            'needs_improvement': overall_quality < 0.8
        }
    
    def _evaluate_layout_logic(self, json_data: Dict, planogram: VisualPlanogram) -> float:
        """Evaluate if products are positioned correctly"""
        score = 1.0
        
        # Check if shelf count matches
        if hasattr(planogram, 'shelf_count'):
            expected_shelves = json_data.get('structure', {}).get('shelf_count', 0)
            if planogram.shelf_count != expected_shelves:
                score -= 0.2
        
        # Check if products are on correct shelves
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                if hasattr(shelf, 'elements'):
                    # Check for overlapping products
                    positions = []
                    for element in shelf.elements:
                        if hasattr(element, 'position_cm'):
                            if element.position_cm in positions:
                                score -= 0.1  # Overlapping products
                            positions.append(element.position_cm)
        
        return max(0, score)
    
    def _evaluate_visual_design(self, planogram: VisualPlanogram) -> float:
        """Evaluate visual clarity and design"""
        score = 1.0
        
        # Check if planogram has required visual elements
        if not hasattr(planogram, 'canvas_data') and not hasattr(planogram, 'svg_data'):
            score -= 0.3  # No visual representation
        
        # Check if dimensions are reasonable
        if hasattr(planogram, 'total_width_cm') and hasattr(planogram, 'total_height_cm'):
            if planogram.total_width_cm <= 0 or planogram.total_height_cm <= 0:
                score -= 0.2
            elif planogram.total_width_cm > 1000 or planogram.total_height_cm > 500:
                score -= 0.1  # Unrealistic dimensions
        
        return max(0, score)
    
    def _evaluate_json_representation(self, json_data: Dict, planogram: VisualPlanogram) -> float:
        """Evaluate how accurately planogram represents JSON data"""
        score = 1.0
        
        # Count products in JSON
        json_products = len(json_data.get('products', []))
        
        # Count products in planogram
        planogram_products = 0
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                if hasattr(shelf, 'elements'):
                    planogram_products += sum(1 for e in shelf.elements if e.type == 'product')
        
        # Check if counts match
        if json_products > 0:
            accuracy = min(json_products, planogram_products) / max(json_products, planogram_products)
            score = accuracy
        
        return score
    
    def _evaluate_spacing_algorithm(self, planogram: VisualPlanogram) -> float:
        """Evaluate product spacing logic"""
        score = 1.0
        
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                if hasattr(shelf, 'elements'):
                    # Check for consistent spacing
                    gaps = []
                    for i in range(1, len(shelf.elements)):
                        if hasattr(shelf.elements[i-1], 'position_cm') and hasattr(shelf.elements[i], 'position_cm'):
                            gap = shelf.elements[i].position_cm - (
                                shelf.elements[i-1].position_cm + shelf.elements[i-1].width_cm
                            )
                            gaps.append(gap)
                    
                    # Check for negative gaps (overlapping)
                    if any(gap < 0 for gap in gaps):
                        score -= 0.3
                    
                    # Check for inconsistent gaps
                    if gaps and max(gaps) > min(gaps) * 3:
                        score -= 0.1
        
        return max(0, score)
    
    def _evaluate_color_system(self, planogram: VisualPlanogram) -> float:
        """Evaluate color coding effectiveness"""
        score = 1.0
        
        # Check if confidence colors are used
        colors_found = set()
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                if hasattr(shelf, 'elements'):
                    for element in shelf.elements:
                        if hasattr(element, 'confidence_color'):
                            colors_found.add(element.confidence_color)
        
        # Should have multiple confidence levels
        if len(colors_found) < 2:
            score -= 0.2
        
        # Check if standard colors are used
        standard_colors = {'#22c55e', '#3b82f6', '#f59e0b', '#ef4444'}
        if not colors_found.intersection(standard_colors):
            score -= 0.1
        
        return max(0, score)
    
    def identify_generation_issues(self, assessment: GenerationQualityAssessment) -> List[GenerationIssue]:
        """Identify specific problems with planogram generation code"""
        issues = []
        
        if assessment.layout_accuracy < 0.8:
            issues.append(GenerationIssue(
                type="layout_algorithm",
                severity="high",
                description="Product positioning logic appears incorrect",
                suggested_fix="Review shelf coordinate calculation in PlanogramGenerator._calculate_product_positions()"
            ))
        
        if assessment.spacing_logic < 0.7:
            issues.append(GenerationIssue(
                type="spacing_algorithm", 
                severity="medium",
                description="Product spacing inconsistent or overlapping",
                suggested_fix="Adjust STANDARD_FACING_WIDTH and gap calculation logic"
            ))
        
        if assessment.visual_clarity < 0.8:
            issues.append(GenerationIssue(
                type="visual_rendering",
                severity="medium",
                description="Visual representation unclear or missing elements",
                suggested_fix="Enhance canvas/SVG rendering in PlanogramRenderer"
            ))
        
        if assessment.data_faithfulness < 0.9:
            issues.append(GenerationIssue(
                type="data_accuracy",
                severity="high",
                description="Planogram doesn't accurately represent JSON data",
                suggested_fix="Verify product mapping in generator.generate_planogram_from_json()"
            ))
        
        if assessment.color_coding < 0.8:
            issues.append(GenerationIssue(
                type="color_system",
                severity="low",
                description="Confidence color coding not effective",
                suggested_fix="Review confidence thresholds and color assignments"
            ))
        
        return issues


class PlanogramCodeImprover:
    """System to improve planogram generation based on human feedback"""
    
    def __init__(self):
        self.feedback_history = []
        
        logger.info(
            "Planogram Code Improver initialized",
            component="code_improver"
        )
    
    def collect_human_feedback(self, planogram_id: str, feedback: Dict) -> GenerationFeedback:
        """Collect human evaluation of planogram generation quality"""
        
        feedback_record = GenerationFeedback(
            planogram_id=planogram_id,
            layout_quality_rating=feedback.get('layout_quality', 3),
            visual_design_rating=feedback.get('visual_design', 3),
            json_accuracy_rating=feedback.get('json_accuracy', 3),
            specific_issues=feedback.get('specific_issues', []),
            suggested_improvements=feedback.get('suggestions', []),
            evaluator_comments=feedback.get('comments', ''),
            timestamp=datetime.utcnow()
        )
        
        # Store feedback
        self.feedback_history.append(feedback_record)
        
        logger.info(
            f"Collected human feedback for planogram {planogram_id}",
            component="code_improver",
            planogram_id=planogram_id,
            overall_rating=(
                feedback_record.layout_quality_rating + 
                feedback_record.visual_design_rating + 
                feedback_record.json_accuracy_rating
            ) / 3
        )
        
        return feedback_record
    
    def analyze_feedback_patterns(self, days: int = 30) -> CodeImprovementPlan:
        """Analyze patterns in generation feedback to identify code improvements"""
        
        # Filter recent feedback
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_feedback = [f for f in self.feedback_history if f.timestamp >= cutoff_date]
        
        if not recent_feedback:
            return CodeImprovementPlan(
                high_priority_fixes=[],
                code_areas_to_review=[],
                suggested_experiments=[]
            )
        
        # Analyze common issues
        common_issues = self._identify_common_issues(recent_feedback)
        priority_fixes = self._prioritize_code_improvements(common_issues)
        
        improvement_plan = CodeImprovementPlan(
            high_priority_fixes=priority_fixes,
            code_areas_to_review=[
                "src/planogram/generator.py:_calculate_shelf_layout()",
                "src/planogram/generator.py:_position_products()",
                "src/planogram/renderer.py:_render_product_blocks()",
                "src/planogram/abstraction_manager.py:_get_confidence_color()"
            ],
            suggested_experiments=[
                "A/B test different spacing algorithms",
                "Test alternative color coding systems", 
                "Experiment with brand-based vs confidence-based colors",
                "Try dynamic facing width based on product type"
            ]
        )
        
        return improvement_plan
    
    def _identify_common_issues(self, feedback_list: List[GenerationFeedback]) -> Dict[str, int]:
        """Identify most common issues from feedback"""
        issue_counts = {}
        
        for feedback in feedback_list:
            # Check ratings
            if feedback.layout_quality_rating <= 2:
                issue_counts['poor_layout'] = issue_counts.get('poor_layout', 0) + 1
            if feedback.visual_design_rating <= 2:
                issue_counts['poor_visual'] = issue_counts.get('poor_visual', 0) + 1
            if feedback.json_accuracy_rating <= 2:
                issue_counts['poor_accuracy'] = issue_counts.get('poor_accuracy', 0) + 1
            
            # Count specific issues
            for issue in feedback.specific_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return issue_counts
    
    def _prioritize_code_improvements(self, issue_counts: Dict[str, int]) -> List[GenerationIssue]:
        """Prioritize code improvements based on issue frequency"""
        priority_fixes = []
        
        # Sort by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        
        for issue_type, count in sorted_issues[:5]:  # Top 5 issues
            if issue_type == 'poor_layout':
                priority_fixes.append(GenerationIssue(
                    type="layout_algorithm",
                    severity="high" if count > 10 else "medium",
                    description=f"Layout issues reported {count} times",
                    suggested_fix="Refactor product positioning algorithm"
                ))
            elif issue_type == 'poor_visual':
                priority_fixes.append(GenerationIssue(
                    type="visual_rendering",
                    severity="high" if count > 10 else "medium",
                    description=f"Visual design issues reported {count} times",
                    suggested_fix="Enhance visual rendering system"
                ))
            elif issue_type == 'poor_accuracy':
                priority_fixes.append(GenerationIssue(
                    type="data_mapping",
                    severity="high",
                    description=f"Data accuracy issues reported {count} times",
                    suggested_fix="Review JSON to visual mapping logic"
                ))
        
        return priority_fixes 