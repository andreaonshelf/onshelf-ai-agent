# UI Restructure Plan

## Current Problem
The UI currently has this structure:
```
Stage Configuration Card
├── Stage tabs
├── Stage-specific settings
│   ├── Prompt & Fields
│   ├── Model selection
│   ├── Temperature slider
│   ├── Orchestrator settings  ← WRONG LOCATION
│   └── Comparison settings    ← WRONG LOCATION
└── Save Stage button
```

## Correct Structure Should Be
```
Configuration Pipeline
├── Stage Configuration Card
│   ├── Stage tabs
│   ├── Stage-specific settings
│   │   ├── Prompt & Fields
│   │   └── Model selection
│   └── Save Stage button
│
├── Pipeline Configuration Card (NEW)
│   ├── Temperature slider
│   ├── Orchestrator settings
│   └── Comparison settings
│
└── Save Full Configuration button
```

## Changes Needed

1. **Move out of stage section**:
   - Temperature slider
   - Orchestrator Model Selection
   - Orchestrator Prompt
   - Planogram Comparison Settings

2. **Create new Pipeline Configuration section**:
   - Place it between Stage Configuration and Configuration Preview
   - Include all pipeline-wide settings

3. **Add granular prompt saving**:
   - Save prompt + fields separately from stage
   - Add API endpoint for prompt management
   - Enable prompt reuse across stages

## Benefits
- Clear separation of concerns
- "Save Stage" only saves stage data
- Pipeline settings are visually separate
- Better user understanding of scope