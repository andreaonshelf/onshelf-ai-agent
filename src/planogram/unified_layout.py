"""
Unified Layout Engine
Shared layout logic for both SVG and React planogram renderers
Ensures consistency between debugging SVG and production React views
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class LayoutProduct:
    """Unified product representation for layout"""
    brand: str
    name: str
    price: Optional[float]
    shelf_number: int
    position_on_shelf: int
    facing_count: int
    stack_count: int
    section: str  # Left/Center/Right
    confidence: float
    

@dataclass
class LayoutDimensions:
    """Standard dimensions for planogram layout"""
    shelf_width_cm: float = 250
    shelf_height_cm: float = 30
    product_width_cm: float = 8  # per facing
    gap_width_cm: float = 2
    margin_cm: float = 5
    

class UnifiedLayoutEngine:
    """
    Calculates product positions for consistent rendering
    Used by both SVG and React renderers
    """
    
    def __init__(self, dimensions: LayoutDimensions = None):
        self.dims = dimensions or LayoutDimensions()
        
    def calculate_product_position(self, 
                                 product: LayoutProduct,
                                 shelf_products: List[LayoutProduct]) -> Dict[str, float]:
        """
        Calculate exact position for a product
        Returns: {x, y, width, height} in cm
        """
        # Sort products by position
        sorted_products = sorted(shelf_products, key=lambda p: p.position_on_shelf)
        
        # Find gaps (missing position numbers)
        max_position = max(p.position_on_shelf for p in sorted_products)
        positions_filled = {p.position_on_shelf for p in sorted_products}
        gaps = set(range(1, max_position + 1)) - positions_filled
        
        # Calculate X position
        x = self.dims.margin_cm
        for pos in range(1, product.position_on_shelf):
            if pos in gaps:
                # Add gap space
                x += self.dims.gap_width_cm * 3  # Visible gap
            else:
                # Add product width
                matching_product = next(p for p in sorted_products if p.position_on_shelf == pos)
                x += matching_product.facing_count * self.dims.product_width_cm + self.dims.gap_width_cm
                
        # Calculate Y position (shelf-based)
        y = (product.shelf_number - 1) * self.dims.shelf_height_cm + self.dims.margin_cm
        
        # Calculate dimensions
        width = product.facing_count * self.dims.product_width_cm
        
        # Height depends on stacking
        if product.stack_count == 1:
            height = self.dims.shelf_height_cm * 0.9  # Full height
        else:
            height = (self.dims.shelf_height_cm * 0.9) / product.stack_count  # Divided for stacks
            
        return {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'stack_rows': product.stack_count
        }
    
    def calculate_section_bounds(self, shelf_width: float) -> Dict[str, Tuple[float, float]]:
        """
        Calculate section boundaries for Left/Center/Right
        Returns: {'Left': (start, end), 'Center': (start, end), 'Right': (start, end)}
        """
        section_width = (shelf_width - 2 * self.dims.margin_cm) / 3
        
        return {
            'Left': (self.dims.margin_cm, self.dims.margin_cm + section_width),
            'Center': (self.dims.margin_cm + section_width, self.dims.margin_cm + 2 * section_width),
            'Right': (self.dims.margin_cm + 2 * section_width, shelf_width - self.dims.margin_cm)
        }
    
    def get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence level"""
        if confidence >= 0.95:
            return '#10b981'  # Green - very high
        elif confidence >= 0.90:
            return '#3b82f6'  # Blue - high
        elif confidence >= 0.80:
            return '#f59e0b'  # Orange - medium
        else:
            return '#ef4444'  # Red - low
            
    def group_products_by_shelf(self, products: List[LayoutProduct]) -> Dict[int, List[LayoutProduct]]:
        """Group products by shelf number"""
        shelf_groups = {}
        for product in products:
            if product.shelf_number not in shelf_groups:
                shelf_groups[product.shelf_number] = []
            shelf_groups[product.shelf_number].append(product)
        return shelf_groups