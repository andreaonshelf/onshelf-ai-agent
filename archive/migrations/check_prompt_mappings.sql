-- Check what prompt_type and stage_type values we have for v2 prompts
SELECT 
    template_id,
    name,
    prompt_type,
    stage_type,
    is_active
FROM prompt_templates
WHERE template_id LIKE '%_v2'
ORDER BY stage_type, name;

-- Check if the query logic is correct
SELECT 'Testing products stage query:' as info;
SELECT 
    template_id,
    name,
    prompt_type,
    stage_type
FROM prompt_templates
WHERE prompt_type = 'position' 
AND is_active = true;

-- What we should be querying instead
SELECT 'Should query by stage_type instead:' as info;
SELECT 
    template_id,
    name,
    prompt_type,
    stage_type
FROM prompt_templates
WHERE stage_type = 'products' 
AND is_active = true;