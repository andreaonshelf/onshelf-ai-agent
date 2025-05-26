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