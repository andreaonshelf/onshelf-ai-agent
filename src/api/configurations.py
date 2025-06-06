"""
Configuration Management API
Handles saving and loading of extraction configurations using existing prompt_templates table
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import os
from supabase import create_client, Client
from pydantic import BaseModel

from ..utils import logger

router = APIRouter(prefix="/api/configurations", tags=["Configuration Management"])

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)


class ConfigurationData(BaseModel):
    name: str
    description: Optional[str] = None
    system: str
    max_budget: float
    temperature: Optional[float] = None
    orchestrator_model: Optional[str] = None
    orchestrator_prompt: Optional[str] = None
    stages: Dict[str, Any]
    created_by: Optional[str] = None


@router.post("")
async def save_configuration(config: ConfigurationData):
    """Save a named configuration using the existing prompt_templates table"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Use the existing prompt_templates table structure
        # Create an extraction config that stores the full configuration
        extraction_config = {
            "system": config.system,
            "max_budget": config.max_budget,
            "temperature": config.temperature,
            "orchestrator_model": config.orchestrator_model,
            "orchestrator_prompt": config.orchestrator_prompt,
            "stages": config.stages
        }
        
        config_record = {
            "template_id": f"config_{config.name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}",
            "prompt_type": "configuration",
            "model_type": "universal",
            "prompt_version": "1.0",
            "prompt_text": config.orchestrator_prompt or "User-defined configuration",
            "name": config.name,
            "description": config.description or f"User configuration: {config.name}",
            "stage_type": "configuration",
            "extraction_config": extraction_config,
            "is_active": True,
            "is_user_created": True,
            "is_public": False,
            "created_by": config.created_by,
            "tags": ["user_configuration", "dashboard_saved"]
        }
        
        result = supabase.table("prompt_templates").insert(config_record).execute()
        
        return {
            "success": True,
            "message": f"Configuration '{config.name}' saved successfully",
            "config_id": result.data[0]["prompt_id"] if result.data else None
        }
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving configuration: {str(e)}")


@router.get("")
async def list_configurations():
    """List all saved configurations from prompt_templates table"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get configurations from prompt_templates where prompt_type = 'configuration'
        result = supabase.table("prompt_templates").select(
            "prompt_id, name, description, extraction_config, created_at, created_by"
        ).eq("prompt_type", "configuration").eq("is_active", True).execute()
        
        configurations = []
        for row in result.data or []:
            config_data = row.get("extraction_config", {})
            configurations.append({
                "id": row["prompt_id"],
                "name": row["name"],
                "description": row["description"],
                "system": config_data.get("system", "unknown"),
                "max_budget": config_data.get("max_budget", 0),
                "temperature": config_data.get("temperature"),
                "orchestrator_model": config_data.get("orchestrator_model"),
                "created_at": row["created_at"],
                "created_by": row["created_by"]
            })
        
        return configurations
        
    except Exception as e:
        logger.error(f"Error fetching configurations: {e}")
        # Return empty list on error
        return []


@router.get("/{config_id}")
async def get_configuration(config_id: str):
    """Get a specific configuration by ID from prompt_templates table"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", config_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        row = result.data[0]
        config_data = row.get("extraction_config", {})
        
        return {
            "id": row["prompt_id"],
            "name": row["name"],
            "description": row["description"],
            "system": config_data.get("system", "unknown"),
            "max_budget": config_data.get("max_budget", 0),
            "temperature": config_data.get("temperature"),
            "orchestrator_model": config_data.get("orchestrator_model"),
            "orchestrator_prompt": config_data.get("orchestrator_prompt"),
            "stages": config_data.get("stages", {}),
            "created_at": row["created_at"],
            "created_by": row["created_by"]
        }
        
    except Exception as e:
        logger.error(f"Error fetching configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching configuration: {str(e)}")


@router.delete("/{config_id}")
async def delete_configuration(config_id: str):
    """Delete a configuration (soft delete) from prompt_templates table"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        result = supabase.table("prompt_templates").update({
            "is_active": False,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("prompt_id", config_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {"success": True, "message": "Configuration deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting configuration: {str(e)}")


@router.put("/{config_id}")
async def update_configuration(config_id: str, config: ConfigurationData):
    """Update an existing configuration in prompt_templates table"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        extraction_config = {
            "system": config.system,
            "max_budget": config.max_budget,
            "temperature": config.temperature,
            "orchestrator_model": config.orchestrator_model,
            "orchestrator_prompt": config.orchestrator_prompt,
            "stages": config.stages
        }
        
        update_data = {
            "name": config.name,
            "description": config.description,
            "prompt_text": config.orchestrator_prompt or "User-defined configuration",
            "extraction_config": extraction_config,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("prompt_templates").update(update_data).eq("prompt_id", config_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Configuration not found")
        
        return {
            "success": True,
            "message": f"Configuration '{config.name}' updated successfully",
            "config_id": config_id
        }
        
    except Exception as e:
        logger.error(f"Error updating configuration {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")