# Configuration Save System Fix

## Current State

We have two save levels that are correctly implemented in the UI:

1. **"Save Stage" Button**
   - Saves individual stage configuration
   - Updates `stageConfigs` state
   - Shows "✓ Stage Saved" confirmation
   - Works correctly

2. **"Save Full Configuration" Button**
   - Prompts for name and description
   - Saves entire pipeline configuration
   - Includes all stages, orchestration, and system settings
   - Works correctly

## The Problem

When processing queue items, the saved configuration **is not being fully utilized**:

```javascript
// Current implementation only sends:
{
    system: currentConfig.system,
    max_budget: currentConfig.budget,
    temperature: fullConfig?.temperature || 0.7,
    orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
    orchestrator_prompt: fullConfig?.orchestrator_prompt || '',
    stage_models: stageModels,  // Just the model names!
    comparison_config: fullConfig?.comparison_config || {...}
}

// Missing: stage prompts, field definitions, and other stage-specific settings!
```

## The Fix

The backend needs to receive the complete stage configurations to properly process the queue item:

```javascript
// Updated handleProcessSelected function
const processConfig = {
    // System configuration
    system: currentConfig.system,
    max_budget: currentConfig.budget,
    temperature: fullConfig?.temperature || 0.7,
    
    // Orchestration configuration
    orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
    orchestrator_prompt: fullConfig?.orchestrator_prompt || '',
    
    // Comparison configuration
    comparison_config: fullConfig?.comparison_config || {
        model: 'gpt-4-vision-preview',
        prompt: DEFAULT_COMPARISON_PROMPT,
        use_visual_comparison: true,
        abstraction_layers: []
    },
    
    // Complete stage configurations (THE FIX!)
    stage_configs: fullConfig?.stages || {},
    
    // Backward compatibility
    stage_models: stageModels
};
```

## Implementation Steps

### 1. Update Queue Processing (Frontend)

```javascript
// In handleProcessSelected function
const handleProcessSelected = async () => {
    if (!selectedItems.length) return;
    
    const fullConfig = configPreview;
    
    for (const itemId of selectedItems) {
        try {
            const response = await fetch(`/api/queue/process/${itemId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    // System settings
                    system: currentConfig.system,
                    max_budget: currentConfig.budget,
                    
                    // Full configuration including stages
                    configuration: fullConfig,  // Send the entire config!
                    
                    // Backward compatibility
                    temperature: fullConfig?.temperature || 0.7,
                    orchestrator_model: fullConfig?.orchestrator_model || 'claude-4-opus',
                    orchestrator_prompt: fullConfig?.orchestrator_prompt || '',
                    stage_models: stageModels
                })
            });
            
            // ... rest of processing
        } catch (error) {
            console.error(`Failed to process item ${itemId}:`, error);
        }
    }
};
```

### 2. Update Backend to Use Stage Configs

```python
# In extraction_orchestrator.py

def load_stage_configuration(self, stage_id: str, stage_config: dict):
    """Load configuration for a specific stage"""
    if not stage_config:
        return
    
    # Use the saved prompt
    if 'prompt_text' in stage_config:
        self.stage_prompts[stage_id] = stage_config['prompt_text']
    
    # Use the saved field definitions
    if 'fields' in stage_config:
        self.stage_fields[stage_id] = stage_config['fields']
    
    # Use the saved models
    if 'models' in stage_config:
        self.stage_models[stage_id] = stage_config['models']
```

### 3. Configuration Flow

```
User Action                    → Saved To              → Used When
─────────────────────────────────────────────────────────────────
"Save Stage"                   → stageConfigs[stage]   → Building full config
"Save Full Configuration"      → localStorage/API      → Loading saved configs
"Process Queue"                → Sent to backend       → Actual extraction
```

## Benefits of This Fix

1. **Saved configurations actually work** - The prompts and fields you configure are used
2. **Consistency** - What you save is what gets executed
3. **Reusability** - Can load and apply saved configurations
4. **Debugging** - Can see exactly what configuration was used

## Visual Representation

```
┌─────────────────────────────────────────┐
│         Configuration Editor            │
├─────────────────────────────────────────┤
│                                         │
│  Stage: Products                        │
│  [Prompt: Extract beverages...]         │
│  [Fields: brand, name, price...]        │
│  [Models: gpt-4, claude-3]              │
│  [Save Stage] ← Saves to stageConfigs  │
│                                         │
│  Stage: Prices                          │
│  [Prompt: Extract prices...]            │
│  [Fields: price, promo...]              │
│  [Models: gpt-4]                        │
│  [Save Stage] ← Saves to stageConfigs  │
│                                         │
├─────────────────────────────────────────┤
│  Orchestration Settings                 │
│  [Model: Claude 4 Opus]                 │
│  [Temperature: 0.7]                     │
│  [Comparison: GPT-4 Vision]             │
├─────────────────────────────────────────┤
│                                         │
│  [Save Full Configuration] ← Saves ALL  │
│                                         │
└─────────────────────────────────────────┘
                    ↓
                    ↓ When processing
                    ↓
┌─────────────────────────────────────────┐
│          Queue Processing               │
├─────────────────────────────────────────┤
│  Sends complete configuration:          │
│  - All stage configs (prompts, fields)  │
│  - Orchestration settings               │
│  - Comparison settings                  │
│  - System settings                      │
└─────────────────────────────────────────┘
```

This ensures that the two-level save system (Stage + Full Configuration) actually works end-to-end.