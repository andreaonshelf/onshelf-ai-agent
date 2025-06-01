-- Create prompt_templates table for saving prompts with field definitions
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    fields JSONB NOT NULL DEFAULT '[]',
    stage_type VARCHAR(50) NOT NULL, -- products, prices, promotions, etc.
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES auth.users(id),
    is_default BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    
    -- Indexes for performance
    CONSTRAINT prompt_templates_name_unique UNIQUE(name, stage_type)
);

-- Create indexes
CREATE INDEX idx_prompt_templates_stage_type ON prompt_templates(stage_type);
CREATE INDEX idx_prompt_templates_tags ON prompt_templates USING GIN(tags);
CREATE INDEX idx_prompt_templates_usage_count ON prompt_templates(usage_count DESC);
CREATE INDEX idx_prompt_templates_created_at ON prompt_templates(created_at DESC);

-- Add RLS policies
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;

-- Policy: Everyone can read prompt templates
CREATE POLICY "Prompt templates are viewable by everyone" ON prompt_templates
    FOR SELECT USING (true);

-- Policy: Authenticated users can create prompt templates
CREATE POLICY "Authenticated users can create prompt templates" ON prompt_templates
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Policy: Users can update their own prompt templates
CREATE POLICY "Users can update own prompt templates" ON prompt_templates
    FOR UPDATE USING (auth.uid() = created_by);

-- Policy: Users can delete their own prompt templates
CREATE POLICY "Users can delete own prompt templates" ON prompt_templates
    FOR DELETE USING (auth.uid() = created_by);

-- Add some default prompt templates
INSERT INTO prompt_templates (name, description, prompt_text, fields, stage_type, is_default, tags) VALUES
(
    'Standard Product Extraction',
    'Default prompt for extracting product information from shelf images',
    'Extract all visible products from this retail shelf image. For each product, identify:
- Brand name
- Product name/description
- Size/volume if visible
- Price if visible
- Number of facings (units visible side by side)
- Shelf position (counting from left)
- Any promotional tags

Focus on accuracy and only extract clearly visible products.',
    '[
        {"name": "brand", "type": "string", "description": "Product brand name", "required": true},
        {"name": "name", "type": "string", "description": "Product name or description", "required": true},
        {"name": "size", "type": "string", "description": "Product size or volume", "required": false},
        {"name": "price", "type": "number", "description": "Product price", "required": false},
        {"name": "facing_count", "type": "integer", "description": "Number of facings", "required": true, "default": 1},
        {"name": "position", "type": "integer", "description": "Position on shelf from left", "required": true},
        {"name": "promotional", "type": "boolean", "description": "Has promotional tag", "required": false, "default": false}
    ]'::jsonb,
    'products',
    true,
    ARRAY['default', 'retail', 'standard']
),
(
    'Beverage Specialist',
    'Optimized for extracting beverage products with detailed flavor and size information',
    'You are a beverage extraction specialist. Extract all beverage products with special attention to:
- Brand and sub-brand (e.g., Coca-Cola, Coca-Cola Zero)
- Flavor variants (e.g., Original, Cherry, Vanilla)
- Package size (ml, L, oz)
- Package type (bottle, can, multipack)
- Caffeine/sugar-free indicators
- Promotional pricing

Pay special attention to subtle flavor differences and package sizes.',
    '[
        {"name": "brand", "type": "string", "description": "Main brand name", "required": true},
        {"name": "sub_brand", "type": "string", "description": "Sub-brand or variant", "required": false},
        {"name": "flavor", "type": "string", "description": "Flavor variant", "required": false},
        {"name": "size", "type": "string", "description": "Package size with units", "required": true},
        {"name": "package_type", "type": "string", "description": "bottle/can/multipack", "required": true},
        {"name": "is_diet", "type": "boolean", "description": "Diet/Zero/Sugar-free", "required": false},
        {"name": "price", "type": "number", "description": "Product price", "required": false},
        {"name": "promo_price", "type": "number", "description": "Promotional price if different", "required": false}
    ]'::jsonb,
    'products',
    false,
    ARRAY['beverage', 'drinks', 'specialized']
);