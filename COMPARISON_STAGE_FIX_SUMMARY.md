# Comparison Stage Loading Fix

## Issue Summary
The comparison stage was not loading in the `/api/extraction/current-config` endpoint, which prevented users from seeing comparison/visual prompts in the dashboard configuration.

## Root Cause Analysis

### Database Investigation
Using Supabase queries, I found that:

1. **Active comparison prompts exist in the database:**
   - "Comparison - Standard" (type: comparison, stage: comparison)
   - "Visual v1" (type: comparison, stage: comparison)

2. **Prompt type mapping issue:**
   - The code was looking for `'visual'` type prompts to map to the `'comparison'` stage
   - But the database actually contains `'comparison'` type prompts, not `'visual'`

3. **Additional mapping issues:**
   - The code didn't handle stage_type keys properly (e.g., `'products'`, `'details'`)

## Fix Applied

### File: `/src/api/extraction_config.py` (Line 248-255)

**Before:**
```python
type_to_stage = {
    'structure': 'structure',
    'product': 'products', 
    'detail': 'details',
    'visual': 'comparison'  # ❌ Wrong: no 'visual' type prompts exist
}
```

**After:**
```python
type_to_stage = {
    'structure': 'structure',
    'product': 'products', 
    'products': 'products',  # ✅ Added: products stage_type maps to products stage
    'detail': 'details',
    'details': 'details',    # ✅ Added: details stage_type maps to details stage  
    'comparison': 'comparison'  # ✅ Fixed: use 'comparison' instead of 'visual'
}
```

## Verification

### Database Query Results
```sql
SELECT name, prompt_type, stage_type, is_active 
FROM prompt_templates 
WHERE prompt_type = 'comparison' AND is_active = true;
```

Results:
- Comparison - Standard (type: comparison, stage: comparison)
- Visual v1 (type: comparison, stage: comparison)

### API Endpoint Test
The `/api/extraction/current-config` endpoint now returns:
```json
{
  "system": "custom_consensus",
  "temperature": 0.1,
  "max_budget": 2.0,
  "orchestrator_model": "claude-4-opus",
  "stages": {
    "structure": {...},
    "products": {...},
    "details": {...},
    "comparison": {
      "prompt_text": "Compare the original shelf photo with the generated planogram visualization..."
    }
  }
}
```

## Impact
- ✅ Comparison stage now loads properly in the dashboard
- ✅ Users can see and configure visual comparison prompts
- ✅ All 4 extraction stages (structure, products, details, comparison) are available
- ✅ Maintains backward compatibility with existing configurations

## Files Modified
- `/src/api/extraction_config.py` - Fixed type mapping in `get_current_extraction_config()` function

## Testing
The fix has been verified to:
1. Load comparison prompts from the database correctly
2. Map them to the proper 'comparison' stage
3. Return complete configuration with all 4 stages via API
4. Maintain compatibility with existing prompt structures