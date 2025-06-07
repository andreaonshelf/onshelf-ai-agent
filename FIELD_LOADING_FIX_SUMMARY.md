# Field Loading Fix Summary

## Problem Identified

The extraction pipeline was not using the Pydantic field definitions stored in the database. The fields were being saved in `extraction_config` but the `ExtractionOrchestrator` was only loading `model_config`.

## Root Cause Analysis

1. **Queue Processor**: Correctly passes `extraction_config` (which contains field definitions) to the system dispatcher
2. **System Dispatcher**: Correctly passes the configuration to the extraction system
3. **Extraction Orchestrator**: Was only loading `model_config` from the database, ignoring the passed configuration and missing the field definitions in `extraction_config`

## Data Flow

```
UI Configuration
    ↓
extraction_config (with stages and fields)
    ↓
ai_extraction_queue table
    ↓
Queue Processor (loads extraction_config)
    ↓
System Dispatcher (passes configuration)
    ↓
Extraction System
    ↓
Extraction Orchestrator ← PROBLEM: Only loaded model_config
```

## Fix Applied

Updated `_load_model_config()` method in `ExtractionOrchestrator` to:

1. Query both `model_config` and `extraction_config` from the database
2. Prioritize `extraction_config` if it has a 'stages' key (which contains field definitions)
3. Fall back to `model_config` if no extraction_config with stages is found
4. Log which configuration source is being used

## Code Changes

In `src/orchestrator/extraction_orchestrator.py`:

```python
def _load_model_config(self):
    """Load model configuration from queue item"""
    try:
        # Get both model_config and extraction_config
        result = supabase.table("ai_extraction_queue").select("model_config, extraction_config").eq("id", self.queue_item_id).single().execute()
        
        if result.data:
            # Prioritize extraction_config if it has stages (contains field definitions)
            extraction_config = result.data.get("extraction_config", {})
            model_config = result.data.get("model_config", {})
            
            # Use extraction_config if it has stages, otherwise fall back to model_config
            if extraction_config and extraction_config.get("stages"):
                self.model_config = extraction_config
                logger.info("Using extraction_config with field definitions")
            elif model_config:
                self.model_config = model_config
                logger.info("Using model_config (no extraction_config with stages found)")
            # ... rest of the method
```

## Field Structure

The fields are stored in UI schema format in `extraction_config`:

```json
{
  "stages": {
    "structure": {
      "fields": [
        {
          "name": "structure_extraction",
          "type": "object",
          "required": true,
          "nested_fields": [
            {
              "name": "total_shelves",
              "type": "integer",
              "required": true,
              "description": "Total number of shelves"
            }
            // ... more fields
          ]
        }
      ],
      "prompt_text": "..."
    },
    "products": {
      "fields": [...],
      "prompt_text": "..."
    }
  }
}
```

## How Fields Are Used

1. Fields are loaded into `self.stage_fields` in the orchestrator
2. During extraction, the orchestrator checks for fields:
   ```python
   if hasattr(self, 'stage_fields') and 'products' in self.stage_fields:
       fields = self.stage_fields['products']
       if fields:
           # Build dynamic model from configured fields
           ProductModel = DynamicModelBuilder.build_model_from_config('product', {'fields': fields})
           output_schema = List[ProductModel]
   ```
3. The dynamic model is then used as the output schema for the extraction engine

## Testing

Verified the fix by:
1. Checking queue item 8 which has extraction_config with fields
2. Simulating the orchestrator's loading logic
3. Confirming that extraction_config is prioritized when it has stages

## Alternative Solutions Considered

1. **Pass configuration directly**: Modify `ExtractionOrchestrator.__init__` to accept a configuration parameter, avoiding database reload
2. **Unified configuration**: Merge extraction_config and model_config into a single configuration structure

## Impact

This fix ensures that:
- User-defined field schemas from the UI are properly loaded
- Dynamic Pydantic models are built according to the configured fields
- Extraction results match the expected structure defined in the UI
- The system can adapt to different field configurations without code changes