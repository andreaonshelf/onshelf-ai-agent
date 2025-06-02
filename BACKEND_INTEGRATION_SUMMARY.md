# Backend Integration Implementation Summary

## Overview
The OnShelf dashboard needs proper backend integration to save prompts, configurations, and manage the extraction pipeline. Currently, the UI changes are only saved in localStorage and not persisted to the database.

## Required Features

### 1. Individual Stage Prompt Saving
- **Endpoint**: `POST /api/prompts/save` ✅ (exists)
- **Functionality**: Save prompts for each stage (structure, products, details, validation)
- **UI Changes**: Add "Save [Stage]" button for each active stage tab
- **Database**: Saves to `meta_prompts` table

### 2. Configuration Management
- **Endpoints needed**:
  - `GET /api/prompts/configurations` ❌ (missing)
  - `GET /api/prompts/configurations/{id}` ❌ (missing)
  - `POST /api/prompts/configurations` ❌ (missing)
  - `PUT /api/prompts/configurations/{id}` ❌ (missing)
  - `DELETE /api/prompts/configurations/{id}` ❌ (missing)
- **Database**: Needs new `extraction_configurations` table
- **Functionality**: Save complete extraction pipeline configurations

### 3. Configuration Preview
- **UI Component**: Modal showing full configuration details
- **Features**:
  - Summary (name, system, budget, stages configured)
  - Stage details (prompts, fields, models)
  - Export to JSON
  - Test configuration

### 4. Visual Feedback
- **Save indicators**: Green checkmark when stage is saved
- **Notifications**: Toast notifications for success/error
- **Stage status**: Visual indication of saved/unsaved states

## Implementation Steps

### Step 1: Add Missing Database Table
```sql
CREATE TABLE extraction_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    avg_performance_score FLOAT,
    usage_count INTEGER DEFAULT 0
);
```

### Step 2: Add Configuration Endpoints
Add the endpoints from `add_configuration_endpoints.py` to `src/api/prompt_management.py`

### Step 3: Update UI Components
1. Replace `handleSaveConfiguration` function
2. Add `handleSaveStagePrompt` function
3. Update stage tabs with save buttons
4. Add configuration preview modal
5. Add notification system

### Step 4: Integrate Features
1. Add `stageConfigs` state to track saved configurations
2. Update stage switching to load saved configurations
3. Implement configuration loading from database
4. Add export/import functionality

## Key UI Changes

### Stage Tabs Enhancement
```javascript
// Before: Simple tabs
<div className="stage-tab">Structure</div>

// After: Tabs with save status and button
<div className="stage-tab saved">
    Structure ✓
    <button className="save-stage-btn">Save Structure</button>
</div>
```

### Configuration Saving Flow
1. User configures each stage
2. Clicks "Save [Stage]" to save individual prompts
3. All stages are collected when "Save Configuration" is clicked
4. User names the configuration
5. Configuration is saved to database
6. Preview modal shows the complete configuration

## API Integration Points

### Save Individual Stage
```javascript
POST /api/prompts/save
{
    "prompt_type": "structure",
    "model_type": "claude",
    "prompt_content": "...",
    "prompt_version": "1.0"
}
```

### Save Complete Configuration
```javascript
POST /api/prompts/save-default-config
{
    "configuration": {
        "name": "High Accuracy Config",
        "system": "custom_consensus",
        "max_budget": 2.0,
        "stages": {
            "structure": {...},
            "products": {...},
            "details": {...},
            "validation": {...}
        }
    },
    "name": "High Accuracy Config",
    "description": "Optimized for accuracy"
}
```

## Benefits

1. **Persistence**: Configurations are saved to database
2. **Reusability**: Load previous configurations
3. **Collaboration**: Share configurations via export
4. **Version Control**: Track changes to prompts
5. **Performance Tracking**: Monitor configuration effectiveness

## Testing Checklist

- [ ] Individual stage prompts save correctly
- [ ] Save indicators appear after saving
- [ ] Full configuration saves all stages
- [ ] Configuration preview shows all details
- [ ] Export generates valid JSON
- [ ] Configurations can be loaded from database
- [ ] Notifications appear for all actions
- [ ] Error handling works correctly

## Next Steps

1. Implement the missing endpoints
2. Create the database table
3. Apply the UI patches from `dashboard_integration_patch.md`
4. Test all features end-to-end
5. Add configuration versioning
6. Implement A/B testing capabilities