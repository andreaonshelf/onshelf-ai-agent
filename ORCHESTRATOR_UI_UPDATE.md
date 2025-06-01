# Orchestrator UI Update Required

## Current Issue
The UI currently shows only one "Orchestrator Model" dropdown, but we actually have 3 different orchestrators that each serve different purposes and could benefit from custom instructions.

## Orchestrators That Need UI Controls

### 1. Master Orchestrator
- **Purpose**: Overall process management and iteration control
- **Needs**:
  - Model selection dropdown
  - Custom instructions textarea
  - Example instructions: "Prioritize accuracy over speed", "Stop early if confidence is high", "Focus on price extraction"

### 2. Extraction Orchestrator  
- **Purpose**: Manages cumulative learning and extraction strategy
- **Needs**:
  - Model selection dropdown (can be different from Master)
  - Custom instructions textarea
  - Example instructions: "Use aggressive learning from previous iterations", "Lock high-confidence items early", "Focus on edge shelves"

### 3. Planogram Orchestrator
- **Purpose**: Generates visual planogram representations
- **Needs**:
  - Model selection dropdown (often can use cheaper models)
  - Custom instructions textarea  
  - Example instructions: "Create detailed product-level view", "Include price labels", "Use compact layout"

## Proposed UI Changes

Replace the current single orchestrator section with:

```html
<!-- Orchestrator Configuration -->
<div style={{ marginBottom: '20px' }}>
    <h4>Orchestrator Configuration</h4>
    
    <!-- Master Orchestrator -->
    <div style={{ marginBottom: '16px', padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            Master Orchestrator (Overall Process Control):
        </label>
        <select value={masterOrchestratorModel} onChange={(e) => setMasterOrchestratorModel(e.target.value)}>
            <!-- Model options -->
        </select>
        <textarea 
            placeholder="Instructions for overall process management..."
            value={masterOrchestratorPrompt}
            onChange={(e) => setMasterOrchestratorPrompt(e.target.value)}
        />
    </div>
    
    <!-- Extraction Orchestrator -->
    <div style={{ marginBottom: '16px', padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            Extraction Orchestrator (Learning Strategy):
        </label>
        <select value={extractionOrchestratorModel} onChange={(e) => setExtractionOrchestratorModel(e.target.value)}>
            <!-- Model options -->
        </select>
        <textarea 
            placeholder="Instructions for extraction strategy and learning..."
            value={extractionOrchestratorPrompt}
            onChange={(e) => setExtractionOrchestratorPrompt(e.target.value)}
        />
    </div>
    
    <!-- Planogram Orchestrator -->
    <div style={{ marginBottom: '16px', padding: '16px', background: '#f8fafc', borderRadius: '8px' }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
            Planogram Orchestrator (Visualization):
        </label>
        <select value={planogramOrchestratorModel} onChange={(e) => setPlanogramOrchestratorModel(e.target.value)}>
            <!-- Model options -->
        </select>
        <textarea 
            placeholder="Instructions for planogram generation..."
            value={planogramOrchestratorPrompt}
            onChange={(e) => setPlanogramOrchestratorPrompt(e.target.value)}
        />
    </div>
</div>
```

## Configuration Structure Update

The pipeline configuration should be updated to:

```json
{
  "pipeline": {
    "temperature": 0.7,
    "orchestrators": {
      "master": {
        "model": "claude-4-opus",
        "prompt": "Custom instructions for master orchestrator"
      },
      "extraction": {
        "model": "claude-4-sonnet", 
        "prompt": "Custom instructions for extraction orchestrator"
      },
      "planogram": {
        "model": "gpt-4o-mini",
        "prompt": "Custom instructions for planogram generation"
      }
    },
    "enable_comparison": true,
    "comparison_threshold": 0.85
  }
}
```

## Benefits

1. **Fine-grained control** - Different models for different tasks
2. **Cost optimization** - Use cheaper models for simpler tasks (like planogram generation)
3. **Specialized instructions** - Each orchestrator gets task-specific guidance
4. **Better visibility** - Users understand the multi-orchestrator architecture

## What's Saved to Library

When saving prompts to library, the system saves:
1. **Prompt text** - The actual prompt content
2. **Field definitions** - Complete schema structure including:
   - Field names
   - Data types
   - Descriptions
   - Required/optional status
   - Nested field structures

This is perfect for Instructor as it provides both the prompt and the expected output structure!