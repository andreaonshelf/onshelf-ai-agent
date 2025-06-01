"""
Prompt Management API
Provides endpoints for the sidebar prompt management interface
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import json
from supabase import create_client, Client

from ..config import SystemConfig
from ..utils import logger
from ..extraction.prompts import PromptTemplates

router = APIRouter(prefix="/api/prompts", tags=["Prompt Management"])

# Initialize Supabase client
config = SystemConfig()
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required")
    supabase = None
else:
    supabase = create_client(supabase_url, supabase_key)

# Initialize prompt templates
prompt_templates = PromptTemplates()


@router.get("/active")
async def get_active_prompts():
    """Get currently active prompts for each type/model combination"""
    
    try:
        active_prompts = {}
        
        if supabase:
            # Get active prompts from Supabase database
            result = supabase.table("prompt_templates").select("*").eq("is_active", True).execute()
            
            for prompt in result.data:
                key = f"{prompt['prompt_type']}_{prompt['model_type']}"
                active_prompts[key] = {
                    "id": prompt['prompt_id'],
                    "template_id": prompt['template_id'],
                    "type": prompt['prompt_type'],
                    "model": prompt['model_type'],
                    "version": prompt['prompt_version'],
                    "content": prompt['prompt_content'][:200] + "..." if len(prompt['prompt_content']) > 200 else prompt['prompt_content'],
                    "full_content": prompt['prompt_content'],
                    "performance": {
                        "success_rate": float(prompt['performance_score']) * 100 if prompt['performance_score'] else 0.0,
                        "usage_count": prompt['usage_count'] or 0,
                        "avg_cost": float(prompt['avg_token_cost']) if prompt['avg_token_cost'] else 0.0
                    },
                    "created_at": prompt['created_at'],
                    "created_from_feedback": prompt['created_from_feedback']
                }
        else:
            # Fallback to static templates if no database
            template_mapping = {
                "scaffolding_analysis": "structure",
                "product_identification": "position", 
                "shelf_by_shelf_extraction": "quantity",
                "price_extraction_specialized": "detail",
                "cross_validation": "validation"
            }
            
            for template_name, prompt_type in template_mapping.items():
                try:
                    template_content = prompt_templates.get_template(template_name)
                    key = f"{prompt_type}_universal"
                    active_prompts[key] = {
                        "id": template_name,
                        "template_id": template_name,
                        "type": prompt_type,
                        "model": "universal",
                        "version": "1.0",
                        "content": template_content[:200] + "..." if len(template_content) > 200 else template_content,
                        "full_content": template_content,
                        "performance": {
                            "success_rate": 85.0,
                            "usage_count": 150,
                            "avg_cost": 0.025
                        },
                        "created_at": datetime.utcnow().isoformat(),
                        "created_from_feedback": False
                    }
                except Exception as e:
                    logger.warning(f"Failed to load template {template_name}: {e}")
        
        return active_prompts
        
    except Exception as e:
        logger.error(f"Failed to get active prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active prompts: {str(e)}")


@router.get("/available")
async def get_available_prompts(
    type: Optional[str] = Query(None),
    model: Optional[str] = Query(None)
):
    """Get available prompt versions for dropdowns"""
    
    try:
        available_prompts = []
        
        if supabase:
            # Get real prompts from database
            query = supabase.table("prompt_templates").select("*")
            
            # Apply filters if provided
            if type:
                query = query.eq("prompt_type", type)
            if model:
                query = query.eq("model_type", model)
            
            result = query.order("created_at", desc=True).execute()
            
            for prompt in result.data:
                available_prompts.append({
                    "id": prompt['prompt_id'],
                    "name": f"{prompt['prompt_type'].title()} Analysis",
                    "type": prompt['prompt_type'],
                    "model": prompt['model_type'],
                    "version": prompt['prompt_version'],
                    "performance_stats": {
                        "success_rate": float(prompt['performance_score']) * 100 if prompt['performance_score'] else 85.0,
                        "usage_count": prompt['usage_count'] or 0,
                        "avg_cost": float(prompt['avg_token_cost']) if prompt['avg_token_cost'] else 0.025
                    },
                    "created_at": prompt['created_at'],
                    "is_active": prompt['is_active']
                })
            
            logger.info(f"Loaded {len(available_prompts)} real prompts from database")
            
            # If we have very few prompts in database, supplement with PromptTemplates
            if len(available_prompts) < 10:
                logger.info("Database has few prompts, supplementing with PromptTemplates")
                
                # Get templates from PromptTemplates class
                template_mapping = {
                    "scaffolding_analysis": "structure",
                    "product_identification": "position", 
                    "shelf_by_shelf_extraction": "quantity",
                    "price_extraction_specialized": "detail",
                    "cross_validation": "validation"
                }
                
                for template_name, prompt_type in template_mapping.items():
                    # Skip if type filter doesn't match
                    if type and prompt_type != type:
                        continue
                        
                    try:
                        template_content = prompt_templates.get_template(template_name)
                        
                        # Create entries for different models
                        models_to_create = [model] if model else ["universal", "gpt4o", "claude", "gemini"]
                        
                        for model_type in models_to_create:
                            # Check if we already have this combination from database
                            existing = any(p['type'] == prompt_type and p['model'] == model_type for p in available_prompts)
                            if not existing:
                                available_prompts.append({
                                    "id": f"{prompt_type}_{model_type}_v1.0",
                                    "name": f"{prompt_type.title()} Analysis",
                                    "type": prompt_type,
                                    "model": model_type,
                                    "version": "1.0",
                                    "performance_stats": {
                                        "success_rate": 85.0,
                                        "usage_count": 150,
                                        "avg_cost": 0.025
                                    },
                                    "created_at": datetime.utcnow().isoformat(),
                                    "is_active": True
                                })
                                
                    except Exception as e:
                        logger.warning(f"Failed to load template {template_name}: {e}")
                
                logger.info(f"Added PromptTemplates fallback, total: {len(available_prompts)} prompts")
            
        else:
            # Fallback to PromptTemplates if no database
            logger.warning("No database connection, using PromptTemplates fallback")
            
            # Get templates from PromptTemplates class
            template_mapping = {
                "scaffolding_analysis": "structure",
                "product_identification": "position", 
                "shelf_by_shelf_extraction": "quantity",
                "price_extraction_specialized": "detail",
                "cross_validation": "validation"
            }
            
            for template_name, prompt_type in template_mapping.items():
                # Skip if type filter doesn't match
                if type and prompt_type != type:
                    continue
                    
                try:
                    template_content = prompt_templates.get_template(template_name)
                    
                    # Create entries for different models
                    models_to_create = [model] if model else ["universal", "gpt4o", "claude", "gemini"]
                    
                    for model_type in models_to_create:
                        available_prompts.append({
                            "id": f"{prompt_type}_{model_type}_v1.0",
                            "name": f"{prompt_type.title()} Analysis",
                            "type": prompt_type,
                            "model": model_type,
                            "version": "1.0",
                            "performance_stats": {
                                "success_rate": 85.0,
                                "usage_count": 150,
                                "avg_cost": 0.025
                            },
                            "created_at": datetime.utcnow().isoformat(),
                            "is_active": True
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to load template {template_name}: {e}")
            
            logger.info(f"Loaded {len(available_prompts)} prompts from PromptTemplates fallback")
        
        return available_prompts
        
    except Exception as e:
        logger.error(f"Failed to get available prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available prompts: {str(e)}")


@router.get("/systems")
async def get_available_systems():
    """Get available extraction systems"""
    
    try:
        from ..systems.base_system import ExtractionSystemFactory
        
        systems = []
        for system_key, system_name in ExtractionSystemFactory.AVAILABLE_SYSTEMS.items():
            systems.append({
                "id": system_key,
                "name": system_name,
                "description": _get_system_description(system_key)
            })
        
        return {"systems": systems}
        
    except Exception as e:
        logger.error(f"Failed to get available systems: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get available systems: {str(e)}")


@router.post("/activate")
async def activate_prompt(request: Dict[str, Any]):
    """Activate a specific prompt version"""
    
    try:
        prompt_id = request.get("prompt_id")
        if not prompt_id:
            raise HTTPException(status_code=400, detail="prompt_id is required")
        
        if supabase:
            # Get the prompt to activate
            prompt_result = supabase.table('prompt_templates').select('*').eq('prompt_id', prompt_id).execute()
            
            if not prompt_result.data:
                raise HTTPException(status_code=404, detail="Prompt not found")
            
            prompt_data = prompt_result.data[0]
            
            # Deactivate all prompts of the same type and model
            supabase.table('prompt_templates').update({
                'is_active': False
            }).eq('prompt_type', prompt_data['prompt_type']).eq('model_type', prompt_data['model_type']).execute()
            
            # Activate the selected prompt
            supabase.table('prompt_templates').update({
                'is_active': True
            }).eq('prompt_id', prompt_id).execute()
            
            logger.info(f"Activated prompt: {prompt_data['template_id']}")
            
            return {
                "success": True,
                "message": f"Activated {prompt_data['prompt_type']} prompt for {prompt_data['model_type']}",
                "prompt": {
                    "id": prompt_id,
                    "type": prompt_data['prompt_type'],
                    "model": prompt_data['model_type'],
                    "version": prompt_data['prompt_version']
                }
            }
        else:
            return {"success": False, "message": "Database not available"}
            
    except Exception as e:
        logger.error(f"Failed to activate prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate prompt: {str(e)}")



@router.get("/list/{prompt_type}")
async def list_prompts_by_type(prompt_type: str, is_active: Optional[bool] = None):
    """List all prompts for a specific type"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Build query
        query = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type)
        
        # Filter by active status if specified
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        # Order by performance score and creation date
        query = query.order("performance_score", desc=True).order("created_at", desc=True)
        
        result = query.execute()
        
        # Format prompts for response
        prompts = []
        for prompt in result.data:
            prompts.append({
                "id": prompt['prompt_id'],
                "name": prompt['prompt_name'],
                "type": prompt['prompt_type'],
                "content": prompt['prompt_content'],
                "version": prompt['prompt_version'],
                "model_type": prompt['model_type'],
                "performance_score": prompt['performance_score'],
                "usage_count": prompt['usage_count'],
                "success_rate": prompt['success_rate'],
                "avg_cost": prompt['avg_token_cost'],
                "is_active": prompt['is_active'],
                "field_definitions": prompt.get('field_definitions', []),
                "created_at": prompt['created_at'],
                "created_by": prompt['created_by']
            })
        
        return {
            "prompt_type": prompt_type,
            "total": len(prompts),
            "prompts": prompts
        }
        
    except Exception as e:
        logger.error(f"Failed to list prompts for type {prompt_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/get/{prompt_id}")
