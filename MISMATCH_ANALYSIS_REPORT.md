# Exact Mismatches Between Configuration and Code

## 1. Image Path Mismatches

### Database Storage:
- **media_files** table columns: `file_path`, `preview_path` (NO `image_path` column!)
- **ai_extraction_queue** table: Has `enhanced_image_path` column
- Sample paths in ai_extraction_queue:
  - `uploads/upload-1748170816503-hzmb2p/images/1748170948489-lpv46yec-4293571-1748170749000.jpg`

### Code Expectations:
- `system_dispatcher.py` line 263: Looks for `enhanced_image_path` in `ai_extraction_queue` table ✓
- Falls back to `file_path` in `media_files` table ✓
- Downloads from Supabase storage bucket "retail-captures" using the path

### MISMATCH IDENTIFIED:
- Some code may be looking for `image_path` column in media_files (doesn't exist)
- The actual column is `file_path`

## 2. Queue Table Names

### Database Reality:
- Table is named `processing_queue` NOT `queue_processor`
- Has columns: `queue_id`, `media_id`, `process_type`, `priority`, etc.
- NO `extraction_config` column in processing_queue!

### Code Expectations:
- Various scripts expect `queue_processor` table (doesn't exist)
- Code expects `extraction_config` column (doesn't exist in processing_queue)

### MISMATCH IDENTIFIED:
- Wrong table name: `queue_processor` vs `processing_queue`
- Missing configuration storage in queue table

## 3. Configuration Structure

### UI Sends (from new_dashboard.html):
```javascript
configuration: {
    system: 'custom_consensus',
    temperature: 0.7,
    orchestrator_model: 'claude-4-opus',
    stages: {
        // stage configurations with prompts and models
    }
}
```

### Code Expects (from system_dispatcher.py):
- Line 150: Checks for `stages` in configuration ✓
- Lines 59-64: Maps stage names:
  - 'structure' → 'structure' ✓
  - 'products' → 'product' (DB has "product" not "products")
  - 'details' → 'detail' (DB has "detail" not "details")

### MISMATCH IDENTIFIED:
- Stage naming: UI uses 'products'/'details' but DB has 'product'/'detail'

## 4. Prompt Loading

### Database Reality:
- `prompt_templates` table has prompt_types: 
  - ['comparison', 'configuration', 'detail', 'orchestrator', 'planogram', 'product', 'structure', 'validation']
- Note: It's 'product' not 'products', 'detail' not 'details'

### Code Expectations:
- system_dispatcher.py correctly maps these in `stage_to_prompt_type`
- But UI might be sending wrong keys

## 5. Prompt Loading Structure Mismatch

### UI Sends:
The UI configuration structure is unclear but likely sends:
```javascript
configuration: {
    stages: {
        structure: { /* stage config */ },
        products: { /* stage config */ },
        // etc.
    }
}
```

### Code Expects (system_dispatcher.py lines 146-194):
1. First tries: `configuration.stages[stage_id].prompt_text`
2. Falls back to: `configuration.prompts[stage_id]` (where value can be "auto" or actual prompt text)
3. Falls back to: `configuration.stage_prompts[stage_id]`

### Extraction System Expects:
- `custom_consensus_visual.py` line 109: Looks for `configuration.stage_prompts`
- Falls back to `self.stage_prompts` (set by system dispatcher)

### MISMATCH IDENTIFIED:
- UI sends prompts in `stages` object but code expects `prompt_text` field within each stage
- The extraction system expects `stage_prompts` but system dispatcher sets it as `self.extraction_system.stage_prompts`

## 6. Critical Path Issues

### Image Loading Flow:
1. UI triggers extraction with queue item ID
2. system_dispatcher tries to get image from:
   - First: `ai_extraction_queue.enhanced_image_path`
   - Fallback: `media_files.file_path` (filtered by file_type='image')
3. Downloads from Supabase storage bucket "retail-captures"

### Configuration Flow:
1. UI builds configuration with `stages` object
2. Passes to queue_processing.py endpoint
3. system_dispatcher receives configuration
4. Extracts prompts from stages using mapped names

## 7. Field Configuration Missing

### From Logs:
- "Configuration keys: ['system', 'max_budget', 'temperature', 'stage_models', 'orchestrators']"
- "Loaded 0 custom prompts from configuration"
- "No field configuration found for structure, using basic fallback schema"
- "No field configuration found for products, using basic fallback schema"
- "No field configuration found for details, using basic fallback schema"

### CRITICAL MISMATCH:
- UI is NOT sending `stages` with prompts/fields in the configuration!
- UI only sends: system, max_budget, temperature, stage_models, orchestrators
- Missing: stages, prompts, field_definitions

## Summary of Required Fixes:

1. **Image Path**: Ensure code looks for `file_path` not `image_path` in media_files
2. **Queue Table**: Update references from `queue_processor` to correct table name
3. **Stage Names**: Ensure UI uses 'product' not 'products', 'detail' not 'details'
4. **Configuration Storage**: Queue items need proper configuration storage mechanism
5. **Prompt Type Mapping**: Verify UI sends correct prompt_type values matching DB
6. **CRITICAL: UI Configuration**: The UI is NOT sending the `stages` configuration with prompts and field definitions! This is why extraction falls back to basic schemas.

## Root Cause Analysis:

The extraction is failing because:
1. The UI sends a configuration object but it's missing the `stages` key
2. Without `stages`, the system cannot load custom prompts from the configuration
3. Without custom prompts, it tries to load from database but may not find them
4. Without field definitions, it falls back to "basic fallback schema"
5. This causes extraction to fail or produce incorrect results

The UI needs to build and send a configuration like:
```javascript
{
    system: 'custom_consensus',
    max_budget: 2.0,
    temperature: 0.7,
    stage_models: { /* models per stage */ },
    orchestrators: { /* orchestrator config */ },
    stages: {
        structure: {
            prompt_text: "...",
            fields: { /* field definitions */ }
        },
        product: {  // Note: 'product' not 'products'
            prompt_text: "...",
            fields: { /* field definitions */ }
        },
        detail: {   // Note: 'detail' not 'details'
            prompt_text: "...",
            fields: { /* field definitions */ }
        }
    }
}
```