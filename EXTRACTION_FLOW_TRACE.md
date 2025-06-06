# Complete Extraction Flow Trace & Issues

## Current Flow:

### 1. UI Process Button Click (new_dashboard.html)
```javascript
// Line 966-980: Preparing extraction data
const extractionData = {
    system: currentConfig.system,
    max_budget: currentConfig.budget,
    temperature: fullConfig?.temperature || 0.7,
    orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
    orchestrator_prompt: fullConfig?.orchestrator_prompt || '',
    stage_models: stageModels,
    // ISSUE #1: Field name mismatch
    extraction_config: currentExtractionConfig || {
        system: currentConfig.system,
        temperature: fullConfig?.temperature || 0.7,
        orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
        stages: fullConfig?.stages || {}
    }
};
```

### 2. API Endpoint (src/api/queue_processing.py)
```python
# Line 22-30: ProcessRequest model
class ProcessRequest(BaseModel):
    system: str = "custom_consensus"
    max_budget: float = 1.50
    temperature: float = 0.7
    orchestrator_model: str = "claude-4-opus"
    orchestrator_prompt: str = ""
    stage_models: Optional[Dict[str, List[str]]] = None
    configuration: Optional[Dict[str, Any]] = None  # Expects 'configuration', not 'extraction_config'
```

**ISSUE #1**: UI sends `extraction_config` but backend expects `configuration`. This causes `request.configuration` to be None.

### 3. Configuration Building (queue_processing.py)
```python
# Line 82-89: Building configuration
configuration = request.configuration or {}  # This is None due to field mismatch
configuration.update({
    "temperature": request.temperature,
    "orchestrator_model": request.orchestrator_model,
    "orchestrator_prompt": request.orchestrator_prompt,
    "stage_models": request.stage_models or {},
    "max_budget": request.max_budget
})
# RESULT: configuration has NO stages or prompts!
```

### 4. System Dispatcher (src/orchestrator/system_dispatcher.py)
```python
# Line 110-121: Extracting prompts from configuration
stage_prompts = {}
stages = configuration.get('stages', {})  # Empty because stages weren't passed
for stage_id, stage_config in stages.items():
    if isinstance(stage_config, dict) and 'prompt_text' in stage_config:
        stage_prompts[stage_id] = stage_config['prompt_text']

self.extraction_system.stage_prompts = stage_prompts  # Empty dict!
```

### 5. CustomConsensusVisualSystem (src/systems/custom_consensus_visual.py)
```python
# Line 114-126: Checking for prompts
if not stage_prompts:
    stage_prompts = getattr(self, 'stage_prompts', {})  # Still empty
    
if not stage_prompts:
    error_msg = (
        "REFUSING TO RUN EXTRACTION: No custom prompts loaded from UI/database..."
    )
    raise ValueError(error_msg)  # EXTRACTION FAILS HERE
```

### 6. Error Handling (src/api/queue_processing.py)
```python
# Line 229-248: Exception handling
except Exception as e:
    logger.error(f"Extraction failed for item {item_id}: {e}")
    # Update status to failed
    supabase.table("ai_extraction_queue").update({
        "status": "failed",  # Should be "failed" but might appear as "completed"
        "error_message": str(e),
        "completed_at": datetime.utcnow().isoformat()
    }).eq("id", item_id).execute()
```

## ROOT CAUSES:

1. **Field Name Mismatch**: UI sends `extraction_config` but backend expects `configuration`
2. **Missing Stages**: Even if field name was correct, the stages with prompts need to be passed in the configuration
3. **Status Update Issue**: The status might be set to "completed" instead of "failed" when extraction fails

## FIXES NEEDED:

### Fix 1: Update UI to send correct field name
In new_dashboard.html, change `extraction_config` to `configuration`:
```javascript
const extractionData = {
    system: currentConfig.system,
    max_budget: currentConfig.budget,
    temperature: fullConfig?.temperature || 0.7,
    orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
    orchestrator_prompt: fullConfig?.orchestrator_prompt || '',
    stage_models: stageModels,
    configuration: currentExtractionConfig || {  // Changed from extraction_config
        system: currentConfig.system,
        temperature: fullConfig?.temperature || 0.7,
        orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
        stages: fullConfig?.stages || {}
    }
};
```

### Fix 2: Ensure stages are included
The configuration must include the stages with their prompts. The UI needs to ensure fullConfig.stages contains the prompt_text for each stage.

### Fix 3: Add logging to verify data flow
Add logging at each step to ensure data is passed correctly.

### Fix 4: Check status update logic
Ensure failed extractions are marked as "failed" not "completed".