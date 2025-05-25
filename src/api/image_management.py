"""
Image Management API
Provides endpoints for image display, library management, and upload integration
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
import io
from PIL import Image
import base64

from ..config import SystemConfig
from ..utils import logger
from supabase import create_client, Client

router = APIRouter(prefix="/api/images", tags=["Image Management"])

# Initialize Supabase client
config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key)


@router.get("/library")
async def get_image_library(
    store: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get paginated image library with filtering"""
    
    try:
        # Build query
        query = supabase.table("ai_extraction_queue").select("""
            id,
            upload_id,
            ready_media_id,
            enhanced_image_path,
            status,
            created_at,
            processed_at,
            current_accuracy,
            metadata
        """)
        
        # Apply filters
        if store:
            query = query.eq("store_id", store)
        if category:
            query = query.eq("category", category)
        if status:
            query = query.eq("status", status)
        if date:
            query = query.gte("created_at", f"{date}T00:00:00").lt("created_at", f"{date}T23:59:59")
        
        # Get total count for pagination
        count_result = query.execute()
        total_count = len(count_result.data) if count_result.data else 0
        
        # Apply pagination
        offset = (page - 1) * limit
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        if not result.data:
            return {
                "images": [],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 0,
                    "pages": 0
                }
            }
        
        # Format images for UI
        images = []
        for item in result.data:
            # Extract metadata
            metadata = item.get('metadata', {}) or {}
            
            # Determine store and category from metadata or defaults
            store_info = metadata.get('store', {})
            category_info = metadata.get('category', 'unknown')
            
            image_data = {
                "id": item['id'],
                "upload_id": item['upload_id'],
                "ready_media_id": item['ready_media_id'],
                "title": f"{category_info.title()} Shelf Analysis",
                "store": store_info.get('id', 'unknown'),
                "storeName": store_info.get('name', 'Unknown Store'),
                "category": category_info,
                "status": item['status'],
                "date": item['created_at'][:10] if item['created_at'] else None,
                "timestamp": item['created_at'],
                "accuracy": item.get('current_accuracy', 0),
                "thumbnail_url": f"/api/images/{item['id']}/thumbnail",
                "image_url": f"/api/images/{item['id']}/full"
            }
            
            # Apply search filter
            if search:
                search_text = f"{image_data['title']} {image_data['storeName']} {image_data['category']}".lower()
                if search.lower() not in search_text:
                    continue
            
            images.append(image_data)
        
        total_pages = (total_count + limit - 1) // limit
        
        return {
            "images": images,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": total_pages
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get image library: {e}", component="image_api")
        raise HTTPException(status_code=500, detail=f"Failed to get image library: {str(e)}")


@router.get("/{image_id}/full")
async def get_full_image(image_id: str):
    """Get full resolution image"""
    
    try:
        # Get image info from database
        result = supabase.table("ai_extraction_queue").select(
            "enhanced_image_path, upload_id"
        ).eq("id", image_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image_info = result.data[0]
        image_path = image_info.get('enhanced_image_path')
        
        if not image_path:
            raise HTTPException(status_code=404, detail="Image path not found")
        
        # Download from Supabase storage
        file_data = supabase.storage.from_("retail-captures").download(image_path)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type="image/jpeg",
            headers={"Cache-Control": "max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get full image {image_id}: {e}", component="image_api")
        raise HTTPException(status_code=500, detail=f"Failed to get image: {str(e)}")


@router.get("/{image_id}/thumbnail")
async def get_thumbnail_image(image_id: str):
    """Get thumbnail version of image"""
    
    try:
        # Get image info from database
        result = supabase.table("ai_extraction_queue").select(
            "enhanced_image_path, upload_id"
        ).eq("id", image_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Image not found")
        
        image_info = result.data[0]
        image_path = image_info.get('enhanced_image_path')
        
        if not image_path:
            raise HTTPException(status_code=404, detail="Image path not found")
        
        # Download from Supabase storage
        file_data = supabase.storage.from_("retail-captures").download(image_path)
        
        # Create thumbnail
        image = Image.open(io.BytesIO(file_data))
        image.thumbnail((300, 300), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        thumbnail_io = io.BytesIO()
        image.save(thumbnail_io, format='JPEG', quality=85)
        thumbnail_io.seek(0)
        
        return StreamingResponse(
            thumbnail_io,
            media_type="image/jpeg",
            headers={"Cache-Control": "max-age=3600"}
        )
        
    except Exception as e:
        logger.error(f"Failed to get thumbnail {image_id}: {e}", component="image_api")
        raise HTTPException(status_code=500, detail=f"Failed to get thumbnail: {str(e)}")


@router.get("/{image_id}/analysis")
async def get_image_analysis(image_id: str):
    """Get analysis results for an image"""
    
    try:
        # Get analysis data from database
        result = supabase.table("ai_extraction_queue").select("*").eq("id", image_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Image analysis not found")
        
        analysis_data = result.data[0]
        
        # Format for progressive disclosure interface
        response = {
            "upload_id": analysis_data['upload_id'],
            "image_id": image_id,
            "status": analysis_data['status'],
            "accuracy": analysis_data.get('current_accuracy', 0),
            "processing_time": analysis_data.get('processing_duration', 0),
            "created_at": analysis_data['created_at'],
            "processed_at": analysis_data.get('processed_at'),
            
            # Mock agent iterations for now - replace with real data
            "agent_iterations": [
                {
                    "agent_number": 1,
                    "accuracy": 0.73,
                    "products_found": 21,
                    "duration": "45s",
                    "model_used": "GPT-4o",
                    "improvements": ["Basic shelf structure detection", "Initial product identification"],
                    "issues": ["Missing 4 products", "Price extraction errors", "Poor positioning accuracy"],
                    "json_data": {"products": [], "structure": {}}
                },
                {
                    "agent_number": 2,
                    "accuracy": 0.89,
                    "products_found": 24,
                    "duration": "38s",
                    "model_used": "Claude",
                    "improvements": ["Found 3 additional products", "Fixed price extraction", "Improved confidence scores"],
                    "issues": ["Minor positioning errors", "2 products still missing"],
                    "json_data": {"products": [], "structure": {}}
                },
                {
                    "agent_number": 3,
                    "accuracy": analysis_data.get('current_accuracy', 0.94),
                    "products_found": 25,
                    "duration": "22s",
                    "model_used": "Hybrid",
                    "improvements": ["Found all products", "Enhanced spatial positioning", "Cross-validation complete"],
                    "issues": ["Minor confidence variations"],
                    "json_data": {"products": [], "structure": {}}
                }
            ]
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get image analysis {image_id}: {e}", component="image_api")
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@router.post("/upload")
async def upload_new_image(
    file: UploadFile = File(...),
    store_id: str = Form(...),
    category: str = Form(...),
    description: Optional[str] = Form(None)
):
    """Upload new image and add to processing queue"""
    
    try:
        # Generate unique IDs
        upload_id = str(uuid.uuid4())
        ready_media_id = str(uuid.uuid4())
        
        # Read image data
        image_data = await file.read()
        
        # Generate storage path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        storage_path = f"uploads/{store_id}/{category}/{timestamp}_{upload_id}.jpg"
        
        # Upload to Supabase storage
        supabase.storage.from_("retail-captures").upload(storage_path, image_data)
        
        # Add to processing queue
        queue_data = {
            "upload_id": upload_id,
            "ready_media_id": ready_media_id,
            "enhanced_image_path": storage_path,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "metadata": {
                "store": {"id": store_id, "name": f"Store {store_id}"},
                "category": category,
                "description": description,
                "original_filename": file.filename,
                "file_size": len(image_data)
            }
        }
        
        result = supabase.table("ai_extraction_queue").insert(queue_data).execute()
        
        logger.info(
            f"New image uploaded and queued for processing",
            component="image_api",
            upload_id=upload_id,
            store_id=store_id,
            category=category
        )
        
        return {
            "success": True,
            "upload_id": upload_id,
            "image_id": result.data[0]['id'],
            "status": "queued_for_processing",
            "message": "Image uploaded successfully and added to processing queue"
        }
        
    except Exception as e:
        logger.error(f"Failed to upload image: {e}", component="image_api")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")


@router.get("/stores")
async def get_stores():
    """Get list of available stores"""
    
    try:
        # Get unique stores from queue data
        result = supabase.table("ai_extraction_queue").select("metadata").execute()
        
        stores = set()
        for item in result.data or []:
            metadata = item.get('metadata', {})
            if isinstance(metadata, dict) and 'store' in metadata:
                store_info = metadata['store']
                if isinstance(store_info, dict):
                    stores.add((store_info.get('id', 'unknown'), store_info.get('name', 'Unknown')))
        
        # Convert to list and add defaults
        store_list = [{"id": store_id, "name": name} for store_id, name in stores]
        
        # Add default stores if none found
        if not store_list:
            store_list = [
                {"id": "store_001", "name": "Downtown"},
                {"id": "store_002", "name": "Mall"},
                {"id": "store_003", "name": "Airport"},
                {"id": "store_004", "name": "Suburb"}
            ]
        
        return {"stores": sorted(store_list, key=lambda x: x['id'])}
        
    except Exception as e:
        logger.error(f"Failed to get stores: {e}", component="image_api")
        return {"stores": []}


@router.get("/categories")
async def get_categories():
    """Get list of available categories"""
    
    return {
        "categories": [
            {"id": "beverages", "name": "Beverages"},
            {"id": "snacks", "name": "Snacks"},
            {"id": "dairy", "name": "Dairy"},
            {"id": "frozen", "name": "Frozen"},
            {"id": "personal_care", "name": "Personal Care"},
            {"id": "household", "name": "Household"},
            {"id": "health_beauty", "name": "Health & Beauty"}
        ]
    } 