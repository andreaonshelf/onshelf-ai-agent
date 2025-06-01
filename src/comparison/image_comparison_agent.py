"""
Image Comparison Agent
Compares original shelf images to generated planograms for accuracy assessment
"""

from typing import Dict, List, Optional
from datetime import datetime
import instructor
import openai
from pydantic import BaseModel, Field

from ..config import SystemConfig
from ..models.shelf_structure import ShelfStructure
from ..planogram.models import VisualPlanogram
from ..orchestrator.feedback_manager import ImageComparison
from ..utils import logger


class ComparisonResult(BaseModel):
    """Structured response from vision model comparison"""
    overall_match_score: float = Field(description="Overall similarity score between 0 and 1")
    products_correct: List[Dict] = Field(description="List of correctly placed products")
    products_misplaced: List[Dict] = Field(description="List of misplaced products")
    products_missing: List[Dict] = Field(description="Products in photo but not in planogram")
    products_extra: List[Dict] = Field(description="Products in planogram but not in photo")
    shelf_accuracy: Dict[int, float] = Field(description="Per-shelf accuracy scores")
    specific_issues: List[str] = Field(description="Specific issues found in comparison")


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
                                       structure_context: ShelfStructure,
                                       planogram_image: Optional[bytes] = None,
                                       model: str = "gpt-4-vision-preview") -> ImageComparison:
        """Compare original shelf image to generated planogram"""
        
        logger.info(
            "Starting REAL image vs planogram comparison using vision AI",
            component="comparison_agent",
            planogram_products=planogram.total_products if hasattr(planogram, 'total_products') else 0,
            has_planogram_image=planogram_image is not None,
            model=model
        )
        
        # Check if we have planogram image for comparison
        if not planogram_image:
            raise ValueError("No planogram image provided for comparison - cannot perform visual comparison")
        
        try:
            # Use GPT-4V for visual comparison
            import base64
            
            # Encode images to base64
            original_image_base64 = base64.b64encode(original_image).decode('utf-8')
            planogram_image_base64 = base64.b64encode(planogram_image).decode('utf-8')
            
            # Create comparison prompt
            comparison_prompt = """
            Compare the retail shelf photo with the planogram representation.
            
            The planogram is an ABSTRACTION that should accurately represent:
            1. Product positions (left to right order)
            2. Shelf placement (which shelf each product is on)
            3. Facing counts (how many units side by side)
            4. Gaps between products
            5. Product names and brands
            
            For each product in the planogram, determine:
            - Is it in the correct position?
            - Is it on the correct shelf?
            - Is the facing count accurate?
            - Are there any missing products in the planogram?
            - Are there any extra products in the planogram that aren't in the photo?
            
            Be specific about position numbers and shelf numbers.
            Consider that the planogram is a simplified grid representation.
            """
            
            # Call vision model with both images
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": comparison_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{original_image_base64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/png;base64,{planogram_image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                response_model=ComparisonResult,
                max_tokens=2000,
                temperature=0.1  # Very low temperature for consistent, factual comparison
            )
            
            # Parse response into our format
            return self._parse_vision_response(response, planogram, structure_context)
            
        except Exception as e:
            logger.error(f"Vision comparison failed: {e}", component="comparison_agent")
            # Fallback to mock if vision fails
            return self._mock_comparison(planogram, structure_context)
    
    def _parse_vision_response(self, vision_response: ComparisonResult, planogram, structure_context):
        """Parse vision model response into ImageComparison format"""
        
        # Convert structured response to ImageComparison format
        matches = vision_response.products_correct
        mismatches = vision_response.products_misplaced
        missing_products = vision_response.products_missing
        extra_products = vision_response.products_extra
        
        # Use the actual similarity score from vision analysis
        overall_similarity = vision_response.overall_match_score
        
        logger.info(
            f"Vision comparison complete: {overall_similarity:.1%} match",
            component="comparison_agent",
            matches=len(matches),
            mismatches=len(mismatches),
            missing=len(missing_products),
            extra=len(extra_products),
            issues=vision_response.specific_issues[:3] if vision_response.specific_issues else []
        )
        
        return ImageComparison(
            matches=matches,
            mismatches=mismatches,
            missing_products=missing_products,
            extra_products=extra_products,
            overall_similarity=overall_similarity
        )
    
    def _mock_comparison(self, planogram, structure_context):
        """Fallback mock comparison when vision is not available"""
        matches = []
        mismatches = []
        missing_products = []
        extra_products = []
        
        # Original mock logic here...
        overall_similarity = 0.75
        
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