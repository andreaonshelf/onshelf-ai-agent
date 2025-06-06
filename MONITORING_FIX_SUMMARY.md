# Monitoring Integration Fix Summary

## Problem
The dashboard was showing "Loading monitoring data..." but no actual progress was displayed during extraction processing.

## Root Cause
The monitoring hooks were registered in the queue processing system but were not being called from within the extraction systems. The extraction pipeline was running without sending any real-time updates to the monitoring system.

## Solution Implemented

### 1. **Updated Base System**
- Added `queue_item_id` parameter to `BaseExtractionSystem.__init__()`
- Updated `ExtractionSystemFactory.get_system()` to pass `queue_item_id` to all extraction systems

### 2. **Updated Custom Consensus Visual System**
- Added `queue_item_id` parameter to constructor
- Integrated monitoring hooks in key methods:
  - `extract_with_iterations()` - Sends iteration updates
  - `_process_stage_with_visual_feedback()` - Sends stage progress and model updates

### 3. **Updated Other Extraction Systems**
- Added `queue_item_id` support to:
  - `CustomConsensusSystem` (parent class)
  - `LangGraphConsensusSystem`
  - `HybridConsensusSystem`

### 4. **Updated System Dispatcher**
- Modified to pass `queue_item_id` when creating extraction systems via the factory

## How It Works Now

1. When a queue item starts processing:
   - Queue processor registers monitoring hooks with the queue item ID
   - Creates extraction system with the queue item ID

2. During extraction:
   - Extraction system sends monitoring updates via `monitoring_hooks`:
     - Iteration progress (`update_iteration`)
     - Stage progress (`update_stage_progress`)
     - Processing details (`update_processing_detail`)

3. Monitoring updates are:
   - Stored in the monitoring hooks system
   - Broadcast via WebSocket to connected clients
   - Available via the `/api/queue/monitor/{item_id}` endpoint

4. Dashboard receives updates:
   - Via WebSocket for real-time updates
   - Falls back to polling if WebSocket fails
   - Displays current stage, model, iteration, etc.

## Testing
To test the monitoring integration:

1. Start the server: `python main.py`
2. Open the dashboard
3. Process a queue item
4. You should see real-time updates showing:
   - Current iteration
   - Stage being processed (structure/products/details)
   - Model being used
   - Progress indicators

## Files Modified
- `src/systems/base_system.py`
- `src/systems/custom_consensus_visual.py`
- `src/systems/custom_consensus.py`
- `src/systems/langgraph_system.py`
- `src/systems/hybrid_system.py`
- `src/orchestrator/system_dispatcher.py`

## Future Enhancements
- Add more granular monitoring updates (e.g., per-shelf progress)
- Include confidence scores in real-time updates
- Add visual indicators for consensus voting progress
- Include partial extraction results in monitoring data