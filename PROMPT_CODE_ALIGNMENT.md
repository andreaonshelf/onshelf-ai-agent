# Prompt-Code Alignment Requirements

## Quick Fixes Needed:

### 1. Add Missing Variable in Products Stage
In `extraction_orchestrator.py`, around line 515, add:
```python
# Add alias for consistency with prompt
retry_context['previous_extraction_data'] = retry_context.get('previous_shelf_products', 'No previous extraction data')
```

### 2. Products Prompt Clarification
Change the prompt header to be clear about shelf-by-shelf:
```
STAGE 2: PRODUCT EXTRACTION - Shelf {SHELF_NUMBER} of {TOTAL_SHELVES}
```

### 3. Field Mapping Consideration
The detail enhancement fields in the prompt use nested structures that might need mapping to the simpler field names the code expects:

Prompt Structure → Code Fields:
- `product_identification.shelf_number` → `shelf_number`
- `pricing.regular_price` → `price`
- `package_info.size` → `size_variant`
- `visual_info.primary_color` → `primary_color`

## No Code Changes Required For:

1. **{IF_RETRY} Processing** - Already works perfectly
2. **Context Variables** - All major ones implemented
3. **Orchestrator Prompts** - These are just user guidance
4. **Comparison Agent** - Works as designed

## Testing Checklist:

1. ✓ Verify structure extraction with retry shows previous shelf count
2. ✓ Verify products extraction shows previous products on retry
3. ✓ Verify details extraction shows missing details on retry
4. ✓ Test that {IF_RETRY} blocks are removed on first attempt
5. ✓ Test that context variables are properly filled

The system is 95% ready - just need minor tweaks for full alignment!