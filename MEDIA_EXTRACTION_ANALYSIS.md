# Media Extraction Programs Analysis: Planogram Generation & Visual Comparison

## Current Implementation Analysis

### 1. When Planogram Generation Happens

**Current Flow (Iteration-Based):**
```
Structure → Products → Details → THEN Generate Planogram → Compare → Next Iteration
```

**Current Flow (Stage-Based):**
```
Structure Stage → Products Stage → Details Stage → THEN Generate Planogram → Compare
```

In BOTH approaches, planogram generation happens **AFTER** all extraction is complete, not during.

### 2. Where Planogram Generation Code Lives

**Master Orchestrator** (`master_orchestrator.py:251-257`):
```python
planogram_result = await self.planogram_orchestrator.generate_for_agent_iteration(
    agent_number=iteration,
    extraction_result=extraction_result,  # Complete extraction result
    structure_context=structure_context,
    abstraction_level=abstraction_level,
    original_image=images['enhanced']
)
```

This happens AFTER extraction_result is complete (line 205-214).

### 3. Visual Comparison Timing

**Current Implementation** (`master_orchestrator.py:286-292`):
```python
# Only happens AFTER planogram is generated
comparison_result = await self.comparison_agent.compare_image_vs_planogram(
    original_image=images['enhanced'],
    planogram=planogram_result.planogram,
    structure_context=structure_context,
    planogram_image=planogram_png,
    model=comparison_model
)
```

The comparison feedback is analyzed (line 305-307) but **NOT passed back to extraction**.

## What Should Happen (Your Vision)

### Ideal Flow:
```
Structure → Products → Generate Planogram → Visual Compare → 
Feedback to Details → Details (with visual context) → Final Planogram
```

### Why This Makes Sense:

1. **After Products Stage**: We have positions and basic product info - enough to generate a planogram
2. **Before Details Stage**: Visual feedback can guide detail extraction (e.g., "The price tag visible at position 3 wasn't captured")
3. **Cumulative Learning**: Details extraction benefits from knowing what the visual comparison found

## Should Both Stages Have Planogram Generation?

### Products Stage: YES
- **Purpose**: Basic planogram for position verification
- **What's needed**: Product names, positions, facings
- **What's NOT needed**: Prices, sizes, detailed variants
- **Benefit**: Early visual feedback catches position errors

### Details Stage: YES (Updated Planogram)
- **Purpose**: Complete planogram with all details
- **What's added**: Prices, sizes, promotional tags
- **Benefit**: Final validation with complete information

## Implementation Requirements

### 1. Split Planogram Generation

```python
# In extraction_orchestrator.py
async def _execute_products_stage(...):
    # Extract products
    products_result = await self._extract_products(...)
    
    # Generate basic planogram immediately
    basic_planogram = await self._generate_basic_planogram(products_result)
    
    # Visual comparison
    comparison_feedback = await self._compare_with_original(
        original_image, 
        basic_planogram,
        comparison_prompt=self.stage_prompts.get('comparison')
    )
    
    # Store feedback for details stage
    self.visual_feedback = comparison_feedback
    
    return products_result

async def _execute_details_stage(...):
    # Include visual feedback in prompt
    prompt = self._build_details_prompt_with_visual_feedback(
        products=products,
        visual_feedback=self.visual_feedback
    )
    
    # Extract details with visual context
    details_result = await self._extract_details(prompt, ...)
    
    # Generate final detailed planogram
    final_planogram = await self._generate_detailed_planogram(details_result)
    
    return details_result
```

### 2. Two Types of Planogram Generation

**Basic Planogram (After Products):**
- Focus on layout accuracy
- Simple product blocks
- Position verification
- No detailed information needed

**Detailed Planogram (After Details):**
- Full product information
- Prices, sizes, variants
- Complete visual representation
- Ready for final output

### 3. Visual Feedback Integration

The visual feedback should be structured and actionable:

```python
visual_feedback = {
    "position_mismatches": [
        {"shelf": 2, "position": 3, "issue": "Product detected in image but not in extraction"},
        {"shelf": 3, "position": 1, "issue": "Empty space in planogram but product visible in image"}
    ],
    "detail_opportunities": [
        {"shelf": 1, "position": 2, "observation": "Price tag clearly visible - $3.99"},
        {"shelf": 2, "position": 5, "observation": "Size variant visible - 500ml"}
    ]
}
```

### 4. Cumulative Learning Enhancement

```python
# In details prompt building
def _build_details_prompt_with_visual_feedback(self, products, visual_feedback):
    prompt = self.stage_prompts['details']
    
    if visual_feedback:
        prompt += "\n\nVISUAL COMPARISON INSIGHTS:\n"
        
        # Add position corrections
        if visual_feedback.get('position_mismatches'):
            prompt += "\nPosition issues to address:\n"
            for mismatch in visual_feedback['position_mismatches']:
                prompt += f"- {mismatch['issue']}\n"
        
        # Add detail opportunities
        if visual_feedback.get('detail_opportunities'):
            prompt += "\nDetails visible in image:\n"
            for opportunity in visual_feedback['detail_opportunities']:
                prompt += f"- {opportunity['observation']}\n"
    
    return prompt
```

## Benefits of This Approach

1. **Early Error Detection**: Position errors caught before details extraction
2. **Guided Detail Extraction**: Visual feedback helps identify what details to look for
3. **Reduced Iterations**: Getting it right within stages instead of full re-runs
4. **Better User Experience**: See planogram evolution during processing
5. **More Accurate Details**: Visual cues guide the detail extraction

## Implementation Priority

1. **High Priority**: 
   - Add planogram generation after products stage
   - Pass visual feedback to details stage
   - Make Image Comparison Agent configurable

2. **Medium Priority**:
   - Optimize planogram generation for speed (basic vs detailed)
   - Structure visual feedback format
   - Add visual feedback to cumulative learning

3. **Lower Priority**:
   - Real-time planogram updates during extraction
   - Progressive planogram refinement
   - Visual feedback analytics

## Conclusion

Yes, media extraction programs (planogram generation and visual comparison) should be implemented at BOTH Products and Details stages, but with different purposes:

- **Products Stage**: Basic planogram for position verification and visual feedback
- **Details Stage**: Complete planogram with all extracted information

This approach aligns with your vision of using visual feedback to improve extraction accuracy within the same iteration, rather than requiring multiple full iterations.