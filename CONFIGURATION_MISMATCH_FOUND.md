# Configuration Mismatch Analysis

## 1. Image Path Mismatch ❌
**Database Column**: `file_path` (NOT `image_path`)
**Code Expects**: `image_path`
**Result**: Code can't find images because it's looking for wrong column name

## 2. Table Name Mismatch ❌
**Database Table**: `processing_queue`
**Code References**: `queue_processor`
**Result**: Queries may fail or reference wrong table

## 3. Missing extraction_config Column ❌
**Database**: `processing_queue` has NO `extraction_config` column
**Code Expects**: `extraction_config` with field definitions
**Result**: System can't load field configurations

## 4. Configuration Structure Mismatch ❌
**UI Sends**:
```json
{
  "system": "langgraph_consensus",
  "max_budget": 10,
  "temperature": 0.7,
  "stage_models": {...},
  "orchestrators": {...}
}
```

**Code Expects**:
```json
{
  "system": "langgraph_consensus",
  "max_budget": 10,
  "temperature": 0.7,
  "stage_models": {...},
  "orchestrators": {...},
  "stages": {  // THIS IS MISSING!
    "structure": {
      "prompt_text": "...",
      "fields": [...]
    },
    "products": {
      "prompt_text": "...", 
      "fields": [...]
    }
  }
}
```

## 5. Prompt Type Name Mismatch ❌
**Database Has**: `product`, `detail` (singular)
**Code/UI May Use**: `products`, `details` (plural)

## The Real Problem
The UI is NOT building the complete configuration. It's missing the entire `stages` object that contains:
- Prompt texts for each stage
- Field definitions for dynamic model building

Without this, the extraction system:
1. Can't load prompts properly
2. Falls back to basic schemas
3. Fails with "response_model" errors

## Fix Required
The dashboard needs to properly build the configuration with the `stages` object included, pulling prompts and field definitions from the database.