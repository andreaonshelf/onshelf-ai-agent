cor# Corrected Vision: Planogram Generation After EACH Model

## Your Actual Vision

### For Products Stage (Example with 3 Models):

```
Model 1 (Products) → Generate Planogram → Visual Compare → Feedback
                                                               ↓
Model 2 (Products) ← Pass feedback as context ←────────────────┘
        ↓
Generate Planogram → Visual Compare → Feedback
                                         ↓
Model 3 (Products) ← Pass feedback as context ←────┘
        ↓
Generate Planogram → Visual Compare → Final Products Result
```

### For Details Stage (Same Pattern):

```
Model 1 (Details) → Generate Planogram → Visual Compare → Feedback
                                                              ↓
Model 2 (Details) ← Pass feedback as context ←───────────────┘
        ↓
Generate Planogram → Visual Compare → Feedback
                                         ↓
Model 3 (Details) ← Pass feedback as context ←────┘
        ↓
Generate Planogram → Visual Compare → Final Details Result
```

## Key Differences from Current Implementation

### Current Implementation:
- Extracts with ALL models/iterations
- Generates planogram ONCE at the end
- Compares ONCE
- No feedback between models

### Your Vision:
- Extract with Model 1
- Generate planogram immediately
- Compare and get feedback
- Pass feedback to Model 2 as context
- Model 2 extracts WITH visual feedback knowledge
- Repeat for each model

## Why This Makes Sense

1. **Progressive Refinement**: Each model builds on visual feedback from previous attempts
2. **Context-Aware Extraction**: Model 2 knows "The planogram showed a gap at position 4, but there's a product visible there"
3. **Reduces Compound Errors**: Early visual feedback prevents propagating mistakes
4. **True Cumulative Learning**: Not just data accumulation but visual validation accumulation

## Implementation Requirements

### 1. Modify Extraction Orchestrator Flow

```python
async def _execute_products_stage_with_visual_feedback(self, images, structure, models_to_use):
    """Execute products stage with visual feedback between each model"""
    
    all_visual_feedback = []
    best_extraction = None
    
    for i, model_id in enumerate(models_to_use):
        # Build prompt with accumulated visual feedback
        prompt = self._build_products_prompt(
            structure=structure,
            visual_feedback=all_visual_feedback,
            attempt_number=i+1
        )
        
        # Extract with current model
        extraction_result = await self._extract_with_model(
            model_id=model_id,
            prompt=prompt,
            images=images
        )
        
        # Generate planogram immediately
        planogram = await self._generate_planogram(extraction_result)
        
        # Visual comparison
        comparison_result = await self._compare_images(
            original=images['enhanced'],
            planogram=planogram,
            comparison_prompt=self.stage_prompts.get('comparison')
        )
        
        # Add feedback to accumulator
        visual_feedback = {
            'model': model_id,
            'attempt': i+1,
            'comparison_result': comparison_result,
            'identified_issues': self._extract_actionable_feedback(comparison_result)
        }
        all_visual_feedback.append(visual_feedback)
        
        # Update best result if this is better
        if comparison_result.overall_similarity > (best_extraction[1] if best_extraction else 0):
            best_extraction = (extraction_result, comparison_result.overall_similarity)
    
    return best_extraction[0], all_visual_feedback
```

### 2. Enhanced Prompt Building with Visual Feedback

```python
def _build_products_prompt(self, structure, visual_feedback, attempt_number):
    base_prompt = self.stage_prompts.get('products', DEFAULT_PRODUCTS_PROMPT)
    
    if visual_feedback:
        base_prompt += "\n\nVISUAL FEEDBACK FROM PREVIOUS ATTEMPTS:\n"
        
        for feedback in visual_feedback:
            base_prompt += f"\nAttempt {feedback['attempt']} ({feedback['model']}):\n"
            
            # Add specific issues found
            for issue in feedback['identified_issues']:
                if issue['type'] == 'missing_product':
                    base_prompt += f"- Missing product at shelf {issue['shelf']}, position {issue['position']}\n"
                elif issue['type'] == 'wrong_position':
                    base_prompt += f"- Product {issue['product']} appears to be at wrong position\n"
                elif issue['type'] == 'quantity_mismatch':
                    base_prompt += f"- Facing count mismatch for {issue['product']}: planogram shows {issue['planogram_count']}, image suggests {issue['image_count']}\n"
        
        base_prompt += "\nPlease address these visual discrepancies in your extraction."
    
    return base_prompt
```

### 3. Structured Visual Feedback Extraction

```python
def _extract_actionable_feedback(self, comparison_result):
    """Convert comparison result into actionable feedback for next model"""
    actionable_feedback = []
    
    # Missing products (visible in image but not in extraction)
    for missing in comparison_result.missing_products:
        actionable_feedback.append({
            'type': 'missing_product',
            'shelf': missing.shelf,
            'position': missing.position,
            'description': missing.description
        })
    
    # Extra products (in extraction but not visible in image)
    for extra in comparison_result.extra_products:
        actionable_feedback.append({
            'type': 'extra_product',
            'product': extra.product_name,
            'shelf': extra.shelf,
            'position': extra.position
        })
    
    # Position mismatches
    for mismatch in comparison_result.mismatches:
        actionable_feedback.append({
            'type': 'position_mismatch',
            'issue': mismatch.issue,
            'severity': mismatch.severity
        })
    
    return actionable_feedback
```

### 4. Update Master Orchestrator

Instead of waiting until the end to generate planogram:

```python
# REMOVE this from master_orchestrator.py (lines ~251-257)
# This happens too late!

# INSTEAD, planogram generation happens INSIDE extraction stages
# The master orchestrator just coordinates the stages
```

## Benefits of This Approach

1. **Real-time Visual Validation**: Each model's output is visually validated before the next model runs
2. **Informed Extraction**: Later models know exactly what visual issues to look for
3. **Efficient Resource Use**: Stop early if visual accuracy is achieved
4. **Better Debugging**: See how each model responds to visual feedback
5. **True Multi-Model Consensus**: Models can "vote" based on visual evidence

## Example Prompt Evolution

**Model 1 Prompt**:
```
Extract all products from this retail shelf image...
```

**Model 2 Prompt** (after visual feedback):
```
Extract all products from this retail shelf image...

VISUAL FEEDBACK FROM PREVIOUS ATTEMPTS:
Attempt 1 (claude-3-sonnet):
- Missing product at shelf 2, position 4
- Facing count mismatch for Coca-Cola: planogram shows 2, image suggests 3
- Product "Pepsi Max" appears to be at wrong position

Please address these visual discrepancies in your extraction.
```

**Model 3 Prompt** (with accumulated feedback):
```
Extract all products from this retail shelf image...

VISUAL FEEDBACK FROM PREVIOUS ATTEMPTS:
Attempt 1 (claude-3-sonnet):
- Missing product at shelf 2, position 4
- Facing count mismatch for Coca-Cola: planogram shows 2, image suggests 3

Attempt 2 (gpt-4o):
- Successfully identified product at shelf 2, position 4 as "Sprite Zero"
- Coca-Cola facing count now correct (3)
- New issue: Missing product at shelf 3, position 1

Please address these remaining visual discrepancies in your extraction.
```

## This is TRUE Cumulative Learning with Visual Feedback!