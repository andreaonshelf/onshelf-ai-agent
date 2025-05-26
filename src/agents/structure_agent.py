"""
Structure Analysis Agent
Phase 0: Analyze shelf structure before product extraction
"""

import json
from typing import Dict, Optional
from datetime import datetime
import instructor
import openai
import anthropic

from ..config import SystemConfig
from ..utils import logger, with_retry, RetryConfig
from ..models.shelf_structure import ShelfStructure, ShelfSection, StructureConfidence


class StructureAnalysisAgent:
    """Phase 0: Analyze shelf structure before product extraction"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        
        # Initialize AI clients
        self.claude_client = instructor.from_anthropic(
            anthropic.Anthropic(api_key=config.anthropic_api_key)
        )
        
        logger.info(
            "Structure Analysis Agent initialized",
            component="structure_agent"
        )
    
    @with_retry(RetryConfig(max_retries=2, base_delay=1.0))
    async def analyze_structure(self, image_bytes: bytes, agent_id: str = None) -> ShelfStructure:
        """Analyze physical shelf structure only"""
        
        prompt = """
        Analyze this retail shelf for PHYSICAL STRUCTURE only:
        
        1. Count horizontal shelf levels from bottom (1) to top
        2. Estimate total shelf width in meters (narrow: <1m, medium: 1-2m, wide: >2m)
        3. Identify vertical section breaks/dividers
        4. Note special fixtures (end caps, promotional displays)
        5. Estimate products per shelf (8-12 typical)
        
        IGNORE PRODUCTS - analyze only the physical shelf structure.
        
        Return a structured analysis with:
        - shelf_count: Number of horizontal shelves (bottom=1)
        - estimated_width_meters: Approximate shelf width
        - sections: Vertical sections (left, center, right)
        - special_fixtures: Any end caps, displays, etc
        - products_per_shelf_estimate: Expected products per shelf
        - confidence: Your confidence in this analysis (0-1)
        """
        
        logger.info(
            "Analyzing shelf structure",
            component="structure_agent",
            agent_id=agent_id
        )
        
        try:
            # Use Claude-3.5-Sonnet for structure analysis
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": self._encode_image(image_bytes)
                            }
                        }
                    ]
                }],
                response_model=ShelfStructure
            )
            
            # Enhance with additional analysis
            response.analysis_timestamp = datetime.utcnow()
            response.analyzed_by = "claude-3-5-sonnet"
            
            logger.info(
                f"Structure analysis complete: {response.shelf_count} shelves, {response.estimated_width_meters}m width",
                component="structure_agent",
                agent_id=agent_id,
                shelf_count=response.shelf_count,
                width=response.estimated_width_meters
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Structure analysis failed: {e}",
                component="structure_agent",
                agent_id=agent_id,
                error=str(e)
            )
            raise
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """Encode image to base64 with compression if needed"""
        import base64
        
        # Compress image if needed for Claude's 5MB limit
        compressed_bytes = self._compress_image_if_needed(image_bytes)
        return base64.b64encode(compressed_bytes).decode('utf-8')
    
    def _compress_image_if_needed(self, img_data: bytes) -> bytes:
        """Compress image if it exceeds Claude's 5MB limit"""
        # Claude has a 5MB limit, but base64 encoding increases size by ~33%
        # So we need to ensure the image is under 3.75MB before encoding
        MAX_SIZE = 3.75 * 1024 * 1024  # 3.75MB to account for base64 overhead
        
        if len(img_data) <= MAX_SIZE:
            return img_data  # No compression needed
        
        logger.info(
            f"Compressing image for Claude: {len(img_data) / 1024 / 1024:.2f}MB -> <3.75MB",
            component="structure_agent",
            original_size_mb=len(img_data) / 1024 / 1024
        )
        
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(img_data))
        
        # Calculate resize ratio to fit within limit
        resize_ratio = (MAX_SIZE / len(img_data)) ** 0.5
        new_size = (int(img.width * resize_ratio), int(img.height * resize_ratio))
        
        # Resize with high quality
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img_resized.save(output, format='JPEG', quality=90, optimize=True)
        
        compressed_data = output.getvalue()
        logger.info(
            f"Image compressed: {len(compressed_data) / 1024 / 1024:.2f}MB",
            component="structure_agent",
            compressed_size_mb=len(compressed_data) / 1024 / 1024
        )
        
        return compressed_data
    
    def validate_structure(self, structure: ShelfStructure) -> Dict[str, any]:
        """Validate structure analysis results"""
        
        issues = []
        warnings = []
        
        # Validate shelf count
        if structure.shelf_count < 1 or structure.shelf_count > 10:
            issues.append(f"Unusual shelf count: {structure.shelf_count}")
        
        # Validate width
        if structure.estimated_width_meters < 0.5 or structure.estimated_width_meters > 5:
            warnings.append(f"Unusual shelf width: {structure.estimated_width_meters}m")
        
        # Validate products per shelf estimate
        if structure.products_per_shelf_estimate < 3 or structure.products_per_shelf_estimate > 30:
            warnings.append(f"Unusual products per shelf estimate: {structure.products_per_shelf_estimate}")
        
        # Check confidence
        if structure.confidence < 0.7:
            warnings.append(f"Low structure confidence: {structure.confidence:.2f}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "confidence": structure.confidence
        } 