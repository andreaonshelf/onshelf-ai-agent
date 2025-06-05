# Analytics Implementation Complete

## What We've Implemented

### 1. **Iterations Table** ✅
Created comprehensive tracking for every extraction attempt:
- Stage-by-stage tracking (structure, products, details, comparison)
- Exact prompts sent (including processed {IF_RETRY} blocks)
- Visual feedback received and sent
- Orchestrator decisions and retry reasons
- Performance metrics (duration, cost, accuracy)

### 2. **Extraction Analytics Module** ✅
`src/utils/extraction_analytics.py` provides:
- Context manager for tracking iterations
- Real-time performance metrics
- Visual feedback impact analysis
- Retry pattern analysis
- Prompt performance with retry effectiveness

### 3. **Updated Analytics Endpoints** ✅
Replaced mocked data with real queries:
- `/stage-performance` - Real success rates, accuracy, duration by stage
- `/visual-feedback-impact` - Shows improvement with feedback
- `/retry-analysis` - Top retry reasons and success rates
- `/prompt-retry-performance` - How well {IF_RETRY} blocks work

### 4. **Integration Points** ✅
Added analytics tracking to:
- `ExtractionOrchestrator._execute_structure_stage()` - Tracks structure attempts
- Ready to add to products and details stages
- Tracks visual feedback between models

## How to Use the Analytics

### 1. Run Database Migration
```bash
psql $DATABASE_URL -f create_iterations_table.sql
```

### 2. Analytics Will Track:
```python
# Every extraction attempt logs:
- Which model was used
- Exact prompt sent (with retry blocks)
- Visual feedback received
- Time taken
- Cost incurred
- Success/failure
- Products found
- Accuracy achieved
```

### 3. Query Examples:

**Where are we getting stuck?**
```sql
SELECT stage, COUNT(*) as failures, AVG(duration_ms) as avg_time
FROM iterations 
WHERE success = false
GROUP BY stage
ORDER BY failures DESC;
```

**Which retry prompts work best?**
```sql
SELECT 
    retry_reason,
    COUNT(*) as uses,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate
FROM iterations
WHERE retry_reason IS NOT NULL
GROUP BY retry_reason;
```

**Visual feedback effectiveness:**
```sql
SELECT 
    stage,
    AVG(CASE WHEN visual_feedback_received IS NULL THEN accuracy_score END) as without_feedback,
    AVG(CASE WHEN visual_feedback_received IS NOT NULL THEN accuracy_score END) as with_feedback
FROM iterations
WHERE stage IN ('products', 'details')
GROUP BY stage;
```

## What You Can Now Track

### 1. **Extraction Flow**
- See each model's attempt in sequence
- Track exact prompts with {IF_RETRY} blocks
- Monitor visual feedback passed between models
- Identify bottlenecks by stage

### 2. **Retry Effectiveness**
- Which retry reasons lead to success
- How much retry prompts improve accuracy
- Which {IF_RETRY} blocks get activated most

### 3. **Visual Feedback Impact**
- Accuracy improvement with feedback
- Which types of feedback help most
- Model performance with/without feedback

### 4. **Cost vs Quality**
- Track API costs per stage
- See accuracy vs cost tradeoffs
- Optimize model selection

## Next Steps to Complete

### 1. Add Analytics to Products Stage
```python
async with analytics.track_iteration(...) as iteration_id:
    # Extract products
    # Log visual comparison
    await analytics.log_visual_comparison(iteration_id, comparison_result)
```

### 2. Add Analytics to Details Stage
Similar pattern for details extraction

### 3. Add Orchestrator Decision Logging
```python
await analytics.log_orchestrator_decision(
    iteration_id,
    decision={
        'action': 'retry',
        'current_accuracy': 0.85,
        'target_accuracy': 0.95,
        'reason': 'missing_products'
    }
)
```

### 4. Create Analytics Dashboard Views
- Real-time extraction monitoring
- Historical performance trends
- Model comparison charts
- Retry pattern visualization

## Benefits

1. **Complete Visibility** - See exactly what happens at each step
2. **Data-Driven Optimization** - Know which prompts/models work best
3. **Debug Failures** - Understand why extractions fail
4. **Track Visual Feedback** - Measure the impact of the new visual system
5. **Cost Control** - Monitor spending by stage/model/prompt

The analytics foundation is now in place. As extractions run, data will accumulate and provide insights into system performance.