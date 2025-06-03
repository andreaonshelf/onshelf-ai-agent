# Integrating Adaptive Prompts with Orchestrators

## Quick Integration Guide

### 1. Update ExtractionOrchestrator

```python
# In extraction_orchestrator.py
from ..extraction.adaptive_prompts import AdaptivePromptBuilder

class ExtractionOrchestrator:
    def __init__(self):
        # ... existing init ...
        self.prompt_builder = AdaptivePromptBuilder()
    
    async def _execute_shelf_by_shelf_extraction(self, ...):
        # ... existing code ...
        
        for shelf_num in range(1, context.structure.shelf_count + 1):
            # Build context for this shelf
            shelf_context = {
                'shelf_number': shelf_num,
                'total_shelves': context.structure.shelf_count,
                'overall_confidence': self._get_shelf_confidence(shelf_num, context),
                'attempt_number': agent_number
            }
            
            # Add previous extraction data if available
            if agent_number > 1 and context.previous_attempts:
                shelf_context['previous_extraction'] = self._get_previous_shelf_data(
                    shelf_num, context.previous_attempts
                )
            
            # Get the unified prompt from configuration or templates
            unified_prompt = self.stage_prompts.get('products', 
                                                   prompt_templates.get_template('products_unified'))
            
            # Build adaptive prompt
            shelf_prompt = self.prompt_builder.build_adaptive_prompt(
                unified_prompt=unified_prompt,
                context=shelf_context,
                attempt_number=agent_number,
                confidence_threshold=0.8
            )
            
            # Execute extraction with adaptive prompt
            # ... rest of extraction code ...
```

### 2. Update UI Instructions

In the UI, users should input prompts in this format:

```
=== INITIAL EXTRACTION ===
[Your standard extraction instructions]

=== RETRY EXTRACTION (IF CONFIDENCE < 0.8) ===
[Your retry-specific instructions with {variables}]
```

### 3. Available Variables for Retry Section

Structure Stage:
- `{shelf_count}` - Previously found shelf count
- `{width}` - Previously found width
- `{confidence_issues}` - Identified problems
- `{specific_issue_1}` - Primary issue to focus on

Products Stage:
- `{high_confidence_products}` - Products to keep
- `{low_confidence_positions}` - Areas needing work
- `{problem_area_1}` - Specific area to check
- `{uncertain_product}` - Product needing verification

Details Stage:
- `{existing_details}` - Already extracted details
- `{missing_attributes}` - What's still needed
- `{where_to_find_price}` - Specific guidance

## Benefits of This Approach

1. **Single UI Field** - No UI changes needed
2. **User Control** - Users can customize both initial and retry behavior
3. **Graceful Fallback** - If no retry section, uses initial prompt
4. **Context Aware** - Only uses retry when confidence is improvable
5. **Backward Compatible** - Existing prompts without retry sections still work

## Example Usage in UI

User enters in Extraction Orchestrator prompt field:
```
=== INITIAL EXTRACTION ===
Extract all products from shelf {shelf_number}.
Scan left to right, identify brand, name, and facing count.

=== RETRY EXTRACTION (IF CONFIDENCE < 0.8) ===
Focus on improving shelf {shelf_number} extraction.
Keep: {high_confidence_products}
Fix: {low_confidence_positions}
Check {problem_area_1} for missed products.
```

The system automatically:
1. Uses initial section for first attempt
2. Switches to retry section for attempts 2+ if confidence is 60-80%
3. Fills in context variables
4. Falls back to initial if confidence is too low (<60%) or too high (>80%)