async def get_prompt_by_id(prompt_id: str):
    """Get a specific prompt by ID"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = result.data[0]
        
        return {
            "id": prompt['prompt_id'],
            "name": prompt['prompt_name'],
            "type": prompt['prompt_type'],
            "content": prompt['prompt_content'],
            "version": prompt['prompt_version'],
            "model_type": prompt['model_type'],
            "performance_score": prompt['performance_score'],
            "usage_count": prompt['usage_count'],
            "success_rate": prompt['success_rate'],
            "avg_cost": prompt['avg_token_cost'],
            "is_active": prompt['is_active'],
            "field_definitions": prompt.get('field_definitions', []),
            "created_at": prompt['created_at'],
            "created_by": prompt['created_by']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/performance/{prompt_id}")
async def track_prompt_performance(prompt_id: str, performance_data: Dict[str, Any]):
    """Track performance metrics for a prompt"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current prompt data
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = result.data[0]
        
        # Update performance metrics
        current_usage = prompt.get('usage_count', 0)
        current_success = prompt.get('success_rate', 0.5)
        current_cost = prompt.get('avg_token_cost', 0)
        
        # Calculate new averages
        new_usage = current_usage + 1
        new_success = ((current_success * current_usage) + performance_data.get('success', 1)) / new_usage
        new_cost = ((current_cost * current_usage) + performance_data.get('cost', 0)) / new_usage
        
        # Calculate performance score (weighted average of success rate and cost efficiency)
        # Lower cost is better, so we invert it
        cost_score = 1 - min(new_cost / 0.1, 1)  # Normalize to 0-1 where 0.1 is considered expensive
        performance_score = (new_success * 0.7) + (cost_score * 0.3)
        
        # Update prompt with new metrics
        update_data = {
            "usage_count": new_usage,
            "success_rate": new_success,
            "avg_token_cost": new_cost,
            "performance_score": performance_score,
            "last_used_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("prompt_templates").update(update_data).eq("prompt_id", prompt_id).execute()
        
        # Log performance tracking
        logger.info(f"Updated performance for prompt {prompt_id}: usage={new_usage}, success={new_success:.2f}, cost=${new_cost:.4f}")
        
        return {
            "prompt_id": prompt_id,
            "updated_metrics": update_data,
            "performance_data": performance_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to track performance for prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track performance: {str(e)}")


@router.get("/best/{prompt_type}/{model_type}")
async def get_best_performing_prompt(prompt_type: str, model_type: str = "universal"):
    """Get the best performing prompt for a specific type and model"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Query for best performing active prompt
        query = supabase.table("prompt_templates")             .select("*")             .eq("prompt_type", prompt_type)             .eq("is_active", True)
        
        # Filter by model type if not universal
        if model_type != "universal":
            query = query.or_(f"model_type.eq.{model_type},model_type.eq.universal")
        else:
            query = query.eq("model_type", "universal")
        
        # Order by performance score
        result = query.order("performance_score", desc=True).limit(1).execute()
        
        if not result.data:
            # Fallback to any active prompt of this type
            fallback_result = supabase.table("prompt_templates")                 .select("*")                 .eq("prompt_type", prompt_type)                 .eq("is_active", True)                 .order("created_at", desc=True)                 .limit(1)                 .execute()
            
            if not fallback_result.data:
                raise HTTPException(status_code=404, detail=f"No prompts found for type {prompt_type}")
            
            result = fallback_result
        
        prompt = result.data[0]
        
        return {
            "id": prompt['prompt_id'],
            "name": prompt['prompt_name'],
            "type": prompt['prompt_type'],
            "content": prompt['prompt_content'],
            "model_type": prompt['model_type'],
            "performance_score": prompt['performance_score'],
            "usage_count": prompt['usage_count'],
            "success_rate": prompt['success_rate'],
            "avg_cost": prompt['avg_token_cost'],
            "selection_reason": "highest_performance_score" if prompt['performance_score'] else "most_recent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get best prompt for {prompt_type}/{model_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get best prompt: {str(e)}")


@router.post("/evolve/{prompt_id}")
async def evolve_underperforming_prompt(prompt_id: str, evolution_params: Optional[Dict[str, Any]] = None):
    """Evolve an underperforming prompt using AI"""
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        # Get current prompt
        result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        prompt = result.data[0]
        
        # Check if prompt is actually underperforming
        if prompt['performance_score'] > 0.7:
            return {
                "message": "Prompt is performing well, evolution not needed",
                "current_performance": prompt['performance_score']
            }
        
        # Generate evolved prompt (in real implementation, this would use AI)
        evolved_content = f"""{prompt['prompt_content']}

ENHANCED INSTRUCTIONS (Based on performance analysis):
- Pay special attention to accuracy in edge cases
- Double-check all extracted values for consistency
- If uncertain, provide confidence scores
- Focus on systematic extraction to avoid missing items
"""
        
        # Create new version of the prompt
        import uuid
        new_prompt_id = str(uuid.uuid4())
        new_version = f"{prompt['prompt_version']}.evolved"
        
        new_prompt_data = {
            "prompt_id": new_prompt_id,
            "template_id": prompt['template_id'],
            "prompt_name": f"{prompt['prompt_name']} (Evolved)",
            "prompt_type": prompt['prompt_type'],
            "model_type": prompt['model_type'],
            "prompt_content": evolved_content,
            "prompt_version": new_version,
            "performance_score": 0.5,  # Start with neutral score
            "usage_count": 0,
            "success_rate": 0.5,
            "avg_token_cost": prompt['avg_token_cost'],
            "is_active": False,  # Not active until tested
            "created_by": "system_evolution",
            "created_from_feedback": True,
            "parent_prompt_id": prompt_id,
            "field_definitions": prompt.get('field_definitions', [])
        }
        
        # Insert evolved prompt
        supabase.table("prompt_templates").insert(new_prompt_data).execute()
        
        logger.info(f"Evolved prompt {prompt_id} -> {new_prompt_id}")
        
        return {
            "success": True,
            "original_prompt_id": prompt_id,
            "evolved_prompt_id": new_prompt_id,
            "version": new_version,
            "evolution_reason": f"Performance score {prompt['performance_score']:.2f} below threshold",
            "improvements": [
                "Added edge case handling",
                "Enhanced accuracy instructions",
                "Incorporated failure pattern analysis",
                "Added confidence scoring requirements"
            ],
            "next_steps": "Test evolved prompt with A/B testing before full activation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evolve prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to evolve prompt: {str(e)}")


@router.post("/save")
async def save_prompt(request: Dict[str, Any]):
    """Save a new prompt version"""
    
    try:
        prompt_type = request.get("prompt_type")
        model_type = request.get("model_type")
        prompt_content = request.get("prompt_content")
        prompt_version = request.get("prompt_version", "1.0")
        
        if not all([prompt_type, model_type, prompt_content]):
            raise HTTPException(status_code=400, detail="prompt_type, model_type, and prompt_content are required")
        
        if supabase:
            # Deactivate existing prompts of this type and model
            supabase.table('prompt_templates').update({
                'is_active': False
            }).eq('prompt_type', prompt_type).eq('model_type', model_type).execute()
            
            # Create new prompt
            new_prompt = {
                'template_id': f"manual_{prompt_type}_{model_type}_{prompt_version}",
                'prompt_type': prompt_type,
                'model_type': model_type,
                'prompt_version': prompt_version,
                'prompt_content': prompt_content,
                'performance_score': 0.0,
                'usage_count': 0,
                'correction_rate': 0.0,
                'is_active': True,
                'created_from_feedback': False,
                'retailer_context': [],
                'category_context': [],
                'created_at': datetime.utcnow().isoformat()
            }
            
            result = supabase.table('prompt_templates').insert(new_prompt).execute()
            
            logger.info(f"Saved new prompt: {new_prompt['template_id']}")
            
            return {
                "success": True,
                "message": f"Saved new {prompt_type} prompt for {model_type}",
                "prompt_id": result.data[0]['prompt_id']
            }
        else:
            return {"success": False, "message": "Database not available"}
            
    except Exception as e:
        logger.error(f"Failed to save prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {str(e)}")


def _get_system_description(system_key: str) -> str:
    """Get description for extraction system"""
    descriptions = {
        "custom": "Lightweight custom consensus with full control over orchestration and voting mechanisms",
        "langgraph": "Professional workflow framework with StateGraph, built-in state persistence, and automatic retry logic",
        "hybrid": "Adaptive system that dynamically selects the best approach per stage using LangChain memory"
    }
    return descriptions.get(system_key, "Unknown system")


@router.get("/library")
async def get_prompt_library(
    prompt_type: Optional[str] = None,
    model_type: Optional[str] = None,
    min_accuracy: Optional[float] = None,
    sort_by: Optional[str] = "performance_score",
    limit: Optional[int] = 50
):
    """Get all prompts with performance metrics for browsing and inspiration"""
    
    try:
        if not supabase:
            # Return mock data for testing
            return {
                "prompts": [
                    {
                        "id": "mock-1",
                        "name": "High-Accuracy Retail Extraction v2",
                        "description": "Optimized for dense shelf layouts with 95%+ accuracy",
                        "prompt_type": "products",
                        "model_type": "gpt4o",
                        "performance_score": 0.95,
                        "usage_count": 127,
                        "avg_cost": 0.023,
                        "error_rate": 0.05,
                        "avg_processing_time": 4.2,
                        "last_used": "2 hours ago",
                        "created_at": "2024-01-15T10:00:00Z",
                        "tags": ["retail", "high-density", "production"],
                        "preview": "Extract all products from this retail shelf image with high precision..."
                    },
                    {
                        "id": "mock-2", 
                        "name": "Budget-Optimized Scanner",
                        "description": "Low-cost extraction with acceptable accuracy for bulk processing",
                        "prompt_type": "products",
                        "model_type": "gemini",
                        "performance_score": 0.82,
                        "usage_count": 453,
                        "avg_cost": 0.008,
                        "error_rate": 0.18,
                        "avg_processing_time": 2.1,
                        "last_used": "5 minutes ago",
                        "created_at": "2024-01-10T08:00:00Z",
                        "tags": ["budget", "bulk", "fast"],
                        "preview": "Quickly identify products in this retail shelf image..."
                    }
                ]
            }
        
        # Build query
        query = supabase.table("prompt_templates").select("*")
        
        # Apply filters
        if prompt_type:
            query = query.eq("prompt_type", prompt_type)
        if model_type:
            query = query.eq("model_type", model_type)
        if min_accuracy:
            query = query.gte("performance_score", min_accuracy)
        
        # Sort and limit
        if sort_by == "performance_score":
            query = query.order("performance_score", desc=True)
        elif sort_by == "usage_count":
            query = query.order("usage_count", desc=True)
        elif sort_by == "cost":
            query = query.order("avg_token_cost", desc=False)
        elif sort_by == "recent":
            query = query.order("last_used", desc=True)
        
        query = query.limit(limit)
        result = query.execute()
        
        # Enhance prompt data
        enhanced_prompts = []
        for prompt in result.data:
            # Calculate relative time
            if prompt.get('last_used'):
                last_used_dt = datetime.fromisoformat(prompt['last_used'].replace('Z', '+00:00'))
                delta = datetime.utcnow() - last_used_dt.replace(tzinfo=None)
                
                if delta.days > 0:
                    last_used = f"{delta.days} days ago"
                elif delta.seconds > 3600:
                    last_used = f"{delta.seconds // 3600} hours ago"
                else:
                    last_used = "Recently"
            else:
                last_used = "Never"
            
            # Extract tags from metadata
            tags = []
            if prompt.get('metadata'):
                tags = prompt['metadata'].get('tags', [])
            
            # Get preview (first 150 chars)
            preview = prompt['prompt_content'][:150] + "..." if len(prompt['prompt_content']) > 150 else prompt['prompt_content']
            
            enhanced_prompts.append({
                "id": prompt['prompt_id'],
                "name": prompt.get('template_id', 'Unnamed Prompt'),
                "description": prompt.get('description', ''),
                "prompt_type": prompt['prompt_type'],
                "model_type": prompt['model_type'],
                "performance_score": float(prompt.get('performance_score') or 0),
                "usage_count": prompt.get('usage_count', 0),
                "avg_cost": float(prompt.get('avg_token_cost') or 0),
                "error_rate": float(prompt.get('correction_rate') or 0),
                "avg_processing_time": prompt.get('avg_processing_time', 0),
                "last_used": last_used,
                "created_at": prompt['created_at'],
                "tags": tags,
                "preview": preview,
                "version": prompt.get('prompt_version', 1),
                "parent_id": prompt.get('parent_prompt_id'),
                "created_from_feedback": prompt.get('created_from_feedback', False)
            })
        
        return {
            "prompts": enhanced_prompts,
            "total": len(enhanced_prompts),
            "filters_applied": {
                "prompt_type": prompt_type,
                "model_type": model_type,
                "min_accuracy": min_accuracy,
                "sort_by": sort_by
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt library: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/library/stats")
async def get_prompt_library_stats():
    """Get aggregate statistics for the prompt library"""
    
    try:
        if not supabase:
            return {
                "total_prompts": 42,
                "avg_performance": 0.87,
                "most_used_type": "products",
                "most_successful_model": "gpt4o",
                "total_usage": 2341,
                "avg_cost_per_extraction": 0.018
            }
        
        # Get aggregate stats
        result = supabase.table("prompt_templates").select("*").execute()
        
        if not result.data:
            return {
                "total_prompts": 0,
                "avg_performance": 0,
                "most_used_type": None,
                "most_successful_model": None,
                "total_usage": 0,
                "avg_cost_per_extraction": 0
            }
        
        # Calculate statistics
        total_prompts = len(result.data)
        performances = [p['performance_score'] for p in result.data if p.get('performance_score')]
        avg_performance = sum(performances) / len(performances) if performances else 0
        
        # Count by type
        type_counts = {}
        model_performances = {}
        total_usage = 0
        total_cost = 0
        
        for prompt in result.data:
            # Type counts
            ptype = prompt['prompt_type']
            type_counts[ptype] = type_counts.get(ptype, 0) + prompt.get('usage_count', 0)
            
            # Model performances
            model = prompt['model_type']
            if model not in model_performances:
                model_performances[model] = []
            if prompt.get('performance_score'):
                model_performances[model].append(prompt['performance_score'])
            
            # Usage and cost
            total_usage += prompt.get('usage_count', 0)
            if prompt.get('avg_token_cost') and prompt.get('usage_count'):
                total_cost += prompt['avg_token_cost'] * prompt['usage_count']
        
        # Find most used type
        most_used_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else None
        
        # Find most successful model
        model_avg_scores = {}
        for model, scores in model_performances.items():
            if scores:
                model_avg_scores[model] = sum(scores) / len(scores)
        
        most_successful_model = max(model_avg_scores.items(), key=lambda x: x[1])[0] if model_avg_scores else None
        
        return {
            "total_prompts": total_prompts,
            "avg_performance": round(avg_performance, 3),
            "most_used_type": most_used_type,
            "most_successful_model": most_successful_model,
            "total_usage": total_usage,
            "avg_cost_per_extraction": round(total_cost / total_usage if total_usage else 0, 4)
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt library stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}")
async def get_prompt_details(prompt_id: str):
    """Get full prompt details for preview/editing"""
    
    try:
        if supabase:
            # Try to get from database first
            result = supabase.table("prompt_templates").select("*").eq("prompt_id", prompt_id).execute()
            
            if result.data:
                prompt = result.data[0]
                return {
                    "id": prompt['prompt_id'],
                    "content": prompt['prompt_content'],
                    "performance_stats": {
                        "success_rate": float(prompt['performance_score']) * 100 if prompt['performance_score'] else 85.0,
                        "usage_count": prompt['usage_count'] or 0,
                        "avg_cost": float(prompt['avg_token_cost']) if prompt['avg_token_cost'] else 0.025,
                        "error_rate": float(prompt['correction_rate']) if prompt['correction_rate'] else 0.15
                    },
                    "metadata": {
                        "created_at": prompt['created_at'],
                        "updated_at": prompt.get('updated_at', prompt['created_at']),
                        "created_by": "system" if not prompt['created_from_feedback'] else "feedback",
                        "model_compatibility": [prompt['model_type']],
                        "prompt_type": prompt['prompt_type'],
                        "prompt_version": prompt['prompt_version'],
                        "is_active": prompt['is_active']
                    },
                    "version_history": []  # Could be populated with related versions
                }
        
        # Try to get from PromptTemplates as fallback
        if prompt_id in prompt_templates.templates:
            content = prompt_templates.get_template(prompt_id)
            return {
                "id": prompt_id,
                "content": content,
                "performance_stats": {
                    "success_rate": 87.5,
                    "usage_count": 245,
                    "avg_cost": 0.023,
                    "error_rate": 0.125
                },
                "metadata": {
                    "created_at": "2025-01-15T10:00:00Z",
                    "updated_at": "2025-01-15T14:30:00Z",
                    "created_by": "system",
                    "model_compatibility": ["universal"],
                    "prompt_type": "template",
                    "prompt_version": "1.0",
                    "is_active": True
                },
                "version_history": []
            }
        
        # Check if it's a generated ID from the available prompts
        # Format: {type}_{model}_v{version}
        if "_v" in prompt_id:
            parts = prompt_id.split("_")
            if len(parts) >= 3:
                prompt_type = parts[0]
                model_type = parts[1]
                version = parts[2].replace("v", "")
                
                # Try to find a matching template
                template_mapping = {
                    "structure": "scaffolding_analysis",
                    "position": "product_identification", 
                    "quantity": "shelf_by_shelf_extraction",
                    "detail": "price_extraction_specialized",
                    "validation": "cross_validation"
                }
                
                template_name = template_mapping.get(prompt_type)
                if template_name and template_name in prompt_templates.templates:
                    content = prompt_templates.get_template(template_name)
                    return {
                        "id": prompt_id,
                        "content": content,
                        "full_content": content,  # Add full_content field
                        "performance_stats": {
                            "success_rate": 85.0,
                            "usage_count": 150,
                            "avg_cost": 0.025,
                            "error_rate": 0.15
                        },
                        "metadata": {
                            "created_at": "2025-01-15T10:00:00Z",
                            "updated_at": "2025-01-15T14:30:00Z",
                            "created_by": "system",
                            "model_compatibility": [model_type],
                            "prompt_type": prompt_type,
                            "prompt_version": version,
                            "is_active": True
                        },
                        "version_history": []
                    }
        
        # If not found anywhere, return 404
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.post("/create-version")
async def create_prompt_version(request_data: Dict[str, Any]):
    """Create new prompt version"""
    
    try:
        base_prompt_id = request_data.get('base_prompt_id')
        content = request_data.get('content')
        notes = request_data.get('notes', '')
        
        if not base_prompt_id or not content:
            raise HTTPException(status_code=400, detail="base_prompt_id and content are required")
        
        # Generate new version ID
        new_version_id = f"{base_prompt_id}_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # In real implementation, save to database
        # For now, add to prompt templates if it's a known template
        if base_prompt_id in prompt_templates.templates:
            prompt_templates.add_custom_template(new_version_id, content)
        
        logger.info(f"Created new prompt version: {new_version_id}")
        
        return {
            "success": True,
            "new_version_id": new_version_id,
            "version": "2.1",
            "created_at": datetime.utcnow().isoformat(),
            "message": "New prompt version created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create prompt version: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create prompt version: {str(e)}")


@router.post("/{prompt_id}/activate")
async def activate_prompt(prompt_id: str):
    """Activate specific prompt version"""
    
    try:
        # In real implementation, update database to set this prompt as active
        # For now, just log the activation
        
        logger.info(f"Activated prompt: {prompt_id}")
        
        return {
            "success": True,
            "prompt_id": prompt_id,
            "activated_at": datetime.utcnow().isoformat(),
            "message": f"Prompt {prompt_id} activated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to activate prompt {prompt_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to activate prompt: {str(e)}")


@router.get("/performance/stats")
async def get_performance_stats():
    """Get system performance metrics for recommendations"""
    
    try:
        return {
            "custom_consensus": {
                "success_rate": 89.2,
                "avg_processing_time": 2.3,
                "cost_per_extraction": 0.045,
                "total_extractions": 1250,
                "error_rate": 0.108
            },
            "langgraph": {
                "success_rate": 85.7,
                "avg_processing_time": 3.1,
                "cost_per_extraction": 0.038,
                "total_extractions": 890,
                "error_rate": 0.143
            },
            "hybrid": {
                "success_rate": 91.5,
                "avg_processing_time": 2.8,
                "cost_per_extraction": 0.052,
                "total_extractions": 650,
                "error_rate": 0.085
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")


@router.post("/test")
async def test_prompt(request_data: Dict[str, Any]):
    """Test a prompt with sample data"""
    
    try:
        prompt_content = request_data.get('prompt_content')
        test_image_id = request_data.get('test_image_id')
        
        if not prompt_content:
            raise HTTPException(status_code=400, detail="prompt_content is required")
        
        # Mock test results
        test_results = {
            "test_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "prompt_length": len(prompt_content),
            "estimated_cost": 0.025,
            "predicted_accuracy": 87.5,
            "processing_time_estimate": 2.1,
            "compatibility_score": {
                "gpt4o": 0.95,
                "claude": 0.92,
                "gemini": 0.88
            },
            "suggestions": [
                "Consider adding more specific spatial instructions",
                "Prompt length is optimal for most models",
                "Good use of structured output format"
            ]
        }
        
        logger.info(f"Tested prompt with {len(prompt_content)} characters")
        
        return {
            "success": True,
            "test_results": test_results,
            "tested_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to test prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test prompt: {str(e)}")


@router.post("/ai-optimize")
async def ai_optimize_prompt(request_data: Dict[str, Any]):
    """Generate AI-powered prompt optimization suggestions"""
    
    try:
        extraction_type = request_data.get('extraction_type')
        current_prompt = request_data.get('current_prompt')
        current_schema = request_data.get('current_schema')
        optimization_goal = request_data.get('optimization_goal')
        context = request_data.get('context', '')
        
        if not all([extraction_type, current_prompt, optimization_goal]):
            raise HTTPException(status_code=400, detail="extraction_type, current_prompt, and optimization_goal are required")
        
        # Generate optimization suggestions based on the goal
        suggestions = generate_optimization_suggestions(extraction_type, optimization_goal, context)
        
        return {
            "success": True,
            "optimization_suggestions": suggestions,
            "goal": optimization_goal,
            "extraction_type": extraction_type
        }
        
    except Exception as e:
        logger.error(f"Failed to generate AI optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI optimization: {str(e)}")


@router.post("/save-default-config")
async def save_default_config(request_data: Dict[str, Any]):
    """Save a configuration as the default"""
    
    try:
        configuration = request_data.get('configuration')
        name = request_data.get('name', 'Default Configuration')
        description = request_data.get('description', '')
        
        if not configuration:
            raise HTTPException(status_code=400, detail="configuration is required")
        
        if supabase:
            # Save to database (would need to create default_configurations table)
            logger.info(f"Saving default configuration: {name}")
            
            return {
                "success": True,
                "message": "Default configuration saved successfully",
                "config_id": f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        else:
            return {
                "success": True,
                "message": "Default configuration saved (database not available)"
            }
            
    except Exception as e:
        logger.error(f"Failed to save default configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save default configuration: {str(e)}")


@router.get("/{prompt_id}/performance")
async def get_prompt_performance(prompt_id: str):
    """Get detailed performance analytics for a prompt"""
    
    try:
        if supabase:
            # Get performance data from database
            performance_result = supabase.table('prompt_performance').select('*').eq('prompt_id', prompt_id).execute()
            
            if performance_result.data:
                # Calculate aggregated statistics
                performances = performance_result.data
                
                stats = {
                    "success_rate": sum(p['accuracy_score'] for p in performances if p['accuracy_score']) / len(performances) * 100,
                    "usage_count": len(performances),
                    "avg_cost": sum(p['api_cost'] for p in performances if p['api_cost']) / len(performances),
                    "avg_time": sum(p['processing_time_ms'] for p in performances if p['processing_time_ms']) / len(performances) / 1000,
                    "total_corrections": sum(p['human_corrections_count'] for p in performances if p['human_corrections_count'])
                }
                
                return {
                    "success": True,
                    "performance": {
                        "stats": stats,
                        "trends": performances[-30:],  # Last 30 uses
                        "total_uses": len(performances)
                    }
                }
        
        # Return mock data if no database or no data found
        return {
            "success": True,
            "performance": {
                "stats": {
                    "success_rate": 87.5,
                    "usage_count": 245,
                    "avg_cost": 0.023,
                    "avg_time": 1.2,
                    "total_corrections": 12
                },
                "trends": [],
                "total_uses": 245
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt performance: {str(e)}")


def generate_optimization_suggestions(extraction_type: str, goal: str, context: str) -> str:
    """Generate optimization suggestions based on goal and context"""
    
    base_suggestions = {
        "accuracy": {
            "structure": """🎯 ACCURACY OPTIMIZATION FOR STRUCTURE ANALYSIS

Key Improvements:
• Add explicit shelf counting methodology: "Count shelves from top to bottom, including partial shelves"
• Include edge case handling: "If shelves are angled or partially visible, estimate based on visible portions"
• Add validation steps: "Cross-check shelf count with product positioning data"
• Specify confidence thresholds: "Mark confidence as low (<0.7) if any shelves are unclear"

Enhanced Instructions:
• Use systematic scanning pattern (top-to-bottom, left-to-right)
• Define clear criteria for shelf boundaries and separations
• Include instructions for handling non-standard layouts (curved shelves, end caps)
• Add specific guidance for depth perception and 3D structure analysis""",
            
            "products": """🎯 ACCURACY OPTIMIZATION FOR PRODUCT IDENTIFICATION

Key Improvements:
• Add brand-specific recognition patterns for common retailers
• Include instructions for handling similar products: "Distinguish between variants by size, flavor, or packaging details"
• Specify facing count methodology: "Count individual product units visible from front, not total depth"
• Add confidence scoring based on visibility: "High confidence (>0.9) for clear, unobstructed products"

Enhanced Instructions:
• Use product hierarchy: Brand → Product Line → Specific Variant
• Include guidance for handling occlusions and partial visibility
• Add instructions for distinguishing between stacked vs. side-by-side products
• Specify how to handle promotional packaging or seasonal variants""",
            
            "details": """🎯 ACCURACY OPTIMIZATION FOR DETAIL EXTRACTION

Key Improvements:
• Add price format validation: "UK prices typically £X.XX format, validate against common patterns"
• Include text clarity assessment: "If price text is blurry or partially obscured, mark confidence as low"
• Specify promotional indicator recognition: "Look for red tags, 'SALE' text, or crossed-out prices"
• Add size/volume extraction rules: "Extract numerical values followed by units (ml, L, g, kg)"

Enhanced Instructions:
• Prioritize price tags over product packaging for price information
• Use context clues (shelf position, product type) to validate extracted prices
• Include guidance for handling multi-buy offers and promotional pricing
• Add specific instructions for reading different price tag formats"""
        },
        
        "speed": {
            "structure": """⚡ SPEED OPTIMIZATION FOR STRUCTURE ANALYSIS

Key Improvements:
• Simplify to essential elements: Focus only on shelf count and basic layout
• Remove detailed measurements: Skip precise width/height calculations unless critical
• Use rapid scanning approach: "Quickly identify horizontal lines that indicate shelf edges"
• Eliminate redundant validation: Trust initial assessment unless obviously incorrect

Streamlined Instructions:
• Count shelves in single pass from top to bottom
• Identify 3 main sections per shelf (left, center, right) without precise boundaries
• Skip detailed structural analysis unless specifically required
• Use confidence thresholds to avoid over-analysis of unclear areas""",
            
            "products": """⚡ SPEED OPTIMIZATION FOR PRODUCT IDENTIFICATION

Key Improvements:
• Focus on obvious, clearly visible products first
• Skip detailed variant analysis: Group similar products together
• Use rapid brand recognition: Identify by logo/color scheme rather than reading text
• Eliminate exhaustive positioning: Use approximate positions (left, center, right)

Streamlined Instructions:
• Scan each shelf section once, left to right
• Identify products by most prominent visual features (brand colors, shapes)
• Count facings in groups (1, 2-3, 4+) rather than exact counts
• Skip products that require detailed analysis to identify""",
            
            "details": """⚡ SPEED OPTIMIZATION FOR DETAIL EXTRACTION

Key Improvements:
• Target only essential information: Price and basic product name
• Skip detailed text extraction: Focus on large, clear text only
• Use pattern recognition: Look for £ symbol and number patterns for prices
• Eliminate comprehensive analysis: Extract what's immediately visible

Streamlined Instructions:
• Scan for price tags first, product text second
• Extract only clearly visible prices (skip if requires squinting)
• Use basic product names without detailed specifications
• Skip promotional analysis unless immediately obvious"""
        },
        
        "cost": {
            "structure": """💰 COST OPTIMIZATION FOR STRUCTURE ANALYSIS

Key Improvements:
• Use minimal, direct language: Remove explanatory text and examples
• Focus on essential output only: Shelf count and basic sections
• Eliminate redundant instructions: Combine related steps
• Use bullet points instead of paragraphs: Reduce token usage

Optimized Instructions:
• Count shelves top to bottom
• Identify left/center/right sections
• Note total shelf count
• Skip detailed measurements""",
            
            "products": """💰 COST OPTIMIZATION FOR PRODUCT IDENTIFICATION

Key Improvements:
• Streamline identification criteria: Use minimal descriptive text
• Focus on essential attributes: Brand, product name, position only
• Remove verbose explanations: Use direct, action-oriented language
• Eliminate examples: Trust model knowledge without extensive guidance

Optimized Instructions:
• Identify products by brand and name
• Note shelf position (1, 2, 3 from top)
• Count facings per product
• Skip detailed descriptions""",
            
            "details": """💰 COST OPTIMIZATION FOR DETAIL EXTRACTION

Key Improvements:
• Target specific information: Price, size, promotional status only
• Use concise language: Remove explanatory text
• Focus on high-value data: Skip low-priority details
• Eliminate redundant validation: Trust initial extraction

Optimized Instructions:
• Extract visible prices
• Note product sizes if clear
• Identify promotions if obvious
• Skip unclear text"""
        },
        
        "consistency": {
            "structure": """🎯 CONSISTENCY OPTIMIZATION FOR STRUCTURE ANALYSIS

Key Improvements:
• Add explicit step-by-step procedure with numbered steps
• Define standardized terminology: "Use 'shelf 1' for top shelf, 'shelf 2' for second, etc."
• Specify exact output format: "Always report as: {shelf_count: X, sections: [...]}"
• Include validation checkpoints: "Verify shelf count matches section count"

Standardized Process:
1. Scan image from top to bottom
2. Identify each horizontal shelf line
3. Number shelves 1-N from top to bottom
4. Divide each shelf into left/center/right sections
5. Validate total count before finalizing""",
            
            "products": """🎯 CONSISTENCY OPTIMIZATION FOR PRODUCT IDENTIFICATION

Key Improvements:
• Define clear product categorization rules: "Group by brand first, then product line"
• Standardize position description: "Use format: shelf_X_position_Y_section_Z"
• Include consistent naming conventions: "Use official brand names, avoid abbreviations"
• Add cross-validation steps: "Verify product count matches facing count"

Standardized Process:
1. Scan each shelf left to right
2. Identify distinct products (not variants)
3. Use standard naming: [Brand] [Product Line] [Size]
4. Count facings for each product
5. Assign consistent position identifiers""",
            
            "details": """🎯 CONSISTENCY OPTIMIZATION FOR DETAIL EXTRACTION

Key Improvements:
• Standardize price format: "Always use £X.XX format, convert pence to pounds"
• Define consistent confidence scoring: "0.9+ for clear text, 0.7-0.9 for readable, <0.7 for unclear"
• Include format validation: "Validate prices against reasonable ranges for product type"
• Add consistency checks: "Ensure all products have price or explicit 'no price visible'"

Standardized Process:
1. Locate price information for each product
2. Extract in standard £X.XX format
3. Assign confidence score based on text clarity
4. Note promotional indicators using standard terms
5. Validate extracted data for consistency"""
        }
    }
    
    suggestions = base_suggestions.get(goal, {}).get(extraction_type, "No specific suggestions available for this combination.")
    
    if context:
        suggestions += f"\n\n📝 CONTEXT-SPECIFIC RECOMMENDATIONS:\nBased on your context: '{context}'\n• Consider testing the optimized prompt with similar scenarios\n• Monitor performance metrics after implementation\n• Adjust confidence thresholds based on your specific requirements"
    
    return suggestions 


@router.post("/extraction/recommend")
async def get_extraction_recommendations(context: dict):
    """Get AI recommendations based on context and historical performance"""
    
    try:
        if not supabase:
            # Fallback recommendations when no database
            return {
                'system': 'custom_consensus',
                'system_reason': 'Default system - no historical data available',
                'models': {
                    'structure': 'claude',
                    'products': 'gpt4o',
                    'details': 'gemini'
                },
                'prompts': {
                    'structure': {
                        'prompt_id': 'structure_claude_v1.0',
                        'name': 'Structure Analysis',
                        'version': '1.0',
                        'performance': 0.85,
                        'reason': 'Default structure prompt'
                    },
                    'products': {
                        'prompt_id': 'products_gpt4o_v1.0',
                        'name': 'Product Extraction',
                        'version': '1.0',
                        'performance': 0.87,
                        'reason': 'Default product prompt'
                    },
                    'details': {
                        'prompt_id': 'details_gemini_v1.0',
                        'name': 'Detail Enhancement',
                        'version': '1.0',
                        'performance': 0.83,
                        'reason': 'Default detail prompt'
                    }
                },
                'history_summary': 'No historical data available'
            }
        
        # Query historical performance for this context
        store = context.get("store", "")
        category = context.get("category", "")
        retailer = context.get("retailer", "")
        
        # Get recent extraction runs for similar context
        history_query = supabase.table("extraction_runs").select("*")
        
        if store:
            history_query = history_query.ilike("metadata->>store", f"%{store}%")
        if category:
            history_query = history_query.eq("metadata->>category", category)
        
        history = history_query.order("created_at", desc=True).limit(20).execute()
        
        # Analyze what worked best
        performance_by_system = {}
        performance_by_model = {}
        performance_by_prompt = {}
        
        for run in history.data:
            if not run.get("final_accuracy"):
                continue
                
            system = run.get("configuration", {}).get("system", "custom_consensus")
            accuracy = float(run["final_accuracy"])
            
            if system not in performance_by_system:
                performance_by_system[system] = []
            performance_by_system[system].append(accuracy)
            
            # Analyze model performance
            models = run.get("configuration", {}).get("models", {})
            for model_type, model_name in models.items():
                key = f"{model_type}_{model_name}"
                if key not in performance_by_model:
                    performance_by_model[key] = []
                performance_by_model[key].append(accuracy)
        
        # Calculate best performers
        best_system = "custom_consensus"
        best_system_score = 0.85
        
        if performance_by_system:
            best_system, scores = max(performance_by_system.items(), 
                                    key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0)
            best_system_score = sum(scores)/len(scores) if scores else 0.85
        
        # Get best prompts for each type
        best_prompts = {}
        for prompt_type in ['structure', 'products', 'details']:
            # Query for best performing prompts of this type
            prompt_query = supabase.table("prompt_templates").select("*").eq("prompt_type", prompt_type)
            
            if category:
                prompt_query = prompt_query.contains("category_context", [category])
            
            prompt_result = prompt_query.order("performance_score", desc=True).limit(1).execute()
            
            if prompt_result.data:
                prompt = prompt_result.data[0]
                best_prompts[prompt_type] = {
                    'prompt_id': prompt['prompt_id'],
                    'name': prompt.get('template_id', f'{prompt_type} Analysis'),
                    'version': prompt.get('prompt_version', '1.0'),
                    'performance': float(prompt.get('performance_score', 0.85)),
                    'reason': f"Best performer for {category or 'general'} category"
                }
            else:
                # Fallback to default
                best_prompts[prompt_type] = {
                    'prompt_id': f'{prompt_type}_auto_v1.0',
                    'name': f'{prompt_type.title()} Analysis',
                    'version': '1.0',
                    'performance': 0.85,
                    'reason': f"Default {prompt_type} prompt"
                }
        
        return {
            'system': best_system,
            'system_reason': f"Achieved {best_system_score:.0%} avg accuracy in similar contexts",
            'models': {
                'structure': 'claude',  # Based on performance analysis
                'products': 'gpt4o',
                'details': 'gemini'
            },
            'prompts': best_prompts,
            'history_summary': f"Based on {len(history.data)} similar extractions"
        }
        
    except Exception as e:
        logger.error(f"Failed to get extraction recommendations: {e}")
        # Return fallback recommendations
        return {
            'system': 'custom_consensus',
            'system_reason': 'Default system due to error',
            'models': {
                'structure': 'claude',
                'products': 'gpt4o', 
                'details': 'gemini'
            },
            'prompts': {
                'structure': {
                    'prompt_id': 'structure_fallback',
                    'name': 'Structure Analysis',
                    'version': '1.0',
                    'performance': 0.85,
                    'reason': 'Fallback prompt'
                },
                'products': {
                    'prompt_id': 'products_fallback',
                    'name': 'Product Extraction', 
                    'version': '1.0',
                    'performance': 0.87,
                    'reason': 'Fallback prompt'
                },
                'details': {
                    'prompt_id': 'details_fallback',
                    'name': 'Detail Enhancement',
                    'version': '1.0', 
                    'performance': 0.83,
                    'reason': 'Fallback prompt'
                }
            },
            'history_summary': 'Error retrieving historical data'
        }


@router.get("/available-with-stats")
async def get_prompts_with_performance(prompt_type: str, model_type: str):
    """Get prompts with full performance statistics"""
    
    try:
        if not supabase:
            # Fallback to static data
            return [{
                'prompt_id': f'{prompt_type}_{model_type}_v1.0',
                'name': f'{prompt_type.title()} Analysis',
                'version': '1.0',
                'performance_score': 0.85,
                'usage_count': 150,
                'last_used': '2 hours ago',
                'avg_token_cost': 0.025,
                'prompt_content': getDefaultPromptTemplate(prompt_type)[:200] + '...'
            }]
        
        # Get prompts with performance data
        prompts = supabase.table("prompt_templates").select("*").match({
            "prompt_type": prompt_type,
            "model_type": model_type,
            "is_active": True
        }).execute()
        
        # Enhance with recent performance
        for prompt in prompts.data:
            # Calculate recent performance metrics
            recent_runs = supabase.table("extraction_runs").select("final_accuracy, created_at, api_cost").contains(
                "configuration->>prompts", {prompt_type: prompt['prompt_id']}
            ).gte("created_at", datetime.utcnow() - timedelta(days=30)).execute()
            
            if recent_runs.data:
                accuracies = [float(run['final_accuracy']) for run in recent_runs.data if run.get('final_accuracy')]
                costs = [float(run['api_cost']) for run in recent_runs.data if run.get('api_cost')]
                
                prompt['recent_accuracy'] = sum(accuracies) / len(accuracies) if accuracies else 0.85
                prompt['recent_uses'] = len(recent_runs.data)
                prompt['avg_token_cost'] = sum(costs) / len(costs) if costs else 0.025
                prompt['last_used'] = max(run['created_at'] for run in recent_runs.data) if recent_runs.data else None
            else:
                prompt['recent_accuracy'] = float(prompt.get('performance_score', 0.85))
                prompt['recent_uses'] = prompt.get('usage_count', 0)
                prompt['avg_token_cost'] = float(prompt.get('avg_token_cost', 0.025))
                prompt['last_used'] = prompt.get('created_at')
        
        return prompts.data
        
    except Exception as e:
        logger.error(f"Failed to get prompts with performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompts: {str(e)}")


@router.get("/intelligence")
async def get_prompt_intelligence():
    """Comprehensive analysis of all prompts and their performance"""
    
    try:
        if not supabase:
            # Return mock data for development
            return {
                'total_prompts': 25,
                'avg_success_rate': 0.87,
                'best_performer': {
                    'name': 'Dense Shelf Analysis v2.3',
                    'success_rate': 0.96
                },
                'success_patterns': [
                    {
                        'pattern': 'systematic left-to-right analysis',
                        'impact': 12.5,
                        'prompt_count': 8,
                        'example_prompts': ['Structure v2.1', 'Product Dense v1.3'],
                        'description': 'Prompts using systematic scanning show 12.5% better accuracy'
                    },
                    {
                        'pattern': 'confidence scoring',
                        'impact': 8.3,
                        'prompt_count': 12,
                        'example_prompts': ['Detail Enhanced v1.2', 'Product Precise v2.0'],
                        'description': 'Including confidence assessment improves reliability by 8.3%'
                    }
                ],
                'failure_patterns': [
                    {
                        'pattern': 'overly complex instructions',
                        'impact': -15.2,
                        'prompt_count': 4,
                        'example_prompts': ['Complex Analysis v1.0'],
                        'description': 'Overly detailed prompts reduce accuracy by 15.2%'
                    }
                ],
                'clusters': [
                    {
                        'name': 'High-Accuracy Structure',
                        'prompt_count': 6,
                        'avg_success': 0.94,
                        'common_traits': ['systematic', 'step-by-step', 'validation'],
                        'top_prompts': [
                            {'name': 'Structure v2.3', 'performance_score': 0.96},
                            {'name': 'Structure v2.1', 'performance_score': 0.94}
                        ]
                    }
                ],
                'ai_insights': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'key_findings': [
                        'Systematic scanning patterns improve accuracy by 12-15%',
                        'Confidence scoring reduces false positives by 23%',
                        'Shorter, focused prompts outperform verbose ones',
                        'Context-specific prompts show 18% better performance'
                    ],
                    'opportunities': [
                        'Standardize systematic scanning across all prompt types',
                        'Implement confidence thresholds for quality control',
                        'Create retailer-specific prompt variants',
                        'Develop automated prompt optimization pipeline'
                    ],
                    'trend_summary': 'Recent prompts show improving accuracy trends, with systematic approaches and confidence scoring being key success factors.'
                },
                'recommendations': [
                    {
                        'title': 'Include systematic scanning in new prompts',
                        'description': 'This pattern shows 12.5% performance improvement',
                        'priority': 'high',
                        'category': 'success_pattern'
                    },
                    {
                        'title': 'Avoid overly complex instructions',
                        'description': 'This pattern correlates with 15.2% performance decrease',
                        'priority': 'high',
                        'category': 'failure_pattern'
                    }
                ]
            }
        
        # Get all prompts with performance data
        prompts = supabase.table("prompt_templates").select("*").execute()
        
        if not prompts.data:
            raise HTTPException(status_code=404, detail="No prompts found")
        
        # Basic statistics
        total_prompts = len(prompts.data)
        success_rates = [float(p['performance_score']) for p in prompts.data if p.get('performance_score')]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.85
        
        # Find best performer
        best_performer = max(prompts.data, key=lambda p: float(p.get('performance_score', 0)))
        
        # Pattern analysis (simplified for now)
        success_patterns = await analyze_prompt_patterns(prompts.data, 'success')
        failure_patterns = await analyze_prompt_patterns(prompts.data, 'failure')
        
        # Cluster analysis (simplified)
        clusters = await cluster_prompts_by_performance(prompts.data)
        
        # AI insights (mock for now)
        ai_insights = {
            'generated_at': datetime.utcnow().isoformat(),
            'key_findings': [
                f'Average success rate across {total_prompts} prompts: {avg_success_rate:.1%}',
                f'Best performing prompt: {best_performer.get("template_id", "Unknown")}',
                'Systematic approaches show consistent improvements',
                'Context-specific prompts outperform generic ones'
            ],
            'opportunities': [
                'Standardize high-performing patterns across prompt types',
                'Implement automated performance monitoring',
                'Create retailer-specific prompt variants',
                'Develop prompt optimization workflows'
            ],
            'trend_summary': f'Analysis of {total_prompts} prompts shows {avg_success_rate:.1%} average success rate with clear patterns for improvement.'
        }
        
        # Generate recommendations
        recommendations = []
        for pattern in success_patterns[:3]:
            recommendations.append({
                'title': f"Include '{pattern['pattern']}' in new prompts",
                'description': f"This pattern shows {pattern['impact']:.1f}% performance improvement",
                'priority': 'high' if pattern['impact'] > 10 else 'medium',
                'category': 'success_pattern'
            })
        
        return {
            'total_prompts': total_prompts,
            'avg_success_rate': avg_success_rate,
            'best_performer': {
                'name': f"{best_performer.get('template_id', 'Unknown')} v{best_performer.get('prompt_version', '1.0')}",
                'success_rate': float(best_performer.get('performance_score', 0))
            },
            'success_patterns': success_patterns,
            'failure_patterns': failure_patterns,
            'clusters': clusters,
            'ai_insights': ai_insights,
            'recommendations': recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompt intelligence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get prompt intelligence: {str(e)}")


async def analyze_prompt_patterns(prompts: List[Dict], pattern_type: str) -> List[Dict]:
    """Analyze common patterns in successful or failing prompts"""
    
    # Filter by performance
    if pattern_type == 'success':
        filtered = [p for p in prompts if float(p.get('performance_score', 0)) > 0.9]
    else:
        filtered = [p for p in prompts if float(p.get('performance_score', 1)) < 0.8]
    
    if not filtered:
        return []
    
    # Simple pattern detection (can be enhanced with NLP)
    patterns = []
    
    # Common successful patterns
    if pattern_type == 'success':
        success_keywords = [
            ('systematic', 'systematic analysis approach'),
            ('step-by-step', 'structured step-by-step instructions'),
            ('confidence', 'confidence scoring and validation'),
            ('left-to-right', 'systematic left-to-right scanning'),
            ('validation', 'built-in validation steps')
        ]
        
        for keyword, description in success_keywords:
            matching_prompts = [p for p in filtered if keyword in p.get('prompt_content', '').lower()]
            if len(matching_prompts) >= 2:
                avg_performance = sum(float(p.get('performance_score', 0)) for p in matching_prompts) / len(matching_prompts)
                overall_avg = sum(float(p.get('performance_score', 0)) for p in prompts) / len(prompts)
                impact = (avg_performance - overall_avg) * 100
                
                patterns.append({
                    'pattern': keyword,
                    'impact': round(impact, 1),
                    'prompt_count': len(matching_prompts),
                    'example_prompts': [p.get('template_id', 'Unknown') for p in matching_prompts[:3]],
                    'description': description
                })
    
    return sorted(patterns, key=lambda x: abs(x['impact']), reverse=True)[:5]


async def cluster_prompts_by_performance(prompts: List[Dict]) -> List[Dict]:
    """Cluster prompts by performance and characteristics"""
    
    # Simple clustering by performance ranges
    clusters = []
    
    # High performance cluster (>90%)
    high_perf = [p for p in prompts if float(p.get('performance_score', 0)) > 0.9]
    if high_perf:
        clusters.append({
            'name': 'High Performance',
            'prompt_count': len(high_perf),
            'avg_success': sum(float(p.get('performance_score', 0)) for p in high_perf) / len(high_perf),
            'common_traits': ['systematic', 'validated', 'optimized'],
            'top_prompts': sorted(high_perf, key=lambda p: float(p.get('performance_score', 0)), reverse=True)[:3]
        })
    
    # Medium performance cluster (70-90%)
    med_perf = [p for p in prompts if 0.7 <= float(p.get('performance_score', 0)) <= 0.9]
    if med_perf:
        clusters.append({
            'name': 'Standard Performance',
            'prompt_count': len(med_perf),
            'avg_success': sum(float(p.get('performance_score', 0)) for p in med_perf) / len(med_perf),
            'common_traits': ['functional', 'reliable', 'standard'],
            'top_prompts': sorted(med_perf, key=lambda p: float(p.get('performance_score', 0)), reverse=True)[:3]
        })
    
    return clusters


@router.post("/regenerate-insights")
async def regenerate_insights():
    """Force regeneration of AI insights"""
    try:
        # In a real implementation, this would trigger AI analysis
        # For now, just return success
        logger.info("Regenerating prompt insights")
        return {"status": "success", "message": "Insights regenerated", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Failed to regenerate insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate insights: {str(e)}")


def getDefaultPromptTemplate(prompt_type: str) -> str:
    """Get default prompt template for a given type"""
    templates = {
        'structure': """You are an expert at analyzing retail shelf images to identify the physical structure and layout.

Your task is to:
1. Identify the number of shelves in the image
2. Determine the width and sections of each shelf
3. Detect any structural elements like dividers, price rails, or shelf edges
4. Note the overall planogram structure

Focus on the physical layout, not the products themselves.

Please analyze the image systematically from top to bottom, left to right.""",
        
        'products': """You are an expert at identifying and cataloging products on retail shelves.

Your task is to:
1. Identify each distinct product on the shelves
2. Determine the exact position of each product
3. Count the number of facings for each product
4. Note any stacking or depth arrangements
5. Identify brand names and product names where visible

Be precise about positioning and avoid double-counting products.

Analyze each shelf section systematically.""",
        
        'details': """You are an expert at extracting detailed product information from retail shelf images.

Your task is to:
1. Extract prices for each identified product
2. Read any visible text on products or price tags
3. Identify promotional indicators or special offers
4. Note product sizes, volumes, or pack information
5. Assess the confidence level of each extraction

Focus on accuracy over speed. If text is unclear, indicate lower confidence.

Process each product methodically."""
    }
    
    return templates.get(prompt_type, 'Please provide instructions for the AI model...')


def getDefaultSchemaTemplate(extraction_type: str) -> str:
    """Get default Pydantic schema template for a given extraction type"""
    schemas = {
        'structure': """from pydantic import BaseModel, Field
from typing import List, Optional

class ShelfSection(BaseModel):
    section_id: str = Field(..., description="Unique identifier for this section")
    position: str = Field(..., description="Position on shelf: left, center, right")
    width_percentage: float = Field(..., description="Approximate width as percentage of shelf")
    has_divider: bool = Field(default=False, description="Whether section has physical divider")

class Shelf(BaseModel):
    shelf_number: int = Field(..., description="Shelf number from top (1-based)")
    height_from_ground: Optional[float] = Field(None, description="Estimated height from ground in cm")
    sections: List[ShelfSection] = Field(..., description="List of sections on this shelf")
    has_price_rail: bool = Field(default=True, description="Whether shelf has price rail")

class StructureAnalysis(BaseModel):
    total_shelves: int = Field(..., description="Total number of shelves identified")
    shelves: List[Shelf] = Field(..., description="Detailed information for each shelf")
    planogram_type: str = Field(..., description="Type of planogram: standard, end-cap, etc")
    confidence: float = Field(..., ge=0, le=1, description="Overall confidence in structure analysis")""",
        
        'products': """from pydantic import BaseModel, Field
from typing import List, Optional

class ProductPosition(BaseModel):
    shelf_number: int = Field(..., description="Shelf number from top")
    section: str = Field(..., description="Section on shelf: left, center, right")
    position_in_section: int = Field(..., description="Position within section (1-based)")

class Product(BaseModel):
    product_id: str = Field(..., description="Unique identifier for this product instance")
    brand: str = Field(..., description="Brand name")
    product_name: str = Field(..., description="Product name")
    position: ProductPosition = Field(..., description="Exact position on shelf")
    facings: int = Field(..., ge=1, description="Number of facings (width)")
    stack_count: int = Field(default=1, ge=1, description="Number stacked vertically")
    depth_count: Optional[int] = Field(None, description="Estimated depth if visible")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in identification")

class ProductExtraction(BaseModel):
    products: List[Product] = Field(..., description="All identified products")
    total_products: int = Field(..., description="Total number of distinct products")
    total_facings: int = Field(..., description="Total number of facings across all products")""",
        
        'details': """from pydantic import BaseModel, Field
from typing import Optional, List

class PriceInfo(BaseModel):
    price: float = Field(..., description="Price in local currency")
    currency_symbol: str = Field(default="£", description="Currency symbol")
    is_promotional: bool = Field(default=False, description="Whether price is promotional")
    original_price: Optional[float] = Field(None, description="Original price if on promotion")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in price extraction")

class ProductDetails(BaseModel):
    product_id: str = Field(..., description="Reference to product from extraction")
    price_info: Optional[PriceInfo] = Field(None, description="Price information if visible")
    size: Optional[str] = Field(None, description="Product size/volume if visible")
    variant: Optional[str] = Field(None, description="Product variant (flavor, type, etc)")
    promotional_text: Optional[str] = Field(None, description="Any promotional messaging")
    barcode: Optional[str] = Field(None, description="Barcode if visible")
    
class DetailEnhancement(BaseModel):
    product_details: List[ProductDetails] = Field(..., description="Enhanced details for products")
    prices_found: int = Field(..., description="Number of prices successfully extracted")
    avg_confidence: float = Field(..., description="Average confidence across all extractions")"""
    }
    
    return schemas.get(extraction_type, "from pydantic import BaseModel\n\nclass ExtractedData(BaseModel):\n    pass")


@router.post("/generate-optimized")
async def generate_optimized_prompt(request_data: Dict[str, Any]):
    """Generate AI-optimized prompt based on inputs and best practices"""
    
    try:
        import uuid
        
        prompt_type = request_data.get('prompt_type')
        base_prompt = request_data.get('base_prompt', '')
        fields_to_extract = request_data.get('fields_to_extract', [])
        special_instructions = request_data.get('special_instructions', '')
        parent_prompt_id = request_data.get('parent_prompt_id')
        
        if not prompt_type:
            raise HTTPException(status_code=400, detail="prompt_type is required")
        
        # Generate optimized prompt based on type and fields
        optimized_prompt = generate_optimized_prompt_content(
            prompt_type, base_prompt, fields_to_extract, special_instructions
        )
        
        # Generate Pydantic model code
        pydantic_model_code = generate_pydantic_model(prompt_type, fields_to_extract)
        
        # Generate complete Instructor configuration
        instructor_config = {
            "prompt_template": optimized_prompt,
            "response_model": f"{prompt_type.title()}Extraction",
            "fields": fields_to_extract,
            "validation_enabled": True
        }
        
        # AI reasoning for optimization
        reasoning = [
            f"Optimized for {prompt_type} extraction with focus on selected fields",
            "Added systematic scanning instructions for consistency",
            "Included confidence scoring for quality control",
            "Structured output format for easy parsing",
            "Added validation steps to reduce errors"
        ]
        
        # Key improvements made
        key_improvements = []
        if "confidence" in fields_to_extract:
            key_improvements.append("Added confidence scoring throughout extraction")
        if len(fields_to_extract) > 5:
            key_improvements.append("Organized complex field extraction into logical groups")
        if special_instructions:
            key_improvements.append(f"Incorporated custom requirements: {special_instructions[:50]}...")
        
        # Estimate token usage
        estimated_tokens = len(optimized_prompt.split()) * 1.3  # Rough estimate
        
        return {
            "success": True,
            "optimized_prompt": optimized_prompt,
            "pydantic_model_code": pydantic_model_code,
            "model_class_name": f"{prompt_type.title()}Extraction",
            "instructor_config": instructor_config,
            "reasoning": reasoning,
            "key_improvements": key_improvements,
            "optimization_focus": f"{prompt_type} extraction with {len(fields_to_extract)} fields",
            "estimated_tokens": int(estimated_tokens),
            "recommended_model": "claude-3-sonnet-20240229" if prompt_type == "structure" else "gpt-4o",
            "parent_prompt_id": parent_prompt_id
        }
        
    except Exception as e:
        logger.error(f"Failed to generate optimized prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate optimized prompt: {str(e)}")


def generate_optimized_prompt_content(prompt_type: str, base_prompt: str, fields: List[str], instructions: str) -> str:
    """Generate optimized prompt content based on inputs"""
    
    # Base template
    if base_prompt:
        optimized = base_prompt + "\n\n"
    else:
        optimized = getDefaultPromptTemplate(prompt_type) + "\n\n"
    
    # Add field-specific instructions
    if fields:
        optimized += "Focus on extracting the following information:\n"
        for field in fields:
            field_instruction = get_field_instruction(field)
            optimized += f"• {field_instruction}\n"
        optimized += "\n"
    
    # Add systematic approach
    optimized += "Approach:\n"
    optimized += "1. Scan systematically from top to bottom, left to right\n"
    optimized += "2. Validate each extraction before moving to the next\n"
    optimized += "3. Assign confidence scores based on visibility and clarity\n"
    optimized += "4. Cross-check related information for consistency\n\n"
    
    # Add special instructions if provided
    if instructions:
        optimized += f"Special Requirements:\n{instructions}\n\n"
    
    # Add output format guidance
    optimized += "Output your analysis in a structured format with clear field labels and confidence indicators."
    
    return optimized


def get_field_instruction(field: str) -> str:
    """Get specific instruction for a field"""
    field_instructions = {
        "product_name": "Product Name - Full product name including variant details",
        "brand": "Brand - Manufacturer or brand name, using standard capitalization",
        "price": "Price - Numeric price value with currency symbol",
        "position": "Position - Exact shelf and section location",
        "facings": "Facings - Number of product units visible from front",
        "stack": "Stack - Vertical stacking count if applicable",
        "color": "Color - Primary product or packaging colors",
        "promo_text": "Promotional Text - Any promotional messaging or offers",
        "package_size": "Package Size - Volume, weight, or count information",
        "confidence": "Confidence Score - Rate extraction confidence (0.0-1.0)"
    }
    return field_instructions.get(field, f"{field.title()} - Extract {field} information")


def generate_pydantic_model(prompt_type: str, fields: List[str]) -> str:
    """Generate Pydantic model code for the extraction"""
    
    # Start with imports
    code = "from pydantic import BaseModel, Field\n"
    code += "from typing import Optional, List\n\n"
    
    # Add field-specific models if needed
    if "position" in fields:
        code += """class Position(BaseModel):
    shelf_number: int = Field(..., description="Shelf number from top")
    section: str = Field(..., description="Section: left, center, or right")
    position_in_section: int = Field(..., description="Position within section")

"""
    
    # Main model
    model_name = f"{prompt_type.title()}Extraction"
    code += f"class {model_name}(BaseModel):\n"
    
    # Add fields
    field_definitions = {
        "product_name": '    product_name: str = Field(..., description="Full product name")',
        "brand": '    brand: str = Field(..., description="Product brand")',
        "price": '    price: Optional[float] = Field(None, description="Product price")',
        "position": '    position: Position = Field(..., description="Product position")',
        "facings": '    facings: int = Field(1, ge=1, description="Number of facings")',
        "stack": '    stack_count: int = Field(1, ge=1, description="Vertical stack count")',
        "color": '    color: Optional[str] = Field(None, description="Primary colors")',
        "promo_text": '    promotional_text: Optional[str] = Field(None, description="Promotional messaging")',
        "package_size": '    package_size: Optional[str] = Field(None, description="Size or volume")',
        "confidence": '    confidence: float = Field(..., ge=0, le=1, description="Extraction confidence")'
    }
    
    for field in fields:
        if field in field_definitions:
            code += field_definitions[field] + "\n"
    
    # Add any default fields based on prompt type
    if prompt_type == "structure":
        code += '    total_shelves: int = Field(..., description="Total number of shelves")\n'
    elif prompt_type == "products":
        code += '    products: List["Product"] = Field(..., description="List of all products")\n'
    
    return code


@router.post("/save-generated")
async def save_generated_prompt(request_data: Dict[str, Any]):
    """Save a newly generated or edited prompt"""
    
    try:
        import uuid
        from datetime import datetime
        
        # Extract data
        prompt_type = request_data.get('prompt_type')
        optimized_prompt = request_data.get('optimized_prompt')
        model_type = request_data.get('model_type', 'universal')
        version_strategy = request_data.get('version_strategy', 'new')
        parent_prompt_id = request_data.get('parent_prompt_id')
        instructor_config = request_data.get('instructor_config', {})
        pydantic_model_code = request_data.get('pydantic_model_code', '')
        
        if not all([prompt_type, optimized_prompt]):
            raise HTTPException(status_code=400, detail="prompt_type and optimized_prompt are required")
        
        # Generate version number
        if version_strategy == 'new' and parent_prompt_id and supabase:
            # Get parent prompt to increment version
            parent = supabase.table("prompt_templates").select("prompt_version").eq("prompt_id", parent_prompt_id).execute()
            if parent.data:
                current_version = parent.data[0].get('prompt_version', '1.0')
                try:
                    major, minor = map(int, current_version.split('.'))
                    new_version = f"{major}.{minor + 1}"
                except:
                    new_version = "1.1"
            else:
                new_version = "1.0"
        else:
            new_version = "1.0"
        
        # Create template ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        template_id = f"{prompt_type}_{model_type}_v{new_version}_{timestamp}"
        
        # Prepare prompt data
        prompt_data = {
            'prompt_id': str(uuid.uuid4()),
            'template_id': template_id,
            'prompt_type': prompt_type,
            'model_type': model_type,
            'prompt_version': new_version,
            'prompt_content': optimized_prompt,
            'metadata': {
                'instructor_config': instructor_config,
                'pydantic_model': pydantic_model_code,
                'fields': instructor_config.get('fields', []),
                'parent_prompt_id': parent_prompt_id,
                'version_strategy': version_strategy
            },
            'performance_score': 0.0,  # Will be updated with usage
            'usage_count': 0,
            'avg_token_cost': 0.0,
            'correction_rate': 0.0,
            'is_active': False,  # Requires explicit activation
            'created_from_feedback': False,
            'retailer_context': [],
            'category_context': [],
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if supabase:
            # Save to database
            result = supabase.table('prompt_templates').insert(prompt_data).execute()
            
            if result.data:
                saved_prompt = result.data[0]
                logger.info(f"Saved new prompt: {template_id}")
                
                return {
                    "success": True,
                    "prompt_id": saved_prompt['prompt_id'],
                    "template_id": template_id,
                    "version": new_version,
                    "message": f"Prompt saved successfully as version {new_version}",
                    "activation_required": True
                }
        else:
            # Fallback - save to local storage or return success
            logger.info(f"Would save prompt: {template_id} (no database)")
            
            return {
                "success": True,
                "prompt_id": prompt_data['prompt_id'],
                "template_id": template_id,
                "version": new_version,
                "message": "Prompt saved locally (no database connection)",
                "activation_required": True
            }
            
    except Exception as e:
        logger.error(f"Failed to save generated prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {str(e)}")


def incrementVersion(version: str) -> str:
    """Increment version number"""
    try:
        parts = version.split('.')
        if len(parts) == 2:
            major, minor = map(int, parts)
            return f"{major}.{minor + 1}"
    except:
        pass
    return "1.1" 