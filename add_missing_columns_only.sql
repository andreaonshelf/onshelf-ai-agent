-- Add only the missing columns to prompt_templates table
-- This avoids errors if columns already exist

-- First, drop the trigger temporarily to avoid errors
DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;

-- Add each column individually with IF NOT EXISTS
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS field_definitions JSONB DEFAULT '[]'::jsonb;
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS is_user_created BOOLEAN DEFAULT false;
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS autonomy_level INTEGER DEFAULT 0;
ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Recreate the trigger
CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Update any NULL values with defaults
UPDATE prompt_templates 
SET 
    name = COALESCE(name, template_id),
    description = COALESCE(description, 'System-generated prompt template'),
    field_definitions = COALESCE(field_definitions, '[]'::jsonb),
    is_user_created = COALESCE(is_user_created, false),
    tags = COALESCE(tags, ARRAY[prompt_type, model_type])
WHERE name IS NULL OR field_definitions IS NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_is_user_created ON prompt_templates(is_user_created);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_tags ON prompt_templates USING GIN(tags);

-- Show final structure to confirm
\d prompt_templates