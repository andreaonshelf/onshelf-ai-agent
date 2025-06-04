"""
System Dispatcher
Simple router that dispatches extraction requests to the appropriate system
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


class SystemDispatcher:
    """Simple router that dispatches extraction requests to the appropriate system"""
    
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
            "System Dispatcher initialized",
            component="system_dispatcher",
            target_accuracy=config.target_accuracy,
            max_iterations=config.max_iterations
        )
    
    async def achieve_target_accuracy(self, 
                                     upload_id: str,
                                     target_accuracy: float = 0.95,
                                     max_iterations: int = 5,
                                     queue_item_id: Optional[int] = None,
                                     system: str = 'custom_consensus',
                                     configuration: Optional[Dict] = None) -> MasterResult:
        """Simple dispatcher - routes extraction requests to the appropriate system"""
        
        start_time = time.time()
        agent_id = str(uuid.uuid4())
        run_id = f"run_{upload_id}_{agent_id[:8]}"
        
        logger.info(
            f"System Dispatcher routing to {system} system",
            component="system_dispatcher",
            upload_id=upload_id,
            system=system,
            target_accuracy=target_accuracy,
            max_iterations=max_iterations
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
            component="system_dispatcher",
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
    
    async def _get_images(self, upload_id: str) -> Dict[str, bytes]:
        """Get images for processing from Supabase storage"""
        from supabase import create_client
        
        try:
            supabase = create_client(self.config.supabase_url, self.config.supabase_service_key)
            
            # Get file path from queue item (more reliable than uploads table)
            queue_result = supabase.table("ai_extraction_queue").select("enhanced_image_path").eq("upload_id", upload_id).execute()
            
            if not queue_result.data:
                raise Exception(f"No queue item found for upload {upload_id}")
            
            file_path = queue_result.data[0]["enhanced_image_path"]
            
            if not file_path:
                raise Exception(f"No image path found for upload {upload_id}")
            
            # Download image from Supabase storage
            image_data = supabase.storage.from_("retail-captures").download(file_path)
            
            logger.info(
                f"Loaded image for upload {upload_id}: {len(image_data)} bytes",
                component="system_dispatcher",
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
                component="system_dispatcher",
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
            component="system_dispatcher",
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
            component="system_dispatcher",
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
                component="system_dispatcher",
                png_size_bytes=len(png_bytes)
            )
            
            return png_bytes
            
        except Exception as e:
            logger.error(f"Failed to render planogram to PNG: {e}", component="system_dispatcher")
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
            component="system_dispatcher",
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
            logger.info("Starting STAGE 1: Structure Extraction", component="system_dispatcher")
            
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
                component="system_dispatcher"
            )
        
        # Stage 2: Product Extraction
        if 'products' in stage_order and 'products' in configuration.get('stages', {}):
            logger.info("Starting STAGE 2: Product Extraction", component="system_dispatcher")
            
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
                component="system_dispatcher"
            )
        
        # Stage 3: Details Enhancement
        if 'details' in stage_order and 'details' in configuration.get('stages', {}):
            logger.info("Starting STAGE 3: Details Enhancement", component="system_dispatcher")
            
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
            
            logger.info("Details stage complete", component="system_dispatcher")
        
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
            component="system_dispatcher",
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
            logger.warning(f"No models configured for stage {stage_name}", component="system_dispatcher")
            return {}
        
        logger.info(
            f"Executing stage '{stage_name}' with {len(stage_models)} models",
            component="system_dispatcher",
            models=stage_models
        )
        
        stage_attempts = []
        best_result = None
        best_accuracy = 0.0
        
        # Run each configured model for this stage
        for attempt_num, model_id in enumerate(stage_models, 1):
            logger.info(
                f"Stage {stage_name} - Attempt {attempt_num}/{len(stage_models)} with {model_id}",
                component="system_dispatcher"
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
                    component="system_dispatcher",
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
            logger.error(f"Failed to generate/compare planogram: {e}", component="system_dispatcher")
        
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
 