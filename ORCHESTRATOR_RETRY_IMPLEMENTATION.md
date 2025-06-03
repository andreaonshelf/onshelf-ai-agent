# Implementing Retry Prompts in Orchestrators

## Current Gap
The orchestrators pass cumulative learning but don't use dedicated retry prompts that focus on specific problem areas.

## Implementation Plan

### 1. Add Retry Templates to PromptTemplates

```python
# In src/extraction/prompts.py, add:

"structure_retry": """
Re-analyze this retail shelf image to verify and correct the shelf structure.

PREVIOUS EXTRACTION FOUND:
{previous_structure}

ISSUES IDENTIFIED:
{specific_problems}

FOCUS AREAS:
{focus_areas}

Please carefully:
- Verify the total shelf count, especially {area_of_concern}
- Double-check {specific_issue}
- Look carefully at {problematic_region}

Be precise with shelf count - this determines how products will be organized.
""",

"products_retry": """
Re-extract products from shelf {shelf_number} of {total_shelves}, focusing on areas that need correction.

PREVIOUS EXTRACTION FOUND:
{previous_products}

KNOWN ISSUES:
{identified_problems}

FOCUS AREAS FOR THIS ATTEMPT:
{focus_guidance}

VERIFICATION TASKS:
- Confirm or correct the products already identified with low confidence
- Pay special attention to {specific_areas}
- Double-check facing counts for {uncertain_products}

Build upon what worked, fix what didn't.
"""
```

### 2. Update ExtractionOrchestrator to Use Retry Templates

```python
# In extraction_orchestrator.py, modify _execute_shelf_by_shelf_extraction:

async def _execute_shelf_by_shelf_extraction(self, ...):
    # ... existing code ...
    
    for shelf_num in range(1, context.structure.shelf_count + 1):
        # Determine if this is a retry scenario
        is_retry = agent_number > 1
        
        if is_retry:
            # Check for previous attempts on this shelf
            previous_shelf_data = self._get_previous_shelf_data(
                shelf_num, context.previous_attempts
            )
            
            if previous_shelf_data and previous_shelf_data.has_low_confidence:
                # Use retry template
                shelf_prompt = prompt_templates.get_template("products_retry").format(
                    shelf_number=shelf_num,
                    total_shelves=context.structure.shelf_count,
                    previous_products=self._format_previous_products(previous_shelf_data),
                    identified_problems=self._identify_problems(previous_shelf_data),
                    focus_guidance=self._build_focus_guidance(previous_shelf_data),
                    specific_areas=self._get_low_confidence_areas(previous_shelf_data),
                    uncertain_products=self._get_uncertain_products(previous_shelf_data)
                )
            else:
                # Use standard template with cumulative context
                shelf_prompt = self._build_cumulative_shelf_prompt(
                    shelf_num, context, prompt_templates
                )
        else:
            # First attempt - use standard template
            shelf_prompt = prompt_templates.get_template("shelf_by_shelf_extraction").format(
                shelf_number=shelf_num,
                total_shelves=context.structure.shelf_count
            )
```

### 3. Add Helper Methods for Problem Identification

```python
def _identify_problems(self, previous_data):
    """Analyze previous extraction to identify specific problems"""
    problems = []
    
    # Check for low confidence products
    low_conf = [p for p in previous_data.products if p.confidence < 0.75]
    if low_conf:
        problems.append(f"Low confidence on {len(low_conf)} products")
    
    # Check for validation flags
    flagged = [p for p in previous_data.products if p.validation_flags]
    if flagged:
        problems.append(f"Validation issues on {len(flagged)} products")
    
    # Check for missing sections
    if previous_data.coverage < 0.8:
        problems.append("Possible missing products in some sections")
    
    return "\n".join(problems)

def _build_focus_guidance(self, previous_data):
    """Build specific guidance for retry attempts"""
    guidance = []
    
    # Analyze patterns in failures
    if previous_data.left_section_confidence < 0.7:
        guidance.append("LEFT SECTION: Products may be obscured by glare or shadow")
    
    if previous_data.has_promo_obstruction:
        guidance.append("Check behind promotional signage for hidden products")
    
    if previous_data.facing_uncertainty > 0.3:
        guidance.append("Facing counts need verification - look for label edges")
    
    return "\n".join(guidance)
```

### 4. Update Stage-Based Prompting

```python
# For structure stage retries
if stage == "structure" and attempt > 1:
    prompt = prompt_templates.get_template("structure_retry").format(
        previous_structure=previous_result.structure,
        specific_problems=self._analyze_structure_issues(previous_result),
        focus_areas=self._get_structure_focus_areas(comparison_feedback),
        area_of_concern="base level products" if base_uncertain else "top shelf visibility",
        specific_issue=main_issue,
        problematic_region=problem_region
    )
```

## Benefits

1. **Focused Retries**: Instead of generic prompts, retries target specific problems
2. **Efficient Token Usage**: Retry prompts only include relevant context
3. **Better Learning**: Explicitly states what worked and what needs fixing
4. **Clearer Instructions**: Agents know exactly what to improve

## Testing Strategy

1. Run extraction with intentionally difficult images
2. Compare results between current (generic) and new (retry) approaches
3. Measure:
   - Confidence improvement rate
   - Token usage efficiency
   - Time to convergence
   - Final accuracy

## Integration Timeline

1. **Phase 1**: Add retry templates to prompts.py
2. **Phase 2**: Update orchestrator to select appropriate templates
3. **Phase 3**: Implement problem analysis helpers
4. **Phase 4**: Test and refine based on results