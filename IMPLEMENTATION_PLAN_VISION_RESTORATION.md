# Implementation Plan: Restoring Three-System Architecture with Visual Feedback Loop

## Vision Summary
1. **Actually use the 3 systems** (Custom Consensus, LangGraph, Hybrid) based on UI selection
2. **Remove Structure Analysis Agent** - integrate into main extraction pipeline with configurable prompts
3. **Generate planograms during extraction** (Products/Details stages), not after
4. **Image Comparison Agent gets configurable prompts** from UI
5. **Visual feedback loop**: Image comparison results flow back to inform next extraction attempt

## Current Problems

### 1. System Selection Ignored
- UI shows system selection but `master_orchestrator.py` ignores it
- Always creates `ExtractionOrchestrator` instead of using `ExtractionSystemFactory`
- Three systems in `/src/systems/` are never instantiated

### 2. Structure Analysis Agent Shouldn't Exist  
- Hardcoded agent at `src/agents/structure_agent.py`
- Called directly in `extraction_orchestrator.py:78-84`
- Should be a configurable stage like Products/Details

### 3. No Visual Feedback Loop
- Image comparison happens after extraction completes
- Results don't flow back to extraction models
- No cumulative learning from visual differences

### 4. Hardcoded Image Comparison Prompts
- `src/comparison/image_comparison_agent.py` uses hardcoded prompt
- No UI configuration for comparison instructions

## Implementation Steps

### Phase 1: Fix System Routing (Priority: HIGH)

#### 1.1 Update Master Orchestrator to Use System Factory
```python
# master_orchestrator.py - Line ~114
# REMOVE:
self.extraction_orchestrator = ExtractionOrchestrator(...)

# REPLACE WITH:
from src.systems.base_system import ExtractionSystemFactory
selected_system = configuration.get('system', 'custom_consensus')
system_type = selected_system.replace('_consensus', '')  # custom, langgraph, or hybrid
self.extraction_system = ExtractionSystemFactory.get_system(
    system_type=system_type,
    config=self.config
)
```

#### 1.2 Update System Base Classes
- Modify `BaseExtractionSystem` to support stage-based extraction
- Add methods for receiving visual feedback
- Ensure all three systems implement the new interface

### Phase 2: Remove Structure Analysis Agent (Priority: HIGH)

#### 2.1 Delete Structure Agent
```bash
# Remove the file
rm src/agents/structure_agent.py
```

#### 2.2 Update Extraction Orchestrator
```python
# extraction_orchestrator.py - Line ~78-84
# REMOVE the structure agent call
# REPLACE WITH stage-based structure extraction using configured prompts
```

#### 2.3 Ensure Structure Stage Uses UI Prompts
- Structure stage should use `stage_prompts['structure']` from UI
- No hardcoded prompts for any stage

### Phase 3: Planogram Generation During Extraction (Priority: HIGH)

#### 3.1 Move Planogram Generation
```python
# extraction_orchestrator.py - After products stage
async def _execute_products_stage(...):
    # Extract products
    products_result = await self._extract_products(...)
    
    # Generate planogram immediately
    planogram_png = await self._generate_planogram(products_result)
    
    # Compare with original image
    comparison_feedback = await self._compare_images(
        original_image, 
        planogram_png,
        comparison_prompt=self.stage_prompts.get('comparison', DEFAULT_COMPARISON_PROMPT)
    )
    
    # Pass feedback to next stage
    context['visual_feedback'] = comparison_feedback
    return products_result, context
```

#### 3.2 Create Comparison Integration
```python
# New method in extraction_orchestrator.py
async def _compare_images(self, original, planogram, comparison_prompt):
    from src.comparison.image_comparison_agent import ImageComparisonAgent
    agent = ImageComparisonAgent()
    return await agent.compare_with_prompt(
        original_image=original,
        planogram_image=planogram,
        prompt=comparison_prompt
    )
```

### Phase 4: UI Configuration for Image Comparison (Priority: HIGH)

#### 4.1 Add Comparison Stage to UI
```javascript
// new_dashboard.html - Add new stage
const stages = ['structure', 'products', 'details', 'comparison'];

// Add comparison prompt field
<div class="stage-config" data-stage="comparison">
    <h4>Image Comparison Configuration</h4>
    <textarea id="comparison-prompt" placeholder="Enter comparison instructions...">
    Compare the retail shelf photo with the planogram representation.
    Identify key differences in:
    - Product positions
    - Missing products
    - Quantity mismatches
    </textarea>
</div>
```

#### 4.2 Update Database Schema
```sql
-- Ensure prompt_templates supports comparison stage
INSERT INTO prompt_templates (name, stage, content, is_active)
VALUES ('default_comparison', 'comparison', 'Compare the images...', true);
```

