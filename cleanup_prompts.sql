-- Remove all prompts except the v2 ones we just added

-- First, let's see what we're about to delete
SELECT 'Prompts to be deleted:' as info;
SELECT 
    template_id,
    name,
    prompt_type,
    stage_type,
    created_at
FROM prompt_templates
WHERE template_id NOT LIKE '%_v2'
ORDER BY created_at;

-- Count how many we're deleting
SELECT COUNT(*) as prompts_to_delete
FROM prompt_templates
WHERE template_id NOT LIKE '%_v2';

-- Delete all non-v2 prompts
DELETE FROM prompt_templates
WHERE template_id NOT LIKE '%_v2';

-- Verify only v2 prompts remain
SELECT 'Remaining prompts after cleanup:' as info;
SELECT 
    template_id,
    name,
    stage_type,
    is_active
FROM prompt_templates
ORDER BY stage_type, name;

-- Final count
SELECT COUNT(*) as remaining_prompts
FROM prompt_templates;