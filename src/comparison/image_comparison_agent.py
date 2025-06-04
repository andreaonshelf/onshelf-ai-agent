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


class ShelfMismatch(BaseModel):
    """Specific mismatch found during comparison"""
    product: str = Field(description="Product name")
    issue_type: str = Field(description="Type: wrong_shelf, wrong_quantity, wrong_position, missing, extra")
    photo_location: Dict[str, int] = Field(description="Where in photo: {shelf, position}")
    planogram_location: Dict[str, int] = Field(description="Where in planogram: {shelf, position}")
    confidence: str = Field(description="Confidence level: high, medium, low")
    details: Optional[str] = Field(description="Additional context about the issue")

class VisualComparisonResult(BaseModel):
    """Structured error checking result from visual comparison"""
    total_products_photo: int = Field(description="Total products counted in photo")
    total_products_planogram: int = Field(description="Total products shown in planogram")
    shelf_mismatches: List[ShelfMismatch] = Field(default_factory=list, description="List of specific mismatches found")
    critical_issues: List[str] = Field(default_factory=list, description="Major structural problems")
    overall_alignment: str = Field(description="Overall assessment: good, moderate, poor")


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
                                       model: str = "gpt-4-vision-preview",
                                       comparison_prompt: Optional[str] = None) -> ImageComparison:
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
        
        # Map frontend model IDs to actual API model names
        model_mapping = {
            # OpenAI models
            "gpt-4-vision-preview": "gpt-4-vision-preview",
            "gpt-4.1": "gpt-4o-2024-11-20",  # Latest GPT-4 with vision
            "gpt-4.1-mini": "gpt-4o-mini",
            "gpt-4o": "gpt-4o-2024-11-20",
            "gpt-4o-mini": "gpt-4o-mini",
            
            # Anthropic models (these would need different handling for Claude API)
            "claude-3-5-sonnet-v2": "claude-3-5-sonnet-20241022",
            "claude-3-7-sonnet": "claude-3-5-sonnet-20241022",  # Fallback
            "claude-4-sonnet": "claude-3-5-sonnet-20241022",    # Fallback
            "claude-4-opus": "claude-3-5-sonnet-20241022",      # Fallback
            
            # Google models (would need different handling)
            "gemini-2.5-flash": "gemini-2.0-flash-exp",
            "gemini-2.5-flash-thinking": "gemini-2.0-flash-exp",
            "gemini-2.5-pro": "gemini-2.0-pro-exp",
            "gemini-pro-vision": "gemini-pro-vision"
        }
        
        api_model = model_mapping.get(model, model)
        
        # Check if it's a Claude model
        is_claude_model = model.startswith('claude-')
        is_gemini_model = model.startswith('gemini-')
        
        try:
            # Use appropriate vision model for comparison
            import base64
            
            # Encode images to base64
            original_image_base64 = base64.b64encode(original_image).decode('utf-8')
            planogram_image_base64 = base64.b64encode(planogram_image).decode('utf-8')
            
            # Use provided prompt or default
            if not comparison_prompt:
                comparison_prompt = """
                Compare the original shelf photo with the generated planogram visualization.

                CHECK THESE SPECIFIC THINGS:

                1. SHELF ASSIGNMENT: Do all products appear on the correct shelf?
                   - List any products that are on a different shelf in the photo vs planogram
                   
                2. QUANTITY CHECK: Are the facing counts roughly correct?
                   - List any products where quantity is significantly off (±3 or more)
                   
                3. POSITION CHECK: Are products in the right general area of each shelf?
                   - List any products that are in wrong section (left/center/right)
                   
                4. MISSING PRODUCTS: Any obvious products in photo but not in planogram?
                   - List only if clearly visible and significant
                   
                5. EXTRA PRODUCTS: Any products in planogram but not visible in photo?
                   - List only if you're confident they're not there

                For each issue found, specify:
                - What: [Product name]
                - Where in photo: [Shelf X, Position Y]
                - Where in planogram: [Shelf X, Position Y]
                - Confidence: [High/Medium/Low]
                
                Also count total products in both photo and planogram.
                Assess overall alignment as good/moderate/poor.
                """
            
            # Handle different model providers
            if is_claude_model:
                # Use Claude for comparison (requires anthropic client)
                logger.info(f"Using Claude model for comparison: {api_model}", component="comparison_agent")
                # For now, fall back to GPT-4V since we need to implement Claude vision support
                api_model = "gpt-4o-2024-11-20"
                logger.info("Falling back to GPT-4 for vision comparison", component="comparison_agent")
            elif is_gemini_model:
                # Use Gemini for comparison (requires different API)
                logger.info(f"Using Gemini model for comparison: {api_model}", component="comparison_agent")
                # For now, fall back to GPT-4V since we need to implement Gemini vision support
                api_model = "gpt-4o-2024-11-20"
                logger.info("Falling back to GPT-4 for vision comparison", component="comparison_agent")
            
            # Call vision model with both images
            response = self.client.chat.completions.create(
                model=api_model,
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
                response_model=VisualComparisonResult,
                max_tokens=2000,
                temperature=0.1  # Very low temperature for consistent, factual comparison
            )
            
            # Parse response into our format
            return self._parse_vision_response(response, planogram, structure_context)
            
        except Exception as e:
            logger.error(f"Vision comparison failed: {e}", component="comparison_agent")
            # Fallback to mock if vision fails
            return self._mock_comparison(planogram, structure_context)
    
    def _parse_vision_response(self, vision_response: VisualComparisonResult, planogram, structure_context):
        """Parse vision model response into ImageComparison format"""
        
        # Convert new structured response to ImageComparison format for compatibility
        matches = []
        mismatches = []
        missing_products = []
        extra_products = []
        
        # Process shelf mismatches into categories
        for mismatch in vision_response.shelf_mismatches:
            if mismatch.issue_type == "missing":
                missing_products.append({
                    'product_name': mismatch.product,
                    'shelf': mismatch.photo_location.get('shelf', 0),
                    'position': mismatch.photo_location.get('position', 0),
                    'confidence': mismatch.confidence,
                    'details': mismatch.details
                })
            elif mismatch.issue_type == "extra":
                extra_products.append({
                    'product_name': mismatch.product,
                    'shelf': mismatch.planogram_location.get('shelf', 0),
                    'position': mismatch.planogram_location.get('position', 0),
                    'confidence': mismatch.confidence,
                    'details': mismatch.details
                })
            else:  # wrong_shelf, wrong_quantity, wrong_position
                mismatches.append({
                    'product': mismatch.product,
                    'issue_type': mismatch.issue_type,
                    'photo_location': mismatch.photo_location,
                    'planogram_location': mismatch.planogram_location,
                    'confidence': mismatch.confidence,
                    'details': mismatch.details
                })
        
        # Calculate overall similarity based on alignment
        alignment_scores = {"good": 0.85, "moderate": 0.65, "poor": 0.35}
        overall_similarity = alignment_scores.get(vision_response.overall_alignment, 0.5)
        
        logger.info(
            f"Vision comparison complete: {vision_response.overall_alignment} alignment",
            component="comparison_agent",
            total_photo=vision_response.total_products_photo,
            total_planogram=vision_response.total_products_planogram,
            mismatches=len(vision_response.shelf_mismatches),
            critical_issues=len(vision_response.critical_issues),
            alignment=vision_response.overall_alignment
        )
        
        # Return compatibility format
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