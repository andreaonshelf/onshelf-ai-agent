"""
OnShelf AI - Queue Review Dashboard
Main FastAPI application with progressive debugging interface for reviewing extraction results
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from src.config import SystemConfig

# Initialize FastAPI app
app = FastAPI(
    title="OnShelf AI - Queue Review Dashboard",
    description="Review and analysis tool for extraction results with progressive disclosure",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
from src.api.progressive_debugger import router as progressive_router
app.include_router(progressive_router)

# Include strategic interface
from src.api.strategic_interface import router as strategic_router
app.include_router(strategic_router)

# Include planogram editor API
from src.api.planogram_editor import router as planogram_editor_router
app.include_router(planogram_editor_router)

# Include real-time debugging interface
from src.api.debug_interface import router as debug_router
app.include_router(debug_router)

# Include planogram rendering
from src.api.planogram_renderer import router as planogram_router
app.include_router(planogram_router)

# Include queue management API
from src.api.queue_management import router as queue_router
app.include_router(queue_router)

# Include iteration tracking API for debugging
from src.api.iteration_tracking import router as iteration_router, iteration_storage
app.include_router(iteration_router)

# Initialize mock iteration data on startup
@app.on_event("startup")
async def initialize_mock_data():
    """Initialize mock iteration data for testing the dashboard"""
    try:
        from datetime import datetime
        
        # Create REAL extraction data structure that matches actual AI agent output
        # This mirrors exactly what ProductExtraction model returns
        real_extraction_products = [
            # Shelf 1 products - exactly as AI agents extract them
            {
                "section": {"horizontal": "1", "vertical": "Left"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Coca-Cola", "name": "Coke Zero Sugar 330ml", "price": 1.29,
                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                "shelf_level": 1, "position_on_shelf": 1,
                "any_text": "Zero Sugar 330ml", "color": "black and red", "pack_size": None, "volume": "330ml",
                "is_on_promo": False, "facings_total": 3,
                "extraction_confidence": 0.94, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "1", "vertical": "Left"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "Coca-Cola", "name": "Sprite Zero 330ml", "price": 1.29,
                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                "shelf_level": 1, "position_on_shelf": 2,
                "any_text": "Sprite Zero 330ml", "color": "green and white", "pack_size": None, "volume": "330ml",
                "is_on_promo": False, "facings_total": 2,
                "extraction_confidence": 0.89, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "1", "vertical": "Center"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "PepsiCo", "name": "Pepsi Max Cherry 330ml", "price": 1.19,
                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                "shelf_level": 1, "position_on_shelf": 4,
                "any_text": "Max Cherry 330ml", "color": "dark blue and red", "pack_size": None, "volume": "330ml",
                "is_on_promo": True, "facings_total": 3,
                "extraction_confidence": 0.92, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "gpt-4o-2024-11-20"
            },
            {
                "section": {"horizontal": "1", "vertical": "Center"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "PepsiCo", "name": "7UP Free 330ml", "price": 1.19,
                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                "shelf_level": 1, "position_on_shelf": 5,
                "any_text": "7UP Free", "color": "green and white", "pack_size": None, "volume": "330ml",
                "is_on_promo": False, "facings_total": 2,
                "extraction_confidence": 0.86, "confidence_category": "high",
                "validation_flags": ["product_name_unclear"], "extracted_by_model": "gpt-4o-2024-11-20"
            },
            # Gap at position 6 - no product detected
            {
                "section": {"horizontal": "1", "vertical": "Right"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Red Bull", "name": "Red Bull Energy Drink 250ml", "price": 1.89,
                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                "shelf_level": 1, "position_on_shelf": 7,
                "any_text": "Energy Drink 250ml", "color": "blue and silver", "pack_size": None, "volume": "250ml",
                "is_on_promo": False, "facings_total": 4,
                "extraction_confidence": 0.96, "confidence_category": "very_high",
                "validation_flags": [], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "1", "vertical": "Right"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "Monster Beverage", "name": "Monster Energy Original 500ml", "price": 2.15,
                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                "shelf_level": 1, "position_on_shelf": 8,
                "any_text": "Monster Energy 500ml", "color": "green and black", "pack_size": None, "volume": "500ml",
                "is_on_promo": False, "facings_total": 2,
                "extraction_confidence": 0.91, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "gemini-2.0-flash-exp"
            },
            
            # Shelf 2 products
            {
                "section": {"horizontal": "2", "vertical": "Left"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Evian", "name": "Natural Mineral Water 500ml", "price": 0.89,
                "quantity": {"stack": 3, "columns": 2, "total_facings": 6},
                "shelf_level": 2, "position_on_shelf": 1,
                "any_text": "Natural Mineral Water 500ml", "color": "clear plastic", "pack_size": None, "volume": "500ml",
                "is_on_promo": False, "facings_total": 6,
                "extraction_confidence": 0.97, "confidence_category": "very_high",
                "validation_flags": [], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "2", "vertical": "Left"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "Coca-Cola", "name": "Smartwater 600ml", "price": 1.49,
                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                "shelf_level": 2, "position_on_shelf": 2,
                "any_text": "smartwater 600ml", "color": "clear with white label", "pack_size": None, "volume": "600ml",
                "is_on_promo": False, "facings_total": 4,
                "extraction_confidence": 0.88, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "gpt-4o-2024-11-20"
            },
            {
                "section": {"horizontal": "2", "vertical": "Center"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Innocent", "name": "Orange Juice Smooth 330ml", "price": 2.29,
                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                "shelf_level": 2, "position_on_shelf": 3,
                "any_text": "Orange Juice Smooth 330ml", "color": "orange carton", "pack_size": None, "volume": "330ml",
                "is_on_promo": True, "facings_total": 3,
                "extraction_confidence": 0.93, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "2", "vertical": "Center"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "Innocent", "name": "Apple Juice 330ml", "price": 2.29,
                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                "shelf_level": 2, "position_on_shelf": 4,
                "any_text": "Apple Juice", "color": "green carton", "pack_size": None, "volume": "330ml",
                "is_on_promo": False, "facings_total": 2,
                "extraction_confidence": 0.85, "confidence_category": "high",
                "validation_flags": ["price_suspicious"], "extracted_by_model": "gpt-4o-2024-11-20"
            },
            {
                "section": {"horizontal": "2", "vertical": "Right"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Lipton", "name": "Ice Tea Lemon 500ml", "price": 1.59,
                "quantity": {"stack": 2, "columns": 3, "total_facings": 6},
                "shelf_level": 2, "position_on_shelf": 6,
                "any_text": "Ice Tea Lemon 500ml", "color": "yellow plastic bottle", "pack_size": None, "volume": "500ml",
                "is_on_promo": False, "facings_total": 6,
                "extraction_confidence": 0.94, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "gemini-2.0-flash-exp"
            },
            
            # Shelf 3 products
            {
                "section": {"horizontal": "3", "vertical": "Left"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Starbucks", "name": "Frappuccino Vanilla 250ml", "price": 2.49,
                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                "shelf_level": 3, "position_on_shelf": 1,
                "any_text": "Frappuccino Vanilla 250ml", "color": "beige bottle", "pack_size": None, "volume": "250ml",
                "is_on_promo": False, "facings_total": 3,
                "extraction_confidence": 0.96, "confidence_category": "very_high",
                "validation_flags": [], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "3", "vertical": "Left"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "Starbucks", "name": "Frappuccino Mocha 250ml", "price": 2.49,
                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                "shelf_level": 3, "position_on_shelf": 2,
                "any_text": "Frappuccino Mocha", "color": "brown bottle", "pack_size": None, "volume": "250ml",
                "is_on_promo": False, "facings_total": 2,
                "extraction_confidence": 0.89, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "gpt-4o-2024-11-20"
            },
            {
                "section": {"horizontal": "3", "vertical": "Center"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Powerade", "name": "ION4 Blue 500ml", "price": 1.79,
                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                "shelf_level": 3, "position_on_shelf": 3,
                "any_text": "ION4 Blue 500ml", "color": "blue plastic bottle", "pack_size": None, "volume": "500ml",
                "is_on_promo": False, "facings_total": 4,
                "extraction_confidence": 0.82, "confidence_category": "high",
                "validation_flags": ["occlusion_detected"], "extracted_by_model": "claude-3-5-sonnet-20241022"
            },
            {
                "section": {"horizontal": "3", "vertical": "Center"},
                "position": {"l_position_on_section": 2, "r_position_on_section": 2, "l_empty": False, "r_empty": False},
                "brand": "Gatorade", "name": "Orange Sports Drink 500ml", "price": 1.79,
                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                "shelf_level": 3, "position_on_shelf": 4,
                "any_text": "Gatorade Orange", "color": "orange plastic bottle", "pack_size": None, "volume": "500ml",
                "is_on_promo": False, "facings_total": 4,
                "extraction_confidence": 0.78, "confidence_category": "medium",
                "validation_flags": ["product_name_unclear", "position_uncertain"], "extracted_by_model": "gemini-2.0-flash-exp"
            },
            {
                "section": {"horizontal": "3", "vertical": "Right"},
                "position": {"l_position_on_section": 1, "r_position_on_section": 1, "l_empty": False, "r_empty": False},
                "brand": "Rockstar", "name": "Energy Drink Original 500ml", "price": 1.99,
                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                "shelf_level": 3, "position_on_shelf": 5,
                "any_text": "Rockstar Energy", "color": "black and gold can", "pack_size": None, "volume": "500ml",
                "is_on_promo": False, "facings_total": 2,
                "extraction_confidence": 0.87, "confidence_category": "high",
                "validation_flags": [], "extracted_by_model": "gpt-4o-2024-11-20"
            }
        ]

        mock_data = {
            'upload_id': 'demo_12345', 
            'iterations': [
                {
                    "iteration": 1,
                    "accuracy": 0.87,
                    "timestamp": datetime.now().isoformat(),
                    "extraction_data": {
                        "total_products": len(real_extraction_products),
                        "products": real_extraction_products,
                        "model_used": "claude-3-5-sonnet-20241022",
                        "confidence": 0.87
                    },
                    "planogram_svg": None,  # Will be generated by SVG renderer
                    "structure": {"shelves": 3, "width": 2.5},
                    "failure_areas": 3
                },
                {
                    "iteration": 2,
                    "accuracy": 0.92,
                    "timestamp": datetime.now().isoformat(),
                    "extraction_data": {
                        "total_products": 3,
                        "products": [
                            {
                                "brand": "Coca-Cola",
                                "name": "Coke Zero 330ml",
                                "price": 1.29,
                                "position": {"shelf_number": 1, "position_on_shelf": 1, "facing_count": 3, "section": "Left", "confidence": 0.95},
                                "extraction_confidence": 0.95,
                                "confidence_category": "very_high"
                            },
                            {
                                "brand": "Pepsi",
                                "name": "Pepsi Max 330ml",
                                "price": 1.19,
                                "position": {"shelf_number": 1, "position_on_shelf": 2, "facing_count": 2, "section": "Center", "confidence": 0.88},
                                "extraction_confidence": 0.88,
                                "confidence_category": "high"
                            },
                            {
                                "brand": "Red Bull",
                                "name": "Energy Drink 250ml",
                                "price": 1.89,
                                "position": {"shelf_number": 2, "position_on_shelf": 1, "facing_count": 4, "section": "Left", "confidence": 0.92},
                                "extraction_confidence": 0.92,
                                "confidence_category": "high"
                            }
                        ],
                        "model_used": "claude-3-sonnet",
                        "confidence": 0.92
                    },
                    "planogram_svg": '<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f5f5f5"/><text x="20" y="35" font-size="24" font-weight="bold" fill="#1f2937">Demo Planogram - Iteration 2 (Improved)</text><rect x="50" y="100" width="120" height="80" fill="white" stroke="#10b981" stroke-width="2" rx="4"/><text x="60" y="130" font-size="12" fill="#1f2937">Coke Zero</text><text x="60" y="150" font-size="10" fill="#6b7280">£1.29 • 3 facings</text><circle cx="160" cy="110" r="4" fill="#10b981"/><rect x="180" y="100" width="100" height="80" fill="white" stroke="#3b82f6" stroke-width="2" rx="4"/><text x="190" y="130" font-size="12" fill="#1f2937">Pepsi Max</text><text x="190" y="150" font-size="10" fill="#6b7280">£1.19 • 2 facings</text><rect x="50" y="200" width="140" height="80" fill="white" stroke="#3b82f6" stroke-width="2" rx="4"/><text x="60" y="230" font-size="12" fill="#1f2937">Red Bull Energy</text><text x="60" y="250" font-size="10" fill="#6b7280">£1.89 • 4 facings</text></svg>',
                    "structure": {"shelves": 3, "width": 2.5},
                    "failure_areas": 1
                },
                {
                    "iteration": 3,
                    "accuracy": 0.97,
                    "timestamp": datetime.now().isoformat(),
                    "extraction_data": {
                        "total_products": 4,
                        "products": [
                            {
                                "brand": "Coca-Cola",
                                "name": "Coke Zero 330ml",
                                "price": 1.29,
                                "position": {"shelf_number": 1, "position_on_shelf": 1, "facing_count": 3, "section": "Left", "confidence": 0.98},
                                "extraction_confidence": 0.98,
                                "confidence_category": "very_high"
                            },
                            {
                                "brand": "Pepsi",
                                "name": "Pepsi Max 330ml",
                                "price": 1.19,
                                "position": {"shelf_number": 1, "position_on_shelf": 2, "facing_count": 2, "section": "Center", "confidence": 0.96},
                                "extraction_confidence": 0.96,
                                "confidence_category": "very_high"
                            },
                            {
                                "brand": "Red Bull",
                                "name": "Energy Drink 250ml",
                                "price": 1.89,
                                "position": {"shelf_number": 2, "position_on_shelf": 1, "facing_count": 4, "section": "Left", "confidence": 0.97},
                                "extraction_confidence": 0.97,
                                "confidence_category": "very_high"
                            },
                            {
                                "brand": "Monster",
                                "name": "Monster Energy 500ml",
                                "price": 2.15,
                                "position": {"shelf_number": 2, "position_on_shelf": 2, "facing_count": 2, "section": "Center", "confidence": 0.94},
                                "extraction_confidence": 0.94,
                                "confidence_category": "very_high"
                            }
                        ],
                        "model_used": "claude-3-sonnet",
                        "confidence": 0.96
                    },
                    "planogram_svg": '<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f5f5f5"/><text x="20" y="35" font-size="24" font-weight="bold" fill="#1f2937">Demo Planogram - Iteration 3 (High Accuracy)</text><rect x="50" y="100" width="120" height="80" fill="white" stroke="#10b981" stroke-width="3" rx="4"/><text x="60" y="125" font-size="11" font-weight="bold" fill="#1f2937">Coke Zero 330ml</text><text x="60" y="140" font-size="9" fill="#6b7280">Coca-Cola</text><text x="60" y="155" font-size="10" fill="#2563eb">£1.29</text><circle cx="160" cy="110" r="4" fill="#10b981"/><rect x="180" y="100" width="100" height="80" fill="white" stroke="#10b981" stroke-width="3" rx="4"/><text x="190" y="125" font-size="11" font-weight="bold" fill="#1f2937">Pepsi Max 330ml</text><text x="190" y="140" font-size="9" fill="#6b7280">Pepsi</text><text x="190" y="155" font-size="10" fill="#2563eb">£1.19</text><circle cx="270" cy="110" r="4" fill="#10b981"/><rect x="50" y="200" width="140" height="80" fill="white" stroke="#10b981" stroke-width="3" rx="4"/><text x="60" y="225" font-size="11" font-weight="bold" fill="#1f2937">Energy Drink 250ml</text><text x="60" y="240" font-size="9" fill="#6b7280">Red Bull</text><text x="60" y="255" font-size="10" fill="#2563eb">£1.89</text><circle cx="180" cy="210" r="4" fill="#10b981"/><rect x="200" y="200" width="120" height="80" fill="white" stroke="#10b981" stroke-width="3" rx="4"/><text x="210" y="225" font-size="11" font-weight="bold" fill="#1f2937">Monster Energy</text><text x="210" y="240" font-size="9" fill="#6b7280">Monster</text><text x="210" y="255" font-size="10" fill="#2563eb">£2.15</text><circle cx="310" cy="210" r="4" fill="#10b981"/></svg>',
                    "structure": {"shelves": 3, "width": 2.5},
                    "failure_areas": 0
                }
            ]
        }
        
        # Store mock data for demo queue item
        iteration_storage[12345] = mock_data
        print(f"✅ Initialized mock iteration data with {len(mock_data['iterations'])} iterations")
        
    except Exception as e:
        print(f"❌ Error initializing mock data: {e}")
        # Create minimal fallback
        iteration_storage[12345] = {
            'upload_id': 'demo_12345',
            'iterations': [{
                "iteration": 1,
                "accuracy": 0.8,
                "timestamp": "2024-01-01T12:00:00",
                "extraction_data": {"total_products": 1, "products": [], "model_used": "claude-3-sonnet", "confidence": 0.8},
                "planogram_svg": '<svg width="800" height="600"><text x="20" y="30">Simple Demo SVG</text></svg>',
                "structure": {"shelves": 3, "width": 2.5},
                "failure_areas": 1
            }]
        }

# Add endpoint to manually initialize mock data
@app.get("/api/init-mock-data")
async def init_mock_data():
    """Manually initialize mock data"""
    await initialize_mock_data()
    return {"message": "Mock data initialized", "items": list(iteration_storage.keys())}

# Serve static files (for the UI)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard interface with progressive disclosure"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OnShelf AI - Extraction Dashboard</title>
        
        <!-- React and Dependencies -->
        <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
        
        <!-- Planogram Styles -->
        <link rel="stylesheet" href="/static/css/planogram.css">
        
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8fafc;
                color: #1e293b;
                line-height: 1.6;
            }
            
            /* Layout Structure */
            .app-container {
                display: flex;
                height: 100vh;
                overflow: hidden;
                position: relative;
            }
            
            /* Left Sidebar - Image Selection */
            .left-sidebar {
                width: 400px;
                background: white;
                border-right: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                transition: all 0.3s ease;
                z-index: 100;
                position: relative;
                flex-shrink: 0;
            }
            
            .left-sidebar.collapsed {
                transform: translateX(-380px);
                width: 20px;
            }
            
            .sidebar-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                background: #f8fafc;
            }
            
            .sidebar-toggle {
                position: fixed;
                left: 0px;
                top: 20px;
                width: 30px;
                height: 40px;
                background: #3b82f6;
                color: white;
                border: none;
                cursor: pointer;
                border-radius: 0 4px 4px 0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                z-index: 1000;
                transition: left 0.3s ease;
            }
            
            .left-sidebar:not(.collapsed) .sidebar-toggle {
                left: 380px;
            }
            
            .filters-section {
                padding: 15px 20px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .filter-group {
                margin-bottom: 15px;
            }
            
            .filter-group label {
                display: block;
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                margin-bottom: 5px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .filter-group select,
            .filter-group input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            
            .search-box {
                position: relative;
            }
            
            .search-box input {
                padding-left: 35px;
            }
            
            .search-box::before {
                content: "🔍";
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 14px;
            }
            
            .view-toggle {
                display: flex;
                gap: 5px;
                margin-top: 10px;
            }
            
            .view-toggle button {
                flex: 1;
                padding: 6px 12px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
            }
            
            .view-toggle button.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            .images-container {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
            }
            
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 10px;
            }
            
            .image-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .image-item {
                border: 2px solid transparent;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.2s ease;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .image-item:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .image-item.selected {
                border-color: #10b981;
                background: #f0fdf4;
            }
            
            .image-item.grid-view {
                aspect-ratio: 1;
            }
            
            .image-item.list-view {
                display: flex;
                padding: 8px;
                align-items: center;
                gap: 10px;
            }
            
            .image-thumbnail {
                width: 100%;
                height: 100%;
                object-fit: cover;
                background: #f1f5f9;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }
            
            .image-item.list-view .image-thumbnail {
                width: 60px;
                height: 60px;
                border-radius: 4px;
                flex-shrink: 0;
            }
            
            .image-info {
                padding: 8px;
                font-size: 12px;
            }
            
            .image-item.list-view .image-info {
                padding: 0;
                flex: 1;
            }
            
            .image-title {
                font-weight: 600;
                margin-bottom: 2px;
                color: #1e293b;
            }
            
            .image-meta {
                color: #64748b;
                font-size: 11px;
            }
            
            .status-badge {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 4px;
            }
            
            .status-pending { background: #fef3c7; color: #92400e; }
            .status-processing { background: #dbeafe; color: #1e40af; }
            .status-completed { background: #d1fae5; color: #065f46; }
            .status-failed { background: #fee2e2; color: #991b1b; }
            .status-review { background: #fde68a; color: #92400e; }
            
            .pagination {
                padding: 15px 20px;
                border-top: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: #64748b;
            }
            
            .pagination-controls {
                display: flex;
                gap: 5px;
            }
            
            .pagination-controls button {
                padding: 4px 8px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .pagination-controls button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .pagination-controls button.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            /* Main Content Area */
            .main-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                width: 100%;
            }
            
            /* Header */
            .header {
                background: white;
                border-bottom: 1px solid #e2e8f0;
                padding: 20px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header h1 {
                font-size: 24px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .mode-selector {
                display: flex;
                gap: 10px;
            }
            
            .mode-btn {
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .mode-btn:hover {
                background: #f8fafc;
                border-color: #3b82f6;
            }
            
            .mode-btn.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            /* Breadcrumb */
            .breadcrumb {
                padding: 15px 30px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 14px;
                color: #64748b;
            }
            
            /* Content Area */
            .content-area {
                flex: 1;
                overflow: hidden;
                position: relative;
            }
            
            /* Queue Interface */
            .queue-interface {
                display: none;
                padding: 30px;
                height: 100%;
                overflow-y: auto;
            }
            
            .queue-interface.active {
                display: block;
            }
            
            .queue-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border-left: 4px solid #3b82f6;
            }
            
            .stat-card.review { border-left-color: #f59e0b; }
            .stat-card.processing { border-left-color: #3b82f6; }
            .stat-card.completed { border-left-color: #10b981; }
            .stat-card.failed { border-left-color: #ef4444; }
            
            .stat-number {
                font-size: 32px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .stat-label {
                font-size: 14px;
                color: #64748b;
                margin-top: 5px;
            }
            
            .queue-grid {
                margin-top: 20px;
            }
            
            .queue-item {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 2px solid transparent;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .queue-item:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .queue-item.selected {
                border-color: #10b981;
                background: #f0fdf4;
            }
            
            .queue-item.priority {
                border-left: 4px solid #f59e0b;
            }
            
            .item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .item-title {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
            }
            
            .item-status {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .item-meta {
                font-size: 14px;
                color: #64748b;
                margin-bottom: 15px;
                line-height: 1.5;
            }
            
            .item-accuracy {
                margin: 15px 0;
            }
            
            .accuracy-bar {
                width: 100%;
                height: 8px;
                background: #e2e8f0;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 5px;
            }
            
            .accuracy-fill {
                height: 100%;
                background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
                transition: width 0.3s ease;
            }
            
            .accuracy-text {
                font-size: 12px;
                font-weight: 600;
                color: #1e293b;
            }
            
            .system-selection {
                margin: 15px 0;
                padding: 15px;
                background: #f8fafc;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
            }
            
            .system-label {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .system-checkboxes {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .system-checkbox {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .system-checkbox input[type="checkbox"] {
                width: 16px;
                height: 16px;
            }
            
            .system-checkbox label {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                cursor: pointer;
            }
            
            .system-description {
                font-size: 12px;
                color: #64748b;
                margin-left: 24px;
                margin-top: -4px;
            }
            
            .item-actions {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }
            
            .btn-primary {
                background: #3b82f6;
                color: white;
            }
            
            .btn-primary:hover {
                background: #2563eb;
            }
            
            .btn-success {
                background: #10b981;
                color: white;
            }
            
            .btn-success:hover {
                background: #059669;
            }
            
            .btn-secondary {
                background: #6b7280;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #4b5563;
            }
            
            .btn-warning {
                background: #f59e0b;
                color: white;
            }
            
            .btn-warning:hover {
                background: #d97706;
            }
            
                         /* Simple Mode - 2 Panel Layout */
             .simple-mode {
                 display: none;
                 height: 100%;
                 padding: 20px;
                 flex-direction: column;
             }
             
             .simple-mode.active {
                 display: flex;
             }
            
            .image-panel,
            .planogram-panel {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .panel-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                background: #f8fafc;
            }
            
            .panel-header h3 {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                margin: 0;
            }
            
            .panel-content {
                flex: 1;
                padding: 20px;
                overflow: auto;
            }
            
            .image-viewer {
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f8fafc;
                border-radius: 6px;
                overflow: hidden;
                position: relative;
            }
            
            .image-viewer img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                transition: transform 0.3s ease;
            }
            
            .image-controls {
                position: absolute;
                bottom: 10px;
                right: 10px;
                display: flex;
                gap: 5px;
                background: rgba(0,0,0,0.7);
                border-radius: 6px;
                padding: 5px;
            }
            
            .control-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .control-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .rating-system {
                margin-top: 20px;
                padding: 20px;
                background: #f8fafc;
                border-radius: 6px;
            }
            
            .rating-system h4 {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 10px;
            }
            
            .star-rating {
                display: flex;
                gap: 5px;
                margin-bottom: 15px;
            }
            
            .star {
                font-size: 24px;
                color: #d1d5db;
                cursor: pointer;
                transition: color 0.2s ease;
            }
            
            .star:hover,
            .star.active {
                color: #fbbf24;
            }
            
            .feedback-area {
                margin-top: 15px;
            }
            
            .feedback-area label {
                display: block;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                margin-bottom: 5px;
            }
            
            .feedback-area textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                resize: vertical;
                min-height: 80px;
            }
            
            /* Comparison Mode */
            .comparison-mode {
                display: none;
                height: 100%;
                padding: 20px;
                overflow-y: auto;
            }
            
            .comparison-mode.active {
                display: block;
            }
            
            .agent-tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .agent-tab {
                padding: 12px 20px;
                border: none;
                background: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #64748b;
                border-bottom: 2px solid transparent;
                transition: all 0.2s ease;
            }
            
            .agent-tab:hover {
                color: #3b82f6;
            }
            
            .agent-tab.active {
                color: #3b82f6;
                border-bottom-color: #3b82f6;
            }
            
            .agent-content {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                padding: 20px;
            }
            
            .agent-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background: #f8fafc;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
            }
            
            .metric-value {
                font-size: 24px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .metric-label {
                font-size: 12px;
                color: #64748b;
                margin-top: 5px;
            }
            
            .extraction-results {
                margin-top: 20px;
            }
            
            .results-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .result-card {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
            }
            
            .result-card h5 {
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 10px;
            }
            
            .result-details {
                font-size: 12px;
                color: #64748b;
                line-height: 1.4;
            }
            
            /* Advanced Mode */
            .advanced-mode {
                display: none;
                height: 100%;
                padding: 20px;
                overflow-y: auto;
            }
            
            .advanced-mode.active {
                display: block;
            }
            
            /* Advanced Mode Tabs */
            .advanced-tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .advanced-tab {
                padding: 12px 20px;
                border: none;
                background: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #64748b;
                border-bottom: 2px solid transparent;
                transition: all 0.2s ease;
            }
            
            .advanced-tab:hover {
                color: #3b82f6;
            }
            
            .advanced-tab.active {
                color: #3b82f6;
                border-bottom-color: #3b82f6;
            }
            
            .advanced-tab-content {
                display: none;
                height: calc(100% - 60px);
            }
            
            .advanced-tab-content.active {
                display: block;
            }
            
            .advanced-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 1fr 1fr;
                gap: 20px;
                height: 100%;
            }
            
            .advanced-panel {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .technical-analysis {
                padding: 20px;
                overflow-y: auto;
            }
            
            /* Log Viewer Styles */
            .logs-container {
                height: 100%;
                display: flex;
                flex-direction: column;
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .log-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .log-filters {
                display: flex;
                gap: 10px;
                align-items: center;
                flex-wrap: wrap;
            }
            
            .log-filters select,
            .log-filters input {
                padding: 6px 10px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 14px;
            }
            
            .log-filters input {
                min-width: 200px;
            }
            
            .log-actions {
                display: flex;
                gap: 8px;
                align-items: center;
            }
            
            .log-viewer {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
                background: #1e293b;
                color: #e2e8f0;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 13px;
                line-height: 1.4;
            }
            
            .log-entry {
                display: flex;
                align-items: flex-start;
                padding: 4px 0;
                border-bottom: 1px solid #334155;
                word-wrap: break-word;
            }
            
            .log-entry:hover {
                background: #334155;
            }
            
            .log-timestamp {
                color: #94a3b8;
                margin-right: 10px;
                min-width: 80px;
                font-weight: 500;
            }
            
            .log-level {
                margin-right: 10px;
                min-width: 60px;
                font-weight: 600;
                text-align: center;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 11px;
            }
            
            .log-level.ERROR {
                background: #dc2626;
                color: white;
            }
            
            .log-level.WARNING {
                background: #d97706;
                color: white;
            }
            
            .log-level.INFO {
                background: #2563eb;
                color: white;
            }
            
            .log-level.DEBUG {
                background: #6b7280;
                color: white;
            }
            
            .log-component {
                color: #60a5fa;
                margin-right: 10px;
                min-width: 120px;
                font-weight: 500;
            }
            
            .log-message {
                flex: 1;
                color: #e2e8f0;
            }
            
            .log-loading {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #64748b;
            }
            
            /* Error Summary Styles */
            .error-summary-panel {
                padding: 20px;
                overflow-y: auto;
            }
            
            .error-summary {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .error-item {
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 12px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .error-item:hover {
                background: #fee2e2;
                border-color: #f87171;
            }
            
            .error-item.warning {
                background: #fffbeb;
                border-color: #fed7aa;
            }
            
            .error-item.warning:hover {
                background: #fef3c7;
                border-color: #fbbf24;
            }
            
            .error-timestamp {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 4px;
            }
            
            .error-component {
                font-size: 12px;
                font-weight: 600;
                color: #374151;
                margin-bottom: 4px;
            }
            
            .error-message {
                font-size: 14px;
                color: #1f2937;
                line-height: 1.4;
            }
            
            .analysis-section {
                margin-bottom: 25px;
            }
            
            .analysis-section h4 {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 10px;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 5px;
            }
            
            .analysis-data {
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 12px;
                background: #f8fafc;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #e2e8f0;
                overflow-x: auto;
            }
            
            .orchestrator-panel {
                padding: 20px;
            }
            
            .orchestrator-flow {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .flow-step {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px;
                background: #f8fafc;
                border-radius: 6px;
                border-left: 4px solid #3b82f6;
            }
            
            .flow-step.completed {
                border-left-color: #10b981;
                background: #f0fdf4;
            }
            
            .flow-step.failed {
                border-left-color: #ef4444;
                background: #fef2f2;
            }
            
            .step-icon {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
                color: white;
                background: #3b82f6;
            }
            
            .flow-step.completed .step-icon {
                background: #10b981;
            }
            
            .flow-step.failed .step-icon {
                background: #ef4444;
            }
            
            .step-details {
                flex: 1;
            }
            
            .step-title {
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
            }
            
            .step-description {
                font-size: 12px;
                color: #64748b;
            }
            
            .step-timing {
                font-size: 11px;
                color: #9ca3af;
            }
            
            /* Responsive Design */
            @media (max-width: 1200px) {
                .left-sidebar {
                    width: 300px;
                }
                
                .advanced-grid {
                    grid-template-columns: 1fr;
                    grid-template-rows: repeat(4, 1fr);
                }
            }
            
            @media (max-width: 768px) {
                .left-sidebar {
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 100%;
                    z-index: 1000;
                    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
                }
                
                .simple-mode {
                    grid-template-columns: 1fr;
                    grid-template-rows: 1fr 1fr;
                }
                
                .queue-grid {
                    grid-template-columns: 1fr;
                }
                
                .queue-stats {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            /* Loading States */
            .loading {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
                color: #64748b;
            }
            
            .loading::before {
                content: "";
                width: 20px;
                height: 20px;
                border: 2px solid #e2e8f0;
                border-top: 2px solid #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Empty States */
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #64748b;
            }
            
            .empty-state h3 {
                font-size: 18px;
                margin-bottom: 10px;
                color: #374151;
            }
            
            .empty-state p {
                font-size: 14px;
                line-height: 1.5;
            }
            
            /* Process With Modal Styles */
            .modal-overlay {
                backdrop-filter: blur(4px);
                animation: fadeIn 0.2s ease-out;
            }
            
            .modal-content {
                animation: slideIn 0.3s ease-out;
                max-height: 90vh;
                overflow-y: auto;
            }
            
            .system-option {
                transition: all 0.2s ease;
            }
            
            .system-option:hover {
                border-color: #3b82f6 !important;
                background: #f8fafc !important;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
            }
            
            .system-option.selected {
                border-color: #3b82f6 !important;
                background: #f0f9ff !important;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideIn {
                from { 
                    opacity: 0;
                    transform: translateY(-20px) scale(0.95);
                }
                to { 
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <!-- Left Sidebar - Image Selection -->
            <div class="left-sidebar" id="leftSidebar">
                <button class="sidebar-toggle" onclick="toggleSidebar()">◀</button>
                
                <div class="sidebar-header">
                    <h3>📁 Image Library</h3>
                    <p style="font-size: 12px; color: #64748b; margin-top: 5px;">
                        Select an image to analyze
                    </p>
                </div>
                
                <div class="filters-section">
                    <div class="filter-group">
                        <label>Search</label>
                        <div class="search-box">
                            <input type="text" id="searchInput" placeholder="Search images..." onkeyup="filterImages()">
                        </div>
                    </div>
                    
                    <div class="filter-group">
                        <label>Store</label>
                        <select id="storeFilter" onchange="filterImages()">
                            <option value="">All Stores</option>
                            <!-- Real store data will be loaded from database -->
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Country</label>
                        <select id="countryFilter" onchange="filterImages()">
                            <option value="">All Countries</option>
                            <!-- Real country data will be loaded from database -->
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>City</label>
                        <select id="cityFilter" onchange="filterImages()">
                            <option value="">All Cities</option>
                            <!-- Real city data will be loaded from database -->
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Category</label>
                        <select id="categoryFilter" onchange="filterImages()">
                            <option value="">All Categories</option>
                            <!-- Real category data will be loaded from database -->
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Status</label>
                        <select id="statusFilter" onchange="filterImages()">
                            <option value="">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="processing">Processing</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                            <option value="review">Needs Review</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Date</label>
                        <input type="date" id="dateFilter" onchange="filterImages()">
                    </div>
                    
                    <div class="view-toggle">
                        <button class="active" onclick="setViewMode('grid')">Grid</button>
                        <button onclick="setViewMode('list')">List</button>
                    </div>
                </div>
                
                <div class="images-container">
                    <div id="imageGrid" class="image-grid">
                        <!-- Images will be loaded here -->
                    </div>
                </div>
                
                <div class="pagination">
                    <span id="paginationInfo">1-20 of 156 images</span>
                    <div class="pagination-controls">
                        <button onclick="previousPage()" id="prevBtn">‹</button>
                        <button class="active">1</button>
                        <button>2</button>
                        <button>3</button>
                        <button onclick="nextPage()" id="nextBtn">›</button>
                    </div>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="main-content">
                <!-- Header -->
                <div class="header">
                    <h1>🤖 OnShelf AI Dashboard</h1>
                                         <div class="mode-selector">
                         <button class="mode-btn active" onclick="switchMode('queue')">Queue</button>
                         <button class="mode-btn" onclick="switchMode('simple')">Simple</button>
                         <button class="mode-btn" onclick="switchMode('advanced')">Advanced</button>
                     </div>
                </div>
                
                <!-- Breadcrumb -->
                <div class="breadcrumb">
                    <span id="breadcrumb">Extraction Queue</span>
                </div>
                
                <!-- Content Area -->
                <div class="content-area">
                    <!-- Queue Interface -->
                    <div id="queue-interface" class="queue-interface active">
                        <div class="queue-stats">
                            <div class="stat-card review">
                                <div class="stat-number" id="reviewCount">0</div>
                                <div class="stat-label">Needs Review</div>
                            </div>
                            <div class="stat-card processing">
                                <div class="stat-number" id="processingCount">0</div>
                                <div class="stat-label">Processing</div>
                            </div>
                            <div class="stat-card completed">
                                <div class="stat-number" id="completedCount">0</div>
                                <div class="stat-label">Completed</div>
                            </div>
                            <div class="stat-card failed">
                                <div class="stat-number" id="failedCount">0</div>
                                <div class="stat-label">Failed</div>
                            </div>
                            <div class="stat-card" style="border-left-color: #f59e0b; background: linear-gradient(135deg, #fef3c7 0%, #fbbf24 100%); cursor: pointer;" onclick="resetAllFailedItems()">
                                <div class="stat-number" style="font-size: 20px; color: #92400e;">🔄</div>
                                <div class="stat-label" style="color: #92400e; font-weight: 600;">Reset All Failed</div>
                                <div style="font-size: 11px; color: #92400e; margin-top: 5px; opacity: 0.8;">Click to reset stuck items</div>
                            </div>
                        </div>
                        
                        <div id="queueGrid" class="queue-grid">
                            <!-- Queue items will be loaded here -->
                        </div>
                    </div>
                    
                                         <!-- Simple Mode - 2 Panel Layout -->
                     <div id="simple-mode" class="simple-mode">
                         <div class="simple-content" style="height: 100%; overflow-y: auto; padding: 20px;">
                             <!-- Top Panels: Image (40%) and Planogram (60%) - 25% taller -->
                             <div class="top-panels" style="display: grid; grid-template-columns: 2fr 3fr; gap: 20px; margin-bottom: 15px; height: 500px;">
                                                                    <div class="image-panel">
                                       <div class="panel-header" style="padding: 8px 20px; min-height: 20px;">
                                           <h3 style="margin: 0; font-size: 14px; font-weight: 600;">📷 Original Image</h3>
                                       </div>
                                     <div class="panel-content" style="height: 100%;">
                                         <div class="image-viewer" style="height: 100%;">
                                             <img id="originalImage" src="" alt="Original shelf image" style="display: none;">
                                             <div id="imageLoading" class="loading">Loading image...</div>
                                             <div class="image-controls">
                                                 <button class="control-btn" onclick="zoomImage(0.5)">50%</button>
                                                 <button class="control-btn" onclick="zoomImage(1.0)">100%</button>
                                                 <button class="control-btn" onclick="zoomImage(2.0)">200%</button>
                                                 <button class="control-btn" onclick="toggleOverlays()">Overlays</button>
                                             </div>
                                         </div>
                                     </div>
                                 </div>
                                 
                                                                    <div class="planogram-panel">
                                       <div class="panel-header" style="padding: 8px 20px; min-height: 20px;">
                                           <h3 style="margin: 0; font-size: 14px; font-weight: 600;">📊 Generated Planogram</h3>
                                       </div>
                                     <div class="panel-content" style="height: 100%;">
                                         <div id="planogramViewer" style="height: 100%; overflow: auto;">
                                             <div class="loading">Loading planogram...</div>
                                         </div>
                                     </div>
                                 </div>
                             </div>
                             
                             <!-- Dashboard and Controls Row - Half height, compact -->
                             <div class="dashboard-controls-row" style="display: grid; grid-template-columns: 2fr 3fr; gap: 20px; margin-bottom: 20px; height: 40px;">
                                 <!-- Compact Stats Dashboard -->
                                 <div id="compactStatsDashboard" class="compact-stats-dashboard" style="width: 100%; height: 100%;">
                                     <!-- Stats will be populated by JavaScript -->
                                 </div>
                                 
                                 <!-- Display Controls - Compact and Close to Planogram -->
                                 <div id="planogramControls" class="planogram-controls" style="width: 100%; height: 100%;">
                                     <!-- Controls will be populated by JavaScript -->
                                 </div>
                             </div>
                             
                             <!-- Full Width Products Table -->
                             <div id="extractedProductsTable" class="extracted-products-table" style="width: 100%; margin-bottom: 20px;">
                                 <!-- Table will be populated by JavaScript -->
                             </div>
                             
                             <!-- Rating System -->
                             <div class="rating-system">
                                 <h4>⭐ Extraction Quality</h4>
                                 <div class="star-rating" data-rating="extraction">
                                     <span class="star" data-value="1">★</span>
                                     <span class="star" data-value="2">★</span>
                                     <span class="star" data-value="3">★</span>
                                     <span class="star" data-value="4">★</span>
                                     <span class="star" data-value="5">★</span>
                                 </div>
                                 
                                 <div class="feedback-area">
                                     <label>What worked well:</label>
                                     <textarea id="workedWell" placeholder="Describe what the AI did correctly..."></textarea>
                                 </div>
                                 
                                 <h4 style="margin-top: 20px;">⭐ Planogram Quality</h4>
                                 <div class="star-rating" data-rating="planogram">
                                     <span class="star" data-value="1">★</span>
                                     <span class="star" data-value="2">★</span>
                                     <span class="star" data-value="3">★</span>
                                     <span class="star" data-value="4">★</span>
                                     <span class="star" data-value="5">★</span>
                                 </div>
                                 
                                 <div class="feedback-area">
                                     <label>Needs improvement:</label>
                                     <textarea id="needsImprovement" placeholder="Describe what needs to be fixed..."></textarea>
                                 </div>
                                 
                                 <div style="margin-top: 20px; display: flex; gap: 10px;">
                                     <button class="btn btn-secondary" onclick="switchMode('advanced')">Advanced Mode</button>
                                     <button class="btn btn-secondary" onclick="switchMode('queue')">Back to Queue</button>
                                 </div>
                             </div>
                         </div>
                     </div>
                    
                    
                    
                    <!-- Advanced Mode - Technical Deep Dive with Tabs -->
                    <div id="advanced-mode" class="advanced-mode">
                                                 <!-- Advanced Mode Tabs -->
                         <div class="advanced-tabs">
                             <button class="advanced-tab active" onclick="switchAdvancedTab('overview')">📊 Overview</button>
                             <button class="advanced-tab" onclick="switchAdvancedTab('logs')">📋 Logs</button>
                             <button class="advanced-tab" onclick="switchAdvancedTab('debugger')">🔍 Pipeline Debugger</button>
                             <button class="advanced-tab" onclick="switchAdvancedTab('iterations')">🔄 Iterations</button>
                             <button class="advanced-tab" onclick="switchAdvancedTab('comparison')">⚖️ System Comparison</button>
                             <button class="advanced-tab" onclick="switchAdvancedTab('orchestrator')">⚙️ Orchestrator</button>
                         </div>
                        
                        <!-- Overview Tab - 4 Panel Grid -->
                        <div id="advanced-overview" class="advanced-tab-content active">
                            <div class="advanced-grid">
                                <!-- Original Image Panel -->
                                <div class="advanced-panel">
                                    <div class="panel-header">
                                        <h3>📷 Original Image Analysis</h3>
                                    </div>
                                    <div class="panel-content">
                                        <div class="image-viewer">
                                            <img id="advancedOriginalImage" src="" alt="Original image">
                                            <div class="image-controls">
                                                <button class="control-btn" onclick="zoomImage(0.5)">50%</button>
                                                <button class="control-btn" onclick="zoomImage(1.0)">100%</button>
                                                <button class="control-btn" onclick="zoomImage(2.0)">200%</button>
                                                <button class="control-btn" onclick="toggleOverlays()">Overlays</button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Agent Deep Dive Panel -->
                                <div class="advanced-panel">
                                    <div class="panel-header">
                                        <h3>🔍 Agent Deep Dive</h3>
                                    </div>
                                    <div class="technical-analysis">
                                                                <div class="analysis-section">
                            <h4>Model Performance</h4>
                            <div class="analysis-data" id="modelPerformance">
                                Loading performance data...
                            </div>
                        </div>
                        
                        <div class="analysis-section">
                            <h4>Confidence Scores</h4>
                            <div class="analysis-data" id="confidenceScores">
                                Loading confidence data...
                            </div>
                        </div>
                        
                        <div class="analysis-section">
                            <h4>Error Analysis</h4>
                            <div class="analysis-data" id="errorAnalysis">
                                Loading error analysis...
                            </div>
                        </div>
                        
                        <div class="analysis-section" style="background: #eff6ff; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6;">
                            <h4>💡 Demo Available</h4>
                            <div style="font-size: 14px; color: #1e40af;">
                                <p>To see the planogram demonstration:</p>
                                <ol style="margin: 10px 0; padding-left: 20px;">
                                    <li>Click the <strong>"🔄 Iterations"</strong> tab above</li>
                                    <li>Select <strong>"📊 Demo: Interactive Planogram"</strong> from the dropdown</li>
                                    <li>View JSON data structure + static SVG representation</li>
                                    <li>See 18 products with stacking, gaps, and confidence colors</li>
                                </ol>
                                <p><em>The Interactive React component is available in Simple Mode when you select an image.</em></p>
                            </div>
                        </div>
                                    </div>
                                </div>
                                
                                <!-- Planogram Analysis Panel -->
                                <div class="advanced-panel">
                                    <div class="panel-header">
                                        <h3>📊 Planogram Analysis</h3>
                                    </div>
                                    <div class="panel-content">
                                        <div id="advancedPlanogramViewer" class="image-viewer">
                                            <div class="loading">Loading planogram...</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Quick Error Summary Panel -->
                                <div class="advanced-panel">
                                    <div class="panel-header">
                                        <h3>⚠️ Error Summary</h3>
                                    </div>
                                    <div class="error-summary-panel">
                                        <div id="errorSummary" class="error-summary">
                                            <!-- Error summary will be loaded here -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Logs Tab -->
                        <div id="advanced-logs" class="advanced-tab-content">
                            <div class="logs-container">
                                <!-- Log Controls -->
                                <div class="log-controls">
                                    <div class="log-filters">
                                        <select id="logLevelFilter" onchange="filterLogs()">
                                            <option value="">All Levels</option>
                                            <option value="ERROR">ERROR</option>
                                            <option value="WARNING">WARNING</option>
                                            <option value="INFO">INFO</option>
                                            <option value="DEBUG">DEBUG</option>
                                        </select>
                                        
                                        <select id="logComponentFilter" onchange="filterLogs()">
                                            <option value="">All Components</option>
                                            <option value="extraction_engine">Extraction Engine</option>
                                            <option value="agent">Agent</option>
                                            <option value="abstraction_manager">Abstraction Manager</option>
                                            <option value="queue_processor">Queue Processor</option>
                                            <option value="cost_tracker">Cost Tracker</option>
                                        </select>
                                        
                                        <input type="text" id="logSearchInput" placeholder="Search logs..." onkeyup="filterLogs()">
                                        
                                        <select id="logTimeRange" onchange="filterLogs()">
                                            <option value="1">Last 1 hour</option>
                                            <option value="6">Last 6 hours</option>
                                            <option value="24" selected>Last 24 hours</option>
                                            <option value="168">Last 7 days</option>
                                        </select>
                                    </div>
                                    
                                    <div class="log-actions">
                                        <button class="btn btn-secondary" onclick="toggleAutoScroll()">
                                            <span id="autoScrollText">⏸️ Pause Auto-scroll</span>
                                        </button>
                                        <button class="btn btn-secondary" onclick="exportLogs()">📥 Export</button>
                                        <button class="btn btn-secondary" onclick="clearLogView()">🗑️ Clear</button>
                                        <button class="btn btn-primary" onclick="refreshLogs()">🔄 Refresh</button>
                                    </div>
                                </div>
                                
                                <!-- Log Viewer -->
                                <div class="log-viewer" id="logViewer">
                                    <div class="log-loading">Loading logs...</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Pipeline Debugger Tab -->
                        <div id="advanced-debugger" class="advanced-tab-content">
                            <div class="debugger-container">
                                <h3>🔍 Real-Time Pipeline Debugger</h3>
                                
                                <!-- Debug Session Controls -->
                                <div class="debug-controls" style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                    <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 15px;">
                                        <div style="flex: 1;">
                                            <label style="display: block; font-weight: 600; margin-bottom: 5px;">Upload ID:</label>
                                            <input type="text" id="debugUploadId" placeholder="Enter upload ID to monitor" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px;">
                                        </div>
                                        <div style="align-self: end;">
                                            <button id="startDebugBtn" onclick="startDebugSession()" style="background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; cursor: pointer;">🔍 Monitor Extraction</button>
                                        </div>
                                    </div>
                                    
                                    <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border-left: 4px solid #64748b; margin-bottom: 15px;">
                                        <p style="margin: 0; font-size: 14px; color: #475569;">
                                            <strong>Real-Time Monitoring:</strong> This interface shows the ACTUAL Master Orchestrator iteration cycle. Each iteration generates a NEW planogram until target accuracy is achieved.
                                        </p>
                                        <p style="margin: 8px 0 0 0; font-size: 13px; color: #64748b;">
                                            🔄 <strong>Multiple Planograms:</strong> Iteration 1 → Planogram A → Compare → 75% accuracy → Iteration 2 → Planogram B → Compare → 88% accuracy → Continue until 95%+ achieved
                                        </p>
                                    </div>
                                    
                                    <div id="debugSessionInfo" style="display: none; background: #f0f9ff; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6;">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <div>
                                                <strong>Monitoring Session:</strong> <span id="debugSessionId">-</span><br>
                                                <strong>Status:</strong> <span id="debugStatus">-</span><br>
                                                <strong>Current Stage:</strong> <span id="debugCurrentStage">-</span>
                                            </div>
                                            <button onclick="stopDebugSession()" style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">Stop Monitoring</button>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Real-Time Pipeline Status -->
                                <div id="pipelineStatus" class="pipeline-status" style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                        <h4 style="margin: 0; color: #1f2937;">📊 System Workflow Status</h4>
                                                                            <div style="display: flex; gap: 10px; align-items: center;">
                                        <div style="background: #f0f9ff; padding: 6px 12px; border-radius: 6px; border: 1px solid #3b82f6;">
                                            <span style="font-size: 12px; font-weight: 600; color: #1e40af;">Monitoring System: </span>
                                            <span id="currentSystem" style="font-size: 12px; font-weight: 700; color: #1e40af;">Custom Consensus</span>
                                        </div>
                                        <div style="background: #fef3c7; padding: 6px 12px; border-radius: 6px; border: 1px solid #f59e0b;">
                                            <span style="font-size: 11px; color: #92400e;">⚠️ System selected before extraction starts</span>
                                        </div>
                                    </div>
                                    </div>
                                    
                                                        <!-- Master Orchestrator Iteration Cycle Progress -->
                    <div class="iteration-cycle-progress" style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight: 600;">Master Orchestrator Iteration Cycle:</span>
                            <span id="iterationProgressText">Ready to monitor extraction</span>
                        </div>
                        
                        <!-- Current Iteration Display -->
                        <div id="currentIterationDisplay" style="background: #f8fafc; padding: 12px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #3b82f6;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>Current Iteration:</strong> <span id="currentIterationNumber">-</span> / <span id="maxIterations">5</span>
                                    <br><strong>Target Accuracy:</strong> <span id="targetAccuracy">95%</span>
                                    <br><strong>Current Accuracy:</strong> <span id="currentAccuracy">-</span>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 24px; font-weight: 700; color: #3b82f6;" id="iterationStatus">⏳</div>
                                    <div style="font-size: 12px; color: #64748b;" id="iterationStatusText">Waiting</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Real Master Orchestrator Steps -->
                        <div id="masterOrchestratorSteps" style="display: flex; flex-direction: column; gap: 8px;">
                            <!-- Steps will be populated based on actual Master Orchestrator flow -->
                        </div>
                    </div>
                                    
                                    <!-- Orchestrator Info -->
                                    <div class="orchestrator-info" style="background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                            <div>
                                                <div style="font-size: 12px; color: #6b7280; font-weight: 600; text-transform: uppercase;">Orchestrator</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #1f2937;" id="orchestratorType">DeterministicOrchestrator</div>
                                            </div>
                                            <div>
                                                <div style="font-size: 12px; color: #6b7280; font-weight: 600; text-transform: uppercase;">Voting Mechanism</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #1f2937;" id="votingMechanism">weighted_consensus</div>
                                            </div>
                                            <div>
                                                <div style="font-size: 12px; color: #6b7280; font-weight: 600; text-transform: uppercase;">Active Models</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #1f2937;" id="activeModels">3</div>
                                            </div>
                                            <div>
                                                <div style="font-size: 12px; color: #6b7280; font-weight: 600; text-transform: uppercase;">Total Cost</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #1f2937;" id="totalCost">£0.00</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Real-Time Model Comparison -->
                                <div id="modelComparison" class="model-comparison" style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: none;">
                                    <h4 style="margin: 0 0 15px 0; color: #1f2937;">🤖 Live Consensus Voting</h4>
                                    
                                    <!-- Current Stage Breakdown -->
                                    <div id="currentStageBreakdown" style="background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
                                        <h5 style="margin: 0 0 10px 0; color: #374151;">Current Stage: <span id="currentStageTitle">Structure Analysis</span></h5>
                                        <div id="stageModelResults" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px;">
                                            <!-- Model results will be populated here -->
                                        </div>
                                    </div>
                                    
                                    <!-- Consensus Voting Results -->
                                    <div id="consensusResults" style="background: #f0f9ff; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6;">
                                        <h5 style="margin: 0 0 10px 0; color: #1e40af;">Consensus Decision</h5>
                                        <div id="consensusDecision" style="font-size: 14px; color: #1e40af;">
                                            Waiting for consensus voting...
                                        </div>
                                    </div>
                                    
                                    <!-- Cost Breakdown by Model -->
                                    <div id="costBreakdown" style="margin-top: 15px;">
                                        <h5 style="margin: 0 0 10px 0; color: #374151;">Cost Breakdown</h5>
                                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px;">
                                            <div style="background: #fef3c7; padding: 10px; border-radius: 4px; text-align: center;">
                                                <div style="font-size: 12px; color: #92400e;">Claude-3.5-Sonnet</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #92400e;" id="claudeCost">£0.00</div>
                                            </div>
                                            <div style="background: #dbeafe; padding: 10px; border-radius: 4px; text-align: center;">
                                                <div style="font-size: 12px; color: #1e40af;">GPT-4o</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #1e40af;" id="gpt4oCost">£0.00</div>
                                            </div>
                                            <div style="background: #d1fae5; padding: 10px; border-radius: 4px; text-align: center;">
                                                <div style="font-size: 12px; color: #065f46;">Gemini-2.0-Flash</div>
                                                <div style="font-size: 16px; font-weight: 700; color: #065f46;" id="geminiCost">£0.00</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Live Prompt Monitoring -->
                                <div id="livePromptMonitoring" class="live-prompt-monitoring" style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: none;">
                                    <h4 style="margin: 0 0 15px 0; color: #1f2937;">🤖 Live Prompt Monitoring</h4>
                                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px;">
                                        <div style="margin-bottom: 15px; font-size: 14px; color: #475569;">
                                            <strong>Real-time view of prompts being used by each AI model during extraction</strong>
                                        </div>
                                        <div id="promptContainer" style="display: flex; flex-direction: column; gap: 15px; max-height: 500px; overflow-y: auto;">
                                            <div style="color: #94a3b8; text-align: center; padding: 20px;">Waiting for extraction to start...</div>
                                        </div>
                                    </div>
                                </div>

                                <!-- Real-Time Logs -->
                                <div id="realTimeLogs" class="real-time-logs" style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: none;">
                                    <h4 style="margin: 0 0 15px 0; color: #1f2937;">📋 Real-Time Extraction Logs</h4>
                                    <div style="background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 13px; max-height: 400px; overflow-y: auto;" id="logContainer">
                                        <div style="color: #94a3b8;">Waiting for debug session to start...</div>
                                    </div>
                                </div>
                                
                                <!-- Active Sessions -->
                                <div class="active-sessions" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                    <h4 style="margin: 0 0 15px 0; color: #1f2937;">🔄 Active Debug Sessions</h4>
                                    <div id="activeSessionsList">
                                        <div style="color: #6b7280; text-align: center; padding: 20px;">No active debug sessions</div>
                                    </div>
                                    <button onclick="loadActiveSessions()" style="background: #6b7280; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-top: 10px;">🔄 Refresh Sessions</button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Iterations Tab -->
                        <div id="advanced-iterations" class="advanced-tab-content">
                            <div class="iterations-container">
                                <h3>🔄 Iteration Analysis</h3>
                                
                                <!-- Iteration Selector -->
                                <div class="iteration-selector">
                                    <label>Select Iteration:</label>
                                    <select id="iterationSelect" onchange="loadIterationDetails()">
                                        <option value="">Loading iterations...</option>
                                    </select>
                                    <span id="iterationStats" style="margin-left: 20px;"></span>
                                </div>
                                
                                <!-- Iteration Content Grid -->
                                <div class="iteration-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                                    <!-- Raw JSON Panel -->
                                    <div class="iteration-panel">
                                        <div class="panel-header">
                                            <h4>📋 Raw Extraction Data (JSON)</h4>
                                            <button onclick="copyJSON()" style="float: right;">📋 Copy</button>
                                        </div>
                                        <div class="json-viewer" id="iterationJSON" style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 12px; overflow: auto; max-height: 600px;">
                                            <div class="loading">Select an iteration to view data...</div>
                                        </div>
                                    </div>
                                    
                                    <!-- Planogram Panel -->
                                    <div class="iteration-panel">
                                        <div class="panel-header">
                                            <h4>📊 Planogram Visualization</h4>
                                            <span id="planogramAccuracy" style="float: right;"></span>
                                        </div>
                                        <div class="planogram-viewer" id="iterationPlanogram" style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow: auto; max-height: 600px;">
                                            <div class="loading">Select an iteration to view planogram...</div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Shelf-by-Shelf Breakdown -->
                                <div class="shelf-breakdown" style="margin-top: 20px;">
                                    <h4>📦 Shelf-by-Shelf Product Breakdown</h4>
                                    <div id="shelfBreakdown" style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                                        <div class="loading">Select an iteration to view shelf breakdown...</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                                                 <!-- System Comparison Tab -->
                         <div id="advanced-comparison" class="advanced-tab-content">
                             <div class="comparison-container">
                                 <div class="agent-tabs">
                                     <button class="agent-tab active" onclick="switchAgent('agent1')">Agent 1: Custom Consensus</button>
                                     <button class="agent-tab" onclick="switchAgent('agent2')">Agent 2: LangGraph</button>
                                     <button class="agent-tab" onclick="switchAgent('agent3')">Agent 3: Hybrid</button>
                                 </div>
                                 
                                 <div id="agent1" class="agent-content">
                                     <div class="agent-metrics">
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent1Accuracy">--</div>
                                             <div class="metric-label">Accuracy</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent1Speed">--</div>
                                             <div class="metric-label">Processing Time</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent1Cost">--</div>
                                             <div class="metric-label">API Cost</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent1Products">--</div>
                                             <div class="metric-label">Products Found</div>
                                         </div>
                                     </div>
                                     
                                     <div class="extraction-results">
                                         <h4>Extraction Results</h4>
                                         <div id="agent1Results" class="results-grid">
                                             <!-- Results will be loaded here -->
                                         </div>
                                     </div>
                                 </div>
                                 
                                 <div id="agent2" class="agent-content" style="display: none;">
                                     <div class="agent-metrics">
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent2Accuracy">--</div>
                                             <div class="metric-label">Accuracy</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent2Speed">--</div>
                                             <div class="metric-label">Processing Time</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent2Cost">--</div>
                                             <div class="metric-label">API Cost</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent2Products">--</div>
                                             <div class="metric-label">Products Found</div>
                                         </div>
                                     </div>
                                     
                                     <div class="extraction-results">
                                         <h4>Extraction Results</h4>
                                         <div id="agent2Results" class="results-grid">
                                             <!-- Results will be loaded here -->
                                         </div>
                                     </div>
                                 </div>
                                 
                                 <div id="agent3" class="agent-content" style="display: none;">
                                     <div class="agent-metrics">
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent3Accuracy">--</div>
                                             <div class="metric-label">Accuracy</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent3Speed">--</div>
                                             <div class="metric-label">Processing Time</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent3Cost">--</div>
                                             <div class="metric-label">API Cost</div>
                                         </div>
                                         <div class="metric-card">
                                             <div class="metric-value" id="agent3Products">--</div>
                                             <div class="metric-label">Products Found</div>
                                         </div>
                                     </div>
                                     
                                     <div class="extraction-results">
                                         <h4>Extraction Results</h4>
                                         <div id="agent3Results" class="results-grid">
                                             <!-- Results will be loaded here -->
                                         </div>
                                     </div>
                                 </div>
                             </div>
                         </div>
                         
                         <!-- Orchestrator Tab -->
                         <div id="advanced-orchestrator" class="advanced-tab-content">
                             <div class="orchestrator-container">
                                 <div class="orchestrator-flow" id="orchestratorFlow">
                                     <!-- Flow steps will be loaded here -->
                                 </div>
                             </div>
                         </div>
                        

                    </div>
                </div>
            </div>
        </div>
        
        <!-- Process With Modal -->
        <div id="processWithModal" class="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 10000; align-items: center; justify-content: center;" onclick="closeProcessWithModal()">
            <div class="modal-content" style="background: white; border-radius: 12px; padding: 30px; max-width: 500px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3);" onclick="event.stopPropagation()">
                <h3 style="margin: 0 0 20px 0; color: #1f2937; font-size: 20px; font-weight: 700;" id="processModalTitle">🚀 Process with AI System</h3>
                
                <div style="margin-bottom: 25px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 10px; color: #374151;">Select AI Extraction System:</label>
                    
                    <div style="display: flex; flex-direction: column; gap: 12px;">
                        <label class="system-option" style="display: flex; align-items: center; gap: 12px; padding: 15px; border: 2px solid #e5e7eb; border-radius: 8px; cursor: pointer;" onclick="selectSystem('custom_consensus', this)">
                            <input type="radio" name="aiSystem" value="custom_consensus" style="width: 18px; height: 18px;">
                            <div>
                                <div style="font-weight: 600; color: #1f2937;">Custom Consensus System</div>
                                <div style="font-size: 13px; color: #6b7280;">3 AI models vote in parallel (GPT-4o, Claude-3.5-Sonnet, Gemini-2.0-Flash)</div>
                                <div style="font-size: 12px; color: #3b82f6; margin-top: 4px;">⚡ Best for accuracy • 🎯 Weighted consensus • 💰 Moderate cost</div>
                            </div>
                        </label>
                        
                        <label class="system-option" style="display: flex; align-items: center; gap: 12px; padding: 15px; border: 2px solid #e5e7eb; border-radius: 8px; cursor: pointer;" onclick="selectSystem('langgraph', this)">
                            <input type="radio" name="aiSystem" value="langgraph" style="width: 18px; height: 18px;">
                            <div>
                                <div style="font-weight: 600; color: #1f2937;">LangGraph Workflow System</div>
                                <div style="font-size: 13px; color: #6b7280;">Sequential workflow with state management and smart retry logic</div>
                                <div style="font-size: 12px; color: #10b981; margin-top: 4px;">🔄 Self-correcting • 📊 State tracking • 💡 Efficient</div>
                            </div>
                        </label>
                        
                        <label class="system-option" style="display: flex; align-items: center; gap: 12px; padding: 15px; border: 2px solid #e5e7eb; border-radius: 8px; cursor: pointer;" onclick="selectSystem('hybrid', this)">
                            <input type="radio" name="aiSystem" value="hybrid" style="width: 18px; height: 18px;">
                            <div>
                                <div style="font-weight: 600; color: #1f2937;">Hybrid Adaptive System</div>
                                <div style="font-size: 13px; color: #6b7280;">Dynamically selects best approach based on image complexity</div>
                                <div style="font-size: 12px; color: #f59e0b; margin-top: 4px;">🧠 Adaptive • 🎯 Context-aware • 🚀 Optimized</div>
                            </div>
                        </label>
                    </div>
                </div>
                
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #3b82f6;">
                    <div style="font-size: 14px; color: #1e40af; font-weight: 600; margin-bottom: 5px;">💡 How it works:</div>
                    <div style="font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 10px;">
                        The Master Orchestrator will run multiple iterations until 95% accuracy is achieved. Each iteration generates a new planogram and compares it to the original image.
                    </div>
                    <div style="font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 8px;">
                        <strong>Keyboard shortcuts:</strong> Press 1-3 to select system • Enter to start • Escape to cancel
                    </div>
                </div>
                
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button onclick="closeProcessWithModal()" style="padding: 10px 20px; border: 1px solid #d1d5db; background: white; border-radius: 6px; cursor: pointer; font-weight: 500; transition: all 0.2s ease;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='white'">Cancel</button>
                    <button id="processWithBtn" onclick="processWithSelectedSystem()" style="padding: 10px 20px; background: #9ca3af; color: white; border: none; border-radius: 6px; cursor: not-allowed; font-weight: 600; transition: all 0.2s ease; opacity: 0.6;" disabled onmouseover="if(!this.disabled) this.style.background='#2563eb'" onmouseout="if(!this.disabled) this.style.background='#3b82f6'">🚀 Start Processing</button>
                </div>
            </div>
        </div>
        
        <!-- Initialize React Components -->
        <script>
            // Debug React loading
            console.log('=== REACT LOADING DEBUG ===');
            console.log('React available:', typeof React !== 'undefined');
            console.log('ReactDOM available:', typeof ReactDOM !== 'undefined');
            
            // Wait for everything to load
            window.addEventListener('DOMContentLoaded', function() {
                console.log('=== DOM LOADED ===');
                console.log('React available:', typeof React !== 'undefined');
                console.log('ReactDOM available:', typeof ReactDOM !== 'undefined');
                console.log('InteractivePlanogram available:', typeof window.InteractivePlanogram !== 'undefined');
                
                // Try to load the component file manually if it's not available
                if (typeof window.InteractivePlanogram === 'undefined') {
                    console.error('❌ InteractivePlanogram component not loaded!');
                    console.log('Attempting to reload component...');
                    
                    const script = document.createElement('script');
                    script.src = '/static/components/InteractivePlanogram.js?v=' + Date.now();
                    script.onload = function() {
                        console.log('✅ Component script reloaded');
                        console.log('InteractivePlanogram now available:', typeof window.InteractivePlanogram !== 'undefined');
                        
                        // If still not available, there's a syntax error in the file
                        if (typeof window.InteractivePlanogram === 'undefined') {
                            console.error('❌ Component still not available after reload - syntax error in file');
                        }
                    };
                    script.onerror = function(e) {
                        console.error('❌ Failed to reload component script:', e);
                        console.log('Trying to fetch the file directly to check content...');
                        
                        fetch('/static/components/InteractivePlanogram.js')
                            .then(response => response.text())
                            .then(text => {
                                console.log('File content preview:', text.substring(0, 200));
                                if (text.includes('<html') || text.includes('<!DOCTYPE')) {
                                    console.error('❌ File is returning HTML instead of JavaScript!');
                                }
                            })
                            .catch(err => console.error('❌ Failed to fetch file:', err));
                    };
                    document.head.appendChild(script);
                } else {
                    console.log('✅ InteractivePlanogram component is available');
                }
            });
        </script>
        
        <script>
            // Global state
            let currentMode = 'queue';
            let selectedItemId = null;
            let queueData = [];
            let imageData = [];
            let filteredImages = [];
            let currentPage = 1;
            let itemsPerPage = 20;
            let viewMode = 'grid';
            let sidebarCollapsed = false;
            let zoomLevel = 1.0;
            let overlaysVisible = false;
            let currentAgent = 'agent1';
            let currentAdvancedTab = 'overview';
            let autoScrollEnabled = true;
            let logRefreshInterval = null;
            
            // Global planogram component reference
            let currentPlanogramComponent = null;
            
                         // Initialize application
             document.addEventListener('DOMContentLoaded', function() {
                 // Initialize sidebar state - start in queue mode with sidebar hidden
                 const sidebar = document.getElementById('leftSidebar');
                 const toggle = sidebar.querySelector('.sidebar-toggle');
                 
                 // Start in queue mode with sidebar hidden
                 sidebar.style.display = 'none';
                 sidebarCollapsed = false;
                 toggle.innerHTML = '◀';
                 
                 loadQueue();
                 loadImages();
                 loadFilterData();
             });
            
            // Sidebar management
            function toggleSidebar() {
                const sidebar = document.getElementById('leftSidebar');
                const toggle = sidebar.querySelector('.sidebar-toggle');
                const mainContent = document.querySelector('.main-content');
                
                sidebarCollapsed = !sidebarCollapsed;
                
                if (sidebarCollapsed) {
                    // Hide sidebar completely
                    sidebar.style.display = 'none';
                    sidebar.classList.add('collapsed');
                    toggle.innerHTML = '▶';
                    toggle.style.left = '0px';
                    
                    // Expand main content to fill entire viewport
                    mainContent.style.width = '100vw';
                    mainContent.style.marginLeft = '0';
                    
                    // Find and resize all the actual content containers
                    const topPanels = document.querySelector('.top-panels');
                    const dashboardControlsRow = document.querySelector('.dashboard-controls-row');
                    const extractedProductsTable = document.getElementById('extractedProductsTable');
                    const ratingSystem = document.querySelector('.rating-system');
                    
                    if (topPanels) {
                        topPanels.style.width = 'calc(100vw - 40px)';
                    }
                    if (dashboardControlsRow) {
                        dashboardControlsRow.style.width = 'calc(100vw - 40px)';
                    }
                    if (extractedProductsTable) {
                        extractedProductsTable.style.width = 'calc(100vw - 40px)';
                    }
                    if (ratingSystem) {
                        ratingSystem.style.width = 'calc(100vw - 40px)';
                    }
                } else {
                    // Show sidebar
                    sidebar.style.display = 'flex';
                    sidebar.classList.remove('collapsed');
                    toggle.innerHTML = '◀';
                    toggle.style.left = '380px';
                    
                    // Reset main content to normal
                    mainContent.style.width = '';
                    mainContent.style.marginLeft = '';
                    
                    // Reset all content containers
                    const topPanels = document.querySelector('.top-panels');
                    const dashboardControlsRow = document.querySelector('.dashboard-controls-row');
                    const extractedProductsTable = document.getElementById('extractedProductsTable');
                    const ratingSystem = document.querySelector('.rating-system');
                    
                    if (topPanels) {
                        topPanels.style.width = '';
                    }
                    if (dashboardControlsRow) {
                        dashboardControlsRow.style.width = '';
                    }
                    if (extractedProductsTable) {
                        extractedProductsTable.style.width = '';
                    }
                    if (ratingSystem) {
                        ratingSystem.style.width = '';
                    }
                }
            }
            
                         // Mode switching
             function switchMode(mode) {
                 // Clean up React components before switching modes
                 const planogramViewer = document.getElementById('planogramViewer');
                 const advancedPlanogram = document.getElementById('advancedPlanogramViewer');
                 
                 if (planogramViewer && typeof ReactDOM !== 'undefined') {
                     try {
                         ReactDOM.unmountComponentAtNode(planogramViewer);
                     } catch (e) {
                         // Ignore unmount errors
                     }
                 }
                 
                 if (advancedPlanogram && typeof ReactDOM !== 'undefined') {
                     try {
                         ReactDOM.unmountComponentAtNode(advancedPlanogram);
                     } catch (e) {
                         // Ignore unmount errors
                     }
                 }
                 
                 // Hide all modes
                 document.getElementById('queue-interface').classList.remove('active');
                 document.getElementById('simple-mode').classList.remove('active');
                 document.getElementById('advanced-mode').classList.remove('active');
                 
                 // Update mode buttons
                 document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
                 // Find the button that was clicked for this mode
                 const targetButton = document.querySelector(`[onclick="switchMode('${mode}')"]`);
                 if (targetButton) {
                     targetButton.classList.add('active');
                 }
                 
                 // Show/hide sidebar based on mode
                 const sidebar = document.querySelector('.left-sidebar');
                 if (mode === 'queue') {
                     sidebar.style.display = 'none';
                 } else {
                     sidebar.style.display = 'flex';
                 }
                 
                 // Show selected mode
                 if (mode === 'queue') {
                     document.getElementById('queue-interface').classList.add('active');
                     updateBreadcrumb('Extraction Queue');
                 } else if (mode === 'simple') {
                     document.getElementById('simple-mode').classList.add('active');
                     
                     // Always default to demo for now since real extraction data isn't available
                     if (!selectedItemId || selectedItemId === 5 || selectedItemId === 1) {
                         selectedItemId = 'demo';
                         updateBreadcrumb('Demo - Interactive Planogram');
                     } else {
                         updateBreadcrumb(`Extraction #${selectedItemId} - Simple Analysis`);
                     }
                     
                     loadSimpleModeData();
                 } else if (mode === 'advanced') {
                     document.getElementById('advanced-mode').classList.add('active');
                     updateBreadcrumb(`Extraction #${selectedItemId} - Advanced Analysis`);
                     loadAdvancedModeData();
                 }
                 
                 currentMode = mode;
             }
            
            function updateBreadcrumb(text) {
                document.getElementById('breadcrumb').innerHTML = `<span>${text}</span>`;
            }
            
            // Load queue data
            async function loadQueue() {
                try {
                    console.log('🔄 Loading queue data from API...');
                    const response = await fetch('/api/queue/items');
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    queueData = data.items || [];
                    
                    console.log(`✅ Successfully loaded ${queueData.length} real queue items from database`);
                    console.log('Queue items:', queueData.map(item => `#${item.id} (${item.status})`).join(', '));
                    
                    updateQueueStats();
                    renderQueue();
                    
                } catch (error) {
                    console.error('❌ Failed to load queue data:', error);
                    
                    // Show error state instead of mock data
                    queueData = [];
                    updateQueueStats();
                    renderQueueError(error.message);
                }
            }
            
            // Load images for sidebar
            async function loadImages() {
                try {
                    console.log('🔄 Loading image data from API...');
                    const response = await fetch('/api/queue/items');
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    imageData = data.items || [];
                    filteredImages = [...imageData];
                    
                    console.log(`✅ Successfully loaded ${imageData.length} real images for sidebar`);
                    renderImages();
                    
                } catch (error) {
                    console.error('❌ Failed to load image data:', error);
                    
                    // Show error state instead of mock data
                    imageData = [];
                    filteredImages = [];
                    renderImagesError(error.message);
                }
            }
            
            // Load real filter data from database
            async function loadFilterData() {
                try {
                    console.log('🔄 Loading filter data from database...');
                    
                    // Load real store data
                    const storeResponse = await fetch('/api/queue/stores');
                    if (storeResponse.ok) {
                        const stores = await storeResponse.json();
                        const storeSelect = document.getElementById('storeFilter');
                        
                        // Clear existing options except "All Stores"
                        while (storeSelect.children.length > 1) {
                            storeSelect.removeChild(storeSelect.lastChild);
                        }
                        
                        // Add real store options
                        stores.forEach(store => {
                            const option = document.createElement('option');
                            option.value = store.id;
                            option.textContent = store.name;
                            storeSelect.appendChild(option);
                        });
                        
                        console.log(`✅ Loaded ${stores.length} real stores`);
                    } else {
                        console.log('ℹ️ No store data available from API');
                    }
                    
                    // Load real category data
                    const categoryResponse = await fetch('/api/queue/categories');
                    if (categoryResponse.ok) {
                        const categories = await categoryResponse.json();
                        const categorySelect = document.getElementById('categoryFilter');
                        
                        // Clear existing options except "All Categories"
                        while (categorySelect.children.length > 1) {
                            categorySelect.removeChild(categorySelect.lastChild);
                        }
                        
                        // Add real category options
                        categories.forEach(category => {
                            const option = document.createElement('option');
                            option.value = category.id;
                            option.textContent = category.name;
                            categorySelect.appendChild(option);
                        });
                        
                        console.log(`✅ Loaded ${categories.length} real categories`);
                    } else {
                        console.log('ℹ️ No category data available from API');
                    }
                    
                    // Load real country data
                    const countryResponse = await fetch('/api/queue/countries');
                    if (countryResponse.ok) {
                        const countries = await countryResponse.json();
                        const countrySelect = document.getElementById('countryFilter');
                        
                        // Clear existing options except "All Countries"
                        while (countrySelect.children.length > 1) {
                            countrySelect.removeChild(countrySelect.lastChild);
                        }
                        
                        // Add real country options
                        countries.forEach(country => {
                            const option = document.createElement('option');
                            option.value = country.id;
                            option.textContent = country.name;
                            countrySelect.appendChild(option);
                        });
                        
                        console.log(`✅ Loaded ${countries.length} real countries`);
                    } else {
                        console.log('ℹ️ No country data available from API');
                    }
                    
                    // Load real city data
                    const cityResponse = await fetch('/api/queue/cities');
                    if (cityResponse.ok) {
                        const cities = await cityResponse.json();
                        const citySelect = document.getElementById('cityFilter');
                        
                        // Clear existing options except "All Cities"
                        while (citySelect.children.length > 1) {
                            citySelect.removeChild(citySelect.lastChild);
                        }
                        
                        // Add real city options
                        cities.forEach(city => {
                            const option = document.createElement('option');
                            option.value = city.id;
                            option.textContent = city.name;
                            citySelect.appendChild(option);
                        });
                        
                        console.log(`✅ Loaded ${cities.length} real cities`);
                    } else {
                        console.log('ℹ️ No city data available from API');
                    }
                    
                } catch (error) {
                    console.error('❌ Failed to load filter data:', error);
                    console.log('ℹ️ Using empty filters (no mock data)');
                }
            }

            
            // Update queue statistics
            function updateQueueStats() {
                const stats = {
                    review: queueData.filter(item => item.human_review_required).length,
                    processing: queueData.filter(item => item.status === 'processing').length,
                    completed: queueData.filter(item => item.status === 'completed').length,
                    failed: queueData.filter(item => item.status === 'failed').length
                };
                
                document.getElementById('reviewCount').textContent = stats.review;
                document.getElementById('processingCount').textContent = stats.processing;
                document.getElementById('completedCount').textContent = stats.completed;
                document.getElementById('failedCount').textContent = stats.failed;
            }
            
            // Render queue error
            function renderQueueError(errorMessage) {
                const grid = document.getElementById('queueGrid');
                grid.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1;">
                        <h3>❌ Failed to Load Queue</h3>
                        <p>Error: ${errorMessage}</p>
                        <button class="btn btn-primary" onclick="loadQueue()" style="margin-top: 15px;">🔄 Retry</button>
                    </div>
                `;
            }
            
            // Render queue items as table
            function renderQueue() {
                const grid = document.getElementById('queueGrid');
                
                if (queueData.length === 0) {
                    grid.innerHTML = `
                        <div class="empty-state">
                            <h3>📭 No Queue Items</h3>
                            <p>No extraction items found in the queue. Upload some images to get started.</p>
                        </div>
                    `;
                    return;
                }
                
                // Transform to table format
                grid.innerHTML = `
                    <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
                        <h3 style="margin: 0 0 20px 0; color: #2d3748; font-size: 20px; font-weight: 700;">📋 Extraction Queue (${queueData.length} items)</h3>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                                <thead>
                                                                            <tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">
                                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #4a5568; min-width: 100px;">Status</th>
                                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #4a5568; min-width: 100px;">Date</th>
                                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #4a5568; min-width: 120px;">Store</th>
                                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #4a5568; min-width: 100px;">Category</th>
                                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #4a5568; min-width: 80px;">Country</th>
                                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #4a5568; min-width: 100px;">Upload ID</th>
                                            <th style="padding: 12px 8px; text-align: center; font-weight: 600; color: #4a5568; min-width: 80px;">Accuracy</th>
                                            <th style="padding: 12px 8px; text-align: center; font-weight: 600; color: #4a5568; min-width: 80px;">Debug</th>
                                            <th style="padding: 12px 8px; text-align: center; font-weight: 600; color: #4a5568; min-width: 120px;">Actions</th>
                                        </tr>
                                </thead>
                                <tbody>
                                    ${queueData.map(item => {
                                        const statusColor = getStatusColor(item.status);
                                        const accuracy = item.final_accuracy ? Math.round(item.final_accuracy * 100) : null;
                                        const accuracyColor = accuracy >= 90 ? '#10b981' : accuracy >= 70 ? '#f59e0b' : '#ef4444';
                                        const uploadId = item.upload_id || '-';
                                        
                                        // Extract data from uploads and metadata
                                        const uploads = item.uploads || {};
                                        const metadata = uploads.metadata || {};
                                        
                                        // Debug logging
                                        if (item.id === 5) {
                                            console.log('Item 5 data:', item);
                                            console.log('Uploads:', uploads);
                                            console.log('Metadata:', metadata);
                                        }
                                        
                                        const category = uploads.category || '-';
                                        const uploadDate = uploads.created_at || item.created_at;
                                        const storeName = metadata.store_name || metadata.retailer || '-';
                                        const storeLocation = metadata.city || '-';
                                        const country = metadata.country || '-';
                                        
                                        return `
                                            <tr style="border-bottom: 1px solid #e2e8f0; cursor: pointer; ${selectedItemId === item.id ? 'background-color: #f0f9ff;' : ''}" 
                                                onclick="selectQueueItem(${item.id})" 
                                                onmouseover="this.style.backgroundColor='#f8fafc'" 
                                                onmouseout="this.style.backgroundColor='${selectedItemId === item.id ? '#f0f9ff' : 'transparent'}'">
                                                <td style="padding: 12px 8px;">
                                                    <div style="display: flex; align-items: center; gap: 8px;">
                                                        <div style="width: 8px; height: 8px; border-radius: 50%; background-color: ${statusColor};"></div>
                                                        <span style="font-weight: 600; color: ${statusColor};">${getStatusText(item.status)}</span>
                                                        ${item.human_review_required ? '<span style="color: #f59e0b; margin-left: 4px;">⚠️</span>' : ''}
                                                    </div>
                                                </td>
                                                <td style="padding: 12px 8px; color: #4a5568;">
                                                    ${new Date(uploadDate).toLocaleDateString()}
                                                    <div style="font-size: 12px; color: #64748b;">${new Date(uploadDate).toLocaleTimeString()}</div>
                                                </td>
                                                <td style="padding: 12px 8px; color: #2d3748; font-weight: 500;">
                                                    ${storeName}
                                                    ${storeLocation !== '-' ? `<div style="font-size: 12px; color: #64748b;">${storeLocation}</div>` : ''}
                                                </td>
                                                <td style="padding: 12px 8px; color: #4a5568;">
                                                    ${category}
                                                </td>
                                                <td style="padding: 12px 8px; color: #4a5568;">
                                                    ${country}
                                                </td>
                                                <td style="padding: 12px 8px; color: #64748b; font-family: monospace; font-size: 12px;">
                                                    ${uploadId.length > 30 ? uploadId.substring(0, 8) + '...' : uploadId}
                                                </td>
                                                <td style="padding: 12px 8px; text-align: center;">
                                                    ${accuracy !== null ? `
                                                        <span style="font-weight: 600; color: ${accuracyColor};">${accuracy}%</span>
                                                    ` : '<span style="color: #94a3b8;">-</span>'}
                                                </td>
                                                <td style="padding: 12px 8px; text-align: center;">
                                                    <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px; background: #8b5cf6; border-color: #8b5cf6; color: white; font-weight: 600;" onclick="event.stopPropagation(); openDebugInterface('${item.ready_media_id || item.id}')">🔍 Debug</button>
                                                </td>
                                                                                                <td style="padding: 12px 8px; text-align: center;">
                                                    <div style="display: flex; gap: 4px; justify-content: center; flex-wrap: wrap;">
                        ${item.status === 'pending' ? `
                                                            <button class="btn btn-primary" style="padding: 4px 8px; font-size: 12px;" onclick="event.stopPropagation(); showProcessWithModal(${item.id})">🚀 Process With</button>
                                                        ` : `
                                                            <button class="btn btn-success" style="padding: 4px 8px; font-size: 12px;" onclick="event.stopPropagation(); viewResults(${item.id})">View</button>
                                                        `}
                                                        ${(item.status === 'failed' || item.status === 'processing') ? `
                                                            <button class="btn btn-warning" style="padding: 4px 8px; font-size: 12px;" onclick="event.stopPropagation(); resetItem(${item.id})">🔄 Reset</button>
                                                        ` : ''}
            ${item.status === 'completed' ? `
                                                            <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px;" onclick="event.stopPropagation(); showProcessWithModal(${item.id}, true)">🔄 Reprocess With</button>
            ` : ''}
                                                        <button class="btn" style="padding: 4px 8px; font-size: 12px; background: #ef4444; color: white;" onclick="event.stopPropagation(); removeItem(${item.id})">🗑️ Remove</button>
                        </div>
                                                </td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }
            
            // Helper function for status colors
            function getStatusColor(status) {
                switch(status) {
                    case 'completed': return '#10b981';
                    case 'processing': return '#3b82f6';
                    case 'pending': return '#f59e0b';
                    case 'failed': return '#ef4444';
                    default: return '#64748b';
                }
            }
            
            // Render images error
            function renderImagesError(errorMessage) {
                const container = document.getElementById('imageGrid');
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>❌ Failed to Load Images</h3>
                        <p>Error: ${errorMessage}</p>
                        <button class="btn btn-primary" onclick="loadImages()" style="margin-top: 15px;">🔄 Retry</button>
                    </div>
                `;
            }
            
            // Render images in sidebar
            function renderImages() {
                const container = document.getElementById('imageGrid');
                const startIndex = (currentPage - 1) * itemsPerPage;
                const endIndex = startIndex + itemsPerPage;
                const pageImages = filteredImages.slice(startIndex, endIndex);
                
                container.className = viewMode === 'grid' ? 'image-grid' : 'image-list';
                
                if (pageImages.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <h3>📭 No Images</h3>
                            <p>No images available. Upload some images to get started.</p>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = pageImages.map(image => `
                    <div class="image-item ${viewMode}-view ${selectedItemId === image.id ? 'selected' : ''}" 
                         onclick="selectImage(${image.id})">
                        <div class="image-thumbnail">
                            <img src="/api/queue/image/${image.id}" alt="Queue item ${image.id}" 
                                 style="width: 100%; height: 100%; object-fit: cover;" 
                                 onerror="this.style.display='none'; this.parentElement.innerHTML='📷';">
                        </div>
                        <div class="image-info">
                            <div class="image-title">Extraction #${image.id}</div>
                            <div class="image-meta">
                                ${image.ready_media_id ? `Media: ${image.ready_media_id.substring(0, 8)}...` : 'No media ID'}<br>
                                ${new Date(image.created_at).toLocaleDateString()}
                                <div class="status-badge status-${image.status}">${image.status}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
                
                updatePagination();
            }
            
            // Image selection
            function selectImage(imageId) {
                selectedItemId = imageId;
                
                // Update visual selection in sidebar
                document.querySelectorAll('.image-item').forEach(item => {
                    item.classList.remove('selected');
                });
                event.target.closest('.image-item').classList.add('selected');
                
                // Auto-switch to simple mode and load the image
                switchMode('simple');
                
                // Close sidebar on mobile
                if (window.innerWidth <= 768) {
                    toggleSidebar();
                }
            }
            
            // Load data for different modes
                         async function loadSimpleModeData() {
                 try {
                     // Load original image (or show demo message)
                     const imageElement = document.getElementById('originalImage');
                     const loadingElement = document.getElementById('imageLoading');
                     
                     if (selectedItemId && selectedItemId !== 'demo') {
                         imageElement.onload = function() {
                             loadingElement.style.display = 'none';
                             imageElement.style.display = 'block';
                         };
                         
                         imageElement.onerror = function() {
                             loadingElement.innerHTML = 'Failed to load image';
                         };
                         
                         imageElement.src = `/api/queue/image/${selectedItemId}`;
                     } else {
                         // Show demo message for image
                         loadingElement.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748b;"><h3>📷 Demo Mode</h3><p>Select a real image from the sidebar to see the original photo, or view the interactive planogram demo on the right.</p></div>';
                         imageElement.style.display = 'none';
                     }
                     
                     // Load interactive planogram - ALWAYS show demo if no real item
                     const planogramViewer = document.getElementById('planogramViewer');
                     const imageId = selectedItemId || 'demo';
                     
                     console.log('Loading planogram for:', imageId);
                     
                     // Simple HTML/CSS Grid Approach - Convert React logic to pure HTML/CSS
                     async function renderSimpleGridPlanogram() {
                         console.log('🎯 Rendering Simple HTML/CSS Grid Planogram (converted from React)');
                         
                         try {
                             // Fetch planogram data
                             const response = await fetch(`/api/planogram/${imageId}/editable`);
                             if (!response.ok) {
                                 throw new Error(`Failed to load data: ${response.statusText}`);
                             }
                             
                             const data = await response.json();
                             console.log('📊 Planogram data loaded:', data);
                             
                             // Clear container
                             planogramViewer.innerHTML = '';
                             
                             // Create the planogram using your React component logic but in pure HTML/CSS
                             createSimpleGridPlanogram(planogramViewer, data.planogram);
                             
                             console.log('✅ Simple HTML/CSS planogram rendered');
                             
                         } catch (error) {
                             console.error('❌ Error loading planogram:', error);
                             planogramViewer.innerHTML = `
                                 <div style="padding: 20px; text-align: center; color: #dc2626;">
                                     <h3>❌ Failed to Load Planogram</h3>
                                     <p>${error.message}</p>
                                 </div>
                             `;
                         }
                     }
                     
                     // Render the simple grid planogram
                     renderSimpleGridPlanogram();
                     
                     // Load planogram controls
                     await loadPlanogramControls(imageId);
                     
                     // Load compact stats dashboard
                     await loadCompactStatsDashboard(imageId);
                     
                     // Load extracted products table
                     await loadExtractedProductsTable(imageId);
                     
                 } catch (error) {
                     console.error('Error loading simple mode data:', error);
                 }
             }
             
             async function loadPlanogramControls(imageId) {
                 const controlsContainer = document.getElementById('planogramControls');
                 
                 // Create ultra-compact controls for half-height container
                 const controlsHTML = `
                     <div style="background: white; border-radius: 6px; padding: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); height: 100%; display: flex; align-items: center;">
                         <div style="width: 100%; display: flex; justify-content: space-between; align-items: center; gap: 8px;">
                             <!-- Zoom Controls - Compact -->
                             <div style="display: flex; align-items: center; gap: 3px;">
                                 <span style="font-size: 8px; font-weight: 600; color: #4a5568;">🔍 <span id="zoomPercentage">100%</span></span>
                                 <button onclick="updatePlanogramZoom(0.5, false, true)" style="padding: 2px 4px; background: #10b981; color: white; border: none; border-radius: 2px; cursor: pointer; font-weight: 600; font-size: 7px;">50%</button>
                                 <button onclick="updatePlanogramZoom(1, true)" style="padding: 2px 4px; background: #6b7280; color: white; border: none; border-radius: 2px; cursor: pointer; font-weight: 600; font-size: 7px;">100%</button>
                                 <button onclick="updatePlanogramZoom(1.5, false, true)" style="padding: 2px 4px; background: #f59e0b; color: white; border: none; border-radius: 2px; cursor: pointer; font-weight: 600; font-size: 7px;">150%</button>
                             </div>
                             
                             <!-- Display Toggles - Ultra Compact -->
                             <div style="display: flex; gap: 2px; align-items: center;">
                                 <label style="display: flex; align-items: center; gap: 2px; padding: 2px 4px; background: #4facfe; color: white; border-radius: 3px; cursor: pointer; font-weight: 600; font-size: 7px; line-height: 1;">
                                     <input type="checkbox" id="toggleBrands" checked onchange="updatePlanogramDisplay('showBrands', this.checked)" style="display: none;">
                                     <span>✓</span>B
                                 </label>
                                 <label style="display: flex; align-items: center; gap: 2px; padding: 2px 4px; background: #fa709a; color: white; border-radius: 3px; cursor: pointer; font-weight: 600; font-size: 7px; line-height: 1;">
                                     <input type="checkbox" id="toggleProducts" checked onchange="updatePlanogramDisplay('showProducts', this.checked)" style="display: none;">
                                     <span>✓</span>P
                                 </label>
                                 <label style="display: flex; align-items: center; gap: 2px; padding: 2px 4px; background: #a8edea; color: #2d3748; border-radius: 3px; cursor: pointer; font-weight: 600; font-size: 7px; line-height: 1;">
                                     <input type="checkbox" id="togglePrices" checked onchange="updatePlanogramDisplay('showPrices', this.checked)" style="display: none;">
                                     <span>✓</span>£
                                 </label>
                                 <label style="display: flex; align-items: center; gap: 2px; padding: 2px 4px; background: #f7fafc; color: #4a5568; border-radius: 3px; cursor: pointer; font-weight: 600; font-size: 7px; line-height: 1;">
                                     <input type="checkbox" id="toggleConfidence" onchange="updatePlanogramDisplay('showConfidence', this.checked)" style="display: none;">
                                     <span>○</span>%
                                 </label>
                             </div>
                         </div>
                     </div>
                 `;
                 
                 controlsContainer.innerHTML = controlsHTML;
             }
             
             async function loadCompactStatsDashboard(imageId) {
                 const dashboardContainer = document.getElementById('compactStatsDashboard');
                 
                 try {
                     const response = await fetch(`/api/planogram/${imageId}/editable`);
                     if (!response.ok) {
                         dashboardContainer.innerHTML = '<div style="color: #64748b; text-align: center; padding: 20px;">No stats data available</div>';
                         return;
                     }
                     
                     const data = await response.json();
                     let totalProducts = 0;
                     let totalFacings = 0;
                     let hasStacking = false;
                     let confidenceSum = 0;
                     let confidenceCount = 0;
                     
                     // Calculate stats from shelves
                     data.planogram.shelves.forEach(shelf => {
                         Object.values(shelf.sections).forEach(section => {
                             section.forEach(slot => {
                                 if (slot.type === 'product') {
                                     totalProducts++;
                                     totalFacings += slot.data.quantity?.total_facings || 1;
                                     if (slot.data.quantity?.stack > 1) {
                                         hasStacking = true;
                                     }
                                     if (slot.data.metadata?.extraction_confidence) {
                                         confidenceSum += slot.data.metadata.extraction_confidence;
                                         confidenceCount++;
                                     }
                                 }
                             });
                         });
                     });
                     
                     const avgConfidence = confidenceCount > 0 ? confidenceSum / confidenceCount : 0.9;
                     const shelfCount = data.planogram.shelves.length;
                     
                     // Generate ultra-compact stats dashboard HTML (half height)
                     const dashboardHTML = `
                         <div style="background: white; border-radius: 6px; padding: 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); height: 100%; display: flex; align-items: center;">
                             <div style="display: flex; gap: 4px; width: 100%; justify-content: space-between;">
                                 <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 3px 6px; border-radius: 3px; text-align: center; flex: 1;">
                                     <div style="font-size: 11px; font-weight: 700; line-height: 1;">${totalProducts}</div>
                                     <div style="font-size: 7px; opacity: 0.9; line-height: 1;">Products</div>
                                 </div>
                                 <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; padding: 3px 6px; border-radius: 3px; text-align: center; flex: 1;">
                                     <div style="font-size: 11px; font-weight: 700; line-height: 1;">${shelfCount}</div>
                                     <div style="font-size: 7px; opacity: 0.9; line-height: 1;">Shelves</div>
                                 </div>
                                 <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #2d3748; padding: 3px 6px; border-radius: 3px; text-align: center; flex: 1;">
                                     <div style="font-size: 11px; font-weight: 700; line-height: 1;">${Math.round(avgConfidence * 100)}%</div>
                                     <div style="font-size: 7px; opacity: 0.8; line-height: 1;">Confidence</div>
                                 </div>
                                 <div style="background: linear-gradient(135deg, #c084fc 0%, #a855f7 100%); color: white; padding: 3px 6px; border-radius: 3px; text-align: center; flex: 1;">
                                     <div style="font-size: 11px; font-weight: 700; line-height: 1;">${totalFacings}</div>
                                     <div style="font-size: 7px; opacity: 0.9; line-height: 1;">Facings</div>
                                 </div>
                                 ${hasStacking ? `
                                     <div style="background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #2d3748; padding: 3px 6px; border-radius: 3px; text-align: center; flex: 1;">
                                         <div style="font-size: 9px; font-weight: 700; line-height: 1;">📚</div>
                                         <div style="font-size: 6px; opacity: 0.8; line-height: 1;">Stack</div>
                                     </div>
                                 ` : ''}
                             </div>
                         </div>
                     `;
                     
                     dashboardContainer.innerHTML = dashboardHTML;
                     
                 } catch (error) {
                     console.error('Error loading stats dashboard:', error);
                     dashboardContainer.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 20px;">Failed to load stats dashboard</div>';
                 }
             }
             
             async function loadExtractedProductsTable(imageId) {
                 const tableContainer = document.getElementById('extractedProductsTable');
                 
                 try {
                     const response = await fetch(`/api/planogram/${imageId}/editable`);
                     if (!response.ok) {
                         tableContainer.innerHTML = '<div style="color: #64748b; text-align: center; padding: 20px;">No extraction data available</div>';
                         return;
                     }
                     
                     const data = await response.json();
                     const products = [];
                     
                     // Extract all products from shelves
                     data.planogram.shelves.forEach(shelf => {
                         Object.values(shelf.sections).forEach(section => {
                             section.forEach(slot => {
                                 if (slot.type === 'product') {
                                     products.push({
                                         ...slot.data,
                                         shelf: shelf.shelf_number,
                                         position: slot.position
                                     });
                                 }
                             });
                         });
                     });
                     
                     // Sort by shelf and position
                     products.sort((a, b) => {
                         if (a.shelf !== b.shelf) return a.shelf - b.shelf;
                         return a.position - b.position;
                     });
                     
                     // Generate table HTML with ALL metadata
                     const tableHTML = `
                         <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);">
                             <h4 style="margin: 0 0 16px 0; color: #2d3748; font-size: 18px; font-weight: 700;">📋 Extracted Products (${products.length} items)</h4>
                             <div style="overflow-x: auto;">
                                 <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                                     <thead>
                                         <tr style="background: #f7fafc; border-bottom: 2px solid #e2e8f0;">
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 50px;">Shelf</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 40px;">Pos</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 80px;">Section</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 100px;">Brand</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 150px;">Product</th>
                                             <th style="padding: 10px 6px; text-align: center; font-weight: 600; color: #4a5568; min-width: 60px;">Price</th>
                                             <th style="padding: 10px 6px; text-align: center; font-weight: 600; color: #4a5568; min-width: 60px;">Facings</th>
                                             <th style="padding: 10px 6px; text-align: center; font-weight: 600; color: #4a5568; min-width: 60px;">Stack</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 60px;">Volume</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 60px;">Color</th>
                                             <th style="padding: 10px 6px; text-align: center; font-weight: 600; color: #4a5568; min-width: 80px;">Confidence</th>
                                             <th style="padding: 10px 6px; text-align: left; font-weight: 600; color: #4a5568; min-width: 60px;">ID</th>
                                         </tr>
                                     </thead>
                                     <tbody>
                                         ${products.map(product => {
                                             const confidence = Math.round((product.metadata?.extraction_confidence || 0.9) * 100);
                                             const confidenceColor = confidence >= 90 ? '#10b981' : confidence >= 70 ? '#f59e0b' : '#ef4444';
                                             const section = product.position?.section?.vertical || 'Unknown';
                                             const stackHeight = product.quantity?.stack || 1;
                                             const volume = product.metadata?.volume || product.volume || '-';
                                             const color = product.metadata?.color || product.color || '-';
                                             const productId = product.id || '-';
                                             
                                             return `
                                                 <tr style="border-bottom: 1px solid #e2e8f0; hover: background-color: #f8fafc;">
                                                     <td style="padding: 8px 6px; font-weight: 600; color: #2d3748;">${product.shelf}</td>
                                                     <td style="padding: 8px 6px; color: #4a5568;">${product.position}</td>
                                                     <td style="padding: 8px 6px; color: #4a5568; font-size: 12px;">${section}</td>
                                                     <td style="padding: 8px 6px; color: #4a5568; font-weight: 500;">${product.brand}</td>
                                                     <td style="padding: 8px 6px; color: #2d3748;">${product.name}</td>
                                                     <td style="padding: 8px 6px; text-align: center; font-weight: 600; color: #2b6cb0;">${product.price ? '£' + product.price.toFixed(2) : '-'}</td>
                                                     <td style="padding: 8px 6px; text-align: center; color: #4a5568;">${product.quantity?.total_facings || 1}</td>
                                                     <td style="padding: 8px 6px; text-align: center; color: ${stackHeight > 1 ? '#f59e0b' : '#4a5568'}; font-weight: ${stackHeight > 1 ? '600' : 'normal'};">${stackHeight}${stackHeight > 1 ? ' 📚' : ''}</td>
                                                     <td style="padding: 8px 6px; color: #4a5568; font-size: 12px;">${volume}</td>
                                                     <td style="padding: 8px 6px; color: #4a5568; font-size: 12px;">${color}</td>
                                                     <td style="padding: 8px 6px; text-align: center; font-weight: 600; color: ${confidenceColor};">${confidence}%</td>
                                                     <td style="padding: 8px 6px; color: #64748b; font-size: 11px; font-family: monospace;">${productId}</td>
                                                 </tr>
                                             `;
                                         }).join('')}
                                     </tbody>
                                 </table>
                             </div>
                         </div>
                     `;
                     
                     tableContainer.innerHTML = tableHTML;
                     
                 } catch (error) {
                     console.error('Error loading products table:', error);
                     tableContainer.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 20px;">Failed to load products table</div>';
                 }
             }
            
            async function loadComparisonModeData() {
                if (!selectedItemId) return;
                
                // Load comparison data for each agent
                try {
                    // This would normally fetch real comparison data
                    // For now, we'll use the existing mock data structure
                    console.log('Loading comparison data for item:', selectedItemId);
                    
                    // Load results for each agent
                    await loadAgentResults('agent1');
                    await loadAgentResults('agent2');
                    await loadAgentResults('agent3');
                    
                } catch (error) {
                    console.error('Error loading comparison data:', error);
                }
            }
            
            async function loadAdvancedModeData() {
                try {
                    // Load original image in advanced mode
                    const advancedImage = document.getElementById('advancedOriginalImage');
                    if (selectedItemId) {
                        advancedImage.src = `/api/queue/image/${selectedItemId}`;
                    } else {
                        // Show demo message when no item selected
                        advancedImage.style.display = 'none';
                        advancedImage.parentElement.innerHTML = '<div class="loading">Select an image from the sidebar or view the Demo in the Iterations tab</div>';
                    }
                    
                    // Load interactive planogram in advanced mode
                    const advancedPlanogram = document.getElementById('advancedPlanogramViewer');
                    try {
                        // Clear existing content
                        advancedPlanogram.innerHTML = '';
                        
                        // Always show demo if no item selected, otherwise show selected item
                        const imageId = selectedItemId || "demo";
                        
                        // Render interactive planogram component
                        if (window.InteractivePlanogram) {
                            ReactDOM.render(
                                React.createElement(window.InteractivePlanogram, {
                                    imageId: imageId,
                                    mode: 'advanced'
                                }),
                                advancedPlanogram
                            );
                        } else {
                            // Fallback to static SVG if React component not loaded
                            if (selectedItemId) {
                                const planogramResponse = await fetch(`/api/planogram/${selectedItemId}/render?format=svg&abstraction_level=sku_view`);
                                if (planogramResponse.ok) {
                                    const svgContent = await planogramResponse.text();
                                    advancedPlanogram.innerHTML = svgContent;
                                } else {
                                    advancedPlanogram.innerHTML = '<div class="loading">Planogram not available</div>';
                                }
                            } else {
                                advancedPlanogram.innerHTML = '<div class="loading">React component not loaded. Please refresh the page to see demo.</div>';
                            }
                        }
                    } catch (error) {
                        advancedPlanogram.innerHTML = '<div class="loading">Failed to load planogram</div>';
                    }
                    
                    // Load technical analysis data
                    await loadTechnicalAnalysis();
                    await loadOrchestratorFlow();
                    
                } catch (error) {
                    console.error('Error loading advanced mode data:', error);
                }
            }
            
            async function loadAgentResults(agentId) {
                const resultsContainer = document.getElementById(`${agentId}Results`);
                
                if (!selectedItemId) {
                    resultsContainer.innerHTML = '<div class="loading">No item selected</div>';
                    return;
                }
                
                try {
                    // Try to load real comparison results
                    const response = await fetch(`/api/queue/comparison/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Process real comparison data here
                        resultsContainer.innerHTML = '<div class="loading">Real comparison data loaded</div>';
                    } else {
                        resultsContainer.innerHTML = '<div class="loading">No comparison data available yet</div>';
                    }
                } catch (error) {
                    console.error('Failed to load agent results:', error);
                    resultsContainer.innerHTML = '<div class="loading">Failed to load comparison data</div>';
                }
            }
            
            async function loadTechnicalAnalysis() {
                if (!selectedItemId) {
                    document.getElementById('modelPerformance').innerHTML = 'No item selected';
                    document.getElementById('confidenceScores').innerHTML = 'No item selected';
                    document.getElementById('errorAnalysis').innerHTML = 'No item selected';
                    return;
                }
                
                try {
                    // Try to load real technical analysis data
                    const response = await fetch(`/api/queue/analysis/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Process real analysis data here
                        document.getElementById('modelPerformance').innerHTML = 'Real performance data loaded';
                        document.getElementById('confidenceScores').innerHTML = 'Real confidence data loaded';
                        document.getElementById('errorAnalysis').innerHTML = 'Real error analysis loaded';
                    } else {
                        document.getElementById('modelPerformance').innerHTML = 'No analysis data available yet';
                        document.getElementById('confidenceScores').innerHTML = 'No confidence data available yet';
                        document.getElementById('errorAnalysis').innerHTML = 'No error analysis available yet';
                    }
                } catch (error) {
                    console.error('Failed to load technical analysis:', error);
                    document.getElementById('modelPerformance').innerHTML = 'Failed to load performance data';
                    document.getElementById('confidenceScores').innerHTML = 'Failed to load confidence data';
                    document.getElementById('errorAnalysis').innerHTML = 'Failed to load error analysis';
                }
            }
            
            async function loadOrchestratorFlow() {
                const flowContainer = document.getElementById('orchestratorFlow');
                
                if (!selectedItemId) {
                    flowContainer.innerHTML = '<div class="loading">No item selected</div>';
                    return;
                }
                
                try {
                    // Try to load real orchestrator flow data
                    const response = await fetch(`/api/queue/flow/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Process real flow data here
                        flowContainer.innerHTML = '<div class="loading">Real orchestrator flow loaded</div>';
                    } else {
                        flowContainer.innerHTML = '<div class="loading">No flow data available yet</div>';
                    }
                } catch (error) {
                    console.error('Failed to load orchestrator flow:', error);
                    flowContainer.innerHTML = '<div class="loading">Failed to load flow data</div>';
                }
            }
            
            // Agent switching in comparison mode
            function switchAgent(agentId) {
                // Hide all agent content
                document.querySelectorAll('.agent-content').forEach(content => {
                    content.style.display = 'none';
                });
                
                // Update tab states
                document.querySelectorAll('.agent-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected agent
                document.getElementById(agentId).style.display = 'block';
                event.target.classList.add('active');
                
                currentAgent = agentId;
            }
            
            // Helper functions
            function getStatusClass(status) {
                const classes = {
                    'pending': 'status-pending',
                    'processing': 'status-processing',
                    'completed': 'status-completed',
                    'failed': 'status-failed'
                };
                return classes[status] || 'status-pending';
            }
            
            function getStatusText(status) {
                const texts = {
                    'pending': 'Pending',
                    'processing': 'Processing',
                    'completed': 'Completed',
                    'failed': 'Failed'
                };
                return texts[status] || 'Unknown';
            }
            
                         // Queue item selection
             function selectQueueItem(itemId) {
                 selectedItemId = itemId;
                 
                 // Update visual selection
                 document.querySelectorAll('.queue-item').forEach(item => {
                     item.classList.remove('selected');
                 });
                 document.querySelector(`[data-item-id="${itemId}"]`).classList.add('selected');
                 
                 // Update breadcrumb
                 updateBreadcrumb(`Extraction #${itemId} Selected`);
                 
                 // Note: Don't auto-switch to simple mode since real data isn't available
                 console.log(`📋 Selected queue item #${itemId} (real extraction data not available yet)`);
             }
            
            // System selection update
            function updateSystemSelection(itemId) {
                const checkboxes = document.querySelectorAll(`input[onchange="updateSystemSelection(${itemId})"]`);
                const selectedSystems = Array.from(checkboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);
                
                // Update the item data
                const item = queueData.find(item => item.id === itemId);
                if (item) {
                    item.selected_systems = selectedSystems;
                }
                
                console.log(`Updated systems for item ${itemId}:`, selectedSystems);
            }
            
            // Processing actions
            async function startProcessing(itemId) {
                const item = queueData.find(item => item.id === itemId);
                if (!item || item.selected_systems.length === 0) {
                    alert('Please select at least one extraction system');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/queue/process/${itemId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ systems: item.selected_systems })
                    });
                    
                    if (response.ok) {
                        // Update item status
                        item.status = 'processing';
                        renderQueue();
                        updateQueueStats();
                    } else {
                        throw new Error('Failed to start processing');
                    }
                } catch (error) {
                    console.error('Error starting processing:', error);
                    alert('Failed to start processing. Please try again.');
                }
            }
            
                         async function viewResults(itemId) {
                 // For now, always show demo since real extraction data isn't available
                 selectedItemId = 'demo';
                 switchMode('simple');
                 console.log(`📊 Viewing results for item #${itemId} (showing demo data instead)`);
             }
            
            async function reprocess(itemId) {
                if (confirm('Are you sure you want to reprocess this extraction?')) {
                    try {
                        const response = await fetch(`/api/queue/reprocess/${itemId}`, {
                            method: 'POST'
                        });
                        
                        if (response.ok) {
                            loadQueue(); // Reload queue
                        } else {
                            throw new Error('Failed to start reprocessing');
                        }
                    } catch (error) {
                        console.error('Error reprocessing:', error);
                        alert('Failed to start reprocessing. Please try again.');
                    }
                }
            }
            
            // Open debug interface for specific queue item
            function openDebugInterface(uploadId) {
                console.log(`🔍 Opening debug interface for upload ID: ${uploadId}`);
                
                // Switch to advanced mode and debugger tab
                switchMode('advanced');
                setTimeout(() => {
                    switchAdvancedTab('debugger');
                    
                    // Pre-populate the debug form with the upload ID
                    setTimeout(() => {
                        const uploadIdInput = document.getElementById('debugUploadId');
                        if (uploadIdInput) {
                            uploadIdInput.value = uploadId;
                            console.log(`✅ Pre-populated debug form with upload ID: ${uploadId}`);
                        }
                        
                        // Optionally auto-start the debug session
                        if (confirm(`Start debug session for upload ${uploadId}?`)) {
                            startDebugSession();
                        }
                    }, 100);
                }, 100);
            }
            
            // Reset individual item
            async function resetItem(itemId) {
                if (confirm('Are you sure you want to reset this item? This will clear its status and allow it to be processed again.')) {
                    try {
                        const response = await fetch(`/api/queue/reset/${itemId}`, {
                            method: 'POST'
                        });
                        
                        if (response.ok) {
                            console.log(`✅ Reset item #${itemId}`);
                            loadQueue(); // Reload queue to show updated status
                            updateQueueStats();
                        } else {
                            throw new Error('Failed to reset item');
                        }
                    } catch (error) {
                        console.error('Error resetting item:', error);
                        alert('Failed to reset item. Please try again.');
                    }
                }
            }
            
            // Reset all failed/stuck items
            async function resetAllFailedItems() {
                const failedItems = queueData.filter(item => item.status === 'failed' || item.status === 'processing');
                
                if (failedItems.length === 0) {
                    alert('No failed or stuck items to reset.');
                    return;
                }
                
                if (confirm(`Are you sure you want to reset ${failedItems.length} failed/stuck items? This will clear their status and allow them to be processed again.`)) {
                    try {
                        const response = await fetch('/api/queue/reset-all-failed', {
                            method: 'POST'
                        });
                        
                        if (response.ok) {
                            console.log(`✅ Reset ${failedItems.length} failed/stuck items`);
                            loadQueue(); // Reload queue to show updated status
                            updateQueueStats();
                        } else {
                            throw new Error('Failed to reset items');
                        }
                    } catch (error) {
                        console.error('Error resetting items:', error);
                        alert('Failed to reset items. Please try again.');
                    }
                }
            }
            
            // Process With Modal Functions
            let currentProcessItemId = null;
            let isReprocessing = false;
            
            function showProcessWithModal(itemId, reprocess = false) {
                currentProcessItemId = itemId;
                isReprocessing = reprocess;
                
                const modal = document.getElementById('processWithModal');
                const title = document.getElementById('processModalTitle');
                
                title.textContent = reprocess ? '🔄 Reprocess with AI System' : '🚀 Process with AI System';
                
                // Reset form
                document.querySelectorAll('input[name="aiSystem"]').forEach(radio => {
                    radio.checked = false;
                });
                document.querySelectorAll('.system-option').forEach(option => {
                    option.style.borderColor = '#e5e7eb';
                    option.style.background = 'white';
                    option.classList.remove('selected');
                });
                const processBtn = document.getElementById('processWithBtn');
                processBtn.disabled = true;
                processBtn.style.opacity = '0.6';
                processBtn.style.cursor = 'not-allowed';
                processBtn.style.background = '#9ca3af';
                
                // Show modal
                modal.style.display = 'flex';
                
                console.log(`${reprocess ? 'Reprocess' : 'Process'} modal opened for item ${itemId}`);
            }
            
            function closeProcessWithModal() {
                const modal = document.getElementById('processWithModal');
                modal.style.display = 'none';
                currentProcessItemId = null;
                isReprocessing = false;
            }
            
            function selectSystem(systemValue, labelElement) {
                // Update radio button
                const radio = labelElement.querySelector('input[type="radio"]');
                radio.checked = true;
                
                // Update visual selection
                document.querySelectorAll('.system-option').forEach(label => {
                    label.style.borderColor = '#e5e7eb';
                    label.style.background = 'white';
                    label.classList.remove('selected');
                });
                
                labelElement.style.borderColor = '#3b82f6';
                labelElement.style.background = '#f0f9ff';
                labelElement.classList.add('selected');
                
                // Enable process button
                const processBtn = document.getElementById('processWithBtn');
                processBtn.disabled = false;
                processBtn.style.opacity = '1';
                processBtn.style.cursor = 'pointer';
                processBtn.style.background = '#3b82f6';
                
                console.log(`Selected system: ${systemValue}`);
            }
            
            // Add keyboard support for modal
            document.addEventListener('keydown', function(e) {
                const modal = document.getElementById('processWithModal');
                if (modal.style.display === 'flex') {
                    if (e.key === 'Escape') {
                        closeProcessWithModal();
                    } else if (e.key === 'Enter') {
                        const processBtn = document.getElementById('processWithBtn');
                        if (!processBtn.disabled) {
                            processWithSelectedSystem();
                        }
                    } else if (e.key >= '1' && e.key <= '3') {
                        // Quick select with number keys
                        const systems = ['custom_consensus', 'langgraph', 'hybrid'];
                        const systemIndex = parseInt(e.key) - 1;
                        if (systemIndex < systems.length) {
                            const systemValue = systems[systemIndex];
                            const label = document.querySelector(`label[onclick*="${systemValue}"]`);
                            if (label) {
                                selectSystem(systemValue, label);
                            }
                        }
                    }
                }
            });
            
            async function processWithSelectedSystem() {
                const selectedSystem = document.querySelector('input[name="aiSystem"]:checked');
                
                if (!selectedSystem || !currentProcessItemId) {
                    alert('Please select a system and try again.');
                    return;
                }
                
                const systemValue = selectedSystem.value;
                const actionText = isReprocessing ? 'Reprocessing' : 'Processing';
                
                try {
                    // Close modal first
                    closeProcessWithModal();
                    
                    // Show processing feedback
                    const item = queueData.find(item => item.id === currentProcessItemId);
                    if (item) {
                        item.status = 'processing';
                        renderQueue();
                        updateQueueStats();
                    }
                    
                    console.log(`${actionText} item ${currentProcessItemId} with ${systemValue}`);
                    
                    // Make API call to start processing
                    const response = await fetch(`/api/queue/${isReprocessing ? 'reprocess' : 'process'}/${currentProcessItemId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            system: systemValue,
                            target_accuracy: 0.95,
                            max_iterations: 5
                        })
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        console.log(`✅ ${actionText} started successfully:`, result);
                        
                        // Show success message
                        alert(`${actionText} started with ${getSystemDisplayName(systemValue)}! You can monitor progress in the Advanced > Pipeline Debugger tab.`);
                        
                        // Reload queue to show updated status
                        setTimeout(() => {
                            loadQueue();
                        }, 1000);
                        
                    } else {
                        throw new Error(`Failed to start ${actionText.toLowerCase()}`);
                    }
                    
                } catch (error) {
                    console.error(`Error ${actionText.toLowerCase()}:`, error);
                    alert(`Failed to start ${actionText.toLowerCase()}. Please try again.`);
                    
                    // Reset item status on error
                    if (item) {
                        item.status = isReprocessing ? 'completed' : 'pending';
                        renderQueue();
                        updateQueueStats();
                    }
                }
            }
            
            function getSystemDisplayName(systemValue) {
                const names = {
                    'custom_consensus': 'Custom Consensus System',
                    'langgraph': 'LangGraph Workflow System', 
                    'hybrid': 'Hybrid Adaptive System'
                };
                return names[systemValue] || systemValue;
            }
            
            // Remove item function
            async function removeItem(itemId) {
                const item = queueData.find(item => item.id === itemId);
                const itemName = item ? `Extraction #${item.id}` : `Item #${itemId}`;
                
                if (confirm(`Are you sure you want to remove ${itemName} from the queue? This action cannot be undone.`)) {
                    try {
                        const response = await fetch(`/api/queue/remove/${itemId}`, {
                            method: 'DELETE'
                        });
                        
                        if (response.ok) {
                            console.log(`✅ Removed item #${itemId} from queue`);
                            
                            // Remove from local data
                            const index = queueData.findIndex(item => item.id === itemId);
                            if (index !== -1) {
                                queueData.splice(index, 1);
                            }
                            
                            // Update UI
                            renderQueue();
                            updateQueueStats();
                            
                            // Show success message
                            alert(`${itemName} has been removed from the queue.`);
                            
                        } else {
                            throw new Error('Failed to remove item');
                        }
                    } catch (error) {
                        console.error('Error removing item:', error);
                        alert('Failed to remove item. Please try again.');
                    }
                }
            }
            
            // Image filtering
            function filterImages() {
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                const storeFilter = document.getElementById('storeFilter').value;
                const countryFilter = document.getElementById('countryFilter').value;
                const cityFilter = document.getElementById('cityFilter').value;
                const categoryFilter = document.getElementById('categoryFilter').value;
                const statusFilter = document.getElementById('statusFilter').value;
                const dateFilter = document.getElementById('dateFilter').value;
                
                filteredImages = imageData.filter(image => {
                    // Extract metadata fields
                    const uploads = image.uploads || {};
                    const metadata = uploads.metadata || {};
                    const category = uploads.category || '';
                    const storeName = metadata.store_name || metadata.retailer || '';
                    const country = metadata.country || '';
                    const city = metadata.city || '';
                    
                    // Search filter (search in ID or store name)
                    if (searchTerm && 
                        !image.id.toString().includes(searchTerm) &&
                        !storeName.toLowerCase().includes(searchTerm)) return false;
                    
                    // Store filter
                    if (storeFilter && storeName !== storeFilter) return false;
                    
                    // Country filter
                    if (countryFilter && country !== countryFilter) return false;
                    
                    // City filter
                    if (cityFilter && city !== cityFilter) return false;
                    
                    // Category filter
                    if (categoryFilter && category !== categoryFilter) return false;
                    
                    // Status filter
                    if (statusFilter && image.status !== statusFilter) return false;
                    
                    // Date filter
                    if (dateFilter) {
                        const imageDate = new Date(image.created_at).toISOString().split('T')[0];
                        if (imageDate !== dateFilter) return false;
                    }
                    
                    return true;
                });
                
                currentPage = 1;
                renderImages();
            }
            
            // View mode switching
            function setViewMode(mode) {
                viewMode = mode;
                
                // Update button states
                document.querySelectorAll('.view-toggle button').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                renderImages();
            }
            
            // Pagination
            function updatePagination() {
                const totalPages = Math.ceil(filteredImages.length / itemsPerPage);
                const startItem = (currentPage - 1) * itemsPerPage + 1;
                const endItem = Math.min(currentPage * itemsPerPage, filteredImages.length);
                
                document.getElementById('paginationInfo').textContent = 
                    `${startItem}-${endItem} of ${filteredImages.length} images`;
                
                document.getElementById('prevBtn').disabled = currentPage === 1;
                document.getElementById('nextBtn').disabled = currentPage === totalPages;
            }
            
            function previousPage() {
                if (currentPage > 1) {
                    currentPage--;
                    renderImages();
                }
            }
            
            function nextPage() {
                const totalPages = Math.ceil(filteredImages.length / itemsPerPage);
                if (currentPage < totalPages) {
                    currentPage++;
                    renderImages();
                }
            }
            
            // Image controls
            function zoomImage(level) {
                zoomLevel = level;
                const images = document.querySelectorAll('.image-viewer img');
                images.forEach(img => {
                    img.style.transform = `scale(${level})`;
                });
            }
            
            function toggleOverlays() {
                overlaysVisible = !overlaysVisible;
                console.log('Overlays toggled:', overlaysVisible);
                // This would toggle overlay visibility in a real implementation
            }
            
            // Star rating system
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('star')) {
                    const rating = e.target.dataset.value;
                    const ratingGroup = e.target.parentElement.dataset.rating;
                    
                    // Update visual state
                    const stars = e.target.parentElement.querySelectorAll('.star');
                    stars.forEach((star, index) => {
                        if (index < rating) {
                            star.classList.add('active');
                        } else {
                            star.classList.remove('active');
                        }
                    });
                    
                    console.log(`Rating for ${ratingGroup}: ${rating} stars`);
                }
            });
            
            // Advanced Mode Tab Switching
            function switchAdvancedTab(tabName) {
                // Hide all tab contents
                document.querySelectorAll('.advanced-tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Update tab states
                document.querySelectorAll('.advanced-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab
                document.getElementById(`advanced-${tabName}`).classList.add('active');
                event.target.classList.add('active');
                
                currentAdvancedTab = tabName;
                
                                 // Load tab-specific data
                 if (tabName === 'logs') {
                     loadLogs();
                     startLogRefresh();
                 } else if (tabName === 'overview') {
                     loadErrorSummary();
                     stopLogRefresh();
                 } else if (tabName === 'iterations') {
                     loadIterations();
                     stopLogRefresh();
                 } else if (tabName === 'comparison') {
                     loadComparisonModeData();
                     stopLogRefresh();
                 } else {
                     stopLogRefresh();
                 }
            }
            
            // Log Viewer Functions
            async function loadLogs() {
                if (!selectedItemId) {
                    document.getElementById('logViewer').innerHTML = '<div class="log-loading">Please select a queue item to view logs</div>';
                    return;
                }
                
                const logViewer = document.getElementById('logViewer');
                const level = document.getElementById('logLevelFilter').value;
                const component = document.getElementById('logComponentFilter').value;
                const search = document.getElementById('logSearchInput').value;
                const hours = document.getElementById('logTimeRange').value;
                
                try {
                    const params = new URLSearchParams({
                        limit: '100',
                        hours: hours
                    });
                    
                    if (level) params.append('level', level);
                    if (component) params.append('component', component);
                    if (search) params.append('search', search);
                    
                    const response = await fetch(`/api/queue/logs/${selectedItemId}?${params}`);
                    
                    if (response.ok) {
                        const data = await response.json();
                        renderLogs(data.logs);
                    } else {
                        logViewer.innerHTML = '<div class="log-loading">Failed to load logs</div>';
                    }
                } catch (error) {
                    console.error('Failed to load logs:', error);
                    logViewer.innerHTML = '<div class="log-loading">Error loading logs</div>';
                }
            }
            
            function renderLogs(logs) {
                const logViewer = document.getElementById('logViewer');
                
                if (logs.length === 0) {
                    logViewer.innerHTML = '<div class="log-loading">No logs found for the selected filters</div>';
                    return;
                }
                
                const logEntries = logs.map(log => `
                    <div class="log-entry">
                        <span class="log-timestamp">${log.timestamp}</span>
                        <span class="log-level ${log.level}">${log.level}</span>
                        <span class="log-component">${log.component}</span>
                        <span class="log-message">${escapeHtml(log.message)}</span>
                    </div>
                `).join('');
                
                logViewer.innerHTML = logEntries;
                
                // Auto-scroll to bottom if enabled
                if (autoScrollEnabled) {
                    logViewer.scrollTop = logViewer.scrollHeight;
                }
            }
            
            function filterLogs() {
                loadLogs();
            }
            
            function toggleAutoScroll() {
                autoScrollEnabled = !autoScrollEnabled;
                const text = document.getElementById('autoScrollText');
                text.textContent = autoScrollEnabled ? '⏸️ Pause Auto-scroll' : '▶️ Resume Auto-scroll';
            }
            
            function exportLogs() {
                if (!selectedItemId) {
                    alert('Please select a queue item first');
                    return;
                }
                
                const level = document.getElementById('logLevelFilter').value;
                const component = document.getElementById('logComponentFilter').value;
                const search = document.getElementById('logSearchInput').value;
                const hours = document.getElementById('logTimeRange').value;
                
                const params = new URLSearchParams({
                    limit: '1000',
                    hours: hours
                });
                
                if (level) params.append('level', level);
                if (component) params.append('component', component);
                if (search) params.append('search', search);
                
                const url = `/api/queue/logs/${selectedItemId}?${params}`;
                window.open(url, '_blank');
            }
            
            function clearLogView() {
                document.getElementById('logViewer').innerHTML = '<div class="log-loading">Log view cleared</div>';
            }
            
            function refreshLogs() {
                loadLogs();
            }
            
            function startLogRefresh() {
                if (logRefreshInterval) clearInterval(logRefreshInterval);
                logRefreshInterval = setInterval(() => {
                    if (currentAdvancedTab === 'logs' && autoScrollEnabled) {
                        loadLogs();
                    }
                }, 5000); // Refresh every 5 seconds
            }
            
            function stopLogRefresh() {
                if (logRefreshInterval) {
                    clearInterval(logRefreshInterval);
                    logRefreshInterval = null;
                }
            }
            
            // Iteration Functions
            async function loadIterations() {
                // Always show demo option first
                const select = document.getElementById('iterationSelect');
                select.innerHTML = '<option value="">Select iteration...</option><option value="demo">📊 Demo: Interactive Planogram (18 Products)</option>';
                
                if (!selectedItemId) {
                    document.getElementById('iterationStats').textContent = 'Demo available - select "Demo" above to view interactive planogram';
                    return;
                }
                
                try {
                    const response = await fetch(`/api/iterations/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        
                        // Add real iterations after demo option
                        data.iterations.forEach(iter => {
                            const option = document.createElement('option');
                            option.value = iter.iteration;
                            option.textContent = `Iteration ${iter.iteration} - ${(iter.accuracy * 100).toFixed(1)}% accuracy (${iter.total_products} products)`;
                            select.appendChild(option);
                        });
                        
                        document.getElementById('iterationStats').textContent = `Total iterations: ${data.total_iterations} (+ Demo available)`;
                    } else if (response.status === 404) {
                        document.getElementById('iterationStats').textContent = 'No real iteration data available - Demo option available above';
                    }
                } catch (error) {
                    console.error('Failed to load iterations:', error);
                    document.getElementById('iterationStats').textContent = 'Error loading iterations - Demo option still available above';
                }
            }
            
            async function loadIterationDetails() {
                const iterationNum = document.getElementById('iterationSelect').value;
                if (!iterationNum) return;
                
                // Handle demo mode
                if (iterationNum === 'demo') {
                    // Load mock data for demo
                    loadDemoIterationData();
                    return;
                }
                
                if (!selectedItemId) return;
                
                // Load products data
                try {
                    const response = await fetch(`/api/iterations/${selectedItemId}/products/${iterationNum}`);
                    if (response.ok) {
                        const data = await response.json();
                        
                        // Display raw JSON with syntax highlighting
                        const jsonViewer = document.getElementById('iterationJSON');
                        jsonViewer.innerHTML = `<pre>${JSON.stringify(data.raw_products, null, 2)}</pre>`;
                        
                        // Display shelf breakdown
                        let shelfHTML = '';
                        const shelves = Object.keys(data.products_by_shelf).sort((a, b) => parseInt(a) - parseInt(b));
                        
                        shelves.forEach(shelf => {
                            const products = data.products_by_shelf[shelf];
                            shelfHTML += `<div style="margin-bottom: 20px;">`;
                            shelfHTML += `<h5 style="color: #2563eb;">Shelf ${shelf} (${products.length} products)</h5>`;
                            shelfHTML += '<table style="width: 100%; border-collapse: collapse;">';
                            shelfHTML += '<tr style="background: #e5e7eb;"><th>Pos</th><th>Brand</th><th>Product</th><th>Facings</th><th>Price</th><th>Confidence</th></tr>';
                            
                            products.forEach(product => {
                                const conf = (product.extraction_confidence * 100).toFixed(0);
                                const confColor = conf >= 90 ? '#10b981' : conf >= 70 ? '#f59e0b' : '#ef4444';
                                shelfHTML += `<tr style="border-bottom: 1px solid #e5e7eb;">`;
                                shelfHTML += `<td style="padding: 5px;">${product.position.position_on_shelf}</td>`;
                                shelfHTML += `<td style="padding: 5px;">${product.brand}</td>`;
                                shelfHTML += `<td style="padding: 5px;">${product.name}</td>`;
                                shelfHTML += `<td style="padding: 5px; text-align: center;">${product.position.facing_count}</td>`;
                                shelfHTML += `<td style="padding: 5px;">${product.price ? '£' + product.price.toFixed(2) : '-'}</td>`;
                                shelfHTML += `<td style="padding: 5px; color: ${confColor}; font-weight: bold;">${conf}%</td>`;
                                shelfHTML += '</tr>';
                            });
                            
                            shelfHTML += '</table></div>';
                        });
                        
                        document.getElementById('shelfBreakdown').innerHTML = shelfHTML;
                    }
                } catch (error) {
                    console.error('Failed to load iteration products:', error);
                    document.getElementById('iterationJSON').innerHTML = '<div class="error">Failed to load product data</div>';
                }
                
                // Load planogram
                try {
                    const response = await fetch(`/api/iterations/${selectedItemId}/planogram/${iterationNum}`);
                    if (response.ok) {
                        const data = await response.json();
                        document.getElementById('iterationPlanogram').innerHTML = data.svg;
                        document.getElementById('planogramAccuracy').textContent = `Accuracy: ${(data.accuracy * 100).toFixed(1)}%`;
                    } else {
                        document.getElementById('iterationPlanogram').innerHTML = '<div class="loading">No planogram available</div>';
                    }
                } catch (error) {
                    console.error('Failed to load planogram:', error);
                    document.getElementById('iterationPlanogram').innerHTML = '<div class="error">Failed to load planogram</div>';
                }
            }
            
            function copyJSON() {
                const jsonContent = document.getElementById('iterationJSON').textContent;
                navigator.clipboard.writeText(jsonContent).then(() => {
                    alert('JSON copied to clipboard!');
                });
            }
            
            async function loadDemoIterationData() {
                // Display demo data with static SVG representation
                try {
                    document.getElementById('iterationJSON').innerHTML = `
                        <div style="margin-bottom: 20px;">
                            <h3>📊 Demo: Planogram Data Structure (18 Products)</h3>
                            <p>This shows the JSON data structure that feeds the interactive React planogram.</p>
                            <p><strong>Features:</strong> 18 products across 3 shelves, stacking data, gap detection, section organization, confidence scores</p>
                        </div>
                        <pre style="background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow: auto; max-height: 400px; font-family: monospace; font-size: 12px;">{
  "shelves": {
    "1": {
      "shelf_number": 1,
      "sections": {
        "Left": [
          {
            "type": "product",
            "position": 1,
            "data": {
              "brand": "Coca-Cola",
              "name": "Coke Zero 330ml",
              "price": 1.29,
              "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
              "visual": {"confidence_color": "#22c55e"},
              "metadata": {"extraction_confidence": 0.98}
            }
          },
          {
            "type": "product", 
            "position": 2,
            "data": {
              "brand": "Coca-Cola",
              "name": "Sprite 330ml", 
              "price": 1.29,
              "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
              "visual": {"confidence_color": "#3b82f6"},
              "metadata": {"extraction_confidence": 0.92}
            }
          }
        ],
        "Center": [
          {
            "type": "product",
            "position": 4,
            "data": {
              "brand": "PepsiCo",
              "name": "Pepsi Max 330ml",
              "price": 1.19,
              "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
              "visual": {"confidence_color": "#22c55e"},
              "metadata": {"extraction_confidence": 0.95}
            }
          },
          {
            "type": "empty",
            "position": 6,
            "reason": "gap_detected"
          }
        ],
        "Right": [
          {
            "type": "product",
            "position": 7,
            "data": {
              "brand": "Red Bull",
              "name": "Energy Drink 250ml",
              "price": 1.89,
              "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
              "visual": {"confidence_color": "#22c55e"},
              "metadata": {"extraction_confidence": 0.96}
            }
          }
        ]
      }
    }
  }
}</pre>
                    `;
                    
                    // Show message directing to Simple Mode for actual planogram
                    const planogramContainer = document.getElementById('iterationPlanogram');
                    planogramContainer.innerHTML = `
                        <div style="background: #eff6ff; padding: 30px; border-radius: 8px; border: 1px solid #3b82f6; text-align: center;">
                            <h3 style="margin: 0 0 15px 0; color: #1e40af;">🎯 View Interactive Planogram</h3>
                            <p style="margin: 0 0 20px 0; color: #1e40af; font-size: 16px;">
                                To see the actual planogram visualization with all 18 products, stacking, gaps, and interactive controls:
                            </p>
                            <button onclick="switchMode('simple')" style="background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 10px;">
                                🚀 Go to Simple Mode
                            </button>
                            <p style="margin: 20px 0 0 0; color: #64748b; font-size: 14px;">
                                The iterations tab shows data structure. The actual planogram visualization is in Simple Mode.
                            </p>
                        </div>
                    `;
                    
                    document.getElementById('planogramAccuracy').textContent = 'Interactive Planogram Available in Simple Mode';
                    
                    // Add shelf breakdown table
                    document.getElementById('shelfBreakdown').innerHTML = `
                        <h4>📦 Shelf-by-Shelf Product Breakdown</h4>
                        
                        <div style="margin-bottom: 20px;">
                            <h5 style="color: #2563eb;">Shelf 1 (Bottom) - 7 products</h5>
                            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                <tr style="background: #e5e7eb; font-weight: bold;">
                                    <th style="padding: 10px; text-align: left;">Pos</th>
                                    <th style="padding: 10px; text-align: left;">Brand</th>
                                    <th style="padding: 10px; text-align: left;">Product</th>
                                    <th style="padding: 10px; text-align: center;">Facings</th>
                                    <th style="padding: 10px; text-align: left;">Price</th>
                                    <th style="padding: 10px; text-align: center;">Confidence</th>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">1</td>
                                    <td style="padding: 8px;">Coca-Cola</td>
                                    <td style="padding: 8px;">Coke Zero Sugar 330ml</td>
                                    <td style="padding: 8px; text-align: center;">3</td>
                                    <td style="padding: 8px;">£1.29</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">98%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">2</td>
                                    <td style="padding: 8px;">Coca-Cola</td>
                                    <td style="padding: 8px;">Sprite Zero 330ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£1.29</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">92%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">3</td>
                                    <td style="padding: 8px;">Coca-Cola</td>
                                    <td style="padding: 8px;">Fanta Orange 330ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£1.29</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">89%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">4</td>
                                    <td style="padding: 8px;">PepsiCo</td>
                                    <td style="padding: 8px;">Pepsi Max Cherry 330ml</td>
                                    <td style="padding: 8px; text-align: center;">3</td>
                                    <td style="padding: 8px;">£1.19</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">95%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">5</td>
                                    <td style="padding: 8px;">PepsiCo</td>
                                    <td style="padding: 8px;">7UP Free 330ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£1.19</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">86%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">7</td>
                                    <td style="padding: 8px;">Red Bull</td>
                                    <td style="padding: 8px;">Energy Drink 250ml</td>
                                    <td style="padding: 8px; text-align: center;">4 <span style="color: #f59e0b; font-size: 10px;">(STACKED 2×2)</span></td>
                                    <td style="padding: 8px;">£1.89</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">96%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">8</td>
                                    <td style="padding: 8px;">Monster</td>
                                    <td style="padding: 8px;">Energy Original 500ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£2.15</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">91%</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h5 style="color: #2563eb;">Shelf 2 (Middle) - 6 products</h5>
                            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                <tr style="background: #e5e7eb; font-weight: bold;">
                                    <th style="padding: 10px; text-align: left;">Pos</th>
                                    <th style="padding: 10px; text-align: left;">Brand</th>
                                    <th style="padding: 10px; text-align: left;">Product</th>
                                    <th style="padding: 10px; text-align: center;">Facings</th>
                                    <th style="padding: 10px; text-align: left;">Price</th>
                                    <th style="padding: 10px; text-align: center;">Confidence</th>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">1</td>
                                    <td style="padding: 8px;">Evian</td>
                                    <td style="padding: 8px;">Natural Water 500ml</td>
                                    <td style="padding: 8px; text-align: center;">6 <span style="color: #f59e0b; font-size: 10px;">(STACKED 3×2)</span></td>
                                    <td style="padding: 8px;">£0.89</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">97%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">2</td>
                                    <td style="padding: 8px;">Coca-Cola</td>
                                    <td style="padding: 8px;">Smartwater 600ml</td>
                                    <td style="padding: 8px; text-align: center;">4 <span style="color: #f59e0b; font-size: 10px;">(STACKED 2×2)</span></td>
                                    <td style="padding: 8px;">£1.49</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">88%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">3</td>
                                    <td style="padding: 8px;">Innocent</td>
                                    <td style="padding: 8px;">Orange Juice 330ml</td>
                                    <td style="padding: 8px; text-align: center;">3</td>
                                    <td style="padding: 8px;">£2.29</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">94%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">4</td>
                                    <td style="padding: 8px;">Innocent</td>
                                    <td style="padding: 8px;">Apple Juice 330ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£2.29</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">90%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">5</td>
                                    <td style="padding: 8px;">Innocent</td>
                                    <td style="padding: 8px;">Berry Smoothie 250ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£2.79</td>
                                    <td style="padding: 8px; color: #f59e0b; font-weight: bold; text-align: center;">76%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">6</td>
                                    <td style="padding: 8px;">Lipton</td>
                                    <td style="padding: 8px;">Ice Tea Lemon 500ml</td>
                                    <td style="padding: 8px; text-align: center;">6 <span style="color: #f59e0b; font-size: 10px;">(STACKED 2×3)</span></td>
                                    <td style="padding: 8px;">£1.59</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">93%</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <h5 style="color: #2563eb;">Shelf 3 (Top) - 5 products</h5>
                            <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                <tr style="background: #e5e7eb; font-weight: bold;">
                                    <th style="padding: 10px; text-align: left;">Pos</th>
                                    <th style="padding: 10px; text-align: left;">Brand</th>
                                    <th style="padding: 10px; text-align: left;">Product</th>
                                    <th style="padding: 10px; text-align: center;">Facings</th>
                                    <th style="padding: 10px; text-align: left;">Price</th>
                                    <th style="padding: 10px; text-align: center;">Confidence</th>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">1</td>
                                    <td style="padding: 8px;">Starbucks</td>
                                    <td style="padding: 8px;">Frappuccino Vanilla 250ml</td>
                                    <td style="padding: 8px; text-align: center;">3</td>
                                    <td style="padding: 8px;">£2.49</td>
                                    <td style="padding: 8px; color: #10b981; font-weight: bold; text-align: center;">96%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">2</td>
                                    <td style="padding: 8px;">Starbucks</td>
                                    <td style="padding: 8px;">Frappuccino Mocha 250ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£2.49</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">89%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">3</td>
                                    <td style="padding: 8px;">Powerade</td>
                                    <td style="padding: 8px;">ION4 Blue 500ml</td>
                                    <td style="padding: 8px; text-align: center;">4 <span style="color: #f59e0b; font-size: 10px;">(STACKED 2×2)</span></td>
                                    <td style="padding: 8px;">£1.79</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">85%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">4</td>
                                    <td style="padding: 8px;">Gatorade</td>
                                    <td style="padding: 8px;">Orange Sports Drink 500ml</td>
                                    <td style="padding: 8px; text-align: center;">4 <span style="color: #f59e0b; font-size: 10px;">(STACKED 2×2)</span></td>
                                    <td style="padding: 8px;">£1.79</td>
                                    <td style="padding: 8px; color: #f59e0b; font-weight: bold; text-align: center;">78%</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #e5e7eb;">
                                    <td style="padding: 8px;">5</td>
                                    <td style="padding: 8px;">Rockstar</td>
                                    <td style="padding: 8px;">Energy Drink 500ml</td>
                                    <td style="padding: 8px; text-align: center;">2</td>
                                    <td style="padding: 8px;">£1.99</td>
                                    <td style="padding: 8px; color: #3b82f6; font-weight: bold; text-align: center;">87%</td>
                                </tr>
                            </table>
                        </div>
                        
                        <div style="background: #f0f9ff; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6;">
                            <h5 style="color: #1e40af; margin: 0 0 10px 0;">📊 Summary Statistics</h5>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; font-size: 14px;">
                                <div><strong>Total Products:</strong> 18</div>
                                <div><strong>Total Facings:</strong> 51</div>
                                <div><strong>Stacked Products:</strong> 6</div>
                                <div><strong>Avg Confidence:</strong> 90.1%</div>
                                <div><strong>Price Range:</strong> £0.89 - £2.79</div>
                                <div><strong>Gaps Detected:</strong> 3</div>
                            </div>
                        </div>
                    `;
                        
                } catch (error) {
                    console.error('Error loading demo data:', error);
                    document.getElementById('iterationJSON').innerHTML = '<div class="error">Error loading demo data</div>';
                }
            }
            
            async function loadDemoIteration(iterationNum) {
                try {
                    // Load products data
                    const productsResponse = await fetch(`/api/iterations/12345/products/${iterationNum}`);
                    if (productsResponse.ok) {
                        const productsData = await productsResponse.json();
                        
                        // Update JSON viewer with selected iteration
                        document.getElementById('iterationJSON').innerHTML = `
                            <div style="margin-bottom: 20px;">
                                <h3>📊 Demo Iteration ${iterationNum} - Products Data</h3>
                                <button onclick="loadDemoIterationData()" style="margin-bottom: 10px; padding: 5px 10px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">← Back to Overview</button>
                            </div>
                            <pre style="background: #f8fafc; padding: 20px; border-radius: 8px; overflow: auto; max-height: 400px;">${JSON.stringify(productsData.raw_products, null, 2)}</pre>
                        `;
                    }
                    
                    // Load planogram
                    const planogramResponse = await fetch(`/api/iterations/12345/planogram/${iterationNum}`);
                    if (planogramResponse.ok) {
                        const planogramData = await planogramResponse.json();
                        document.getElementById('iterationPlanogram').innerHTML = planogramData.svg;
                        document.getElementById('planogramAccuracy').textContent = `Demo Iteration ${iterationNum} - Accuracy: ${(planogramData.accuracy * 100).toFixed(1)}%`;
                    } else {
                        document.getElementById('iterationPlanogram').innerHTML = '<div class="loading">No planogram available for this iteration</div>';
                    }
                } catch (error) {
                    console.error('Error loading demo iteration:', error);
                    document.getElementById('iterationJSON').innerHTML = '<div class="error">Error loading iteration data</div>';
                }
            }
            
            // Error Summary Functions
            async function loadErrorSummary() {
                const errorSummary = document.getElementById('errorSummary');
                
                try {
                    const response = await fetch('/api/queue/logs/errors?limit=5');
                    
                    if (response.ok) {
                        const data = await response.json();
                        renderErrorSummary(data.errors);
                    } else {
                        errorSummary.innerHTML = '<div class="log-loading">Failed to load error summary</div>';
                    }
                } catch (error) {
                    console.error('Failed to load error summary:', error);
                    errorSummary.innerHTML = '<div class="log-loading">Error loading error summary</div>';
                }
            }
            
            // Real-Time Debugging Functions
            let debugWebSocket = null;
            let currentDebugSessionId = null;
            
            // System workflow definitions
            const systemWorkflows = {
                "Custom Consensus": {
                    "stages": [
                        {"name": "structure_consensus", "display": "Structure Analysis", "models": ["GPT-4o", "Claude-3.5-Sonnet", "Gemini-2.0-Flash"], "type": "parallel"},
                        {"name": "position_consensus", "display": "Position Consensus", "models": ["GPT-4o", "Claude-3.5-Sonnet", "Gemini-2.0-Flash"], "type": "shelf_by_shelf"},
                        {"name": "quantity_consensus", "display": "Quantity Analysis", "models": ["GPT-4o", "Claude-3.5-Sonnet", "Gemini-2.0-Flash"], "type": "parallel"},
                        {"name": "detail_consensus", "display": "Detail Extraction", "models": ["GPT-4o", "Claude-3.5-Sonnet", "Gemini-2.0-Flash"], "type": "parallel"},
                        {"name": "planogram_generation", "display": "Generate Planogram", "models": ["PlanogramOrchestrator"], "type": "iteration_step"},
                        {"name": "ai_comparison", "display": "AI Compare vs Original", "models": ["ImageComparisonAgent"], "type": "iteration_step"},
                        {"name": "accuracy_calculation", "display": "Calculate Accuracy", "models": ["FeedbackManager"], "type": "iteration_step"},
                        {"name": "iteration_decision", "display": "Continue or Stop?", "models": ["MasterOrchestrator"], "type": "decision_point"}
                    ],
                    "orchestrator": "DeterministicOrchestrator",
                    "voting_mechanism": "weighted_consensus"
                },
                "LangGraph": {
                    "stages": [
                        {"name": "structure_consensus_node", "display": "Structure Node", "models": ["GPT-4o", "Claude-3.5-Sonnet"], "type": "workflow_node"},
                        {"name": "position_consensus_node", "display": "Position Node", "models": ["GPT-4o", "Claude-3.5-Sonnet"], "type": "workflow_node"},
                        {"name": "quantity_consensus_node", "display": "Quantity Node", "models": ["GPT-4o", "Claude-3.5-Sonnet"], "type": "workflow_node"},
                        {"name": "detail_consensus_node", "display": "Detail Node", "models": ["GPT-4o", "Claude-3.5-Sonnet"], "type": "workflow_node"},
                        {"name": "generate_planogram_node", "display": "Planogram Node", "models": ["Workflow"], "type": "workflow_node"},
                        {"name": "validate_end_to_end_node", "display": "Validation Node", "models": ["Workflow"], "type": "workflow_node"},
                        {"name": "smart_retry_node", "display": "Smart Retry", "models": ["Workflow"], "type": "conditional"}
                    ],
                    "orchestrator": "LangGraph StateGraph",
                    "voting_mechanism": "workflow_state_management"
                },
                "Hybrid": {
                    "stages": [
                        {"name": "adaptive_structure", "display": "Adaptive Structure", "models": ["Dynamic Selection"], "type": "adaptive"},
                        {"name": "multi_model_positions", "display": "Multi-Model Positions", "models": ["Best Available"], "type": "adaptive"},
                        {"name": "consensus_validation", "display": "Consensus Validation", "models": ["Ensemble"], "type": "ensemble"},
                        {"name": "quality_optimization", "display": "Quality Optimization", "models": ["Feedback Loop"], "type": "iterative"}
                    ],
                    "orchestrator": "AdaptiveOrchestrator",
                    "voting_mechanism": "dynamic_consensus"
                }
            };

            function displaySystemWorkflow(systemName) {
                const workflow = systemWorkflows[systemName];
                
                // Update system display
                document.getElementById('currentSystem').textContent = systemName;
                document.getElementById('orchestratorType').textContent = workflow.orchestrator;
                document.getElementById('votingMechanism').textContent = workflow.voting_mechanism;
                
                // Count active models
                const allModels = new Set();
                workflow.stages.forEach(stage => {
                    stage.models.forEach(model => allModels.add(model));
                });
                document.getElementById('activeModels').textContent = allModels.size;
                
                // Show REAL Master Orchestrator iteration cycle steps
                displayMasterOrchestratorSteps(systemName);
                
                console.log(`📊 Displaying workflow for ${systemName} with real Master Orchestrator steps`);
            }
            
            function displayMasterOrchestratorSteps(systemName) {
                const stepsContainer = document.getElementById('masterOrchestratorSteps');
                stepsContainer.innerHTML = '';
                
                // REAL Master Orchestrator iteration cycle steps (from src/orchestrator/master_orchestrator.py)
                const masterSteps = [
                    {
                        id: 'extract_data',
                        name: `Step 1: Extract with ${systemName}`,
                        description: 'ExtractionOrchestrator.extract_with_cumulative_learning() - Uses previous attempts and focus areas',
                        status: 'pending',
                        component: 'ExtractionOrchestrator'
                    },
                    {
                        id: 'generate_planogram',
                        name: 'Step 2: Generate Planogram',
                        description: 'PlanogramOrchestrator.generate_for_agent_iteration() - Creates visual planogram from extraction JSON',
                        status: 'pending',
                        component: 'PlanogramOrchestrator'
                    },
                    {
                        id: 'ai_compare',
                        name: 'Step 3: AI Comparison Analysis',
                        description: 'ImageComparisonAgent.compare_image_vs_planogram() - Compares original image vs generated planogram',
                        status: 'pending',
                        component: 'ImageComparisonAgent'
                    },
                    {
                        id: 'calculate_accuracy',
                        name: 'Step 4: Calculate Accuracy',
                        description: 'FeedbackManager.analyze_accuracy_with_failure_areas() - Analyzes comparison and identifies failure areas',
                        status: 'pending',
                        component: 'CumulativeFeedbackManager'
                    },
                    {
                        id: 'iteration_decision',
                        name: 'Step 5: Iteration Decision',
                        description: 'MasterOrchestrator checks: if accuracy >= target_accuracy, STOP; else prepare next iteration with focus areas',
                        status: 'pending',
                        component: 'MasterOrchestrator'
                    }
                ];
                
                masterSteps.forEach((step, index) => {
                    const stepDiv = document.createElement('div');
                    stepDiv.className = 'master-step';
                    stepDiv.setAttribute('data-step', step.id);
                    stepDiv.style.cssText = `
                        display: flex; 
                        align-items: center; 
                        padding: 8px 12px; 
                        background: #f8fafc; 
                        border-radius: 6px; 
                        border-left: 4px solid #e5e7eb;
                        transition: all 0.3s ease;
                    `;
                    
                    stepDiv.innerHTML = `
                        <div style="width: 24px; height: 24px; border-radius: 50%; background: #e5e7eb; color: #6b7280; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; margin-right: 12px;">
                            ${index + 1}
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; color: #374151; font-size: 14px;">${step.name}</div>
                            <div style="font-size: 12px; color: #6b7280; margin-top: 2px;">${step.description}</div>
                            <div style="font-size: 11px; color: #3b82f6; margin-top: 4px; font-weight: 500;">🔧 ${step.component}</div>
                        </div>
                        <div style="font-size: 12px; color: #6b7280; font-weight: 600;">⏸ Pending</div>
                    `;
                    
                    stepsContainer.appendChild(stepDiv);
                });
            }

            // Initialize workflow display on page load
            document.addEventListener('DOMContentLoaded', function() {
                displaySystemWorkflow('Custom Consensus');
            });
            
            async function startDebugSession() {
                const uploadId = document.getElementById('debugUploadId').value.trim();
                
                if (!uploadId) {
                    alert('Please enter an upload ID to monitor');
                    return;
                }
                
                try {
                    // Start monitoring session - system will be detected automatically
                    const response = await fetch('/api/debug/start-session', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            upload_id: uploadId,
                            system_name: 'Custom Consensus'  // Default system for monitoring
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`Failed to start debug session: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    currentDebugSessionId = data.session_id;
                    
                    // Update UI
                    document.getElementById('debugSessionId').textContent = currentDebugSessionId;
                    document.getElementById('debugStatus').textContent = 'Starting...';
                    document.getElementById('debugCurrentStage').textContent = 'Detecting system...';
                    document.getElementById('debugSessionInfo').style.display = 'block';
                    document.getElementById('startDebugBtn').disabled = true;
                    document.getElementById('startDebugBtn').textContent = '🔄 Monitoring...';
                    
                    // Update system display based on actual system being used
                    if (data.system) {
                        displaySystemWorkflow(data.system);
                        addLogMessage(`Monitoring ${data.system} extraction system`, 'info');
                    }
                    
                    // Show pipeline status panels
                    document.getElementById('pipelineStatus').style.display = 'block';
                    document.getElementById('modelComparison').style.display = 'block';
                    document.getElementById('livePromptMonitoring').style.display = 'block';
                    document.getElementById('realTimeLogs').style.display = 'block';
                    
                    // Connect WebSocket for real-time updates
                    connectDebugWebSocket(currentDebugSessionId);
                    
                    console.log(`✅ Started monitoring session: ${currentDebugSessionId} for system: ${data.system || 'Unknown'}`);
                    
                } catch (error) {
                    console.error('Failed to start monitoring session:', error);
                    alert(`Failed to start monitoring session: ${error.message}`);
                }
            }
            
            function connectDebugWebSocket(sessionId) {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/debug/ws/${sessionId}`;
                
                debugWebSocket = new WebSocket(wsUrl);
                
                debugWebSocket.onopen = function() {
                    console.log('✅ Monitoring WebSocket connected');
                    addLogMessage('Connected to monitoring session', 'info');
                };
                
                debugWebSocket.onmessage = function(event) {
                    const update = JSON.parse(event.data);
                    handleDebugUpdate(update);
                };
                
                debugWebSocket.onclose = function() {
                    console.log('🔌 Monitoring WebSocket disconnected');
                    addLogMessage('Disconnected from monitoring session', 'warning');
                };
                
                debugWebSocket.onerror = function(error) {
                    console.error('❌ Monitoring WebSocket error:', error);
                    addLogMessage('WebSocket connection error', 'error');
                };
            }
            
            function handleDebugUpdate(update) {
                console.log('📡 Debug update received:', update);
                
                switch (update.type) {
                    case 'initial_status':
                        document.getElementById('debugStatus').textContent = update.status;
                        document.getElementById('debugCurrentStage').textContent = update.current_stage;
                        break;
                        
                    case 'stage_update':
                        updatePipelineStage(update.stage, update.status);
                        document.getElementById('debugCurrentStage').textContent = update.stage;
                        document.getElementById('pipelineProgressText').textContent = update.message || `${update.stage} - ${update.status}`;
                        addLogMessage(`Stage ${update.stage}: ${update.status}`, 'info');
                        break;
                        
                    case 'prompt_used':
                        // Show live prompts being used by each model
                        displayLivePrompt(update.model, update.step, update.prompt_template, update.prompt_content, update.agent_id);
                        addLogMessage(`🤖 ${update.model} using prompt: ${update.prompt_template} for ${update.step}`, 'info');
                        break;
                        
                    case 'iteration_start':
                        updateIterationStart(update);
                        addLogMessage(`🔄 Starting Iteration ${update.iteration} - Target: ${update.target_accuracy}%`, 'info');
                        break;
                        
                    case 'extract_data_start':
                        updateMasterStep('extract_data', 'processing', `Extracting with ${update.system}`);
                        addLogMessage(`🔍 Step 1: Extracting data using ${update.system}`, 'info');
                        break;
                        
                    case 'extract_data_complete':
                        updateMasterStep('extract_data', 'completed', `Found ${update.products} products`);
                        addLogMessage(`✅ Step 1 Complete: ${update.products} products extracted`, 'success');
                        break;
                        
                    case 'planogram_generation_start':
                        updateMasterStep('generate_planogram', 'processing', 'Creating visual planogram');
                        addLogMessage(`📊 Step 2: Generating planogram from extraction JSON`, 'info');
                        break;
                        
                    case 'planogram_generated':
                        updateMasterStep('generate_planogram', 'completed', `Planogram created`);
                        addLogMessage(`✅ Step 2 Complete: Planogram generated for ${update.products} products`, 'success');
                        break;
                        
                    case 'ai_comparison_start':
                        updateMasterStep('ai_compare', 'processing', 'Comparing vs original image');
                        addLogMessage(`🔍 Step 3: AI comparing planogram vs original image`, 'info');
                        break;
                        
                    case 'ai_comparison_complete':
                        updateMasterStep('ai_compare', 'completed', 'Comparison analysis done');
                        addLogMessage(`✅ Step 3 Complete: AI comparison analysis finished`, 'success');
                        break;
                        
                    case 'accuracy_calculation_start':
                        updateMasterStep('calculate_accuracy', 'processing', 'Analyzing accuracy');
                        addLogMessage(`📊 Step 4: Calculating accuracy from comparison`, 'info');
                        break;
                        
                    case 'accuracy_calculated':
                        updateMasterStep('calculate_accuracy', 'completed', `${update.accuracy}% accuracy`);
                        updateMasterStep('iteration_decision', 'processing', 'Deciding next action');
                        
                        const accuracyColor = update.accuracy >= 95 ? 'success' : update.accuracy >= 80 ? 'warning' : 'error';
                        addLogMessage(`🎯 Step 4 Complete: ${update.accuracy}% accuracy (Target: ${update.target}%)`, accuracyColor);
                        
                        // Update current accuracy display
                        document.getElementById('currentAccuracy').textContent = `${update.accuracy}%`;
                        
                        if (update.accuracy >= update.target) {
                            updateMasterStep('iteration_decision', 'completed', '✅ Target achieved - STOP');
                            updateIterationComplete(update.iteration, update.accuracy, true);
                            addLogMessage(`✅ Step 5 Complete: Target accuracy achieved! Stopping iterations.`, 'success');
                        } else {
                            updateMasterStep('iteration_decision', 'completed', '⏭️ Continue to next iteration');
                            addLogMessage(`⏭️ Step 5 Complete: Accuracy below target, continuing to next iteration...`, 'info');
                            // Reset steps for next iteration
                            setTimeout(() => resetMasterStepsForNextIteration(), 1000);
                        }
                        break;
                        
                    case 'iteration_complete':
                        updateIterationInfo(update);
                        addLogMessage(`Iteration ${update.iteration} complete - Accuracy: ${(update.accuracy * 100).toFixed(1)}%, Products: ${update.products_found}, Cost: £${update.cost.toFixed(2)}`, 'success');
                        break;
                        
                    case 'extraction_complete':
                        document.getElementById('debugStatus').textContent = 'Completed';
                        document.getElementById('startDebugBtn').disabled = false;
                        document.getElementById('startDebugBtn').textContent = '🔍 Monitor Extraction';
                        addLogMessage(`Extraction complete! Final accuracy: ${(update.final_accuracy * 100).toFixed(1)}%, Total cost: £${update.total_cost.toFixed(2)}`, 'success');
                        break;
                        
                    case 'extraction_failed':
                        document.getElementById('debugStatus').textContent = 'Failed';
                        document.getElementById('startDebugBtn').disabled = false;
                        document.getElementById('startDebugBtn').textContent = '🔍 Monitor Extraction';
                        addLogMessage(`Extraction failed: ${update.error}`, 'error');
                        break;
                }
            }
            
            function updatePipelineStage(stage, status) {
                const stageElement = document.querySelector(`[data-stage="${stage}"]`);
                if (stageElement) {
                    stageElement.classList.remove('pending', 'processing', 'completed', 'failed');
                    
                    if (status === 'processing') {
                        stageElement.style.background = '#f59e0b';
                        stageElement.style.color = 'white';
                        stageElement.innerHTML = `${stage.charAt(0).toUpperCase() + stage.slice(1)} ⏳`;
                    } else if (status === 'completed') {
                        stageElement.style.background = '#10b981';
                        stageElement.style.color = 'white';
                        stageElement.innerHTML = `${stage.charAt(0).toUpperCase() + stage.slice(1)} ✅`;
                    } else if (status === 'failed') {
                        stageElement.style.background = '#ef4444';
                        stageElement.style.color = 'white';
                        stageElement.innerHTML = `${stage.charAt(0).toUpperCase() + stage.slice(1)} ❌`;
                    }
                }
            }
            
            function updateIterationInfo(update) {
                document.getElementById('currentIteration').textContent = update.iteration;
                document.getElementById('productsFound').textContent = update.products_found;
                document.getElementById('currentAccuracy').textContent = `${(update.accuracy * 100).toFixed(1)}%`;
                document.getElementById('totalCost').textContent = `£${update.total_cost.toFixed(2)}`;
            }
            
            function addLogMessage(message, level = 'info') {
                const logContainer = document.getElementById('logContainer');
                const timestamp = new Date().toLocaleTimeString();
                
                let color = '#e2e8f0';
                let icon = 'ℹ️';
                
                switch (level) {
                    case 'success':
                        color = '#10b981';
                        icon = '✅';
                        break;
                    case 'warning':
                        color = '#f59e0b';
                        icon = '⚠️';
                        break;
                    case 'error':
                        color = '#ef4444';
                        icon = '❌';
                        break;
                }
                
                const logEntry = document.createElement('div');
                logEntry.style.color = color;
                logEntry.style.marginBottom = '5px';
                logEntry.innerHTML = `<span style="color: #94a3b8;">[${timestamp}]</span> ${icon} ${message}`;
                
                logContainer.appendChild(logEntry);
                logContainer.scrollTop = logContainer.scrollHeight;
            }
            
            function stopDebugSession() {
                if (currentDebugSessionId) {
                    // Close WebSocket
                    if (debugWebSocket) {
                        debugWebSocket.close();
                        debugWebSocket = null;
                    }
                    
                    // Clean up session
                    fetch(`/api/debug/session/${currentDebugSessionId}`, {
                        method: 'DELETE'
                    }).catch(console.error);
                    
                    // Reset UI
                    document.getElementById('debugSessionInfo').style.display = 'none';
                    document.getElementById('pipelineStatus').style.display = 'none';
                    document.getElementById('modelComparison').style.display = 'none';
                    document.getElementById('livePromptMonitoring').style.display = 'none';
                    document.getElementById('realTimeLogs').style.display = 'none';
                    document.getElementById('startDebugBtn').disabled = false;
                    document.getElementById('startDebugBtn').textContent = '🔍 Monitor Extraction';
                    
                    currentDebugSessionId = null;
                    console.log('🛑 Monitoring session stopped');
                }
            }
            
            async function loadActiveSessions() {
                try {
                    const response = await fetch('/api/debug/active-sessions');
                    if (response.ok) {
                        const data = await response.json();
                        renderActiveSessions(data.active_sessions);
                    }
                } catch (error) {
                    console.error('Failed to load active sessions:', error);
                }
            }
            
            function renderActiveSessions(sessions) {
                const container = document.getElementById('activeSessionsList');
                
                if (sessions.length === 0) {
                    container.innerHTML = '<div style="color: #6b7280; text-align: center; padding: 20px;">No active debug sessions</div>';
                    return;
                }
                
                const sessionItems = sessions.map(session => `
                    <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>Session:</strong> ${session.session_id.substring(0, 8)}...<br>
                                <strong>Upload ID:</strong> ${session.upload_id}<br>
                                <strong>Status:</strong> ${session.status}<br>
                                <strong>Stage:</strong> ${session.current_stage}<br>
                                <strong>Iterations:</strong> ${session.iterations}
                            </div>
                            <div>
                                <button onclick="connectToSession('${session.session_id}')" style="background: #3b82f6; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; margin-bottom: 5px;">Connect</button><br>
                                <button onclick="stopSession('${session.session_id}')" style="background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer;">Stop</button>
                            </div>
                        </div>
                    </div>
                `).join('');
                
                container.innerHTML = sessionItems;
            }
            
            function connectToSession(sessionId) {
                if (currentDebugSessionId) {
                    stopDebugSession();
                }
                
                currentDebugSessionId = sessionId;
                document.getElementById('debugSessionId').textContent = sessionId;
                document.getElementById('debugSessionInfo').style.display = 'block';
                document.getElementById('pipelineStatus').style.display = 'block';
                document.getElementById('modelComparison').style.display = 'block';
                document.getElementById('livePromptMonitoring').style.display = 'block';
                document.getElementById('realTimeLogs').style.display = 'block';
                
                connectDebugWebSocket(sessionId);
                
                // Load current session status
                fetch(`/api/debug/session/${sessionId}/status`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('debugStatus').textContent = data.status;
                        document.getElementById('debugCurrentStage').textContent = data.current_stage;
                    })
                    .catch(console.error);
            }
            
            function stopSession(sessionId) {
                fetch(`/api/debug/session/${sessionId}`, {
                    method: 'DELETE'
                }).then(() => {
                    loadActiveSessions();
                    if (currentDebugSessionId === sessionId) {
                        stopDebugSession();
                    }
                }).catch(console.error);
            }
            
            // Real-time Master Orchestrator step updates
            function updateIterationStart(update) {
                document.getElementById('currentIterationNumber').textContent = update.iteration;
                document.getElementById('targetAccuracy').textContent = `${update.target_accuracy}%`;
                document.getElementById('iterationStatus').textContent = '🔄';
                document.getElementById('iterationStatusText').textContent = 'Running';
                document.getElementById('iterationProgressText').textContent = `Iteration ${update.iteration} - Extracting Data`;
                
                // Reset all steps to pending for new iteration
                resetMasterStepsForNextIteration();
            }
            
            function updateMasterStep(stepId, status, statusText) {
                const stepElement = document.querySelector(`[data-step="${stepId}"]`);
                if (!stepElement) return;
                
                const circle = stepElement.querySelector('div:first-child');
                const statusElement = stepElement.querySelector('div:last-child');
                
                if (status === 'processing') {
                    stepElement.style.borderLeftColor = '#f59e0b';
                    stepElement.style.background = '#fffbeb';
                    circle.style.background = '#f59e0b';
                    circle.style.color = 'white';
                    statusElement.innerHTML = '⏳ Processing';
                    statusElement.style.color = '#f59e0b';
                } else if (status === 'completed') {
                    stepElement.style.borderLeftColor = '#10b981';
                    stepElement.style.background = '#f0fdf4';
                    circle.style.background = '#10b981';
                    circle.style.color = 'white';
                    statusElement.innerHTML = '✅ Complete';
                    statusElement.style.color = '#10b981';
                } else if (status === 'failed') {
                    stepElement.style.borderLeftColor = '#ef4444';
                    stepElement.style.background = '#fef2f2';
                    circle.style.background = '#ef4444';
                    circle.style.color = 'white';
                    statusElement.innerHTML = '❌ Failed';
                    statusElement.style.color = '#ef4444';
                }
                
                // Update status text if provided
                if (statusText) {
                    const descriptionElement = stepElement.querySelector('div:nth-child(2) div:last-child');
                    if (descriptionElement) {
                        descriptionElement.textContent = statusText;
                    }
                }
            }
            
            function updateIterationComplete(iteration, accuracy, targetAchieved) {
                document.getElementById('currentAccuracy').textContent = `${accuracy}%`;
                
                if (targetAchieved) {
                    document.getElementById('iterationStatus').textContent = '✅';
                    document.getElementById('iterationStatusText').textContent = 'Complete';
                    document.getElementById('iterationProgressText').textContent = `Iteration ${iteration} - Target Achieved!`;
                } else {
                    document.getElementById('iterationStatus').textContent = '⏭️';
                    document.getElementById('iterationStatusText').textContent = 'Continuing';
                    document.getElementById('iterationProgressText').textContent = `Iteration ${iteration} - Preparing Next`;
                }
            }
            
            function resetMasterStepsForNextIteration() {
                const steps = ['extract_data', 'generate_planogram', 'ai_compare', 'calculate_accuracy', 'iteration_decision'];
                
                steps.forEach(stepId => {
                    const stepElement = document.querySelector(`[data-step="${stepId}"]`);
                    if (!stepElement) return;
                    
                    const circle = stepElement.querySelector('div:first-child');
                    const statusElement = stepElement.querySelector('div:last-child');
                    
                    // Reset to pending state
                    stepElement.style.borderLeftColor = '#e5e7eb';
                    stepElement.style.background = '#f8fafc';
                    circle.style.background = '#e5e7eb';
                    circle.style.color = '#6b7280';
                    statusElement.innerHTML = '⏸ Pending';
                    statusElement.style.color = '#6b7280';
                });
            }
            
            // Live prompt monitoring functions
            function displayLivePrompt(model, step, promptTemplate, promptContent, agentId) {
                const promptContainer = document.getElementById('promptContainer');
                
                // Clear the waiting message if it's the first prompt
                if (promptContainer.innerHTML.includes('Waiting for extraction')) {
                    promptContainer.innerHTML = '';
                }
                
                // Create unique ID for this prompt
                const promptId = `prompt-${model}-${step}-${agentId || 'main'}`;
                
                // Remove existing prompt from same model/step if it exists
                const existingPrompt = document.getElementById(promptId);
                if (existingPrompt) {
                    existingPrompt.remove();
                }
                
                // Get model color
                const modelColors = {
                    'GPT-4o': '#10b981',
                    'Claude-3.5-Sonnet': '#3b82f6', 
                    'Gemini-2.0-Flash': '#f59e0b',
                    'GPT-4o-Latest': '#10b981',
                    'Claude-3-Sonnet': '#3b82f6'
                };
                
                const modelColor = modelColors[model] || '#6b7280';
                
                // Create prompt display element
                const promptElement = document.createElement('div');
                promptElement.id = promptId;
                promptElement.style.cssText = `
                    border: 2px solid ${modelColor};
                    border-radius: 8px;
                    background: white;
                    overflow: hidden;
                    margin-bottom: 10px;
                `;
                
                // Truncate prompt content for display
                const truncatedContent = promptContent.length > 300 
                    ? promptContent.substring(0, 300) + '...' 
                    : promptContent;
                
                promptElement.innerHTML = `
                    <div style="background: ${modelColor}; color: white; padding: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>🤖 ${model}</strong> • Step: ${step} • Template: ${promptTemplate}
                            ${agentId ? ` • Agent: ${agentId}` : ''}
                        </div>
                        <div style="font-size: 12px; opacity: 0.9;">
                            ${new Date().toLocaleTimeString()}
                        </div>
                    </div>
                    <div style="padding: 15px;">
                        <div style="background: #f8fafc; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; line-height: 1.4; color: #374151; max-height: 200px; overflow-y: auto;">
                            ${escapeHtml(truncatedContent)}
                        </div>
                        <div style="margin-top: 10px; display: flex; gap: 10px;">
                            <button onclick="expandPrompt('${promptId}')" style="background: #e5e7eb; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                📄 View Full Prompt
                            </button>
                            <button onclick="copyPrompt('${promptId}')" style="background: #e5e7eb; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">
                                📋 Copy
                            </button>
                        </div>
                    </div>
                `;
                
                // Store full content for later access
                promptElement.dataset.fullContent = promptContent;
                
                // Add to container (newest at top)
                promptContainer.insertBefore(promptElement, promptContainer.firstChild);
                
                // Limit to last 10 prompts to avoid memory issues
                const allPrompts = promptContainer.children;
                if (allPrompts.length > 10) {
                    for (let i = 10; i < allPrompts.length; i++) {
                        allPrompts[i].remove();
                    }
                }
            }
            
            function expandPrompt(promptId) {
                const promptElement = document.getElementById(promptId);
                if (!promptElement) return;
                
                const fullContent = promptElement.dataset.fullContent;
                
                // Create modal to show full prompt
                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                `;
                
                modal.innerHTML = `
                    <div style="background: white; border-radius: 12px; max-width: 800px; width: 100%; max-height: 80vh; overflow: hidden; display: flex; flex-direction: column;">
                        <div style="padding: 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                            <h3 style="margin: 0; color: #1f2937;">Full Prompt Content</h3>
                            <button onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="background: #ef4444; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer;">✕ Close</button>
                        </div>
                        <div style="padding: 20px; overflow-y: auto; flex: 1;">
                            <pre style="background: #f8fafc; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 13px; line-height: 1.4; color: #374151; white-space: pre-wrap; margin: 0;">${escapeHtml(fullContent)}</pre>
                        </div>
                        <div style="padding: 20px; border-top: 1px solid #e5e7eb; display: flex; gap: 10px;">
                            <button onclick="copyToClipboard('${escapeHtml(fullContent).replace(/'/g, "\\'")}'); this.textContent='✅ Copied!'; setTimeout(() => this.textContent='📋 Copy Full Prompt', 2000)" style="background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">📋 Copy Full Prompt</button>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                
                // Close on background click
                modal.addEventListener('click', function(e) {
                    if (e.target === modal) {
                        modal.remove();
                    }
                });
            }
            
            function copyPrompt(promptId) {
                const promptElement = document.getElementById(promptId);
                if (!promptElement) return;
                
                const fullContent = promptElement.dataset.fullContent;
                copyToClipboard(fullContent);
                
                // Show feedback
                const button = promptElement.querySelector('button[onclick*="copyPrompt"]');
                if (button) {
                    const originalText = button.textContent;
                    button.textContent = '✅ Copied!';
                    setTimeout(() => {
                        button.textContent = originalText;
                    }, 2000);
                }
            }
            
            function copyToClipboard(text) {
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(text);
                } else {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                }
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            function renderErrorSummary(errors) {
                const errorSummary = document.getElementById('errorSummary');
                
                if (errors.length === 0) {
                    errorSummary.innerHTML = '<div class="log-loading">✅ No recent errors found</div>';
                    return;
                }
                
                const errorItems = errors.map(error => `
                    <div class="error-item ${error.level.toLowerCase()}" onclick="jumpToLogContext('${error.timestamp}', '${error.component}')">
                        <div class="error-timestamp">${error.timestamp}</div>
                        <div class="error-component">${error.component}</div>
                        <div class="error-message">${escapeHtml(error.message)}</div>
                    </div>
                `).join('');
                
                errorSummary.innerHTML = errorItems;
            }
            
            function jumpToLogContext(timestamp, component) {
                // Switch to logs tab
                switchAdvancedTab('logs');
                
                // Set filters to show context around this error
                document.getElementById('logComponentFilter').value = component;
                document.getElementById('logSearchInput').value = '';
                
                // Load logs with the specific context
                setTimeout(() => {
                    loadLogs();
                }, 100);
            }
            
            // Fallback planogram display (pure HTML/CSS)
            function showFallbackPlanogram(container) {
                console.log('Showing fallback HTML planogram...');
                container.innerHTML = `
                    <div class="interactive-planogram">
                        <!-- Planogram Header -->
                        <div class="planogram-header">
                            <div class="planogram-stats">
                                <span class="stat">📦 18 Products</span>
                                <span class="stat">📚 3 Shelves</span>
                                <span class="stat">🎯 90% Confidence</span>
                                <span class="stat stacking-indicator">📚 Stacking Detected</span>
                            </div>
                        </div>

                        <!-- Shelf Container -->
                        <div class="shelves-container">
                            <!-- Shelf 3 (Top) -->
                            <div class="shelf-component">
                                <div class="shelf-header">
                                    <h3>Shelf 3</h3>
                                    <div class="shelf-stats">
                                        <span class="products-count">5 products</span>
                                        <span class="gaps-count">1 gaps</span>
                                    </div>
                                </div>
                                <div class="shelf-content">
                                    <div class="shelf-section section-left">
                                        <div class="section-label">Left</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-1">
                                                <div class="product-slot full-height" style="background-color: #22c55e;">
                                                    <div class="product-content">
                                                        <div class="product-name">Starbucks Frappuccino Vanilla 250ml</div>
                                                        <div class="product-price">£2.49</div>
                                                        <div class="product-facings">3 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-2">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">Starbucks Frappuccino Mocha 250ml</div>
                                                        <div class="product-price">£2.49</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="shelf-section section-center">
                                        <div class="section-label">Center</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-3">
                                                <div class="product-slot stacked">
                                                    <div class="stack-row stack-top" style="background-color: #3b82f6;">
                                                        <div class="product-content">
                                                            <div class="product-name">Powerade ION4 Blue</div>
                                                            <div class="stacking-indicator">Stack 1/2</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row stack-bottom" style="background-color: #3b82f6;">
                                                        <div class="product-content">
                                                            <div class="product-name">Powerade ION4 Blue</div>
                                                            <div class="stacking-indicator">Stack 2/2</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-4">
                                                <div class="product-slot stacked">
                                                    <div class="stack-row stack-top" style="background-color: #f59e0b;">
                                                        <div class="product-content">
                                                            <div class="product-name">Gatorade Orange</div>
                                                            <div class="stacking-indicator">Stack 1/2</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row stack-bottom" style="background-color: #f59e0b;">
                                                        <div class="product-content">
                                                            <div class="product-name">Gatorade Orange</div>
                                                            <div class="stacking-indicator">Stack 2/2</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="shelf-section section-right">
                                        <div class="section-label">Right</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-5">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">Rockstar Energy 500ml</div>
                                                        <div class="product-price">£1.99</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-6">
                                                <div class="empty-slot">
                                                    <div class="empty-content">
                                                        <span class="empty-icon">📭</span>
                                                        <span class="empty-text">Empty</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Shelf 2 (Middle) -->
                            <div class="shelf-component">
                                <div class="shelf-header">
                                    <h3>Shelf 2</h3>
                                    <div class="shelf-stats">
                                        <span class="products-count">6 products</span>
                                        <span class="gaps-count">1 gaps</span>
                                    </div>
                                </div>
                                <div class="shelf-content">
                                    <div class="shelf-section section-left">
                                        <div class="section-label">Left</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-1">
                                                <div class="product-slot stacked">
                                                    <div class="stack-row" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Evian Water</div>
                                                            <div class="stacking-indicator">Stack 1/3</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Evian Water</div>
                                                            <div class="stacking-indicator">Stack 2/3</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Evian Water</div>
                                                            <div class="stacking-indicator">Stack 3/3</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-2">
                                                <div class="product-slot stacked">
                                                    <div class="stack-row stack-top" style="background-color: #3b82f6;">
                                                        <div class="product-content">
                                                            <div class="product-name">Smartwater</div>
                                                            <div class="stacking-indicator">Stack 1/2</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row stack-bottom" style="background-color: #3b82f6;">
                                                        <div class="product-content">
                                                            <div class="product-name">Smartwater</div>
                                                            <div class="stacking-indicator">Stack 2/2</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="shelf-section section-center">
                                        <div class="section-label">Center</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-3">
                                                <div class="product-slot full-height" style="background-color: #22c55e;">
                                                    <div class="product-content">
                                                        <div class="product-name">Innocent Orange Juice 330ml</div>
                                                        <div class="product-price">£2.29</div>
                                                        <div class="product-facings">3 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-4">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">Innocent Apple Juice 330ml</div>
                                                        <div class="product-price">£2.29</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-5">
                                                <div class="product-slot full-height" style="background-color: #f59e0b;">
                                                    <div class="product-content">
                                                        <div class="product-name">Innocent Berry Smoothie</div>
                                                        <div class="product-price">£2.79</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="shelf-section section-right">
                                        <div class="section-label">Right</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-6">
                                                <div class="product-slot stacked">
                                                    <div class="stack-row stack-top" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Lipton Ice Tea</div>
                                                            <div class="stacking-indicator">Stack 1/2</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row stack-bottom" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Lipton Ice Tea</div>
                                                            <div class="stacking-indicator">Stack 2/2</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-7">
                                                <div class="empty-slot">
                                                    <div class="empty-content">
                                                        <span class="empty-icon">📭</span>
                                                        <span class="empty-text">Empty</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Shelf 1 (Bottom) -->
                            <div class="shelf-component">
                                <div class="shelf-header">
                                    <h3>Shelf 1</h3>
                                    <div class="shelf-stats">
                                        <span class="products-count">7 products</span>
                                        <span class="gaps-count">1 gaps</span>
                                    </div>
                                </div>
                                <div class="shelf-content">
                                    <div class="shelf-section section-left">
                                        <div class="section-label">Left</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-1">
                                                <div class="product-slot full-height" style="background-color: #22c55e;">
                                                    <div class="product-content">
                                                        <div class="product-name">Coca-Cola Coke Zero 330ml</div>
                                                        <div class="product-price">£1.29</div>
                                                        <div class="product-facings">3 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-2">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">Coca-Cola Sprite 330ml</div>
                                                        <div class="product-price">£1.29</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-3">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">Coca-Cola Fanta Orange</div>
                                                        <div class="product-price">£1.29</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="shelf-section section-center">
                                        <div class="section-label">Center</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-4">
                                                <div class="product-slot full-height" style="background-color: #22c55e;">
                                                    <div class="product-content">
                                                        <div class="product-name">PepsiCo Pepsi Max 330ml</div>
                                                        <div class="product-price">£1.19</div>
                                                        <div class="product-facings">3 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-5">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">PepsiCo 7UP Free</div>
                                                        <div class="product-price">£1.19</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-6">
                                                <div class="empty-slot">
                                                    <div class="empty-content">
                                                        <span class="empty-icon">📭</span>
                                                        <span class="empty-text">Empty</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="shelf-section section-right">
                                        <div class="section-label">Right</div>
                                        <div class="section-slots">
                                            <div class="slot-container position-7">
                                                <div class="product-slot stacked">
                                                    <div class="stack-row stack-top" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Red Bull Energy</div>
                                                            <div class="stacking-indicator">Stack 1/2</div>
                                                        </div>
                                                    </div>
                                                    <div class="stack-row stack-bottom" style="background-color: #22c55e;">
                                                        <div class="product-content">
                                                            <div class="product-name">Red Bull Energy</div>
                                                            <div class="stacking-indicator">Stack 2/2</div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="slot-container position-8">
                                                <div class="product-slot full-height" style="background-color: #3b82f6;">
                                                    <div class="product-content">
                                                        <div class="product-name">Monster Energy 500ml</div>
                                                        <div class="product-price">£2.15</div>
                                                        <div class="product-facings">2 facings</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Overlay Controls -->
                        <div class="planogram-overlay-controls">
                            <h4>Display Options</h4>
                            <div class="overlay-toggles">
                                <label><input type="checkbox" checked> Product Names</label>
                                <label><input type="checkbox" checked> Prices</label>
                                <label><input type="checkbox" checked> Facing Counts</label>
                                <label><input type="checkbox"> Confidence Scores</label>
                                <label><input type="checkbox" checked> Stacking Indicators</label>
                            </div>
                            <p style="margin-top: 10px; font-size: 12px; color: #64748b;">
                                <strong>Note:</strong> This is a fallback HTML version. The React component provides full interactivity.
                            </p>
                        </div>
                    </div>
                `;
            }
            
            // Global planogram control functions - working with HTML grid
            let currentZoomLevel = 1.0;
            let displaySettings = {
                showBrands: true,
                showProducts: true, 
                showPrices: true,
                showConfidence: false
            };

            function updatePlanogramZoom(factor, reset = false) {
                const planogramViewer = document.getElementById('planogramViewer');
                if (!planogramViewer) return;

                if (reset) {
                    currentZoomLevel = 1.0;
                } else {
                    currentZoomLevel *= factor;
                    currentZoomLevel = Math.max(0.5, Math.min(3.0, currentZoomLevel)); // Limit zoom range
                }

                planogramViewer.style.transform = `scale(${currentZoomLevel})`;
                planogramViewer.style.transformOrigin = 'top left';
                
                const zoomElement = document.getElementById('zoomPercentage');
                if (zoomElement) {
                    zoomElement.textContent = Math.round(currentZoomLevel * 100) + '%';
                }
                
                console.log(`🔍 Zoom updated: ${Math.round(currentZoomLevel * 100)}%`);
            }
            
            function updatePlanogramDisplay(setting, enabled) {
                displaySettings[setting] = enabled;
                
                // Update button visual state
                const button = document.querySelector(`#toggle${setting.charAt(0).toUpperCase() + setting.slice(1).replace('show', '')}`);
                if (button) {
                    const label = button.parentElement;
                    const span = label.querySelector('span');
                    if (enabled) {
                        span.textContent = '✓';
                        label.style.background = getToggleColor(setting);
                        label.style.color = setting === 'showPrices' ? '#2d3748' : 'white';
                    } else {
                        span.textContent = '○';
                        label.style.background = '#f7fafc';
                        label.style.color = '#4a5568';
                    }
                }

                // Apply display changes to all product cells
                const productCells = document.querySelectorAll('[data-product-cell]');
                productCells.forEach(cell => {
                    const brandDiv = cell.querySelector('[data-brand]');
                    const nameDiv = cell.querySelector('[data-name]');
                    const priceDiv = cell.querySelector('[data-price]');
                    const confidenceDiv = cell.querySelector('[data-confidence]');

                    if (brandDiv) brandDiv.style.display = displaySettings.showBrands ? 'block' : 'none';
                    if (nameDiv) nameDiv.style.display = displaySettings.showProducts ? 'block' : 'none';
                    if (priceDiv) priceDiv.style.display = displaySettings.showPrices ? 'block' : 'none';
                    if (confidenceDiv) confidenceDiv.style.display = displaySettings.showConfidence ? 'block' : 'none';
                });
                
                console.log(`✅ Updated planogram display: ${setting} = ${enabled}`);
            }
            
            function getToggleColor(setting) {
                const colors = {
                    'showBrands': '#4facfe',
                    'showProducts': '#fa709a', 
                    'showPrices': '#a8edea',
                    'showConfidence': '#ffecd2'
                };
                return colors[setting] || '#f7fafc';
            }
            
            // Zoom functionality for planogram
            let currentZoom = 1.0;
            
            function updatePlanogramZoom(factor, reset = false, absolute = false) {
                if (reset) {
                    currentZoom = 1.0;
                } else if (absolute) {
                    // Set absolute zoom level
                    currentZoom = factor;
                } else {
                    // Multiply current zoom by factor
                    currentZoom *= factor;
                }
                // Limit zoom range
                currentZoom = Math.max(0.3, Math.min(3.0, currentZoom));
                
                // Apply zoom to all planogram grids AND adjust containers properly
                const planogramGrids = document.querySelectorAll('.planogram-grid');
                const planogramViewer = document.getElementById('planogramViewer');
                const shelfContainers = document.querySelectorAll('.planogram-grid').forEach(grid => {
                    const shelfContainer = grid.closest('div[style*="background: white"]');
                    if (shelfContainer) {
                        // Scale the entire shelf container, not just the grid
                        shelfContainer.style.transform = `scale(${currentZoom})`;
                        shelfContainer.style.transformOrigin = 'top left';
                        
                        // Adjust container dimensions to prevent clipping
                        if (currentZoom > 1.0) {
                            // When zooming in, increase the container size proportionally
                            shelfContainer.style.marginBottom = `${(currentZoom - 1) * 100}px`;
                            shelfContainer.style.marginRight = `${(currentZoom - 1) * 200}px`;
                        } else {
                            // Reset margins when zooming out or at normal zoom
                            shelfContainer.style.marginBottom = '0px';
                            shelfContainer.style.marginRight = '0px';
                        }
                    }
                });
                
                // Adjust the main container to accommodate the scaled content
                if (planogramViewer) {
                    // Always enable scrolling for zoom
                    planogramViewer.style.overflow = 'auto';
                    planogramViewer.style.height = '100%';
                    
                    // Adjust the container's internal spacing based on zoom
                    const planogramDiv = planogramViewer.querySelector('div[style*="background: #f8fafc"]');
                    if (planogramDiv) {
                        if (currentZoom > 1.0) {
                            // Add extra padding when zoomed in to prevent clipping
                            planogramDiv.style.paddingBottom = `${currentZoom * 50}px`;
                            planogramDiv.style.paddingRight = `${currentZoom * 50}px`;
                        } else {
                            // Reset padding for normal/zoom out
                            planogramDiv.style.paddingBottom = '16px';
                            planogramDiv.style.paddingRight = '16px';
                        }
                    }
                }
                
                // Update zoom percentage display
                const zoomDisplay = document.getElementById('zoomPercentage');
                if (zoomDisplay) {
                    zoomDisplay.textContent = `${Math.round(currentZoom * 100)}%`;
                }
                
                console.log(`🔍 Planogram zoom updated: ${Math.round(currentZoom * 100)}% - Containers scaled and adjusted for proper visibility`);
            }
            
            // Dynamic Grid Planogram - GLOBAL width consistency + proper stacking
            function createSimpleGridPlanogram(container, planogramData) {
                console.log('🎯 Creating GLOBAL CONSISTENT GRID planogram with proper stacking');
                
                const { shelves } = planogramData;
                
                // Calculate GLOBAL dimensions across ALL shelves - CUMULATIVE APPROACH
                let globalMaxPosition = 8; // Minimum shelf width
                let globalMaxStackHeight = 1;
                
                console.log('🔍 Calculating global dimensions using CUMULATIVE positioning...');
                
                // First pass: calculate actual grid slots needed for each shelf
                shelves.forEach(shelf => {
                    console.log(`📏 Analyzing shelf ${shelf.shelf_number} for global dimensions`);
                    
                    let shelfGridPosition = 1; // Track cumulative position for this shelf
                    
                    ['Left', 'Center', 'Right'].forEach(sectionName => {
                        if (shelf.sections[sectionName]) {
                            shelf.sections[sectionName].forEach(slot => {
                                if (slot.type === 'product' && slot.data) {
                                    const product = slot.data;
                                    const facings = product.quantity?.columns || 1;
                                    const stackHeight = product.quantity?.stack || 1;
                                    
                                    console.log(`  📍 ${product.brand} ${product.name}: ${facings} facings starting at grid ${shelfGridPosition}`);
                                    
                                    shelfGridPosition += facings; // Move to next position
                                    globalMaxStackHeight = Math.max(globalMaxStackHeight, stackHeight);
                                    
                                } else if (slot.type === 'empty') {
                                    console.log(`  ⭕ Empty slot at grid ${shelfGridPosition}`);
                                    shelfGridPosition += 1; // Empty takes 1 slot
                                }
                            });
                        }
                    });
                    
                    const shelfTotalSlots = shelfGridPosition - 1;
                    console.log(`  📊 Shelf ${shelf.shelf_number} needs ${shelfTotalSlots} total grid slots`);
                    globalMaxPosition = Math.max(globalMaxPosition, shelfTotalSlots);
                });

                console.log(`📏 Global dimensions: ${globalMaxPosition} positions × ${globalMaxStackHeight} stack height`);
                
                // DEBUG: Test the logic with Coke Zero example
                console.log('🧪 TESTING LOGIC: Coke Zero at position 1 with 3 facings should fill grid slots 1, 2, 3');
                console.log('🧪 Grid calculation: position 1 → grid columns 0, 1, 2 (0-based)');
                console.log('🧪 Display: Should show 3 separate Coke Zero cells');

                // Create main container
                const planogramDiv = document.createElement('div');
                planogramDiv.style.cssText = `
                    background: #f8fafc;
                    height: 100%;
                    padding: 16px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    overflow: auto;
                    display: flex;
                    flex-direction: column;
                `;
                
                // Create shelves container
                const shelvesContainer = document.createElement('div');
                shelvesContainer.style.cssText = `
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                    min-height: 100%;
                    overflow: visible;
                    padding: 8px;
                    min-width: max-content;
                `;

                // Sort shelves from top to bottom (highest shelf number first)
                const sortedShelves = shelves.sort((a, b) => b.shelf_number - a.shelf_number);

                // ALL shelves use the SAME global dimensions
                sortedShelves.forEach(shelf => {
                    const shelfDiv = createGlobalConsistentShelfGrid(shelf, globalMaxPosition, globalMaxStackHeight);
                    shelvesContainer.appendChild(shelfDiv);
                });
                
                planogramDiv.appendChild(shelvesContainer);
                container.appendChild(planogramDiv);
            }
            

            
            function getConfidenceColor(confidence) {
                // EXACT MATCH with backend color mapping in src/api/planogram_editor.py
                // This must match the get_confidence_color function in the backend
                if (confidence >= 0.95) return '#22c55e'; // Green - very high (95%+)
                if (confidence >= 0.85) return '#3b82f6'; // Blue - high (85-94%)
                if (confidence >= 0.70) return '#f59e0b'; // Orange - medium (70-84%)
                return '#ef4444'; // Red - low (below 70%)
            }
            
            function getTotalProducts(shelves) {
                let total = 0;
                shelves.forEach(shelf => {
                    total += shelf.product_count || 0;
                });
                return total;
            }
            
            function getMaxStackHeight(shelf) {
                let maxStack = 1;
                Object.values(shelf.sections).forEach(section => {
                    section.forEach(slot => {
                        if (slot.type === 'product') {
                            const stack = slot.data.quantity?.stack || 1;
                            maxStack = Math.max(maxStack, stack);
                        }
                    });
                });
                return maxStack;
            }
            
            // Create GLOBAL CONSISTENT shelf grid - all shelves same width
            function createGlobalConsistentShelfGrid(shelf, globalMaxPosition, globalMaxStackHeight) {
                console.log(`🏗️ Creating GLOBAL CONSISTENT grid for Shelf ${shelf.shelf_number}: ${globalMaxPosition} positions × ${globalMaxStackHeight} stack (SAME for all shelves)`);
                
                const shelfDiv = document.createElement('div');
                shelfDiv.style.cssText = `
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                    padding: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    display: flex;
                    align-items: stretch;
                `;

                // Shelf number on the left side
                const shelfNumber = document.createElement('div');
                shelfNumber.style.cssText = `
                    background: transparent;
                    color: #64748b;
                    font-weight: 600;
                    font-size: 16px;
                    padding: 8px 4px;
                    margin-right: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 25px;
                    flex-shrink: 0;
                `;
                shelfNumber.textContent = shelf.shelf_number;
                shelfDiv.appendChild(shelfNumber);

                // Grid container (no header)
                const gridWrapper = document.createElement('div');
                gridWrapper.style.cssText = `
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    min-width: 0;
                `;

                // Create 2D grid array using GLOBAL dimensions
                const grid = createGlobal2DGrid(shelf, globalMaxPosition, globalMaxStackHeight);
                
                // Calculate ACTUAL stack height for THIS shelf (not global)
                let actualShelfStackHeight = 1;
                ['Left', 'Center', 'Right'].forEach(sectionName => {
                    if (shelf.sections[sectionName]) {
                        shelf.sections[sectionName].forEach(slot => {
                            if (slot.type === 'product' && slot.data) {
                                const stackHeight = slot.data.quantity?.stack || 1;
                                actualShelfStackHeight = Math.max(actualShelfStackHeight, stackHeight);
                            }
                        });
                    }
                });

                console.log(`📐 Shelf ${shelf.shelf_number}: Using actual stack height ${actualShelfStackHeight} (not global ${globalMaxStackHeight})`);

                // Create the visual grid container with FIXED compact dimensions - no horizontal scroll
                const gridContainer = document.createElement('div');
                gridContainer.className = 'planogram-grid';
                gridContainer.style.cssText = `
                    display: grid;
                    grid-template-columns: repeat(${globalMaxPosition}, 45px);
                    grid-template-rows: repeat(${actualShelfStackHeight}, 32px);
                    gap: 1px;
                    background: #f7fafc;
                    border-radius: 4px;
                    padding: 6px;
                    width: 100%;
                    max-width: 100%;
                    box-sizing: border-box;
                    overflow: hidden;
                    transform-origin: top left;
                    transition: transform 0.3s ease;
                    justify-content: start;
                `;

                // DEBUG: Check what's actually in the grid before rendering
                console.log(`🔍 GRID CONTENTS for shelf ${shelf.shelf_number}:`);
                for (let stackLevel = 0; stackLevel < actualShelfStackHeight; stackLevel++) {
                    let rowContents = [];
                    for (let position = 0; position < globalMaxPosition; position++) {
                        const cellData = grid[stackLevel][position];
                        if (cellData.type === 'product') {
                            rowContents.push(`${cellData.product.brand}(F${cellData.facingIndex})`);
                        } else {
                            rowContents.push('EMPTY');
                        }
                    }
                    console.log(`  Row ${stackLevel}: [${rowContents.join(', ')}]`);
                }

                // Fill grid with cells using ACTUAL shelf stack height
                for (let stackLevel = actualShelfStackHeight - 1; stackLevel >= 0; stackLevel--) {
                    for (let position = 0; position < globalMaxPosition; position++) {
                        const cellData = grid[stackLevel][position];
                        const cell = createGlobalGridCell(cellData, position + 1, stackLevel + 1);
                        gridContainer.appendChild(cell);
                    }
                }

                gridWrapper.appendChild(gridContainer);
                shelfDiv.appendChild(gridWrapper);
                return shelfDiv;
            }
            
            // Create GLOBAL 2D grid array using ACTUAL JSON data
            function createGlobal2DGrid(shelf, globalMaxPosition, globalMaxStackHeight) {
                console.log(`📊 Creating GLOBAL 2D grid from JSON: ${globalMaxPosition} × ${globalMaxStackHeight}`);
                
                // Initialize empty grid with GLOBAL dimensions
                const grid = [];
                for (let stackLevel = 0; stackLevel < globalMaxStackHeight; stackLevel++) {
                    grid[stackLevel] = [];
                    for (let position = 0; position < globalMaxPosition; position++) {
                        grid[stackLevel][position] = { 
                            type: 'empty', 
                            position: position + 1, 
                            stackLevel: stackLevel + 1 
                        };
                    }
                }
                
                // Place products from ACTUAL JSON data - CALCULATE REAL GRID POSITIONS
                console.log(`🏗️ Shelf ${shelf.shelf_number}: Starting product placement`);
                console.log(`📊 Raw shelf data:`, shelf);
                
                let currentGridPosition = 1; // Track actual grid position
                
                ['Left', 'Center', 'Right'].forEach(sectionName => {
                    if (shelf.sections[sectionName]) {
                        console.log(`📂 Section ${sectionName}: ${shelf.sections[sectionName].length} slots`);
                        console.log(`📋 Section ${sectionName} raw data:`, shelf.sections[sectionName]);
                        
                        shelf.sections[sectionName].forEach((slot, index) => {
                            console.log(`🔍 Processing slot ${index + 1}:`, slot);
                            
                            if (slot.type === 'product' && slot.data) {
                                const facings = slot.data.quantity?.columns || 1;
                                console.log(`📍 PRODUCT: ${slot.data.brand} ${slot.data.name}`);
                                console.log(`📐 JSON position: ${slot.position} (sequence in section)`);
                                console.log(`📐 REAL grid position: ${currentGridPosition} (calculated)`);
                                console.log(`📐 Facings: ${facings} → will occupy grid slots ${currentGridPosition} to ${currentGridPosition + facings - 1}`);
                                
                                placeProductInGlobalGrid(grid, slot.data, currentGridPosition);
                                currentGridPosition += facings; // Move to next available position
                                
                            } else if (slot.type === 'empty') {
                                console.log(`⭕ EMPTY: JSON position ${slot.position} → grid position ${currentGridPosition}`);
                                currentGridPosition += 1; // Empty slot takes 1 position
                            } else {
                                console.log(`❓ UNKNOWN SLOT TYPE: ${slot.type}`, slot);
                            }
                        });
                    } else {
                        console.log(`📂 Section ${sectionName}: No data`);
                    }
                });
                console.log(`✅ Shelf ${shelf.shelf_number}: Product placement complete. Total grid positions used: ${currentGridPosition - 1}`);
                
                return grid;
            }
            
            // Place product in GLOBAL grid - DECOUPLE JSON position from grid positions
            function placeProductInGlobalGrid(grid, product, jsonPosition) {
                // Extract EXACT values from JSON data
                const facings = product.quantity?.columns || 1;
                const stackHeight = product.quantity?.stack || 1;
                
                console.log(`📦 PRODUCT: ${product.brand} ${product.name}`);
                console.log(`📍 JSON position: ${jsonPosition} (starting position of this product)`);
                console.log(`📐 Facings: ${facings} (will occupy ${facings} grid slots)`);
                console.log(`📚 Stack: ${stackHeight} (height in each slot)`);
                console.log(`🎯 GRID SLOTS TO FILL: ${jsonPosition} to ${jsonPosition + facings - 1}`);
                
                // FILL GRID SLOTS: Each facing gets its own grid column
                for (let stackLevel = 0; stackLevel < stackHeight; stackLevel++) {
                    for (let facing = 0; facing < facings; facing++) {
                        // GRID POSITION CALCULATION:
                        // - jsonPosition is 1-based (e.g., position 4)
                        // - grid is 0-based (e.g., grid[0][3])
                        // - facing 0 goes to jsonPosition, facing 1 goes to jsonPosition+1, etc.
                        const gridRow = stackLevel;
                        const gridCol = (jsonPosition - 1) + facing; // Convert to 0-based and add facing offset
                        
                        console.log(`  🔲 SLOT ${gridCol + 1}: grid[${gridRow}][${gridCol}] = ${product.brand} facing ${facing + 1}/${facings}, stack ${stackLevel + 1}/${stackHeight}`);
                        
                        if (gridRow < grid.length && gridCol < grid[0].length) {
                            grid[gridRow][gridCol] = {
                                type: 'product',
                                product: product,
                                jsonPosition: jsonPosition, // Original JSON position
                                gridPosition: gridCol + 1, // Actual grid slot (1-based)
                                stackLevel: stackLevel + 1,
                                facingIndex: facing + 1,
                                totalFacings: facings,
                                totalStack: stackHeight,
                                cellId: `${product.id || product.brand}-JSON${jsonPosition}-GRID${gridCol + 1}-F${facing + 1}S${stackLevel + 1}`
                            };
                            console.log(`    ✅ FILLED grid slot ${gridCol + 1} with ${product.brand} facing ${facing + 1}`);
                        } else {
                            console.error(`❌ GRID OVERFLOW: grid[${gridRow}][${gridCol}] for ${product.brand} facing ${facing + 1}`);
                        }
                    }
                }
                console.log(`✅ ${product.brand}: JSON position ${jsonPosition} → FILLED grid slots ${jsonPosition} to ${jsonPosition + facings - 1}`);
            }
            
            // Create grid cell using EXACT JSON data - truly empty slots are invisible
            function createGlobalGridCell(cellData, position, stackLevel) {
                const cell = document.createElement('div');
                
                if (cellData.type === 'empty') {
                    // TRULY EMPTY cell - completely transparent/invisible with fixed dimensions
                    cell.style.cssText = `
                        background: transparent;
                        border: none;
                        height: 32px;
                        width: 45px;
                        min-width: 45px;
                        max-width: 45px;
                        box-sizing: border-box;
                    `;
                    return cell;
                }

                // Product cell using EXACT JSON data
                const { product, jsonPosition, gridPosition, facingIndex, stackLevel: productStackLevel, totalFacings, totalStack, cellId } = cellData;
                
                // Use EXACT confidence from JSON - prioritize visual.confidence_color if available
                const confidence = product.metadata?.extraction_confidence || product.extraction_confidence || 0.9;
                const confidenceColor = product.visual?.confidence_color || getConfidenceColor(confidence);
                
                console.log(`🎨 Cell: ${cellId}, JSON pos: ${jsonPosition}, Grid pos: ${gridPosition}, Facing: ${facingIndex}/${totalFacings}, Stack: ${productStackLevel}/${totalStack}, Confidence: ${confidence}`);
                console.log(`🎨 Color source: ${product.visual?.confidence_color ? 'JSON visual.confidence_color' : 'calculated from confidence'} = ${confidenceColor}`);
                console.log(`🎨 Product visual data:`, product.visual);
                
                // Style product cell - FIXED compact size to prevent expansion
                cell.style.cssText = `
                    background: linear-gradient(135deg, ${confidenceColor} 0%, ${adjustColor(confidenceColor, -20)} 100%);
                    color: white;
                    border-radius: 2px;
                    height: 32px;
                    width: 45px;
                    min-width: 45px;
                    max-width: 45px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    font-size: 6px;
                    font-weight: 500;
                    border: 1px solid ${confidenceColor};
                    position: relative;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                    box-sizing: border-box;
                    overflow: hidden;
                `;

                // Add hover effect
                cell.addEventListener('mouseenter', () => {
                    cell.style.transform = 'scale(1.05)';
                    cell.style.zIndex = '10';
                    cell.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                });
                cell.addEventListener('mouseleave', () => {
                    cell.style.transform = 'scale(1)';
                    cell.style.zIndex = '1';
                    cell.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                });

                // Add data attribute for display controls
                cell.setAttribute('data-product-cell', 'true');

                // ALL CELLS show the same product info - no "main cell" concept for facings
                const brandDiv = document.createElement('div');
                brandDiv.setAttribute('data-brand', 'true');
                brandDiv.style.cssText = `
                    font-weight: 700;
                    font-size: 6px;
                    text-align: center;
                    margin-bottom: 0px;
                    text-overflow: ellipsis;
                    overflow: hidden;
                    white-space: nowrap;
                    width: 100%;
                    line-height: 1;
                `;
                brandDiv.textContent = product.brand || 'Unknown';

                const nameDiv = document.createElement('div');
                nameDiv.setAttribute('data-name', 'true');
                nameDiv.style.cssText = `
                    font-size: 5px;
                    text-align: center;
                    opacity: 0.9;
                    text-overflow: ellipsis;
                    overflow: hidden;
                    white-space: nowrap;
                    width: 100%;
                    line-height: 1;
                    margin-bottom: 0px;
                `;
                nameDiv.textContent = product.name || 'Product';

                if (product.price) {
                    const priceDiv = document.createElement('div');
                    priceDiv.setAttribute('data-price', 'true');
                    priceDiv.style.cssText = `
                        font-size: 5px;
                        font-weight: 700;
                        text-align: center;
                        background: rgba(255,255,255,0.2);
                        padding: 0px 2px;
                        border-radius: 1px;
                        line-height: 1;
                        margin-top: 1px;
                    `;
                    priceDiv.textContent = `£${product.price.toFixed(2)}`;
                    cell.appendChild(priceDiv);
                }

                const confidenceDiv = document.createElement('div');
                confidenceDiv.setAttribute('data-confidence', 'true');
                confidenceDiv.style.cssText = `
                    font-size: 4px;
                    font-weight: 700;
                    text-align: center;
                    background: rgba(0,0,0,0.7);
                    color: white;
                    padding: 0px 1px;
                    border-radius: 1px;
                    margin-top: 1px;
                    display: none;
                    line-height: 1;
                `;
                confidenceDiv.textContent = `${Math.round(confidence * 100)}%`;
                cell.appendChild(confidenceDiv);

                cell.appendChild(brandDiv);
                cell.appendChild(nameDiv);

                // Add facing indicator for debugging (optional)
                if (totalFacings > 1) {
                    const indicator = document.createElement('div');
                    indicator.style.cssText = `
                        position: absolute;
                        top: 1px;
                        right: 1px;
                        background: rgba(0,0,0,0.7);
                        color: white;
                        font-size: 4px;
                        padding: 0px 1px;
                        border-radius: 1px;
                        font-weight: 700;
                        line-height: 1;
                    `;
                    indicator.textContent = `F${facingIndex}`;
                    cell.appendChild(indicator);
                }

                // Add click handler with EXACT JSON data
                cell.addEventListener('click', () => {
                    console.log(`🖱️ Clicked cell: ${cellId}`);
                    console.log(`📍 Product: ${product.brand} ${product.name}`);
                    console.log(`📐 JSON position: ${jsonPosition}, Grid position: ${gridPosition}`);
                    console.log(`📊 Facing: ${facingIndex}/${totalFacings}, Stack: ${productStackLevel}/${totalStack}`);
                    console.log('Full product data:', product);
                });

                return cell;
            }
            
            // Utility function to adjust color brightness
            function adjustColor(color, amount) {
                const usePound = color[0] === '#';
                const col = usePound ? color.slice(1) : color;
                const num = parseInt(col, 16);
                let r = (num >> 16) + amount;
                let g = (num >> 8 & 0x00FF) + amount;
                let b = (num & 0x0000FF) + amount;
                r = r > 255 ? 255 : r < 0 ? 0 : r;
                g = g > 255 ? 255 : g < 0 ? 0 : g;
                b = b > 255 ? 255 : b < 0 ? 0 : b;
                return (usePound ? '#' : '') + (r << 16 | g << 8 | b).toString(16).padStart(6, '0');
            }



            // Utility function
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            // Load React component after React libraries are ready
            function loadReactComponent() {
                console.log('📦 Loading React component...');
                
                // Check if React is available
                if (typeof React === 'undefined' || typeof ReactDOM === 'undefined') {
                    console.log('⏳ React not ready, waiting...');
                    setTimeout(loadReactComponent, 100);
                    return;
                }
                
                // Load the component script
                const script = document.createElement('script');
                script.src = '/static/components/InteractivePlanogram.js';
                script.onload = function() {
                    console.log('✅ React component script loaded');
                    initializePlanogramComponent();
                };
                script.onerror = function() {
                    console.error('❌ Failed to load React component script');
                };
                document.head.appendChild(script);
            }
            
            // Initialize React Planogram Component
            function initializePlanogramComponent() {
                console.log('🚀 Initializing React Planogram Component...');
                
                // Check if everything is loaded
                if (typeof React === 'undefined') {
                    console.error('❌ React not loaded');
                    return false;
                }
                
                if (typeof ReactDOM === 'undefined') {
                    console.error('❌ ReactDOM not loaded');
                    return false;
                }
                
                if (typeof window.InteractivePlanogram === 'undefined') {
                    console.error('❌ InteractivePlanogram component not loaded');
                    return false;
                }
                
                // Find the planogram container
                const planogramContainer = document.getElementById('planogramViewer');
                if (!planogramContainer) {
                    console.log('⚠️ Planogram container not found (will try later)');
                    return false;
                }
                
                try {
                    // Clear existing content
                    planogramContainer.innerHTML = '';
                    
                    // Create and render React component
                    const planogramElement = React.createElement(window.InteractivePlanogram, {
                        imageId: 'demo'
                    });
                    
                    ReactDOM.render(planogramElement, planogramContainer);
                    console.log('✅ React Planogram Component rendered successfully');
                    return true;
                } catch (error) {
                    console.error('❌ Error rendering React component:', error);
                    planogramContainer.innerHTML = `
                        <div style="padding: 20px; text-align: center; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; color: #dc2626;">
                            <h3>⚠️ Component Error</h3>
                            <p>Failed to render planogram: ${error.message}</p>
                        </div>
                    `;
                    return false;
                }
            }
            
            // Start loading when DOM is ready
            document.addEventListener('DOMContentLoaded', function() {
                console.log('🔄 DOM loaded, starting React component loading...');
                loadReactComponent();
                
                // Also try to load it when switching to simple mode
                window.forceLoadPlanogram = function() {
                    console.log('🔧 Force loading planogram...');
                    if (typeof window.InteractivePlanogram !== 'undefined') {
                        initializePlanogramComponent();
                    } else {
                        loadReactComponent();
                    }
                };
            });
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "queue_review_dashboard",
        "features": [
            "queue_management",
            "multi_system_selection",
            "progressive_disclosure",
            "human_evaluation"
        ]
    }

@app.get("/api/status")
async def api_status():
    """API status and capabilities"""
    return {
        "api_version": "2.0.0",
        "interface_modes": ["queue", "simple", "comparison", "advanced"],
        "extraction_systems": ["custom_consensus", "langgraph", "hybrid"],
        "evaluation_system": "human_in_the_loop",
        "database": "supabase_integration"
    }

if __name__ == "__main__":
    config = SystemConfig()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

