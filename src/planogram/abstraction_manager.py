"""
Planogram Abstraction Manager
Manages three levels of planogram abstraction: Brand, Product, and SKU views
"""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel

from ..models.extraction_models import ProductExtraction
from ..utils import logger


class BrandBlock(BaseModel):
    """Brand-level block for planogram"""
    brand_name: str
    total_facings: int
    shelf_distribution: Dict[int, Dict]  # shelf_number -> {positions, facings}
    confidence_color: str
    block_width_cm: float
    average_confidence: float


class ProductBlock(BaseModel):
    """Product-level block for planogram"""
    product_name: str
    brand: str
    shelf_number: int
    position_on_shelf: int
    facing_count: int
    price: Optional[float]
    confidence_color: str
    block_width_cm: float
    confidence: float


class SKUBlock(BaseModel):
    """SKU-level block for planogram"""
    sku_name: str
    brand: str
    package_size: str
    shelf_number: int
    position_on_shelf: int
    facing_index: int  # Which facing of this product (1, 2, 3, etc.)
    price: Optional[float]
    confidence_color: str
    block_width_cm: float = 8  # Standard facing width
    confidence: float


class BrandViewPlanogram(BaseModel):
    """Brand-level planogram view"""
    brand_blocks: List[BrandBlock]
    total_brands: int
    abstraction_level: str = "brand_view"


class ProductViewPlanogram(BaseModel):
    """Product-level planogram view"""
    product_blocks: List[ProductBlock]
    total_products: int
    abstraction_level: str = "product_view"


class SKUViewPlanogram(BaseModel):
    """SKU-level planogram view"""
    sku_blocks: List[SKUBlock]
    total_skus: int
    abstraction_level: str = "sku_view"


