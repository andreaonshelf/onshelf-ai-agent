-- Comprehensive script to fix duplicates and complete migration
-- This handles the existing duplicate names before applying constraints

BEGIN;

-- Step 1: Show current duplicates
SELECT 'Current duplicates:' as step;
SELECT 
    name, 
    stage_type, 
    COUNT(*) as count,
    string_agg(template_id::text, ', ' ORDER BY created_at) as template_ids
FROM prompt_templates
WHERE name IS NOT NULL
GROUP BY name, stage_type
HAVING COUNT(*) > 1
ORDER BY count DESC, name;

-- Step 2: Fix duplicates by adding version numbers
-- This preserves the oldest one and adds (v2), (v3) etc to newer ones
WITH duplicates_ranked AS (
    SELECT 
        prompt_id,
        name,
        stage_type,
        template_id,
        ROW_NUMBER() OVER (PARTITION BY name, stage_type ORDER BY created_at, prompt_id) as rn
    FROM prompt_templates
    WHERE name IS NOT NULL
)
UPDATE prompt_templates p
SET name = d.name || ' (v' || d.rn || ')'
FROM duplicates_ranked d
WHERE p.prompt_id = d.prompt_id
AND d.rn > 1;

-- Step 3: Verify no more duplicates
SELECT 'After fix - checking for remaining duplicates:' as step;
SELECT 
    name, 
    stage_type, 
    COUNT(*) as count
FROM prompt_templates
WHERE name IS NOT NULL
GROUP BY name, stage_type
HAVING COUNT(*) > 1;

-- Step 4: Now we can safely add missing columns if they don't exist
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS fields JSONB DEFAULT '[]'::jsonb;

ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS stage_type VARCHAR(50);

ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS name VARCHAR(255);

ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS description TEXT;

ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Step 5: Rename prompt_content to prompt_text if needed
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

-- Step 6: Update stage_type for existing records
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

-- Step 7: Set names for records that don't have them
WITH numbered_prompts AS (
    SELECT 
        prompt_id,
        prompt_type,
        model_type,
        prompt_version,
        ROW_NUMBER() OVER (PARTITION BY prompt_type, model_type ORDER BY created_at, prompt_id) as rn
    FROM prompt_templates
    WHERE name IS NULL
)
UPDATE prompt_templates p
SET name = CONCAT(
    CASE 
        WHEN p.prompt_type = 'structure' THEN 'Structure Extraction'
        WHEN p.prompt_type = 'position' THEN 'Product Position'
        WHEN p.prompt_type = 'quantity' THEN 'Product Quantity'
        WHEN p.prompt_type = 'detail' THEN 'Detail Enhancement'
        WHEN p.prompt_type = 'validation' THEN 'Validation Check'
        ELSE p.prompt_type
    END,
    ' - ',
    p.model_type,
    ' v',
    p.prompt_version,
    CASE WHEN n.rn > 1 THEN ' (' || n.rn || ')' ELSE '' END
)
FROM numbered_prompts n
WHERE p.prompt_id = n.prompt_id AND p.name IS NULL;

-- Step 8: Add descriptions
UPDATE prompt_templates 
SET description = CONCAT(
    'Auto-migrated from legacy schema. Original type: ',
    prompt_type,
    ', Model: ',
    model_type
)
WHERE description IS NULL;

-- Step 9: Create indexes
CREATE INDEX IF NOT EXISTS idx_prompt_templates_stage_type 
ON prompt_templates(stage_type);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_tags 
ON prompt_templates USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_fields 
ON prompt_templates USING GIN(fields);

-- Step 10: Create or replace trigger
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

-- Step 11: Now add the unique constraint
ALTER TABLE prompt_templates 
DROP CONSTRAINT IF EXISTS prompt_templates_name_stage_type_unique;

ALTER TABLE prompt_templates 
ADD CONSTRAINT prompt_templates_name_stage_type_unique 
UNIQUE(name, stage_type);

-- Step 12: Add comments
COMMENT ON COLUMN prompt_templates.fields IS 'JSONB array of field definitions for Pydantic schema generation';
COMMENT ON COLUMN prompt_templates.stage_type IS 'Stage of extraction: structure, products, details, validation, retry_structure, retry_products, retry_details';
COMMENT ON COLUMN prompt_templates.tags IS 'Tags for categorizing and searching prompts';
COMMENT ON COLUMN prompt_templates.prompt_text IS 'The actual prompt text with optional placeholders for context variables';

-- Final verification
SELECT 'Migration complete! Final state:' as step;
SELECT 
    COUNT(*) as total_prompts,
    COUNT(DISTINCT name) as unique_names,
    COUNT(DISTINCT stage_type) as stage_types
FROM prompt_templates;

-- Show sample of migrated prompts
SELECT 'Sample of migrated prompts:' as step;
SELECT 
    template_id,
    name,
    stage_type,
    prompt_type,
    array_length(tags, 1) as tag_count,
    CASE WHEN fields IS NULL THEN 'No' ELSE 'Yes' END as has_fields
FROM prompt_templates
ORDER BY stage_type, name
LIMIT 10;

COMMIT;

-- Final schema check
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'prompt_templates'
ORDER BY ordinal_position;