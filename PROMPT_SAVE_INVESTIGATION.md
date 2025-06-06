# Prompt Save Investigation Summary

## Problem
Saved prompts aren't appearing in the dropdown in the dashboard.

## Root Causes Found

1. **Missing API Endpoint**: The frontend is calling `POST /api/prompts` but there was no endpoint at that exact path.
   - **Fixed**: Added a new endpoint `@router.post("")` in `prompt_management.py` that matches frontend expectations

2. **Table Schema Mismatch**: The `prompt_templates` table uses `prompt_text` (not `prompt_content`) after migration.
   - **Fixed**: Updated the save endpoint to detect and use the correct column name dynamically

3. **Missing prompt_library Table**: The `prompt_library` table referenced in some code doesn't exist in the database.
   - **Status**: The code now falls back to using `prompt_templates` table instead

4. **Column Availability**: The `prompt_templates` table has been extended with additional columns:
   - ✓ name
   - ✓ fields (and field_definitions)
   - ✓ stage_type
   - ✓ tags
   - ✓ description

## Changes Made

### 1. Added POST endpoint in `src/api/prompt_management.py`:
```python
@router.post("")
async def save_prompt_to_library(request: Dict[str, Any]):
```
This endpoint:
- Accepts the format the frontend sends
- Maps stage names to prompt_types for compatibility
- Dynamically detects whether to use `prompt_text` or `prompt_content`
- Saves to `prompt_templates` table with all required fields

### 2. Updated `get_prompts_by_stage` to:
- Extract names from template_id for user-created prompts
- Handle both `prompt_text` and `prompt_content` columns
- Include fields and tags in the response

### 3. Removed checks for non-existent tables:
- Removed attempts to query `prompt_library` table
- Removed incorrect queries to `meta_prompts` table

## Testing Instructions

1. Start the server:
   ```bash
   python main.py
   ```

2. Open the dashboard at http://localhost:8000

3. Test saving a prompt:
   - Navigate to any stage (Products, Prices, etc.)
   - Enter a prompt name and content
   - Add some field definitions
   - Click "Save Prompt to Library"

4. Check if the prompt appears:
   - The dropdown should update immediately
   - The saved prompt should be selectable
   - When selected, it should load the prompt text and fields

## Browser Console Debugging

If prompts still don't appear, check the browser console:

1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for any errors when:
   - Saving a prompt
   - Loading the dropdown
   
4. Go to Network tab
5. Look for:
   - POST request to `/api/prompts` - check status and response
   - GET request to `/api/prompts/by-stage/{stage}` - check if prompts are returned

## Database Verification

To verify prompts are being saved:

```sql
-- Check saved prompts
SELECT template_id, name, stage_type, prompt_type, is_active 
FROM prompt_templates 
WHERE template_id LIKE 'user_%' 
ORDER BY created_at DESC;

-- Check all prompts for a stage
SELECT template_id, name, stage_type, prompt_type 
FROM prompt_templates 
WHERE stage_type = 'products' OR prompt_type = 'position'
AND is_active = true;
```

## Next Steps if Issues Persist

1. Check if the migration has been applied:
   ```bash
   psql $DATABASE_URL < clean_and_migrate_prompt_templates.sql
   ```

2. Verify API is registered:
   - Check that `main.py` includes the prompt_management router
   - Verify no duplicate router registrations

3. Test with the debug scripts:
   ```bash
   python test_prompt_save.html  # Open in browser
   python test_simple_save.py    # Test API directly
   ```

## Status
The backend implementation is complete. The issue should be resolved once the server is running and the frontend can communicate with the API endpoints.