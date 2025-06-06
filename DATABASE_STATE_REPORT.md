# Database State Report - Prompt Management System

## Current Database Status

### Tables Related to Prompts

1. **prompt_templates** - Main table for storing all prompts (EXISTS ✓)
   - Contains both system and user-created prompts
   - Currently has 7 default prompts installed

2. **meta_prompts** - Meta-prompts for prompt generation (EXISTS ✓)
   - Contains 3 meta-prompt templates
   - Used for generating new prompts programmatically

3. **prompt_library** - Does not exist (was likely planned but not implemented)

### Schema of prompt_templates Table

The table has the following key columns:
- `prompt_id` (UUID) - Primary key
- `template_id` (TEXT) - Required, unique identifier
- `name` (VARCHAR) - Human-readable name
- `prompt_type` (TEXT) - Type of prompt (structure, position, detail, etc.)
- `stage_type` (VARCHAR) - Extraction stage (structure, products, details, etc.)
- `prompt_text` (TEXT) - The actual prompt content
- `fields` (JSON) - Field definitions as JSON string
- `model_type` (TEXT) - Which model to use (universal, gpt4o, claude, etc.)
- `is_active` (BOOLEAN) - Whether prompt is active
- `is_user_created` (BOOLEAN) - Whether created by user vs system
- `tags` (TEXT[]) - Array of tags for categorization
- `description` (TEXT) - Description of the prompt
- Performance tracking columns (performance_score, usage_count, etc.)

### Current Prompts in Database

#### By Stage:

1. **STRUCTURE** (1 prompt)
   - ✓ Structure Extraction - Standard

2. **PRODUCTS** (1 prompt)
   - ✓ Product Extraction - Standard

3. **DETAILS** (1 prompt)
   - ✓ Detail Enhancement - Standard

4. **VALIDATION** (1 prompt)
   - ✓ Validation - Standard

5. **COMPARISON** (1 prompt)
   - ✓ Comparison - Standard

6. **PLANOGRAM** (1 prompt)
   - ✓ Planogram Generation - Standard

7. **ORCHESTRATOR** (1 prompt)
   - ✓ Master Orchestrator - Main

### Key Findings

1. **No User-Created Prompts Yet**
   - All current prompts are system defaults
   - User hasn't saved any custom prompts yet

2. **API Endpoints**
   - `/api/prompts/by-stage/{stage}` - Get prompts for a specific stage
   - `/api/prompts/active` - Get all active prompts
   - `/api/prompts/save` - Save a new prompt
   - `/api/prompts/{id}` - Update/delete a specific prompt

3. **Dashboard Integration**
   - The dashboard should load prompts in the sidebar
   - Users can select, edit, and save prompts
   - Field definitions are stored as JSON in the `fields` column

### How to Access Saved Prompts

1. **Via Dashboard UI**
   - Prompts appear in the sidebar under each extraction stage
   - Click on a prompt to load it
   - Edit and save to create new versions

2. **Via API**
   ```javascript
   // Get prompts for a stage
   fetch('/api/prompts/by-stage/products')
   
   // Save a new prompt
   fetch('/api/prompts/save', {
     method: 'POST',
     body: JSON.stringify({
       name: 'My Custom Prompt',
       stage_type: 'products',
       prompt_text: '...',
       fields: [...]
     })
   })
   ```

3. **Direct Database Query**
   ```sql
   -- Get all user-created prompts
   SELECT * FROM prompt_templates 
   WHERE is_user_created = true;
   
   -- Get prompts for a specific stage
   SELECT * FROM prompt_templates 
   WHERE stage_type = 'products' 
   AND is_active = true;
   ```

### Next Steps for Users

1. **Start Creating Custom Prompts**
   - Use the dashboard to create tailored prompts
   - Save different versions for different scenarios
   - Track performance over time

2. **Organize with Tags**
   - Add tags to categorize prompts
   - Filter by tags in the UI

3. **Performance Optimization**
   - System tracks usage and performance
   - Switch between prompts based on results

## Troubleshooting

If prompts don't appear in the dashboard:
1. Check that the API server is running (`python main.py`)
2. Verify the dashboard is connecting to the correct API endpoint
3. Check browser console for any JavaScript errors
4. Ensure Supabase credentials are correctly configured

The database is now properly set up with default prompts for all extraction stages. Users can start creating and saving their own custom prompts through the dashboard interface.