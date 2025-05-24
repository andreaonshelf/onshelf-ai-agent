"""
OnShelf AI Agent System - Main Entry Point
Run the complete system with API, WebSocket, and Dashboard
"""

import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
import subprocess
import sys
import os

from src import OnShelfAISystem, SystemConfig
from src.websocket import websocket_manager
from src.agent.models import AgentResult


# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("🚀 Starting OnShelf AI Agent System...")
    
    # Start WebSocket heartbeat
    asyncio.create_task(websocket_manager.send_heartbeat())
    
    yield
    
    # Shutdown
    print("👋 Shutting down OnShelf AI Agent System...")


app = FastAPI(
    title="OnShelf AI Agent API",
    description="Revolutionary self-debugging AI extraction system for retail shelf analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize system
system = OnShelfAISystem()


# =====================================================
# REST API ENDPOINTS
# =====================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "OnShelf AI Agent System",
        "version": "1.0.0",
        "stats": system.get_system_stats()
    }


@app.post("/api/v1/process/{upload_id}")
async def process_upload(upload_id: str):
    """Process a single upload through the AI system"""
    try:
        result = await system.process_upload(upload_id)
        return {
            "success": True,
            "agent_id": result.agent_id,
            "accuracy": result.accuracy,
            "iterations": result.iterations_completed,
            "human_review_required": result.human_review_required,
            "duration_seconds": result.processing_duration,
            "api_cost": result.total_api_cost
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/bulk")
async def process_bulk(upload_ids: list[str], max_concurrent: int = 3):
    """Process multiple uploads"""
    try:
        results = await system.process_bulk(upload_ids, max_concurrent)
        return {
            "success": True,
            "total": len(upload_ids),
            "processed": sum(1 for r in results.values() if r is not None),
            "results": {
                upload_id: {
                    "success": result is not None,
                    "accuracy": result.accuracy if result else None,
                    "human_review": result.human_review_required if result else None
                }
                for upload_id, result in results.items()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agent/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get current status of an AI agent"""
    # This would query the database
    return {
        "agent_id": agent_id,
        "status": "running",
        "current_iteration": 2,
        "current_accuracy": 0.87,
        "estimated_completion": 120  # seconds
    }


# =====================================================
# WEBSOCKET ENDPOINTS
# =====================================================

@app.websocket("/ws/agent/{agent_id}")
async def websocket_agent_updates(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time agent updates"""
    await websocket_manager.connect(websocket, agent_id)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, agent_id)


@app.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()


# =====================================================
# DASHBOARD LAUNCHER
# =====================================================

def run_streamlit_dashboard():
    """Run Streamlit dashboard in a separate process"""
    dashboard_script = os.path.join(os.path.dirname(__file__), "dashboard.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_script])


# =====================================================
# MAIN EXECUTION
# =====================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OnShelf AI Agent System")
    parser.add_argument("--mode", choices=["api", "dashboard", "all"], default="all",
                       help="Run mode: api, dashboard, or all")
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    if args.mode in ["dashboard", "all"]:
        # Start dashboard in a separate thread
        dashboard_thread = threading.Thread(target=run_streamlit_dashboard, daemon=True)
        dashboard_thread.start()
        print("📊 Dashboard starting on http://localhost:8501")
    
    if args.mode in ["api", "all"]:
        # Run FastAPI with Uvicorn
        print(f"🚀 API starting on http://{args.host}:{args.port}")
        print(f"📡 WebSocket available at ws://{args.host}:{args.port}/ws/agent/{{agent_id}}")
        
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    
    elif args.mode == "dashboard":
        # Keep main thread alive if only running dashboard
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...") 