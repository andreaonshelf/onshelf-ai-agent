"""
Multi-Image Coordination System
Intelligently coordinate analysis across overview and detail images
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum
import base64
from .logger import logger


class ImageType(str, Enum):
    """Types of images in the capture set"""
    OVERVIEW = "overview"
    TOP_DETAIL = "top_detail"
    BOTTOM_DETAIL = "bottom_detail"
    SECTION_DETAIL = "section_detail"
    UNKNOWN = "unknown"


class ImageClassifier:
    """Classify images based on filename and content"""
    
    @staticmethod
    def classify_image(filename: str, image_data: bytes) -> ImageType:
        """Classify image type based on filename and metadata"""
        filename_lower = filename.lower()
        
        # Classification based on filename keywords
        if any(keyword in filename_lower for keyword in ['overview', 'wide', 'full', 'complete']):
            return ImageType.OVERVIEW
        elif any(keyword in filename_lower for keyword in ['top', 'upper', 'shelf_1', 'shelf_2']):
            return ImageType.TOP_DETAIL
        elif any(keyword in filename_lower for keyword in ['bottom', 'lower', 'shelf_3', 'shelf_4']):
            return ImageType.BOTTOM_DETAIL
        elif any(keyword in filename_lower for keyword in ['detail', 'section', 'close']):
            return ImageType.SECTION_DETAIL
        else:
            return ImageType.UNKNOWN


class MultiImageCoordinator:
    """Coordinate analysis across multiple images"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.images: Dict[ImageType, bytes] = {}
        self.image_metadata: Dict[ImageType, Dict] = {}
    
    def add_images(self, images: Dict[str, bytes]) -> None:
        """Add and classify images"""
        
        logger.info(
            f"Processing {len(images)} images for multi-image analysis",
            component="image_coordinator",
            agent_id=self.agent_id,
            image_count=len(images)
        )
        
        for filename, image_data in images.items():
            image_type = ImageClassifier.classify_image(filename, image_data)
            
            # Store image
            if image_type in self.images:
                # If we already have this type, prefer larger images (likely higher quality)
                if len(image_data) > len(self.images[image_type]):
                    self.images[image_type] = image_data
                    logger.debug(
                        f"Replaced {image_type.value} with larger image: {filename}",
                        component="image_coordinator",
                        agent_id=self.agent_id
                    )
            else:
                self.images[image_type] = image_data
                logger.debug(
                    f"Added {image_type.value} image: {filename}",
                    component="image_coordinator",
                    agent_id=self.agent_id
                )
            
            # Store metadata
            self.image_metadata[image_type] = {
                'filename': filename,
                'size_bytes': len(image_data),
                'type': image_type.value
            }
        
        # Log final image inventory
        available_types = list(self.images.keys())
        logger.info(
            f"Image inventory: {[t.value for t in available_types]}",
            component="image_coordinator",
            agent_id=self.agent_id,
            available_types=[t.value for t in available_types]
        )
    
    def get_primary_image(self) -> bytes:
        """Get the primary image for analysis (preferably overview)"""
        if ImageType.OVERVIEW in self.images:
            return self.images[ImageType.OVERVIEW]
        elif ImageType.UNKNOWN in self.images:
            return self.images[ImageType.UNKNOWN]
        elif self.images:
            # Return any available image
            return list(self.images.values())[0]
        else:
            raise ValueError("No images available for analysis")
    
    def get_images_for_step(self, step_id: str) -> Dict[str, bytes]:
        """Get appropriate images for a specific extraction step"""
        
        if step_id == "scaffolding" or step_id == "enhanced_scaffolding":
            # Structure analysis needs overview
            return self._get_structure_images()
        
        elif step_id == "products":
            # Product identification benefits from multiple views
            return self._get_product_images()
        
        elif step_id == "specialized_pricing":
            # Price extraction needs detail images
            return self._get_price_images()
        
        elif step_id == "facing_quantification":
            # Facing counts need clear detail views
            return self._get_facing_images()
        
        else:
            # Default: return primary image
            return {"primary": self.get_primary_image()}
    
    def _get_structure_images(self) -> Dict[str, bytes]:
        """Get images for structure analysis"""
        images = {}
        
        # Primary: overview for overall structure
        if ImageType.OVERVIEW in self.images:
            images["overview"] = self.images[ImageType.OVERVIEW]
        else:
            images["primary"] = self.get_primary_image()
        
        return images
    
    def _get_product_images(self) -> Dict[str, bytes]:
        """Get images for product identification"""
        images = {}
        
        # Start with overview
        if ImageType.OVERVIEW in self.images:
            images["overview"] = self.images[ImageType.OVERVIEW]
        
        # Add detail shots for better product recognition
        if ImageType.TOP_DETAIL in self.images:
            images["top_detail"] = self.images[ImageType.TOP_DETAIL]
        
        if ImageType.BOTTOM_DETAIL in self.images:
            images["bottom_detail"] = self.images[ImageType.BOTTOM_DETAIL]
        
        if ImageType.SECTION_DETAIL in self.images:
            images["section_detail"] = self.images[ImageType.SECTION_DETAIL]
        
        # Fallback to primary if no specific images
        if not images:
            images["primary"] = self.get_primary_image()
        
        return images
    
    def _get_price_images(self) -> Dict[str, bytes]:
        """Get images for price extraction (details needed)"""
        images = {}
        
        # Price tags are usually small, so detail images are crucial
        detail_priority = [ImageType.BOTTOM_DETAIL, ImageType.TOP_DETAIL, 
                          ImageType.SECTION_DETAIL, ImageType.OVERVIEW]
        
        for image_type in detail_priority:
            if image_type in self.images:
                images[image_type.value] = self.images[image_type]
        
        # Ensure we have at least one image
        if not images:
            images["primary"] = self.get_primary_image()
        
        return images
    
    def _get_facing_images(self) -> Dict[str, bytes]:
        """Get images for facing quantification"""
        images = {}
        
        # Facing counts benefit from clear, detailed views
        if ImageType.OVERVIEW in self.images:
            images["overview"] = self.images[ImageType.OVERVIEW]
        
        # Add all detail images for comprehensive analysis
        for image_type in [ImageType.TOP_DETAIL, ImageType.BOTTOM_DETAIL, ImageType.SECTION_DETAIL]:
            if image_type in self.images:
                images[image_type.value] = self.images[image_type]
        
        if not images:
            images["primary"] = self.get_primary_image()
        
        return images
    
    def get_comparison_images(self) -> Dict[str, bytes]:
        """Get images for AI comparison with planogram"""
        images = {}
        
        # For comparison, we want the most comprehensive view
        if ImageType.OVERVIEW in self.images:
            images["overview"] = self.images[ImageType.OVERVIEW]
        
        # Add detail images for thorough comparison
        for image_type in [ImageType.TOP_DETAIL, ImageType.BOTTOM_DETAIL]:
            if image_type in self.images:
                images[image_type.value] = self.images[image_type]
        
        if not images:
            images["primary"] = self.get_primary_image()
        
        return images
    
    def get_image_summary(self) -> Dict:
        """Get summary of available images"""
        return {
            'total_images': len(self.images),
            'available_types': [t.value for t in self.images.keys()],
            'has_overview': ImageType.OVERVIEW in self.images,
            'has_details': any(t in self.images for t in [ImageType.TOP_DETAIL, ImageType.BOTTOM_DETAIL]),
            'total_size_mb': sum(len(img) for img in self.images.values()) / (1024 * 1024),
            'metadata': self.image_metadata
        }
    
    def prepare_multi_image_prompt(self, base_prompt: str, step_id: str) -> str:
        """Enhance prompt with multi-image context"""
        
        image_count = len(self.get_images_for_step(step_id))
        
        if image_count > 1:
            multi_image_context = f"""
MULTI-IMAGE ANALYSIS CONTEXT:
You have access to {image_count} images of this retail shelf:
{self._get_image_descriptions(step_id)}

Use ALL available images to cross-reference and validate your analysis. 
Pay special attention to:
- Consistency across different views
- Details visible in close-up shots
- Overall layout from overview images

"""
            return multi_image_context + base_prompt
        else:
            return base_prompt
    
    def _get_image_descriptions(self, step_id: str) -> str:
        """Get descriptions of images available for a step"""
        images = self.get_images_for_step(step_id)
        descriptions = []
        
        for image_name in images.keys():
            if image_name == "overview":
                descriptions.append("- Overview: Full shelf layout and structure")
            elif image_name == "top_detail":
                descriptions.append("- Top Detail: Close-up of upper shelves")
            elif image_name == "bottom_detail":
                descriptions.append("- Bottom Detail: Close-up of lower shelves")
            elif image_name == "section_detail":
                descriptions.append("- Section Detail: Focused view of specific shelf section")
            else:
                descriptions.append(f"- {image_name.title()}: Detailed view")
        
        return "\n".join(descriptions) 