# Database Schema Report

## Executive Summary

Based on my investigation of the database schema, I've found the following key information about the tables and their structures:

## 1. prompt_templates Table

### Current Column Structure:
- `prompt_id` - Primary key
- `template_id` - Unique identifier for the template
- `prompt_type` - Type of prompt (structure, position, etc.)
- `model_type` - Model type (universal, gpt4o, etc.)
- `prompt_version` - Version number
- `prompt_text` - The actual prompt text
- `performance_score` - Performance metric
- `usage_count` - Usage counter
- `correction_rate` - Correction rate metric
- `is_active` - Active flag
- `created_from_feedback` - Feedback origin flag
- `parent_prompt_id` - Reference to parent prompt
- `retailer_context` - Retailer-specific context
- `category_context` - Category-specific context
- `avg_token_cost` - Average token cost
- `created_at` - Creation timestamp
- `name` - Human-readable name
- `description` - Description of the prompt
- **`fields`** - JSONB field for Pydantic schema (EXISTS)
- `stage_type` - Stage type identifier
- `tags` - Array of tags
- `created_by` - Creator identifier
- `is_system_generated` - System generation flag
- `is_public` - Public visibility flag
- `overall_performance_score` - Overall performance metric
- `overall_usage_count` - Overall usage counter
- `overall_avg_cost` - Overall average cost
- `field_definitions` - Field definitions (EXISTS but different from `fields`)
- `is_user_created` - User creation flag
- `autonomy_level` - Autonomy level setting
- `updated_at` - Update timestamp

### Key Findings:
1. **The column for Pydantic schema is named `fields`**, not `field_schema` or `instructor_fields`
2. There is also a `field_definitions` column which appears to be different from `fields`
3. All SQL insert files are using the `fields` column correctly

## 2. meta_prompts Table

### Current Column Structure:
- `id` - Primary key
- `name` - Prompt name
- `description` - Description
- `template` - Template text
- `category` - Category classification
- `is_default` - Default flag
- `usage_count` - Usage counter
- `success_rate` - Success rate metric
- `version` - Version number
- `parent_id` - Parent reference
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp
- `created_by` - Creator identifier
- `is_active` - Active flag
- `config` - Configuration settings

### Key Finding:
- The meta_prompts table exists and is properly structured

## 3. field_definitions Table

### Current Column Structure:
- `id` - Primary key
- `field_name` - Field name
- `display_name` - Display name
- `definition` - Field definition
- `examples` - Examples
- `data_type` - Data type
- `is_required` - Required flag
- `default_value` - Default value
- `category` - Category
- `usage_count` - Usage counter
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp
- `is_active` - Active flag
- `validation_rules` - Validation rules
- `metadata` - Additional metadata
- `sort_order` - Sort order
- `parent_field` - Parent field reference

### Key Finding:
- This table exists but does NOT have an `instructor_fields` column
- This appears to be a different table than what some SQL scripts expect

## 4. Schema Mismatches Found

### In SQL Insert Files:
All the SQL insert files (`insert_planogram_prompts_current_schema.sql`, `insert_all_prompts_complete.sql`, `insert_prompts_without_conflict.sql`) are correctly using:
- `fields` column for the Pydantic schema (JSONB format)
- Standard columns that exist in the database

### Potential Issues:
1. Some scripts may be looking for `field_schema` which doesn't exist (should use `fields`)
2. Some scripts may be looking for `instructor_fields` which doesn't exist in any table
3. The `field_definitions` column in `prompt_templates` table might cause confusion with the separate `field_definitions` table

## 5. Recommendations

1. **Use `fields` column** in `prompt_templates` table for storing Pydantic schemas
2. **Avoid using** `field_schema` or `instructor_fields` as these columns don't exist
3. **Be careful** not to confuse the `field_definitions` column in `prompt_templates` with the separate `field_definitions` table
4. **All insert statements** should use the `fields` column for Pydantic schema data

## 6. Sample Data Format

Based on the SQL files, the `fields` column should contain JSONB data in this format:

```json
[
    {
        "name": "field_name",
        "type": "object",
        "description": "Field description",
        "required": true,
        "nested_fields": [
            {
                "name": "nested_field",
                "type": "string",
                "description": "Nested field description",
                "required": true
            }
        ]
    }
]
```

This format is consistent across all the insert SQL files examined.