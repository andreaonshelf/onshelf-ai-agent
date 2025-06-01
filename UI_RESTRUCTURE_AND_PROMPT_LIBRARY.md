# UI Restructure and Prompt Library Implementation

## Summary of Changes

### 1. UI Restructuring - Separation of Concerns

**Problem**: "Save Stage" button was saving pipeline-wide settings (orchestrator, comparison) along with stage settings.

**Solution**: 
- Moved Temperature, Orchestrator, and Comparison settings OUT of the stage configuration section
- Created a new "Pipeline Configuration" card that contains all pipeline-wide settings
- "Save Stage" now only saves stage-specific data (prompt, fields, models)
- Clear visual separation between stage and pipeline configurations

**New Structure**:
```
├── Stage Configuration Card
│   ├── Stage tabs
│   ├── Prompt & Fields
│   ├── Model selection for this stage
│   └── [Save Stage] button
│
├── Pipeline Configuration Card (NEW)
│   ├── Temperature slider
│   ├── Orchestrator settings
│   └── Comparison settings
│
└── [Save Full Configuration] button
```

### 2. Prompt Library Implementation

**Features Added**:
- Save prompts with field definitions to a reusable library
- Load prompts from library for any stage
- Track usage count for each prompt
- Search and filter prompts by stage type

**UI Elements**:
- 📾 Save to Library button (in prompt editor)
- 📚 Load from Library button (in prompt editor)
- Modal for browsing saved prompts
- Dialog for naming and describing prompts when saving

**API Endpoints Created**:
- `POST /api/prompt-library/save` - Save a prompt template
- `GET /api/prompt-library/list/{stage_type}` - List prompts for a stage
- `GET /api/prompt-library/get/{prompt_id}` - Get specific prompt
- `POST /api/prompt-library/update/{prompt_id}` - Update prompt
- `DELETE /api/prompt-library/delete/{prompt_id}` - Delete prompt
- `GET /api/prompt-library/search` - Search prompts

### 3. Database Schema

Created `prompt_templates` table:
```sql
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    fields JSONB NOT NULL,
    stage_type VARCHAR(50) NOT NULL,
    tags TEXT[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by UUID,
    is_default BOOLEAN,
    usage_count INTEGER
);
```

### 4. Backend Integration

**Files Created**:
- `src/api/prompt_library.py` - Complete prompt library API
- `create_prompt_templates_table.sql` - Database migration

**Files Modified**:
- `main.py` - Added prompt library router
- `new_dashboard.html` - UI restructuring and prompt library UI
- `src/orchestrator/extraction_orchestrator.py` - Uses custom prompts from config
- `src/orchestrator/master_orchestrator.py` - Passes comparison config
- `src/comparison/image_comparison_agent.py` - Configurable comparison
- `src/api/queue_management.py` - Stores complete configuration

## Benefits

1. **Clear Separation**: Users understand what "Save Stage" vs "Save Configuration" does
2. **Prompt Reusability**: Build a library of tested prompts over time
3. **Granular Control**: Save just prompts+fields without model selection
4. **Better Organization**: Pipeline settings visually separated from stage settings
5. **Configuration Works**: Saved prompts and fields are actually used during extraction

## Next Steps

1. Run the SQL migration to create the prompt_templates table
2. Test the prompt library functionality
3. Consider adding prompt versioning
4. Add import/export functionality for sharing prompts