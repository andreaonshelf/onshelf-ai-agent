"""
OnShelf AI System
Main system interface for the revolutionary self-debugging AI extraction system
"""

import asyncio
from typing import Optional

from .config import SystemConfig
from .agent.agent import OnShelfAIAgent
from .agent.models import AgentResult
from .websocket.manager import websocket_manager
from .queue.processor import AIExtractionQueueProcessor


class OnShelfAISystem:
    """Main system interface for OnShelf AI"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """Initialize the AI system
        
        Args:
            config: System configuration. If None, uses default from environment
        """
        self.config = config or SystemConfig()
        
        # Validate configuration
        if not self.config.validate():
            raise ValueError("Invalid configuration. Please check environment variables.")
        
        # Initialize agent with WebSocket support
        self.agent = OnShelfAIAgent(self.config, websocket_manager)
        
        # Initialize queue processor for automatic processing
        self.queue_processor = AIExtractionQueueProcessor(self.config)
        
        print("🚀 OnShelf AI System initialized")
        print(f"   Target accuracy: {self.config.target_accuracy:.0%}")
        print(f"   Max iterations: {self.config.max_iterations}")
        print(f"   Models configured: {len(self.config.models)}")
        print(f"   🔄 Queue processor ready")
    
    async def start_queue_processing(self, polling_interval: int = 30):
        """Start automatic queue processing"""
        await self.queue_processor.start_processing(polling_interval)
    
    def stop_queue_processing(self):
        """Stop automatic queue processing"""
        self.queue_processor.stop_processing()
    
    async def process_upload(self, upload_id: str) -> AgentResult:
        """Process an upload through the complete AI system (LEGACY)
        
        Args:
            upload_id: OnShelf upload ID to process
            
        Returns:
            AgentResult with extraction, planogram, and accuracy metrics
        """
        print(f"\n📋 Processing upload: {upload_id} (LEGACY MODE)")
        print("="*50)
        
        try:
            # Run the AI agent
            result = await self.agent.achieve_target_accuracy(upload_id)
            
            # Log summary
            print("\n📊 PROCESSING COMPLETE")
            print(f"   Final accuracy: {result.accuracy:.2%}")
            print(f"   Iterations: {result.iterations_completed}")
            print(f"   Duration: {result.processing_duration:.1f}s")
            print(f"   API cost: £{result.total_api_cost:.2f}")
            print(f"   Human review: {'Required' if result.human_review_required else 'Not required'}")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Processing failed: {e}")
            raise

    async def process_enhanced_media(self, ready_media_id: str) -> AgentResult:
        """Process admin-approved, enhanced images (PRODUCTION)
        
        Args:
            ready_media_id: ID of processed media in media_processing_pipeline table
            
        Returns:
            AgentResult with extraction, planogram, and accuracy metrics
        """
        print(f"\n🔥 Processing enhanced media: {ready_media_id} (PRODUCTION MODE)")
        print("="*60)
        print("   ✅ Admin approved")
        print("   ✅ Quality enhanced") 
        print("   ✅ Preprocessed")
        print("="*60)
        
        try:
            # Run the AI agent with enhanced image processing
            result = await self.agent.achieve_target_accuracy_enhanced(ready_media_id)
            
            # Enhanced logging for production
            print("\n🎯 ENHANCED PROCESSING COMPLETE")
            print(f"   Final accuracy: {result.accuracy:.2%}")
            print(f"   Iterations: {result.iterations_completed}")
            print(f"   Duration: {result.processing_duration:.1f}s")
            print(f"   API cost: £{result.total_api_cost:.2f}")
            print(f"   Human review: {'Required' if result.human_review_required else 'Not required'}")
            print(f"   Enhanced features: Admin approved, Quality enhanced")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Enhanced processing failed: {e}")
            raise
    
    async def process_bulk(self, upload_ids: list[str], max_concurrent: int = 3) -> dict[str, AgentResult]:
        """Process multiple uploads concurrently
        
        Args:
            upload_ids: List of upload IDs to process
            max_concurrent: Maximum concurrent processing (default 3)
            
        Returns:
            Dictionary mapping upload_id to AgentResult
        """
        print(f"\n📦 Processing {len(upload_ids)} uploads (max {max_concurrent} concurrent)")
        
        results = {}
        
        # Process in batches
        for i in range(0, len(upload_ids), max_concurrent):
            batch = upload_ids[i:i + max_concurrent]
            
            # Process batch concurrently
            tasks = [self.process_upload(upload_id) for upload_id in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Store results
            for upload_id, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"❌ Failed to process {upload_id}: {result}")
                    results[upload_id] = None
                else:
                    results[upload_id] = result
        
        # Summary
        successful = sum(1 for r in results.values() if r is not None)
        print(f"\n✅ Bulk processing complete: {successful}/{len(upload_ids)} successful")
        
        return results
    
    def get_system_stats(self) -> dict:
        """Get system statistics"""
        return {
            'config': {
                'target_accuracy': self.config.target_accuracy,
                'max_iterations': self.config.max_iterations,
                'models': list(self.config.models.keys())
            },
            'websocket_connections': websocket_manager.get_connection_stats(),
            'agent': {
                'current_state': self.agent.current_state.value if self.agent.current_state else 'idle',
                'active_agent_id': self.agent.agent_id
            },
            'queue_processor': self.queue_processor.get_stats()
        }


# Convenience function for quick processing
async def process_upload(upload_id: str, config: Optional[SystemConfig] = None) -> AgentResult:
    """Quick function to process a single upload
    
    Args:
        upload_id: OnShelf upload ID
        config: Optional system configuration
        
    Returns:
        AgentResult
    """
    system = OnShelfAISystem(config)
    return await system.process_upload(upload_id) 