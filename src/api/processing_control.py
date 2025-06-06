"""
Processing Control API
Controls whether the queue processor runs automatically or manually
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import sys
import asyncio
import signal
import subprocess
import psutil

from ..utils import logger

router = APIRouter(prefix="/api/queue", tags=["Processing Control"])

# Store processing mode in memory (could be in database/Redis for production)
processing_mode = os.getenv('PROCESSING_MODE', 'manual')

@router.post("/processing-mode")
async def set_processing_mode(request: Dict[str, Any]):
    """Set the processing mode (manual or automatic)"""
    global processing_mode
    
    mode = request.get('mode')
    if mode not in ['manual', 'automatic']:
        raise HTTPException(status_code=400, detail="Mode must be 'manual' or 'automatic'")
    
    old_mode = processing_mode
    processing_mode = mode
    
    # If switching to manual, stop the queue processor
    if mode == 'manual' and old_mode == 'automatic':
        await stop_queue_processor()
    
    # If switching to automatic, start the queue processor
    elif mode == 'automatic' and old_mode == 'manual':
        await start_queue_processor()
    
    logger.info(f"Processing mode changed from {old_mode} to {mode}")
    
    return {
        "status": "success",
        "mode": mode,
        "message": f"Processing mode set to {mode}"
    }

@router.get("/processing-mode")
async def get_processing_mode():
    """Get the current processing mode"""
    return {
        "mode": processing_mode,
        "is_running": await is_queue_processor_running()
    }

async def stop_queue_processor():
    """Stop the queue processor if it's running"""
    try:
        # Find the queue processor process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'src.queue_system' in ' '.join(cmdline):
                    logger.info(f"Stopping queue processor (PID: {proc.pid})")
                    proc.terminate()
                    # Wait for graceful shutdown
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        logger.warning("Queue processor didn't stop gracefully, forcing kill")
                        proc.kill()
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        logger.info("No queue processor found to stop")
        return False
        
    except Exception as e:
        logger.error(f"Failed to stop queue processor: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop queue processor: {str(e)}")

async def start_queue_processor():
    """Start the queue processor in the background"""
    try:
        # Check if already running
        if await is_queue_processor_running():
            logger.info("Queue processor is already running")
            return True
        
        # Start the queue processor
        cmd = [sys.executable, "-m", "src.queue_system"]
        
        # Start in background
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        logger.info(f"Started queue processor (PID: {proc.pid})")
        
        # Give it a moment to start
        await asyncio.sleep(2)
        
        # Check if it's still running
        if proc.poll() is None:
            return True
        else:
            # Process ended, check why
            stdout, stderr = proc.communicate()
            logger.error(f"Queue processor failed to start: {stderr.decode()}")
            raise Exception(f"Queue processor failed to start: {stderr.decode()}")
            
    except Exception as e:
        logger.error(f"Failed to start queue processor: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start queue processor: {str(e)}")

async def is_queue_processor_running():
    """Check if the queue processor is currently running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'src.queue_system' in ' '.join(cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception as e:
        logger.error(f"Failed to check queue processor status: {e}")
        return False