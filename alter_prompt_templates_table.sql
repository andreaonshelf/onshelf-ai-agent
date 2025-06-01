-- Add missing columns to prompt_templates table for unified prompt management

-- Add name column
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS name VARCHAR(255);

-- Add description column
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add field_definitions column for storing field schemas
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS field_definitions JSONB DEFAULT '[]'::jsonb;

-- Add is_user_created flag
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT false;

-- Add tags for categorization
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Add autonomy_level for graduated autonomy
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS autonomy_level INTEGER DEFAULT 0;

-- Update existing rows to have default values
UPDATE prompt_templates 
SET 
    name = COALESCE(name, template_id),
    description = COALESCE(description, 'System-generated prompt template'),
    field_definitions = COALESCE(field_definitions, '[]'::jsonb),
    is_user_created = COALESCE(is_user_created, false),
    tags = COALESCE(tags, ARRAY[prompt_type, model_type])
WHERE name IS NULL OR field_definitions IS NULL;

-- Add indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_is_user_created ON prompt_templates(is_user_created);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_tags ON prompt_templates USING GIN(tags);

-- Add comment for the enhanced table
COMMENT ON TABLE prompt_templates IS 'Unified prompt templates table supporting both system and user-created prompts with performance tracking';