# Real-Time Master Orchestrator Monitoring

## Overview

The debug interface now shows the **ACTUAL** Master Orchestrator iteration cycle in real-time, not generic workflow steps. This connects directly to what the system is actually doing.

## Master Orchestrator Iteration Cycle

Each iteration follows these **REAL** steps from `src/orchestrator/master_orchestrator.py`:

### Step 1: Extract with Cumulative Learning
- **Component**: `ExtractionOrchestrator`
- **Method**: `extract_with_cumulative_learning()`
- **What it does**: 
  - Uses the chosen consensus system (Custom Consensus, LangGraph, or Hybrid)
  - Incorporates previous attempts and failure areas
  - Focuses on areas that failed in previous iterations
  - Locks in high-confidence positions from previous iterations

### Step 2: Generate Planogram
- **Component**: `PlanogramOrchestrator` 
- **Method**: `generate_for_agent_iteration()`
- **What it does**:
  - Creates visual planogram from extraction JSON
  - Uses `PlanogramGenerator.generate_from_extraction_result()`
  - Applies quality evaluation
  - **KEY**: This happens ONCE per iteration, creating a NEW planogram each time

### Step 3: AI Comparison Analysis
- **Component**: `ImageComparisonAgent`
- **Method**: `compare_image_vs_planogram()`
- **What it does**:
  - Compares original image vs generated planogram
  - Identifies visual differences
  - Analyzes spatial accuracy
  - Detects missing/extra products

### Step 4: Calculate Accuracy
- **Component**: `CumulativeFeedbackManager`
- **Method**: `analyze_accuracy_with_failure_areas()`
- **What it does**:
  - Analyzes comparison results
  - Calculates overall accuracy score
  - Identifies specific failure areas
  - Determines high-confidence positions to lock

### Step 5: Iteration Decision
- **Component**: `MasterOrchestrator`
- **Logic**: Target accuracy check
- **What it does**:
  - If `accuracy >= target_accuracy` (95%): **STOP**
  - If `accuracy < target_accuracy`: **Continue to next iteration**
  - Creates focused instructions for next iteration
  - Prepares failure area focus and locked positions

## Multiple Planograms Per Upload

**Critical Understanding**: The system generates **MULTIPLE** planograms per upload:

```
Upload ID: 12345
├── Iteration 1: Extract (18 products) → Generate Planogram A → Compare → 75% accuracy
├── Iteration 2: Extract (23 products) → Generate Planogram B → Compare → 88% accuracy  
├── Iteration 3: Extract (24 products) → Generate Planogram C → Compare → 95% accuracy ✓
└── Final Result: Planogram C (target achieved)
```

## System-Specific Behavior

The monitoring adapts to show the **actual** system being used:

### Custom Consensus System
- Shows parallel model voting in Step 1
- Displays consensus mechanisms
- Tracks individual model performance

### LangGraph System  
- Shows workflow node progression
- Displays state management
- Tracks conditional routing

### Hybrid System
- Shows adaptive model selection
- Displays dynamic consensus
- Tracks optimization decisions

## Real-Time Updates

The interface receives WebSocket updates for:

- `iteration_start`: New iteration begins
- `extract_data_start/complete`: Extraction progress
- `planogram_generation_start`: Planogram creation begins
- `planogram_generated`: New planogram created
- `ai_comparison_start/complete`: Comparison analysis
- `accuracy_calculated`: Accuracy score and decision
- `iteration_decision`: Continue or stop decision

## Key Differences from Generic Workflows

❌ **Generic**: "Run extraction → Generate planogram → Done"
✅ **Real**: "Iterate until target accuracy achieved with cumulative learning"

❌ **Generic**: "One planogram per upload"  
✅ **Real**: "Multiple planograms per upload (one per iteration)"

❌ **Generic**: "Fixed workflow steps"
✅ **Real**: "Adaptive steps based on system and previous failures"

## Monitoring Benefits

1. **Transparency**: See exactly what the system is doing
2. **Debugging**: Identify where iterations fail or succeed
3. **Optimization**: Understand which systems perform better
4. **Learning**: See how cumulative learning improves results
5. **Cost Tracking**: Monitor API costs per iteration

## Future Enhancements

- Real-time planogram preview updates
- Failure area visualization
- Model performance comparison
- Cost optimization suggestions
- Iteration efficiency metrics 