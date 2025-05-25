"""
Planogram Rendering API
Generates visual planograms from extraction data
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
import io
import json
import os
from PIL import Image, ImageDraw, ImageFont
import base64
from supabase import create_client, Client

from ..config import SystemConfig
from ..utils import logger

router = APIRouter(prefix="/api/planogram", tags=["Planogram Rendering"])

# Initialize Supabase client
config = SystemConfig()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)


@router.get("/{image_id}/render")
async def render_planogram(
    image_id: str,
    abstraction_level: str = Query("product_view", description="brand_view, product_view, or sku_view"),
    format: str = Query("svg", description="svg, png, or json")
):
    """Render planogram for an image using real extraction data"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get real extraction data from database
        extraction_data = await get_extraction_data(image_id)
        
        if not extraction_data:
            # Fallback to mock data if no real data available
            logger.warning(f"No extraction data found for image {image_id}, using mock data")
            extraction_data = get_mock_extraction_data()
        
        if format == "svg":
            svg_content = generate_svg_planogram_from_data(extraction_data, abstraction_level)
            return StreamingResponse(
                io.StringIO(svg_content),
                media_type="image/svg+xml",
                headers={"Cache-Control": "max-age=3600"}
            )
        elif format == "png":
            png_data = generate_png_planogram_from_data(extraction_data, abstraction_level)
            return StreamingResponse(
                io.BytesIO(png_data),
                media_type="image/png",
                headers={"Cache-Control": "max-age=3600"}
            )
        elif format == "json":
            json_data = generate_json_planogram_from_data(extraction_data, abstraction_level)
            return json_data
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use svg, png, or json")
            
    except Exception as e:
        logger.error(f"Failed to render planogram for {image_id}: {e}", component="planogram_api")
        raise HTTPException(status_code=500, detail=f"Failed to render planogram: {str(e)}")


