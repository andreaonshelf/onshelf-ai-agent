
        -- Add model_config column to ai_extraction_queue table if it doesn't exist
        ALTER TABLE ai_extraction_queue
        ADD COLUMN IF NOT EXISTS model_config JSONB DEFAULT '{}'::jsonb;

        -- Add comment to explain the column
        COMMENT ON COLUMN ai_extraction_queue.model_config IS 'Model configuration including temperature, orchestrator model/prompt, and stage-specific model selections';
        