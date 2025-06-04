-- Verify what prompts were successfully inserted

-- Check v2 prompts in prompt_templates
SELECT 'V2 Prompts in prompt_templates:' as info;
SELECT 
    template_id,
    name,
    stage_type,
    CASE WHEN fields IS NOT NULL THEN 'Yes' ELSE 'No' END as has_fields,
    CASE WHEN length(prompt_text) > 0 THEN 'Yes' ELSE 'No' END as has_prompt,
    is_active
FROM prompt_templates
WHERE template_id LIKE '%_v2'
ORDER BY stage_type, name;

-- Count by stage type
SELECT 'Summary by stage_type:' as info;
SELECT 
    stage_type,
    COUNT(*) as count,
    COUNT(*) FILTER (WHERE fields IS NOT NULL) as with_pydantic_fields
FROM prompt_templates
WHERE template_id LIKE '%_v2'
GROUP BY stage_type
ORDER BY stage_type;

-- Check meta prompts
SELECT 'Orchestrator prompts in meta_prompts:' as info;
SELECT 
    name,
    category,
    CASE WHEN length(template) > 0 THEN 'Yes' ELSE 'No' END as has_template,
    is_default
FROM meta_prompts
WHERE category = 'orchestrator'
ORDER BY name;

-- Check if any prompts are missing fields
SELECT 'Checking for prompts missing critical data:' as info;
SELECT 
    template_id,
    name,
    CASE 
        WHEN fields IS NULL THEN 'Missing fields'
        WHEN prompt_text IS NULL OR length(prompt_text) = 0 THEN 'Missing prompt text'
        WHEN stage_type IS NULL THEN 'Missing stage_type'
        ELSE 'Complete'
    END as status
FROM prompt_templates
WHERE template_id LIKE '%_v2'
AND (fields IS NULL OR prompt_text IS NULL OR length(prompt_text) = 0 OR stage_type IS NULL);

-- Final confirmation
SELECT 'Ready for use in Extraction Config UI!' as status;