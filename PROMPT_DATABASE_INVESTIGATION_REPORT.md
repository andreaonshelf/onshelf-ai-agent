# Prompt Database Investigation Report

## 1. Current Table Structure

The `prompt_templates` table currently has the following columns:
- prompt_id
- template_id
- prompt_type
- model_type
- prompt_version
- prompt_text
- performance_score
- usage_count
- correction_rate
- is_active
- created_from_feedback
- parent_prompt_id
- retailer_context
- category_context
- avg_token_cost
- created_at
- name
- description
- fields (JSONB)
- stage_type
- tags
- created_by
- is_system_generated
- is_public
- overall_performance_score
- overall_usage_count
- overall_avg_cost
- field_definitions (JSONB)
- is_user_created
- autonomy_level
- updated_at

## 2. Current Prompts in Database

Total prompts found: 7

All prompts have `field_name` as 'Unknown', indicating they may have been inserted without proper field mapping.

### Prompts by Type:
- **products**: Initial Product Extraction
- **structure**: Structure Extraction - Standard v2
- **position**: Product Extraction - Planogram Aware v2
- **detail**: Detail Refinement v1
- **validation**: Product Detail Enhancement

## 3. Missing Orchestrator Support

The following columns needed for orchestrator retry prompts are **MISSING**:
- ❌ context (for storing prompt context variables)
- ❌ variables (for storing available template variables)
- ❌ retry_config (for retry-specific settings)
- ❌ meta_prompt_id (for linking to meta-prompts table)
- ❌ extraction_config (for stage-specific configurations)

## 4. SQL Files for Insertion

Found multiple insertion SQL files:
1. `insert_all_prompts_complete.sql` - Most comprehensive, includes all prompts with error handling
2. `insert_planogram_prompts.sql` - Planogram-specific prompts
3. `insert_planogram_prompts_current_schema.sql` - Updated for current schema
4. `insert_prompts_final.sql` - Final version of prompts
5. `insert_prompts_without_conflict.sql` - Handles conflicts during insertion

## 5. Key Findings

### Issue 1: Field Name Mapping
All prompts in the database have `field_name` as 'Unknown', suggesting the field mapping wasn't properly set during insertion.

### Issue 2: Missing Orchestrator Columns
The table lacks columns necessary for:
- Storing retry prompt templates with {IF_RETRY} blocks
- Managing context variables for prompt processing
- Linking to meta-prompts for dynamic prompt generation

### Issue 3: No Template vs Prompt Distinction
Current schema doesn't distinguish between:
- Static prompts (ready to use)
- Template prompts (with {IF_RETRY} blocks that need processing)

## 6. Recommendations

### Immediate Actions:
1. **Add orchestrator columns** using `add_orchestrator_columns.sql`
2. **Update existing prompts** to have proper field mappings
3. **Insert retry prompt templates** with {IF_RETRY} blocks

### Schema Improvements:
1. Add `template` column for raw templates with placeholders
2. Add `is_template` flag to distinguish templates from ready prompts
3. Add `context` and `variables` columns for dynamic prompt processing
4. Add `retry_config` for retry-specific configurations

### Insertion Strategy:
1. Use `insert_all_prompts_complete.sql` as the base
2. Add retry templates for each stage (structure, products, details)
3. Ensure proper field_name mapping for all prompts

## 7. Next Steps

1. Execute `add_orchestrator_columns.sql` to add missing columns
2. Create retry prompt templates with {IF_RETRY} blocks
3. Update the orchestrator to process these templates
4. Test the complete retry flow with context variables