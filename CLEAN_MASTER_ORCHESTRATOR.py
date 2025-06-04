    async def achieve_target_accuracy(self, 
                                     upload_id: str,
                                     target_accuracy: float = 0.95,
                                     max_iterations: int = 5,
                                     queue_item_id: Optional[int] = None,
                                     system: str = 'custom_consensus',
                                     configuration: Optional[Dict] = None) -> MasterResult:
        """Simplified orchestrator - just dispatches to the real orchestrator (the extraction system)"""
        
        start_time = time.time()
        agent_id = str(uuid.uuid4())
        run_id = f"run_{upload_id}_{agent_id[:8]}"
        
        logger.info(
            f"Master Orchestrator dispatching to {system} system",
            component="master_orchestrator",
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