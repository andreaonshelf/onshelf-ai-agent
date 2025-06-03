# Clear Examples of Where Prompts Go

## In "Extraction Orchestrator Custom Instructions" Field:

```
=== STRUCTURE STAGE ===
Count all shelves from bottom to top. 
Identify fixture type and dimensions.

{IF_RETRY}
Previous found {shelf_count} shelves.
Double-check:
- Bottom shelf for floor-level products
- Top shelf visibility
- Price rails as shelf indicators
{/IF_RETRY}

=== PRODUCTS STAGE ===
Extract all products from shelf {shelf_number}.
Scan left to right, count facings accurately.

{IF_RETRY}
Build on previous extraction:
{high_confidence_products}

Focus on fixing:
{low_confidence_areas}
Check edges and behind promos.
{/IF_RETRY}

=== DETAILS STAGE ===
Add price, size, and color for each product.

{IF_RETRY}
Still missing: {missing_details}
Look at shelf edge labels for prices.
Check product labels for sizes.
{/IF_RETRY}
```

## In "Master Orchestrator Instructions" Field:

```
Focus on achieving 95% accuracy efficiently.
Prioritize structural accuracy first.
Use expensive models only when needed.
Stop iterations when confidence plateaus.
```

## How It Works:

1. **User enters the prompts above in UI**

2. **Extraction Orchestrator receives the full prompt**

3. **On first attempt (Agent 1)**:
   - Orchestrator removes {IF_RETRY} blocks
   - Sends clean initial prompt to LLM

4. **On retry attempts (Agent 2, 3)**:
   - Orchestrator keeps {IF_RETRY} content
   - Fills in variables like {shelf_count}
   - Sends enhanced prompt to LLM

## The Code Flow:

```
UI Input → Extraction Orchestrator → Process Prompt → LLM

Where:
- UI Input: User's prompt with {IF_RETRY} blocks
- Process Prompt: Removes/keeps retry sections based on attempt
- LLM: Receives processed prompt (GPT-4, Claude, etc.)
```

## Key Point:

The {IF_RETRY} blocks are instructions FOR the extraction LLMs (Claude/GPT doing the actual shelf analysis), NOT for the orchestrators.

The orchestrators just:
1. Decide when to retry
2. Process the prompts (remove/keep retry sections)
3. Pass them to the appropriate LLM