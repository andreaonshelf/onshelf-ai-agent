# Debug System Selection Fixes

## Issues Identified and Fixed

### 1. Import Error - HybridSystem Class Missing
**Problem**: `ImportError: cannot import name 'HybridSystem' from 'src.systems.hybrid_system'`

**Root Cause**: The file `src/systems/hybrid_system.py` contained a class named `HybridConsensusSystem`, but the import was looking for `HybridSystem`.

**Fix Applied**:
```python
# Before (in src/api/debug_interface.py)
from ..systems.hybrid_system import HybridSystem

# After
from ..systems.hybrid_system import HybridConsensusSystem
```

### 2. Logical Error - System Selection During Extraction
**Problem**: The debug interface had a dropdown to "select" extraction systems while monitoring a live extraction, which is logically impossible.

**Root Cause**: Confusion between:
- **System Selection**: Happens BEFORE extraction starts (in queue)
- **System Monitoring**: Happens DURING extraction (in debugger)

**Fix Applied**:
1. **Removed confusing dropdown**: No more system selection during monitoring
2. **Added clear messaging**: Explains that system is chosen when extraction starts
3. **Made display read-only**: Shows which system is currently running
4. **Added warning message**: "⚠️ System selected before extraction starts"

### 3. UI/UX Improvements

**Before**:
```html
<select id="systemSelector" onchange="updateSystemWorkflow()">
    <option value="Custom Consensus">Custom Consensus</option>
    <option value="LangGraph">LangGraph</option>
    <option value="Hybrid">Hybrid</option>
</select>
```

**After**:
```html
<div style="background: #f0f9ff; padding: 6px 12px; border-radius: 6px;">
    <span>Monitoring System: </span>
    <span id="currentSystem">Custom Consensus</span>
</div>
<div style="background: #fef3c7; padding: 6px 12px; border-radius: 6px;">
    <span>⚠️ System selected before extraction starts</span>
</div>
```

## Correct System Selection Flow

### 1. Queue Tab (System Selection)
- User selects which extraction systems to use
- Multiple systems can be selected for comparison
- This happens BEFORE processing starts

### 2. Processing (System Execution)
- Selected system(s) run the extraction
- System choice is locked during processing
- Cannot be changed mid-extraction

### 3. Debug Tab (System Monitoring)
- Shows which system is currently running
- Displays workflow stages and progress
- Read-only monitoring interface

## Key Learnings

1. **System Selection ≠ System Monitoring**
   - Selection: Choose before starting
   - Monitoring: Observe while running

2. **Logical Consistency**
   - You can't change the engine while the car is driving
   - You can't change the extraction system while extraction is running

3. **Clear User Communication**
   - UI should reflect the actual system capabilities
   - Confusing options should be removed or clarified

## Technical Implementation

### JavaScript Changes
```javascript
// Before: Confusing system selection
function updateSystemWorkflow() {
    const selectedSystem = document.getElementById('systemSelector').value;
    // ... update workflow
}

// After: Clear system display
function displaySystemWorkflow(systemName) {
    // ... display read-only workflow for systemName
    console.log(`📊 Displaying workflow for ${systemName} (read-only)`);
}
```

### Debug Session Updates
```javascript
// Now properly detects and displays the actual system being used
if (data.system) {
    displaySystemWorkflow(data.system);
    addLogMessage(`Monitoring ${data.system} extraction system`, 'info');
}
```

## Result

✅ **Server starts successfully** - No more import errors
✅ **Logical consistency** - System selection happens at the right time
✅ **Clear user experience** - No confusing options during monitoring
✅ **Proper messaging** - Users understand when system selection occurs

The debug interface now correctly shows which system is running without allowing impossible mid-extraction changes. 