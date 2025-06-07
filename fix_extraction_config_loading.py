#!/usr/bin/env python3
"""
Fix the extraction orchestrator to use extraction_config instead of model_config.
This ensures fields are properly loaded and used for dynamic model building.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("FIX: Update ExtractionOrchestrator to use extraction_config")
print("=" * 80)

# Read the current extraction orchestrator
with open('src/orchestrator/extraction_orchestrator.py', 'r') as f:
    content = f.read()

# The fix: Update _load_model_config to also check extraction_config
new_load_model_config = '''    def _load_model_config(self):
        """Load model configuration from queue item"""
        try:
            from supabase import create_client
            import os
            
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_SERVICE_KEY")
            )
            
            # Get both model_config and extraction_config
            result = supabase.table("ai_extraction_queue").select("model_config, extraction_config").eq("id", self.queue_item_id).single().execute()
            
            if result.data:
                # Prioritize extraction_config if it has stages (contains field definitions)
                extraction_config = result.data.get("extraction_config", {})
                model_config = result.data.get("model_config", {})
                
                # Use extraction_config if it has stages, otherwise fall back to model_config
                if extraction_config and extraction_config.get("stages"):
                    self.model_config = extraction_config
                    logger.info(
                        "Using extraction_config with field definitions",
                        component="extraction_orchestrator",
                        stage_count=len(extraction_config.get("stages", {}))
                    )
                elif model_config:
                    self.model_config = model_config
                    logger.info(
                        "Using model_config (no extraction_config with stages found)",
                        component="extraction_orchestrator"
                    )
                else:
                    self.model_config = {}
                    logger.warning(
                        "No configuration found in queue item",
                        component="extraction_orchestrator"
                    )
                
                # Extract configuration values
                self.temperature = self.model_config.get("temperature", 0.7)
                self.orchestrator_model = self.model_config.get("orchestrator_model", "claude-4-opus")
                self.orchestrator_prompt = self.model_config.get("orchestrator_prompt", "")
                self.stage_models = self.model_config.get("stage_models", {})
                
                # Load stage configurations if available
                self.stage_configs = self.model_config.get("stages", {})
                
                # Initialize stage prompts and fields from configuration
                self.stage_prompts = {}
                self.stage_fields = {}
                
                for stage_id, stage_config in self.stage_configs.items():
                    if isinstance(stage_config, dict):
                        if "prompt_text" in stage_config:
                            self.stage_prompts[stage_id] = stage_config["prompt_text"]
                        if "fields" in stage_config:
                            self.stage_fields[stage_id] = stage_config["fields"]
                            logger.info(
                                f"Loaded {len(stage_config['fields'])} fields for stage {stage_id}",
                                component="extraction_orchestrator",
                                stage=stage_id,
                                field_count=len(stage_config['fields'])
                            )
                
                logger.info(
                    "Loaded model configuration from queue item",
                    component="extraction_orchestrator",
                    queue_item_id=self.queue_item_id,
                    temperature=self.temperature,
                    orchestrator_model=self.orchestrator_model,
                    stages_loaded=list(self.stage_configs.keys()),
                    fields_loaded={k: len(v) for k, v in self.stage_fields.items()}
                )
        except Exception as e:
            logger.error(f"Failed to load model config: {e}", component="extraction_orchestrator")'''

# Find the old _load_model_config method
import re
pattern = r'def _load_model_config\(self\):.*?(?=\n    def|\n\nclass|\Z)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Replace the old method with the new one
    content = content[:match.start()] + new_load_model_config.strip() + '\n' + content[match.end():]
    
    # Write the updated file
    with open('src/orchestrator/extraction_orchestrator.py', 'w') as f:
        f.write(content)
    
    print("✓ Updated _load_model_config method to check extraction_config")
    print("\nChanges made:")
    print("1. Now queries both model_config and extraction_config")
    print("2. Prioritizes extraction_config if it has 'stages' (contains fields)")
    print("3. Falls back to model_config if no extraction_config with stages")
    print("4. Logs which configuration source is being used")
    print("5. Logs field counts for each stage")
else:
    print("✗ Could not find _load_model_config method to update")

print("\n" + "=" * 80)
print("ALTERNATIVE FIX: Pass configuration directly")
print("=" * 80)

print("""
Another approach would be to modify the ExtractionOrchestrator __init__ to accept
a configuration parameter directly:

def __init__(self, config: SystemConfig, queue_item_id: Optional[int] = None, 
             extraction_run_id: Optional[str] = None, configuration: Optional[Dict] = None):
    self.config = config
    self.queue_item_id = queue_item_id
    self.extraction_run_id = extraction_run_id
    
    # Use passed configuration if available
    if configuration:
        self.model_config = configuration
        self._parse_configuration()
    elif queue_item_id:
        self._load_model_config()
    else:
        # Initialize defaults
        self.model_config = {}
        self.temperature = 0.7
        ...

This would allow the system dispatcher to pass configuration directly,
avoiding the need to reload from the database.
""")