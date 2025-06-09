#!/usr/bin/env python3
"""
Fix to ensure planogram generation happens during extraction
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def generate_planogram_svg(products: List[Dict[str, Any]]) -> str:
    """Generate a simple SVG planogram from extracted products"""
    
    if not products:
        return '<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f5f5f5"/><text x="400" y="200" text-anchor="middle" font-size="20">No products extracted</text></svg>'
    
    svg_parts = [
        '<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">',
        '<rect width="100%" height="100%" fill="#f5f5f5"/>',
        '<rect x="0" y="0" width="100%" height="60" fill="white"/>',
        '<text x="20" y="35" font-size="24" font-weight="bold" fill="#1f2937">Planogram View</text>',
        f'<text x="20" y="50" font-size="14" fill="#6b7280">{len(products)} products extracted</text>'
    ]
    
    # Group products by shelf
    shelves = {}
    max_shelf = 1
    for p in products:
        shelf = p.get('shelf', 1)
        if shelf > max_shelf:
            max_shelf = shelf
        if shelf not in shelves:
            shelves[shelf] = []
        shelves[shelf].append(p)
    
    # Calculate dimensions
    shelf_height = (600 - 80) / max_shelf  # Leave space for header
    
    # Draw shelves from bottom to top
    for shelf_num in range(1, max_shelf + 1):
        shelf_y = 80 + (max_shelf - shelf_num) * shelf_height
        
        # Draw shelf background
        svg_parts.append(
            f'<rect x="0" y="{shelf_y}" width="800" height="{shelf_height}" '
            f'fill="white" stroke="#e5e7eb" stroke-width="1"/>'
        )
        
        # Draw shelf line
        line_y = shelf_y + shelf_height - 5
        svg_parts.append(
            f'<line x1="20" y1="{line_y}" x2="780" y2="{line_y}" '
            f'stroke="#374151" stroke-width="3"/>'
        )
        
        # Shelf label
        svg_parts.append(
            f'<text x="10" y="{shelf_y + shelf_height/2}" font-size="12" '
            f'fill="#6b7280" text-anchor="middle" transform="rotate(-90 10 {shelf_y + shelf_height/2})">'
            f'Shelf {shelf_num}</text>'
        )
        
        # Draw products on this shelf
        if shelf_num in shelves:
            shelf_products = sorted(shelves[shelf_num], key=lambda x: x.get('position', 0))
            
            x_pos = 40
            for product in shelf_products:
                width = 80 * product.get('facings', 1)
                height = min(90, shelf_height - 20)
                
                # Product box
                svg_parts.append(
                    f'<rect x="{x_pos}" y="{shelf_y + 10}" width="{width}" height="{height}" '
                    f'fill="white" stroke="#3b82f6" stroke-width="2" rx="4"/>'
                )
                
                # Product text
                brand = str(product.get('brand', 'Unknown'))[:15]
                name = str(product.get('name', 'Product'))[:15]
                price = product.get('price')
                
                text_y = shelf_y + 30
                svg_parts.append(f'<text x="{x_pos + 5}" y="{text_y}" font-size="11" font-weight="bold" fill="#1f2937">{brand}</text>')
                svg_parts.append(f'<text x="{x_pos + 5}" y="{text_y + 15}" font-size="10" fill="#475569">{name}</text>')
                
                if price is not None:
                    svg_parts.append(f'<text x="{x_pos + 5}" y="{text_y + 40}" font-size="12" fill="#059669" font-weight="bold">${price}</text>')
                
                # Confidence indicator
                confidence = product.get('confidence', 0.8)
                color = '#10b981' if confidence > 0.8 else '#f59e0b' if confidence > 0.6 else '#ef4444'
                svg_parts.append(
                    f'<circle cx="{x_pos + width - 10}" cy="{shelf_y + 20}" r="5" fill="{color}"/>'
                )
                
                x_pos += width + 10
                
                if x_pos > 750:  # Prevent overflow
                    break
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def update_extraction_systems():
    """Update extraction systems to include planogram generation"""
    
    # Get Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(url, key)
    
    print("Checking queue items that need planogram generation...")
    
    # Get completed items without planograms
    response = supabase.table('ai_extraction_queue').select('*').eq('status', 'completed').execute()
    
    if response.data:
        items_updated = 0
        for item in response.data:
            # Check if it already has a real planogram
            planogram_result = item.get('planogram_result')
            if planogram_result and isinstance(planogram_result, dict):
                svg = planogram_result.get('svg', '')
                if 'Planogram Placeholder' not in svg and len(svg) > 500:
                    continue  # Already has a real planogram
            
            # Extract products from extraction result
            extraction_result = item.get('extraction_result')
            if not extraction_result:
                continue
                
            products = []
            if isinstance(extraction_result, dict):
                if 'stages' in extraction_result:
                    stages = extraction_result['stages']
                    if 'products' in stages and isinstance(stages['products'], dict):
                        products = stages['products'].get('data', [])
                    elif 'product_v1' in stages and isinstance(stages['product_v1'], dict):
                        products = stages['product_v1'].get('data', [])
                elif 'products' in extraction_result:
                    products = extraction_result.get('products', [])
            
            if products:
                # Generate planogram
                svg = generate_planogram_svg(products)
                
                # Update queue item
                update_result = supabase.table('ai_extraction_queue').update({
                    'planogram_result': {
                        'svg': svg,
                        'layout': {
                            'products': len(products),
                            'shelves': len(set(p.get('shelf', 1) for p in products))
                        }
                    }
                }).eq('id', item['id']).execute()
                
                if update_result.data:
                    items_updated += 1
                    print(f"✅ Updated queue item {item['id']} with planogram ({len(products)} products)")
        
        print(f"\nTotal items updated: {items_updated}")
    else:
        print("No completed queue items found")


if __name__ == "__main__":
    update_extraction_systems()