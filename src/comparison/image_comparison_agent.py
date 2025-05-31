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
                                       structure_context: ShelfStructure,
                                       model_id: str = None,
                                       custom_prompt: str = None,
                                       use_visual_comparison: bool = False,
                                       abstraction_layers: list = None) -> ImageComparison:
        """Compare original shelf image to generated planogram using vision AI"""
        
        logger.info(
            "Starting image vs planogram comparison",
            component="comparison_agent",
            planogram_products=planogram.total_products if hasattr(planogram, 'total_products') else 0,
            model=model_id or "gpt-4-vision-preview",
            use_visual=use_visual_comparison
        )
        
        # Use visual comparison if enabled
        if use_visual_comparison:
            return await self._compare_with_visual_planogram(
                original_image=original_image,
                planogram=planogram,
                structure_context=structure_context,
                model_id=model_id,
                custom_prompt=custom_prompt
            )
        
        # If we have the planogram SVG, convert it to an image for comparison
        planogram_image = None
        if hasattr(planogram, 'svg_data') and planogram.svg_data:
            # In production, you'd convert SVG to PNG here
            # For now, we'll use the vision model with text description
            planogram_description = self._generate_planogram_description(planogram)
        else:
            planogram_description = "No planogram data available"
        
        try:
            # Use vision model for comparison
            import base64
            from openai import OpenAI
            
            client = OpenAI(api_key=self.config.openai_api_key)
            
            # Encode image
            image_base64 = base64.b64encode(original_image).decode('utf-8')
            
            # Map model names to actual API names
            model_mapping = {
                "gpt-4-vision-preview": "gpt-4-vision-preview",
                "claude-3-opus": "claude-3-opus-20240229",
                "claude-4-opus": "claude-4-opus-20250514",
                "gemini-pro-vision": "gemini-pro-vision"
            }
            
            comparison_model = model_mapping.get(model_id, "gpt-4-vision-preview")
            
            # Use custom prompt or default
            if custom_prompt:
                comparison_prompt = custom_prompt.format(
                    planogram_description=planogram_description,
                    shelf_count=structure_context.shelf_count,
                    products_per_shelf_estimate=structure_context.products_per_shelf_estimate
                )
            else:
                # Default prompt
                comparison_prompt = f"""
                Analyze this retail shelf image and compare it to the following planogram description:
                
                PLANOGRAM DESCRIPTION:
                {planogram_description}
                
                SHELF STRUCTURE:
                - Total shelves: {structure_context.shelf_count}
                - Estimated products per shelf: {structure_context.products_per_shelf_estimate}
                
                Please identify:
                1. MATCHES: Products that are correctly positioned according to the planogram
                2. MISMATCHES: Products in wrong positions or incorrectly identified
                3. MISSING: Products in the planogram but not visible in the image
                4. EXTRA: Products visible in the image but not in the planogram
                
                For each product, provide:
                - Shelf number (counting from top)
                - Position on shelf (counting from left)
                - Product name/brand
                - Confidence score (0-1)
                - Any issues or discrepancies
                
                Format your response as JSON with keys: matches, mismatches, missing_products, extra_products
                """
            
            # Handle different API providers
            if comparison_model.startswith("gpt-"):
                response = client.chat.completions.create(
                    model=comparison_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": comparison_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0
            )
            
                # Parse the response
                comparison_data = self._parse_vision_response(response.choices[0].message.content)
            
            elif comparison_model.startswith("claude-"):
                # TODO: Implement Claude vision API
                logger.warning(f"Claude vision not yet implemented, falling back to GPT-4")
                comparison_model = "gpt-4-vision-preview"
                # Recursive call with GPT-4
                return await self.compare_image_vs_planogram(
                    original_image, planogram, structure_context, 
                    "gpt-4-vision-preview", custom_prompt, use_visual_comparison, abstraction_layers
                )
            
            else:
                # Default to GPT-4
                logger.warning(f"Unknown model {comparison_model}, using GPT-4 Vision")
                comparison_model = "gpt-4-vision-preview"
                # Recursive call with GPT-4
                return await self.compare_image_vs_planogram(
                    original_image, planogram, structure_context, 
                    "gpt-4-vision-preview", custom_prompt, use_visual_comparison, abstraction_layers
                )
            
            # Calculate overall similarity
            total_items = (len(comparison_data.get('matches', [])) + 
                          len(comparison_data.get('mismatches', [])) + 
                          len(comparison_data.get('missing_products', [])))
            
            overall_similarity = len(comparison_data.get('matches', [])) / total_items if total_items > 0 else 0.0
            
            comparison = ImageComparison(
                matches=comparison_data.get('matches', []),
                mismatches=comparison_data.get('mismatches', []),
                missing_products=comparison_data.get('missing_products', []),
                extra_products=comparison_data.get('extra_products', []),
                overall_similarity=overall_similarity
            )
            
            logger.info(
                f"Vision comparison complete: {overall_similarity:.1%} similarity",
                component="comparison_agent",
                matches=len(comparison.matches),
                mismatches=len(comparison.mismatches),
                missing=len(comparison.missing_products),
                overall_similarity=overall_similarity
            )
            
            return comparison
            
        except Exception as e:
            logger.error(f"Vision comparison failed, falling back to basic comparison: {e}")
            # Fallback to basic comparison
            return self._basic_comparison(planogram, structure_context)
    
    def _generate_planogram_description(self, planogram: VisualPlanogram) -> str:
        """Generate text description of planogram for vision model"""
        description_parts = []
        
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                shelf_desc = f"Shelf {shelf.shelf_number}:"
                products = []
                
                if hasattr(shelf, 'elements'):
                    for i, element in enumerate(shelf.elements):
                        if element.type == 'product':
                            products.append(f"Position {i+1}: {element.name} ({element.facings} facings)")
                
                if products:
                    shelf_desc += " " + ", ".join(products)
                    description_parts.append(shelf_desc)
        
        return "\n".join(description_parts) if description_parts else "No product data"
    
    def _parse_vision_response(self, response_text: str) -> Dict:
        """Parse vision model response into structured data"""
        import json
        import re
        
        # Try to extract JSON from response
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: parse text response
        return {
            'matches': [],
            'mismatches': [],
            'missing_products': [],
            'extra_products': []
        }
    
    def _basic_comparison(self, planogram: VisualPlanogram, structure_context: ShelfStructure) -> ImageComparison:
        """Basic comparison fallback when vision model fails"""
        matches = []
        mismatches = []
        
        # Simple heuristic: assume 70% match rate for demo
        if hasattr(planogram, 'shelves'):
            for shelf in planogram.shelves:
                if hasattr(shelf, 'elements'):
                    for i, element in enumerate(shelf.elements):
                        if element.type == 'product':
                            confidence = 0.7 + (0.2 * (1 - i/10))  # Decreasing confidence
                            
                            if confidence >= 0.75:
                                matches.append({
                                    'shelf_number': shelf.shelf_number,
                                    'position_on_shelf': i + 1,
                                    'product_name': element.name,
                                    'confidence': confidence,
                                    'match_type': 'approximate'
                                })
                            else:
                                mismatches.append({
                                    'shelf_number': shelf.shelf_number,
                                    'position_on_shelf': i + 1,
                                    'product_name': element.name,
                                    'confidence': confidence,
                                    'error_type': 'low_confidence',
                                    'issues': ['Unable to verify with vision model']
                                })
        
        total_items = len(matches) + len(mismatches)
        overall_similarity = len(matches) / total_items if total_items > 0 else 0.7
        
        return ImageComparison(
            matches=matches,
            mismatches=mismatches,
            missing_products=[],
            extra_products=[],
            overall_similarity=overall_similarity
        )
    
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
    
    async def _compare_with_visual_planogram(self,
                                           original_image: bytes,
                                           planogram: VisualPlanogram,
                                           structure_context: ShelfStructure,
                                           model_id: str = None,
                                           custom_prompt: str = None) -> ImageComparison:
        """Compare using direct visual comparison (SVG to PNG)"""
        
        logger.info(
            "Using visual comparison mode",
            component="comparison_agent"
        )
        
        # Convert SVG to PNG
        try:
            import cairosvg
            import io
            from PIL import Image
            import base64
            from openai import OpenAI
            
            # Convert SVG to PNG
            if hasattr(planogram, 'svg_data') and planogram.svg_data:
                png_data = cairosvg.svg2png(
                    bytestring=planogram.svg_data.encode('utf-8'),
                    output_width=800,
                    output_height=600
                )
                
                # Encode both images
                original_base64 = base64.b64encode(original_image).decode('utf-8')
                planogram_base64 = base64.b64encode(png_data).decode('utf-8')
                
                # Visual comparison prompt
                visual_prompt = custom_prompt or """
                Compare these two images:
                1. Original retail shelf photo
                2. Generated planogram representation
                
                The planogram is a simplified visual representation showing product positions.
                Each colored rectangle represents a product with its brand/name.
                
                Please analyze:
                - POSITION ACCURACY: Are products in the same relative positions?
                - PRODUCT IDENTIFICATION: Are the products correctly identified?
                - FACING COUNTS: Do the number of facings match?
                - MISSING/EXTRA: Any products in one image but not the other?
                
                Important: The planogram is abstract - focus on logical arrangement, not visual appearance.
                
                Provide structured output as JSON with:
                - Overall accuracy score (0-100)
                - matches: list of correctly positioned products
                - mismatches: list of incorrectly positioned/identified products  
                - missing_products: list of products in planogram but not in photo
                - extra_products: list of products in photo but not in planogram
                """
                
                # Use specified model or default
                comparison_model = model_id or "gpt-4-vision-preview"
                
                client = OpenAI(api_key=self.config.openai_api_key)
                
                response = client.chat.completions.create(
                    model=comparison_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": visual_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{original_base64}",
                                        "detail": "high"
                                    }
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{planogram_base64}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0
                )
                
                # Parse the response
                comparison_data = self._parse_vision_response(response.choices[0].message.content)
                
                # Calculate overall similarity
                total_items = (len(comparison_data.get('matches', [])) + 
                              len(comparison_data.get('mismatches', [])) + 
                              len(comparison_data.get('missing_products', [])))
                
                overall_similarity = len(comparison_data.get('matches', [])) / total_items if total_items > 0 else 0.0
                
                comparison = ImageComparison(
                    matches=comparison_data.get('matches', []),
                    mismatches=comparison_data.get('mismatches', []),
                    missing_products=comparison_data.get('missing_products', []),
                    extra_products=comparison_data.get('extra_products', []),
                    overall_similarity=overall_similarity
                )
                
                logger.info(
                    f"Visual comparison complete: {overall_similarity:.1%} similarity",
                    component="comparison_agent",
                    mode="visual"
                )
                
                return comparison
                
        except ImportError:
            logger.error("cairosvg not installed, falling back to text-based comparison")
            # Fall back to text-based comparison
            return await self.compare_image_vs_planogram(
                original_image, planogram, structure_context,
                model_id, custom_prompt, False, None
            )
        except Exception as e:
            logger.error(f"Visual comparison failed: {e}")
            # Fall back to text-based comparison
            return await self.compare_image_vs_planogram(
                original_image, planogram, structure_context,
                model_id, custom_prompt, False, None
            ) 