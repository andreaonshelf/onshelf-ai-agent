"""
Iteration Tracking API
Provides endpoints for tracking and retrieving detailed iteration data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime

from ..utils import logger

router = APIRouter(prefix="/api/iterations", tags=["Iteration Tracking"])

# In-memory storage for iteration data (in production, use database)
iteration_storage = {}

@router.post("/store/{queue_item_id}")
async def store_iteration_data(queue_item_id: int, iteration_data: Dict[str, Any]):
    """Store iteration data for a queue item"""
    try:
        iteration_storage[queue_item_id] = iteration_data
        logger.info(
            f"Stored iteration data for queue item {queue_item_id}",
            component="iteration_tracking",
            iterations=len(iteration_data.get('iterations', []))
        )
        return {"success": True, "message": "Iteration data stored"}
    except Exception as e:
        logger.error(f"Failed to store iteration data: {e}", component="iteration_tracking")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{queue_item_id}")
async def get_iteration_data(queue_item_id: int):
    """Get all iteration data for a queue item"""
    
    if queue_item_id not in iteration_storage:
        # Try to load from file (for debugging)
        debug_file = f"debug_iterations_{queue_item_id}.json"
        if os.path.exists(debug_file):
            with open(debug_file, 'r') as f:
                iteration_storage[queue_item_id] = json.load(f)
        else:
            raise HTTPException(status_code=404, detail="No iteration data found")
    
    data = iteration_storage[queue_item_id]
    
    # Process data for display
    iterations = []
    for iter_data in data.get('iterations', []):
        iterations.append({
            "iteration": iter_data['iteration'],
            "accuracy": iter_data['accuracy'],
            "timestamp": iter_data['timestamp'],
            "total_products": iter_data['extraction_data']['total_products'],
            "model_used": iter_data['extraction_data']['model_used'],
            "shelves": iter_data['structure']['shelves'],
            "has_planogram": iter_data.get('planogram_svg') is not None,
            "failure_areas": iter_data.get('failure_areas', 0) if isinstance(iter_data.get('failure_areas', 0), int) else len(iter_data.get('failure_areas', []))
        })
    
    return {
        "upload_id": data.get('upload_id'),
        "total_iterations": len(iterations),
        "iterations": iterations
    }


@router.get("/{queue_item_id}/iteration/{iteration_number}")
async def get_specific_iteration(queue_item_id: int, iteration_number: int):
    """Get detailed data for a specific iteration"""
    
    if queue_item_id not in iteration_storage:
        raise HTTPException(status_code=404, detail="No iteration data found")
    
    data = iteration_storage[queue_item_id]
    iterations = data.get('iterations', [])
    
    # Find the specific iteration
    for iter_data in iterations:
        if iter_data['iteration'] == iteration_number:
            return {
                "iteration": iter_data['iteration'],
                "accuracy": iter_data['accuracy'],
                "timestamp": iter_data['timestamp'],
                "extraction_data": iter_data['extraction_data'],
                "planogram_svg": iter_data.get('planogram_svg'),
                "structure": iter_data['structure'],
                "failure_areas": iter_data.get('failure_areas', [])
            }
    
    raise HTTPException(status_code=404, detail=f"Iteration {iteration_number} not found")


@router.get("/{queue_item_id}/products/{iteration_number}")
async def get_iteration_products(queue_item_id: int, iteration_number: int):
    """Get raw product extraction data for a specific iteration"""
    
    if queue_item_id not in iteration_storage:
        raise HTTPException(status_code=404, detail="No iteration data found")
    
    data = iteration_storage[queue_item_id]
    iterations = data.get('iterations', [])
    
    # Find the specific iteration
    for iter_data in iterations:
        if iter_data['iteration'] == iteration_number:
            products = iter_data['extraction_data']['products']
            
            # Group products by shelf
            products_by_shelf = {}
            for product in products:
                shelf = product['position']['shelf_number']
                if shelf not in products_by_shelf:
                    products_by_shelf[shelf] = []
                products_by_shelf[shelf].append(product)
            
            # Sort products within each shelf by position
            for shelf in products_by_shelf:
                products_by_shelf[shelf].sort(
                    key=lambda p: p['position']['position_on_shelf']
                )
            
            return {
                "iteration": iteration_number,
                "total_products": len(products),
                "products_by_shelf": products_by_shelf,
                "raw_products": products
            }
    
    raise HTTPException(status_code=404, detail=f"Iteration {iteration_number} not found")


@router.get("/{queue_item_id}/planogram/{iteration_number}")
async def get_iteration_planogram(queue_item_id: int, iteration_number: int):
    """Get planogram SVG for a specific iteration"""
    
    if queue_item_id not in iteration_storage:
        raise HTTPException(status_code=404, detail="No iteration data found")
    
    data = iteration_storage[queue_item_id]
    iterations = data.get('iterations', [])
    
    # Find the specific iteration
    for iter_data in iterations:
        if iter_data['iteration'] == iteration_number:
            svg_data = iter_data.get('planogram_svg')
            if not svg_data:
                raise HTTPException(status_code=404, detail="No planogram available for this iteration")
            
            return {
                "iteration": iteration_number,
                "svg": svg_data,
                "accuracy": iter_data['accuracy']
            }
    
    raise HTTPException(status_code=404, detail=f"Iteration {iteration_number} not found")


@router.post("/debug/save/{queue_item_id}")
async def save_debug_data(queue_item_id: int):
    """Save iteration data to file for debugging"""
    
    if queue_item_id not in iteration_storage:
        raise HTTPException(status_code=404, detail="No iteration data found")
    
    debug_file = f"debug_iterations_{queue_item_id}.json"
    with open(debug_file, 'w') as f:
        json.dump(iteration_storage[queue_item_id], f, indent=2, default=str)
    
    return {
        "success": True,
        "file": debug_file,
        "message": f"Debug data saved to {debug_file}"
    }