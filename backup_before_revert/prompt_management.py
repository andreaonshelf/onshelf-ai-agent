"""
Enhanced Prompt Management API
Uses the unified prompt_templates table with performance tracking
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

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
    """Enhanced prompt template with performance tracking"""
    prompt_id: Optional[str] = None
    template_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    prompt_type: str  # 'extraction', 'structure', 'position', 'quantity', 'detail', 'validation'
    model_type: str = 'universal'  # 'gpt4o', 'claude', 'gemini', 'universal'
    prompt_version: str = '1.0'
    prompt_content: str
    field_definitions: List[Dict[str, Any]]
    tags: List[str] = []
    is_user_created: bool = True
    is_active: bool = True
    performance_score: float = 0.0
    usage_count: int = 0
    correction_rate: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SavePromptRequest(BaseModel):
    """Request to save a prompt template"""
    name: str
    description: Optional[str] = None
    prompt_content: str
    field_definitions: List[Dict[str, Any]]
    prompt_type: str = 'extraction'
    model_type: str = 'universal'
    tags: List[str] = []


@router.post("/save")
async def save_prompt_template(request: SavePromptRequest):
    """Save a user-created prompt template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Generate IDs
        prompt_id = str(uuid.uuid4())
        template_id = f"user_{request.prompt_type}_{int(datetime.utcnow().timestamp())}"
        
        # Create prompt template record
        prompt_data = {
            "prompt_id": prompt_id,
            "template_id": template_id,
            "name": request.name,
            "description": request.description,
            "prompt_type": request.prompt_type,
            "model_type": request.model_type,
            "prompt_version": "1.0",
            "prompt_content": request.prompt_content,
            "field_definitions": request.field_definitions,
            "tags": request.tags,
            "is_user_created": True,
            "is_active": True,
            "performance_score": 0.0,
            "usage_count": 0,
            "correction_rate": 0.0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Insert into prompt_templates table
        result = supabase.table("prompt_templates").insert(prompt_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save prompt template")
        
        logger.info(
            f"Saved prompt template: {request.name}",
            component="prompt_management",
            prompt_id=prompt_id,
            template_id=template_id,
            prompt_type=request.prompt_type
        )
        
        return {
            "success": True,
            "prompt_id": prompt_id,
            "template_id": template_id,
            "message": f"Prompt template '{request.name}' saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to save prompt template: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to save prompt template: {str(e)}")


@router.get("/list/{prompt_type}")
async def list_prompt_templates(prompt_type: str, include_system: bool = True):
    """List all prompt templates for a specific type"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Build query
        query = supabase.table("prompt_templates")\
            .select("*")\
            .eq("prompt_type", prompt_type)\
            .eq("is_active", True)
        
        # Filter by user/system prompts
        if not include_system:
            query = query.eq("is_user_created", True)
        
        # Execute query
        result = query.order("performance_score", desc=True).execute()
        
        prompts = result.data if result.data else []
        
        logger.info(
            f"Listed {len(prompts)} prompt templates for type {prompt_type}",
            component="prompt_management",
            prompt_type=prompt_type,
            count=len(prompts)
        )
        
        return {
            "success": True,
            "prompts": prompts,
            "count": len(prompts)
        }
        
    except Exception as e:
        logger.error(f"Failed to list prompt templates: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to list prompt templates: {str(e)}")


@router.get("/get/{prompt_id}")
async def get_prompt_template(prompt_id: str):
    """Get a specific prompt template by ID"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get prompt template
        result = supabase.table("prompt_templates")\
            .select("*")\
            .eq("prompt_id", prompt_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        # Increment usage count (will be more sophisticated with performance tracking)
        supabase.table("prompt_templates")\
            .update({"usage_count": result.data["usage_count"] + 1})\
            .eq("prompt_id", prompt_id)\
            .execute()
        
        logger.info(
            f"Retrieved prompt template: {result.data['name']}",
            component="prompt_management",
            prompt_id=prompt_id
        )
        
        return {
            "success": True,
            "prompt": result.data
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt template: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt template: {str(e)}")


@router.post("/performance/{prompt_id}")
async def track_prompt_performance(
    prompt_id: str,
    accuracy_score: float,
    had_corrections: bool = False,
    processing_time_ms: Optional[int] = None,
    token_usage: Optional[int] = None,
    api_cost: Optional[float] = None
):
    """Track performance metrics for a prompt template"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current prompt data
        prompt_result = supabase.table("prompt_templates")\
            .select("*")\
            .eq("prompt_id", prompt_id)\
            .single()\
            .execute()
        
        if not prompt_result.data:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        prompt_data = prompt_result.data
        
        # Calculate new performance score (weighted average)
        current_score = prompt_data["performance_score"]
        current_count = prompt_data["usage_count"]
        new_score = (current_score * current_count + accuracy_score) / (current_count + 1)
        
        # Calculate new correction rate
        current_correction_rate = prompt_data["correction_rate"]
        new_correction_rate = (
            (current_correction_rate * current_count + (1.0 if had_corrections else 0.0)) / 
            (current_count + 1)
        )
        
        # Update prompt performance
        update_data = {
            "performance_score": new_score,
            "correction_rate": new_correction_rate,
            "usage_count": current_count + 1
        }
        
        supabase.table("prompt_templates")\
            .update(update_data)\
            .eq("prompt_id", prompt_id)\
            .execute()
        
        # Insert performance record
        performance_data = {
            "prompt_id": prompt_id,
            "accuracy_score": accuracy_score,
            "human_corrections_count": 1 if had_corrections else 0,
            "processing_time_ms": processing_time_ms,
            "token_usage": token_usage,
            "api_cost": api_cost,
            "model_type": prompt_data["model_type"],
            "prompt_type": prompt_data["prompt_type"]
        }
        
        supabase.table("prompt_performance").insert(performance_data).execute()
        
        logger.info(
            f"Tracked performance for prompt: {prompt_data['name']}",
            component="prompt_management",
            prompt_id=prompt_id,
            accuracy_score=accuracy_score,
            new_performance_score=new_score
        )
        
        return {
            "success": True,
            "new_performance_score": new_score,
            "new_correction_rate": new_correction_rate,
            "total_usage_count": current_count + 1
        }
        
    except Exception as e:
        logger.error(f"Failed to track prompt performance: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to track prompt performance: {str(e)}")


@router.get("/best/{prompt_type}/{model_type}")
async def get_best_prompt(
    prompt_type: str,
    model_type: str,
    context_tags: Optional[List[str]] = None
):
    """Get the best performing prompt for a specific type and model"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Try model-specific prompt first
        query = supabase.table("prompt_templates")\
            .select("*")\
            .eq("prompt_type", prompt_type)\
            .eq("model_type", model_type)\
            .eq("is_active", True)\
            .gte("usage_count", 5)  # Only consider prompts with enough usage
        
        # Add context filtering if provided
        if context_tags:
            # This would need a more sophisticated query for array overlap
            # For now, we'll do client-side filtering
            pass
        
        result = query.order("performance_score", desc=True).limit(1).execute()
        
        # If no model-specific prompt, try universal
        if not result.data:
            result = supabase.table("prompt_templates")\
                .select("*")\
                .eq("prompt_type", prompt_type)\
                .eq("model_type", "universal")\
                .eq("is_active", True)\
                .order("performance_score", desc=True)\
                .limit(1)\
                .execute()
        
        if not result.data:
            # Return a default if nothing found
            return {
                "success": False,
                "message": "No suitable prompt template found",
                "prompt": None
            }
        
        prompt = result.data[0]
        
        logger.info(
            f"Retrieved best prompt: {prompt['name']}",
            component="prompt_management",
            prompt_type=prompt_type,
            model_type=model_type,
            performance_score=prompt['performance_score']
        )
        
        return {
            "success": True,
            "prompt": prompt,
            "performance_score": prompt['performance_score'],
            "usage_count": prompt['usage_count']
        }
        
    except Exception as e:
        logger.error(f"Failed to get best prompt: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to get best prompt: {str(e)}")


@router.post("/evolve/{prompt_id}")
async def evolve_prompt_template(prompt_id: str, evolution_reason: str):
    """Create an evolved version of a prompt based on performance data"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current prompt
        result = supabase.table("prompt_templates")\
            .select("*")\
            .eq("prompt_id", prompt_id)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt template not found")
        
        parent_prompt = result.data
        
        # Create new evolved prompt (placeholder - would use AI here)
        new_prompt_id = str(uuid.uuid4())
        new_version = f"{float(parent_prompt['prompt_version']) + 0.1:.1f}"
        
        evolved_prompt = {
            "prompt_id": new_prompt_id,
            "template_id": f"{parent_prompt['template_id']}_v{new_version}",
            "name": f"{parent_prompt['name']} (Evolved)",
            "description": f"Evolved from {parent_prompt['name']}: {evolution_reason}",
            "prompt_type": parent_prompt["prompt_type"],
            "model_type": parent_prompt["model_type"],
            "prompt_version": new_version,
            "prompt_content": parent_prompt["prompt_content"],  # Would be AI-generated
            "field_definitions": parent_prompt["field_definitions"],
            "tags": parent_prompt["tags"] + ["evolved"],
            "is_user_created": False,
            "is_active": False,  # Starts inactive for testing
            "parent_prompt_id": prompt_id,
            "performance_score": 0.0,
            "usage_count": 0,
            "correction_rate": 0.0,
            "created_from_feedback": True
        }
        
        # Insert evolved prompt
        supabase.table("prompt_templates").insert(evolved_prompt).execute()
        
        logger.info(
            f"Created evolved prompt from: {parent_prompt['name']}",
            component="prompt_management",
            parent_prompt_id=prompt_id,
            new_prompt_id=new_prompt_id,
            evolution_reason=evolution_reason
        )
        
        return {
            "success": True,
            "evolved_prompt_id": new_prompt_id,
            "message": f"Created evolved version of '{parent_prompt['name']}'"
        }
        
    except Exception as e:
        logger.error(f"Failed to evolve prompt: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to evolve prompt: {str(e)}")


@router.get("/analytics/summary")
async def get_prompt_analytics():
    """Get analytics summary for all prompts"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get all active prompts with performance data
        result = supabase.table("prompt_templates")\
            .select("*")\
            .eq("is_active", True)\
            .gte("usage_count", 1)\
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "summary": {},
                "top_performers": [],
                "needs_improvement": []
            }
        
        prompts = result.data
        
        # Calculate summary statistics
        summary = {}
        for prompt_type in set(p["prompt_type"] for p in prompts):
            type_prompts = [p for p in prompts if p["prompt_type"] == prompt_type]
            
            summary[prompt_type] = {
                "count": len(type_prompts),
                "avg_performance": sum(p["performance_score"] for p in type_prompts) / len(type_prompts),
                "avg_correction_rate": sum(p["correction_rate"] for p in type_prompts) / len(type_prompts),
                "total_usage": sum(p["usage_count"] for p in type_prompts)
            }
        
        # Find top performers and those needing improvement
        top_performers = sorted(prompts, key=lambda p: p["performance_score"], reverse=True)[:5]
        needs_improvement = [p for p in prompts if p["performance_score"] < 0.7 and p["usage_count"] >= 10]
        
        return {
            "success": True,
            "summary": summary,
            "top_performers": top_performers,
            "needs_improvement": needs_improvement
        }
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}", component="prompt_management")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


# Update FieldDefinition model to support forward references
FieldDefinition.model_rebuild()