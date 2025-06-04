-- Add columns needed for orchestrator retry prompts and meta-prompts
-- These columns will support the {IF_RETRY} blocks and context variables

BEGIN;

-- Add context column for storing prompt context variables
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'::jsonb;

-- Add variables column for storing available template variables
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS variables JSONB DEFAULT '[]'::jsonb;

-- Add retry_config column for retry-specific settings
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS retry_config JSONB DEFAULT '{}'::jsonb;

-- Add meta_prompt_id for linking to meta-prompts table
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS meta_prompt_id UUID;

-- Add extraction_config for stage-specific configurations
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS extraction_config JSONB DEFAULT '{}'::jsonb;

-- Add template column for storing raw template with {IF_RETRY} blocks
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS template TEXT;

-- Add is_template flag to distinguish between plain prompts and templates
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE;

-- Add retry_count to track how many times a prompt has been used in retries
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Add parent_template_id for linking retry prompts to their base prompts
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS parent_template_id VARCHAR(255);

-- Show the updated schema
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'prompt_templates'
ORDER BY ordinal_position;

COMMIT;