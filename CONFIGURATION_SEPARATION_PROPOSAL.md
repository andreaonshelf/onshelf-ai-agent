# Configuration Separation Proposal

## Problem Statement

Currently, the "Save Stage" button saves not just stage-specific configuration, but also orchestrator-level and comparison-level settings. This violates separation of concerns because:

1. **Stage Config** = How to extract specific information (products, prices, etc.)
2. **Orchestrator Config** = How to coordinate the extraction process
3. **Comparison Config** = How to validate results against the original image

These operate at different system levels and should be managed separately.

## Current Issues

### 1. Mixed Responsibilities
```javascript
// When "Save Stage" is clicked, it includes:
{
    stages: { /* stage-specific */ },
    orchestrator_model: "...",     // Should NOT be in stage save
    comparison_config: { ... },     // Should NOT be in stage save
    temperature: 0.7,              // Should NOT be in stage save
}
```

### 2. Confusing User Experience
- User thinks they're saving stage configuration
- Actually saving system-wide settings
- Changes to orchestrator affect ALL stages
- No clear indication of scope

### 3. Configuration Conflicts
- Multiple stages might have conflicting orchestrator settings
- Last saved stage overwrites global settings
- No way to save orchestrator config independently

## Proposed Solution

### 1. Separate Configuration Sections

```javascript
// Three distinct configuration domains:

// 1. Extraction Configuration (per-stage)
const stageConfigs = {
    "products": {
        prompt_id: "uuid",
        prompt_text: "Extract products...",
        fields: [...],
        models: ["gpt-4", "claude-3"],
        temperature: 0.7,  // Stage-specific temperature
        max_tokens: 2000
    }
};

// 2. Orchestration Configuration (system-wide)
const orchestrationConfig = {
    orchestrator: {
        model: "claude-4-opus",
        prompt: "You are orchestrating...",
        temperature: 0.3,
        max_iterations: 5,
        budget_allocation: "dynamic"
    },
    comparison: {
        model: "gpt-4-vision-preview",
        prompt: "Compare these images...",
        use_visual_comparison: true,
        abstraction_layers: [...]
    },
    system: {
        system_type: "custom_consensus",
        max_budget: 2.00,
        target_accuracy: 0.95
    }
};

// 3. Pipeline Configuration (combines both)
const pipelineConfig = {
    name: "High Accuracy Beverage Pipeline",
    description: "Optimized for beverage shelves",
    orchestration: orchestrationConfig,
    stages: stageConfigs,
    metadata: {
        created_at: "2024-01-01",
        version: "1.0"
    }
};
```

### 2. UI Changes

#### A. Separate Save Buttons
```jsx
// In Stage Configuration Section
<button onClick={handleSaveStageOnly}>
    Save Stage Configuration
</button>

// In Orchestrator Section
<button onClick={handleSaveOrchestration}>
    Save Orchestration Settings
</button>

// At Pipeline Level
<button onClick={handleSavePipeline}>
    Save Complete Pipeline
</button>
```

#### B. Clear Section Headers
```jsx
<div className="config-section">
    <h3>Stage Configuration</h3>
    <p className="help-text">
        Configure how this specific stage extracts information
    </p>
    {/* Stage-specific settings */}
</div>

<div className="config-section">
    <h3>Pipeline Orchestration</h3>
    <p className="help-text">
        Configure how the entire extraction pipeline operates
    </p>
    {/* Orchestrator, comparison, system settings */}
</div>
```

### 3. Implementation Plan

#### Phase 1: Backend Separation
```python
# src/api/configuration.py

class StageConfiguration(BaseModel):
    """Configuration for a single extraction stage"""
    prompt_id: str
    prompt_text: str
    fields: List[FieldDefinition]
    models: List[str]
    temperature: float = 0.7
    max_tokens: int = 2000

class OrchestrationConfiguration(BaseModel):
    """Configuration for pipeline orchestration"""
    orchestrator: OrchestratorSettings
    comparison: ComparisonSettings
    system: SystemSettings

class PipelineConfiguration(BaseModel):
    """Complete pipeline configuration"""
    name: str
    description: str
    orchestration: OrchestrationConfiguration
    stages: Dict[str, StageConfiguration]
    metadata: ConfigMetadata

# Separate endpoints
@router.post("/api/config/stage/{stage_id}")
async def save_stage_config(stage_id: str, config: StageConfiguration):
    """Save configuration for a specific stage"""
    pass

@router.post("/api/config/orchestration")
async def save_orchestration_config(config: OrchestrationConfiguration):
    """Save orchestration configuration"""
    pass

@router.post("/api/config/pipeline")
async def save_pipeline_config(config: PipelineConfiguration):
    """Save complete pipeline configuration"""
    pass
```

#### Phase 2: UI Refactoring
```javascript
// Separate state management
const [stageConfigs, setStageConfigs] = useState({});
const [orchestrationConfig, setOrchestrationConfig] = useState({
    orchestrator: { model: 'claude-4-opus', prompt: '' },
    comparison: { model: 'gpt-4-vision-preview', use_visual: true },
    system: { system_type: 'custom_consensus', max_budget: 2.0 }
});

// Save functions with clear scope
const handleSaveStageOnly = () => {
    const stageConfig = {
        prompt_id: selectedPrompt?.id,
        prompt_text: editedPrompt,
        fields: definedFields,
        models: stageModels[selectedStage.id] || []
    };
    
    // Save only stage config
    saveStageConfiguration(selectedStage.id, stageConfig);
};

const handleSaveOrchestration = () => {
    // Save only orchestration config
    saveOrchestrationConfiguration(orchestrationConfig);
};
```

### 4. Benefits

1. **Clear Separation of Concerns**
   - Stage configs are stage-specific
   - Orchestration is pipeline-wide
   - No accidental overwrites

2. **Better User Experience**
   - Clear what each save button does
   - Can update orchestration without touching stages
   - Can share stage configs across pipelines

3. **Improved Flexibility**
   - Can have stage-specific temperatures
   - Can reuse orchestration configs
   - Can compose pipelines from existing parts

4. **Easier Testing**
   - Test stages independently
   - Test orchestration independently
   - Mock configurations more easily

### 5. Migration Path

1. **Keep backward compatibility** temporarily
2. **Add new endpoints** alongside existing ones
3. **Update UI** to use new structure
4. **Deprecate old endpoints** after migration
5. **Clean up** old code

### 6. Visual Mockup

```
┌─────────────────────────────────────────────────┐
│ Pipeline: High Accuracy Beverage Pipeline       │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─── Pipeline Settings ────────────────────┐   │
│ │ System: Custom Consensus                 │   │
│ │ Budget: £2.00                           │   │
│ │ Target: 95%                             │   │
│ │ [Save Pipeline Settings]                │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ ┌─── Orchestration ─────────────────────────┐   │
│ │ Orchestrator Model: Claude 4 Opus        │   │
│ │ Comparison Model: GPT-4 Vision          │   │
│ │ Visual Mode: ✓                          │   │
│ │ [Save Orchestration]                    │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ ┌─── Stage: Products ───────────────────────┐   │
│ │ Prompt: Extract all products...          │   │
│ │ Models: [GPT-4] [Claude-3]              │   │
│ │ Temperature: 0.7                        │   │
│ │ [Save Stage] [Test Stage]               │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

This separation makes it clear what each section controls and what each save button affects.