-- Comprehensive migration to update prompt_templates table to support Pydantic field schemas
-- This migration adds essential columns for storing field definitions with prompts

BEGIN;

-- Step 1: Add the fields column for Pydantic schemas (JSONB for flexibility)
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS fields JSONB DEFAULT '[]'::jsonb;

-- Step 2: Add stage_type column for categorizing prompts
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS stage_type VARCHAR(50);

-- Step 3: Add name and description columns if they don't exist
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS name VARCHAR(255);

ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Step 4: Add tags for better organization
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- Step 5: Add updated_at timestamp
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Step 6: Rename prompt_content to prompt_text for consistency
-- Check if column exists before renaming
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'prompt_templates' 
               AND column_name = 'prompt_content'
               AND NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'prompt_templates' 
                              AND column_name = 'prompt_text')) THEN
        ALTER TABLE prompt_templates RENAME COLUMN prompt_content TO prompt_text;
    END IF;
END $$;

-- Step 7: Update existing records to have proper stage_type based on prompt_type
UPDATE prompt_templates 
SET stage_type = CASE 
    WHEN prompt_type = 'structure' THEN 'structure'
    WHEN prompt_type = 'position' THEN 'products'
    WHEN prompt_type = 'quantity' THEN 'products'
    WHEN prompt_type = 'detail' THEN 'details'
    WHEN prompt_type = 'validation' THEN 'validation'
    ELSE prompt_type
END
WHERE stage_type IS NULL;

-- Step 8: Set default names for existing prompts
UPDATE prompt_templates 
SET name = CONCAT(
    CASE 
        WHEN prompt_type = 'structure' THEN 'Structure Extraction'
        WHEN prompt_type = 'position' THEN 'Product Position'
        WHEN prompt_type = 'quantity' THEN 'Product Quantity'
        WHEN prompt_type = 'detail' THEN 'Detail Enhancement'
        WHEN prompt_type = 'validation' THEN 'Validation Check'
        ELSE prompt_type
    END,
    ' - ',
    model_type,
    ' v',
    prompt_version
)
WHERE name IS NULL;

-- Step 9: Add description for existing prompts
UPDATE prompt_templates 
SET description = CONCAT(
    'Auto-migrated from legacy schema. Original type: ',
    prompt_type,
    ', Model: ',
    model_type
)
WHERE description IS NULL;

-- Step 10: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompt_templates_stage_type 
ON prompt_templates(stage_type);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_tags 
ON prompt_templates USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_fields 
ON prompt_templates USING GIN(fields);

-- Step 11: Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_prompt_templates_updated_at ON prompt_templates;

CREATE TRIGGER update_prompt_templates_updated_at 
BEFORE UPDATE ON prompt_templates 
FOR EACH ROW 
EXECUTE FUNCTION update_updated_at_column();

-- Step 12: Add constraint to ensure name is unique within stage_type
-- First, make names unique by appending template_id where needed
WITH duplicates AS (
    SELECT name, stage_type, COUNT(*) as count
    FROM prompt_templates
    WHERE name IS NOT NULL AND stage_type IS NOT NULL
    GROUP BY name, stage_type
    HAVING COUNT(*) > 1
)
UPDATE prompt_templates p
SET name = p.name || ' (' || p.template_id || ')'
FROM duplicates d
WHERE p.name = d.name 
AND p.stage_type = d.stage_type;

-- Now add the constraint
ALTER TABLE prompt_templates 
DROP CONSTRAINT IF EXISTS prompt_templates_name_stage_type_unique;

ALTER TABLE prompt_templates 
ADD CONSTRAINT prompt_templates_name_stage_type_unique 
UNIQUE(name, stage_type);

-- Step 13: Add comments for documentation
COMMENT ON COLUMN prompt_templates.fields IS 'JSONB array of field definitions for Pydantic schema generation';
COMMENT ON COLUMN prompt_templates.stage_type IS 'Stage of extraction: structure, products, details, validation, retry_structure, retry_products, retry_details';
COMMENT ON COLUMN prompt_templates.tags IS 'Tags for categorizing and searching prompts';
COMMENT ON COLUMN prompt_templates.prompt_text IS 'The actual prompt text with optional placeholders for context variables';

-- Verify the migration
DO $$
DECLARE
    missing_columns TEXT[];
    col TEXT;
BEGIN
    -- Check for essential columns
    missing_columns := ARRAY[]::TEXT[];
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' AND column_name = 'fields') THEN
        missing_columns := array_append(missing_columns, 'fields');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' AND column_name = 'stage_type') THEN
        missing_columns := array_append(missing_columns, 'stage_type');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'prompt_templates' AND column_name = 'prompt_text') THEN
        missing_columns := array_append(missing_columns, 'prompt_text');
    END IF;
    
    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION 'Migration failed. Missing columns: %', array_to_string(missing_columns, ', ');
    ELSE
        RAISE NOTICE 'Migration completed successfully. All essential columns are present.';
    END IF;
END $$;

COMMIT;

-- Display the final schema
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'prompt_templates'
ORDER BY 
    ordinal_position;