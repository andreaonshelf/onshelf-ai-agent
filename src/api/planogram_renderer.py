"""
Planogram Rendering API
Generates visual planograms from extraction data
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
import io
import json
from PIL import Image, ImageDraw, ImageFont
import base64

from ..config import SystemConfig
from ..utils import logger

router = APIRouter(prefix="/api/planogram", tags=["Planogram Rendering"])


@router.get("/{image_id}/render")
async def render_planogram(
    image_id: str,
    abstraction_level: str = Query("product_view", description="brand_view, product_view, or sku_view"),
    format: str = Query("svg", description="svg, png, or json")
):
    """Render planogram for an image"""
    
    try:
        # For now, generate a mock planogram
        # In production, this would fetch real extraction data and render accordingly
        
        if format == "svg":
            svg_content = generate_svg_planogram(image_id, abstraction_level)
            return StreamingResponse(
                io.StringIO(svg_content),
                media_type="image/svg+xml",
                headers={"Cache-Control": "max-age=3600"}
            )
        elif format == "png":
            png_data = generate_png_planogram(image_id, abstraction_level)
            return StreamingResponse(
                io.BytesIO(png_data),
                media_type="image/png",
                headers={"Cache-Control": "max-age=3600"}
            )
        elif format == "json":
            json_data = generate_json_planogram(image_id, abstraction_level)
            return json_data
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use svg, png, or json")
            
    except Exception as e:
        logger.error(f"Failed to render planogram for {image_id}: {e}", component="planogram_api")
        raise HTTPException(status_code=500, detail=f"Failed to render planogram: {str(e)}")


def generate_svg_planogram(image_id: str, abstraction_level: str) -> str:
    """Generate SVG planogram"""
    
    # Mock planogram data - replace with real extraction data
    shelves = [
        {"id": "shelf_1", "y": 50, "products": [
            {"name": "Coca Cola", "x": 50, "width": 80, "color": "#FF0000"},
            {"name": "Pepsi", "x": 150, "width": 80, "color": "#0066CC"},
            {"name": "Sprite", "x": 250, "width": 80, "color": "#00AA00"},
        ]},
        {"id": "shelf_2", "y": 150, "products": [
            {"name": "Water", "x": 50, "width": 60, "color": "#0099FF"},
            {"name": "Juice", "x": 130, "width": 100, "color": "#FF9900"},
            {"name": "Energy", "x": 250, "width": 80, "color": "#9900CC"},
        ]},
        {"id": "shelf_3", "y": 250, "products": [
            {"name": "Snacks A", "x": 50, "width": 90, "color": "#FFCC00"},
            {"name": "Snacks B", "x": 160, "width": 70, "color": "#CC6600"},
            {"name": "Snacks C", "x": 250, "width": 80, "color": "#FF6600"},
        ]},
    ]
    
    svg_content = f'''
    <svg width="400" height="350" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .shelf-label {{ font-family: Arial, sans-serif; font-size: 12px; fill: #333; }}
                .product-label {{ font-family: Arial, sans-serif; font-size: 10px; fill: white; text-anchor: middle; }}
                .title {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #333; }}
            </style>
        </defs>
        
        <!-- Title -->
        <text x="200" y="25" class="title" text-anchor="middle">Planogram - {abstraction_level.replace('_', ' ').title()}</text>
        
        <!-- Shelves and Products -->
    '''
    
    for shelf in shelves:
        shelf_y = shelf["y"]
        
        # Shelf background
        svg_content += f'<rect x="30" y="{shelf_y}" width="340" height="80" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>\n'
        
        # Shelf label
        svg_content += f'<text x="10" y="{shelf_y + 45}" class="shelf-label">{shelf["id"]}</text>\n'
        
        # Products
        for product in shelf["products"]:
            product_x = product["x"]
            product_width = product["width"]
            product_height = 60
            
            # Product rectangle
            svg_content += f'<rect x="{product_x}" y="{shelf_y + 10}" width="{product_width}" height="{product_height}" fill="{product["color"]}" stroke="#333" stroke-width="1"/>\n'
            
            # Product label
            label_x = product_x + product_width // 2
            label_y = shelf_y + 45
            
            if abstraction_level == "brand_view":
                label = product["name"].split()[0]  # Just brand name
            elif abstraction_level == "sku_view":
                label = f'{product["name"]}\n500ml'  # Full SKU details
            else:
                label = product["name"]  # Product view
            
            svg_content += f'<text x="{label_x}" y="{label_y}" class="product-label">{label}</text>\n'
    
    svg_content += '</svg>'
    
    return svg_content


def generate_png_planogram(image_id: str, abstraction_level: str) -> bytes:
    """Generate PNG planogram"""
    
    # Create image
    width, height = 800, 600
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Title
    title = f"Planogram - {abstraction_level.replace('_', ' ').title()}"
    draw.text((width//2 - 100, 20), title, fill='black', font=font)
    
    # Mock shelf data
    shelves = [
        {"name": "Shelf 1", "y": 100, "products": [
            {"name": "Coca Cola", "x": 100, "width": 120, "color": (255, 0, 0)},
            {"name": "Pepsi", "x": 240, "width": 120, "color": (0, 102, 204)},
            {"name": "Sprite", "x": 380, "width": 120, "color": (0, 170, 0)},
        ]},
        {"name": "Shelf 2", "y": 250, "products": [
            {"name": "Water", "x": 100, "width": 100, "color": (0, 153, 255)},
            {"name": "Juice", "x": 220, "width": 140, "color": (255, 153, 0)},
            {"name": "Energy", "x": 380, "width": 120, "color": (153, 0, 204)},
        ]},
        {"name": "Shelf 3", "y": 400, "products": [
            {"name": "Snacks A", "x": 100, "width": 130, "color": (255, 204, 0)},
            {"name": "Snacks B", "x": 250, "width": 110, "color": (204, 102, 0)},
            {"name": "Snacks C", "x": 380, "width": 120, "color": (255, 102, 0)},
        ]},
    ]
    
    for shelf in shelves:
        shelf_y = shelf["y"]
        
        # Shelf background
        draw.rectangle([80, shelf_y, 620, shelf_y + 120], fill=(240, 240, 240), outline=(200, 200, 200))
        
        # Shelf label
        draw.text((20, shelf_y + 50), shelf["name"], fill='black', font=small_font)
        
        # Products
        for product in shelf["products"]:
            product_x = product["x"]
            product_width = product["width"]
            product_height = 80
            
            # Product rectangle
            draw.rectangle([product_x, shelf_y + 20, product_x + product_width, shelf_y + 20 + product_height], 
                         fill=product["color"], outline=(0, 0, 0))
            
            # Product label
            label_x = product_x + product_width // 2 - 30
            label_y = shelf_y + 55
            
            if abstraction_level == "brand_view":
                label = product["name"].split()[0]
            elif abstraction_level == "sku_view":
                label = f'{product["name"]}\n500ml'
            else:
                label = product["name"]
            
            draw.text((label_x, label_y), label, fill='white', font=small_font)
    
    # Convert to bytes
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    
    return img_io.getvalue()


def generate_json_planogram(image_id: str, abstraction_level: str) -> Dict[str, Any]:
    """Generate JSON planogram data"""
    
    return {
        "image_id": image_id,
        "abstraction_level": abstraction_level,
        "generated_at": "2024-01-01T12:00:00Z",
        "dimensions": {
            "width": 400,
            "height": 350,
            "unit": "pixels"
        },
        "shelves": [
            {
                "id": "shelf_1",
                "position": {"x": 30, "y": 50},
                "dimensions": {"width": 340, "height": 80},
                "products": [
                    {
                        "id": "prod_1",
                        "name": "Coca Cola" if abstraction_level != "brand_view" else "Coca Cola",
                        "brand": "Coca Cola",
                        "sku": "COKE-500ML" if abstraction_level == "sku_view" else None,
                        "position": {"x": 50, "y": 60},
                        "dimensions": {"width": 80, "height": 60},
                        "color": "#FF0000",
                        "confidence": 0.95
                    },
                    {
                        "id": "prod_2",
                        "name": "Pepsi" if abstraction_level != "brand_view" else "Pepsi",
                        "brand": "Pepsi",
                        "sku": "PEPSI-500ML" if abstraction_level == "sku_view" else None,
                        "position": {"x": 150, "y": 60},
                        "dimensions": {"width": 80, "height": 60},
                        "color": "#0066CC",
                        "confidence": 0.92
                    }
                ]
            },
            {
                "id": "shelf_2",
                "position": {"x": 30, "y": 150},
                "dimensions": {"width": 340, "height": 80},
                "products": [
                    {
                        "id": "prod_3",
                        "name": "Water" if abstraction_level != "brand_view" else "Aqua",
                        "brand": "Aqua",
                        "sku": "AQUA-500ML" if abstraction_level == "sku_view" else None,
                        "position": {"x": 50, "y": 160},
                        "dimensions": {"width": 60, "height": 60},
                        "color": "#0099FF",
                        "confidence": 0.88
                    }
                ]
            }
        ],
        "metadata": {
            "total_products": 3,
            "total_shelves": 2,
            "accuracy": 0.92,
            "processing_time": "2.3s"
        }
    } 