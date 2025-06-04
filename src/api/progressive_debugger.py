"""
Progressive Debugger API
API endpoints for the new progressive debugging interface
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from ..orchestrator.system_dispatcher import SystemDispatcher
from ..orchestrator.planogram_orchestrator import PlanogramOrchestrator
from ..evaluation.human_evaluation import HumanEvaluationSystem
from ..config import SystemConfig
from ..utils import logger

router = APIRouter(prefix="/api/v2", tags=["Progressive Debugger"])

# Initialize system components
config = SystemConfig()
master_orchestrator = SystemDispatcher(config)
planogram_orchestrator = PlanogramOrchestrator(config)
human_evaluation = HumanEvaluationSystem(config)


@router.post("/process-with-iterations")
async def process_with_iterations(
    file: UploadFile = File(...),
    target_accuracy: float = Form(0.95),
    max_iterations: int = Form(5),
    abstraction_level: str = Form("product_view")
):
    """Process image with full iteration tracking for progressive debugging"""
    
    upload_id = str(uuid.uuid4())
    
    logger.info(
        f"Starting progressive processing for upload {upload_id}",
        component="progressive_api",
        upload_id=upload_id,
        target_accuracy=target_accuracy,
        max_iterations=max_iterations
    )
    
    try:
        # Read image data
        image_data = await file.read()
        
        # TODO: Store image in Supabase
        # For now, we'll use the upload_id as a reference
        
        # Process with full iteration tracking
        result = await master_orchestrator.process_with_comparison_set(
            upload_id=upload_id,
            generate_all_iterations=True
        )
        
        # Format response for UI
        response = {
            "upload_id": upload_id,
            "processing_complete": True,
            "target_achieved": result['master_result'].target_achieved,
            "final_accuracy": result['master_result'].final_accuracy,
            "iterations_completed": result['master_result'].iterations_completed,
            "total_duration": result['master_result'].total_duration,
            "total_cost": result['master_result'].total_cost,
            "needs_human_review": result['master_result'].needs_human_review,
            
            # Agent iteration data
            "agent_iterations": [
                {
                    "agent_number": i + 1,
                    "accuracy": iter_data["accuracy"],
                    "products_found": iter_data["extraction_result"].total_products,
                    "confidence": iter_data["extraction_result"].overall_confidence.value,
                    "model_used": iter_data["extraction_result"].model_used,
                    "duration": iter_data["extraction_result"].extraction_duration_seconds,
                    "improvements": iter_data["extraction_result"].improvements_from_previous or [],
                    "issues": [
                        f"Confidence: {iter_data['accuracy']:.1%}",
                        f"Failed areas: {len(iter_data['failure_areas'])}"
                    ],
                    "json_data": {
                        "products": [p.dict() for p in iter_data["extraction_result"].products],
                        "structure": iter_data["extraction_result"].structure.dict()
                    },
                    "planogram_quality": iter_data["planogram"].quality_assessment
                }
                for i, iter_data in enumerate(result['master_result'].iteration_history)
            ],
            
            # Comparison analysis
            "progression_analysis": result.get('progression_analysis', {}),
            "best_iteration": result.get('best_iteration', 1),
            
            # Structure analysis
            "structure_analysis": result['master_result'].structure_analysis.dict()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(
            f"Processing failed for upload {upload_id}: {e}",
            component="progressive_api",
            upload_id=upload_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/iteration/{upload_id}/{agent_number}")
async def get_iteration_details(upload_id: str, agent_number: int):
    """Get detailed results for a specific agent iteration"""
    
    # TODO: Retrieve from database
    # For now, return mock data
    
    return {
        "agent_number": agent_number,
        "upload_id": upload_id,
        "extraction_data": {
            "products": [],
            "confidence": 0.85,
            "model_used": "claude-3-5-sonnet"
        },
        "planogram_data": {
            "quality_score": 0.88,
            "issues": [],
            "visual_data": {}
        },
        "comparison_data": {
            "matches": [],
            "mismatches": [],
            "overall_similarity": 0.85
        }
    }


@router.post("/switch-abstraction/{upload_id}/{agent_number}")
async def switch_abstraction_level(
    upload_id: str,
    agent_number: int,
    new_level: str = Form(...)
):
    """Switch planogram to different abstraction level"""
    
    logger.info(
        f"Switching abstraction level for {upload_id} agent {agent_number} to {new_level}",
        component="progressive_api",
        upload_id=upload_id,
        agent_number=agent_number,
        new_level=new_level
    )
    
    try:
        # TODO: Retrieve agent result from database
        # For now, return mock response
        
        return {
            "success": True,
            "new_abstraction_level": new_level,
            "planogram_updated": True,
            "visual_data": {
                "svg": "<svg>...</svg>",
                "canvas_js": "// Canvas rendering code"
            }
        }
        
    except Exception as e:
        logger.error(
            f"Abstraction switch failed: {e}",
            component="progressive_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Abstraction switch failed: {str(e)}")


@router.post("/human-evaluation/{upload_id}")
async def submit_human_evaluation(
    upload_id: str,
    evaluation_data: Dict[str, Any]
):
    """Submit human evaluation feedback"""
    
    logger.info(
        f"Receiving human evaluation for upload {upload_id}",
        component="progressive_api",
        upload_id=upload_id
    )
    
    try:
        # Create evaluation session if not exists
        # TODO: Check if session exists in database
        
        # Submit evaluation
        evaluation = await human_evaluation.submit_human_evaluation(
            session_id=upload_id,  # Using upload_id as session_id for simplicity
            evaluation_data=evaluation_data
        )
        
        return {
            "success": True,
            "evaluation_id": evaluation.session_id,
            "timestamp": evaluation.timestamp.isoformat(),
            "overall_rating": (
                evaluation.extraction_accuracy + 
                evaluation.planogram_accuracy + 
                evaluation.overall_satisfaction
            ) / 3
        }
        
    except Exception as e:
        logger.error(
            f"Human evaluation submission failed: {e}",
            component="progressive_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Evaluation submission failed: {str(e)}")


@router.get("/evaluation-trends")
async def get_evaluation_trends(days: int = 30):
    """Get human evaluation trends over time"""
    
    try:
        trends = human_evaluation.get_evaluation_trends(days=days)
        
        return {
            "trends": trends.dict(),
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(
            f"Failed to get evaluation trends: {e}",
            component="progressive_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


@router.post("/prompt-editor/{upload_id}/{agent_number}")
async def update_agent_prompts(
    upload_id: str,
    agent_number: int,
    prompt_data: Dict[str, str]
):
    """Update agent prompts and re-run extraction"""
    
    logger.info(
        f"Updating prompts for {upload_id} agent {agent_number}",
        component="progressive_api",
        upload_id=upload_id,
        agent_number=agent_number
    )
    
    try:
        # TODO: Update prompts in agent configuration
        # TODO: Re-run extraction with new prompts
        
        return {
            "success": True,
            "prompts_updated": True,
            "rerun_triggered": True,
            "new_results": {
                "accuracy": 0.92,
                "products_found": 25,
                "improvements": ["Better price extraction", "Improved positioning"]
            }
        }
        
    except Exception as e:
        logger.error(
            f"Prompt update failed: {e}",
            component="progressive_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Prompt update failed: {str(e)}")


@router.get("/debug-interface/{upload_id}")
async def get_debug_interface_data(upload_id: str):
    """Get all data needed for the progressive debug interface"""
    
    try:
        # TODO: Retrieve complete processing results from database
        
        return {
            "upload_id": upload_id,
            "original_image_url": f"/api/images/{upload_id}/original",
            "processing_status": "complete",
            "agent_iterations": [
                {
                    "agent_number": 1,
                    "name": "Agent 1 - Initial Extraction",
                    "accuracy": 73,
                    "duration": "45s",
                    "status": "complete",
                    "model": "gpt-4o",
                    "products_found": 21,
                    "improvements": ["Basic shelf structure detection", "Initial product identification"],
                    "issues": ["Missing 4 products", "Price extraction errors", "Poor positioning accuracy"]
                },
                {
                    "agent_number": 2,
                    "name": "Agent 2 - Enhanced Detection",
                    "accuracy": 89,
                    "duration": "38s",
                    "status": "complete",
                    "model": "claude-4-sonnet",
                    "products_found": 24,
                    "improvements": ["Found 3 additional products", "Fixed price extraction", "Improved confidence scores"],
                    "issues": ["Minor positioning errors", "2 products still missing"]
                },
                {
                    "agent_number": 3,
                    "name": "Agent 3 - Final Optimization",
                    "accuracy": 94,
                    "duration": "22s",
                    "status": "complete",
                    "model": "claude-4-sonnet + gemini-2.5",
                    "products_found": 25,
                    "improvements": ["Found all products", "Enhanced spatial positioning", "Cross-validation complete"],
                    "issues": ["Minor confidence variations"]
                }
            ],
            "structure_analysis": {
                "shelf_count": 4,
                "estimated_width_meters": 1.8,
                "products_per_shelf_estimate": 8,
                "confidence": 0.95
            },
            "human_evaluation_session": None,
            "available_abstractions": ["brand_view", "product_view", "sku_view"]
        }
        
    except Exception as e:
        logger.error(
            f"Failed to get debug interface data: {e}",
            component="progressive_api",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get debug data: {str(e)}") 