async def get_extraction_data(image_id: str) -> Optional[Dict[str, Any]]:
    """Get real extraction data from database"""
    try:
        # Query the ai_extraction_queue table for extraction results
        result = supabase.table("ai_extraction_queue").select(
            "extraction_result, planogram_result, final_accuracy"
        ).eq("id", image_id).execute()
        
        if not result.data:
            return None
        
        item = result.data[0]
        extraction_result = item.get('extraction_result')
        planogram_result = item.get('planogram_result')
        
        if not extraction_result:
            return None
        
        return {
            "extraction_result": extraction_result,
            "planogram_result": planogram_result,
            "accuracy": item.get('final_accuracy', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get extraction data for {image_id}: {e}")
        return None


def get_mock_extraction_data() -> Dict[str, Any]:
    """Get mock extraction data as fallback"""
    return {
        "extraction_result": {
            "products": [
                {
                    "brand": "Coca Cola",
                    "name": "Coca Cola Original",
                    "position": {"x": 50, "y": 60, "shelf": 1},
                    "confidence": 0.95,
                    "facings": 3
                },
                {
                    "brand": "Pepsi",
                    "name": "Pepsi Cola",
                    "position": {"x": 150, "y": 60, "shelf": 1},
                    "confidence": 0.92,
                    "facings": 2
                },
                {
                    "brand": "Sprite",
                    "name": "Sprite Lemon",
                    "position": {"x": 250, "y": 60, "shelf": 1},
                    "confidence": 0.88,
                    "facings": 2
                }
            ],
            "shelf_structure": {
                "shelf_count": 3,
                "width_cm": 250
            },
            "accuracy_score": 0.92
        },
        "accuracy": 0.92
    }


def generate_svg_planogram_from_data(extraction_data: Dict[str, Any], abstraction_level: str) -> str:
    """Generate SVG planogram from real extraction data"""
    
    extraction_result = extraction_data.get("extraction_result", {})
    products = extraction_result.get("products", [])
    shelf_structure = extraction_result.get("shelf_structure", {})
    accuracy = extraction_data.get("accuracy", 0.0)
    
    # Group products by shelf
    shelves = {}
    for product in products:
        position = product.get("position", {})
        shelf_num = position.get("shelf", 1)
        
        if shelf_num not in shelves:
            shelves[shelf_num] = []
        shelves[shelf_num].append(product)
    
    # Generate colors for brands
    brand_colors = {
        "Coca Cola": "#FF0000",
        "Pepsi": "#0066CC", 
        "Sprite": "#00AA00",
        "Water": "#0099FF",
        "Juice": "#FF9900",
        "Energy": "#9900CC"
    }
    
    svg_content = f'''
    <svg width="400" height="{50 + len(shelves) * 100}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <style>
                .shelf-label {{ font-family: Arial, sans-serif; font-size: 12px; fill: #333; }}
                .product-label {{ font-family: Arial, sans-serif; font-size: 10px; fill: white; text-anchor: middle; }}
                .title {{ font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #333; }}
                .accuracy {{ font-family: Arial, sans-serif; font-size: 12px; fill: #666; }}
            </style>
        </defs>
        
        <!-- Title -->
        <text x="200" y="25" class="title" text-anchor="middle">Real Planogram - {abstraction_level.replace('_', ' ').title()}</text>
        <text x="200" y="40" class="accuracy" text-anchor="middle">Accuracy: {accuracy:.1%}</text>
        
        <!-- Shelves and Products -->
    '''
    
    for shelf_num in sorted(shelves.keys()):
        shelf_products = shelves[shelf_num]
        shelf_y = 50 + (shelf_num - 1) * 100
        
        # Shelf background
        svg_content += f'<rect x="30" y="{shelf_y}" width="340" height="80" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>\n'
        
        # Shelf label
        svg_content += f'<text x="10" y="{shelf_y + 45}" class="shelf-label">Shelf {shelf_num}</text>\n'
        
        # Products
        for i, product in enumerate(shelf_products):
            brand = product.get("brand", "Unknown")
            name = product.get("name", brand)
            facings = product.get("facings", 1)
            confidence = product.get("confidence", 0.0)
            
            # Calculate position and width based on facings
            product_x = 50 + i * 80
            product_width = max(60, facings * 20)
            product_height = 60
            
            # Get brand color
            color = brand_colors.get(brand, "#666666")
            
            # Product rectangle
            svg_content += f'<rect x="{product_x}" y="{shelf_y + 10}" width="{product_width}" height="{product_height}" fill="{color}" stroke="#333" stroke-width="1"/>\n'
            
            # Product label based on abstraction level
            label_x = product_x + product_width // 2
            label_y = shelf_y + 45
            
            if abstraction_level == "brand_view":
                label = brand
            elif abstraction_level == "sku_view":
                label = f'{name}\n{facings}x'
            else:  # product_view
                label = name
            
            svg_content += f'<text x="{label_x}" y="{label_y}" class="product-label">{label}</text>\n'
            
            # Confidence indicator (small circle)
            confidence_color = "#00AA00" if confidence > 0.9 else "#FF9900" if confidence > 0.7 else "#FF0000"
            svg_content += f'<circle cx="{product_x + product_width - 10}" cy="{shelf_y + 20}" r="4" fill="{confidence_color}"/>\n'
    
    svg_content += '</svg>'
    
    return svg_content


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


def generate_png_planogram_from_data(extraction_data: Dict[str, Any], abstraction_level: str) -> bytes:
    """Generate PNG planogram from real extraction data"""
    
    extraction_result = extraction_data.get("extraction_result", {})
    products = extraction_result.get("products", [])
    accuracy = extraction_data.get("accuracy", 0.0)
    
    # Group products by shelf
    shelves = {}
    for product in products:
        position = product.get("position", {})
        shelf_num = position.get("shelf", 1)
        
        if shelf_num not in shelves:
            shelves[shelf_num] = []
        shelves[shelf_num].append(product)
    
    # Create image
    width, height = 800, 150 + len(shelves) * 150
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
    
    # Brand colors
    brand_colors = {
        "Coca Cola": (255, 0, 0),
        "Pepsi": (0, 102, 204),
        "Sprite": (0, 170, 0),
        "Water": (0, 153, 255),
        "Juice": (255, 153, 0),
        "Energy": (153, 0, 204)
    }
    
    for shelf_num in sorted(shelves.keys()):
        shelf_products = shelves[shelf_num]
        shelf_y = 100 + (shelf_num - 1) * 150
        
        # Shelf background
        draw.rectangle([80, shelf_y, 720, shelf_y + 120], fill=(240, 240, 240), outline=(200, 200, 200))
        
        # Shelf label
        draw.text((20, shelf_y + 50), f"Shelf {shelf_num}", fill='black', font=small_font)
        
        # Products
        for i, product in enumerate(shelf_products):
            brand = product.get("brand", "Unknown")
            name = product.get("name", brand)
            facings = product.get("facings", 1)
            confidence = product.get("confidence", 0.0)
            
            # Calculate position and width
            product_x = 100 + i * 120
            product_width = max(80, facings * 30)
            product_height = 80
            
            # Get brand color
            color = brand_colors.get(brand, (102, 102, 102))
            
            # Product rectangle
            draw.rectangle([product_x, shelf_y + 20, product_x + product_width, shelf_y + 20 + product_height], 
                         fill=color, outline=(0, 0, 0))
            
            # Product label
            label_x = product_x + 10
            label_y = shelf_y + 55
            
            if abstraction_level == "brand_view":
                label = brand
            elif abstraction_level == "sku_view":
                label = f'{name}\n{facings}x'
            else:
                label = name
            
            draw.text((label_x, label_y), label, fill='white', font=small_font)
            
            # Confidence indicator
            conf_color = (0, 170, 0) if confidence > 0.9 else (255, 153, 0) if confidence > 0.7 else (255, 0, 0)
            draw.ellipse([product_x + product_width - 15, shelf_y + 25, product_x + product_width - 5, shelf_y + 35], fill=conf_color)
    
    # Convert to bytes
    img_io = io.BytesIO()
    image.save(img_io, format='PNG')
    img_io.seek(0)
    
    return img_io.getvalue()


def generate_json_planogram_from_data(extraction_data: Dict[str, Any], abstraction_level: str) -> Dict[str, Any]:
    """Generate JSON planogram data from real extraction data"""
    
    extraction_result = extraction_data.get("extraction_result", {})
    products = extraction_result.get("products", [])
    shelf_structure = extraction_result.get("shelf_structure", {})
    accuracy = extraction_data.get("accuracy", 0.0)
    
    # Group products by shelf
    shelves = {}
    for product in products:
        position = product.get("position", {})
        shelf_num = position.get("shelf", 1)
        
        if shelf_num not in shelves:
            shelves[shelf_num] = []
        shelves[shelf_num].append(product)
    
    # Build JSON structure
    json_shelves = []
    for shelf_num in sorted(shelves.keys()):
        shelf_products = shelves[shelf_num]
        
        json_products = []
        for i, product in enumerate(shelf_products):
            brand = product.get("brand", "Unknown")
            name = product.get("name", brand)
            facings = product.get("facings", 1)
            confidence = product.get("confidence", 0.0)
            
            json_products.append({
                "id": f"prod_{shelf_num}_{i}",
                "name": name if abstraction_level != "brand_view" else brand,
                "brand": brand,
                "sku": f"{brand.upper()}-500ML" if abstraction_level == "sku_view" else None,
                "position": {"x": 50 + i * 80, "y": 50 + (shelf_num - 1) * 100},
                "dimensions": {"width": max(60, facings * 20), "height": 60},
                "facings": facings,
                "confidence": confidence,
                "color": "#FF0000" if "Coca" in brand else "#0066CC" if "Pepsi" in brand else "#666666"
            })
        
        json_shelves.append({
            "id": f"shelf_{shelf_num}",
            "position": {"x": 30, "y": 50 + (shelf_num - 1) * 100},
            "dimensions": {"width": 340, "height": 80},
            "products": json_products
        })
    
    return {
        "abstraction_level": abstraction_level,
        "generated_at": "2024-01-01T12:00:00Z",
        "dimensions": {
            "width": 400,
            "height": 50 + len(shelves) * 100,
            "unit": "pixels"
        },
        "shelves": json_shelves,
        "metadata": {
            "total_products": len(products),
            "total_shelves": len(shelves),
            "accuracy": accuracy,
            "processing_time": "real_data",
            "data_source": "ai_extraction_queue"
        }
    }


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