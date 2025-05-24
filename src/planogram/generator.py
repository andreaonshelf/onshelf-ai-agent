"""
Planogram Generator
Convert JSON extraction data to visual planogram
"""

import json
from typing import List, Union, Dict, Optional
from datetime import datetime

from ..extraction.models import CompleteShelfExtraction, ProductExtraction
from .models import (
    VisualPlanogram, ProductBlock, EmptySpace, PromotionalElement,
    ShelfLine
)
from .renderer import PlanogramRenderer


class PlanogramGenerator:
    """Convert JSON extraction data to visual planogram using HTML5 Canvas + Fabric.js"""
    
    def __init__(self):
        # Standard retail measurements
        self.standard_facing_width_cm = 8
        self.standard_shelf_height_cm = 50
        self.standard_gap_width_cm = 2
        self.min_gap_for_oos = 15  # Minimum gap to consider out of stock
        
        # Color scheme for confidence levels
        self.confidence_colors = {
            'very_high': '#22c55e',  # Green
            'high': '#3b82f6',       # Blue
            'medium': '#f59e0b',     # Orange
            'low': '#ef4444'         # Red
        }
    
    async def generate_planogram_from_json(self, extraction: CompleteShelfExtraction) -> VisualPlanogram:
        """Convert CompleteShelfExtraction JSON to visual planogram"""
        
        print(f"🏗️ Generating planogram for extraction {extraction.extraction_id}")
        
        # Calculate dimensions
        total_width_cm = extraction.shelf_structure.estimated_width_meters * 100
        total_height_cm = extraction.shelf_structure.number_of_shelves * self.standard_shelf_height_cm
        
        # Calculate scale factor
        scale_factor = total_width_cm / extraction.shelf_structure.picture_width
        
        # Process shelves
        shelf_lines = []
        total_products = 0
        total_facings = 0
        
        for shelf_num in range(1, extraction.shelf_structure.number_of_shelves + 1):
            shelf_products = [p for p in extraction.products 
                            if int(p.section.horizontal) == shelf_num]
            
            # Sort products left to right
            shelf_products.sort(key=lambda p: p.position.l_position_on_section)
            
            # Generate shelf layout
            shelf_elements = self._generate_shelf_layout(
                shelf_products, total_width_cm, shelf_num, extraction
            )
            
            # Calculate utilization
            product_width = sum(e.width_cm for e in shelf_elements if e.type == "product")
            utilization = (product_width / total_width_cm) * 100
            
            # Create shelf line
            shelf_line = ShelfLine(
                shelf_number=shelf_num,
                y_position_cm=(shelf_num - 1) * self.standard_shelf_height_cm,
                elements=shelf_elements,
                total_width_cm=total_width_cm,
                utilization_percent=utilization
            )
            
            shelf_lines.append(shelf_line)
            
            # Update totals
            for element in shelf_elements:
                if element.type == "product":
                    total_products += 1
                    total_facings += element.facings
        
        # Calculate space utilization
        total_product_space = sum(
            sum(e.width_cm for e in shelf.elements if e.type == "product")
            for shelf in shelf_lines
        )
        total_space = total_width_cm * len(shelf_lines)
        space_utilization = (total_product_space / total_space) * 100 if total_space > 0 else 0
        
        # Create planogram
        planogram = VisualPlanogram(
            extraction_id=extraction.extraction_id,
            shelf_count=extraction.shelf_structure.number_of_shelves,
            total_width_cm=total_width_cm,
            total_height_cm=total_height_cm,
            shelves=shelf_lines,
            accuracy_score=extraction.accuracy_score,
            total_products=total_products,
            total_facings=total_facings,
            space_utilization=space_utilization,
            original_image_dimensions={
                'width': extraction.shelf_structure.picture_width,
                'height': extraction.shelf_structure.picture_height
            },
            scale_factor=scale_factor
        )
        
        # Generate rendering data
        renderer = PlanogramRenderer()
        planogram.canvas_data = renderer.generate_canvas_javascript(planogram)
        planogram.svg_data = renderer.generate_svg(planogram)
        
        print(f"✅ Planogram generated: {planogram.shelf_count} shelves, {total_products} products, {total_facings} facings")
        return planogram
    
    def _generate_shelf_layout(self, 
                             products: List[ProductExtraction],
                             total_width_cm: float,
                             shelf_number: int,
                             extraction: CompleteShelfExtraction) -> List[Union[ProductBlock, EmptySpace, PromotionalElement]]:
        """Generate layout for a single shelf"""
        
        shelf_elements = []
        current_position_cm = 0
        
        # Process products
        for i, product in enumerate(products):
            # Check for gap before product
            expected_position = self._calculate_expected_position(product, total_width_cm)
            
            if expected_position > current_position_cm + self.standard_gap_width_cm:
                gap_width = expected_position - current_position_cm
                empty_space = self._create_empty_space(
                    gap_width, current_position_cm, shelf_number, i == 0
                )
                shelf_elements.append(empty_space)
                current_position_cm += gap_width
            
            # Calculate product width based on facings
            product_width_cm = product.quantity.total_facings * self.standard_facing_width_cm
            
            # Create product block
            product_block = ProductBlock(
                name=product.name,
                brand=product.brand,
                price=product.price,
                facings=product.quantity.total_facings,
                width_cm=product_width_cm,
                confidence_color=self.confidence_colors.get(
                    product.confidence_category.value, 
                    self.confidence_colors['low']
                ),
                pixel_coordinates=product.pixel_coordinates.dict(),
                position_cm=current_position_cm,
                shelf_number=shelf_number
            )
            
            shelf_elements.append(product_block)
            current_position_cm += product_width_cm
        
        # Check for promotional elements
        if extraction.non_product_elements.promotional_materials:
            for promo in extraction.non_product_elements.promotional_materials:
                # Simple positioning based on description
                if f"shelf {shelf_number}" in promo.position.get('description', '').lower():
                    promo_element = PromotionalElement(
                        element_type=promo.material_type,
                        text=promo.promotional_text,
                        position_cm=current_position_cm,
                        shelf_number=shelf_number,
                        width_cm=10  # Standard width
                    )
                    shelf_elements.append(promo_element)
        
        # Fill remaining space
        if current_position_cm < total_width_cm:
            remaining_width = total_width_cm - current_position_cm
            if remaining_width > self.standard_gap_width_cm:
                empty_space = EmptySpace(
                    width_cm=remaining_width,
                    reason="end_of_shelf" if remaining_width < self.min_gap_for_oos else "potential_out_of_stock",
                    position_cm=current_position_cm,
                    shelf_number=shelf_number,
                    severity="warning" if remaining_width > self.min_gap_for_oos else "info"
                )
                shelf_elements.append(empty_space)
        
        return shelf_elements
    
    def _calculate_expected_position(self, product: ProductExtraction, total_width_cm: float) -> float:
        """Calculate expected position based on pixel coordinates"""
        # Simple linear mapping from pixels to cm
        pixel_ratio = product.pixel_coordinates.x / product.pixel_coordinates.width
        return pixel_ratio * total_width_cm
    
    def _create_empty_space(self, width_cm: float, position_cm: float, 
                           shelf_number: int, is_start: bool) -> EmptySpace:
        """Create empty space with appropriate classification"""
        if is_start and width_cm < 5:
            reason = "gap_detected"
            severity = "info"
        elif width_cm < self.min_gap_for_oos:
            reason = "gap_detected"
            severity = "info"
        else:
            reason = "potential_out_of_stock"
            severity = "warning"
        
        return EmptySpace(
            width_cm=width_cm,
            reason=reason,
            position_cm=position_cm,
            shelf_number=shelf_number,
            severity=severity
        )
    
    def validate_planogram(self, planogram: VisualPlanogram, extraction: CompleteShelfExtraction) -> Dict[str, any]:
        """Validate planogram against extraction data"""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Check product count
        planogram_products = sum(
            len([e for e in shelf.elements if e.type == "product"])
            for shelf in planogram.shelves
        )
        
        if planogram_products != len(extraction.products):
            validation_results['errors'].append(
                f"Product count mismatch: {planogram_products} in planogram vs {len(extraction.products)} extracted"
            )
            validation_results['is_valid'] = False
        
        # Check shelf count
        if planogram.shelf_count != extraction.shelf_structure.number_of_shelves:
            validation_results['errors'].append(
                f"Shelf count mismatch: {planogram.shelf_count} vs {extraction.shelf_structure.number_of_shelves}"
            )
            validation_results['is_valid'] = False
        
        # Check space utilization
        if planogram.space_utilization < 50:
            validation_results['warnings'].append(
                f"Low space utilization: {planogram.space_utilization:.1f}%"
            )
        
        # Add metrics
        validation_results['metrics'] = {
            'product_count': planogram_products,
            'total_facings': planogram.total_facings,
            'space_utilization': planogram.space_utilization,
            'accuracy_score': planogram.accuracy_score
        }
        
        return validation_results 