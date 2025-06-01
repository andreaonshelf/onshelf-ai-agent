# Orchestrator UI Implementation Summary

## Overview
Successfully implemented UI changes to support all three orchestrators (Master, Extraction, Planogram) with individual model selection and instruction fields, as requested.

## Changes Made

### 1. Frontend UI Updates (new_dashboard_ui_separated.html)

#### State Management
Added separate state variables for each orchestrator:
```javascript
// Three separate orchestrators - Master, Extraction, Planogram
const [masterOrchestratorModel, setMasterOrchestratorModel] = useState('claude-4-opus');
const [masterOrchestratorPrompt, setMasterOrchestratorPrompt] = useState('');
const [extractionOrchestratorModel, setExtractionOrchestratorModel] = useState('claude-4-sonnet');
const [extractionOrchestratorPrompt, setExtractionOrchestratorPrompt] = useState('');
const [planogramOrchestratorModel, setPlanogramOrchestratorModel] = useState('gpt-4o-mini');
const [planogramOrchestratorPrompt, setPlanogramOrchestratorPrompt] = useState('');
```

#### Configuration Structure
Updated configuration to new nested structure:
```javascript
pipeline: {
    temperature: modelCreativity,
    orchestrators: {
        master: {
            model: masterOrchestratorModel,
            prompt: masterOrchestratorPrompt
        },
        extraction: {
            model: extractionOrchestratorModel,
            prompt: extractionOrchestratorPrompt
        },
        planogram: {
            model: planogramOrchestratorModel,
            prompt: planogramOrchestratorPrompt
        }
    },
    enable_comparison: true,
    comparison_threshold: 0.85
}
```

#### UI Components
Replaced single orchestrator dropdown with three separate sections:
- 🎯 **Master Orchestrator** (Overall Process Control)
  - Model selection with high-performance models recommended
  - Custom instructions textarea
  - Blue color scheme (#1e40af)

- 🔍 **Extraction Orchestrator** (Learning Strategy)
  - Model selection with balanced models recommended
  - Custom instructions textarea
  - Green color scheme (#059669)

- 📊 **Planogram Orchestrator** (Visualization)
  - Model selection with cost-effective models recommended
  - Custom instructions textarea
  - Purple color scheme (#7c3aed)

Each section includes:
- Clear labeling with icons
- Helpful placeholder text with examples
- Model dropdown with grouped options (High Performance, Balanced, Cost Effective)
- Description of what each orchestrator does

### 2. Backend API Updates (queue_management.py)

#### Process Endpoint Enhancement
Updated `/api/queue/process/{item_id}` to:
- Accept new orchestrator configuration format
- Store configuration in `extraction_config` column
- Maintain backward compatibility with old format

```python
extraction_config = {
    "system": system,
    "max_budget": request_data.get('max_budget', 2.0),
    "temperature": request_data.get('temperature', 0.7),
    "orchestrators": request_data.get('orchestrators', {
        "master": { "model": "claude-4-opus", "prompt": "" },
        "extraction": { "model": "claude-4-sonnet", "prompt": "" },
        "planogram": { "model": "gpt-4o-mini", "prompt": "" }
    }),
    "stage_models": request_data.get('stage_models', {})
}
```

### 3. Queue Processor Updates (processor.py)

Modified `_process_queue_item` to:
- Read `extraction_config` from queue item
- Pass configuration to MasterOrchestrator
- Support dynamic orchestrator configuration

```python
# Extract configuration from queue item
extraction_config = queue_item.get('extraction_config', {})
system = extraction_config.get('system', 'custom_consensus')

# Pass configuration to orchestrator
result = await orchestrator.achieve_target_accuracy(
    upload_id, 
    queue_item_id=queue_id,
    system=system,
    configuration=extraction_config
)
```

### 4. Orchestrator Configuration Patch

Created `orchestrator_config_patch.py` with templates for:
- Updating orchestrator constructors to accept configuration
- Dynamic model selection based on configuration
- Custom prompt injection into extraction process

## Benefits

1. **Fine-grained Control**: Users can now select different models for different tasks
2. **Cost Optimization**: Use expensive models only where needed (e.g., cheaper models for planogram)
3. **Specialized Instructions**: Each orchestrator gets task-specific guidance
4. **Better Visibility**: Users understand the multi-orchestrator architecture
5. **Flexibility**: Easy to experiment with different model combinations

## Example Use Cases

- **High Accuracy Run**: Use Claude 4 Opus for all orchestrators
- **Cost-Optimized Run**: Use Claude 4 Opus for Master, Claude 4 Sonnet for Extraction, GPT-4o mini for Planogram
- **Speed-Optimized Run**: Use faster models like GPT-4o for all orchestrators
- **Custom Instructions**: Add specific guidance like "focus on price accuracy" or "prioritize edge shelf products"

## Migration Notes

The system maintains backward compatibility:
- Old single orchestrator config still works
- New UI sends nested orchestrator structure
- Database stores full configuration in `extraction_config` column
- Queue processor passes config to orchestrators

## Next Steps

To fully activate the custom orchestrator configuration:
1. Apply patches from `orchestrator_config_patch.py` to orchestrator classes
2. Test different model combinations
3. Monitor performance impact of different configurations
4. Consider adding preset configurations for common scenarios