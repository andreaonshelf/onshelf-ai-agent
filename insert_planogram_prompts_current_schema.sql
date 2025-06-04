-- Insert OnShelf AI Extraction Prompts using current schema
-- This version uses the existing column names in your database

-- STAGE 1: STRUCTURE EXTRACTION - Standard
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    name,
    description,
    stage_type,
    fields,
    tags,
    is_active
) VALUES (
    'structure_extraction_standard_v2',
    'structure',
    'universal',
    '2.0',
    'Analyze this retail shelf image to identify the physical structure.

COUNT:
□ Number of horizontal shelves (bottom = 1, count up)
□ Each product display level = one shelf
□ Include floor level only if products are placed there

MEASURE:
□ Fixture width: _____ meters (estimate)
□ Fixture height: _____ meters (estimate)
□ Fixture type: wall_shelf | gondola | end_cap | cooler | freezer | bin | pegboard | other

IDENTIFY NON-PRODUCT ELEMENTS:
□ Security devices: grids, magnetic tags, plastic cases, bottle locks
□ Promotional materials: shelf wobblers, hanging signs, price cards, banners
□ Shelf equipment: dividers, pushers, price rails, shelf strips
□ Display accessories: hooks, clip strips, shelf talkers
□ Empty spaces: gaps between products, out-of-stock sections
□ Fixtures: end panels, header boards, base decks

Output the total shelf count and all fixture details.',
    'Structure Extraction - Standard v2',
    'Initial prompt for extracting shelf physical structure with Pydantic schema',
    'structure',
    '[
        {
            "name": "structure_extraction",
            "type": "object",
            "description": "Complete shelf structure analysis",
            "required": true,
            "nested_fields": [
                {
                    "name": "shelf_structure",
                    "type": "object",
                    "description": "Physical structure of the shelf fixture",
                    "required": true,
                    "nested_fields": [
                        {"name": "total_shelves", "type": "integer", "description": "Total number of horizontal shelves", "required": true},
                        {"name": "shelf_type", "type": "string", "description": "Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)", "required": true},
                        {"name": "width_meters", "type": "float", "description": "Estimated width of fixture in meters", "required": true},
                        {"name": "height_meters", "type": "float", "description": "Estimated height of fixture in meters", "required": true},
                        {
                            "name": "shelves",
                            "type": "list",
                            "description": "Detailed information for each shelf level",
                            "required": true,
                            "list_item_type": "object",
                            "nested_fields": [
                                {"name": "shelf_number", "type": "integer", "description": "Shelf identifier (1=bottom, counting up)", "required": true},
                                {"name": "has_price_rail", "type": "boolean", "description": "Whether shelf has price label strip/rail", "required": true},
                                {"name": "special_features", "type": "string", "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)", "required": false}
                            ]
                        },
                        {
                            "name": "non_product_elements",
                            "type": "object",
                            "description": "Items on shelves that are not products",
                            "required": true,
                            "nested_fields": [
                                {
                                    "name": "security_devices",
                                    "type": "list",
                                    "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "type", "type": "string", "description": "Type of security device"},
                                        {"name": "location", "type": "string", "description": "Where on shelf it''s located"}
                                    ]
                                },
                                {
                                    "name": "promotional_materials",
                                    "type": "list",
                                    "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "type", "type": "string", "description": "Type of promotional material"},
                                        {"name": "location", "type": "string", "description": "Where positioned"},
                                        {"name": "text_visible", "type": "string", "description": "Any readable promotional text"}
                                    ]
                                },
                                {
                                    "name": "shelf_equipment",
                                    "type": "list",
                                    "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "type", "type": "string", "description": "Type of equipment"},
                                        {"name": "location", "type": "string", "description": "Where installed"}
                                    ]
                                },
                                {
                                    "name": "empty_spaces",
                                    "type": "list",
                                    "description": "Significant gaps or out-of-stock areas",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "shelf_number", "type": "integer", "description": "Which shelf has the gap"},
                                        {"name": "section", "type": "string", "description": "left, center, or right section"},
                                        {"name": "estimated_width_cm", "type": "float", "description": "Approximate gap width"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]'::jsonb,
    ARRAY['planogram', 'structure', 'shelf-analysis', 'standard'],
    true
)
ON CONFLICT (template_id) DO UPDATE 
SET 
    prompt_text = EXCLUDED.prompt_text,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    stage_type = EXCLUDED.stage_type,
    fields = EXCLUDED.fields,
    tags = EXCLUDED.tags,
    updated_at = NOW();

-- STAGE 1: STRUCTURE EXTRACTION - RETRY
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    name,
    description,
    stage_type,
    fields,
    tags,
    is_active
) VALUES (
    'structure_extraction_retry_v2',
    'structure',
    'universal',
    '2.0',
    'Analyze this retail shelf image to identify the physical structure.

COUNT:
□ Number of horizontal shelves (bottom = 1, count up)
□ Each product display level = one shelf
□ Include floor level only if products are placed there

MEASURE:
□ Fixture width: _____ meters (estimate)
□ Fixture height: _____ meters (estimate)
□ Fixture type: wall_shelf | gondola | end_cap | cooler | freezer | bin | pegboard | other

IDENTIFY NON-PRODUCT ELEMENTS:
□ Security devices: grids, magnetic tags, plastic cases, bottle locks
□ Promotional materials: shelf wobblers, hanging signs, price cards, banners
□ Shelf equipment: dividers, pushers, price rails, shelf strips
□ Display accessories: hooks, clip strips, shelf talkers
□ Empty spaces: gaps between products, out-of-stock sections
□ Fixtures: end panels, header boards, base decks

Output the total shelf count and all fixture details.

{IF_RETRY}
PREVIOUS ATTEMPT: {SHELVES} shelves found
Uncertainty areas: {PROBLEM_AREAS}

Common issues to verify:
- Is the bottom/floor level actually holding products?
- Are there partial shelves at the top?
- Did they count dividers as separate shelves?

NOTE: Trust your own analysis over previous attempts.
{/IF_RETRY}',
    'Structure Extraction - Retry v2',
    'Retry prompt for structure extraction with context from previous attempt',
    'retry_structure',
    '[
        {
            "name": "structure_extraction",
            "type": "object",
            "description": "Complete shelf structure analysis",
            "required": true,
            "nested_fields": [
                {
                    "name": "shelf_structure",
                    "type": "object",
                    "description": "Physical structure of the shelf fixture",
                    "required": true,
                    "nested_fields": [
                        {"name": "total_shelves", "type": "integer", "description": "Total number of horizontal shelves", "required": true},
                        {"name": "shelf_type", "type": "string", "description": "Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)", "required": true},
                        {"name": "width_meters", "type": "float", "description": "Estimated width of fixture in meters", "required": true},
                        {"name": "height_meters", "type": "float", "description": "Estimated height of fixture in meters", "required": true},
                        {
                            "name": "shelves",
                            "type": "list",
                            "description": "Detailed information for each shelf level",
                            "required": true,
                            "list_item_type": "object",
                            "nested_fields": [
                                {"name": "shelf_number", "type": "integer", "description": "Shelf identifier (1=bottom, counting up)", "required": true},
                                {"name": "has_price_rail", "type": "boolean", "description": "Whether shelf has price label strip/rail", "required": true},
                                {"name": "special_features", "type": "string", "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)", "required": false}
                            ]
                        },
                        {
                            "name": "non_product_elements",
                            "type": "object",
                            "description": "Items on shelves that are not products",
                            "required": true,
                            "nested_fields": [
                                {
                                    "name": "security_devices",
                                    "type": "list",
                                    "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "type", "type": "string", "description": "Type of security device"},
                                        {"name": "location", "type": "string", "description": "Where on shelf it''s located"}
                                    ]
                                },
                                {
                                    "name": "promotional_materials",
                                    "type": "list",
                                    "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "type", "type": "string", "description": "Type of promotional material"},
                                        {"name": "location", "type": "string", "description": "Where positioned"},
                                        {"name": "text_visible", "type": "string", "description": "Any readable promotional text"}
                                    ]
                                },
                                {
                                    "name": "shelf_equipment",
                                    "type": "list",
                                    "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "type", "type": "string", "description": "Type of equipment"},
                                        {"name": "location", "type": "string", "description": "Where installed"}
                                    ]
                                },
                                {
                                    "name": "empty_spaces",
                                    "type": "list",
                                    "description": "Significant gaps or out-of-stock areas",
                                    "required": false,
                                    "list_item_type": "object",
                                    "nested_fields": [
                                        {"name": "shelf_number", "type": "integer", "description": "Which shelf has the gap"},
                                        {"name": "section", "type": "string", "description": "left, center, or right section"},
                                        {"name": "estimated_width_cm", "type": "float", "description": "Approximate gap width"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]'::jsonb,
    ARRAY['planogram', 'structure', 'shelf-analysis', 'retry', 'context-aware'],
    false
)
ON CONFLICT (template_id) DO UPDATE 
SET 
    prompt_text = EXCLUDED.prompt_text,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    stage_type = EXCLUDED.stage_type,
    fields = EXCLUDED.fields,
    tags = EXCLUDED.tags,
    updated_at = NOW();

-- STAGE 2: PRODUCT EXTRACTION - Standard
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    name,
    description,
    stage_type,
    fields,
    tags,
    is_active
) VALUES (
    'product_extraction_planogram_v2',
    'position',
    'universal',
    '2.0',
    'STAGE 2: PRODUCT EXTRACTION

Analyze this retail shelf image to identify the products present on the shelf. 

We have already identified that {TOTAL_SHELVES} horizontal shelves exist, numbered from bottom (1) to top ({TOTAL_SHELVES}).

WHAT YOU''RE BUILDING:
You are extracting product data that will be converted into a planogram. A planogram is a visual diagram showing product placement on shelves - like a map of the shelf. Your data will become a grid where each product facing gets its own cell.

HOW YOUR EXTRACTION BECOMES VISUAL:
- Each product facing (unit visible from front) = one cell in the grid
- Position 1,2,3 = left-to-right order in the planogram
- Gaps in position numbers = empty space in the visual
- Example: If you extract positions 1,2,5, the planogram shows: [Prod1][Prod2][Empty][Empty][Prod5]

EXTRACT:
1. Scan left to right, identify each distinct product
2. Count facings (units visible from front only)
3. Number products sequentially: 1, 2, 3...
4. Include empty spaces as positions too
5. Note section: Left | Center | Right (divide shelf in thirds)

CRITICAL: Missing positions create gaps in the planogram. Only skip numbers if there''s actual empty space on the shelf.',
    'Product Extraction - Planogram Aware v2',
    'Extract products with planogram context explanation',
    'products',
    '[
        {
            "name": "shelf_extraction",
            "type": "object",
            "description": "Products extracted from a single shelf",
            "required": true,
            "nested_fields": [
                {"name": "shelf_number", "type": "integer", "description": "Which shelf this extraction is for (1=bottom)", "required": true},
                {
                    "name": "products",
                    "type": "list",
                    "description": "All products found on this shelf",
                    "required": true,
                    "list_item_type": "object",
                    "nested_fields": [
                        {"name": "position", "type": "integer", "description": "Sequential position from left to right", "required": true},
                        {"name": "section", "type": "string", "description": "Shelf section (left, center, or right)", "required": true},
                        {"name": "brand", "type": "string", "description": "Product brand name", "required": true},
                        {"name": "name", "type": "string", "description": "Product name or variant", "required": true},
                        {"name": "product_type", "type": "string", "description": "Package type (can, bottle, box, pouch, jar, other)", "required": true},
                        {"name": "facings", "type": "integer", "description": "Number of units visible from front", "required": true},
                        {"name": "stack", "type": "integer", "description": "Vertical stacking count (usually 1)", "required": true, "default": 1}
                    ]
                },
                {
                    "name": "empty_positions",
                    "type": "list",
                    "description": "Position numbers where gaps exist",
                    "required": false,
                    "list_item_type": "integer"
                }
            ]
        }
    ]'::jsonb,
    ARRAY['planogram', 'products', 'extraction', 'planogram-aware'],
    true
)
ON CONFLICT (template_id) DO UPDATE 
SET 
    prompt_text = EXCLUDED.prompt_text,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    stage_type = EXCLUDED.stage_type,
    fields = EXCLUDED.fields,
    tags = EXCLUDED.tags,
    updated_at = NOW();

-- Continue with remaining prompts...
-- I'll add just one more for brevity, but you can add all of them

-- Visual Comparison Agent
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    name,
    description,
    stage_type,
    fields,
    tags,
    is_active
) VALUES (
    'visual_comparison_agent_v2',
    'validation',
    'universal',
    '2.0',
    'COMPARISON AGENT

Compare the GENERATED PLANOGRAM IMAGE with the ORIGINAL SHELF PHOTO.

YOUR TASK:
You will see two images:
1. Original shelf photograph
2. AI-generated planogram visualization

The planogram is a simplified grid representation where:
- Each shelf = horizontal row of colored boxes
- Each box = one product facing
- Box width = number of facings
- Colors/labels identify products

COMPARE THE TWO IMAGES:

□ SHELF COUNT: Same number of rows in planogram as shelves in photo?
□ PRODUCT PRESENCE: Are all major visible products in the planogram?
□ POSITIONING: Products in correct left-to-right sequence?
□ PROPORTIONS: Do product widths match their shelf space?
□ GAPS: Are empty spaces in the right places?

SPECIFIC VISUAL CHECKS:
- If planogram shows [Coke][Coke][Empty][Pepsi]
- Does photo show empty space between Coke and Pepsi?
- Or is there a product missing from extraction?

IGNORE:
- Exact colors/design (planogram is simplified)
- Products deep on shelf (only front facings matter)
- Minor proportion differences

OUTPUT:
Overall accuracy: ____%
Major visual mismatches:
- {ISSUE_1}: "Product X appears on wrong shelf in planogram"
- {ISSUE_2}: "Gap at position Y in planogram but products visible in photo"
- {ISSUE_3}: "Product Z visible in photo but missing from planogram"

Suggested fixes: {SPECIFIC_CORRECTIONS}
Confidence: HIGH | MEDIUM | LOW',
    'Visual Comparison Agent v2',
    'Compare generated planogram with original shelf photo for validation',
    'validation',
    '[
        {
            "name": "comparison_result",
            "type": "object",
            "description": "Visual comparison analysis result",
            "required": true,
            "nested_fields": [
                {"name": "overall_accuracy", "type": "float", "description": "Overall accuracy percentage (0-100)", "required": true},
                {"name": "shelf_count_match", "type": "boolean", "description": "Whether shelf count matches between images", "required": true},
                {"name": "confidence_level", "type": "string", "description": "Confidence in comparison (HIGH, MEDIUM, LOW)", "required": true},
                {
                    "name": "visual_mismatches",
                    "type": "list",
                    "description": "List of visual discrepancies found",
                    "required": true,
                    "list_item_type": "object",
                    "nested_fields": [
                        {"name": "issue_type", "type": "string", "description": "Type of mismatch (wrong_shelf, missing_product, wrong_position, etc.)", "required": true},
                        {"name": "description", "type": "string", "description": "Detailed description of the mismatch", "required": true},
                        {"name": "location", "type": "string", "description": "Where the issue occurs (shelf number, position)", "required": true}
                    ]
                },
                {
                    "name": "suggested_corrections",
                    "type": "list",
                    "description": "Specific corrections to improve accuracy",
                    "required": true,
                    "list_item_type": "string"
                }
            ]
        }
    ]'::jsonb,
    ARRAY['planogram', 'validation', 'visual-comparison', 'comparison-agent'],
    true
)
ON CONFLICT (template_id) DO UPDATE 
SET 
    prompt_text = EXCLUDED.prompt_text,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    stage_type = EXCLUDED.stage_type,
    fields = EXCLUDED.fields,
    tags = EXCLUDED.tags,
    updated_at = NOW();

-- Insert orchestrator prompts into meta_prompts table
INSERT INTO meta_prompts (name, description, template, category, is_default) VALUES
(
    'Master Orchestrator - User Customization',
    'Template for user-defined extraction priorities and strategies',
    'Guide the extraction pipeline with these priorities:

{USER_PRIORITIES}

Examples:
- "Prioritize accuracy over cost for alcohol products"
- "Use faster models after 3 iterations"
- "Focus on price accuracy for promotional items"
- "Stop if accuracy plateaus for 2 iterations"
- "Premium spirits need 95%+ accuracy"',
    'orchestrator',
    false
),
(
    'Extraction Orchestrator - User Guidelines',
    'Template for user-defined extraction guidelines and context',
    'Apply these extraction guidelines:

{USER_GUIDELINES}

Examples:
- "Pay extra attention to promotional pricing"
- "Beverage shelves often have security devices"
- "This store uses digital price tags"
- "Products are tightly packed on bottom shelves"
- "Watch for multipack vs single unit confusion"',
    'orchestrator',
    false
)
ON CONFLICT (name) DO NOTHING;

-- Show what was inserted
SELECT 'New prompts inserted:' as status;
SELECT 
    template_id,
    name,
    stage_type,
    CASE WHEN fields IS NOT NULL THEN 'Yes' ELSE 'No' END as has_pydantic_schema,
    is_active
FROM prompt_templates
WHERE template_id LIKE '%_v2'
ORDER BY stage_type, name;