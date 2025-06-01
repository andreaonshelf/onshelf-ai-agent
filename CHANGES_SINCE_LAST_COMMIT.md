# Changes Since Last Commit & Current Issues

## Last Commit
- **Commit Hash**: ff4704f
- **Message**: "fix: Major UI improvements and database enhancements"

## Changes Made Since Last Commit

### 1. UI Separation of Concerns (What You Requested)
- **Goal**: Separate "Save Stage" functionality to only save stage-specific data (prompts, fields, models)
- **Implementation**: 
  - Moved orchestrator settings, temperature, and comparison settings out of stage configuration
  - Created a new "Pipeline Configuration" card for these settings
  - Stage configuration now only contains: prompt, field definitions, and model selection

### 2. Prompt Library Integration (Within Dashboard)
- **Goal**: Add ability to save/load prompts with field definitions to a library
- **Implementation**:
  - Added "Save to Library" and "Load from Library" buttons in stage configuration
  - Created prompt library modal for browsing saved prompts
  - Integrated within the main dashboard (not a separate page)

### 3. Database Schema Evolution
- **Original Plan**: Create separate `prompt_library` table
- **Pivot**: After discovering existing `prompt_templates` table, decided to enhance it instead
- **Unified Approach**: Single table for both system-generated and user-created prompts with performance tracking

### 4. Self-Improving System Architecture
- **Added Components**:
  - Performance tracking after each extraction
  - Multi-armed bandit configuration selection
  - Automatic prompt evolution engine
  - Graduated autonomy levels (Observe → Suggest → Test → Auto-optimize → Full autonomy)

### 5. New API Endpoints Created
- `/api/prompts/save` - Save user prompts to library
- `/api/prompts/list/{prompt_type}` - List prompts by type
- `/api/prompts/get/{prompt_id}` - Get specific prompt
- `/api/prompts/performance/{prompt_id}` - Track performance
- `/api/prompts/best/{prompt_type}/{model_type}` - Get best performing prompt
- `/api/prompts/evolve/{prompt_id}` - Evolve underperforming prompts

### 6. New Python Modules Created
- `src/api/prompt_management.py` - Enhanced prompt management API
- `src/extraction/performance_tracker.py` - Track extraction performance
- `src/extraction/configuration_selector.py` - Multi-armed bandit selection
- `src/extraction/prompt_evolution.py` - AI-powered prompt evolution

### 7. SQL Files Created
- `alter_prompt_templates_table.sql` - Add missing columns to existing table
- `insert_default_prompts_fixed.sql` - Insert default prompts
- Multiple table creation scripts for the self-improving system

## Current Problem

### The Issue
The React dashboard (`new_dashboard.html`) that contains all these new features won't load due to a **Babel transpilation error**.

### Root Cause
1. The dashboard uses JSX syntax with inline Babel transformation
2. JSX comments `{/* comment */}` are causing parsing errors
3. Even after removing comments, conditional rendering syntax like `{configPreview && Object.keys(configPreview.stages).length > 0 && (` is failing to parse
4. The error suggests a syntax issue at line ~2882 where this conditional appears

### Why This Happened
1. The original dashboard was working fine
2. When adding new features (prompt library, pipeline config), the JSX became more complex
3. The in-browser Babel transformer is having issues with the more complex JSX structure
4. The conditional rendering might be in an invalid position or missing proper wrapping

### What We Tried
1. Removed all JSX comments - didn't solve it
2. Created simplified versions - you rejected (rightfully so)
3. Tried to fix JSX structure - Babel still fails

## Recommended Solution

1. **Revert to last commit**: `git checkout ff4704f`
2. **Re-implement changes carefully**:
   - Add UI separation one step at a time
   - Test after each change
   - Avoid complex JSX structures that might confuse Babel
   - Consider pre-compiling JSX instead of in-browser transformation
3. **Alternative approach**:
   - Use a build step to compile JSX to JavaScript
   - Or use React without JSX (React.createElement)
   - Or fix the specific syntax issue in the current file

## Key Features to Preserve After Revert

1. **UI Changes**:
   - Stage Configuration: Only prompts, fields, models
   - Pipeline Configuration: Temperature, orchestrator, comparison (separate card)
   - Prompt Library: Save/Load buttons integrated in main UI

2. **API Structure**:
   - Enhanced prompt_templates table (not separate prompt_library)
   - Performance tracking endpoints
   - Evolution and selection endpoints

3. **System Architecture**:
   - Unified self-improving system
   - Multi-armed bandit selection
   - Graduated autonomy levels

The main challenge is fixing the React dashboard while preserving all the architectural improvements we've made.