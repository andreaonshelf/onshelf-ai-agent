# Where {IF_RETRY} Blocks Actually Go - Corrected

## Current UI Structure:

1. **Extraction Orchestrator Custom Instructions**
   - General instructions for the orchestrator itself
   - NOT where stage prompts go

2. **Individual Stage Configurations** (Structure, Products, Details)
   - Each stage has its own prompt field
   - These prompts go directly to the LLMs
   - THIS is where {IF_RETRY} blocks should go

## Correct Implementation:

### In the Structure Stage Prompt Field:
```
Analyze the shelf structure and count all shelves.

{IF_RETRY}
Previous extraction found {shelf_count} shelves.
Double-check:
- Bottom shelf for floor products
- Top shelf visibility
{/IF_RETRY}
```

### In the Products Stage Prompt Field:
```
Extract all products from shelf {shelf_number}.

{IF_RETRY}
Previous extraction confidence was low.
Focus on:
- Products behind promotional materials
- Edge products that may be cut off
Keep these confirmed products:
{high_confidence_products}
{/IF_RETRY}
```

### In the Details Stage Prompt Field:
```
Extract price, size, and color for each product.

{IF_RETRY}
Still missing these details:
{missing_details}
Check shelf labels and product packaging.
{/IF_RETRY}
```

## How It Works:

```
┌─────────────────────────┐
│  Stage Configuration UI  │
│ ┌─────────────────────┐ │
│ │ Structure Prompt:   │ │◄── User writes {IF_RETRY} HERE
│ │ [................]  │ │
│ └─────────────────────┘ │
│ ┌─────────────────────┐ │
│ │ Products Prompt:    │ │◄── User writes {IF_RETRY} HERE
│ │ [................]  │ │
│ └─────────────────────┘ │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Extraction Orchestrator │
│  - Gets stage prompt    │
│  - Processes {IF_RETRY} │
│  - Adds context vars    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  LLM (GPT-4, Claude)    │
│  - Receives processed   │
│    stage prompt         │
│  - Extracts data        │
└─────────────────────────┘
```

## Code Implementation Needed:

In `extraction_orchestrator.py`, update where stage prompts are used:

```python
# For structure stage (line ~752)
prompt = self.stage_prompts.get('structure', self.prompt_templates.get_template('structure_analysis'))
# Add processing here
prompt = self.process_retry_blocks(prompt, attempt_number, context)

# For products stage (line ~432)
shelf_prompt_template = self.stage_prompts['products']
# Add processing here
shelf_prompt = self.process_retry_blocks(shelf_prompt_template, agent_number, shelf_context)

# For details stage (line ~823)
prompt = self.stage_prompts.get('details', self.prompt_templates.get_template('details_extraction'))
# Add processing here
prompt = self.process_retry_blocks(prompt, attempt_number, context)
```

## Key Point:
The {IF_RETRY} blocks go in the individual stage prompt fields in the UI, NOT in the orchestrator instructions field.