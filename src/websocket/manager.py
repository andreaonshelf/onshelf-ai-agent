"""
WebSocket Manager
Real-time updates during Agent iterations
"""

from typing import Dict, List, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio


class WebSocketManager:
    """Manage WebSocket connections for real-time Agent updates"""
    
    def __init__(self):
        # Store active connections by agent_id
        self.connections: Dict[str, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str, client_id: str = None):
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Initialize agent connection list if needed
        if agent_id not in self.connections:
            self.connections[agent_id] = []
        
        # Add connection
        self.connections[agent_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[f"{agent_id}:{client_id or 'anonymous'}"] = {
            'connected_at': datetime.utcnow(),
            'agent_id': agent_id,
            'client_id': client_id
        }
        
        # Send initial connection confirmation
        await websocket.send_json({
            'type': 'connection_established',
            'agent_id': agent_id,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket, agent_id: str):
        """Remove WebSocket connection"""
        if agent_id in self.connections:
            try:
                self.connections[agent_id].remove(websocket)
                # Clean up empty lists
                if not self.connections[agent_id]:
                    del self.connections[agent_id]
            except ValueError:
                pass  # Connection already removed
    
    async def broadcast_to_agent(self, agent_id: str, message: Dict):
        """Broadcast message to all connections watching an agent"""
        if agent_id not in self.connections:
            return
        
        # Add timestamp if not present
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()
        
        # Send to all connections
        disconnected = []
        for websocket in self.connections[agent_id]:
            try:
                await websocket.send_json(message)
            except:
                # Mark for removal if connection failed
                disconnected.append(websocket)
        
        # Clean up disconnected connections
        for websocket in disconnected:
            self.disconnect(websocket, agent_id)
    
    async def broadcast_iteration_start(self, agent_id: str, iteration: int, max_iterations: int):
        """Broadcast iteration start event"""
        message = {
            'type': 'iteration_start',
            'agent_id': agent_id,
            'iteration': iteration,
            'max_iterations': max_iterations,
            'progress': iteration / max_iterations
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_state_change(self, agent_id: str, new_state: str):
        """Broadcast agent state change"""
        message = {
            'type': 'state_change',
            'agent_id': agent_id,
            'state': new_state
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_accuracy_update(self, agent_id: str, accuracy: float, details: Dict):
        """Broadcast accuracy improvement"""
        message = {
            'type': 'accuracy_update',
            'agent_id': agent_id,
            'accuracy': accuracy,
            'accuracy_percent': f"{accuracy:.1%}",
            **details
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_extraction_progress(self, agent_id: str, step: str, status: str):
        """Broadcast extraction step progress"""
        message = {
            'type': 'extraction_progress',
            'agent_id': agent_id,
            'step': step,
            'status': status
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_mismatch_found(self, agent_id: str, mismatch: Dict):
        """Broadcast when a mismatch is identified"""
        message = {
            'type': 'mismatch_found',
            'agent_id': agent_id,
            'mismatch': mismatch
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_planogram_update(self, agent_id: str, planogram_id: str, preview_url: str = None):
        """Broadcast planogram generation/update"""
        message = {
            'type': 'planogram_update',
            'agent_id': agent_id,
            'planogram_id': planogram_id,
            'preview_url': preview_url
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_escalation(self, agent_id: str, final_accuracy: float, reason: str):
        """Broadcast human escalation needed"""
        message = {
            'type': 'human_escalation',
            'agent_id': agent_id,
            'final_accuracy': final_accuracy,
            'final_accuracy_percent': f"{final_accuracy:.1%}",
            'escalation_reason': reason
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def broadcast_completion(self, agent_id: str, result: Dict):
        """Broadcast agent completion"""
        message = {
            'type': 'agent_completed',
            'agent_id': agent_id,
            'success': result.get('target_achieved', False),
            'final_accuracy': result.get('accuracy', 0),
            'iterations': result.get('iterations_completed', 0),
            'duration_seconds': result.get('processing_duration', 0)
        }
        await self.broadcast_to_agent(agent_id, message)
    
    async def send_heartbeat(self):
        """Send periodic heartbeat to keep connections alive"""
        while True:
            await asyncio.sleep(30)  # Every 30 seconds
            
            for agent_id, connections in self.connections.items():
                message = {
                    'type': 'heartbeat',
                    'agent_id': agent_id
                }
                
                disconnected = []
                for websocket in connections:
                    try:
                        await websocket.send_json(message)
                    except:
                        disconnected.append(websocket)
                
                # Clean up disconnected
                for websocket in disconnected:
                    self.disconnect(websocket, agent_id)
    
    def get_connection_stats(self) -> Dict:
        """Get statistics about active connections"""
        stats = {
            'total_agents': len(self.connections),
            'total_connections': sum(len(conns) for conns in self.connections.values()),
            'agents': {}
        }
        
        for agent_id, connections in self.connections.items():
            stats['agents'][agent_id] = {
                'connection_count': len(connections),
                'oldest_connection': min(
                    (meta['connected_at'] for key, meta in self.connection_metadata.items() 
                     if meta['agent_id'] == agent_id),
                    default=None
                )
            }
        
        return stats


# Global WebSocket manager instance
websocket_manager = WebSocketManager() 