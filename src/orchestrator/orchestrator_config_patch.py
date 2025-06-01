"""
Patch for orchestrators to use configuration from extraction_config
This file contains the modifications needed to support dynamic orchestrator configuration
"""

from typing import Dict, Any, Optional

def patch_master_orchestrator_init():
    """
    Modify MasterOrchestrator.__init__ to accept configuration
    """
    return '''
    def __init__(self, config: SystemConfig, supabase_client=None, extraction_config: Optional[Dict[str, Any]] = None):
        self.config = config
        self.extraction_config = extraction_config or {}
        self.extraction_orchestrator = ExtractionOrchestrator(config, extraction_config=extraction_config)
        self.planogram_orchestrator = PlanogramOrchestrator(config, extraction_config=extraction_config)
        self.feedback_manager = CumulativeFeedbackManager()
        self.comparison_agent = ImageComparisonAgent(config)
        self.human_evaluation = HumanEvaluationSystem(config)
        self.state_tracker = get_state_tracker(supabase_client)
        
        # Store orchestrator configuration
        self.orchestrator_configs = extraction_config.get('orchestrators', {}) if extraction_config else {}
        
        logger.info(
            "Master Orchestrator initialized with custom configuration",
            component="master_orchestrator",
            target_accuracy=config.target_accuracy,
            max_iterations=config.max_iterations,
            has_custom_config=bool(extraction_config)
        )
    '''

def patch_extraction_orchestrator_model_selection():
    """
    Modify ExtractionOrchestrator to use configured models
    """
    return '''
    def _select_model_for_agent(self, agent_number: int, context: CumulativeExtractionContext) -> AIModelType:
        """Select appropriate model based on agent number and context"""
        
        # Check if we have custom configuration
        if hasattr(self, 'extraction_config') and self.extraction_config:
            orchestrator_config = self.extraction_config.get('orchestrators', {}).get('extraction', {})
            model_name = orchestrator_config.get('model')
            
            if model_name:
                # Map model name to AIModelType
                model_mapping = {
                    'claude-4-opus': AIModelType.CLAUDE_4_OPUS,
                    'claude-4-sonnet': AIModelType.CLAUDE_4_SONNET,
                    'claude-3-5-sonnet-v2': AIModelType.CLAUDE_3_5_SONNET,
                    'gpt-4.1': AIModelType.GPT4_TURBO,
                    'gpt-4o': AIModelType.GPT4O_LATEST,
                    'gpt-4o-mini': AIModelType.GPT4O_MINI,
                    'gemini-2.5-pro': AIModelType.GEMINI_2_5_PRO,
                    'gemini-2.5-flash': AIModelType.GEMINI_2_5_FLASH,
                }
                
                if model_name in model_mapping:
                    return model_mapping[model_name]
        
        # Default behavior if no custom config
        if agent_number == 1:
            return AIModelType.GPT4O_LATEST  # Fast initial extraction
        elif agent_number == 2:
            return AIModelType.CLAUDE_3_SONNET  # Better reasoning for improvements
        else:
            # Use best model for final refinements
            return AIModelType.CLAUDE_3_SONNET
    '''

def patch_extraction_orchestrator_prompt():
    """
    Modify ExtractionOrchestrator to use configured prompts
    """
    return '''
    def _build_cumulative_prompt(self, agent_number: int, context: CumulativeExtractionContext) -> str:
        """Build prompt that includes learning from all previous agents"""
        
        # Base prompt construction
        base_prompt = super()._build_cumulative_prompt(agent_number, context)
        
        # Add custom instructions if configured
        if hasattr(self, 'extraction_config') and self.extraction_config:
            orchestrator_config = self.extraction_config.get('orchestrators', {}).get('extraction', {})
            custom_prompt = orchestrator_config.get('prompt')
            
            if custom_prompt:
                base_prompt += f"\\n\\nCUSTOM EXTRACTION INSTRUCTIONS:\\n{custom_prompt}"
        
        return base_prompt
    '''

def patch_master_orchestrator_pass_config():
    """
    Update MasterOrchestrator.achieve_target_accuracy to use configuration
    """
    return '''
    # Inside achieve_target_accuracy method, when calling extraction orchestrator:
    
    # Step 1: Extract with cumulative learning
    extraction_start = time.time()
    
    # Pass custom instructions if available
    custom_instructions = None
    if self.orchestrator_configs.get('master', {}).get('prompt'):
        custom_instructions = self.orchestrator_configs['master']['prompt']
    
    extraction_result = await self.extraction_orchestrator.extract_with_cumulative_learning(
        image=images['enhanced'],
        iteration=iteration,
        previous_attempts=previous_attempts,
        focus_areas=self._get_focus_areas_from_previous(iteration_history),
        locked_positions=self._get_locked_positions_from_previous(iteration_history),
        agent_id=agent_id,
        custom_instructions=custom_instructions
    )
    '''

# Example of how to apply these patches:
"""
1. In master_orchestrator.py:
   - Replace __init__ method with patch_master_orchestrator_init()
   - Update achieve_target_accuracy to pass custom instructions

2. In extraction_orchestrator.py:
   - Replace _select_model_for_agent with patch_extraction_orchestrator_model_selection()
   - Update _build_cumulative_prompt to include custom prompts

3. In planogram_orchestrator.py:
   - Similar updates to use planogram orchestrator config

4. In queue processor:
   - Pass extraction_config when creating MasterOrchestrator:
     orchestrator = MasterOrchestrator(self.config, extraction_config=extraction_config)
"""