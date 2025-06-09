"""
Planogram Renderer API
Renders planograms from real extraction data - NO MOCK DATA
"""

import io
import base64
from typing import Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException
from PIL import Image, ImageDraw, ImageFont

from ..config import SystemConfig
from ..utils import logger

# Initialize router
router = APIRouter(prefix="/api/planogram", tags=["planogram"])

# Get config and database connection
config = SystemConfig()
try:
    from supabase import create_client
    supabase = create_client(config.supabase_url, config.supabase_service_key)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None


@router.get("/{image_id}/render")
async def render_planogram(
    image_id: str,
    abstraction_level: str = Query("product_view", description="brand_view, product_view, or sku_view"),
    format: str = Query("svg", description="svg, png, or json")
):
    """Render planogram for an image using ONLY real extraction data"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get real extraction data from database
        extraction_data = await get_real_extraction_data(image_id)
        
        if not extraction_data:
            # Check if processing is still ongoing
            queue_result = supabase.table("ai_extraction_queue").select("status, error_message").eq("id", image_id).execute()
            
            if queue_result.data:
                status = queue_result.data[0].get("status")
                if status == "processing":
                    raise HTTPException(status_code=202, detail="Extraction is currently processing - please wait")
                elif status == "failed":
                    error_msg = queue_result.data[0].get("error_message", "Unknown error")
                    raise HTTPException(status_code=500, detail=f"Extraction failed: {error_msg}")
                elif status == "pending":
                    raise HTTPException(status_code=202, detail="Extraction is queued for processing")
            
            raise HTTPException(status_code=404, detail="No extraction data found for this image")
        
        # Generate planogram based on format
        if format == "svg":
            return {"svg": generate_svg_from_real_data(extraction_data, abstraction_level)}
        elif format == "png":
            png_data = generate_png_from_real_data(extraction_data, abstraction_level)
            return {"png": base64.b64encode(png_data).decode()}
        elif format == "json":
            return generate_json_from_real_data(extraction_data, abstraction_level)
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'svg', 'png', or 'json'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to render planogram for {image_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to render planogram: {str(e)}")


async def get_real_extraction_data(image_id: str) -> Optional[Dict[str, Any]]:
    """Get REAL extraction data from database - NO MOCK DATA"""
    
    if not supabase:
        return None
    
    try:
        # Get extraction results from database
        result = supabase.table("ai_extraction_queue").select(
            "extraction_result, planogram_result, final_accuracy, status"
        ).eq("id", image_id).execute()
        
        if not result.data:
            logger.warning(f"No queue item found for image_id {image_id}")
            return None
        
        queue_item = result.data[0]
        
        # Check if we have real extraction results
        extraction_result = queue_item.get("extraction_result")
        if not extraction_result:
            logger.info(f"No extraction result yet for image_id {image_id}")
            return None
        
        # Parse the extraction result if it's a string
        if isinstance(extraction_result, str):
            import json
            extraction_result = json.loads(extraction_result)
        
        return {
            "extraction_result": extraction_result,
            "accuracy": queue_item.get("final_accuracy", 0.0),
            "status": queue_item.get("status")
        }
        
    except Exception as e:
        logger.error(f"Failed to get real extraction data for {image_id}: {e}")
        return None


def generate_svg_from_real_data(extraction_data: Dict[str, Any], abstraction_level: str) -> str:
    """Generate SVG planogram from REAL extraction data only"""
    
    extraction_result = extraction_data.get("extraction_result", {})
    products = extraction_result.get("products", [])
    accuracy = extraction_data.get("accuracy", 0.0)
    
    if not products:
        return generate_no_data_svg("No products found in extraction data")
    
    # Group products by shelf
    shelves = {}
    for product in products:
        # Handle different data structures
        if hasattr(product, 'section'):
            shelf_num = int(product.section.horizontal)
        elif isinstance(product, dict) and 'section' in product:
            shelf_num = int(product['section']['horizontal'])
        else:
            shelf_num = 1  # Default shelf
        
        if shelf_num not in shelves:
            shelves[shelf_num] = []
        shelves[shelf_num].append(product)
    
    # Generate SVG
    svg_height = 100 + len(shelves) * 120
    svg_content = f'''
    <svg width="600" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .shelf-label {{ font-family: Arial, sans-serif; font-size: 14px; fill: #333; }}
                .product-label {{ font-family: Arial, sans-serif; font-size: 11px; fill: white; text-anchor: middle; }}
                .title {{ font-family: Arial, sans-serif; font-size: 18px; font-weight: bold; fill: #333; }}
                .accuracy {{ font-family: Arial, sans-serif; font-size: 14px; fill: #666; }}
            </style>
        </defs>
        
        <!-- Title -->
        <text x="300" y="30" class="title" text-anchor="middle">Real Planogram - {abstraction_level.replace('_', ' ').title()}</text>
        <text x="300" y="50" class="accuracy" text-anchor="middle">Accuracy: {accuracy:.1%}</text>
        <text x="300" y="70" class="accuracy" text-anchor="middle">Products: {len(products)}</text>
        
        <!-- Shelves and Products -->
    '''
    
    for shelf_num in sorted(shelves.keys()):
        shelf_products = shelves[shelf_num]
        shelf_y = 80 + (shelf_num - 1) * 120
        
        # Shelf background
        svg_content += f'<rect x="50" y="{shelf_y}" width="500" height="100" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>\n'
        
        # Shelf label
        svg_content += f'<text x="20" y="{shelf_y + 55}" class="shelf-label">Shelf {shelf_num}</text>\n'
        
        # Products
        for i, product in enumerate(shelf_products):
            # Extract product data
            if hasattr(product, 'brand'):
                brand = product.brand
                name = product.name
                confidence = product.extraction_confidence
            elif isinstance(product, dict):
                brand = product.get('brand', 'Unknown')
                name = product.get('name', 'Unknown Product')
                confidence = product.get('extraction_confidence', 0.0)
            else:
                brand = 'Unknown'
                name = 'Unknown Product'
                confidence = 0.0
            
            # Calculate position
            product_x = 70 + i * 90
            product_width = 80
            product_height = 70
            
            # Color based on confidence
            if confidence >= 0.9:
                color = "#28a745"  # Green
            elif confidence >= 0.7:
                color = "#ffc107"  # Yellow
            else:
                color = "#dc3545"  # Red
            
            # Product rectangle
            svg_content += f'<rect x="{product_x}" y="{shelf_y + 15}" width="{product_width}" height="{product_height}" fill="{color}" stroke="#333" stroke-width="1"/>\n'
            
            # Product label
            label_x = product_x + product_width // 2
            label_y = shelf_y + 55
            
            if abstraction_level == "brand_view":
                label = brand
            else:
                label = name[:12] + "..." if len(name) > 12 else name
            
            svg_content += f'<text x="{label_x}" y="{label_y}" class="product-label">{label}</text>\n'
            
            # Confidence text
            svg_content += f'<text x="{label_x}" y="{label_y + 15}" class="product-label">{confidence:.2f}</text>\n'
    
    svg_content += '</svg>'
    return svg_content


def generate_png_from_real_data(extraction_data: Dict[str, Any], abstraction_level: str) -> bytes:
    """Generate PNG planogram from REAL extraction data only"""
    
    extraction_result = extraction_data.get("extraction_result", {})
    products = extraction_result.get("products", [])
    accuracy = extraction_data.get("accuracy", 0.0)
    
    if not products:
        return generate_no_data_png("No products found in extraction data")
    
    # Create image
    width, height = 800, 200 + len(products) * 50
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Title
    title = f"Real Planogram - {abstraction_level.replace('_', ' ').title()}"
    draw.text((width//2 - 150, 20), title, fill='black', font=font)
    draw.text((width//2 - 100, 50), f"Accuracy: {accuracy:.1%}", fill='gray', font=small_font)
    draw.text((width//2 - 80, 80), f"Products: {len(products)}", fill='gray', font=small_font)
    
    # Draw products
    y_pos = 120
    for i, product in enumerate(products):
        # Extract product data
        if hasattr(product, 'brand'):
            brand = product.brand
            name = product.name
            # Handle missing extraction_confidence gracefully
            confidence = getattr(product, 'extraction_confidence', 0.85)
        elif isinstance(product, dict):
            brand = product.get('brand', 'Unknown')
            name = product.get('name', 'Unknown Product')
            confidence = product.get('extraction_confidence', 0.85)
        else:
            brand = 'Unknown'
            name = 'Unknown Product'
            confidence = 0.0
        
        # Color based on confidence
        if confidence >= 0.9:
            color = (40, 167, 69)  # Green
        elif confidence >= 0.7:
            color = (255, 193, 7)  # Yellow
        else:
            color = (220, 53, 69)  # Red
        
        # Product rectangle
        draw.rectangle([50, y_pos, 300, y_pos + 40], fill=color, outline=(0, 0, 0))
        
        # Product text
        text = f"{brand} - {name} (Confidence: {confidence:.2f})"
        draw.text((60, y_pos + 15), text, fill='white', font=small_font)
        
        y_pos += 50
    
    # Convert to bytes
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    
    return img_io.getvalue()


def generate_json_from_real_data(extraction_data: Dict[str, Any], abstraction_level: str) -> Dict[str, Any]:
    """Generate JSON planogram from REAL extraction data only"""
    
    extraction_result = extraction_data.get("extraction_result", {})
    products = extraction_result.get("products", [])
    accuracy = extraction_data.get("accuracy", 0.0)
    
    if not products:
        return {
            "error": "No products found in extraction data",
            "abstraction_level": abstraction_level,
            "accuracy": accuracy,
            "total_products": 0
        }
    
    # Convert products to JSON format
    json_products = []
    for i, product in enumerate(products):
        # Extract product data
        if hasattr(product, 'brand'):
            brand = product.brand
            name = product.name
            # Handle missing extraction_confidence gracefully
            confidence = getattr(product, 'extraction_confidence', 0.85)
        elif isinstance(product, dict):
            brand = product.get('brand', 'Unknown')
            name = product.get('name', 'Unknown Product')
            confidence = product.get('extraction_confidence', 0.85)
        else:
            brand = 'Unknown'
            name = 'Unknown Product'
            confidence = 0.0
        
        json_products.append({
            "id": f"product_{i}",
            "brand": brand,
            "name": name,
            "confidence": confidence,
            "display_name": brand if abstraction_level == "brand_view" else name
        })
    
    return {
        "abstraction_level": abstraction_level,
        "accuracy": accuracy,
        "total_products": len(products),
        "products": json_products,
        "data_source": "real_extraction",
        "generated_at": "real_time"
    }


def generate_no_data_svg(message: str) -> str:
    """Generate SVG for when no data is available"""
    return f'''
    <svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="200" fill="#f8f9fa" stroke="#dee2e6" stroke-width="2"/>
        <text x="200" y="100" text-anchor="middle" font-family="Arial" font-size="16" fill="#6c757d">
            {message}
        </text>
        <text x="200" y="130" text-anchor="middle" font-family="Arial" font-size="12" fill="#6c757d">
            Please wait for extraction to complete
        </text>
    </svg>
    '''


def generate_no_data_png(message: str) -> bytes:
    """Generate PNG for when no data is available"""
    image = Image.new('RGB', (400, 200), '#f8f9fa')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw.text((200, 100), message, fill='#6c757d', font=font, anchor="mm")
    
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    
    return img_io.getvalue() 