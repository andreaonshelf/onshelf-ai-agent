"""
Planogram Generator
Convert JSON extraction data to visual planogram with abstraction support
"""

import json
from typing import Any, List, Union, Dict, Optional
from datetime import datetime

from ..models.extraction_models import ExtractionResult, ProductExtraction
from ..models.shelf_structure import ShelfStructure
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
    
    async def generate_from_abstraction(self, 
                                      planogram_data: Any,
                                      structure_context: ShelfStructure,
                                      abstraction_level: str) -> VisualPlanogram:
        """Generate visual planogram from abstraction data"""
        
        print(f"🏗️ Generating planogram from {abstraction_level}")
        
        # Calculate dimensions
        total_width_cm = structure_context.estimated_width_meters * 100
        total_height_cm = structure_context.shelf_count * self.standard_shelf_height_cm
        
        # Process shelves based on abstraction level
        shelf_lines = []
        total_products = 0
        total_facings = 0
        
        if abstraction_level == "brand_view":
            shelf_lines, total_products, total_facings = self._generate_brand_shelves(
                planogram_data, structure_context, total_width_cm
            )
        elif abstraction_level == "sku_view":
            shelf_lines, total_products, total_facings = self._generate_sku_shelves(
                planogram_data, structure_context, total_width_cm
            )
        else:  # product_view
            shelf_lines, total_products, total_facings = self._generate_product_shelves(
                planogram_data, structure_context, total_width_cm
            )
        
        # Calculate space utilization
        total_product_space = sum(
            sum(e.width_cm for e in shelf.elements if e.type == "product")
            for shelf in shelf_lines
        )
        total_space = total_width_cm * len(shelf_lines)
        space_utilization = (total_product_space / total_space) * 100 if total_space > 0 else 0
        
        # Create planogram
        planogram = VisualPlanogram(
            extraction_id=f"abstraction_{abstraction_level}",
            shelf_count=structure_context.shelf_count,
            total_width_cm=total_width_cm,
            total_height_cm=total_height_cm,
            shelves=shelf_lines,
            accuracy_score=0.95,  # Mock score
            total_products=total_products,
            total_facings=total_facings,
            space_utilization=space_utilization,
            original_image_dimensions={
                'width': 1920,
                'height': 1080
            },
            scale_factor=1.0
        )
        
        # Generate rendering data
        renderer = PlanogramRenderer()
        planogram.canvas_data = renderer.generate_canvas_javascript(planogram)
        planogram.svg_data = renderer.generate_svg(planogram)
        
        print(f"✅ Planogram generated: {planogram.shelf_count} shelves, {total_products} products, {total_facings} facings")
        return planogram
    
    def _generate_brand_shelves(self, brand_data, structure_context, total_width_cm):
        """Generate shelves for brand view"""
        shelf_lines = []
        total_products = len(brand_data.brand_blocks)
        total_facings = sum(block.total_facings for block in brand_data.brand_blocks)
        
        # Distribute brands across shelves
        brands_per_shelf = max(1, total_products // structure_context.shelf_count)
        
        for shelf_num in range(1, structure_context.shelf_count + 1):
            start_idx = (shelf_num - 1) * brands_per_shelf
            end_idx = min(start_idx + brands_per_shelf, total_products)
            shelf_brands = brand_data.brand_blocks[start_idx:end_idx]
            
            elements = []
            current_position = 0
            
            for brand in shelf_brands:
                element = ProductBlock(
                    name=brand.brand_name,
                    brand=brand.brand_name,
                    price=None,
                    facings=brand.total_facings,
                    width_cm=brand.block_width_cm,
                    confidence_color=brand.confidence_color,
                    pixel_coordinates={},
                    position_cm=current_position,
                    shelf_number=shelf_num
                )
                elements.append(element)
                current_position += brand.block_width_cm
            
            shelf_line = ShelfLine(
                shelf_number=shelf_num,
                y_position_cm=(shelf_num - 1) * self.standard_shelf_height_cm,
                elements=elements,
                total_width_cm=total_width_cm,
                utilization_percent=(current_position / total_width_cm) * 100
            )
            shelf_lines.append(shelf_line)
        
        return shelf_lines, total_products, total_facings
    
    def _generate_product_shelves(self, product_data, structure_context, total_width_cm):
        """Generate shelves for product view"""
        shelf_lines = []
        total_products = len(product_data.product_blocks)
        total_facings = sum(block.facing_count for block in product_data.product_blocks)
        
        # Group products by shelf
        shelves = {}
        for product in product_data.product_blocks:
            shelf_num = product.shelf_number
            if shelf_num not in shelves:
                shelves[shelf_num] = []
            shelves[shelf_num].append(product)
        
        # Generate shelf lines
        for shelf_num in range(1, structure_context.shelf_count + 1):
            shelf_products = shelves.get(shelf_num, [])
            
            elements = []
            current_position = 0
            
            for product in shelf_products:
                element = ProductBlock(
                    name=product.product_name,
                    brand=product.brand,
                    price=product.price,
                    facings=product.facing_count,
                    width_cm=product.block_width_cm,
                    confidence_color=product.confidence_color,
                    pixel_coordinates={},
                    position_cm=current_position,
                    shelf_number=shelf_num
                )
                elements.append(element)
                current_position += product.block_width_cm
            
            shelf_line = ShelfLine(
                shelf_number=shelf_num,
                y_position_cm=(shelf_num - 1) * self.standard_shelf_height_cm,
                elements=elements,
                total_width_cm=total_width_cm,
                utilization_percent=(current_position / total_width_cm) * 100 if total_width_cm > 0 else 0
            )
            shelf_lines.append(shelf_line)
        
        return shelf_lines, total_products, total_facings
    
    def _generate_sku_shelves(self, sku_data, structure_context, total_width_cm):
        """Generate shelves for SKU view"""
        shelf_lines = []
        total_products = len(set((sku.shelf_number, sku.position_on_shelf) for sku in sku_data.sku_blocks))
        total_facings = len(sku_data.sku_blocks)
        
        # Group SKUs by shelf
        shelves = {}
        for sku in sku_data.sku_blocks:
            shelf_num = sku.shelf_number
            if shelf_num not in shelves:
                shelves[shelf_num] = []
            shelves[shelf_num].append(sku)
        
        # Generate shelf lines
        for shelf_num in range(1, structure_context.shelf_count + 1):
            shelf_skus = shelves.get(shelf_num, [])
            
            elements = []
            current_position = 0
            
            for sku in shelf_skus:
                element = ProductBlock(
                    name=f"{sku.sku_name} (Facing {sku.facing_index})",
                    brand=sku.brand,
                    price=sku.price,
                    facings=1,  # Each SKU block is one facing
                    width_cm=sku.block_width_cm,
                    confidence_color=sku.confidence_color,
                    pixel_coordinates={},
                    position_cm=current_position,
                    shelf_number=shelf_num
                )
                elements.append(element)
                current_position += sku.block_width_cm
            
            shelf_line = ShelfLine(
                shelf_number=shelf_num,
                y_position_cm=(shelf_num - 1) * self.standard_shelf_height_cm,
                elements=elements,
                total_width_cm=total_width_cm,
                utilization_percent=(current_position / total_width_cm) * 100 if total_width_cm > 0 else 0
            )
            shelf_lines.append(shelf_line)
        
        return shelf_lines, total_products, total_facings

    # Keep existing methods for backward compatibility
    async def generate_planogram_from_json(self, extraction: Any) -> VisualPlanogram:
        """Legacy method for backward compatibility"""
        # Convert to new format and use abstraction system
        if hasattr(extraction, 'products'):
            from .abstraction_manager import PlanogramAbstractionManager
            abstraction_manager = PlanogramAbstractionManager()
            product_view = abstraction_manager.generate_product_view(extraction.products)
            
            return await self.generate_from_abstraction(
                product_view,
                extraction.structure if hasattr(extraction, 'structure') else None,
                "product_view"
            )
        
        # Fallback to original implementation
        return await self._legacy_generate_planogram(extraction)

    def _legacy_generate_planogram(self, extraction: Any) -> VisualPlanogram:
        """Legacy method for generating planogram"""
        # Implementation of the legacy method
        # This method should be implemented to handle the legacy planogram generation logic
        # It should return a VisualPlanogram object
        pass

    def validate_planogram(self, planogram: VisualPlanogram, extraction: Any) -> Dict[str, Any]:
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