# Implementation Requirements for Adaptive Prompts

## Current Reality
The orchestrators currently:
- Take prompts from configuration as-is
- Append basic context like "Previous analysis found X shelves"
- Don't make any intelligent decisions about which prompt to use

## Required Changes

### 1. Update ExtractionOrchestrator

```python
# In extraction_orchestrator.py, add to __init__:
from ..extraction.adaptive_prompts import AdaptivePromptBuilder
self.prompt_builder = AdaptivePromptBuilder()

# Modify _execute_stage_structure:
async def _execute_stage_structure(self, ...):
    # Get base prompt
    base_prompt = self.stage_prompts.get('structure', 
                                         self.prompt_templates.get_template('structure_analysis'))
    
    # Build context
    context = {
        'attempt_number': len(previous_attempts) + 1,
        'overall_confidence': previous_attempts[-1].confidence if previous_attempts else 0
    }
    
    if previous_attempts:
        context['previous_extraction'] = previous_attempts[-1]
    
    # Use adaptive prompt builder
    prompt = self.prompt_builder.build_adaptive_prompt(
        unified_prompt=base_prompt,
        context=context,
        attempt_number=context['attempt_number']
    )
    
    # Execute with adaptive prompt...
```

### 2. Add the AdaptivePromptBuilder class
The one I created earlier needs to be actually added to the codebase.

### 3. Update Master Orchestrator Instructions

The Master Orchestrator would need to understand this system:

```python
# In master_orchestrator.py configuration
"master": {
    "prompt": """
    Guide extraction with understanding that prompts have two sections:
    - Initial extraction (for first attempts)
    - Retry extraction (for attempts 2+ when confidence is 60-80%)
    
    When confidence is very low (<60%), instruct fresh start.
    When confidence is high (>80%), focus on minor refinements only.
    """
}
```

## Simpler Alternative: Manual Approach

If you don't want to implement the automatic switching, users could manually structure their prompts:

```
For structure extraction, analyze the shelf.

{IF_RETRY}
Previous found {shelf_count} shelves. Focus on:
- Verifying bottom shelf products
- Checking if top shelf is partially visible
{/IF_RETRY}
```

Then update orchestrator to replace `{IF_RETRY}...{/IF_RETRY}` blocks based on attempt number:

```python
# Simple implementation
def process_prompt(prompt, attempt_number):
    if attempt_number == 1:
        # Remove retry blocks
        return re.sub(r'\{IF_RETRY\}.*?\{/IF_RETRY\}', '', prompt, flags=re.DOTALL)
    else:
        # Remove the markers but keep content
        prompt = prompt.replace('{IF_RETRY}', '')
        prompt = prompt.replace('{/IF_RETRY}', '')
        return prompt
```

## Recommendation

1. **Start with the simple {IF_RETRY} approach** - requires minimal code changes
2. **Test if it actually improves results**
3. **Only implement full adaptive system if proven valuable**

The research shows adaptive systems work, but they need to be actually implemented, not just designed!