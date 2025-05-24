"""
OnShelf AI Agent
The orchestrator that achieves 95%+ accuracy through self-debugging iterations
Enhanced with comprehensive logging, cost tracking, error handling, and multi-image support
"""

import asyncio
import time
import base64
import json
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from supabase import create_client, Client

import instructor
import openai
from PIL import Image, ImageDraw
import io

from ..config import SystemConfig
from ..utils import (
    logger, CostTracker, CostLimitExceededException, ErrorHandler,
    with_retry, RetryConfig, GracefulDegradation, MultiImageCoordinator
)
from ..extraction.engine import ModularExtractionEngine
from ..extraction.models import CompleteShelfExtraction
from ..planogram.generator import PlanogramGenerator
from ..planogram.models import VisualPlanogram
from .models import (
    MismatchAnalysis, MismatchIssue, MismatchSeverity, RootCause,
    AgentResult, AgentState, AgentIteration, IterationDecision
)
from ..websocket.manager import WebSocketManager


class OnShelfAIAgent:
    """Main AI Agent that orchestrates the entire pipeline"""
    
    def __init__(self, config: SystemConfig, websocket_manager: Optional[WebSocketManager] = None):
        self.config = config
        self.supabase = create_client(config.supabase_url, config.supabase_service_key)
        self.websocket_manager = websocket_manager
        
        # Initialize comparison AI
        self.comparison_client = instructor.from_openai(
            openai.OpenAI(api_key=config.openai_api_key)
        )
        
        # Enhanced capabilities
        self.cost_tracker: Optional[CostTracker] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.image_coordinator: Optional[MultiImageCoordinator] = None
        
        # Agent state
        self.agent_id = None
        self.current_state = AgentState.INITIALIZING
        self.iteration_history = []
        self.total_api_cost = 0.0
        
        logger.info(
            "OnShelf AI Agent initialized",
            component="agent",
            target_accuracy=config.target_accuracy,
            max_iterations=config.max_iterations
        )
    
    async def achieve_target_accuracy(self, upload_id: str) -> AgentResult:
        """Main method: iterate until 95%+ accuracy achieved (LEGACY - raw uploads)"""
        
        self.agent_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize enhanced capabilities
        self.cost_tracker = CostTracker(self.config.max_api_cost_per_extraction, self.agent_id)
        self.error_handler = ErrorHandler(self.agent_id)
        self.image_coordinator = MultiImageCoordinator(self.agent_id)
        
        # Initialize extraction components with agent context
        self.extraction_engine = ModularExtractionEngine(self.config)
        self.extraction_engine.initialize_for_agent(self.agent_id, self.config.max_api_cost_per_extraction)
        self.planogram_generator = PlanogramGenerator()
        
        logger.log_agent_start(self.agent_id, upload_id, self.config.target_accuracy)
        await self._update_state(AgentState.INITIALIZING)
        
        # Save agent start in database
        await self._save_agent_start(upload_id)
        
        try:
            # Get original images from OnShelf database (LEGACY PATH)
            original_images = await self._get_original_images(upload_id)
            
            # Continue with existing processing logic...
            return await self._process_images_to_result(upload_id, original_images, start_time)
            
        except Exception as e:
            logger.critical(
                f"Critical system failure in AI Agent: {e}",
                component="agent",
                agent_id=self.agent_id,
                error=str(e)
            )
            await self._update_state(AgentState.FAILED)
            raise

    async def _process_images_to_result(self, identifier: str, images: Dict[str, bytes], start_time: float, is_enhanced: bool = False) -> AgentResult:
        """Common processing logic for both legacy and enhanced images"""
        
        # Setup image coordination
        self.image_coordinator.add_images(images)
        
        # Agent iteration loop
        iteration = 1
        current_accuracy = 0.0
        best_result = None
        previous_failures = []
        
        processing_type = "ENHANCED" if is_enhanced else "LEGACY"
        
        while (iteration <= self.config.max_iterations and 
               current_accuracy < self.config.target_accuracy):
            
            logger.log_iteration_start(self.agent_id, iteration, f"{processing_type} Iteration {iteration}")
            
            # Check cost limits before starting iteration
            if self.cost_tracker.is_approaching_limit(0.9):
                logger.warning(
                    f"Approaching cost limit: {self.cost_tracker.get_cost_summary()}",
                    component="agent",
                    agent_id=self.agent_id
                )
            
            # Broadcast iteration start
            if self.websocket_manager:
                await self.websocket_manager.broadcast_iteration_start(
                    self.agent_id, iteration, self.config.max_iterations
                )
            
            iteration_start = time.time()
            
            try:
                # Step 1: Design extraction sequence based on previous failures
                await self._update_state(AgentState.EXTRACTING)
                extraction_steps = await self.extraction_engine.design_extraction_sequence(
                    images, previous_failures, self.agent_id
                )
                
                logger.info(
                    f"Designed extraction sequence with {len(extraction_steps)} steps",
                    component="agent",
                    agent_id=self.agent_id,
                    iteration=iteration,
                    step_count=len(extraction_steps),
                    processing_type=processing_type
                )
                
                # Step 2: Execute extraction sequence
                extraction_result = await self.extraction_engine.execute_extraction_sequence(
                    identifier, images, extraction_steps, self.agent_id
                )
                extraction_duration = time.time() - iteration_start
                
                logger.info(
                    f"Extraction complete: {extraction_result.total_products_detected} products found",
                    component="agent",
                    agent_id=self.agent_id,
                    iteration=iteration,
                    products_found=extraction_result.total_products_detected,
                    extraction_duration=extraction_duration,
                    processing_type=processing_type
                )
                
                # Step 3: Generate planogram from extraction JSON
                await self._update_state(AgentState.GENERATING_PLANOGRAM)
                planogram_start = time.time()
                planogram = await self.planogram_generator.generate_planogram_from_json(
                    extraction_result
                )
                planogram_duration = time.time() - planogram_start
                
                # Step 4: AI comparison - original images vs generated planogram
                await self._update_state(AgentState.COMPARING)
                comparison_start = time.time()
                mismatch_analysis = await self._ai_compare_original_vs_planogram(
                    images, planogram, extraction_result
                )
                comparison_duration = time.time() - comparison_start
                
                # Step 5: Calculate accuracy
                current_accuracy = mismatch_analysis.overall_accuracy
                
                logger.log_accuracy_update(
                    self.agent_id, iteration, current_accuracy, len(mismatch_analysis.issues)
                )
                
                # Broadcast accuracy update
                if self.websocket_manager:
                    await self.websocket_manager.broadcast_accuracy_update(
                        self.agent_id, 
                        current_accuracy,
                        {
                            'iteration': iteration,
                            'issues': len(mismatch_analysis.issues),
                            'planogram_id': planogram.planogram_id,
                            'processing_type': processing_type
                        }
                    )
                
                # Track iteration
                iteration_data = AgentIteration(
                    iteration_number=iteration,
                    extraction_steps=[s.dict() for s in extraction_steps],
                    extraction_duration=extraction_duration,
                    planogram_generation_duration=planogram_duration,
                    comparison_duration=comparison_duration,
                    accuracy_achieved=current_accuracy,
                    issues_found=len(mismatch_analysis.issues),
                    improvements_from_previous=current_accuracy - (best_result.accuracy if best_result else 0),
                    api_costs={
                        'extraction': extraction_result.api_cost_estimate,
                        'comparison': 0.02  # Estimate
                    },
                    total_iteration_cost=extraction_result.api_cost_estimate + 0.02
                )
                self.iteration_history.append(iteration_data)
                self.total_api_cost += iteration_data.total_iteration_cost
                
                # Track best result
                if best_result is None or current_accuracy > best_result.accuracy:
                    best_result = AgentResult(
                        agent_id=self.agent_id,
                        upload_id=identifier,
                        extraction=extraction_result.dict(),
                        planogram=planogram.dict(),
                        mismatch_analysis=mismatch_analysis,
                        accuracy=current_accuracy,
                        iterations_completed=iteration,
                        target_achieved=current_accuracy >= self.config.target_accuracy,
                        processing_duration=time.time() - start_time,
                        total_api_cost=self.total_api_cost,
                        confidence_in_result=self._calculate_confidence(mismatch_analysis)
                    )
                
                # Check if target achieved
                if current_accuracy >= self.config.target_accuracy:
                    logger.info(
                        f"TARGET ACHIEVED! {current_accuracy:.2%} accuracy ({processing_type})",
                        component="agent",
                        agent_id=self.agent_id,
                        final_accuracy=current_accuracy,
                        iterations=iteration,
                        processing_type=processing_type
                    )
                    await self._update_state(AgentState.COMPLETED)
                    break
                
                # Continue iteration logic...
                iteration += 1
                
            except CostLimitExceededException as e:
                logger.error(
                    f"Cost limit exceeded during iteration {iteration}",
                    component="agent",
                    agent_id=self.agent_id,
                    iteration=iteration,
                    cost_limit=e.limit,
                    current_cost=e.current_cost
                )
                best_result.escalation_reason = f"COST_LIMIT_EXCEEDED_£{e.current_cost:.2f}"
                break
            
            except Exception as e:
                self.error_handler.record_error(e, {
                    'iteration': iteration,
                    'identifier': identifier,
                    'stage': self.current_state.value,
                    'processing_type': processing_type
                })
                
                if self.error_handler.should_escalate(e, iteration):
                    logger.error(
                        f"Critical error during iteration {iteration}, escalating",
                        component="agent",
                        agent_id=self.agent_id,
                        iteration=iteration,
                        error=str(e)
                    )
                    best_result.escalation_reason = f"CRITICAL_ERROR_{type(e).__name__}"
                    break
                else:
                    logger.warning(
                        f"Recoverable error during iteration {iteration}, continuing",
                        component="agent",
                        agent_id=self.agent_id,
                        iteration=iteration,
                        error=str(e)
                    )
                    continue
        
        # Finalize result
        best_result.iterations_completed = iteration - 1
        best_result.processing_duration = time.time() - start_time
        best_result.total_api_cost = self.total_api_cost
        best_result.completed_at = datetime.utcnow()
        
        # Determine if human review needed
        if current_accuracy < self.config.target_accuracy:
            best_result.human_review_required = True
            if not best_result.escalation_reason:
                best_result.escalation_reason = f"AI_MAX_ITERATIONS_REACHED_ACCURACY_{current_accuracy:.1%}"
            await self._update_state(AgentState.ESCALATED)
            
            logger.log_escalation(self.agent_id, best_result.escalation_reason, current_accuracy)
        else:
            best_result.human_review_required = False
            await self._update_state(AgentState.COMPLETED)
            
            logger.log_completion(
                self.agent_id, current_accuracy, iteration-1, 
                best_result.processing_duration, self.total_api_cost
            )
        
        # Save final result to database
        await self._save_agent_result(best_result)
        
        return best_result
    
    async def achieve_target_accuracy_enhanced(self, ready_media_id: str) -> AgentResult:
        """Main method for enhanced images: iterate until 95%+ accuracy achieved (PRODUCTION)"""
        
        self.agent_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Initialize enhanced capabilities
        self.cost_tracker = CostTracker(self.config.max_api_cost_per_extraction, self.agent_id)
        self.error_handler = ErrorHandler(self.agent_id)
        self.image_coordinator = MultiImageCoordinator(self.agent_id)
        
        # Initialize extraction components with agent context
        self.extraction_engine = ModularExtractionEngine(self.config)
        self.extraction_engine.initialize_for_agent(self.agent_id, self.config.max_api_cost_per_extraction)
        self.planogram_generator = PlanogramGenerator()
        
        logger.log_agent_start(self.agent_id, ready_media_id, self.config.target_accuracy)
        await self._update_state(AgentState.INITIALIZING)
        
        # Save agent start in database with enhanced flag
        await self._save_agent_start_enhanced(ready_media_id)
        
        try:
            # Get enhanced images from processed storage (PRODUCTION PATH)
            enhanced_images = await self._get_enhanced_images(ready_media_id)
            
            logger.info(
                f"🔥 Enhanced images loaded for {ready_media_id}",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id,
                enhanced_image_count=len(enhanced_images),
                processing_type="enhanced"
            )
            
            # Continue with existing processing logic using enhanced images
            return await self._process_images_to_result(ready_media_id, enhanced_images, start_time, is_enhanced=True)
            
        except Exception as e:
            logger.critical(
                f"Critical system failure in Enhanced AI Agent: {e}",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id,
                error=str(e)
            )
            await self._update_state(AgentState.FAILED)
            raise
    
    async def _get_original_images(self, upload_id: str) -> Dict[str, bytes]:
        """Get original images from OnShelf database"""
        try:
            logger.info(
                f"Loading images for upload {upload_id}",
                component="agent",
                agent_id=self.agent_id,
                upload_id=upload_id
            )
            
            # Get media files for upload
            result = self.supabase.table("media_files") \
                .select("storage_path, file_name") \
                .eq("upload_id", upload_id) \
                .execute()
            
            if not result.data:
                raise ValueError(f"No media files found for upload {upload_id}")
            
            images = {}
            for media_file in result.data:
                # Download from storage
                file_data = self.supabase.storage \
                    .from_("retail-captures") \
                    .download(media_file['storage_path'])
                
                # Use filename as key for better image coordination
                filename = media_file['file_name']
                images[filename] = file_data
                
                logger.debug(
                    f"Loaded image: {filename} ({len(file_data)} bytes)",
                    component="agent",
                    agent_id=self.agent_id,
                    filename=filename,
                    size_bytes=len(file_data)
                )
            
            logger.info(
                f"Successfully loaded {len(images)} images from upload {upload_id}",
                component="agent",
                agent_id=self.agent_id,
                upload_id=upload_id,
                image_count=len(images),
                total_size_mb=sum(len(img) for img in images.values()) / (1024 * 1024)
            )
            return images
            
        except Exception as e:
            logger.error(
                f"Failed to get original images: {e}",
                component="agent",
                agent_id=self.agent_id,
                upload_id=upload_id,
                error=str(e)
            )
            raise
    
    async def _get_enhanced_images(self, ready_media_id: str) -> Dict[str, bytes]:
        """Get enhanced images from processed storage (PRODUCTION PATH)"""
        try:
            logger.info(
                f"🔥 Loading enhanced images for ready_media_id {ready_media_id}",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id,
                processing_type="enhanced"
            )
            
            # Query ai_extraction_queue table for enhanced image path
            result = self.supabase.table("ai_extraction_queue") \
                .select("id, ready_media_id, enhanced_image_path, upload_id, status") \
                .eq("ready_media_id", ready_media_id) \
                .execute()
            
            if not result.data:
                raise ValueError(f"No queue item found for ready_media_id {ready_media_id}")
            
            media_info = result.data[0]
            enhanced_path = media_info.get('enhanced_image_path')
            
            if not enhanced_path:
                raise ValueError(f"No enhanced_image_path found for ready_media_id {ready_media_id}")
            
            logger.info(
                f"Found enhanced media path: {enhanced_path}",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id
            )
            
            images = {}
            
            try:
                # Download from enhanced storage path
                file_data = self.supabase.storage \
                    .from_("retail-captures") \
                    .download(enhanced_path)
                
                # Use descriptive filename for enhanced image
                filename = f"enhanced_{ready_media_id}.jpg"
                images[filename] = file_data
                
                logger.info(
                    f"✅ Enhanced image loaded: {filename} ({len(file_data)} bytes)",
                    component="agent",
                    agent_id=self.agent_id,
                    image_filename=filename,
                    size_bytes=len(file_data),
                    storage_path=enhanced_path
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to download enhanced image from {enhanced_path}: {e}",
                    component="agent",
                    agent_id=self.agent_id,
                    storage_path=enhanced_path,
                    error=str(e)
                )
                raise
            
            # Check if there are additional processed images (multi-view)
            metadata = media_info.get('metadata', {})
            if isinstance(metadata, dict) and 'additional_views' in metadata:
                for view_name, view_path in metadata['additional_views'].items():
                    try:
                        additional_data = self.supabase.storage \
                            .from_("retail-captures") \
                            .download(view_path)
                        
                        view_filename = f"enhanced_{view_name}_{ready_media_id}.jpg"
                        images[view_filename] = additional_data
                        
                        logger.debug(
                            f"Additional enhanced view loaded: {view_filename}",
                            component="agent",
                            agent_id=self.agent_id,
                            view_name=view_name
                        )
                        
                    except Exception as e:
                        logger.warning(
                            f"Failed to load additional view {view_name}: {e}",
                            component="agent",
                            agent_id=self.agent_id,
                            view_name=view_name
                        )
                        # Continue processing with main image
            
            logger.info(
                f"🎯 Successfully loaded {len(images)} enhanced images for {ready_media_id}",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id,
                image_count=len(images),
                total_size_mb=sum(len(img) for img in images.values()) / (1024 * 1024),
                processing_type="enhanced"
            )
            
            return images
            
        except Exception as e:
            logger.error(
                f"Failed to get enhanced images for {ready_media_id}: {e}",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id,
                error=str(e)
            )
            raise
    
    @with_retry(RetryConfig(max_retries=2, base_delay=2.0))
    async def _ai_compare_original_vs_planogram(self, 
                                              original_images: Dict[str, bytes],
                                              planogram: VisualPlanogram,
                                              extraction: CompleteShelfExtraction) -> MismatchAnalysis:
        """Use AI vision to compare original images with generated planogram"""
        
        comparison_start = time.time()
        
        logger.info(
            "Starting AI comparison between original images and planogram",
            component="agent",
            agent_id=self.agent_id,
            planogram_id=planogram.planogram_id,
            extraction_id=extraction.extraction_id
        )
        
        # Convert planogram to image for comparison
        planogram_image = await self._render_planogram_as_image(planogram)
        
        # Get appropriate comparison images using image coordinator
        if self.image_coordinator:
            comparison_images = self.image_coordinator.get_comparison_images()
            logger.debug(
                f"Using {len(comparison_images)} images for comparison",
                component="agent",
                agent_id=self.agent_id,
                comparison_image_types=list(comparison_images.keys())
            )
        else:
            comparison_images = original_images
        
        comparison_prompt = f"""
You are an expert retail analyst comparing an original shelf photo with an AI-generated planogram.

OBJECTIVE: Identify ALL mismatches that prevent 95%+ accuracy.

EXTRACTION SUMMARY:
- Products Detected: {len(extraction.products)}
- Shelves: {extraction.shelf_structure.number_of_shelves}
- Confidence: {extraction.overall_confidence.value}
- Processing Duration: {extraction.extraction_duration_seconds:.1f}s

COMPARISON TASKS:
1. Structure Verification:
   - Count shelves in both images
   - Check shelf alignment and spacing
   - Verify overall layout matches

2. Product Comparison:
   - Count total products in original vs planogram
   - Check each product's position (shelf and horizontal placement)
   - Verify product names and brands match
   - Validate facing counts

3. Detail Checks:
   - Price accuracy (if visible)
   - Gap detection (empty spaces)
   - Promotional elements

For EACH mismatch found:
- Type: (missing_product, wrong_position, incorrect_facings, price_error, etc.)
- Location: Be specific (e.g., "Shelf 2, 3rd position from left")
- Severity: critical/high/medium/low based on impact
- Root cause: structure_error/extraction_error/visualization_error/coordinate_error/quantity_error/price_error
- Confidence: Your confidence in this diagnosis (0.0-1.0)
- Accuracy impact: How much this affects overall accuracy (0.0-1.0)
- Suggested fix: Specific recommendation

Calculate accuracy scores for:
- Overall accuracy (0.0-1.0)
- Structure accuracy
- Product detection accuracy
- Spatial positioning accuracy
- Price accuracy
- Facing count accuracy

Provide strategic recommendations for improvement.
"""
        
        try:
            # Use primary comparison image
            primary_image = comparison_images.get('overview', list(comparison_images.values())[0])
            
            response = self.comparison_client.chat.completions.create(
                model=self.config.models['image_comparison'],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": comparison_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(primary_image).decode()}",
                                    "detail": "high"
                                },
                            },
                            {
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(planogram_image).decode()}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                response_model=MismatchAnalysis,
                max_tokens=4000
            )
            
            # Fill in metadata
            response.extraction_id = extraction.extraction_id
            response.planogram_id = planogram.planogram_id
            response.analysis_duration_seconds = time.time() - comparison_start
            response.model_used = self.config.models['image_comparison']
            
            # Count issues by severity
            response.critical_issues = len([i for i in response.issues if i.severity == MismatchSeverity.CRITICAL])
            response.high_issues = len([i for i in response.issues if i.severity == MismatchSeverity.HIGH])
            response.medium_issues = len([i for i in response.issues if i.severity == MismatchSeverity.MEDIUM])
            response.low_issues = len([i for i in response.issues if i.severity == MismatchSeverity.LOW])
            
            # Track cost
            comparison_cost = 0.03  # Estimate for comparison
            if self.cost_tracker:
                self.cost_tracker.add_cost("ai_comparison", comparison_cost)
            
            logger.info(
                f"AI comparison completed: {response.overall_accuracy:.2%} accuracy, {len(response.issues)} issues found",
                component="agent",
                agent_id=self.agent_id,
                comparison_duration=time.time() - comparison_start,
                overall_accuracy=response.overall_accuracy,
                total_issues=len(response.issues),
                critical_issues=response.critical_issues,
                cost=comparison_cost
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"AI comparison failed: {e}",
                component="agent",
                agent_id=self.agent_id,
                error=str(e)
            )
            
            # Create fallback analysis
            fallback_analysis = MismatchAnalysis(
                extraction_id=extraction.extraction_id,
                planogram_id=planogram.planogram_id,
                overall_accuracy=0.0,
                structure_accuracy=0.0,
                product_accuracy=0.0,
                spatial_accuracy=0.0,
                price_accuracy=0.0,
                facing_accuracy=0.0,
                issues=[],
                analysis_duration_seconds=time.time() - comparison_start,
                model_used=self.config.models['image_comparison'],
                recommendations=["AI comparison failed - manual review required"]
            )
            
            logger.warning(
                "Using fallback analysis due to comparison failure",
                component="agent",
                agent_id=self.agent_id
            )
            
            return fallback_analysis
    
    async def _render_planogram_as_image(self, planogram: VisualPlanogram) -> bytes:
        """Render planogram as image for AI comparison"""
        
        logger.debug(
            "Rendering planogram as image for comparison",
            component="agent",
            agent_id=self.agent_id,
            planogram_id=planogram.planogram_id
        )
        
        # Create planogram image using PIL
        width = int(planogram.total_width_cm * 4)  # 4 pixels per cm
        height = int(planogram.total_height_cm * 4)
        
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Use a default font
        try:
            from PIL import ImageFont
            font = ImageFont.load_default()
        except:
            font = None
        
        # Draw header
        draw.text((10, 10), f"OnShelf Planogram - {planogram.accuracy_score:.1%} Accuracy", 
                 fill='black', font=font)
        
        # Draw shelves
        shelf_height = (height - 60) // planogram.shelf_count
        
        for shelf in planogram.shelves:
            y_start = 60 + ((shelf.shelf_number - 1) * shelf_height)
            
            # Draw shelf line
            draw.line([(0, y_start + shelf_height), (width, y_start + shelf_height)], 
                     fill='gray', width=2)
            
            # Draw shelf number
            draw.text((5, y_start + 5), f"Shelf {shelf.shelf_number}", fill='black', font=font)
            
            # Draw elements
            for element in shelf.elements:
                x_pos = int(element.position_cm * 4)
                elem_width = int(element.width_cm * 4)
                
                if element.type == "product":
                    # Product rectangle
                    draw.rectangle([x_pos, y_start + 10, x_pos + elem_width - 2, y_start + shelf_height - 10],
                                 fill=element.confidence_color, outline='black')
                    
                    # Product text
                    draw.text((x_pos + 3, y_start + 15), element.name[:15], fill='white', font=font)
                    if element.price:
                        draw.text((x_pos + 3, y_start + 30), f"£{element.price:.2f}", fill='white', font=font)
                    draw.text((x_pos + 3, y_start + 45), f"{element.facings} facings", fill='white', font=font)
                    
                elif element.type == "empty":
                    # Empty space
                    fill_color = '#fee2e2' if element.reason == "potential_out_of_stock" else '#f3f4f6'
                    draw.rectangle([x_pos, y_start + 10, x_pos + elem_width - 2, y_start + shelf_height - 10],
                                 fill=fill_color, outline='gray')
                    
                    label = "OOS?" if element.reason == "potential_out_of_stock" else "Empty"
                    text_width = draw.textlength(label, font=font) if font else 30
                    draw.text((x_pos + (elem_width - text_width) // 2, y_start + shelf_height // 2),
                             label, fill='gray', font=font)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=90)
        
        planogram_image_size = len(img_bytes.getvalue())
        logger.debug(
            f"Planogram rendered as {width}x{height} image ({planogram_image_size} bytes)",
            component="agent",
            agent_id=self.agent_id,
            image_width=width,
            image_height=height,
            image_size_bytes=planogram_image_size
        )
        
        return img_bytes.getvalue()
    
    async def _decide_iteration_strategy(self, 
                                       mismatch_analysis: MismatchAnalysis,
                                       iteration: int,
                                       current_accuracy: float) -> IterationDecision:
        """Decide whether and how to iterate based on analysis"""
        
        # Don't iterate if accuracy is very low after multiple attempts
        if iteration >= 3 and current_accuracy < 0.5:
            return IterationDecision(
                should_iterate=False,
                reason="Accuracy too low after multiple iterations - likely fundamental issue",
                strategy_adjustments=[],
                focus_areas=[],
                expected_improvement=0.0
            )
        
        # Calculate potential improvement
        critical_impact = sum(i.accuracy_impact for i in mismatch_analysis.issues 
                            if i.severity == MismatchSeverity.CRITICAL)
        high_impact = sum(i.accuracy_impact for i in mismatch_analysis.issues 
                        if i.severity == MismatchSeverity.HIGH)
        
        potential_improvement = critical_impact + (high_impact * 0.5)
        
        # Don't iterate if improvement would be minimal
        if potential_improvement < 0.05:
            return IterationDecision(
                should_iterate=False,
                reason="Minimal improvement potential from remaining issues",
                strategy_adjustments=[],
                focus_areas=[],
                expected_improvement=potential_improvement
            )
        
        # Identify focus areas
        focus_areas = []
        strategy_adjustments = []
        
        # Analyze root causes
        root_cause_counts = {}
        for issue in mismatch_analysis.issues:
            if issue.severity in [MismatchSeverity.CRITICAL, MismatchSeverity.HIGH]:
                root_cause_counts[issue.root_cause] = root_cause_counts.get(issue.root_cause, 0) + 1
        
        # Determine strategy based on root causes
        if root_cause_counts.get(RootCause.STRUCTURE_ERROR, 0) > 0:
            focus_areas.append("shelf_structure")
            strategy_adjustments.append("Use enhanced scaffolding analysis")
        
        if root_cause_counts.get(RootCause.EXTRACTION_ERROR, 0) > 2:
            focus_areas.append("product_detection")
            strategy_adjustments.append("Multi-model product extraction")
        
        if root_cause_counts.get(RootCause.PRICE_ERROR, 0) > 3:
            focus_areas.append("price_extraction")
            strategy_adjustments.append("Specialized price extraction step")
        
        if root_cause_counts.get(RootCause.QUANTITY_ERROR, 0) > 2:
            focus_areas.append("facing_counts")
            strategy_adjustments.append("Enhanced facing quantification")
        
        return IterationDecision(
            should_iterate=True,
            reason=f"Can improve accuracy by {potential_improvement:.1%}",
            strategy_adjustments=strategy_adjustments,
            focus_areas=focus_areas,
            expected_improvement=potential_improvement
        )
    
    def _calculate_confidence(self, mismatch_analysis: MismatchAnalysis) -> float:
        """Calculate confidence in the result"""
        base_confidence = mismatch_analysis.overall_accuracy
        
        # Reduce confidence based on issue severity
        confidence_penalty = (
            mismatch_analysis.critical_issues * 0.1 +
            mismatch_analysis.high_issues * 0.05 +
            mismatch_analysis.medium_issues * 0.02
        )
        
        return max(0.0, base_confidence - confidence_penalty)
    
    async def _update_state(self, new_state: AgentState):
        """Update agent state and broadcast if needed"""
        self.current_state = new_state
        
        if self.websocket_manager:
            await self.websocket_manager.broadcast_state_change(
                self.agent_id, new_state.value
            )
    
    async def _save_agent_start(self, upload_id: str):
        """Save agent start to database"""
        try:
            self.supabase.rpc('start_ai_agent', {
                'p_upload_id': upload_id,
                'p_target_accuracy': self.config.target_accuracy,
                'p_max_iterations': self.config.max_iterations
            }).execute()
        except Exception as e:
            print(f"Failed to save agent start: {e}")
    
    async def _save_agent_start_enhanced(self, ready_media_id: str):
        """Save enhanced agent start to database"""
        try:
            # For now, just log the start - can be enhanced later with proper database tracking
            logger.info(
                f"Starting enhanced agent processing",
                component="agent",
                agent_id=self.agent_id,
                ready_media_id=ready_media_id,
                target_accuracy=self.config.target_accuracy,
                max_iterations=self.config.max_iterations,
                processing_type="enhanced"
            )
        except Exception as e:
            print(f"Failed to save enhanced agent start: {e}")
    
    async def _save_agent_result(self, result: AgentResult):
        """Save final agent result to database"""
        try:
            # TODO: Implement save_agent_result database function or use existing save methods
            logger.info(
                f"Agent result ready to save: accuracy={result.accuracy:.2%}, iterations={result.iterations_completed}",
                component="agent",
                agent_id=result.agent_id
            )
            
            # For now, skip saving to avoid errors
            # self.supabase.rpc('save_agent_result', {
            #     'p_agent_id': result.agent_id,
            #     'p_final_accuracy': result.accuracy,
            #     'p_iterations_completed': result.iterations_completed,
            #     'p_processing_duration': int(result.processing_duration),
            #     'p_escalation_reason': result.escalation_reason
            # }).execute()
            
            # # Save iterations
            # for iteration in self.iteration_history:
            #     self.supabase.table('agent_iterations').insert({
            #         'agent_id': result.agent_id,
            #         'iteration_number': iteration.iteration_number,
            #         'extraction_steps': iteration.extraction_steps,
            #         'accuracy_achieved': iteration.accuracy_achieved,
            #         'iteration_duration_seconds': int(iteration.extraction_duration + 
            #                                          iteration.planogram_generation_duration + 
            #                                          iteration.comparison_duration),
            #         'api_costs': iteration.api_costs
            #     }).execute()
                
        except Exception as e:
            print(f"Failed to save agent result: {e}") 