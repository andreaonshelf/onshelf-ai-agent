"""
Planogram Renderer
Generate visual representations using Canvas/Fabric.js and SVG
"""

import json
from typing import Dict, List, Union
from .models import VisualPlanogram, ProductBlock, EmptySpace, PromotionalElement


class PlanogramRenderer:
    """Render planograms in various formats"""
    
    def generate_canvas_javascript(self, planogram: VisualPlanogram) -> str:
        """Generate HTML5 Canvas + Fabric.js code for rendering planogram"""
        
        # Serialize shelf data for JavaScript
        shelves_json = []
        for shelf in planogram.shelves:
            shelf_data = {
                'shelf_number': shelf.shelf_number,
                'y_position': shelf.y_position_cm,
                'elements': [self._serialize_element(e) for e in shelf.elements]
            }
            shelves_json.append(shelf_data)
        
        canvas_js = f"""
// OnShelf AI Planogram Renderer
// Generated from extraction {planogram.extraction_id}

const PlanogramData = {{
    planogramId: "{planogram.planogram_id}",
    extractionId: "{planogram.extraction_id}",
    shelfCount: {planogram.shelf_count},
    totalWidthCm: {planogram.total_width_cm},
    totalHeightCm: {planogram.total_height_cm},
    accuracyScore: {planogram.accuracy_score},
    totalProducts: {planogram.total_products},
    totalFacings: {planogram.total_facings},
    spaceUtilization: {planogram.space_utilization},
    shelves: {json.dumps(shelves_json, indent=2)}
}};

class OnShelfPlanogramRenderer {{
    constructor(canvasElementId, options = {{}}) {{
        this.canvas = new fabric.Canvas(canvasElementId);
        this.options = {{
            cmToPixelRatio: 4,
            shelfHeightPx: 60,
            fontSize: 10,
            showLabels: true,
            showPrices: true,
            showFacings: true,
            showConfidence: true,
            ...options
        }};
        
        this.setupCanvas();
        this.colorScheme = {{
            shelfLine: '#666666',
            productBorder: '#333333',
            emptySpace: '#f3f4f6',
            oosBg: '#fee2e2',
            promoBg: '#fef3c7',
            textColor: '#1f2937'
        }};
    }}
    
    setupCanvas() {{
        const widthPx = PlanogramData.totalWidthCm * this.options.cmToPixelRatio;
        const heightPx = PlanogramData.totalHeightCm * this.options.cmToPixelRatio * 1.2;
        
        this.canvas.setDimensions({{
            width: widthPx,
            height: heightPx
        }});
        
        this.canvas.backgroundColor = 'white';
    }}
    
    render() {{
        this.canvas.clear();
        this.drawHeader();
        this.drawShelfStructure();
        
        PlanogramData.shelves.forEach(shelf => {{
            this.drawShelfElements(shelf);
        }});
        
        this.drawFooter();
        this.canvas.renderAll();
    }}
    
    drawHeader() {{
        const header = new fabric.Text(
            `OnShelf AI Planogram - Accuracy: ${{(PlanogramData.accuracyScore * 100).toFixed(1)}}%`,
            {{
                left: 10,
                top: 10,
                fontSize: 16,
                fontWeight: 'bold',
                fill: this.colorScheme.textColor
            }}
        );
        
        const metrics = new fabric.Text(
            `Products: ${{PlanogramData.totalProducts}} | Facings: ${{PlanogramData.totalFacings}} | Space Utilization: ${{PlanogramData.spaceUtilization.toFixed(1)}}%`,
            {{
                left: 10,
                top: 30,
                fontSize: 12,
                fill: this.colorScheme.textColor
            }}
        );
        
        this.canvas.add(header, metrics);
    }}
    
    drawShelfStructure() {{
        const startY = 60;
        
        for (let i = 0; i < PlanogramData.shelfCount; i++) {{
            const y = startY + (i * this.options.shelfHeightPx);
            
            // Shelf line
            const shelfLine = new fabric.Line(
                [0, y + this.options.shelfHeightPx, this.canvas.width, y + this.options.shelfHeightPx],
                {{
                    stroke: this.colorScheme.shelfLine,
                    strokeWidth: 2
                }}
            );
            
            // Shelf number
            const shelfLabel = new fabric.Text(`Shelf ${{i + 1}}`, {{
                left: 5,
                top: y + 5,
                fontSize: 10,
                fill: this.colorScheme.textColor
            }});
            
            this.canvas.add(shelfLine, shelfLabel);
        }}
    }}
    
    drawShelfElements(shelf) {{
        const startY = 60 + ((shelf.shelf_number - 1) * this.options.shelfHeightPx);
        
        shelf.elements.forEach(element => {{
            const x = element.position_cm * this.options.cmToPixelRatio;
            const width = element.width_cm * this.options.cmToPixelRatio;
            
            if (element.type === 'product') {{
                this.drawProduct(element, x, startY, width);
            }} else if (element.type === 'empty') {{
                this.drawEmptySpace(element, x, startY, width);
            }} else if (element.type === 'promotional') {{
                this.drawPromoElement(element, x, startY, width);
            }}
        }});
    }}
    
    drawProduct(product, x, y, width) {{
        // Product rectangle with confidence color
        const rect = new fabric.Rect({{
            left: x,
            top: y + 5,
            width: width - 2,
            height: this.options.shelfHeightPx - 15,
            fill: product.confidence_color,
            stroke: this.colorScheme.productBorder,
            strokeWidth: 1,
            rx: 3,
            ry: 3
        }});
        
        this.canvas.add(rect);
        
        // Product text
        if (this.options.showLabels) {{
            const truncatedName = this.truncateText(product.name, width - 10);
            const nameText = new fabric.Text(truncatedName, {{
                left: x + 3,
                top: y + 8,
                fontSize: this.options.fontSize,
                fontWeight: 'bold',
                fill: 'white'
            }});
            
            this.canvas.add(nameText);
        }}
        
        // Price
        if (this.options.showPrices && product.price) {{
            const priceText = new fabric.Text(`£${{product.price.toFixed(2)}}`, {{
                left: x + 3,
                top: y + 20,
                fontSize: this.options.fontSize - 1,
                fill: 'white'
            }});
            
            this.canvas.add(priceText);
        }}
        
        // Facings
        if (this.options.showFacings) {{
            const facingText = new fabric.Text(`${{product.facings}} facing${{product.facings > 1 ? 's' : ''}}`, {{
                left: x + 3,
                top: y + 32,
                fontSize: this.options.fontSize - 2,
                fill: 'white'
            }});
            
            this.canvas.add(facingText);
        }}
    }}
    
    drawEmptySpace(space, x, y, width) {{
        const bgColor = space.reason === 'potential_out_of_stock' 
            ? this.colorScheme.oosBg 
            : this.colorScheme.emptySpace;
        
        const rect = new fabric.Rect({{
            left: x,
            top: y + 5,
            width: width - 2,
            height: this.options.shelfHeightPx - 15,
            fill: bgColor,
            stroke: '#d1d5db',
            strokeWidth: 1,
            strokeDashArray: [5, 5]
        }});
        
        this.canvas.add(rect);
        
        // Label
        const label = space.reason === 'potential_out_of_stock' ? 'OUT OF STOCK?' : 'EMPTY';
        const labelText = new fabric.Text(label, {{
            left: x + width/2,
            top: y + this.options.shelfHeightPx/2,
            fontSize: this.options.fontSize - 1,
            fill: '#6b7280',
            originX: 'center',
            originY: 'center',
            fontStyle: 'italic'
        }});
        
        this.canvas.add(labelText);
    }}
    
    drawPromoElement(promo, x, y, width) {{
        const rect = new fabric.Rect({{
            left: x,
            top: y + 5,
            width: width - 2,
            height: this.options.shelfHeightPx - 15,
            fill: this.colorScheme.promoBg,
            stroke: '#f59e0b',
            strokeWidth: 2
        }});
        
        this.canvas.add(rect);
        
        const icon = new fabric.Text('🏷️', {{
            left: x + 3,
            top: y + 10,
            fontSize: 16
        }});
        
        const text = new fabric.Text(promo.text, {{
            left: x + 25,
            top: y + 15,
            fontSize: this.options.fontSize - 1,
            fill: '#92400e',
            fontWeight: 'bold'
        }});
        
        this.canvas.add(rect, icon, text);
    }}
    
    drawFooter() {{
        const footer = new fabric.Text(
            `Generated by OnShelf AI Agent | ID: ${{PlanogramData.planogramId.slice(0, 8)}}`,
            {{
                left: 10,
                top: this.canvas.height - 20,
                fontSize: 10,
                fill: '#9ca3af'
            }}
        );
        
        this.canvas.add(footer);
    }}
    
    truncateText(text, maxWidth) {{
        const maxChars = Math.floor(maxWidth / (this.options.fontSize * 0.6));
        return text.length > maxChars ? text.substring(0, maxChars - 3) + '...' : text;
    }}
    
    toDataURL(format = 'jpeg', quality = 0.9) {{
        return this.canvas.toDataURL({{
            format: format,
            quality: quality,
            multiplier: 2  // Higher resolution
        }});
    }}
    
    toSVG() {{
        return this.canvas.toSVG();
    }}
    
    enableInteractivity() {{
        this.canvas.on('mouse:over', (e) => {{
            if (e.target && e.target.product) {{
                this.showProductTooltip(e.target.product, e.e);
            }}
        }});
    }}
    
    showProductTooltip(product, event) {{
        // Implement interactive tooltip
        const tooltip = new fabric.Rect({{
            left: event.layerX,
            top: event.layerY - 50,
            width: 200,
            height: 50,
            fill: 'black',
            opacity: 0.8,
            rx: 5,
            ry: 5
        }});
        
        const text = new fabric.Text(
            `${{product.brand}} ${{product.name}}\\nConfidence: ${{(product.confidence * 100).toFixed(0)}}%`,
            {{
                left: event.layerX + 5,
                top: event.layerY - 45,
                fontSize: 10,
                fill: 'white'
            }}
        );
        
        this.tooltip = new fabric.Group([tooltip, text]);
        this.canvas.add(this.tooltip);
        this.canvas.renderAll();
        
        setTimeout(() => {{
            this.canvas.remove(this.tooltip);
            this.canvas.renderAll();
        }}, 2000);
    }}
}}

// Auto-initialize if canvas element exists
document.addEventListener('DOMContentLoaded', () => {{
    const canvasElement = document.getElementById('planogram-canvas');
    if (canvasElement) {{
        window.planogramRenderer = new OnShelfPlanogramRenderer('planogram-canvas');
        window.planogramRenderer.render();
        window.planogramRenderer.enableInteractivity();
    }}
}});
"""
        
        return canvas_js
    
    def generate_svg(self, planogram: VisualPlanogram) -> str:
        """Generate SVG representation of planogram"""
        
        width = planogram.total_width_cm * 4  # 4px per cm
        height = planogram.total_height_cm * 4 * 1.2
        
        svg_elements = []
        
        # SVG header
        svg_elements.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">')
        svg_elements.append('<rect width="100%" height="100%" fill="white"/>')
        
        # Title
        svg_elements.append(f'<text x="10" y="20" font-size="16" font-weight="bold">OnShelf AI Planogram - Accuracy: {planogram.accuracy_score*100:.1f}%</text>')
        
        # Shelves
        start_y = 60
        for shelf in planogram.shelves:
            y = start_y + ((shelf.shelf_number - 1) * 60)
            
            # Shelf line
            svg_elements.append(f'<line x1="0" y1="{y+60}" x2="{width}" y2="{y+60}" stroke="#666" stroke-width="2"/>')
            
            # Shelf elements
            for element in shelf.elements:
                x = element.position_cm * 4
                elem_width = element.width_cm * 4
                
                if element.type == "product":
                    svg_elements.append(self._svg_product(element, x, y, elem_width))
                elif element.type == "empty":
                    svg_elements.append(self._svg_empty_space(element, x, y, elem_width))
        
        svg_elements.append('</svg>')
        
        return '\n'.join(svg_elements)
    
    def _serialize_element(self, element: Union[ProductBlock, EmptySpace, PromotionalElement]) -> Dict:
        """Serialize element for JavaScript"""
        return element.dict()
    
    def _svg_product(self, product: ProductBlock, x: float, y: float, width: float) -> str:
        """Generate SVG for product"""
        return f'''
        <g>
            <rect x="{x}" y="{y+5}" width="{width-2}" height="50" 
                  fill="{product.confidence_color}" stroke="#333" rx="3"/>
            <text x="{x+3}" y="{y+20}" font-size="10" fill="white" font-weight="bold">
                {product.name[:20]}
            </text>
            <text x="{x+3}" y="{y+35}" font-size="9" fill="white">
                £{product.price:.2f} | {product.facings} facings
            </text>
        </g>'''
    
    def _svg_empty_space(self, space: EmptySpace, x: float, y: float, width: float) -> str:
        """Generate SVG for empty space"""
        fill = "#fee2e2" if space.reason == "potential_out_of_stock" else "#f3f4f6"
        label = "OUT OF STOCK?" if space.reason == "potential_out_of_stock" else "EMPTY"
        
        return f'''
        <g>
            <rect x="{x}" y="{y+5}" width="{width-2}" height="50" 
                  fill="{fill}" stroke="#d1d5db" stroke-dasharray="5,5"/>
            <text x="{x+width/2}" y="{y+30}" font-size="10" fill="#6b7280" 
                  text-anchor="middle" font-style="italic">
                {label}
            </text>
        </g>''' 