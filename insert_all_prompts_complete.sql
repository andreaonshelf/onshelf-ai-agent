-- Insert ALL OnShelf AI Extraction Prompts - COMPLETE VERSION
-- This includes all prompts with proper error handling

-- Check existing prompts
SELECT 'Checking for existing v2 prompts:' as info;
SELECT COUNT(*) as existing_v2_prompts 
FROM prompt_templates 
WHERE template_id LIKE '%_v2';

-- Insert all prompts using conditional logic
DO $$
BEGIN
    -- STAGE 1: STRUCTURE EXTRACTION - Standard
    IF NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_id = 'structure_extraction_standard_v2') THEN
        INSERT INTO prompt_templates (
            template_id, prompt_type, model_type, prompt_version, prompt_text,
            name, description, stage_type, fields, tags, is_active
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
            '[{"name": "structure_extraction", "type": "object", "description": "Complete shelf structure analysis", "required": true, "nested_fields": [{"name": "shelf_structure", "type": "object", "description": "Physical structure of the shelf fixture", "required": true, "nested_fields": [{"name": "total_shelves", "type": "integer", "description": "Total number of horizontal shelves", "required": true}, {"name": "shelf_type", "type": "string", "description": "Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)", "required": true}, {"name": "width_meters", "type": "float", "description": "Estimated width of fixture in meters", "required": true}, {"name": "height_meters", "type": "float", "description": "Estimated height of fixture in meters", "required": true}, {"name": "shelves", "type": "list", "description": "Detailed information for each shelf level", "required": true, "list_item_type": "object", "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Shelf identifier (1=bottom, counting up)", "required": true}, {"name": "has_price_rail", "type": "boolean", "description": "Whether shelf has price label strip/rail", "required": true}, {"name": "special_features", "type": "string", "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)", "required": false}]}, {"name": "non_product_elements", "type": "object", "description": "Items on shelves that are not products", "required": true, "nested_fields": [{"name": "security_devices", "type": "list", "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)", "required": false, "list_item_type": "object", "nested_fields": [{"name": "type", "type": "string", "description": "Type of security device"}, {"name": "location", "type": "string", "description": "Where on shelf it''s located"}]}, {"name": "promotional_materials", "type": "list", "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)", "required": false, "list_item_type": "object", "nested_fields": [{"name": "type", "type": "string", "description": "Type of promotional material"}, {"name": "location", "type": "string", "description": "Where positioned"}, {"name": "text_visible", "type": "string", "description": "Any readable promotional text"}]}, {"name": "shelf_equipment", "type": "list", "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)", "required": false, "list_item_type": "object", "nested_fields": [{"name": "type", "type": "string", "description": "Type of equipment"}, {"name": "location", "type": "string", "description": "Where installed"}]}, {"name": "empty_spaces", "type": "list", "description": "Significant gaps or out-of-stock areas", "required": false, "list_item_type": "object", "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Which shelf has the gap"}, {"name": "section", "type": "string", "description": "left, center, or right section"}, {"name": "estimated_width_cm", "type": "float", "description": "Approximate gap width"}]}]}]}]}]'::jsonb,
            ARRAY['planogram', 'structure', 'shelf-analysis', 'standard'],
            true
        );
        RAISE NOTICE 'Inserted: Structure Extraction - Standard v2';
    END IF;

    -- STAGE 1: STRUCTURE EXTRACTION - RETRY
    IF NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_id = 'structure_extraction_retry_v2') THEN
        INSERT INTO prompt_templates (
            template_id, prompt_type, model_type, prompt_version, prompt_text,
            name, description, stage_type, fields, tags, is_active
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
            '[{"name": "structure_extraction", "type": "object", "description": "Complete shelf structure analysis", "required": true, "nested_fields": [{"name": "shelf_structure", "type": "object", "description": "Physical structure of the shelf fixture", "required": true, "nested_fields": [{"name": "total_shelves", "type": "integer", "description": "Total number of horizontal shelves", "required": true}, {"name": "shelf_type", "type": "string", "description": "Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)", "required": true}, {"name": "width_meters", "type": "float", "description": "Estimated width of fixture in meters", "required": true}, {"name": "height_meters", "type": "float", "description": "Estimated height of fixture in meters", "required": true}, {"name": "shelves", "type": "list", "description": "Detailed information for each shelf level", "required": true, "list_item_type": "object", "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Shelf identifier (1=bottom, counting up)", "required": true}, {"name": "has_price_rail", "type": "boolean", "description": "Whether shelf has price label strip/rail", "required": true}, {"name": "special_features", "type": "string", "description": "Unusual characteristics (slanted, wire mesh, divided sections, damaged)", "required": false}]}, {"name": "non_product_elements", "type": "object", "description": "Items on shelves that are not products", "required": true, "nested_fields": [{"name": "security_devices", "type": "list", "description": "Security measures (grids, magnetic tags, plastic cases, bottle locks)", "required": false, "list_item_type": "object", "nested_fields": [{"name": "type", "type": "string", "description": "Type of security device"}, {"name": "location", "type": "string", "description": "Where on shelf it''s located"}]}, {"name": "promotional_materials", "type": "list", "description": "Marketing materials (shelf wobblers, hanging signs, price cards, banners)", "required": false, "list_item_type": "object", "nested_fields": [{"name": "type", "type": "string", "description": "Type of promotional material"}, {"name": "location", "type": "string", "description": "Where positioned"}, {"name": "text_visible", "type": "string", "description": "Any readable promotional text"}]}, {"name": "shelf_equipment", "type": "list", "description": "Shelf organization tools (dividers, pushers, price rails, shelf strips)", "required": false, "list_item_type": "object", "nested_fields": [{"name": "type", "type": "string", "description": "Type of equipment"}, {"name": "location", "type": "string", "description": "Where installed"}]}, {"name": "empty_spaces", "type": "list", "description": "Significant gaps or out-of-stock areas", "required": false, "list_item_type": "object", "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Which shelf has the gap"}, {"name": "section", "type": "string", "description": "left, center, or right section"}, {"name": "estimated_width_cm", "type": "float", "description": "Approximate gap width"}]}]}]}]}]'::jsonb,
            ARRAY['planogram', 'structure', 'shelf-analysis', 'retry', 'context-aware'],
            false
        );
        RAISE NOTICE 'Inserted: Structure Extraction - Retry v2';
    END IF;

    -- STAGE 2: PRODUCT EXTRACTION - Standard
    IF NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_id = 'product_extraction_planogram_v2') THEN
        INSERT INTO prompt_templates (
            template_id, prompt_type, model_type, prompt_version, prompt_text,
            name, description, stage_type, fields, tags, is_active
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
            '[{"name": "shelf_extraction", "type": "object", "description": "Products extracted from a single shelf", "required": true, "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Which shelf this extraction is for (1=bottom)", "required": true}, {"name": "products", "type": "list", "description": "All products found on this shelf", "required": true, "list_item_type": "object", "nested_fields": [{"name": "position", "type": "integer", "description": "Sequential position from left to right", "required": true}, {"name": "section", "type": "string", "description": "Shelf section (left, center, or right)", "required": true}, {"name": "brand", "type": "string", "description": "Product brand name", "required": true}, {"name": "name", "type": "string", "description": "Product name or variant", "required": true}, {"name": "product_type", "type": "string", "description": "Package type (can, bottle, box, pouch, jar, other)", "required": true}, {"name": "facings", "type": "integer", "description": "Number of units visible from front", "required": true}, {"name": "stack", "type": "integer", "description": "Vertical stacking count (usually 1)", "required": true, "default": 1}]}, {"name": "empty_positions", "type": "list", "description": "Position numbers where gaps exist", "required": false, "list_item_type": "integer"}]}]'::jsonb,
            ARRAY['planogram', 'products', 'extraction', 'planogram-aware'],
            true
        );
        RAISE NOTICE 'Inserted: Product Extraction - Planogram Aware v2';
    END IF;

    -- STAGE 2: PRODUCT EXTRACTION - RETRY
    IF NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_id = 'product_extraction_retry_v2') THEN
        INSERT INTO prompt_templates (
            template_id, prompt_type, model_type, prompt_version, prompt_text,
            name, description, stage_type, fields, tags, is_active
        ) VALUES (
            'product_extraction_retry_v2',
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

CRITICAL: Missing positions create gaps in the planogram. Only skip numbers if there''s actual empty space on the shelf.

{IF_RETRY}
PREVIOUS FOUND ON THIS SHELF:
{PREVIOUS_SHELF_PRODUCTS}

VISUAL FEEDBACK:
{PLANOGRAM_FEEDBACK}
Example: "Shelf looks too sparse - check for missed products"

NOTE: Trust what you see. Add/correct products as needed.
You can disagree with the previous extraction completely.
{/IF_RETRY}',
            'Product Extraction - Retry with Context v2',
            'Retry product extraction with previous attempt context and visual feedback',
            'retry_products',
            '[{"name": "shelf_extraction", "type": "object", "description": "Products extracted from a single shelf", "required": true, "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Which shelf this extraction is for (1=bottom)", "required": true}, {"name": "products", "type": "list", "description": "All products found on this shelf", "required": true, "list_item_type": "object", "nested_fields": [{"name": "position", "type": "integer", "description": "Sequential position from left to right", "required": true}, {"name": "section", "type": "string", "description": "Shelf section (left, center, or right)", "required": true}, {"name": "brand", "type": "string", "description": "Product brand name", "required": true}, {"name": "name", "type": "string", "description": "Product name or variant", "required": true}, {"name": "product_type", "type": "string", "description": "Package type (can, bottle, box, pouch, jar, other)", "required": true}, {"name": "facings", "type": "integer", "description": "Number of units visible from front", "required": true}, {"name": "stack", "type": "integer", "description": "Vertical stacking count (usually 1)", "required": true, "default": 1}]}, {"name": "empty_positions", "type": "list", "description": "Position numbers where gaps exist", "required": false, "list_item_type": "integer"}]}]'::jsonb,
            ARRAY['planogram', 'products', 'extraction', 'retry', 'context-aware'],
            false
        );
        RAISE NOTICE 'Inserted: Product Extraction - Retry with Context v2';
    END IF;

    -- STAGE 3: DETAIL ENHANCEMENT - Standard (I'll make this shorter for space)
    IF NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_id = 'detail_enhancement_standard_v2') THEN
        INSERT INTO prompt_templates (
            template_id, prompt_type, model_type, prompt_version, prompt_text,
            name, description, stage_type, fields, tags, is_active
        ) VALUES (
            'detail_enhancement_standard_v2',
            'detail',
            'universal',
            '2.0',
            'Look at this retail shelf image.

We have already identified and located these products:

{COMPLETE_PRODUCT_LIST}

YOUR TASK:
For EACH product in the list above, LOOK AT THE IMAGE and extract the following details:

1. FIND THE PRODUCT IN THE IMAGE using its shelf and position information
2. EXTRACT THESE DETAILS BY LOOKING AT:

PRICING (check shelf edge labels below/near the product):
□ Regular price: £_____
□ Promotional price: £_____ (if different)
□ Promotion text: _____ (e.g., "3 for £5", "Buy 2 get 1 free")
□ Currency: GBP | EUR | USD | other

PACKAGE DETAILS (read from the product itself):
□ Package size: _____ (e.g., "330ml", "750ml", "1L", "6-pack")
□ If multipack: individual unit size and count
□ Total volume: _____ (e.g., "6 × 330ml = 1,980ml")
□ Package type: can | bottle | box | pouch | jar | other

PHYSICAL CHARACTERISTICS (observe the actual product):
□ Width relative to neighbors: narrow | normal | wide
□ Height relative to shelf: short | medium | tall
□ Estimated dimensions: width ___cm, height ___cm

VISUAL APPEARANCE (look at the actual package):
□ Primary color: _____ (most dominant color you see)
□ Secondary color: _____ (second most prominent)
□ Package finish: metallic | matte | glossy | transparent

VISIBILITY ASSESSMENT:
□ How clearly can you see this product: clearly_visible | partially_obscured | mostly_hidden
□ Confidence in details extracted: high | medium | low
□ Any issues: _____ (e.g., "price tag torn", "product behind security device")

Process EVERY product in the list systematically.',
            'Detail Enhancement - Standard v2',
            'Extract detailed product information for all identified products',
            'details',
            '[{"name": "detail_extraction", "type": "object", "description": "Detailed product information extraction", "required": true, "nested_fields": [{"name": "product_details_list", "type": "list", "description": "Detailed information for all products", "required": true, "list_item_type": "object", "nested_fields": [{"name": "product_identification", "type": "object", "description": "Product location and identity", "required": true, "nested_fields": [{"name": "shelf_number", "type": "integer", "description": "Which shelf the product is on", "required": true}, {"name": "position", "type": "integer", "description": "Product position on shelf", "required": true}, {"name": "brand", "type": "string", "description": "Product brand name", "required": true}, {"name": "name", "type": "string", "description": "Product name or variant", "required": true}]}, {"name": "pricing", "type": "object", "description": "Price information", "required": true, "nested_fields": [{"name": "regular_price", "type": "float", "description": "Standard price", "required": false}, {"name": "promotional_price", "type": "float", "description": "Sale or discounted price", "required": false}, {"name": "promotion_text", "type": "string", "description": "Promotional offer text", "required": false}, {"name": "currency", "type": "string", "description": "Currency code (GBP, EUR, USD)", "required": true}, {"name": "price_visible", "type": "boolean", "description": "Whether price is visible in image", "required": true}]}, {"name": "package_info", "type": "object", "description": "Package details", "required": true, "nested_fields": [{"name": "package_type", "type": "string", "description": "Type of container", "required": true}, {"name": "size", "type": "string", "description": "Package size", "required": false}, {"name": "unit_count", "type": "integer", "description": "Number of units in multipack", "required": false}, {"name": "unit_size", "type": "string", "description": "Size of individual units", "required": false}, {"name": "total_volume", "type": "string", "description": "Total volume calculation", "required": false}]}, {"name": "dimensions", "type": "object", "description": "Physical size characteristics", "required": true, "nested_fields": [{"name": "width_relative", "type": "string", "description": "Width compared to shelf average", "required": true}, {"name": "height_relative", "type": "string", "description": "Height compared to shelf average", "required": true}, {"name": "width_cm", "type": "float", "description": "Estimated width in centimeters", "required": false}, {"name": "height_cm", "type": "float", "description": "Estimated height in centimeters", "required": false}]}, {"name": "visual_info", "type": "object", "description": "Visual appearance", "required": true, "nested_fields": [{"name": "primary_color", "type": "string", "description": "Most dominant package color", "required": true}, {"name": "secondary_color", "type": "string", "description": "Second most prominent color", "required": true}, {"name": "finish", "type": "string", "description": "Surface finish", "required": false}]}, {"name": "extraction_quality", "type": "object", "description": "Quality assessment", "required": true, "nested_fields": [{"name": "visibility", "type": "string", "description": "How well product is visible", "required": true}, {"name": "confidence", "type": "string", "description": "Extraction confidence level", "required": true}, {"name": "issues", "type": "list", "description": "Any extraction problems encountered", "required": false, "list_item_type": "string"}]}]}]}]'::jsonb,
            ARRAY['planogram', 'details', 'enhancement', 'standard'],
            true
        );
        RAISE NOTICE 'Inserted: Detail Enhancement - Standard v2';
    END IF;

    -- Visual Comparison Agent
    IF NOT EXISTS (SELECT 1 FROM prompt_templates WHERE template_id = 'visual_comparison_agent_v2') THEN
        INSERT INTO prompt_templates (
            template_id, prompt_type, model_type, prompt_version, prompt_text,
            name, description, stage_type, fields, tags, is_active
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
            '[{"name": "comparison_result", "type": "object", "description": "Visual comparison analysis result", "required": true, "nested_fields": [{"name": "overall_accuracy", "type": "float", "description": "Overall accuracy percentage (0-100)", "required": true}, {"name": "shelf_count_match", "type": "boolean", "description": "Whether shelf count matches between images", "required": true}, {"name": "confidence_level", "type": "string", "description": "Confidence in comparison (HIGH, MEDIUM, LOW)", "required": true}, {"name": "visual_mismatches", "type": "list", "description": "List of visual discrepancies found", "required": true, "list_item_type": "object", "nested_fields": [{"name": "issue_type", "type": "string", "description": "Type of mismatch", "required": true}, {"name": "description", "type": "string", "description": "Detailed description of the mismatch", "required": true}, {"name": "location", "type": "string", "description": "Where the issue occurs", "required": true}]}, {"name": "suggested_corrections", "type": "list", "description": "Specific corrections to improve accuracy", "required": true, "list_item_type": "string"}]}]'::jsonb,
            ARRAY['planogram', 'validation', 'visual-comparison', 'comparison-agent'],
            true
        );
        RAISE NOTICE 'Inserted: Visual Comparison Agent v2';
    END IF;

