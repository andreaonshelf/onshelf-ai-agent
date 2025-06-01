"""
Configuration Integration for Queue Processor
Patches the missing integration between queue configuration and orchestrators
"""

import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
import time

from ..config import SystemConfig
from ..utils import logger
from ..orchestrator.master_orchestrator import MasterOrchestrator


async def process_queue_item_with_config(queue_processor, queue_item: Dict[str, Any]):
    """
    Enhanced queue processing that passes extraction configuration to orchestrators
    """
    queue_id = queue_item['id']
    ready_media_id = queue_item.get('ready_media_id')
    enhanced_image_path = queue_item.get('enhanced_image_path')
    
    # Extract configuration from queue item
    extraction_config = queue_item.get('extraction_config') or queue_item.get('enhanced_config') or {}
    
    # Also check for legacy columns
    if not extraction_config and queue_item.get('selected_systems'):
        # Build config from legacy columns
        extraction_config = {
            'system': queue_item.get('current_extraction_system', 'custom_consensus'),
            'systems': queue_item.get('selected_systems', ['custom_consensus']),
            'max_budget': 2.00,  # Default budget
            'pipeline': {
                'temperature': 0.1,
                'orchestrator_model': 'claude-4-opus',
                'enable_comparison': len(queue_item.get('selected_systems', [])) > 1
            }
        }
    
    try:
        # Mark as processing
        await queue_processor._update_queue_status(queue_id, "processing")
        
        logger.info(
            f"🔥 Processing queue item {queue_id} with configuration",
            component="queue_processor",
            queue_id=queue_id,
            ready_media_id=ready_media_id,
            has_config=bool(extraction_config),
            system=extraction_config.get('system', 'default')
        )
        
        # Process with master orchestrator (it handles image loading)
        start_time = time.time()
        
        # Create orchestrator with system config
        config = queue_processor.config
        
        # Override with extraction config if provided
        if extraction_config:
            # Apply system selection
            if 'system' in extraction_config:
                config.extraction_system = extraction_config['system']
            
            # Apply pipeline settings
            if 'pipeline' in extraction_config:
                pipeline = extraction_config['pipeline']
                if 'temperature' in pipeline:
                    config.model_temperature = pipeline['temperature']
                if 'orchestrator_model' in pipeline:
                    config.orchestrator_model = pipeline['orchestrator_model']
        
        orchestrator = MasterOrchestrator(config)
        
        # Process with master orchestrator using upload_id and configuration
        upload_id = queue_item['upload_id']
        result = await orchestrator.achieve_target_accuracy(
            upload_id,
            configuration=extraction_config  # Pass the full configuration
        )
        
        processing_duration = time.time() - start_time
        
        # Update queue with results
        await queue_processor._update_queue_with_results(queue_id, result, processing_duration)
        
        # Track performance if we have prompt IDs
        if extraction_config and 'prompts' in extraction_config:
            await track_prompt_performance(extraction_config['prompts'], result)
        
        logger.info(
            f"✅ Successfully processed queue item {queue_id}",
            component="queue_processor",
            queue_id=queue_id,
            ready_media_id=ready_media_id,
            final_accuracy=result.final_accuracy if hasattr(result, 'final_accuracy') else 0.0,
            duration=processing_duration,
            system_used=extraction_config.get('system', 'default')
        )
        
        queue_processor.processing_count += 1
        
    except Exception as e:
        # Mark as failed
        await queue_processor._update_queue_status(queue_id, "failed", str(e))
        
        logger.error(
            f"❌ Failed to process queue item {queue_id}: {e}",
            component="queue_processor",
            queue_id=queue_id,
            ready_media_id=ready_media_id,
            error=str(e)
        )


async def track_prompt_performance(prompts: Dict[str, str], result: Any):
    """Track performance for prompts used in extraction"""
    try:
        # Import here to avoid circular imports
        from ..api.prompt_management import track_prompt_performance as api_track_performance
        
        # Track performance for each prompt used
        for prompt_type, prompt_id in prompts.items():
            if prompt_id and hasattr(result, 'final_accuracy'):
                performance_data = {
                    'success': result.final_accuracy > 0.85,
                    'accuracy': result.final_accuracy,
                    'cost': getattr(result, 'total_api_cost', 0.05),
                    'iterations': getattr(result, 'iterations_completed', 1)
                }
                
                # Call the API endpoint to track performance
                await api_track_performance(prompt_id, performance_data)
                
    except Exception as e:
        logger.warning(f"Failed to track prompt performance: {e}")


# Patch for extraction orchestrator to use configuration
def create_extraction_orchestrator_with_config(config: SystemConfig, extraction_config: Optional[Dict] = None):
    """
    Create extraction orchestrator that respects configuration overrides
    """
    from ..orchestrator.extraction_orchestrator import ExtractionOrchestrator
    
    # Create base orchestrator
    orchestrator = ExtractionOrchestrator(config)
    
    # Apply configuration overrides
    if extraction_config:
        # Override temperature
        if 'pipeline' in extraction_config and 'temperature' in extraction_config['pipeline']:
            orchestrator.temperature = extraction_config['pipeline']['temperature']
        
        # Override model selection
        if 'models' in extraction_config:
            orchestrator.model_overrides = extraction_config['models']
        
        # Override prompts
        if 'prompts' in extraction_config:
            orchestrator.prompt_overrides = extraction_config['prompts']
    
    # Patch the model selection method
    original_select_model = orchestrator._select_model_for_agent
    
    def patched_select_model(agent_number: int, context: Any) -> str:
        # Check for model overrides first
        if hasattr(orchestrator, 'model_overrides'):
            # Determine extraction type based on context
            extraction_type = 'structure' if context.iteration == 1 else 'products'
            if extraction_type in orchestrator.model_overrides:
                return orchestrator.model_overrides[extraction_type]
        
        # Fall back to original selection
        return original_select_model(agent_number, context)
    
    orchestrator._select_model_for_agent = patched_select_model
    
    return orchestrator


# Patch for master orchestrator to pass configuration
def patch_master_orchestrator_with_config():
    """
    Patch master orchestrator to pass configuration to sub-orchestrators
    """
    from ..orchestrator.master_orchestrator import MasterOrchestrator
    
    # Store original method
    original_achieve_target = MasterOrchestrator.achieve_target_accuracy
    
    async def patched_achieve_target_accuracy(self, upload_id: str, configuration: Optional[Dict] = None):
        """Enhanced version that uses configuration"""
        
        # Store configuration in instance
        self.extraction_config = configuration
        
        # If we have configuration, update the extraction orchestrator
        if configuration:
            # Create new extraction orchestrator with config
            self.extraction_orchestrator = create_extraction_orchestrator_with_config(
                self.config,
                configuration
            )
        
        # Call original method
        return await original_achieve_target(self, upload_id, configuration)
    
    # Apply patch
    MasterOrchestrator.achieve_target_accuracy = patched_achieve_target_accuracy


# Apply patches when module is imported
patch_master_orchestrator_with_config()