class PlanogramAbstractionManager:
    """Manages three levels of planogram abstraction"""
    
    def __init__(self):
        self.standard_facing_width_cm = 8
        
        logger.info(
            "Planogram Abstraction Manager initialized",
            component="abstraction_manager"
        )
    
    def generate_brand_view(self, products: List[ProductExtraction]) -> BrandViewPlanogram:
        """Level 1: Brand blocks (e.g., all Coca-Cola products as one block)"""
        
        logger.info(
            f"Generating brand view for {len(products)} products",
            component="abstraction_manager",
            product_count=len(products)
        )
        
        brand_groups = {}
        
        for product in products:
            brand = product.brand
            
            if brand not in brand_groups:
                brand_groups[brand] = {
                    "total_facings": 0,
                    "shelves": {},
                    "confidence": [],
                    "products": []
                }
            
            # Accumulate brand data
            brand_groups[brand]["total_facings"] += product.quantity.total_facings
            brand_groups[brand]["confidence"].append(product.extraction_confidence)
            brand_groups[brand]["products"].append(product)
            
            # Track shelf distribution
            shelf = product.section.horizontal
            if shelf not in brand_groups[brand]["shelves"]:
                brand_groups[brand]["shelves"][shelf] = {
                    "positions": [],
                    "total_facings": 0
                }
            
            brand_groups[brand]["shelves"][shelf]["positions"].append(
                product.position.l_position_on_section
            )
            brand_groups[brand]["shelves"][shelf]["total_facings"] += product.quantity.total_facings
        
        # Generate visual blocks
        brand_blocks = []
        for brand, data in brand_groups.items():
            avg_confidence = sum(data["confidence"]) / len(data["confidence"])
            
            brand_block = BrandBlock(
                brand_name=brand,
                total_facings=data["total_facings"],
                shelf_distribution=data["shelves"],
                confidence_color=self._get_confidence_color(avg_confidence),
                block_width_cm=data["total_facings"] * self.standard_facing_width_cm,
                average_confidence=avg_confidence
            )
            brand_blocks.append(brand_block)
        
        # Sort by total facings (largest brands first)
        brand_blocks.sort(key=lambda x: x.total_facings, reverse=True)
        
        planogram = BrandViewPlanogram(
            brand_blocks=brand_blocks,
            total_brands=len(brand_blocks)
        )
        
        logger.info(
            f"Brand view generated: {len(brand_blocks)} brands",
            component="abstraction_manager",
            brand_count=len(brand_blocks)
        )
        
        return planogram
    
    def generate_product_view(self, products: List[ProductExtraction]) -> ProductViewPlanogram:
        """Level 2: Product-level detail (e.g., Coca-Cola Classic, Coca-Cola Zero)"""
        
        logger.info(
            f"Generating product view for {len(products)} products",
            component="abstraction_manager",
            product_count=len(products)
        )
        
        product_blocks = []
        
        for product in products:
            product_block = ProductBlock(
                product_name=f"{product.brand} {product.name}",
                brand=product.brand,
                shelf_number=product.section.horizontal,
                position_on_shelf=product.position.l_position_on_section,
                facing_count=product.quantity.total_facings,
                price=product.price,
                confidence_color=self._get_confidence_color(product.extraction_confidence),
                block_width_cm=product.quantity.total_facings * self.standard_facing_width_cm,
                confidence=product.extraction_confidence
            )
            product_blocks.append(product_block)
        
        # Sort by shelf then position
        product_blocks.sort(key=lambda x: (x.shelf_number, x.position_on_shelf))
        
        planogram = ProductViewPlanogram(
            product_blocks=product_blocks,
            total_products=len(product_blocks)
        )
        
        return planogram
    
    def generate_sku_view(self, products: List[ProductExtraction]) -> SKUViewPlanogram:
        """Level 3: SKU-level detail (e.g., Coca-Cola Classic 330ml, 500ml, 1.5L)"""
        
        logger.info(
            f"Generating SKU view for {len(products)} products",
            component="abstraction_manager",
            product_count=len(products)
        )
        
        sku_blocks = []
        
        for product in products:
            # Extract package size from product name
            package_size = self._extract_package_size(product.name)
            
            # For each facing, create individual SKU block
            for facing_index in range(product.quantity.total_facings):
                sku_block = SKUBlock(
                    sku_name=f"{product.brand} {product.name}",
                    brand=product.brand,
                    package_size=package_size,
                    shelf_number=product.section.horizontal,
                    position_on_shelf=product.position.l_position_on_section,
                    facing_index=facing_index + 1,
                    price=product.price,
                    confidence_color=self._get_confidence_color(product.extraction_confidence),
                    confidence=product.extraction_confidence
                )
                sku_blocks.append(sku_block)
        
        # Sort by shelf, position, then facing
        sku_blocks.sort(key=lambda x: (x.shelf_number, x.position_on_shelf, x.facing_index))
        
        planogram = SKUViewPlanogram(
            sku_blocks=sku_blocks,
            total_skus=len(sku_blocks)
        )
        
        logger.info(
            f"SKU view generated: {len(sku_blocks)} individual facings",
            component="abstraction_manager",
            sku_count=len(sku_blocks)
        )
        
        return planogram
    
    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence level"""
        if confidence >= 0.95:
            return '#22c55e'  # Green - very high
        elif confidence >= 0.85:
            return '#3b82f6'  # Blue - high
        elif confidence >= 0.70:
            return '#f59e0b'  # Orange - medium
        else:
            return '#ef4444'  # Red - low
    
    def _extract_package_size(self, product_name: str) -> str:
        """Extract package size from product name"""
        import re
        
        # Common size patterns
        patterns = [
            r'(\d+(?:\.\d+)?)\s*ml',
            r'(\d+(?:\.\d+)?)\s*l',
            r'(\d+(?:\.\d+)?)\s*g',
            r'(\d+(?:\.\d+)?)\s*kg',
            r'(\d+(?:\.\d+)?)\s*oz',
            r'(\d+)\s*pack',
            r'(\d+)\s*x\s*(\d+(?:\.\d+)?)\s*ml'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_name.lower())
            if match:
                return match.group(0)
        
        return "standard"
    
    def convert_between_levels(self, 
                             current_view: Union[BrandViewPlanogram, ProductViewPlanogram, SKUViewPlanogram],
                             target_level: str,
                             products: List[ProductExtraction]) -> Union[BrandViewPlanogram, ProductViewPlanogram, SKUViewPlanogram]:
        """Convert between different abstraction levels"""
        
        logger.info(
            f"Converting from {current_view.abstraction_level} to {target_level}",
            component="abstraction_manager",
            from_level=current_view.abstraction_level,
            to_level=target_level
        )
        
        if target_level == "brand_view":
            return self.generate_brand_view(products)
        elif target_level == "product_view":
            return self.generate_product_view(products)
        elif target_level == "sku_view":
            return self.generate_sku_view(products)
        else:
            raise ValueError(f"Unknown abstraction level: {target_level}") 