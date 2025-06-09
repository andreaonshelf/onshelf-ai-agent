"""
Diagnostics API endpoints for extraction run analysis
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import json

from ..utils import logger
from ..config import SystemConfig
from ..utils.extraction_analytics import get_extraction_analytics

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

@router.get("/extraction-runs")
async def get_extraction_runs(days: int = Query(7, description="Number of days to look back")):
    """Get list of extraction runs with summary metrics"""
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Query extraction runs with summary from materialized view
        response = supabase.rpc(
            'get_extraction_analytics_summary',
            {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        ).execute()
        
        # Use real data from ai_extraction_queue table
        response = supabase.table('ai_extraction_queue') \
            .select('*') \
            .gte('created_at', start_date.isoformat()) \
            .lte('created_at', end_date.isoformat()) \
            .order('created_at', desc=True) \
            .execute()
        
        runs = []
        if response.data:
            for run in response.data:
                runs.append({
                    'run_id': f"queue_{run['id']}",
                    'system_type': run.get('current_extraction_system', 'unknown'),
                    'started_at': run.get('started_at') or run['created_at'],
                    'status': run.get('status', 'unknown'),
                    'total_iterations': run.get('iterations_completed', 0),
                    'total_cost': run.get('api_cost', 0.0),
                    'avg_accuracy': run.get('final_accuracy', 0.0),
                    'processing_duration': run.get('processing_duration_seconds', 0),
                    'upload_id': run.get('upload_id'),
                    'queue_id': run['id']
                })
        
        return {"runs": runs}
        
    except Exception as e:
        logger.error(f"Failed to get extraction runs: {e}")
        return {"runs": [], "error": str(e)}

@router.get("/extraction-run/{run_id}")
async def get_extraction_run_details(run_id: str):
    """Get detailed iteration data for a specific extraction run"""
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        # Extract queue_id from run_id (format: queue_{id})
        if run_id.startswith("queue_"):
            queue_id = run_id.replace("queue_", "")
            
            # Get queue item details
            queue_result = supabase.table('ai_extraction_queue') \
                .select('*') \
                .eq('id', queue_id) \
                .execute()
            
            if not queue_result.data:
                raise HTTPException(status_code=404, detail="Queue item not found")
            
            queue_item = queue_result.data[0]
            
            # Get extraction result details
            extraction_result = queue_item.get('extraction_result', {})
            
            # Build iterations from queue item data
            iterations = []
            
            # Add basic processing iteration
            iterations.append({
                "id": 1,
                "stage": queue_item.get('current_extraction_system', 'unknown'),
                "model_used": "Multiple models",
                "iteration_number": queue_item.get('iterations_completed', 1),
                "retry_reason": queue_item.get('error_message') if queue_item.get('status') == 'failed' else None,
                "accuracy_score": queue_item.get('final_accuracy', 0.0),
                "products_found": len(extraction_result.get('products', [])) if extraction_result else 0,
                "duration_ms": (queue_item.get('processing_duration_seconds', 0) * 1000),
                "api_cost": queue_item.get('api_cost', 0.0),
                "visual_feedback_received": None,
                "retry_blocks_activated": [],
                "actual_prompt": "Real extraction with configured system and prompts",
                "queue_item_data": queue_item
            })
        else:
            # Handle other run_id formats or return empty
            iterations = []
        
        # Calculate visual feedback summary
        visual_feedback_summary = {
            "total_feedback_received": sum(1 for i in iterations if i['visual_feedback_received']),
            "avg_accuracy_with_feedback": sum(i['accuracy_score'] for i in iterations if i['visual_feedback_received']) / max(1, sum(1 for i in iterations if i['visual_feedback_received'])),
            "avg_accuracy_without_feedback": sum(i['accuracy_score'] for i in iterations if not i['visual_feedback_received']) / max(1, sum(1 for i in iterations if not i['visual_feedback_received']))
        }
        
        return {
            "run_id": run_id,
            "iterations": iterations,
            "visual_feedback_summary": visual_feedback_summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get run details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompt-execution-history")
async def get_prompt_execution_history(
    run_id: Optional[str] = None,
    stage: Optional[str] = None,
    model: Optional[str] = None
):
    """Get detailed prompt execution history with retry block analysis"""
    try:
        analytics = get_extraction_analytics()
        
        # Get recent history across all runs
        history = await analytics.get_recent_prompt_executions(
            days=7,
            stage=stage,
            model=model,
            run_id=run_id
        ) if hasattr(analytics, 'get_recent_prompt_executions') else []
        
        return {"executions": history}
        
    except Exception as e:
        logger.error(f"Failed to get prompt execution history: {e}")
        return {"executions": []}

@router.get("/visual-feedback-analysis/{run_id}")
async def get_visual_feedback_analysis(run_id: str):
    """Get detailed visual feedback analysis for a run"""
    try:
        config = SystemConfig()
        from supabase import create_client
        supabase = create_client(config.supabase_url, config.supabase_service_key)
        
        # Get visual feedback data
        response = supabase.table('visual_feedback_log') \
            .select('*') \
            .eq('extraction_run_id', run_id) \
            .execute()
        
        if not response.data:
            return {"feedback_analysis": None}
        
        # Analyze feedback patterns
        feedback_types = {}
        accuracy_improvements = []
        
        for feedback in response.data:
            fb_type = feedback.get('feedback_type', 'unknown')
            feedback_types[fb_type] = feedback_types.get(fb_type, 0) + 1
            
            if feedback.get('impact_on_accuracy'):
                accuracy_improvements.append(feedback['impact_on_accuracy'])
        
        return {
            "feedback_analysis": {
                "total_feedback": len(response.data),
                "feedback_types": feedback_types,
                "avg_accuracy_improvement": sum(accuracy_improvements) / len(accuracy_improvements) if accuracy_improvements else 0,
                "high_impact_feedback": [f for f in response.data if f.get('high_confidence_issues', 0) > 0]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get visual feedback analysis: {e}")
        return {"feedback_analysis": None}

@router.get("/extraction-logs/{queue_item_id}")
async def get_extraction_logs(
    queue_item_id: int,
    lines: int = Query(100, description="Number of recent log lines to return"),
    level: Optional[str] = Query(None, description="Filter by log level")
):
    """Get real-time extraction logs for a specific queue item"""
    import os
    from collections import deque
    
    # Use current date for log file
    current_date = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "logs",
        f"onshelf_ai_{current_date}.log"
    )
    
    if not os.path.exists(log_file):
        return {"logs": [], "error": "Log file not found"}
    
    relevant_logs = []
    
    # Read the last N lines of the log file
    with open(log_file, 'r') as f:
        tail_lines = deque(f, lines * 10)  # Read more lines to filter
    
    # Parse and filter logs
    for line in tail_lines:
        try:
            log_entry = json.loads(line.strip())
            
            # Check if this log is related to our queue item
            queue_id = log_entry.get('extra', {}).get('queue_item_id')
            message = log_entry.get('message', '')
            
            # Also check if the message mentions our item
            if (queue_id == queue_item_id or 
                f"item {queue_item_id}" in message or 
                f"item_id={queue_item_id}" in message or
                f"queue_item_id={queue_item_id}" in message):
                
                # Apply level filter if specified
                if level and log_entry.get('level') != level:
                    continue
                
                # Format the log entry
                timestamp = log_entry.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp[:19].split('T')[1] if 'T' in timestamp else '??:??:??'
                else:
                    time_str = '??:??:??'
                
                relevant_logs.append({
                    "time": time_str,
                    "level": log_entry.get('level', 'INFO'),
                    "component": log_entry.get('component', 'unknown'),
                    "message": log_entry.get('message', ''),
                    "extra": {k: v for k, v in log_entry.get('extra', {}).items() 
                             if k in ['iteration', 'stage', 'model', 'accuracy', 'cost', 'error', 'duration']}
                })
                
        except:
            # Not a JSON log line, skip
            pass
    
    # If no specific logs found, get general extraction activity
    if not relevant_logs:
        for line in tail_lines[-50:]:
            try:
                log_entry = json.loads(line.strip())
                component = log_entry.get('component', '')
                
                if component in ['extraction_engine', 'langgraph_system', 'orchestrator', 'system_dispatcher']:
                    timestamp = log_entry.get('timestamp', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%H:%M:%S')
                        except:
                            time_str = timestamp[:19].split('T')[1] if 'T' in timestamp else '??:??:??'
                    else:
                        time_str = '??:??:??'
                    
                    relevant_logs.append({
                        "time": time_str,
                        "level": log_entry.get('level', 'INFO'),
                        "component": log_entry.get('component', 'unknown'),
                        "message": log_entry.get('message', '')[:200],  # Truncate long messages
                        "extra": {}
                    })
            except:
                pass
    
    # Limit to requested number of lines
    relevant_logs = relevant_logs[-lines:]
    
    return {
        "queue_item_id": queue_item_id,
        "total_logs": len(relevant_logs),
        "logs": relevant_logs
    }