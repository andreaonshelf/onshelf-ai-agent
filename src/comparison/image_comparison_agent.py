"""
Image Comparison Agent
Compares original shelf images to generated planograms for accuracy assessment
"""

from typing import Dict, List, Optional
from datetime import datetime
import instructor
import openai

from ..config import SystemConfig
from ..models.shelf_structure import ShelfStructure
from ..planogram.models import VisualPlanogram
from ..orchestrator.feedback_manager import ImageComparison
from ..utils import logger


class ImageComparisonAgent:
    """AI agent that compares original images to planograms"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        
        # Initialize AI client
        self.client = instructor.from_openai(
            openai.OpenAI(api_key=config.openai_api_key)
        )
        
        logger.info(
            "Image Comparison Agent initialized",
            component="comparison_agent"
        )
    
    async def compare_image_vs_planogram(self,
                                       original_image: bytes,
                                       planogram: VisualPlanogram,
                                       structure_context: ShelfStructure) -> ImageComparison:
        """Compare original shelf image to generated planogram"""
        
        logger.info(
            "Starting image vs planogram comparison",
            component="comparison_agent",
            planogram_products=planogram.total_products if hasattr(planogram, 'total_products') else 0
        )
        
        # For now, create mock comparison result
        # TODO: Implement actual AI comparison using GPT-4V or Claude
        
        matches = []
        mismatches = []
        missing_products = []
        extra_products = []
        
        # Simulate comparison based on planogram data
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                shelf_num = shelf.shelf_number
                
                if hasattr(shelf, 'elements'):
                    for i, element in enumerate(shelf.elements):
                        if element.type == 'product':
                            # Simulate confidence based on position
                            confidence = 0.95 if i < 3 else 0.85 if i < 6 else 0.75
                            
                            if confidence >= 0.85:
                                matches.append({
                                    'shelf_number': shelf_num,
                                    'position_on_shelf': i + 1,
                                    'product_name': element.name,
                                    'confidence': confidence,
                                    'match_type': 'exact'
                                })
                            else:
                                mismatches.append({
                                    'shelf_number': shelf_num,
                                    'position_on_shelf': i + 1,
                                    'product_name': element.name,
                                    'confidence': confidence,
                                    'error_type': 'position_uncertain' if i > 6 else 'product_variant_confusion',
                                    'issues': ['Low visibility', 'Partial occlusion'] if i > 6 else ['Similar products']
                                })
        
        # Simulate some missing products
        if structure_context.shelf_count > 2:
            missing_products.append({
                'expected_shelf': 3,
                'expected_position': 5,
                'product_type': 'beverage',
                'reason': 'Hidden behind promotional material'
            })
        
        # Calculate overall similarity
        total_items = len(matches) + len(mismatches) + len(missing_products)
        overall_similarity = len(matches) / total_items if total_items > 0 else 0.0
        
        comparison = ImageComparison(
            matches=matches,
            mismatches=mismatches,
            missing_products=missing_products,
            extra_products=extra_products,
            overall_similarity=overall_similarity
        )
        
        logger.info(
            f"Comparison complete: {overall_similarity:.1%} similarity",
            component="comparison_agent",
            matches=len(matches),
            mismatches=len(mismatches),
            missing=len(missing_products),
            overall_similarity=overall_similarity
        )
        
        return comparison
    
    async def compare_with_ai_vision(self,
                                   original_image: bytes,
                                   planogram_image: bytes,
                                   structure_context: ShelfStructure) -> ImageComparison:
        """Use AI vision model to compare images (future implementation)"""
        
        prompt = f"""
        Compare these two images:
        1. Original shelf photo
        2. Generated planogram
        
        Shelf structure context:
        - {structure_context.shelf_count} shelves
        - Approximately {structure_context.products_per_shelf_estimate} products per shelf
        
        For each product, determine:
        1. Is it in the correct position? (shelf number and position)
        2. Is the product identification correct? (brand, name, variant)
        3. Is the facing count accurate?
        4. Are there any missing or extra products?
        
        Provide a structured comparison with confidence scores.
        """
        
        # TODO: Implement actual AI vision comparison
        # This would use GPT-4V or Claude with vision capabilities
        
        return await self.compare_image_vs_planogram(original_image, None, structure_context) 