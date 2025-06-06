"""
Queue Processing API endpoints for the new unified dashboard
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import asyncio
import time
from datetime import datetime, timedelta

from ..utils import logger
from ..config import SystemConfig
from ..orchestrator.system_dispatcher import SystemDispatcher
from ..orchestrator.monitoring_hooks import monitoring_hooks

router = APIRouter()

# Global store for monitoring data
monitoring_data = {}

class ProcessRequest(BaseModel):
    """Request model for processing queue items"""
    system: str = "custom_consensus"
    max_budget: float = 1.50
    temperature: float = 0.7
    orchestrator_model: str = "claude-4-opus"
    orchestrator_prompt: str = ""
    stage_models: Optional[Dict[str, List[str]]] = None
    configuration: Optional[Dict[str, Any]] = None

@router.post("/process/{item_id}")
async def process_queue_item(
    item_id: int,
    background_tasks: BackgroundTasks,
    request: ProcessRequest
):
    """Process a single queue item with specified configuration"""
    try:
        config = SystemConfig()
        
        # Get queue item from Supabase
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        # Fetch queue item
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Queue item not found")
        
        queue_item = result.data[0]
        
        # Update status to processing
        supabase.table("ai_extraction_queue").update({
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "current_extraction_system": request.system
        }).eq("id", item_id).execute()
        
        # Initialize monitoring data
        initial_data = {
            "status": "processing",
            "started_at": time.time(),
            "current_iteration": 1,
            "current_stage": "Starting",
            "duration": 0,
            "structure_complete": False,
            "products_complete": False,
            "locked_items": [],
            "current_processing": "Initializing extraction...",
            "models_status": [
                {"name": "Claude", "status": "Waiting..."},
                {"name": "GPT-4", "status": "Waiting..."},
                {"name": "Gemini", "status": "Waiting..."}
            ]
        }
        
        monitoring_data[item_id] = initial_data
        monitoring_hooks.register_monitor(item_id, initial_data)
        
        # Build configuration with all the parameters
        configuration = request.configuration or {}
        
        logger.info(f"Received configuration from UI: {configuration}")
        logger.info(f"Configuration has stages: {'stages' in configuration}")
        if 'stages' in configuration:
            logger.info(f"Stages in configuration: {list(configuration.get('stages', {}).keys())}")
        
        configuration.update({
            "temperature": request.temperature,
            "orchestrator_model": request.orchestrator_model,
            "orchestrator_prompt": request.orchestrator_prompt,
            "stage_models": request.stage_models or {},
            "max_budget": request.max_budget
        })
        
        logger.info(f"Final configuration being passed: {configuration}")
        
        # Run extraction in background - use wrapper for async function
        logger.info(f"Adding background task for item {item_id}, upload {queue_item['upload_id']}")
        background_tasks.add_task(
            run_extraction_wrapper,
            item_id=item_id,
            upload_id=queue_item["upload_id"],
            system=request.system,
            max_budget=request.max_budget,
            configuration=configuration
        )
        
        logger.info(f"Background task added successfully for item {item_id}")
        
        return {
            "status": "started",
            "item_id": item_id,
            "message": "Processing started successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_extraction_wrapper(
    item_id: int,
    upload_id: str,
    system: str,
    max_budget: float,
    configuration: Dict[str, Any]
):
    """Wrapper to run async extraction in background"""
    logger.info(f"🚀 run_extraction_wrapper started for item {item_id}, upload {upload_id}")
    
    # Create new event loop for the background task
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        logger.info(f"Running extraction coroutine for item {item_id}")
        loop.run_until_complete(
            run_extraction(item_id, upload_id, system, max_budget, configuration)
        )
        logger.info(f"✅ Extraction completed for item {item_id}")
    except Exception as e:
        logger.error(f"❌ Extraction wrapper failed for item {item_id}: {e}")
        raise
    finally:
        loop.close()


async def run_extraction(
    item_id: int,
    upload_id: str,
    system: str,
    max_budget: float,
    configuration: Dict[str, Any]
):
    """Run the extraction process in the background"""
    logger.info(f"🚀 Starting extraction for item {item_id}, upload {upload_id}, system {system}")
    logger.info(f"Configuration received in run_extraction: {configuration}")
    logger.info(f"Configuration has stages: {'stages' in configuration}")
    
    try:
        config = SystemConfig()
        config.max_budget = max_budget
        
        # Create orchestrator
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        orchestrator = SystemDispatcher(config, supabase_client=supabase)
        
        # Set up monitoring callback
        def update_monitoring(queue_item_id: int, updates: Dict[str, Any]):
            """Callback to update monitoring data"""
            if queue_item_id in monitoring_data:
                monitoring_data[queue_item_id].update(updates)
                monitoring_data[queue_item_id]["last_update"] = datetime.utcnow().isoformat()
        
        # Register monitoring callback
        monitoring_hooks.register_callback(item_id, lambda data: update_monitoring(item_id, data))
        
        # Update initial status
        await monitoring_hooks.update_extraction_stage(
            item_id,
            "Initializing",
            {"message": "Starting extraction pipeline"}
        )
        
        logger.info(f"Starting extraction for queue item {item_id}, upload {upload_id}")
        
        # Run extraction with proper parameters
        result = await orchestrator.achieve_target_accuracy(
            upload_id=upload_id,
            target_accuracy=0.95,
            max_iterations=5,
            queue_item_id=item_id,
            system=system,
            configuration=configuration
        )
        
        # Update final status in monitoring
        monitoring_data[item_id]["status"] = "completed"
        monitoring_data[item_id]["final_accuracy"] = result.final_accuracy
        monitoring_data[item_id]["total_cost"] = result.total_cost
        monitoring_data[item_id]["iterations_completed"] = result.iterations_completed
        
        # Clear monitoring hooks
        monitoring_hooks.clear_monitor(item_id)
        
        # Update queue item with results
        supabase.table("ai_extraction_queue").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "final_accuracy": result.final_accuracy,
            "iterations_completed": result.iterations_completed,
            "api_cost": result.total_cost,
            "human_review_required": result.needs_human_review,
            "selected_systems": [system],
            "current_extraction_system": system
        }).eq("id", item_id).execute()
        
        # Store the result for later retrieval
        if result.best_planogram:
            # Store planogram data
            planogram_data = {
                "queue_item_id": item_id,
                "planogram_svg": result.best_planogram.planogram.svg_data if hasattr(result.best_planogram.planogram, 'svg_data') else None,
                "accuracy": result.final_accuracy,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # You might want to store this in a planograms table
            # supabase.table("planograms").insert(planogram_data).execute()
        
        logger.info(
            f"Extraction completed for item {item_id}",
            final_accuracy=result.final_accuracy,
            iterations=result.iterations_completed,
            cost=result.total_cost
        )
        
    except Exception as e:
        logger.error(f"Extraction failed for item {item_id}: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        
        # Update status to failed
        try:
            logger.info(f"Updating status to 'failed' for item {item_id}")
            update_result = supabase.table("ai_extraction_queue").update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", item_id).execute()
            logger.info(f"Status update result: {update_result}")
        except Exception as update_error:
            logger.error(f"Failed to update status: {update_error}")
        
        # Update monitoring data
        if item_id in monitoring_data:
            monitoring_data[item_id]["status"] = "failed"
            monitoring_data[item_id]["error"] = str(e)
            logger.info(f"Updated monitoring data to failed status for item {item_id}")
        
        # Clear monitoring hooks
        monitoring_hooks.clear_monitor(item_id)
        
        # Re-raise the exception to ensure it's logged at the wrapper level
        raise


@router.get("/monitor/{item_id}")
async def get_monitoring_data(item_id: int):
    """Get real-time monitoring data for a processing item"""
    
    # First try monitoring hooks
    hook_data = monitoring_hooks.get_monitor_data(item_id)
    if hook_data:
        # Calculate duration
        started_at = hook_data.get("started_at")
        if isinstance(started_at, datetime):
            duration = int((datetime.utcnow() - started_at).total_seconds())
        else:
            duration = int(time.time() - started_at)
        
        hook_data["duration"] = duration
        return hook_data
    
    # Then check our local monitoring data
    if item_id in monitoring_data:
        data = monitoring_data[item_id].copy()
        data["duration"] = int(time.time() - data["started_at"])
        return data
    
    # Finally try database
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        result = supabase.table("ai_extraction_queue").select("status").eq("id", item_id).execute()
        if result.data:
            return {
                "status": result.data[0]["status"],
                "message": "Item not currently being monitored"
            }
    except:
        pass
        
    raise HTTPException(status_code=404, detail="Monitoring data not found")


@router.post("/force-complete/{item_id}")
async def force_complete_item(item_id: int):
    """Force a stuck item to complete"""
    if item_id in monitoring_data:
        monitoring_data[item_id]["status"] = "completed"
        monitoring_data[item_id]["forced"] = True
    
    # Update in database
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        supabase.table("ai_extraction_queue").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "notes": "Forced completion by user"
        }).eq("id", item_id).execute()
        
        return {"status": "success", "message": "Item forced to complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/abort/{item_id}")
async def abort_item(item_id: int):
    """Abort processing of an item"""
    if item_id in monitoring_data:
        monitoring_data[item_id]["status"] = "aborted"
        monitoring_data[item_id]["aborted"] = True
    
    # Update in database
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        supabase.table("ai_extraction_queue").update({
            "status": "failed",
            "error_message": "Aborted by user"
        }).eq("id", item_id).execute()
        
        return {"status": "success", "message": "Processing aborted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{item_id}")
async def get_extraction_results(item_id: int):
    """Get extraction results for a completed item"""
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        # Get queue item with extraction data
        result = supabase.table("ai_extraction_queue").select("*").eq("id", item_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        queue_item = result.data[0]
        
        # Get upload info with store details
        upload_result = supabase.table("uploads").select("""
            *,
            collections!inner(
                store_id,
                stores!inner(
                    retailer_name,
                    format,
                    location_city,
                    location_address,
                    country
                )
            )
        """).eq("id", queue_item["upload_id"]).execute()
        
        upload_info = upload_result.data[0] if upload_result.data else {}
        store_info = upload_info.get("collections", {}).get("stores", {}) if upload_info else {}
        
        # Get extraction runs
        runs_result = supabase.table("ai_extraction_runs").select("*").eq("queue_item_id", item_id).order("created_at", desc=True).limit(1).execute()
        latest_run = runs_result.data[0] if runs_result.data else None
        
        # Get actual extraction results if available
        products = []
        planogram_svg = None
        iterations_data = []
        
        if latest_run and latest_run.get("result_data"):
            result_data = latest_run["result_data"]
            
            # Extract products from result data
            if "extraction_result" in result_data:
                extraction_data = result_data["extraction_result"]
                if "products" in extraction_data:
                    products = extraction_data["products"]
            
            # Get planogram SVG if available
            if "best_planogram" in result_data and result_data["best_planogram"]:
                planogram_data = result_data["best_planogram"]
                if "planogram" in planogram_data and "svg_data" in planogram_data["planogram"]:
                    planogram_svg = planogram_data["planogram"]["svg_data"]
        
        # Get iterations data from tracking API
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://localhost:8000/api/iterations/{item_id}") as response:
                    if response.status == 200:
                        iter_data = await response.json()
                        if "iterations" in iter_data:
                            iterations_data = iter_data["iterations"]
        except Exception as e:
            logger.warning(f"Failed to get iteration data: {e}")
        
        # Format products for display
        formatted_products = []
        for i, product in enumerate(products):
            formatted_products.append({
                "id": f"prod_{i}",
                "name": product.get("name", "Unknown Product"),
                "brand": product.get("brand", "Unknown Brand"),
                "shelf": product.get("shelf_level", 1),
                "position": product.get("position_on_shelf", i + 1),
                "price": f"£{product.get('price', 0):.2f}" if product.get('price') else "Unknown",
                "verified": False,  # Will be updated when feedback system is connected
                "facings": product.get("facings_total", 1),
                "confidence": product.get("extraction_confidence", 0)
            })
        
        # Calculate time since completion
        completed_time = "Unknown"
        if queue_item.get("completed_at"):
            completed_dt = datetime.fromisoformat(queue_item["completed_at"].replace('Z', '+00:00'))
            time_diff = datetime.utcnow() - completed_dt.replace(tzinfo=None)
            if time_diff.days > 0:
                completed_time = f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                completed_time = f"{time_diff.seconds // 3600} hours ago"
            else:
                completed_time = f"{time_diff.seconds // 60} minutes ago"
        
        # Get image URL
        image_url = f"/api/queue/image/{item_id}"
        
        # Default planogram if none available
        if not planogram_svg:
            planogram_svg = '<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg"><rect width="400" height="300" fill="#f0f0f0"/><text x="200" y="150" text-anchor="middle" font-size="20" fill="#666">No planogram generated yet</text></svg>'
        
        return {
            "item_id": item_id,
            "store_name": store_info.get("retailer_name", "Unknown Store"),
            "store_location": store_info.get("location_city", "Unknown Location"),
            "category": upload_info.get("category", "Unknown Category"),
            "completed_time": completed_time,
            "accuracy": queue_item.get("final_accuracy", 0),
            "total_cost": queue_item.get("api_cost", 0),
            "iterations": queue_item.get("iterations_completed", 0),
            "total_products": len(formatted_products),
            "products": formatted_products,
            "original_image_url": image_url,
            "planogram_svg": planogram_svg,
            "iterations_data": iterations_data,
            "status": queue_item.get("status", "unknown"),
            "human_review_required": queue_item.get("human_review_required", False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/save")
async def save_configuration(config_data: Dict[str, Any]):
    """Save extraction configuration"""
    # This would save to database or config file
    # For now just return success
    return {"status": "success", "message": "Configuration saved"}


