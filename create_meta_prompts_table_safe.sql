-- Create meta_prompts table for storing prompt generation templates
-- These are the prompts sent to Claude to generate extraction prompts

DO $$ 
BEGIN
    -- Check if table exists before creating it
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'meta_prompts'
    ) THEN
        CREATE TABLE meta_prompts (
            -- Primary key
            id SERIAL PRIMARY KEY,
            
            -- Meta-prompt identification
            name VARCHAR(255) NOT NULL,
            description TEXT,
            
            -- The actual meta-prompt template
            template TEXT NOT NULL,
            
            -- Categorization
            category VARCHAR(50) DEFAULT 'extraction',
            is_default BOOLEAN DEFAULT FALSE,
            
            -- Performance tracking
            usage_count INTEGER DEFAULT 0,
            success_rate DECIMAL(3,2),
            
            -- Versioning
            version INTEGER DEFAULT 1,
            parent_id INTEGER REFERENCES meta_prompts(id),
            
            -- Metadata
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            
            -- Additional configuration
            config JSONB,
            
            -- Unique constraint on name + version
            UNIQUE(name, version)
        );

        -- Create indexes
        CREATE INDEX idx_meta_prompts_category ON meta_prompts(category);
        CREATE INDEX idx_meta_prompts_is_default ON meta_prompts(is_default);
        CREATE INDEX idx_meta_prompts_is_active ON meta_prompts(is_active);

        -- Add comment
        COMMENT ON TABLE meta_prompts IS 'Stores meta-prompt templates used to generate extraction prompts via AI';
        
        RAISE NOTICE 'meta_prompts table created successfully';
    ELSE
        RAISE NOTICE 'meta_prompts table already exists';
    END IF;

    -- Check if we need to add the updated_at trigger
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.triggers 
        WHERE trigger_name = 'update_meta_prompts_updated_at'
    ) THEN
        -- First check if the trigger function exists
        IF EXISTS (
            SELECT 1 
            FROM pg_proc 
            WHERE proname = 'update_updated_at_column'
        ) THEN
            CREATE TRIGGER update_meta_prompts_updated_at 
                BEFORE UPDATE ON meta_prompts 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
            RAISE NOTICE 'Trigger update_meta_prompts_updated_at created';
        ELSE
            RAISE NOTICE 'Trigger function update_updated_at_column does not exist, skipping trigger creation';
        END IF;
    END IF;
END $$;

-- Insert default meta-prompt only if the table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM meta_prompts LIMIT 1) THEN
        INSERT INTO meta_prompts (name, description, template, is_default, category) VALUES
        ('default_extraction_meta_prompt', 
         'Default meta-prompt for generating extraction prompts', 
         'Create an optimized extraction prompt for retail shelf images.

Type: {prompt_type}
Fields to extract: {fields}
Base context: {base_prompt}
Special instructions: {special_instructions}

Generate:
1. An optimized prompt that will achieve >90% accuracy
2. A Pydantic model for structured output with the requested fields
3. Key improvements and reasoning

IMPORTANT: The prompt and Pydantic model will be used with the Instructor library.
The prompt should be clear, specific, and include examples where helpful.
The Pydantic model must use proper type annotations and Field descriptors.

Format the response as JSON with keys:
- optimized_prompt: The full prompt text that will be passed to the AI model
- pydantic_model_code: Complete Pydantic model code with proper imports and Field descriptors
- model_class_name: Name of the main Pydantic class (e.g., "ExtractionResult")
- reasoning: List of optimization decisions made
- key_improvements: List of key improvements
- optimization_focus: What this prompt is optimized for
- recommended_model: Which AI model to use (claude/gpt4o/gemini)',
         true,
         'extraction');
        
        RAISE NOTICE 'Default meta-prompt inserted';
    ELSE
        RAISE NOTICE 'Meta-prompts already exist, skipping default data';
    END IF;
END $$;