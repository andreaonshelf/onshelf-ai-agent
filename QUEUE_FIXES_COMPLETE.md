# Queue Management Fixes - COMPLETE

## What I've Done

### 1. Fixed Dynamic Model Loading (CRITICAL FIX)
All extraction stages (structure, products, details) were using hardcoded schemas instead of your configured fields. Now they properly:
- Check for configured fields in `stage_fields[stage_name]`
- Build dynamic models using `DynamicModelBuilder.build_model_from_config()`
- Use the dynamic models for extraction instead of hardcoded defaults

### 2. Added Reset All Items Button
- Added a "Reset All Items" button in the dashboard queue controls
- Creates API endpoint `/queue/reset-all` to reset failed/completed items to pending
- Allows you to retry all items that may have failed with the old configuration

### 3. Identified Queue Insertion Issue
The approved media files aren't getting into the queue because:
- You approve media using `update_media_approval()` which sets `approval_status='approved'` on media_files
- BUT the queue table uses `upload_id` as the primary reference, not `media_id`
- The trigger needs to watch media_files changes and create queue entries with the upload_id

## How to Fix the Queue Insertion

### Option 1: Run the Existing Trigger Fix
```bash
# This SQL file already exists and should fix the trigger
psql $DATABASE_URL < fix_approval_queue_trigger.sql
```

### Option 2: Manually Add Approved Items
Run the Python script to add all approved media to the queue:
```bash
python fix_queue_insertion_for_approved_media.py
```

### Option 3: Use the New API Endpoint
```bash
curl -X POST http://localhost:8000/queue/add-approved-media
```

## Next Steps

1. **Apply the trigger fix** to ensure future approvals automatically create queue entries
2. **Use the Reset All Items button** to reset any failed items
3. **Run an extraction** - it should now use your configured fields!
4. **Check the logs** for messages like:
   - "Building dynamic model for structure stage with X fields"
   - "Building dynamic model for products stage with X fields"
   - "Building dynamic model for details stage with X fields"

## What This Means
Your extractions will now:
- Use YOUR custom prompts (this was already working)
- Use YOUR custom field definitions (THIS IS NOW FIXED)
- Extract exactly the fields you've configured in the UI
- No more hardcoded schemas!

The system should finally work as intended - using both your prompts AND your field configurations for all stages.