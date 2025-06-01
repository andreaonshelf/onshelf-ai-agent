-- Insert default prompts into prompt_templates table
-- Using the actual existing columns

INSERT INTO prompt_templates (
    prompt_id,
    template_id,
    name, 
    description, 
    prompt_type,
    model_type,
    prompt_version,
    prompt_content,
    field_definitions,
    is_user_created,
    is_active,
    tags,
    performance_score,
    usage_count,
    created_at
) VALUES
(
    gen_random_uuid(),
    'standard_product_extraction_v1',
    'Standard Product Extraction',
    'Default prompt for extracting product information from shelf images',
    'extraction',
    'universal',
    '1.0',
    E'Extract all visible products from this retail shelf image. For each product, identify:\n- Brand name\n- Product name/description\n- Size/volume if visible\n- Price if visible\n- Number of facings (units visible side by side)\n- Shelf position (counting from left)\n- Any promotional tags\n\nFocus on accuracy and only extract clearly visible products.',
    '[
        {"name": "brand", "type": "string", "description": "Product brand name", "required": true},
        {"name": "name", "type": "string", "description": "Product name or description", "required": true},
        {"name": "size", "type": "string", "description": "Product size or volume", "required": false},
        {"name": "price", "type": "number", "description": "Product price", "required": false},
        {"name": "facing_count", "type": "integer", "description": "Number of facings", "required": true, "default": 1},
        {"name": "position", "type": "integer", "description": "Position on shelf from left", "required": true},
        {"name": "promotional", "type": "boolean", "description": "Has promotional tag", "required": false, "default": false}
    ]'::jsonb,
    true,
    true,
    ARRAY['default', 'retail', 'standard', 'products'],
    0.85,
    0,
    NOW()
),
(
    gen_random_uuid(),
    'beverage_specialist_v1',
    'Beverage Specialist',
    'Optimized for extracting beverage products with detailed flavor and size information',
    'extraction',
    'universal',
    '1.0',
    E'You are a beverage extraction specialist. Extract all beverage products with special attention to:\n- Brand and sub-brand (e.g., Coca-Cola, Coca-Cola Zero)\n- Flavor variants (e.g., Original, Cherry, Vanilla)\n- Package size (ml, L, oz)\n- Package type (bottle, can, multipack)\n- Caffeine/sugar-free indicators\n- Promotional pricing\n\nPay special attention to subtle flavor differences and package sizes.',
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
    true,
    true,
    ARRAY['beverage', 'drinks', 'specialized', 'products'],
    0.0,
    0,
    NOW()
),
(
    gen_random_uuid(),
    'price_focus_extraction_v1',
    'Price Focus Extraction',
    'Specialized prompt for accurate price extraction',
    'extraction',
    'universal',
    '1.0',
    E'Focus on extracting price information from this retail shelf image.\n\nFor each visible price tag or label:\n1. Match the price to the correct product\n2. Extract the exact price value\n3. Identify if it''s a regular or promotional price\n4. Note any multi-buy offers (e.g., "2 for £3")\n5. Extract price per unit if shown (e.g., "£2.50/kg")\n\nBe extremely careful to match prices to the correct products above or below the price tag.',
    '[
        {"name": "product_name", "type": "string", "description": "Product the price belongs to", "required": true},
        {"name": "regular_price", "type": "number", "description": "Regular price", "required": true},
        {"name": "promo_price", "type": "number", "description": "Promotional price if different", "required": false},
        {"name": "multi_buy_offer", "type": "string", "description": "Multi-buy offer text", "required": false},
        {"name": "price_per_unit", "type": "string", "description": "Price per unit if shown", "required": false},
        {"name": "currency", "type": "string", "description": "Currency symbol", "required": false, "default": "£"}
    ]'::jsonb,
    true,
    true,
    ARRAY['default', 'pricing', 'standard', 'prices'],
    0.0,
    0,
    NOW()
),
(
    gen_random_uuid(),
    'shelf_structure_analysis_v1',
    'Shelf Structure Analysis',
    'Analyze shelf structure and layout',
    'structure',
    'universal',
    '1.0',
    E'Analyze the shelf structure in this retail image:\n\n1. Count the number of shelf levels (from bottom to top)\n2. Identify any shelf dividers or sections\n3. Estimate shelf dimensions if possible\n4. Note any special fixtures (end caps, promotional displays)\n5. Identify shelf edge labels or price rails\n\nBe precise with shelf counting - each physical shelf level should be counted.',
    '[
        {"name": "shelf_count", "type": "integer", "description": "Total number of shelf levels", "required": true},
        {"name": "shelf_width_estimate", "type": "string", "description": "Estimated width in meters", "required": false},
        {"name": "has_dividers", "type": "boolean", "description": "Whether shelves have dividers", "required": false},
        {"name": "special_fixtures", "type": "array", "description": "List of special fixtures", "required": false}
    ]'::jsonb,
    true,
    true,
    ARRAY['default', 'structure', 'layout'],
    0.0,
    0,
    NOW()
);