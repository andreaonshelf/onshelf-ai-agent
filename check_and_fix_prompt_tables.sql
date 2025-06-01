-- Check existing prompt_templates structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'prompt_templates'
ORDER BY ordinal_position;

-- Since prompt_templates already exists with a different structure,
-- we should use the prompt_library table instead
-- Drop the table if it exists (be careful with this in production!)
DROP TABLE IF EXISTS prompt_library CASCADE;

-- Create the new prompt_library table
CREATE TABLE prompt_library (
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
    
    -- Link to existing prompt_templates if needed
    prompt_template_id UUID REFERENCES prompt_templates(prompt_id),
    
    -- Unique constraint on name per stage
    CONSTRAINT prompt_library_name_stage_unique UNIQUE(name, stage_type)
);

-- Create indexes
CREATE INDEX idx_prompt_library_stage_type ON prompt_library(stage_type);
CREATE INDEX idx_prompt_library_tags ON prompt_library USING GIN(tags);
CREATE INDEX idx_prompt_library_usage_count ON prompt_library(usage_count DESC);
CREATE INDEX idx_prompt_library_created_at ON prompt_library(created_at DESC);

-- Add RLS policies
ALTER TABLE prompt_library ENABLE ROW LEVEL SECURITY;

-- Policy: Everyone can read prompt library entries
CREATE POLICY "Prompt library viewable by everyone" ON prompt_library
    FOR SELECT USING (true);

-- Policy: Authenticated users can create prompt library entries  
CREATE POLICY "Authenticated users can create prompt library entries" ON prompt_library
    FOR INSERT WITH CHECK (true);  -- Changed to true for testing, use auth.uid() IS NOT NULL in production

-- Policy: Users can update their own prompt library entries
CREATE POLICY "Users can update own prompt library entries" ON prompt_library
    FOR UPDATE USING (true);  -- Changed to true for testing, use auth.uid() = created_by in production

-- Policy: Users can delete their own prompt library entries
CREATE POLICY "Users can delete own prompt library entries" ON prompt_library
    FOR DELETE USING (true);  -- Changed to true for testing, use auth.uid() = created_by in production

-- Create or replace the update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_prompt_library_updated_at ON prompt_library;
CREATE TRIGGER update_prompt_library_updated_at 
    BEFORE UPDATE ON prompt_library 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add default prompts
INSERT INTO prompt_library (name, description, prompt_text, fields, stage_type, is_default, tags) VALUES
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
),
(
    'Price Focus Extraction',
    'Specialized prompt for accurate price extraction',
    'Focus on extracting price information from this retail shelf image.

For each visible price tag or label:
1. Match the price to the correct product
2. Extract the exact price value
3. Identify if it''s a regular or promotional price
4. Note any multi-buy offers (e.g., "2 for £3")
5. Extract price per unit if shown (e.g., "£2.50/kg")

Be extremely careful to match prices to the correct products above or below the price tag.',
    '[
        {"name": "product_name", "type": "string", "description": "Product the price belongs to", "required": true},
        {"name": "regular_price", "type": "number", "description": "Regular price", "required": true},
        {"name": "promo_price", "type": "number", "description": "Promotional price if different", "required": false},
        {"name": "multi_buy_offer", "type": "string", "description": "Multi-buy offer text", "required": false},
        {"name": "price_per_unit", "type": "string", "description": "Price per unit if shown", "required": false},
        {"name": "currency", "type": "string", "description": "Currency symbol", "required": false, "default": "£"}
    ]'::jsonb,
    'prices',
    true,
    ARRAY['default', 'pricing', 'standard']
),
(
    'Shelf Structure Analysis',
    'Analyze shelf structure and layout',
    'Analyze the shelf structure in this retail image:

1. Count the number of shelf levels (from bottom to top)
2. Identify any shelf dividers or sections
3. Estimate shelf dimensions if possible
4. Note any special fixtures (end caps, promotional displays)
5. Identify shelf edge labels or price rails

Be precise with shelf counting - each physical shelf level should be counted.',
    '[
        {"name": "shelf_count", "type": "integer", "description": "Total number of shelf levels", "required": true},
        {"name": "shelf_width_estimate", "type": "string", "description": "Estimated width in meters", "required": false},
        {"name": "has_dividers", "type": "boolean", "description": "Whether shelves have dividers", "required": false},
        {"name": "special_fixtures", "type": "array", "description": "List of special fixtures", "required": false}
    ]'::jsonb,
    'structure',
    true,
    ARRAY['default', 'structure', 'layout']
);

-- Add comment
COMMENT ON TABLE prompt_library IS 'User-created prompt templates with field definitions for different extraction stages';

-- Show the final structure
SELECT 'Prompt library table created successfully!' as status;

-- Verify the structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'prompt_library'
ORDER BY ordinal_position;