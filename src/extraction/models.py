"""
Data models for extraction engine
Structured output schemas for AI models using Instructor
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import uuid


class ConfidenceLevel(str, Enum):
    """Confidence levels for extraction quality"""
    VERY_HIGH = "very_high"   # >95%
    HIGH = "high"            # 85-95%
    MEDIUM = "medium"        # 70-85%
    LOW = "low"             # <70%


class ValidationFlag(str, Enum):
    """Flags for extraction validation issues"""
    PRICE_SUSPICIOUS = "price_suspicious"
    PRODUCT_NAME_UNCLEAR = "product_name_unclear"
    POSITION_UNCERTAIN = "position_uncertain"
    OCCLUSION_DETECTED = "occlusion_detected"
    DUPLICATE_SUSPECTED = "duplicate_suspected"
    MODEL_DISAGREEMENT = "model_disagreement"


class AIModelType(str, Enum):
    """Available AI models for extraction"""
    CLAUDE_3_SONNET = "claude-3-5-sonnet-20241022"
    GPT4O_LATEST = "gpt-4o-2024-11-20"
    GEMINI_2_FLASH = "gemini-2.0-flash-exp"


class SectionCoordinates(BaseModel):
    """Shelf section coordinates"""
    horizontal: str = Field(description="Shelf number from bottom up (1=bottom)")
    vertical: str = Field(description="Left/Center/Right section")


class Position(BaseModel):
    """Product position on shelf"""
    l_position_on_section: int = Field(description="Position from left to right")
    r_position_on_section: int = Field(description="Position from right to left") 
    l_empty: bool = Field(description="Empty space on left")
    r_empty: bool = Field(description="Empty space on right")


class Quantity(BaseModel):
    """Product quantity information"""
    stack: int = Field(description="Units stacked vertically")
    columns: int = Field(description="Units adjacent horizontally")
    total_facings: int = Field(description="Total visible product facings")


class PixelCoordinates(BaseModel):
    """Pixel coordinates in image"""
    x: int = Field(description="Left edge pixel coordinate")
    y: int = Field(description="Top edge pixel coordinate")
    width: int = Field(description="Bounding box width")
    height: int = Field(description="Bounding box height")


class ProductExtraction(BaseModel):
    """Single product with complete data"""
    
    # Spatial positioning
    section: SectionCoordinates
    position: Position
    
    # Product details
    brand: str
    name: str
    price: Optional[float] = Field(None, description="Price in GBP")
    
    # Quantity information (critical for retail)
    quantity: Quantity
    
    # Pixel location (for consumer surveys)
    pixel_coordinates: PixelCoordinates
    
    # Quality metrics
    extraction_confidence: float = Field(description="0.0-1.0")
    confidence_category: ConfidenceLevel
    validation_flags: List[ValidationFlag] = Field(default_factory=list)
    extracted_by_model: AIModelType
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('confidence_category', pre=True, always=True)
    def set_confidence_category(cls, v, values):
        """Auto-set confidence category based on confidence score"""
        if 'extraction_confidence' in values:
            conf = values['extraction_confidence']
            if conf >= 0.95:
                return ConfidenceLevel.VERY_HIGH
            elif conf >= 0.85:
                return ConfidenceLevel.HIGH
            elif conf >= 0.70:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW
        return v


class SecurityDevice(BaseModel):
    """Security device detection"""
    device_type: str = Field(description="grid, magnetic_tag, plastic_case, bottle_security")
    coverage_area: Dict[str, int] = Field(description="Pixel coordinates")
    affected_products: List[str] = Field(description="Product names affected")


class PromotionalMaterial(BaseModel):
    """Promotional material detection"""
    material_type: str = Field(description="shelf_wobbler, price_tag, banner, hanging_sign")
    promotional_text: str = Field(description="Visible text")
    position: Dict[str, int] = Field(description="Pixel coordinates")
    associated_products: List[str] = Field(description="Related products")


class NonProductElements(BaseModel):
    """Non-product elements on shelf"""
    security_devices: List[SecurityDevice] = Field(default_factory=list)
    promotional_materials: List[PromotionalMaterial] = Field(default_factory=list)
    empty_spaces: List[Dict[str, int]] = Field(default_factory=list)


class ShelfStructure(BaseModel):
    """Physical shelf layout"""
    picture_height: int
    picture_width: int
    number_of_shelves: int
    estimated_width_meters: float
    estimated_height_meters: float
    shelf_coordinates: List[Dict[str, int]] = Field(description="Y coordinates per shelf")
    structure_confidence: ConfidenceLevel


class CompleteShelfExtraction(BaseModel):
    """Final extraction output - this is what gets converted to planogram"""
    
    extraction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    upload_id: str
    media_file_ids: List[str]
    
    # Core extraction data
    shelf_structure: ShelfStructure
    products: List[ProductExtraction]
    total_products_detected: int
    non_product_elements: NonProductElements
    
    # Quality assessment
    overall_confidence: ConfidenceLevel
    requires_human_review: bool
    accuracy_score: float = Field(description="0.0-1.0")
    
    # Processing metadata
    extraction_duration_seconds: float
    models_used: List[AIModelType]
    api_cost_estimate: float
    validation_summary: Dict[str, int]
    
    @validator('total_products_detected', pre=True, always=True)
    def set_total_products(cls, v, values):
        """Auto-calculate total products"""
        if 'products' in values:
            return len(values['products'])
        return v


class ExtractionStep(BaseModel):
    """Individual extraction step that builds on previous outputs"""
    step_id: str
    model: AIModelType
    prompt_template: str
    input_dependencies: List[str] = Field(default_factory=list, description="Previous step outputs to use")
    output_schema: str = Field(description="Expected output type")
    confidence_threshold: float = 0.8 