"""
Interactive Planogram Editor API
Provides editable planogram data and handles manual corrections
"""

import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from ..config import SystemConfig
from ..utils import logger

# Initialize router
router = APIRouter(prefix="/api/planogram", tags=["planogram_editor"])

# Get config and database connection
config = SystemConfig()
try:
    from supabase import create_client
    supabase = create_client(config.supabase_url, config.supabase_service_key)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None


@router.get("/{image_id}/editable")
async def get_editable_planogram_data(image_id: str):
    """Get planogram data merged with human corrections for editing"""
    
    # Return demo data for demo image ID
    if image_id == "demo" or image_id == "12345":
        return get_demo_planogram_data()
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get AI extraction data
        ai_data = await get_ai_extraction_data(image_id)
        if not ai_data:
            raise HTTPException(status_code=404, detail="No extraction data found")
        
        # Get human corrections
        corrections = await get_human_corrections(image_id)
        
        # Merge AI data with corrections
        merged_data = merge_ai_data_with_corrections(ai_data, corrections)
        
        # Convert to editable format
        editable_planogram = convert_to_editable_format(merged_data)
        
        return {
            "image_id": image_id,
            "planogram": editable_planogram,
            "has_corrections": len(corrections) > 0,
            "correction_count": len(corrections)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get editable planogram data for {image_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get planogram data: {str(e)}")


def get_demo_planogram_data():
    """Return demo planogram data with 18 products for testing"""
    return {
        "image_id": "demo",
        "planogram": {
            "structure": {
                "shelf_count": 3,
                "total_width": 250,
                "total_height": 180
            },
            "shelves": [
                # Shelf 1 (Bottom)
                {
                    "shelf_number": 1,
                    "sections": {
                        "Left": [
                            {"type": "product", "position": 1, "data": {
                                "id": "coke_1", "brand": "Coca-Cola", "name": "Coke Zero 330ml", "price": 1.29,
                                "position": {"shelf_level": 1, "position_on_shelf": 1, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 3, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.98, "color": "black", "volume": "330ml"}
                            }},
                            {"type": "product", "position": 2, "data": {
                                "id": "sprite_1", "brand": "Coca-Cola", "name": "Sprite 330ml", "price": 1.29,
                                "position": {"shelf_level": 1, "position_on_shelf": 2, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.92, "color": "green", "volume": "330ml"}
                            }},
                            {"type": "product", "position": 3, "data": {
                                "id": "fanta_1", "brand": "Coca-Cola", "name": "Fanta Orange 330ml", "price": 1.29,
                                "position": {"shelf_level": 1, "position_on_shelf": 3, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.89, "color": "orange", "volume": "330ml"}
                            }}
                        ],
                        "Center": [
                            {"type": "product", "position": 4, "data": {
                                "id": "pepsi_1", "brand": "Pepsi", "name": "Pepsi Max 330ml", "price": 1.19,
                                "position": {"shelf_level": 1, "position_on_shelf": 4, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 3, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.95, "color": "blue", "volume": "330ml"}
                            }},
                            {"type": "product", "position": 5, "data": {
                                "id": "7up_1", "brand": "Pepsi", "name": "7UP 330ml", "price": 1.19,
                                "position": {"shelf_level": 1, "position_on_shelf": 5, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.87, "color": "green", "volume": "330ml"}
                            }},
                            {"type": "empty", "position": 6, "reason": "gap_detected"}
                        ],
                        "Right": [
                            {"type": "product", "position": 7, "data": {
                                "id": "redbull_1", "brand": "Red Bull", "name": "Red Bull Energy 250ml", "price": 1.89,
                                "position": {"shelf_level": 1, "position_on_shelf": 7, "section": {"vertical": "Right"}},
                                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                                "visual": {"uses_full_height": False, "stack_rows": 2, "facing_width": 2, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.96, "color": "blue", "volume": "250ml"}
                            }},
                            {"type": "product", "position": 8, "data": {
                                "id": "monster_1", "brand": "Monster", "name": "Monster Energy 500ml", "price": 2.15,
                                "position": {"shelf_level": 1, "position_on_shelf": 8, "section": {"vertical": "Right"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.91, "color": "green", "volume": "500ml"}
                            }}
                        ]
                    },
                    "total_positions": 8,
                    "product_count": 7,
                    "empty_count": 1
                },
                # Shelf 2 (Middle)
                {
                    "shelf_number": 2,
                    "sections": {
                        "Left": [
                            {"type": "product", "position": 1, "data": {
                                "id": "water_1", "brand": "Evian", "name": "Natural Water 500ml", "price": 0.89,
                                "position": {"shelf_level": 2, "position_on_shelf": 1, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 3, "columns": 2, "total_facings": 6},
                                "visual": {"uses_full_height": False, "stack_rows": 3, "facing_width": 2, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.97, "color": "clear", "volume": "500ml"}
                            }},
                            {"type": "product", "position": 2, "data": {
                                "id": "smartwater_1", "brand": "Coca-Cola", "name": "Smartwater 600ml", "price": 1.49,
                                "position": {"shelf_level": 2, "position_on_shelf": 2, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                                "visual": {"uses_full_height": False, "stack_rows": 2, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.88, "color": "clear", "volume": "600ml"}
                            }}
                        ],
                        "Center": [
                            {"type": "product", "position": 3, "data": {
                                "id": "juice_1", "brand": "Innocent", "name": "Orange Juice 330ml", "price": 2.29,
                                "position": {"shelf_level": 2, "position_on_shelf": 3, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 3, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.94, "color": "orange", "volume": "330ml"}
                            }},
                            {"type": "product", "position": 4, "data": {
                                "id": "apple_juice_1", "brand": "Innocent", "name": "Apple Juice 330ml", "price": 2.29,
                                "position": {"shelf_level": 2, "position_on_shelf": 4, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.90, "color": "green", "volume": "330ml"}
                            }},
                            {"type": "product", "position": 5, "data": {
                                "id": "smoothie_1", "brand": "Innocent", "name": "Berry Smoothie 250ml", "price": 2.79,
                                "position": {"shelf_level": 2, "position_on_shelf": 5, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#f59e0b"},
                                "metadata": {"extraction_confidence": 0.76, "color": "purple", "volume": "250ml"}
                            }}
                        ],
                        "Right": [
                            {"type": "product", "position": 6, "data": {
                                "id": "tea_1", "brand": "Lipton", "name": "Ice Tea Lemon 500ml", "price": 1.59,
                                "position": {"shelf_level": 2, "position_on_shelf": 6, "section": {"vertical": "Right"}},
                                "quantity": {"stack": 2, "columns": 3, "total_facings": 6},
                                "visual": {"uses_full_height": False, "stack_rows": 2, "facing_width": 3, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.93, "color": "yellow", "volume": "500ml"}
                            }},
                            {"type": "empty", "position": 7, "reason": "gap_detected"}
                        ]
                    },
                    "total_positions": 7,
                    "product_count": 6,
                    "empty_count": 1
                },
                # Shelf 3 (Top)
                {
                    "shelf_number": 3,
                    "sections": {
                        "Left": [
                            {"type": "product", "position": 1, "data": {
                                "id": "coffee_1", "brand": "Starbucks", "name": "Frappuccino Vanilla 250ml", "price": 2.49,
                                "position": {"shelf_level": 3, "position_on_shelf": 1, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 1, "columns": 3, "total_facings": 3},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 3, "confidence_color": "#22c55e"},
                                "metadata": {"extraction_confidence": 0.96, "color": "beige", "volume": "250ml"}
                            }},
                            {"type": "product", "position": 2, "data": {
                                "id": "coffee_2", "brand": "Starbucks", "name": "Frappuccino Mocha 250ml", "price": 2.49,
                                "position": {"shelf_level": 3, "position_on_shelf": 2, "section": {"vertical": "Left"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.89, "color": "brown", "volume": "250ml"}
                            }}
                        ],
                        "Center": [
                            {"type": "product", "position": 3, "data": {
                                "id": "sports_1", "brand": "Powerade", "name": "Blue Sport Drink 500ml", "price": 1.79,
                                "position": {"shelf_level": 3, "position_on_shelf": 3, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                                "visual": {"uses_full_height": False, "stack_rows": 2, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.85, "color": "blue", "volume": "500ml"}
                            }},
                            {"type": "product", "position": 4, "data": {
                                "id": "sports_2", "brand": "Gatorade", "name": "Orange Sport Drink 500ml", "price": 1.79,
                                "position": {"shelf_level": 3, "position_on_shelf": 4, "section": {"vertical": "Center"}},
                                "quantity": {"stack": 2, "columns": 2, "total_facings": 4},
                                "visual": {"uses_full_height": False, "stack_rows": 2, "facing_width": 2, "confidence_color": "#f59e0b"},
                                "metadata": {"extraction_confidence": 0.78, "color": "orange", "volume": "500ml"}
                            }}
                        ],
                        "Right": [
                            {"type": "product", "position": 5, "data": {
                                "id": "energy_1", "brand": "Rockstar", "name": "Energy Drink 500ml", "price": 1.99,
                                "position": {"shelf_level": 3, "position_on_shelf": 5, "section": {"vertical": "Right"}},
                                "quantity": {"stack": 1, "columns": 2, "total_facings": 2},
                                "visual": {"uses_full_height": True, "stack_rows": 1, "facing_width": 2, "confidence_color": "#3b82f6"},
                                "metadata": {"extraction_confidence": 0.86, "color": "black", "volume": "500ml"}
                            }},
                            {"type": "empty", "position": 6, "reason": "gap_detected"}
                        ]
                    },
                    "total_positions": 6,
                    "product_count": 5,
                    "empty_count": 1
                }
            ]
        },
        "has_corrections": False,
        "correction_count": 0
    }


async def get_ai_extraction_data(image_id: str) -> Optional[Dict[str, Any]]:
    """Get original AI extraction data from database"""
    
    try:
        result = supabase.table("ai_extraction_queue").select(
            "extraction_result, planogram_result"
        ).eq("id", image_id).execute()
        
        if not result.data:
            return None
        
        queue_item = result.data[0]
        extraction_result = queue_item.get("extraction_result")
        
        if not extraction_result:
            return None
        
        # Parse if string
        if isinstance(extraction_result, str):
            extraction_result = json.loads(extraction_result)
        
        return extraction_result
        
    except Exception as e:
        logger.error(f"Failed to get AI extraction data for {image_id}: {e}")
        return None


async def get_human_corrections(image_id: str) -> List[Dict[str, Any]]:
    """Get all human corrections for this image"""
    
    try:
        result = supabase.table("human_corrections").select("*").eq(
            "upload_id", image_id
        ).order("created_at", desc=False).execute()
        
        return result.data or []
        
    except Exception as e:
        logger.error(f"Failed to get human corrections for {image_id}: {e}")
        return []


def merge_ai_data_with_corrections(ai_data: Dict[str, Any], corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge AI extraction data with human corrections"""
    
    # Start with AI data
    merged_data = ai_data.copy()
    products = merged_data.get("products", [])
    
    # Apply corrections in chronological order
    for correction in corrections:
        correction_type = correction.get("correction_type")
        original_result = correction.get("original_ai_result", {})
        human_correction = correction.get("human_correction", {})
        
        if correction_type == "product_moved":
            # Update product position
            product_id = original_result.get("product_id")
            if product_id:
                for product in products:
                    if product.get("id") == product_id:
                        # Update position fields
                        if "shelf_level" in human_correction:
                            product["shelf_level"] = human_correction["shelf_level"]
                        if "position_on_shelf" in human_correction:
                            product["position_on_shelf"] = human_correction["position_on_shelf"]
                        if "section" in human_correction:
                            product["section"] = human_correction["section"]
                        break
        
        elif correction_type == "product_edited":
            # Update product details
            product_id = original_result.get("product_id")
            if product_id:
                for product in products:
                    if product.get("id") == product_id:
                        # Update any changed fields
                        for key, value in human_correction.items():
                            if key != "product_id":
                                product[key] = value
                        break
        
        elif correction_type == "product_added":
            # Add new product
            products.append(human_correction)
        
        elif correction_type == "product_removed":
            # Remove product
            product_id = original_result.get("product_id")
            if product_id:
                products = [p for p in products if p.get("id") != product_id]
    
    merged_data["products"] = products
    return merged_data


def convert_to_editable_format(merged_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert merged data to format suitable for interactive planogram"""
    
    products = merged_data.get("products", [])
    
    # Group products by shelf
    shelves = {}
    for product in products:
        shelf_level = product.get("shelf_level", 1)
        if shelf_level not in shelves:
            shelves[shelf_level] = []
        shelves[shelf_level].append(product)
    
    # Process each shelf
    processed_shelves = {}
    for shelf_num, shelf_products in shelves.items():
        processed_shelves[shelf_num] = process_shelf_for_visualization(shelf_products, shelf_num)
    
    return {
        "shelves": processed_shelves,
        "total_products": len(products),
        "shelf_count": len(shelves),
        "metadata": {
            "extraction_confidence": merged_data.get("accuracy_score", 0.0),
            "has_stacking": any(p.get("quantity", {}).get("stack", 1) > 1 for p in products)
        }
    }


def process_shelf_for_visualization(products: List[Dict[str, Any]], shelf_num: int) -> Dict[str, Any]:
    """Process products on a shelf for visualization"""
    
    # Sort products by position
    sorted_products = sorted(products, key=lambda p: p.get("position_on_shelf", 0))
    
    # Find gaps in positions
    positions = [p.get("position_on_shelf", 0) for p in sorted_products]
    max_position = max(positions) if positions else 0
    
    # Create grid slots
    grid_slots = []
    for pos in range(1, max_position + 1):
        product = next((p for p in sorted_products if p.get("position_on_shelf") == pos), None)
        
        if product:
            # Process product for visualization
            processed_product = process_product_for_visualization(product)
            grid_slots.append({
                "type": "product",
                "position": pos,
                "data": processed_product
            })
        else:
            # Empty slot
            grid_slots.append({
                "type": "empty",
                "position": pos,
                "reason": "gap_detected"
            })
    
    # Group by sections (Left/Center/Right)
    sections = {"Left": [], "Center": [], "Right": []}
    
    # Calculate section boundaries based on total positions
    section_size = max(1, max_position // 3)
    
    for slot in grid_slots:
        if slot["type"] == "product":
            section = slot["data"].get("section", {}).get("vertical", "Center")
            sections[section].append(slot)
        else:
            # For empty slots, calculate section based on position
            position = slot["position"]
            if position <= section_size:
                section = "Left"
            elif position <= section_size * 2:
                section = "Center"
            else:
                section = "Right"
            sections[section].append(slot)
    
    return {
        "shelf_number": shelf_num,
        "sections": sections,
        "total_positions": max_position,
        "product_count": len([s for s in grid_slots if s["type"] == "product"]),
        "empty_count": len([s for s in grid_slots if s["type"] == "empty"])
    }


def process_product_for_visualization(product: Dict[str, Any]) -> Dict[str, Any]:
    """Process individual product for visualization"""
    
    quantity = product.get("quantity", {})
    stack_count = quantity.get("stack", 1)
    columns = quantity.get("columns", 1)
    
    return {
        "id": product.get("id", f"product_{product.get('position_on_shelf', 0)}"),
        "brand": product.get("brand", "Unknown"),
        "name": product.get("name", "Unknown Product"),
        "price": product.get("price"),
        "position": {
            "shelf_level": product.get("shelf_level", 1),
            "position_on_shelf": product.get("position_on_shelf", 1),
            "section": product.get("section", {"vertical": "Center"})
        },
        "quantity": {
            "stack": stack_count,
            "columns": columns,
            "total_facings": quantity.get("total_facings", columns)
        },
        "visual": {
            "uses_full_height": stack_count == 1,
            "stack_rows": stack_count,
            "facing_width": columns,
            "confidence_color": get_confidence_color(product.get("extraction_confidence", 0.0))
        },
        "metadata": {
            "extraction_confidence": product.get("extraction_confidence", 0.0),
            "color": product.get("color"),
            "volume": product.get("volume"),
            "category": product.get("category")
        }
    }


def get_confidence_color(confidence: float) -> str:
    """Get color based on confidence level"""
    if confidence >= 0.95:
        return "#22c55e"  # Green - very high
    elif confidence >= 0.85:
        return "#3b82f6"  # Blue - high
    elif confidence >= 0.70:
        return "#f59e0b"  # Orange - medium
    else:
        return "#ef4444"  # Red - low


@router.post("/{image_id}/corrections")
async def save_planogram_corrections(image_id: str, corrections_data: Dict[str, Any]):
    """Save human corrections for planogram edits"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        corrections = corrections_data.get("corrections", [])
        
        # Save each correction to database
        for correction in corrections:
            correction_record = {
                "upload_id": image_id,
                "correction_type": correction.get("type"),
                "original_ai_result": correction.get("original"),
                "human_correction": correction.get("corrected"),
                "correction_context": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": correction.get("action"),
                    "user_notes": correction.get("notes")
                }
            }
            
            supabase.table("human_corrections").insert(correction_record).execute()
        
        logger.info(
            f"Saved {len(corrections)} corrections for image {image_id}",
            component="planogram_editor"
        )
        
        return {
            "success": True,
            "corrections_saved": len(corrections),
            "message": "Corrections saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save corrections for {image_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save corrections: {str(e)}") 