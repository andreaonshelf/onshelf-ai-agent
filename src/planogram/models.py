"""
Planogram Data Models
Visual representation structures for shelf planograms
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
import uuid


class ProductBlock(BaseModel):
    """Visual product representation in planogram"""
    name: str
    brand: str
    price: Optional[float]
    facings: int
    width_cm: float
    height_cm: float = 40.0  # Standard shelf height
    confidence_color: str
    position_cm: float
    shelf_number: int
    type: str = "product"
    
    # Additional metadata
    product_id: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None


class EmptySpace(BaseModel):
    """Empty shelf space representation"""
    width_cm: float
    height_cm: float = 40.0
    reason: str  # gap_detected, potential_out_of_stock, end_of_shelf
    position_cm: float
    shelf_number: int
    type: str = "empty"
    severity: str = "info"  # info, warning, critical


class PromotionalElement(BaseModel):
    """Promotional element in planogram"""
    element_type: str  # wobbler, banner, shelf_talker
    text: str
    position_cm: float
    shelf_number: int
    width_cm: float
    type: str = "promotional"


class ShelfLine(BaseModel):
    """Single shelf in planogram"""
    shelf_number: int
    y_position_cm: float
    elements: List[Union[ProductBlock, EmptySpace, PromotionalElement]]
    total_width_cm: float
    utilization_percent: float


class VisualPlanogram(BaseModel):
    """Complete planogram representation"""
    planogram_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    extraction_id: str
    shelf_count: int
    total_width_cm: float
    total_height_cm: float
    shelves: List[ShelfLine]
    
    # Metrics
    accuracy_score: float
    total_products: int
    total_facings: int
    space_utilization: float
    
    # Rendering data
    canvas_data: Optional[str] = None
    svg_data: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    store_id: Optional[str] = None
    category: Optional[str] = None
    
    # Comparison data
    original_image_dimensions: Dict[str, int]
    scale_factor: float 