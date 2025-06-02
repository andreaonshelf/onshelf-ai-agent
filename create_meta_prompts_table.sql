-- Create meta_prompts table for storing prompt generation templates
-- These are the prompts sent to Claude to generate extraction prompts

CREATE TABLE IF NOT EXISTS meta_prompts (
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
    success_rate DECIMAL(5,2),
    
    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    parent_id INTEGER REFERENCES meta_prompts(id)
);

-- Create indexes
CREATE INDEX idx_meta_prompts_category ON meta_prompts(category);
CREATE INDEX idx_meta_prompts_is_default ON meta_prompts(is_default);
CREATE INDEX idx_meta_prompts_is_active ON meta_prompts(is_active);

-- Add trigger for updated_at
CREATE TRIGGER update_meta_prompts_updated_at 
    BEFORE UPDATE ON meta_prompts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default meta-prompt
INSERT INTO meta_prompts (name, description, template, category, is_default) VALUES (
    'Default Extraction Prompt Generator',
    'Standard meta-prompt for generating retail shelf extraction prompts',
    'Create an optimized extraction prompt for retail shelf images.

Type: {prompt_type}
Fields to extract: {fields}
Field definitions: {field_definitions}
Base context: {base_prompt}
Special instructions: {special_instructions}

Generate:
1. An optimized prompt that will achieve >90% accuracy
2. A Pydantic model for structured output with the requested fields
3. Key improvements and reasoning

The prompt should be clear, specific, and include examples where helpful.
Use the field definitions to ensure accurate understanding of what to extract.
Format the response as JSON with keys:
- optimized_prompt: The full prompt text
- pydantic_model_code: Complete Pydantic model code
- model_class_name: Name of the Pydantic class
- reasoning: List of optimization decisions made
- key_improvements: List of key improvements
- optimization_focus: What this prompt is optimized for
- recommended_model: Which AI model to use (claude/gpt4o/gemini)',
    'extraction',
    TRUE
);

-- Add comments
COMMENT ON TABLE meta_prompts IS 'Stores meta-prompts used to generate extraction prompts';
COMMENT ON COLUMN meta_prompts.template IS 'The meta-prompt template with placeholders like {prompt_type}, {fields}, etc.';