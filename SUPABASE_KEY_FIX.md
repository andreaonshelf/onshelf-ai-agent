# Supabase Key Environment Variable Fix

## Issue Found
The error "Failed to initialize Supabase client: supabase_key is required" was occurring because several files were trying to use `SUPABASE_KEY` instead of the correct environment variable `SUPABASE_SERVICE_KEY`.

## Root Cause
The Supabase Python client library raises this error when it receives a None or empty value for the key parameter during client initialization. This was happening because `os.getenv("SUPABASE_KEY")` was returning None since the actual environment variable is named `SUPABASE_SERVICE_KEY`.

## Files Fixed
The following files were updated to use the correct environment variable name:

1. `/src/utils/model_usage_tracker.py`
   - Line 23: Changed from `os.getenv("SUPABASE_KEY")` to `os.getenv("SUPABASE_SERVICE_KEY")`

2. `/src/api/queue_reset.py`
   - Line 19: Changed from `os.getenv("SUPABASE_KEY")` to `os.getenv("SUPABASE_SERVICE_KEY")`

3. `/src/comparison/image_comparison_agent.py`
   - Line 322: Changed from `os.getenv("SUPABASE_KEY")` to `os.getenv("SUPABASE_SERVICE_KEY")`

4. `/src/orchestrator/extraction_orchestrator.py`
   - Line 414: Changed from `os.getenv("SUPABASE_KEY")` to `os.getenv("SUPABASE_SERVICE_KEY")`

## Files Already Correct
Some files were already using the correct pattern by assigning `SUPABASE_SERVICE_KEY` to a variable named `SUPABASE_KEY`:
- `/src/api/image_analysis.py`
- `/src/api/field_definitions.py`

## Additional Files to Consider
There are several migration and utility scripts outside the main src directory that also use `SUPABASE_KEY`. These should be updated if they are actively used:
- `add_model_config_column_supabase.py`
- `fix_all_field_definitions.py`
- `reset_all_queue_items.py`
- `fix_queue_insertion_for_approved_media.py`
- `FIX_DYNAMIC_MODEL_USAGE.py`
- `run_model_usage_migration.py`
- `archive/migrations/check_extraction_config_column.py`

## Testing
After these changes, the Supabase client should initialize correctly when the `SUPABASE_SERVICE_KEY` environment variable is properly set.