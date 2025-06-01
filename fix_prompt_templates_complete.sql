-- Complete fix for prompt_templates table
-- This script checks what exists and only adds what's missing

-- First, let's see what columns already exist
DO $$
BEGIN
    -- Add name column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'name') THEN
        ALTER TABLE prompt_templates ADD COLUMN name VARCHAR(255);
    END IF;

    -- Add description column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'description') THEN
        ALTER TABLE prompt_templates ADD COLUMN description TEXT;
    END IF;

    -- Add field_definitions column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'field_definitions') THEN
        ALTER TABLE prompt_templates ADD COLUMN field_definitions JSONB DEFAULT '[]'::jsonb;
    END IF;

    -- Add is_user_created column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'is_user_created') THEN
        ALTER TABLE prompt_templates ADD COLUMN is_user_created BOOLEAN DEFAULT false;
    END IF;

    -- Add tags column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'tags') THEN
        ALTER TABLE prompt_templates ADD COLUMN tags TEXT[] DEFAULT '{}';
    END IF;

    -- Add autonomy_level column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'autonomy_level') THEN
        ALTER TABLE prompt_templates ADD COLUMN autonomy_level INTEGER DEFAULT 0;
    END IF;

    -- Add updated_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' 
                   AND column_name = 'updated_at') THEN
        ALTER TABLE prompt_templates ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Create or replace the update function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if the column exists
    IF TG_TABLE_NAME = 'prompt_templates' THEN
        NEW.updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop and recreate the trigger
DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;

CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Update existing rows with defaults
UPDATE prompt_templates 
SET 
    name = COALESCE(name, template_id),
    description = COALESCE(description, 'System-generated prompt template'),
    field_definitions = COALESCE(field_definitions, '[]'::jsonb),
    is_user_created = COALESCE(is_user_created, false),
    tags = COALESCE(tags, ARRAY[prompt_type, model_type])
WHERE name IS NULL OR field_definitions IS NULL;

-- Create indexes only if they don't exist
CREATE INDEX IF NOT EXISTS idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_is_user_created ON prompt_templates(is_user_created);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_tags ON prompt_templates USING GIN(tags);

-- Show the final structure
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'prompt_templates'
ORDER BY ordinal_position;