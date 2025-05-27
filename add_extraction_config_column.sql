-- Migration to add extraction_config column to ai_extraction_queue table
-- This column stores the complete extraction configuration including system, models, prompts, and reasoning

-- Check if column exists before adding it
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'ai_extraction_queue' 
        AND column_name = 'extraction_config'
    ) THEN
        ALTER TABLE ai_extraction_queue 
        ADD COLUMN extraction_config JSONB;
        
        -- Add comment to describe the column
        COMMENT ON COLUMN ai_extraction_queue.extraction_config IS 
        'Stores the complete extraction configuration including system selection, model assignments, prompt selections, and reasoning for each extraction stage';
        
        -- Create an index for better query performance on extraction_config
        CREATE INDEX idx_ai_extraction_queue_extraction_config 
        ON ai_extraction_queue USING GIN (extraction_config);
        
        RAISE NOTICE 'extraction_config column added successfully';
    ELSE
        RAISE NOTICE 'extraction_config column already exists';
    END IF;
END $$;

-- Migrate existing data from enhanced_config or prompt_overrides if they exist
UPDATE ai_extraction_queue
SET extraction_config = 
    CASE 
        WHEN enhanced_config IS NOT NULL THEN enhanced_config
        WHEN prompt_overrides IS NOT NULL THEN 
            jsonb_build_object(
                'system', current_extraction_system,
                'prompts', prompt_overrides,
                'models', jsonb_build_object(
                    'structure', 'claude',
                    'products', 'gpt4o',
                    'details', 'gemini'
                )
            )
        ELSE NULL
    END
WHERE extraction_config IS NULL 
  AND (enhanced_config IS NOT NULL OR prompt_overrides IS NOT NULL);