#### 4.3 Update Image Comparison Agent
```python
# image_comparison_agent.py
class ImageComparisonAgent:
    async def compare_with_prompt(self, original_image, planogram_image, prompt):
        # Use provided prompt instead of hardcoded one
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image", "image": original_image},
                {"type": "image", "image": planogram_image}
            ]
        }]
        # ... rest of comparison logic
```

### Phase 5: Implement Visual Feedback Loop (Priority: HIGH)

#### 5.1 Update Cumulative Learning
```python
# extraction_orchestrator.py
def _build_cumulative_prompt(self, stage, context):
    prompt = self.stage_prompts.get(stage, '')
    
    # Add visual feedback if available
    if context.get('visual_feedback') and stage in ['products', 'details']:
        prompt += "\n\nVISUAL COMPARISON FEEDBACK:\n"
        prompt += context['visual_feedback']
        prompt += "\n\nPlease address these visual discrepancies in your extraction."
    
    # Add previous attempts context
    if context.get('previous_attempts'):
        prompt += "\n\nPREVIOUS ATTEMPTS:\n"
        # ... existing cumulative learning logic
    
    return prompt
```

#### 5.2 Update Context Flow
```python
# Ensure context flows through all stages
context = {
    'previous_attempts': [],
    'visual_feedback': None,
    'locked_positions': {},
    'focus_areas': []
}

# After each stage, update context
context = await self._execute_stage_with_feedback(stage, image, context)
```

### Phase 6: Three Systems Implementation (Priority: MEDIUM)

#### 6.1 Update Custom Consensus System
```python
# src/systems/custom_consensus.py
class CustomConsensusSystem(BaseExtractionSystem):
    async def extract_with_consensus(self, image_data, upload_id):
        # Implement stage-based extraction with visual feedback
        # Use voting mechanism for consensus
        # Direct API calls, full control
```

#### 6.2 Update LangGraph System
```python
# src/systems/langgraph_system.py
class LangGraphConsensusSystem(BaseExtractionSystem):
    async def extract_with_consensus(self, image_data, upload_id):
        # Use LangGraph workflow management
        # Implement visual feedback as graph nodes
        # State persistence between stages
```

#### 6.3 Update Hybrid System
```python
# src/systems/hybrid_system.py
class HybridConsensusSystem(BaseExtractionSystem):
    async def extract_with_consensus(self, image_data, upload_id):
        # Combine custom consensus with LangChain tools
        # Use memory for visual feedback context
        # Enhanced reasoning with both approaches
```

## Testing Plan

### 1. System Routing Test
```python
# Test that each system is actually used
for system in ['custom_consensus', 'langgraph', 'hybrid']:
    result = await process_with_system(image, system)
    assert result.system_type == system
```

### 2. Visual Feedback Loop Test
```python
# Test that comparison feedback affects extraction
result1 = await extract_without_feedback(image)
result2 = await extract_with_feedback(image, comparison_feedback)
assert result2.accuracy > result1.accuracy
```

### 3. Configuration Test
```python
# Test all stages use UI prompts
config = {
    'stage_prompts': {
        'structure': 'Custom structure prompt',
        'products': 'Custom products prompt',
        'details': 'Custom details prompt',
        'comparison': 'Custom comparison prompt'
    }
}
result = await extract_with_config(image, config)
# Verify prompts were used
```

## Migration Strategy

1. **Day 1-2**: Implement system routing fix
2. **Day 3-4**: Remove Structure Agent, integrate into pipeline
3. **Day 5-6**: Add comparison configuration to UI
4. **Day 7-8**: Implement visual feedback loop
5. **Day 9-10**: Test all three systems with new flow
6. **Day 11-12**: Performance optimization and bug fixes

## Success Metrics

1. **System Selection Works**: Choosing different systems in UI produces different behavior
2. **All Stages Configurable**: No hardcoded prompts anywhere
3. **Visual Feedback Improves Accuracy**: Measurable improvement when feedback is used
4. **Planogram Generated During Extraction**: Not as post-processing
5. **Three Systems Differentiated**: Each system shows unique characteristics as designed

## Risks and Mitigations

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Implement behind feature flag first

2. **Risk**: Performance degradation from mid-extraction planogram generation
   - **Mitigation**: Async generation, caching, only generate when needed

3. **Risk**: Three systems have diverged too much from original design
   - **Mitigation**: Start with Custom system, gradually add others

## Next Steps

1. Review this plan and approve approach
2. Create feature branch for implementation
3. Start with Phase 1: Fix system routing
4. Implement visual feedback loop early for testing
5. Iterate based on results