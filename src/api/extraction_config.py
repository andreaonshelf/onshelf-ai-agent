"""
Extraction Configuration API
Handles the full extraction configuration from the UI
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import os
from supabase import create_client, Client
from pydantic import BaseModel

from ..config import SystemConfig
from ..utils import logger

router = APIRouter(prefix="/api/extraction", tags=["Extraction Configuration"])

# Initialize Supabase client
config = SystemConfig()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)


class PipelineConfig(BaseModel):
    temperature: float = 0.1
    orchestrator_model: str = "claude-4-opus"
    orchestrator_prompt: Optional[str] = None
    enable_comparison: bool = True
    comparison_threshold: float = 0.85


class StageConfig(BaseModel):
    prompt_id: Optional[str] = None
    prompt_text: str
    fields: List[Dict[str, Any]]
    models: List[str]


class ExtractionConfig(BaseModel):
    system: str = "custom_consensus"
    max_budget: float = 2.00
    pipeline: PipelineConfig
    stages: Dict[str, StageConfig]
    stage_order: List[str]


@router.post("/configure")
async def configure_extraction(queue_item_id: int, config: ExtractionConfig):
    """Configure extraction for a queue item with full settings"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Convert config to dict for storage
        config_dict = config.dict()
        config_dict['created_at'] = datetime.utcnow().isoformat()
        
        # Update queue item with configuration
        update_data = {
            "extraction_config": config_dict,
            "current_extraction_system": config.system,
            "status": "ready",  # Mark as ready for processing
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("ai_extraction_queue").update(update_data).eq("id", queue_item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        logger.info(
            f"Configured extraction for queue item {queue_item_id}",
            component="extraction_config_api",
            system=config.system,
            stages=list(config.stages.keys()),
            budget=config.max_budget
        )
        
        return {
            "success": True,
            "queue_item_id": queue_item_id,
            "configuration": config_dict,
            "message": "Extraction configured successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to configure extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure extraction: {str(e)}")


@router.post("/batch-configure-full")
async def batch_configure_full(request_data: Dict[str, Any]):
    """Configure multiple queue items with full extraction settings"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        item_ids = request_data.get('item_ids', [])
        config_data = request_data.get('extraction_config', {})
        
        if not item_ids:
            raise HTTPException(status_code=400, detail="No items selected")
        
        if not config_data:
            raise HTTPException(status_code=400, detail="No configuration provided")
        
        # Add timestamp
        config_data['created_at'] = datetime.utcnow().isoformat()
        
        # Update all selected items
        successful_updates = []
        failed_updates = []
        
        for item_id in item_ids:
            try:
                update_data = {
                    "extraction_config": config_data,
                    "current_extraction_system": config_data.get('system', 'custom_consensus'),
                    "status": "ready",
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = supabase.table("ai_extraction_queue").update(update_data).eq("id", item_id).execute()
                
                if result.data:
                    successful_updates.append(item_id)
                else:
                    failed_updates.append(item_id)
                    
            except Exception as e:
                logger.error(f"Failed to update item {item_id}: {e}")
                failed_updates.append(item_id)
        
        return {
            "success": len(successful_updates) > 0,
            "updated": successful_updates,
            "failed": failed_updates,
            "total": len(item_ids),
            "configuration": config_data
        }
        
    except Exception as e:
        logger.error(f"Failed to batch configure: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch configure: {str(e)}")


@router.post("/start-extraction")
async def start_extraction_with_config(queue_item_id: int):
    """Start extraction for a configured queue item"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get queue item with configuration
        result = supabase.table("ai_extraction_queue").select("*").eq("id", queue_item_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        queue_item = result.data[0]
        
        if not queue_item.get('extraction_config'):
            raise HTTPException(status_code=400, detail="Queue item has no extraction configuration")
        
        # Update status to trigger processing
        update_data = {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "processing_attempts": (queue_item.get('processing_attempts', 0) + 1)
        }
        
        supabase.table("ai_extraction_queue").update(update_data).eq("id", queue_item_id).execute()
        
        logger.info(
            f"Started extraction for queue item {queue_item_id}",
            component="extraction_config_api",
            system=queue_item['extraction_config'].get('system', 'unknown')
        )
        
        return {
            "success": True,
            "queue_item_id": queue_item_id,
            "message": "Extraction started with configuration"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start extraction: {str(e)}")


@router.get("/config-templates")
async def get_configuration_templates():
    """Get pre-configured extraction templates"""
    
    templates = [
        {
            "id": "high_accuracy",
            "name": "High Accuracy",
            "description": "Best for complex shelves with many products",
            "config": {
                "system": "custom_consensus",
                "max_budget": 3.00,
                "pipeline": {
                    "temperature": 0.1,
                    "orchestrator_model": "claude-4-opus",
                    "enable_comparison": True,
                    "comparison_threshold": 0.90
                }
            }
        },
        {
            "id": "balanced",
            "name": "Balanced",
            "description": "Good balance of speed and accuracy",
            "config": {
                "system": "custom_consensus",
                "max_budget": 2.00,
                "pipeline": {
                    "temperature": 0.1,
                    "orchestrator_model": "claude-4-sonnet",
                    "enable_comparison": True,
                    "comparison_threshold": 0.85
                }
            }
        },
        {
            "id": "fast_budget",
            "name": "Fast & Budget",
            "description": "Quick results at lower cost",
            "config": {
                "system": "langgraph",
                "max_budget": 1.00,
                "pipeline": {
                    "temperature": 0.1,
                    "orchestrator_model": "gpt-4o-mini",
                    "enable_comparison": False,
                    "comparison_threshold": 0.80
                }
            }
        }
    ]
    
    return {"templates": templates}


@router.post("/validate-config")
async def validate_extraction_config(config: ExtractionConfig):
    """Validate extraction configuration before applying"""
    
    issues = []
    warnings = []
    
    # Validate system
    valid_systems = ['custom_consensus', 'langgraph', 'hybrid']
    if config.system not in valid_systems:
        issues.append(f"Invalid system: {config.system}")
    
    # Validate budget
    if config.max_budget < 0.50:
        issues.append("Budget too low, minimum is £0.50")
    elif config.max_budget > 10.00:
        warnings.append("Budget is very high, consider if this is necessary")
    
    # Validate pipeline
    if config.pipeline.temperature < 0 or config.pipeline.temperature > 1:
        issues.append("Temperature must be between 0 and 1")
    
    # Validate stages
    if not config.stages:
        issues.append("At least one stage must be configured")
    
    for stage_id, stage in config.stages.items():
        if not stage.prompt_text:
            issues.append(f"Stage {stage_id} has no prompt text")
        if not stage.models:
            issues.append(f"Stage {stage_id} has no models selected")
        if len(stage.models) > 5:
            warnings.append(f"Stage {stage_id} has many models ({len(stage.models)}), this may be expensive")
    
    # Check stage order
    for stage_id in config.stage_order:
        if stage_id not in config.stages:
            issues.append(f"Stage {stage_id} in order but not configured")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "summary": f"{len(issues)} issues, {len(warnings)} warnings"
    }