"""
Cumulative Feedback Manager
Manages cumulative learning and feedback between iterations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ..models.shelf_structure import ShelfStructure
from ..models.extraction_models import ProductExtraction, ConfidenceLevel
from ..utils import logger


class PositionAccuracy(BaseModel):
    """Accuracy data for a specific shelf position"""
    confidence: float
    primary_error: Optional[str] = None
    issues: List[str] = Field(default_factory=list)


class FailureArea(BaseModel):
    """Area that needs improvement in next iteration"""
    confidence: float
    error_type: str
    specific_issues: List[str]
    enhancement_strategy: str


class PositionLock(BaseModel):
    """High-confidence position to preserve"""
    shelf_number: int
    position_on_shelf: int
    confidence: float
    data: Dict
    instruction: str = "PRESERVE_EXACT"


class AccuracyAnalysis(BaseModel):
    """Detailed accuracy analysis with failure areas"""
    overall_accuracy: float
    shelf_level_accuracy: Dict[int, Dict]
    failure_areas: Dict[int, Dict]
    high_confidence_positions: List[PositionLock]
    improvement_areas: List[Dict]


class FocusedInstructions(BaseModel):
    """Instructions for next iteration based on failures"""
    preserve_exact: List[Dict]
    improve_focus: List[Dict]
    ignore_regions: List[Dict]
    enhanced_prompts: Dict[str, str]
    efficiency_metrics: Optional[Dict] = None


class ImageComparison(BaseModel):
    """Result of comparing original image to planogram"""
    matches: List[Dict]
    mismatches: List[Dict]
    missing_products: List[Dict]
    extra_products: List[Dict]
    overall_similarity: float


class CumulativeFeedbackManager:
    """Manages cumulative learning between iterations"""
    
    def __init__(self):
        logger.info(
            "Cumulative Feedback Manager initialized",
            component="feedback_manager"
        )
    
    def analyze_accuracy_with_failure_areas(self, 
                                          comparison_result: ImageComparison,
                                          structure: ShelfStructure) -> AccuracyAnalysis:
        """Detailed analysis of what succeeded vs failed by position"""
        
        logger.info(
            "Analyzing accuracy with failure areas",
            component="feedback_manager",
            overall_similarity=comparison_result.overall_similarity
        )
        
        accuracy_map = {}
        failure_areas = {}
        locked_positions = []
        
        # Initialize shelf accuracy tracking
        for shelf_num in range(1, structure.shelf_count + 1):
            accuracy_map[shelf_num] = {}
            failure_areas[shelf_num] = {}
        
        # Analyze matches (high confidence positions)
        for match in comparison_result.matches:
            shelf_num = match.get('shelf_number', 1)
            position_num = match.get('position_on_shelf', 1)
            confidence = match.get('confidence', 0.5)
            
            position_accuracy = PositionAccuracy(
                confidence=confidence,
                primary_error=None,
                issues=[]
            )
            
            accuracy_map[shelf_num][position_num] = position_accuracy
            
            if confidence >= 0.95:
                # HIGH CONFIDENCE - Lock this position
                locked_positions.append(PositionLock(
                    shelf_number=shelf_num,
                    position_on_shelf=position_num,
                    confidence=confidence,
                    data=match,
                    instruction="PRESERVE_EXACT"
                ))
        
        # Analyze mismatches (failure areas)
        for mismatch in comparison_result.mismatches:
            shelf_num = mismatch.get('shelf_number', 1)
            position_num = mismatch.get('position_on_shelf', 1)
            confidence = mismatch.get('confidence', 0.5)
            error_type = mismatch.get('error_type', 'unknown')
            
            position_accuracy = PositionAccuracy(
                confidence=confidence,
                primary_error=error_type,
                issues=mismatch.get('issues', [])
            )
            
            accuracy_map[shelf_num][position_num] = position_accuracy
            
            if confidence < 0.75:
                # LOW CONFIDENCE - Focus area for next iteration
                failure_areas[shelf_num][position_num] = FailureArea(
                    confidence=confidence,
                    error_type=error_type,
                    specific_issues=mismatch.get('issues', []),
                    enhancement_strategy=self._get_enhancement_strategy(error_type)
                )
        
        # Handle missing products
        for missing in comparison_result.missing_products:
            shelf_num = missing.get('expected_shelf', 1)
            position_num = missing.get('expected_position', 1)
            
            failure_areas[shelf_num][position_num] = FailureArea(
                confidence=0.0,
                error_type="missing_product",
                specific_issues=["Product not detected"],
                enhancement_strategy=self._get_enhancement_strategy("missing_product")
            )
        
        overall_accuracy = comparison_result.overall_similarity
        
        analysis = AccuracyAnalysis(
            overall_accuracy=overall_accuracy,
            shelf_level_accuracy=accuracy_map,
            failure_areas=failure_areas,
            high_confidence_positions=locked_positions,
            improvement_areas=self._prioritize_improvement_areas(failure_areas)
        )
        
        logger.info(
            f"Accuracy analysis complete: {overall_accuracy:.1%} overall",
            component="feedback_manager",
            overall_accuracy=overall_accuracy,
            locked_positions=len(locked_positions),
            failure_count=sum(len(failures) for failures in failure_areas.values())
        )
        
        return analysis
    
    def create_focused_extraction_instructions(self, 
                                             failure_areas: Dict,
                                             locked_positions: List[PositionLock],
                                             structure: ShelfStructure) -> FocusedInstructions:
        """Create specific instructions for next iteration"""
        
        logger.info(
            "Creating focused extraction instructions",
            component="feedback_manager",
            locked_count=len(locked_positions),
            failure_shelves=len(failure_areas)
        )
        
        instructions = FocusedInstructions(
            preserve_exact=[],
            improve_focus=[],
            ignore_regions=[],
            enhanced_prompts={}
        )
        
        # 1. Lock high-confidence positions
        for lock in locked_positions:
            instructions.preserve_exact.append({
                "shelf": lock.shelf_number,
                "position": lock.position_on_shelf,
                "instruction": f"KEEP EXACT: Shelf {lock.shelf_number}, Position {lock.position_on_shelf}",
                "data": lock.data,
                "confidence": lock.confidence
            })
        
        # 2. Focus on failure areas with enhanced prompts
        for shelf_num, shelf_failures in failure_areas.items():
            for position_num, failure_info in shelf_failures.items():
                instructions.improve_focus.append({
                    "shelf": shelf_num,
                    "position": position_num,
                    "error_type": failure_info.error_type,
                    "enhancement": failure_info.enhancement_strategy,
                    "instruction": f"RE-EXTRACT: Shelf {shelf_num}, Position {position_num} with focus on {failure_info.error_type}"
                })
                
                # Add enhanced prompt for this specific error type
                if failure_info.error_type not in instructions.enhanced_prompts:
                    instructions.enhanced_prompts[failure_info.error_type] = self._get_enhanced_prompt(failure_info.error_type)
        
        # 3. Calculate processing efficiency
        total_positions = structure.shelf_count * structure.products_per_shelf_estimate
        positions_to_reprocess = len(instructions.improve_focus)
        efficiency_gain = 1 - (positions_to_reprocess / total_positions) if total_positions > 0 else 0
        
        instructions.efficiency_metrics = {
            "total_positions": total_positions,
            "locked_positions": len(instructions.preserve_exact),
            "reprocess_positions": positions_to_reprocess,
            "efficiency_gain": efficiency_gain,
            "focus_percentage": (positions_to_reprocess / total_positions * 100) if total_positions > 0 else 0
        }
        
        logger.info(
            f"Instructions created: {efficiency_gain:.1%} efficiency gain",
            component="feedback_manager",
            efficiency_gain=efficiency_gain,
            locked=len(instructions.preserve_exact),
            focus=len(instructions.improve_focus)
        )
        
        return instructions
    
    def _get_enhancement_strategy(self, error_type: str) -> str:
        """Get enhancement strategy for specific error type"""
        strategies = {
            "price_unclear": "Enhanced OCR with price tag focus",
            "product_variant_confusion": "Detailed variant analysis with color/text differentiation",
            "position_uncertain": "Precise shelf grid mapping with edge detection",
            "missing_product": "Multi-angle detection with shadow/occlusion handling",
            "facing_count_error": "Individual facing boundary detection",
            "brand_unclear": "Logo recognition and text extraction enhancement",
            "unknown": "General accuracy improvement with multi-model consensus"
        }
        
        return strategies.get(error_type, strategies["unknown"])
    
    def _get_enhanced_prompt(self, error_type: str) -> str:
        """Get enhanced prompts for specific error types"""
        enhanced_prompts = {
            "price_unclear": """
            PRICE EXTRACTION FOCUS:
            - Look specifically for price tags, shelf tags, promotional stickers
            - Use OCR enhancement for small text
            - Check for promotional pricing (was/now prices)
            - Verify currency symbols and decimal places
            - Consider multi-buy offers (2 for £3, etc.)
            """,
            
            "product_variant_confusion": """
            PRODUCT VARIANT FOCUS:
            - Distinguish carefully between similar products (Classic vs Zero vs Light)
            - Read full product names including size/variant information
            - Look for color coding on packaging that indicates variants
            - Check for subtle text differences on labels
            - Note flavor variations and special editions
            """,
            
            "position_uncertain": """
            POSITION ACCURACY FOCUS:
            - Use shelf structure to determine exact placement
            - Count positions carefully from left edge
            - Note any gaps or spacing irregularities
            - Verify facing count and product boundaries
            - Check for shelf dividers or section markers
            """,
            
            "missing_product": """
            DETECTION ENHANCEMENT FOCUS:
            - Scan for partially visible products behind other items
            - Look for products in shadow areas or poor lighting
            - Check for products at unusual angles or positions
            - Scan gaps that might contain products
            - Consider reflections or glare hiding products
            """,
            
            "facing_count_error": """
            FACING COUNT FOCUS:
            - Count individual product units side by side
            - Look for product edges to determine boundaries
            - Don't confuse stacked products with facings
            - Check if products are pushed back on shelf
            - Verify consistent product width for facing calculation
            """,
            
            "brand_unclear": """
            BRAND IDENTIFICATION FOCUS:
            - Look for logos and brand marks
            - Read text on packaging carefully
            - Check for manufacturer information
            - Use color schemes associated with brands
            - Cross-reference with known product ranges
            """
        }
        
        return enhanced_prompts.get(error_type, "Enhanced extraction focus required for improved accuracy")
    
    def _prioritize_improvement_areas(self, failure_areas: Dict[int, Dict]) -> List[Dict]:
        """Prioritize which areas need most improvement"""
        improvement_priorities = []
        
        # Flatten and sort by confidence (lowest first)
        for shelf_num, shelf_failures in failure_areas.items():
            for position_num, failure_info in shelf_failures.items():
                improvement_priorities.append({
                    "shelf": shelf_num,
                    "position": position_num,
                    "confidence": failure_info.confidence,
                    "error_type": failure_info.error_type,
                    "priority_score": (1 - failure_info.confidence) * 100
                })
        
        # Sort by priority score (highest priority first)
        improvement_priorities.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return improvement_priorities[:10]  # Top 10 priority areas
    
    def calculate_iteration_improvement(self,
                                      current_analysis: AccuracyAnalysis,
                                      previous_analysis: AccuracyAnalysis) -> Dict[str, Any]:
        """Calculate improvement between iterations"""
        
        improvement = {
            "accuracy_change": current_analysis.overall_accuracy - previous_analysis.overall_accuracy,
            "accuracy_change_percent": (current_analysis.overall_accuracy - previous_analysis.overall_accuracy) * 100,
            "locked_positions_change": len(current_analysis.high_confidence_positions) - len(previous_analysis.high_confidence_positions),
            "failure_areas_change": sum(len(f) for f in current_analysis.failure_areas.values()) - sum(len(f) for f in previous_analysis.failure_areas.values()),
            "improvement_trend": "improving" if current_analysis.overall_accuracy > previous_analysis.overall_accuracy else "declining"
        }
        
        # Calculate shelf-level improvements
        shelf_improvements = {}
        for shelf_num in range(1, len(current_analysis.shelf_level_accuracy) + 1):
            current_shelf = current_analysis.shelf_level_accuracy.get(shelf_num, {})
            previous_shelf = previous_analysis.shelf_level_accuracy.get(shelf_num, {})
            
            current_avg = sum(p.confidence for p in current_shelf.values()) / len(current_shelf) if current_shelf else 0
            previous_avg = sum(p.confidence for p in previous_shelf.values()) / len(previous_shelf) if previous_shelf else 0
            
            shelf_improvements[shelf_num] = {
                "confidence_change": current_avg - previous_avg,
                "positions_improved": sum(1 for pos in current_shelf if current_shelf[pos].confidence > previous_shelf.get(pos, PositionAccuracy(confidence=0)).confidence)
            }
        
        improvement["shelf_improvements"] = shelf_improvements
        
        logger.info(
            f"Iteration improvement: {improvement['accuracy_change_percent']:+.1f}%",
            component="feedback_manager",
            accuracy_change=improvement["accuracy_change_percent"],
            trend=improvement["improvement_trend"]
        )
        
        return improvement 