"""
Master Orchestrator
Top-level orchestrator managing extraction + planogram + feedback loops
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from PIL import Image, ImageDraw, ImageFont
import io

from ..config import SystemConfig
from .extraction_orchestrator import ExtractionOrchestrator
from .planogram_orchestrator import PlanogramOrchestrator
from .feedback_manager import CumulativeFeedbackManager, ImageComparison
from ..comparison.image_comparison_agent import ImageComparisonAgent
from ..evaluation.human_evaluation import HumanEvaluationSystem
from ..models.extraction_models import ExtractionResult
from ..models.shelf_structure import ShelfStructure
from ..utils import logger
from .models import MasterResult
from ..extraction.state_tracker import get_state_tracker, ExtractionStage, ExtractionStatus
from ..planogram.models import VisualPlanogram
from .monitoring_hooks import monitoring_hooks
from .smart_iteration_manager import SmartIterationManager


class MasterOrchestrator:
    """Top-level orchestrator managing extraction + planogram + feedback loops"""
    
    def __init__(self, config: SystemConfig, supabase_client=None, queue_item_id: Optional[int] = None):
        self.config = config
        self.queue_item_id = queue_item_id
        # Don't initialize extraction orchestrator here - do it per run
        self.extraction_orchestrator = None
        self.planogram_orchestrator = PlanogramOrchestrator(config)
        self.feedback_manager = CumulativeFeedbackManager()
        self.comparison_agent = ImageComparisonAgent(config)
        self.human_evaluation = HumanEvaluationSystem(config)
        self.state_tracker = get_state_tracker(supabase_client)
        self.smart_iteration_manager = SmartIterationManager()
        
        logger.info(
            "Master Orchestrator initialized",
            component="master_orchestrator",
            target_accuracy=config.target_accuracy,
            max_iterations=config.max_iterations
        )
    
    async def achieve_target_accuracy(self, 
                                    upload_id: str, 
                                    target_accuracy: float = 0.95,
                                    max_iterations: int = 5,
                                    queue_item_id: Optional[int] = None,
                                    system: str = "custom_consensus",
                                    configuration: Optional[Dict[str, Any]] = None) -> MasterResult:
        """Main entry point: decides whether to use stage-based or iteration-based approach"""
        
        # Check if stage-based execution is configured
        stages = configuration.get('stages', {}) if configuration else {}
        stage_models = configuration.get('stage_models', {}) if configuration else {}
        
        # Use stage-based if we have stage configurations with models
        if stages and stage_models and any(models for models in stage_models.values()):
            stage_order = configuration.get('stage_order', ['structure', 'products', 'details'])
            return await self.execute_stage_pipeline(
                upload_id=upload_id,
                queue_item_id=queue_item_id,
                target_accuracy=target_accuracy,
                max_iterations=max_iterations,
                system=system,
                configuration=configuration,
                stage_order=stage_order
            )
        
        # Otherwise use traditional iteration-based approach
        
        start_time = time.time()
        agent_id = str(uuid.uuid4())
        run_id = f"run_{upload_id}_{agent_id[:8]}"
        
        logger.info(
            f"Starting master orchestration for upload {upload_id}",
            component="master_orchestrator",
            upload_id=upload_id,
            target_accuracy=target_accuracy,
            max_iterations=max_iterations,
            agent_id=agent_id,
            run_id=run_id
        )
        
        # Create extraction run in state tracker
        if queue_item_id:
            extraction_run = await self.state_tracker.create_run(
                run_id=run_id,
                queue_item_id=queue_item_id,
                upload_id=upload_id,
                system=system,
                configuration=configuration or {}
            )
            
            # Initialize monitoring
            await monitoring_hooks.update_extraction_stage(
                queue_item_id, 
                "Initializing",
                {"message": "Starting extraction pipeline"}
            )
        
        # Get images
        images = await self._get_images(upload_id)
        
        # Initialize the appropriate extraction system based on selection
        from ..systems.base_system import ExtractionSystemFactory
        
        # Map UI system names to factory system names
        system_type_map = {
            'custom_consensus': 'custom',
            'langgraph': 'langgraph',
            'langgraph_based': 'langgraph',  # Legacy support
            'hybrid': 'hybrid'
        }
        
        system_type = system_type_map.get(system, 'custom')
        
        logger.info(
            f"Initializing {system_type} extraction system",
            component="master_orchestrator",
            ui_system=system,
            mapped_system=system_type
        )
        
        # Create the selected extraction system
        self.extraction_system = ExtractionSystemFactory.get_system(
            system_type=system_type,
            config=self.config
        )
        
        # Pass configuration to the system
        if configuration:
            self.extraction_system.configuration = configuration
            self.extraction_system.temperature = configuration.get('temperature', 0.7)
            self.extraction_system.stage_models = configuration.get('stage_models', {})
            self.extraction_system.stage_prompts = configuration.get('stage_prompts', {})
        
        # Initialize tracking
        iteration_history = []
        best_accuracy = 0.0
        best_planogram = None
        structure_context = None
        previous_attempts = []
        
        # Store detailed iteration data for debugging
        self.iteration_details = {
            'upload_id': upload_id,
            'iterations': []
        }
        
        # Log configuration usage
        if configuration and queue_item_id:
            from ..utils.model_usage_tracker import get_model_usage_tracker
            tracker = get_model_usage_tracker()
            
            # Create configuration name from settings
            config_name = f"{system}_{configuration.get('temperature', 0.7)}_{configuration.get('orchestrator_model', 'default')}"
            
            await tracker.log_configuration_usage(
                configuration_name=config_name,
                configuration_id=f"config_{queue_item_id}_{run_id}",
                system=system,
                orchestrator_model=configuration.get('orchestrator_model', 'claude-4-opus'),
                orchestrator_prompt=configuration.get('orchestrator_prompt', ''),
                temperature=configuration.get('temperature', 0.7),
                max_budget=configuration.get('max_budget', 2.0),
                stage_models=configuration.get('stage_models', {})
            )
        
        try:
            # Let the extraction system handle ALL orchestration
            # It will manage iterations, visual feedback, and intelligent decisions
            extraction_result = await self.extraction_system.extract_with_iterations(
                image_data=images['enhanced'],
                upload_id=upload_id,
                target_accuracy=target_accuracy,
                max_iterations=max_iterations,
                configuration=configuration
            )
            
            # Create simplified result
            total_duration = time.time() - start_time
            
            result = MasterResult(
                final_accuracy=getattr(extraction_result, 'overall_accuracy', 0.8),
                target_achieved=getattr(extraction_result, 'overall_accuracy', 0.8) >= target_accuracy,
                iterations_completed=getattr(extraction_result, 'iteration_count', 1),
                iteration_history=[],  # System manages its own history now
                needs_human_review=getattr(extraction_result, 'overall_accuracy', 0.8) < target_accuracy,
                structure_analysis=getattr(extraction_result, 'structure', None),
                best_planogram=None,  # System generates planograms internally
                total_duration=total_duration,
                total_cost=getattr(extraction_result, 'api_cost_estimate', 0.0)
            )
            
            return result
            
        except Exception as e:
            # Re-raise the exception
            raise
            
                # Step 2: Generate planogram
                # Get abstraction level from comparison config or use default
                comparison_config = configuration.get('comparison_config', {}) if configuration else {}
                abstraction_level = "product_view"  # Default
                
                # If abstraction layers are specified, use the first enabled one
                if comparison_config.get('abstraction_layers'):
                    enabled_layers = [layer for layer in comparison_config['abstraction_layers'] if layer.get('enabled', True)]
                    if enabled_layers:
                        # Map layer ID to abstraction level
                        layer_mapping = {
                            'brand': 'brand_view',
                            'product': 'product_view',
                            'confidence': 'product_view',  # Use product view with confidence coloring
                            'price_range': 'product_view',  # Use product view with price info
                            'category': 'product_view'  # Use product view with category grouping
                        }
                        abstraction_level = layer_mapping.get(enabled_layers[0]['id'], 'product_view')
                
                planogram_result = await self.planogram_orchestrator.generate_for_agent_iteration(
                    agent_number=iteration,
                    extraction_result=extraction_result,
                    structure_context=structure_context,
                    abstraction_level=abstraction_level,
                    original_image=images['enhanced']
                )
            
                # Update state: Validation
                if queue_item_id:
                    await self.state_tracker.update_stage(
                        run_id=run_id,
                        stage=ExtractionStage.VALIDATION
                    )
            
                # Step 3: Visual comparison with planogram
                validation_start = time.time()
                
                # Get comparison config from configuration
                comparison_config = configuration.get('comparison_config', {}) if configuration else {}
                
                # Always render planogram to PNG for our visual comparison approach
                planogram_png = await self._render_planogram_to_png(
                    planogram_result.planogram,
                    extraction_result
                )
                
                # Step 3b: AI comparison analysis with rendered image (skip if no PNG)
                if planogram_png:
                    # Use model from comparison config or fall back to configuration/default
                    comparison_model = (
                        comparison_config.get('model') or 
                        configuration.get('comparison_model', 'gpt-4-vision-preview') if configuration else 'gpt-4-vision-preview'
                    )
                    
                    # Get comparison prompt from configuration
                    comparison_prompt = None
                    if configuration and 'stage_prompts' in configuration:
                        comparison_prompt = configuration['stage_prompts'].get('comparison')
                    
                    comparison_result = await self.comparison_agent.compare_image_vs_planogram(
                        original_image=images['enhanced'],
                        planogram=planogram_result.planogram,
                        structure_context=structure_context,
                        planogram_image=planogram_png,
                        model=comparison_model,
                        comparison_prompt=comparison_prompt
                    )
                else:
                    # Skip comparison entirely if no PNG - no API call
                    logger.warning("Skipping visual comparison - no planogram PNG available")
                    comparison_result = ImageComparison(
                        matches=[],
                        mismatches=[],
                        missing_products=[],
                        extra_products=[],
                        overall_similarity=0.0  # Unknown accuracy
                    )
            
                # Step 4: Calculate accuracy and analyze failures
                accuracy_analysis = self.feedback_manager.analyze_accuracy_with_failure_areas(
                    comparison_result, structure_context
                )
            
                current_accuracy = accuracy_analysis.overall_accuracy
            
                # Record validation metrics
                if queue_item_id:
                    validation_time = time.time() - validation_start
                    await self.state_tracker.record_stage_metrics(
                        run_id=run_id,
                        stage=ExtractionStage.VALIDATION,
                        metrics={
                            "duration_seconds": validation_time,
                            "accuracy": current_accuracy
                        }
                    )
            
                # Step 5: Track iteration with detailed data for debugging
                iteration_data = {
                    "iteration": iteration,
                    "accuracy": current_accuracy,
                    "extraction_result": extraction_result,
                    "planogram": planogram_result,
                    "comparison_result": comparison_result,
                    "accuracy_analysis": accuracy_analysis,
                    "failure_areas": accuracy_analysis.failure_areas,
                    "locked_positions": accuracy_analysis.high_confidence_positions,
                    "timestamp": datetime.utcnow()
                }
                iteration_history.append(iteration_data)
                previous_attempts.append(extraction_result)
            
                # Store detailed iteration data for dashboard
                self.iteration_details['iterations'].append({
                    "iteration": iteration,
                    "accuracy": current_accuracy,
                    "timestamp": datetime.utcnow().isoformat(),
                    "extraction_data": {
                        "total_products": len(extraction_result.products),
                        "products": [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in extraction_result.products],
                        "model_used": extraction_result.model_used,
                        "confidence": extraction_result.overall_confidence
                    },
                    "planogram_svg": planogram_result.planogram.svg_data if hasattr(planogram_result.planogram, 'svg_data') else None,
                    "structure": {
                        "shelves": structure_context.shelf_count,
                        "width": structure_context.estimated_width_meters
                    },
                    "failure_areas": [area.model_dump() if hasattr(area, 'model_dump') else area.dict() for area in accuracy_analysis.failure_areas] if accuracy_analysis.failure_areas else []
                })
            
                # Step 6: Use smart iteration manager to analyze results
                extraction_focus = self.smart_iteration_manager.analyze_iteration_results(
                    iteration=iteration,
                    extraction_result=extraction_result,
                    accuracy_analysis=accuracy_analysis,
                    structure=structure_context
                )
                
                # Update monitoring with smart iteration details
                if queue_item_id:
                    locked_items_desc = [
                        f"{lock.product_data.get('name', 'Product')} (Shelf {lock.shelf})"
                        for lock in list(self.smart_iteration_manager.locked_positions.values())[:5]
                    ]
                    if len(self.smart_iteration_manager.locked_positions) > 5:
                        locked_items_desc.append(f"... and {len(self.smart_iteration_manager.locked_positions) - 5} more")
                    
                    await monitoring_hooks.update_monitor(queue_item_id, {
                        "locked_count": len(self.smart_iteration_manager.locked_positions),
                        "locked_items": locked_items_desc,
                        "reextract_shelves": list(extraction_focus.shelves_to_reextract),
                        "issues_found": list(extraction_focus.specific_issues.keys())
                    })
                
                # Update best result
                if current_accuracy > best_accuracy:
                    best_accuracy = current_accuracy
                    best_planogram = planogram_result
            
                # Step 7: Check if target achieved
                if current_accuracy >= target_accuracy:
                    logger.info(
                        f"Target accuracy {target_accuracy:.1%} achieved!",
                        component="master_orchestrator",
                        final_accuracy=current_accuracy,
                        iterations=iteration
                    )
                    break
            
                # Step 7: Prepare next iteration focus areas
                if iteration < max_iterations:
                    logger.info(
                        f"Accuracy: {current_accuracy:.1%} - Preparing iteration {iteration + 1}",
                        component="master_orchestrator",
                        current_accuracy=current_accuracy,
                        next_iteration=iteration + 1
                    )
                
                    # Create focused instructions for next iteration
                    instructions = self.feedback_manager.create_focused_extraction_instructions(
                        accuracy_analysis.failure_areas,
                        accuracy_analysis.high_confidence_positions,
                        structure_context
                    )
                
                    logger.info(
                        f"Next iteration will focus on {len(instructions.improve_focus)} areas",
                        component="master_orchestrator",
                        focus_areas=len(instructions.improve_focus),
                        locked_positions=len(instructions.preserve_exact),
                        efficiency_gain=instructions.efficiency_metrics['efficiency_gain']
                    )
            
        except Exception as e:
            logger.error(f"Error during extraction: {e}", component="master_orchestrator", error=str(e))
            
            # Mark run as failed in state tracker
            if queue_item_id:
                await self.state_tracker.fail_run(
                    run_id=run_id,
                    error_message=str(e),
                    stage=ExtractionStage.STRUCTURE_EXTRACTION if iteration == 1 else ExtractionStage.VALIDATION
                )
            
            # Re-raise the exception
            raise
        
        # Calculate totals
        total_duration = time.time() - start_time
        total_cost = sum(iter_data['extraction_result'].api_cost_estimate for iter_data in iteration_history)
        
        # Determine if human review needed
        needs_human_review = current_accuracy < target_accuracy
        
        # Complete the extraction run in state tracker
        if queue_item_id:
            final_status = ExtractionStatus.COMPLETED if best_accuracy >= target_accuracy else ExtractionStatus.REQUIRES_REVIEW
            await self.state_tracker.complete_run(
                run_id=run_id,
                status=final_status,
                result_data={
                    "final_accuracy": best_accuracy,
                    "target_achieved": best_accuracy >= target_accuracy,
                    "iterations": len(iteration_history),
                    "best_planogram_id": best_planogram.planogram_id if best_planogram else None,
                    "total_duration": total_duration,
                    "total_cost": total_cost
                }
            )
            
            # Update configuration stats
            if configuration:
                from ..utils.model_usage_tracker import get_model_usage_tracker
                tracker = get_model_usage_tracker()
                
                config_name = f"{system}_{configuration.get('temperature', 0.7)}_{configuration.get('orchestrator_model', 'default')}"
                
                await tracker.update_configuration_stats(
                    configuration_name=config_name,
                    accuracy=best_accuracy,
                    cost=total_cost,
                    duration_seconds=int(total_duration),
                    success=best_accuracy >= target_accuracy
                )
        
        # Create final result
        result = MasterResult(
            final_accuracy=best_accuracy,
            target_achieved=best_accuracy >= target_accuracy,
            iterations_completed=len(iteration_history),
            iteration_history=iteration_history,
            needs_human_review=needs_human_review,
            structure_analysis=structure_context,
            best_planogram=best_planogram,
            total_duration=total_duration,
            total_cost=total_cost
        )
        
        # Trigger human evaluation if needed
        if needs_human_review:
            await self._trigger_human_evaluation(upload_id, result)
        
        # Store iteration data for dashboard viewing
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Assuming queue_item_id is the upload_id or we need to get it
                # For now, use a hash of upload_id as a simple ID
                queue_item_id = abs(hash(upload_id)) % 100000
                
                async with session.post(
                    f"http://localhost:8000/api/iterations/store/{queue_item_id}",
                    json=self.iteration_details
                ) as response:
                    if response.status == 200:
                        logger.info(f"Stored iteration data for queue item {queue_item_id}", component="master_orchestrator")
                    else:
                        logger.warning(f"Failed to store iteration data: {response.status}", component="master_orchestrator")
        except Exception as e:
            logger.error(f"Failed to store iteration data: {e}", component="master_orchestrator")
        
        logger.info(
            f"Master orchestration complete",
            component="master_orchestrator",
            final_accuracy=best_accuracy,
            iterations_completed=len(iteration_history),
            total_duration=total_duration,
            total_cost=total_cost,
            human_review_required=needs_human_review
        )
        
        return result
    
    async def _get_images(self, upload_id: str) -> Dict[str, bytes]:
        """Get images for processing from Supabase storage"""
        from supabase import create_client
        
        try:
            supabase = create_client(self.config.supabase_url, self.config.supabase_service_key)
            
            # First try to get from queue item's enhanced_image_path
            queue_result = supabase.table("ai_extraction_queue").select("enhanced_image_path").eq("upload_id", upload_id).execute()
            
            file_path = None
            if queue_result.data and queue_result.data[0].get("enhanced_image_path"):
                file_path = queue_result.data[0]["enhanced_image_path"]
                logger.info(f"Found image path in queue item: {file_path}")
            
            # If no path in queue item, get from media_files table (filter for images only)
            if not file_path:
                media_result = supabase.table("media_files").select("file_path").eq("upload_id", upload_id).eq("file_type", "image").neq("file_path", None).limit(1).execute()
                
                if media_result.data and media_result.data[0].get("file_path"):
                    file_path = media_result.data[0]["file_path"]
                    logger.info(f"Found image path in media_files: {file_path}")
                    
                    # Update queue item with this path for future use (only if queue item exists)
                    if queue_result.data:
                        try:
                            supabase.table("ai_extraction_queue").update({
                                "enhanced_image_path": file_path
                            }).eq("upload_id", upload_id).execute()
                            logger.info(f"Updated queue item with image path: {file_path}")
                        except Exception as update_error:
                            logger.warning(f"Failed to update queue item with image path: {update_error}")
                    else:
                        logger.warning(f"No queue item found for upload {upload_id}, cannot update enhanced_image_path")
                else:
                    raise Exception(f"No image files found for upload {upload_id}")
            
            if not file_path:
                raise Exception(f"No image path found for upload {upload_id}")
            
            # Download image from Supabase storage
            image_data = supabase.storage.from_("retail-captures").download(file_path)
            
            logger.info(
                f"Loaded image for upload {upload_id}: {len(image_data)} bytes",
                component="master_orchestrator",
                upload_id=upload_id,
                file_path=file_path,
                size_mb=len(image_data) / 1024 / 1024
            )
            
            # Return both enhanced and original as the same image for now
            return {
                'enhanced': image_data,
                'original': image_data,
                'overview': image_data  # Some steps expect 'overview'
            }
            
        except Exception as e:
            logger.error(
                f"Failed to load images for upload {upload_id}: {e}",
                component="master_orchestrator",
                upload_id=upload_id,
                error=str(e)
            )
            raise Exception(f"No image data found for upload {upload_id}: {e}")
    
    def _get_focus_areas_from_previous(self, iteration_history: List[Dict]) -> List[Dict]:
        """Extract focus areas from smart iteration manager"""
        if not self.smart_iteration_manager.extraction_history:
            return []
        
        # Get the latest extraction focus
        latest_history = self.smart_iteration_manager.extraction_history[-1]
        extraction_focus = latest_history.get('focus')
        
        if not extraction_focus:
            return []
        
        focus_areas = []
        
        # Convert smart iteration focus to focus areas format
        for issue_type, issue_list in extraction_focus.specific_issues.items():
            for issue in issue_list:
                focus_areas.append({
                    "shelf": issue['shelf'],
                    "position": issue.get('position'),
                    "failure_type": issue_type,
                    "enhancement": extraction_focus.enhancement_strategies.get(issue_type, ""),
                    "details": issue.get('details', {})
                })
        
        return focus_areas
    
    def _get_locked_positions_from_previous(self, iteration_history: List[Dict]) -> List[Dict]:
        """Get locked positions from smart iteration manager"""
        locked_positions = []
        
        # Get instructions from smart iteration manager
        if self.smart_iteration_manager.extraction_history:
            latest_focus = self.smart_iteration_manager.extraction_history[-1].get('focus')
            instructions = self.smart_iteration_manager.get_extraction_instructions(latest_focus)
            
            # Convert to format expected by extraction orchestrator
            for locked_pos in instructions.get('locked_positions', []):
                locked_positions.append({
                    "shelf": locked_pos['shelf'],
                    "position": locked_pos['position'],
                    "product_name": locked_pos['product_name'],
                    "instruction": locked_pos['instruction']
                })
        
        return locked_positions
    
    async def _trigger_human_evaluation(self, upload_id: str, result: MasterResult):
        """Trigger human evaluation for results below target"""
        logger.info(
            f"Triggering human evaluation for upload {upload_id}",
            component="master_orchestrator",
            upload_id=upload_id,
            final_accuracy=result.final_accuracy
        )
        
        # Create evaluation session
        evaluation_session = await self.human_evaluation.create_evaluation_session(
            master_result=result,
            upload_id=upload_id
        )
        
        logger.info(
            f"Human evaluation session created: {evaluation_session.session_id}",
            component="master_orchestrator",
            session_id=evaluation_session.session_id
        )
    
    async def process_with_comparison_set(self,
                                        upload_id: str,
                                        generate_all_iterations: bool = True) -> Dict:
        """Process and generate comparison set for all iterations"""
        
        # Run main processing
        result = await self.achieve_target_accuracy(upload_id)
        
        if generate_all_iterations:
            # Extract all agent results
            agent_results = [
                iter_data['extraction_result'] 
                for iter_data in result.iteration_history
            ]
            
            # Generate comparison set
            comparison_set = await self.planogram_orchestrator.generate_comparison_set(
                agent_results=agent_results,
                structure_context=result.structure_analysis,
                abstraction_level="product_view"
            )
            
            return {
                'master_result': result,
                'comparison_set': comparison_set,
                'best_iteration': comparison_set.best_iteration,
                'progression_analysis': comparison_set.progression_analysis
            }
        
        return {'master_result': result}
    
    async def _render_planogram_to_png(self, planogram: VisualPlanogram, extraction_result: ExtractionResult) -> bytes:
        """Render planogram to PNG image for visual comparison"""
        try:
            # Prepare data in the format expected by the rendering function
            extraction_data = {
                "extraction_result": {
                    "products": [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in extraction_result.products]
                },
                "accuracy": planogram.accuracy_score
            }
            
            # Import the rendering function from planogram_renderer
            from ..api.planogram_renderer import generate_png_from_real_data
            
            # Generate PNG with product view (most detailed)
            png_bytes = generate_png_from_real_data(extraction_data, "product_view")
            
            logger.info(
                "Successfully rendered planogram to PNG for visual comparison",
                component="master_orchestrator",
                png_size_bytes=len(png_bytes)
            )
            
            return png_bytes
            
        except Exception as e:
            logger.error(f"Failed to render planogram to PNG: {e}", component="master_orchestrator")
            return None
    
    async def execute_stage_pipeline(self,
                                   upload_id: str,
                                   queue_item_id: Optional[int] = None,
                                   target_accuracy: float = 0.95,
                                   max_iterations: int = 5,
                                   system: str = 'langgraph_based',
                                   configuration: Optional[Dict] = None,
                                   stage_order: List[str] = None) -> MasterResult:
        """Execute extraction using stage-based pipeline approach"""
        
        if not stage_order:
            stage_order = ['structure', 'products', 'details']
        
        start_time = time.time()
        agent_id = str(uuid.uuid4())
        run_id = f"run_{upload_id}_{agent_id[:8]}"
        
        logger.info(
            f"Starting STAGE-BASED orchestration for upload {upload_id}",
            component="master_orchestrator",
            upload_id=upload_id,
            stage_order=stage_order,
            agent_id=agent_id
        )
        
        # Get images
        images = await self._get_images(upload_id)
        
        # Initialize extraction orchestrator
        from .extraction_orchestrator import ExtractionOrchestrator
        self.extraction_orchestrator = ExtractionOrchestrator(self.config, queue_item_id=queue_item_id)
        
        # Load configuration
        if configuration:
            self.extraction_orchestrator.model_config = configuration
            self.extraction_orchestrator.temperature = configuration.get('temperature', 0.1)
            self.extraction_orchestrator.stage_models = configuration.get('stage_models', {})
            self.extraction_orchestrator.stage_configs = configuration.get('stages', {})
        
        # Initialize tracking
        stage_results = {}
        locked_context = {}
        total_cost = 0.0
        
        # Stage 1: Structure Extraction
        if 'structure' in stage_order and 'structure' in configuration.get('stages', {}):
            logger.info("Starting STAGE 1: Structure Extraction", component="master_orchestrator")
            
            structure_result = await self._execute_stage(
                stage_name='structure',
                images=images,
                locked_context={},
                queue_item_id=queue_item_id,
                run_id=run_id,
                target_accuracy=0.95  # High confidence needed for structure
            )
            
            stage_results['structure'] = structure_result
            locked_context['structure'] = structure_result['final_result']
            total_cost += structure_result.get('total_cost', 0)
            
            logger.info(
                f"Structure stage complete: {structure_result['final_result'].shelf_count} shelves",
                component="master_orchestrator"
            )
        
        # Stage 2: Product Extraction
        if 'products' in stage_order and 'products' in configuration.get('stages', {}):
            logger.info("Starting STAGE 2: Product Extraction", component="master_orchestrator")
            
            products_result = await self._execute_stage(
                stage_name='products',
                images=images,
                locked_context=locked_context,
                queue_item_id=queue_item_id,
                run_id=run_id,
                target_accuracy=target_accuracy
            )
            
            stage_results['products'] = products_result
            locked_context['products'] = products_result['final_result']
            total_cost += products_result.get('total_cost', 0)
            
            logger.info(
                f"Products stage complete: {len(products_result['final_result'].products)} products found",
                component="master_orchestrator"
            )
        
        # Stage 3: Details Enhancement
        if 'details' in stage_order and 'details' in configuration.get('stages', {}):
            logger.info("Starting STAGE 3: Details Enhancement", component="master_orchestrator")
            
            details_result = await self._execute_stage(
                stage_name='details',
                images=images,
                locked_context=locked_context,
                queue_item_id=queue_item_id,
                run_id=run_id,
                target_accuracy=0.90  # Can be slightly lower for details
            )
            
            stage_results['details'] = details_result
            total_cost += details_result.get('total_cost', 0)
            
            logger.info("Details stage complete", component="master_orchestrator")
        
        # Generate final planogram
        final_extraction = stage_results.get('products', {}).get('final_result')
        if not final_extraction and 'structure' in stage_results:
            # Create mock extraction if only structure was run
            final_extraction = ExtractionResult(
                agent_number=1,
                structure=stage_results['structure']['final_result'],
                products=[],
                total_products=0,
                overall_confidence='LOW',
                accuracy_estimate=0.0,
                extraction_duration_seconds=0,
                model_used='none',
                api_cost_estimate=0
            )
        
        # Generate planogram from final results
        if final_extraction:
            from .planogram_orchestrator import PlanogramOrchestrator
            self.planogram_orchestrator = PlanogramOrchestrator(self.config)
            
            final_planogram = await self.planogram_orchestrator.generate_for_agent_iteration(
                agent_number=1,
                extraction_result=final_extraction,
                structure_context=locked_context.get('structure'),
                abstraction_level="product_view",
                original_image=images['enhanced']
            )
        else:
            final_planogram = None
        
        # Create final result
        total_duration = time.time() - start_time
        
        result = MasterResult(
            final_accuracy=stage_results.get('products', {}).get('final_accuracy', 0.0),
            target_achieved=stage_results.get('products', {}).get('final_accuracy', 0.0) >= target_accuracy,
            iterations_completed=sum(s.get('iterations_completed', 0) for s in stage_results.values()),
            iteration_history=[],  # Different format for stage-based
            needs_human_review=False,
            structure_analysis=locked_context.get('structure'),
            best_planogram=final_planogram,
            total_duration=total_duration,
            total_cost=total_cost,
            stage_results=stage_results  # New field for stage-based results
        )
        
        logger.info(
            f"Stage-based orchestration complete",
            component="master_orchestrator",
            stages_completed=len(stage_results),
            total_duration=total_duration,
            total_cost=total_cost
        )
        
        return result
    
    async def _execute_stage(self,
                           stage_name: str,
                           images: Dict[str, bytes],
                           locked_context: Dict,
                           queue_item_id: Optional[int],
                           run_id: str,
                           target_accuracy: float) -> Dict:
        """Execute a single stage with multiple model attempts"""
        
        stage_config = self.extraction_orchestrator.stage_configs.get(stage_name, {})
        stage_models = self.extraction_orchestrator.stage_models.get(stage_name, [])
        
        if not stage_models:
            logger.warning(f"No models configured for stage {stage_name}", component="master_orchestrator")
            return {}
        
        logger.info(
            f"Executing stage '{stage_name}' with {len(stage_models)} models",
            component="master_orchestrator",
            models=stage_models
        )
        
        stage_attempts = []
        best_result = None
        best_accuracy = 0.0
        
        # Run each configured model for this stage
        for attempt_num, model_id in enumerate(stage_models, 1):
            logger.info(
                f"Stage {stage_name} - Attempt {attempt_num}/{len(stage_models)} with {model_id}",
                component="master_orchestrator"
            )
            
            # Update monitoring
            if queue_item_id:
                await monitoring_hooks.update_stage_progress(
                    queue_item_id=queue_item_id,
                    stage_name=stage_name,
                    attempt=attempt_num,
                    total_attempts=len(stage_models),
                    model=model_id,
                    complete=False
                )
            
            # Execute stage with current model
            attempt_result = await self.extraction_orchestrator.execute_stage(
                stage_name=stage_name,
                model_id=model_id,
                images=images,
                locked_context=locked_context,
                previous_attempts=stage_attempts,
                attempt_number=attempt_num,
                agent_id=f"{run_id}_{stage_name}_{attempt_num}"
            )
            
            stage_attempts.append(attempt_result)
            
            # Evaluate stage results
            if stage_name == 'structure':
                # For structure, we need high confidence in shelf count
                current_accuracy = attempt_result.structure_confidence if hasattr(attempt_result, 'structure_confidence') else 0.8
            elif stage_name == 'products':
                # For products, generate planogram and compare
                planogram = await self._generate_and_compare_planogram(
                    attempt_result, 
                    locked_context.get('structure'),
                    images
                )
                current_accuracy = planogram.get('accuracy', 0.0) if planogram else 0.0
            else:
                # For details, check completeness
                current_accuracy = self._evaluate_details_completeness(attempt_result)
            
            if current_accuracy > best_accuracy:
                best_accuracy = current_accuracy
                best_result = attempt_result
            
            # Check if we've reached target accuracy for this stage
            if current_accuracy >= target_accuracy:
                logger.info(
                    f"Stage {stage_name} reached target accuracy {target_accuracy:.1%}",
                    component="master_orchestrator",
                    attempt=attempt_num,
                    accuracy=current_accuracy
                )
                # Mark stage as complete
                if queue_item_id:
                    await monitoring_hooks.update_stage_progress(
                        queue_item_id=queue_item_id,
                        stage_name=stage_name,
                        attempt=attempt_num,
                        total_attempts=len(stage_models),
                        model=model_id,
                        complete=True
                    )
                break
        
        return {
            'stage_name': stage_name,
            'attempts': stage_attempts,
            'final_result': best_result,
            'final_accuracy': best_accuracy,
            'iterations_completed': len(stage_attempts),
            'models_used': stage_models[:len(stage_attempts)],
            'total_cost': sum(a.api_cost_estimate if hasattr(a, 'api_cost_estimate') else 0 for a in stage_attempts)
        }
    
    async def _generate_and_compare_planogram(self, extraction_result, structure_context, images):
        """Generate planogram and compare for accuracy evaluation"""
        try:
            from .planogram_orchestrator import PlanogramOrchestrator
            if not hasattr(self, 'planogram_orchestrator'):
                self.planogram_orchestrator = PlanogramOrchestrator(self.config)
            
            # Generate planogram
            planogram_result = await self.planogram_orchestrator.generate_for_agent_iteration(
                agent_number=1,
                extraction_result=extraction_result,
                structure_context=structure_context,
                abstraction_level="product_view",
                original_image=images['enhanced']
            )
            
            # Render to PNG
            planogram_png = await self._render_planogram_to_png(
                planogram_result.planogram,
                extraction_result
            )
            
            if planogram_png:
                # Compare using vision
                comparison_result = await self.comparison_agent.compare_image_vs_planogram(
                    original_image=images['enhanced'],
                    planogram=planogram_result.planogram,
                    structure_context=structure_context,
                    planogram_image=planogram_png,
                    model='gpt-4-vision-preview'
                )
                
                # Analyze accuracy
                accuracy_analysis = self.feedback_manager.analyze_accuracy_with_failure_areas(
                    comparison_result, structure_context
                )
                
                return {
                    'planogram': planogram_result,
                    'comparison': comparison_result,
                    'accuracy': accuracy_analysis.overall_accuracy
                }
            
        except Exception as e:
            logger.error(f"Failed to generate/compare planogram: {e}", component="master_orchestrator")
        
        return None
    
    def _evaluate_details_completeness(self, details_result) -> float:
        """Evaluate how complete the details extraction is"""
        if not hasattr(details_result, 'products'):
            return 0.0
        
        total_products = len(details_result.products)
        if total_products == 0:
            return 0.0
        
        # Count products with key details
        with_prices = sum(1 for p in details_result.products if hasattr(p, 'price') and p.price is not None)
        with_sizes = sum(1 for p in details_result.products if hasattr(p, 'size_variant') and p.size_variant)
        
        # Calculate completeness score
        price_completeness = with_prices / total_products
        size_completeness = with_sizes / total_products
        
        # Weighted average
        return (price_completeness * 0.6 + size_completeness * 0.4)
 