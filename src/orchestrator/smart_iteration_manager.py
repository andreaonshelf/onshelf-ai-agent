"""
Smart Iteration Manager
Manages selective locking and targeted re-extraction between iterations
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from ..models.extraction_models import ExtractionResult, ProductExtraction
from ..models.shelf_structure import ShelfStructure
from ..utils import logger


@dataclass
class LockedPosition:
    """Represents a locked product position that shouldn't be re-extracted"""
    shelf: int
    position: int
    product_data: Dict
    confidence: float
    locked_at_iteration: int
    reason: str = "high_confidence"


@dataclass
class ExtractionFocus:
    """Defines what to focus on in the next iteration"""
    shelves_to_reextract: Set[int] = field(default_factory=set)
    positions_to_reextract: Set[Tuple[int, int]] = field(default_factory=set)  # (shelf, position)
    specific_issues: Dict[str, List[Dict]] = field(default_factory=dict)
    enhancement_strategies: Dict[str, str] = field(default_factory=dict)


class SmartIterationManager:
    """Manages intelligent iteration strategy with selective locking"""
    
    def __init__(self):
        self.locked_positions: Dict[Tuple[int, int], LockedPosition] = {}
        self.extraction_history: List[Dict] = []
        self.structure_locked: bool = False
        self.structure_data: Optional[ShelfStructure] = None
        
    def analyze_iteration_results(
        self,
        iteration: int,
        extraction_result: ExtractionResult,
        accuracy_analysis: Dict,
        structure: ShelfStructure
    ) -> ExtractionFocus:
        """Analyze results and determine what to lock and what to re-extract"""
        
        logger.info(
            f"Analyzing iteration {iteration} results for smart locking",
            component="smart_iteration",
            accuracy=accuracy_analysis.get("overall_accuracy", 0),
            products=len(extraction_result.products)
        )
        
        # Lock structure after first successful iteration
        if iteration == 1 and accuracy_analysis.get("structure_accuracy", 0) > 0.9:
            self.structure_locked = True
            self.structure_data = structure
            logger.info("Structure locked after iteration 1", component="smart_iteration")
        
        # Analyze products for locking
        focus = ExtractionFocus()
        products_by_position = self._group_products_by_position(extraction_result.products)
        
        # Check each position
        for (shelf, position), product in products_by_position.items():
            position_key = (shelf, position)
            
            # Determine if this position should be locked
            if self._should_lock_position(product, accuracy_analysis, position_key):
                # Lock this position
                self.locked_positions[position_key] = LockedPosition(
                    shelf=shelf,
                    position=position,
                    product_data=self._serialize_product(product),
                    confidence=product.extraction_confidence,
                    locked_at_iteration=iteration,
                    reason=self._get_lock_reason(product, accuracy_analysis)
                )
                logger.debug(
                    f"Locked position {shelf}-{position}: {product.name}",
                    component="smart_iteration"
                )
            else:
                # Mark for re-extraction
                focus.positions_to_reextract.add(position_key)
                focus.shelves_to_reextract.add(shelf)
                
                # Analyze specific issues
                if hasattr(accuracy_analysis, 'failure_areas'):
                    failure_info = accuracy_analysis.failure_areas.get(shelf, {}).get(position)
                    if failure_info:
                        issue_type = failure_info.error_type
                        if issue_type not in focus.specific_issues:
                            focus.specific_issues[issue_type] = []
                        focus.specific_issues[issue_type].append({
                            "shelf": shelf,
                            "position": position,
                            "details": failure_info
                        })
                        focus.enhancement_strategies[issue_type] = failure_info.enhancement_strategy
        
        # Check for missing positions (gaps)
        self._identify_missing_positions(structure, products_by_position, focus)
        
        # Log iteration summary
        logger.info(
            f"Iteration {iteration} locking summary",
            component="smart_iteration",
            locked_count=len(self.locked_positions),
            reextract_positions=len(focus.positions_to_reextract),
            reextract_shelves=len(focus.shelves_to_reextract),
            issue_types=list(focus.specific_issues.keys())
        )
        
        # Store in history
        self.extraction_history.append({
            "iteration": iteration,
            "locked_count": len(self.locked_positions),
            "focus": focus,
            "timestamp": datetime.utcnow()
        })
        
        return focus
    
    def get_locked_products(self) -> List[ProductExtraction]:
        """Get all locked products to preserve in next iteration"""
        locked_products = []
        
        for position_key, locked_pos in self.locked_positions.items():
            # Reconstruct product from locked data
            product_data = locked_pos.product_data.copy()
            product_data["locked_from_iteration"] = locked_pos.locked_at_iteration
            locked_products.append(product_data)
        
        return locked_products
    
    def get_extraction_instructions(self, focus: ExtractionFocus) -> Dict[str, Any]:
        """Generate specific instructions for the next iteration"""
        instructions = {
            "preserve_structure": self.structure_locked,
            "structure_data": self.structure_data.dict() if self.structure_data else None,
            "locked_positions": [
                {
                    "shelf": pos.shelf,
                    "position": pos.position,
                    "product_name": pos.product_data.get("name"),
                    "instruction": f"PRESERVE EXACT - Do not re-extract"
                }
                for pos in self.locked_positions.values()
            ],
            "focus_areas": [
                {
                    "shelf": shelf,
                    "positions": [p for s, p in focus.positions_to_reextract if s == shelf],
                    "instruction": f"RE-EXTRACT all products on shelf {shelf}"
                }
                for shelf in focus.shelves_to_reextract
            ],
            "enhancement_strategies": focus.enhancement_strategies,
            "specific_issues": focus.specific_issues
        }
        
        return instructions
    
    def _should_lock_position(
        self, 
        product: ProductExtraction, 
        accuracy_analysis: Dict,
        position_key: Tuple[int, int]
    ) -> bool:
        """Determine if a position should be locked"""
        
        # Already locked? Keep it locked
        if position_key in self.locked_positions:
            return True
        
        # High confidence extraction
        if product.extraction_confidence >= 0.95:
            return True
        
        # Check if this position has no issues in accuracy analysis
        if hasattr(accuracy_analysis, 'high_confidence_positions'):
            for high_conf_pos in accuracy_analysis.high_confidence_positions:
                if (high_conf_pos.shelf == position_key[0] and 
                    high_conf_pos.position == position_key[1]):
                    return True
        
        # Stable across multiple iterations
        position_history = self._get_position_history(position_key)
        if len(position_history) >= 2:
            # Check if product details are consistent
            if self._is_position_stable(position_history):
                return True
        
        return False
    
    def _get_lock_reason(self, product: ProductExtraction, accuracy_analysis: Dict) -> str:
        """Determine why a position was locked"""
        if product.extraction_confidence >= 0.95:
            return "high_confidence"
        elif hasattr(accuracy_analysis, 'visual_match') and accuracy_analysis.visual_match:
            return "visual_confirmation"
        else:
            return "stable_across_iterations"
    
    def _group_products_by_position(
        self, 
        products: List[ProductExtraction]
    ) -> Dict[Tuple[int, int], ProductExtraction]:
        """Group products by their shelf and position"""
        products_by_pos = {}
        
        for product in products:
            shelf = product.shelf_level
            position = product.position_on_shelf
            products_by_pos[(shelf, position)] = product
        
        return products_by_pos
    
    def _serialize_product(self, product: ProductExtraction) -> Dict:
        """Serialize product for storage"""
        return {
            "name": product.name,
            "brand": product.brand,
            "price": product.price,
            "shelf_level": product.shelf_level,
            "position_on_shelf": product.position_on_shelf,
            "facings_total": product.facings_total,
            "any_text": product.any_text,
            "extraction_confidence": product.extraction_confidence
        }
    
    def _identify_missing_positions(
        self,
        structure: ShelfStructure,
        products_by_position: Dict,
        focus: ExtractionFocus
    ):
        """Identify gaps where products might be missing"""
        for shelf in range(1, structure.shelf_count + 1):
            # Get all positions on this shelf
            shelf_positions = [p for (s, p) in products_by_position.keys() if s == shelf]
            
            if shelf_positions:
                min_pos = min(shelf_positions)
                max_pos = max(shelf_positions)
                
                # Check for gaps
                for pos in range(min_pos, max_pos + 1):
                    if (shelf, pos) not in products_by_position:
                        # Found a gap
                        focus.positions_to_reextract.add((shelf, pos))
                        focus.shelves_to_reextract.add(shelf)
                        
                        if "missing_product" not in focus.specific_issues:
                            focus.specific_issues["missing_product"] = []
                        focus.specific_issues["missing_product"].append({
                            "shelf": shelf,
                            "position": pos,
                            "details": {"type": "gap_in_sequence"}
                        })
    
    def _get_position_history(self, position_key: Tuple[int, int]) -> List[Dict]:
        """Get extraction history for a specific position"""
        history = []
        
        for iteration_data in self.extraction_history:
            # Would need to store more detailed data to implement this fully
            pass
        
        return history
    
    def _is_position_stable(self, position_history: List[Dict]) -> bool:
        """Check if a position has stable extractions across iterations"""
        # Simplified check - would need more sophisticated logic
        return len(position_history) >= 2