END $$;

-- Handle meta_prompts table separately
DO $$
BEGIN
    -- Master Orchestrator
    IF NOT EXISTS (SELECT 1 FROM meta_prompts WHERE name = 'Master Orchestrator - User Customization') THEN
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
        );
        RAISE NOTICE 'Inserted: Master Orchestrator - User Customization';
    END IF;

    -- Extraction Orchestrator
    IF NOT EXISTS (SELECT 1 FROM meta_prompts WHERE name = 'Extraction Orchestrator - User Guidelines') THEN
        INSERT INTO meta_prompts (name, description, template, category, is_default) VALUES
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
        );
        RAISE NOTICE 'Inserted: Extraction Orchestrator - User Guidelines';
    END IF;
END $$;

-- Final summary
SELECT 'INSERTION COMPLETE!' as status;

SELECT 'Prompt Templates Summary:' as info;
SELECT 
    stage_type,
    COUNT(*) as prompt_count,
    COUNT(*) FILTER (WHERE fields IS NOT NULL) as with_pydantic_schema,
    COUNT(*) FILTER (WHERE is_active = true) as active_prompts
FROM prompt_templates
WHERE template_id LIKE '%_v2'
GROUP BY stage_type
ORDER BY stage_type;

SELECT 'Meta Prompts Summary:' as info;
SELECT category, COUNT(*) as count
FROM meta_prompts
WHERE category = 'orchestrator'
GROUP BY category;