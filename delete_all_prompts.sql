-- Delete all existing prompts to start fresh with {IF_RETRY} system
-- This will remove all prompts from prompt_templates table

BEGIN;

-- First, let's see what we're about to delete
SELECT COUNT(*) as total_prompts, 
       COUNT(DISTINCT prompt_type) as unique_types,
       STRING_AGG(DISTINCT prompt_type, ', ') as prompt_types
FROM prompt_templates;

-- Delete all prompts
DELETE FROM prompt_templates;

-- Verify deletion
SELECT COUNT(*) as remaining_prompts FROM prompt_templates;

COMMIT;

-- Note: This will permanently delete all prompts. 
-- Make sure you have backups if needed!