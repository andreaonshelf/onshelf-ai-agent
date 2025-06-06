# Dynamic Model Building Fix

## Issue Analysis

The log message "No dynamic model built for stage structure, using generic schema" indicated that the DynamicModelBuilder was not receiving proper field definitions, causing extractions to fall back to generic schemas instead of user-defined structured outputs.

## Root Cause Discovery

Through systematic investigation, I traced the issue through the complete extraction pipeline:

### 1. ✅ Dynamic Model Builder Works Correctly
- The `DynamicModelBuilder.build_model_from_config()` function works perfectly
- Successfully converts field definitions to Pydantic models
- The logic in `custom_consensus_visual.py` is sound

### 2. ✅ Configuration Storage/Retrieval Works
- Configuration API properly saves and loads `stages` with `fields`
- Database storage preserves field definitions correctly
- The `stages` structure includes all necessary field metadata

### 3. ❌ Queue Items Missing Configurations
**ROOT CAUSE IDENTIFIED:** Queue items created from image uploads do not include any `extraction_config`.

When images are uploaded via `/api/images/upload`, the queue item contains:
```python
queue_data = {
    "upload_id": upload_id,
    "ready_media_id": ready_media_id,
    "enhanced_image_path": storage_path,
    "status": "pending",
    "metadata": {...}
    # NO extraction_config!
}
```

### 4. Impact on Processing
When queue processor runs:
```python
extraction_config = queue_item.get('extraction_config') or {}  # Empty dict!
```

This results in:
- No configuration passed to system dispatcher
- No `stages` with field definitions
- `stage_config = {}` in custom_consensus_visual.py
- Condition `stage_config and 'fields' in stage_config` fails
- Falls back to generic schemas

## Solution Implemented

Added default configuration loading to `processor_config_integration.py`:

```python
# If still no configuration, load a default configuration with proper field definitions
if not extraction_config:
    logger.info(
        f"No configuration found for queue item {queue_id}, loading default configuration",
        component="queue_processor",
        queue_id=queue_id
    )
    extraction_config = await _load_default_configuration()
```

### Default Configuration Includes:

1. **Structure Stage Fields:**
   - `shelf_count` (integer) - Number of shelves
   - `fixture_type` (literal) - Type of fixture with allowed values
   - `sections` (integer, optional) - Number of sections

2. **Products Stage Fields:**
   - `products` (list) with nested fields:
     - `brand` (string) - Product brand
     - `name` (string) - Product name  
     - `shelf_number` (integer) - Shelf position
     - `position` (integer) - Horizontal position
     - `facings` (integer) - Number of side-by-side items

3. **Details Stage Fields:**
   - `product_details` (list) with nested fields:
     - `product_name` (string) - Reference name
     - `price` (float, optional) - Price if visible
     - `size_variant` (string, optional) - Size information
     - `promotional_tags` (list, optional) - Promotional elements

## Testing Results

✅ **Configuration Flow Test Passed:**
- Default configuration properly structured
- All stages include `fields` definitions
- Condition checks pass: `stage_config and 'fields' in stage_config` = True
- Dynamic models will be built successfully

## Files Modified

1. **`src/queue_system/processor_config_integration.py`**
   - Added default configuration loading logic
   - Added comprehensive field definitions for all stages
   - Ensures queue items without explicit configs get proper field structures

2. **`src/systems/custom_consensus_visual.py`** 
   - Removed debug logging (temporary debugging code)

3. **`src/orchestrator/system_dispatcher.py`**
   - Removed debug logging (temporary debugging code)

## Expected Outcome

After this fix:
- ✅ Queue items without configurations will load default field definitions
- ✅ Dynamic models will be built for all stages 
- ✅ Structured extraction outputs will be generated
- ✅ No more "using generic schema" warnings
- ✅ Better extraction accuracy and consistency

## Alternative Solutions Considered

1. **Attach configurations during upload** - Would require UI changes and user configuration before upload
2. **Load user-specific configurations** - Would require user management and configuration selection
3. **Load from saved configurations** - Would require configuration management in queue processing

The implemented solution (default configuration) provides immediate benefit for all queue processing while maintaining compatibility with future configuration management features.