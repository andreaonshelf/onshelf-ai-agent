-- Investigate and fix duplicate prompt names

-- First, let's see what duplicates exist
SELECT 
    name, 
    stage_type, 
    COUNT(*) as count,
    array_agg(template_id ORDER BY created_at) as template_ids,
    array_agg(prompt_id::text ORDER BY created_at) as prompt_ids
FROM prompt_templates
WHERE name IS NOT NULL
GROUP BY name, stage_type
HAVING COUNT(*) > 1
ORDER BY count DESC, name;

-- Let's look specifically at the problematic prompt
SELECT 
    prompt_id,
    template_id,
    name,
    prompt_type,
    stage_type,
    model_type,
    prompt_version,
    created_at
FROM prompt_templates
WHERE name = 'custom_structure_gpt4o_v2.0'
ORDER BY created_at;

-- Fix the duplicates by making names unique
BEGIN;

-- For each duplicate, append a number based on creation order
WITH duplicates_ranked AS (
    SELECT 
        prompt_id,
        name,
        stage_type,
        ROW_NUMBER() OVER (PARTITION BY name, stage_type ORDER BY created_at, prompt_id) as rn
    FROM prompt_templates
    WHERE name IS NOT NULL
)
UPDATE prompt_templates p
SET name = CASE 
    WHEN d.rn = 1 THEN p.name  -- Keep first one unchanged
    ELSE p.name || ' (copy ' || (d.rn - 1) || ')'  -- Add "copy N" to others
END
FROM duplicates_ranked d
WHERE p.prompt_id = d.prompt_id
AND d.rn > 1;  -- Only update duplicates, not the first one

-- Verify no more duplicates
SELECT 
    name, 
    stage_type, 
    COUNT(*) as count
FROM prompt_templates
WHERE name IS NOT NULL
GROUP BY name, stage_type
HAVING COUNT(*) > 1;

-- If no duplicates remain, add the constraint
ALTER TABLE prompt_templates 
DROP CONSTRAINT IF EXISTS prompt_templates_name_stage_type_unique;

ALTER TABLE prompt_templates 
ADD CONSTRAINT prompt_templates_name_stage_type_unique 
UNIQUE(name, stage_type);

COMMIT;

-- Show the fixed prompts
SELECT 
    template_id,
    name,
    stage_type,
    prompt_type,
    is_active
FROM prompt_templates
WHERE name LIKE '%custom_structure_gpt4o%'
ORDER BY name;