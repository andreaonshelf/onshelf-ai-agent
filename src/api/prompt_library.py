"""
Prompt Library API
Manages saving and loading of prompts with field definitions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from ..config import SystemConfig
from ..utils import logger
from supabase import create_client

router = APIRouter()

# Initialize Supabase client
config = SystemConfig()
supabase = create_client(config.supabase_url, config.supabase_service_key) if config.supabase_url and config.supabase_service_key else None


class FieldDefinition(BaseModel):
    """Field definition model"""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    fields: Optional[List['FieldDefinition']] = None  # For nested objects
    items: Optional['FieldDefinition'] = None  # For arrays


class PromptTemplate(BaseModel):
    """Prompt template with field definitions"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    prompt_text: str
    fields: List[FieldDefinition]
    stage_type: str  # products, prices, promotions, etc.
    tags: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    is_default: bool = False
    usage_count: int = 0


class SavePromptRequest(BaseModel):
    """Request to save a prompt template"""
    name: str
    description: Optional[str] = None
    prompt_text: str
    fields: List[Dict[str, Any]]
    stage_type: str
    tags: List[str] = []


@router.post("/save")
async def save_prompt_template(request: SavePromptRequest):
    """Save a prompt template with field definitions"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Generate ID
        prompt_id = str(uuid.uuid4())
        
        # Create prompt template record
        prompt_data = {
            "id": prompt_id,
            "name": request.name,
            "description": request.description,
            "prompt_text": request.prompt_text,
            "fields": request.fields,
            "stage_type": request.stage_type,
            "tags": request.tags,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_default": False,
            "usage_count": 0
        }
        
        # Insert into prompt_library table
        result = supabase.table("prompt_library").insert(prompt_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save prompt template")
        
        logger.info(
            f"Saved prompt template: {request.name}",
            component="prompt_library",
            prompt_id=prompt_id,
            stage_type=request.stage_type
        )
        
        return {
            "success": True,
            "prompt_id": prompt_id,
            "message": f"Prompt template '{request.name}' saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save prompt template: {e}", component="prompt_library")
        raise HTTPException(status_code=500, detail=f"Failed to save prompt template: {str(e)}")


@router.get("/list/{stage_type}")
async def list_prompt_library(stage_type: str):
    """List all prompt templates for a specific stage type"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get prompts for the stage type
        result = supabase.table("prompt_library")\
            .select("*")\
            .eq("stage_type", stage_type)\
            .order("usage_count", desc=True)\
            .execute()
        
        prompts = result.data if result.data else []
        
        logger.info(
            f"Listed {len(prompts)} prompt templates for stage {stage_type}",
            component="prompt_library",
            stage_type=stage_type,
            count=len(prompts)
        )
        
        return {
            "success": True,
            "prompts": prompts,
            "count": len(prompts)
        }
        
    except Exception as e:
        logger.error(f"Failed to list prompt templates: {e}", component="prompt_library")
        raise HTTPException(status_code=500, detail=f"Failed to list prompt templates: {str(e)}")


@router.get("/get/{prompt_id}")
async def get_prompt_template(prompt_id: str):
    """Get a specific prompt template by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get prompt template
        result = supabase.table("prompt_library")\
            .select("*")\
            .eq("id", prompt_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        # Increment usage count
        supabase.table("prompt_library")\
            .update({"usage_count": result.data["usage_count"] + 1})\
            .eq("id", prompt_id)\
            .execute()
        
        logger.info(
            f"Retrieved prompt template: {result.data['name']}",
            component="prompt_library",
            prompt_id=prompt_id
        )
        
        return {
            "success": True,
            "prompt": result.data
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt template: {e}", component="prompt_library")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt template: {str(e)}")


@router.post("/update/{prompt_id}")
async def update_prompt_template(prompt_id: str, request: SavePromptRequest):
    """Update an existing prompt template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Update prompt template
        update_data = {
            "name": request.name,
            "description": request.description,
            "prompt_text": request.prompt_text,
            "fields": request.fields,
            "stage_type": request.stage_type,
            "tags": request.tags,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("prompt_library")\
            .update(update_data)\
            .eq("id", prompt_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        logger.info(
            f"Updated prompt template: {request.name}",
            component="prompt_library",
            prompt_id=prompt_id
        )
        
        return {
            "success": True,
            "message": f"Prompt template '{request.name}' updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update prompt template: {e}", component="prompt_library")
        raise HTTPException(status_code=500, detail=f"Failed to update prompt template: {str(e)}")


@router.delete("/delete/{prompt_id}")
async def delete_prompt_template(prompt_id: str):
    """Delete a prompt template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Delete prompt template
        result = supabase.table("prompt_library")\
            .delete()\
            .eq("id", prompt_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        logger.info(
            f"Deleted prompt template",
            component="prompt_library",
            prompt_id=prompt_id
        )
        
        return {
            "success": True,
            "message": "Prompt template deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete prompt template: {e}", component="prompt_library")
        raise HTTPException(status_code=500, detail=f"Failed to delete prompt template: {str(e)}")


@router.get("/search")
async def search_prompt_library(query: str, stage_type: Optional[str] = None):
    """Search prompt templates by name or description"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Build query
        query_builder = supabase.table("prompt_library").select("*")
        
        # Filter by stage type if provided
        if stage_type:
            query_builder = query_builder.eq("stage_type", stage_type)
        
        # Search in name and description
        query_builder = query_builder.or_(f"name.ilike.%{query}%,description.ilike.%{query}%")
        
        # Execute query
        result = query_builder.order("usage_count", desc=True).execute()
        
        prompts = result.data if result.data else []
        
        logger.info(
            f"Search found {len(prompts)} prompt templates",
            component="prompt_library",
            query=query,
            stage_type=stage_type,
            count=len(prompts)
        )
        
        return {
            "success": True,
            "prompts": prompts,
            "count": len(prompts)
        }
        
    except Exception as e:
        logger.error(f"Failed to search prompt templates: {e}", component="prompt_library")
        raise HTTPException(status_code=500, detail=f"Failed to search prompt templates: {str(e)}")


# Update FieldDefinition model to support forward references
FieldDefinition.model_rebuild()