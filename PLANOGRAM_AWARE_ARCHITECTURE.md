# Planogram-Aware Extraction Architecture

## Core Concept
The extraction process should be fundamentally aware that its output will be rendered as a visual planogram grid, not just data.

## Key Components

### 1. Master Orchestrator - The Strategic Thinker
**Role**: Understands both the image reality AND the planogram constraints

**Responsibilities**:
- Injects PLANOGRAM_AWARE_PROMPT into all extractions
- After each iteration, evaluates: "Will this create a sensible planogram?"
- Guides improvements based on visual logic, not just data accuracy
- Examples of guidance:
  - "The gap at position 4 doesn't match the image - likely a missed product"
  - "Three Coke facings followed by 2 empty positions seems wrong"
  - "Stack of 2 makes sense for the tall products on shelf 3"

**Key Prompts**:
```
Given this extraction will be rendered as:
[Product][Product][Gap][Product]

Does this match what you see in the image? 
If not, what's likely missing or wrong?
```

### 2. Extraction Orchestrator - The Executor
**Role**: Extracts with planogram awareness

**Responsibilities**:
- Always includes PLANOGRAM_AWARE_PROMPT in extraction instructions
- Focuses on positional accuracy (gaps matter!)
- Considers visual width (facings) and height (stacks)
- Learns from previous attempts about what creates good planograms

**Enhanced Prompt Structure**:
```
PLANOGRAM_AWARE_PROMPT + 
CUMULATIVE_LEARNING + 
SPECIFIC_FOCUS_AREAS
```

### 3. Comparison Feedback - Visual Logic
**Current Problem**: Comparison is mocked/data-only
**Solution**: Enhance comparison to consider visual logic

**New Comparison Factors**:
- Logical gaps: "Is this gap intentional or a missed product?"
- Facing patterns: "Do these facing counts make visual sense?"
- Stack patterns: "Are taller products stacked logically?"
- Section coherence: "Do similar products cluster as expected?"

## Implementation Changes

### 1. Update Master Orchestrator
```python
class MasterOrchestrator:
    def __init__(self, config, extraction_config=None):
        # Add planogram awareness
        self.planogram_aware_prompt = PLANOGRAM_AWARE_PROMPT
        self.visual_logic_evaluator = VisualLogicEvaluator()
    
    async def achieve_target_accuracy(self, ...):
        # Pass planogram awareness to extraction
        extraction_config['base_prompt'] = self.planogram_aware_prompt
        
        # After extraction, evaluate visual logic
        visual_assessment = self.visual_logic_evaluator.assess(
            extraction_result, 
            original_image,
            "Will this create a logical planogram?"
        )
        
        # Use visual assessment in next iteration guidance
```

### 2. Update Extraction Orchestrator
```python
def _build_cumulative_prompt(self, agent_number, context):
    # Always start with planogram awareness
    prompt = PLANOGRAM_AWARE_PROMPT + "\n\n"
    
    # Add cumulative learning
    prompt += self._base_cumulative_prompt(agent_number, context)
    
    # Add visual hints from previous iterations
    if context.visual_feedback:
        prompt += "\n\nVISUAL FEEDBACK FROM PLANOGRAM:\n"
        prompt += context.visual_feedback
    
    return prompt
```

### 3. Add Visual Logic Evaluation
```python
class VisualLogicEvaluator:
    """Evaluates if extraction will create sensible planogram"""
    
    def assess(self, extraction, image, question):
        # Use AI to evaluate visual logic
        assessment = ai_model.analyze(
            image=image,
            extraction=extraction,
            question=question,
            context="This will be rendered as a grid planogram"
        )
        
        return {
            'makes_visual_sense': assessment.score > 0.8,
            'issues': assessment.visual_issues,
            'suggestions': assessment.improvements
        }
```

## Benefits

1. **Aligned Extraction**: AI understands it's extracting for a specific visual format
2. **Logical Planograms**: Reduces weird gaps and illogical layouts
3. **Better Feedback Loop**: Comparison considers visual logic, not just data matching
4. **Clearer Architecture**: Each component has a clear, focused role

## UI Implications

### Remove:
- Planogram Orchestrator model selection (it's not AI)

### Keep/Enhance:
- Master Orchestrator: Add "Visual Logic Instructions"
- Extraction Orchestrator: Add "Planogram Awareness Level"

### Example Master Orchestrator Instructions:
```
"Prioritize creating visually logical planograms. 
Avoid unexplained gaps. Consider that 3 facings 
of Coke should be contiguous. Taller products 
often stack 2 high."
```

## Migration Path

1. **Phase 1**: Add PLANOGRAM_AWARE_PROMPT to current extraction
2. **Phase 2**: Enhance Master Orchestrator with visual logic evaluation  
3. **Phase 3**: Implement real image comparison (not mocked)
4. **Phase 4**: Add visual feedback loop to guide iterations

This aligns with your original vision while making the system actually useful for creating accurate, logical planograms.