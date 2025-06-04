-- Fix duplicate names and add unique constraint
-- Since the migration is already applied, we just need to fix duplicates

BEGIN;

-- Step 1: Show current duplicates
SELECT 'Current duplicates:' as info;
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
SELECT 'After fix - checking for remaining duplicates:' as info;
SELECT 
    name, 
    stage_type, 
    COUNT(*) as count
FROM prompt_templates
WHERE name IS NOT NULL
GROUP BY name, stage_type
HAVING COUNT(*) > 1;

-- Step 4: Now add the unique constraint
ALTER TABLE prompt_templates 
DROP CONSTRAINT IF EXISTS prompt_templates_name_stage_type_unique;

ALTER TABLE prompt_templates 
ADD CONSTRAINT prompt_templates_name_stage_type_unique 
UNIQUE(name, stage_type);

-- Step 5: Show what we fixed
SELECT 'Fixed prompts (showing those with version numbers):' as info;
SELECT 
    template_id,
    name,
    stage_type,
    prompt_type
FROM prompt_templates
WHERE name LIKE '% (v%)'
ORDER BY name;

COMMIT;

SELECT 'Duplicates fixed and constraint added successfully!' as status;