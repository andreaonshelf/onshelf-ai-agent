# Analytics Tracking Implementation Complete

## What Was Implemented

### 1. **Standalone SQL Migration File** ✅
Created `create_iterations_table_standalone.sql` with:
- Complete iterations table with all tracking fields
- Supporting tables (prompt_execution_log, visual_feedback_log, orchestrator_decisions)
- Materialized view for performance (extraction_analytics_summary)
- Helper functions for analysis
- Proper indexes and permissions

**To Execute**: Run the entire SQL file in Supabase SQL Editor

### 2. **Analytics Integration in Extraction Orchestrator** ✅
Modified `src/orchestrator/extraction_orchestrator.py`:
- Added optional `extraction_run_id` parameter to constructor
- Initialize analytics tracking when run_id is provided
- Track each shelf extraction attempt including:
  - Exact prompts sent (after retry block processing)
  - Model used and attempt number
  - Retry context and visual feedback
  - Duration and cost metrics
  - Success/failure status

### 3. **Diagnostics Tab in Dashboard** ✅
Added new "Diagnostics" tab to the dashboard at port 8130:
- Lists extraction runs with summary metrics
- Shows detailed timeline view of each extraction
- Displays exact prompts sent to models
- Shows which retry blocks were activated
- Tracks visual feedback received
- Visualizes the flow of extraction attempts

### 4. **API Endpoints Created** ✅
Created `/api/diagnostics/*` endpoints:
- `/extraction-runs` - Get list of runs with metrics
- `/extraction-run/{run_id}` - Get detailed iteration data
- `/prompt-execution-history` - Analyze prompt patterns
- `/visual-feedback-analysis/{run_id}` - Feedback impact analysis

## How It Works

### During Extraction:
```python
# When creating orchestrator, pass extraction_run_id
orchestrator = ExtractionOrchestrator(
    config=config,
    queue_item_id=queue_item_id,
    extraction_run_id=run_id  # This enables analytics
)

# Analytics automatically tracks:
- Each model attempt
- Exact prompts (including {IF_RETRY} processing)
- Visual feedback between models
- Performance metrics
```

### In the Dashboard:
1. Navigate to the **Diagnostics** tab
2. Select time range (7 or 30 days)
3. Click on any extraction run to see:
   - Complete timeline of attempts
   - Exact prompts sent to each model
   - Visual feedback impact
   - Retry patterns and effectiveness

## Key Features

### 1. **Prompt Tracking**
- Stores the EXACT prompt sent to models
- Shows which {IF_RETRY} blocks were activated
- Tracks how prompts evolve with visual feedback

### 2. **Visual Feedback Analysis**
- Shows when feedback was received
- Tracks impact on accuracy
- Identifies common issues

### 3. **Performance Metrics**
- Duration of each attempt
- API costs per model
- Accuracy scores
- Product counts

### 4. **Retry Analysis**
- Why retries happened
- Which retry strategies worked
- Success rates by retry reason

## Next Steps

1. **Execute the SQL migration** in Supabase
2. **Update queue processing** to pass extraction_run_id to orchestrator
3. **Start collecting data** as extractions run
4. **Use diagnostics** to optimize prompts and model selection

## Benefits

- **Complete Visibility**: See exactly what happens at each step
- **Prompt Optimization**: Know which prompts and retry blocks work best
- **Cost Control**: Track spending by model and stage
- **Debug Failures**: Understand why extractions fail
- **Visual Feedback Impact**: Measure the effectiveness of the visual feedback system

The analytics infrastructure is now in place. As extractions run with the new tracking, the Diagnostics tab will provide invaluable insights into system performance.