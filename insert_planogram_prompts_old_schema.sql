-- Insert OnShelf AI Extraction Prompts into prompt_templates table (OLD SCHEMA VERSION)
-- This version uses prompt_content instead of prompt_text

-- First, let's check which schema version we have
DO $$
BEGIN
    -- Check if we have the old schema (with prompt_content)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'prompt_templates' 
               AND column_name = 'prompt_content') THEN
        
        -- Insert into old schema format
        -- Note: Old schema doesn't have fields, stage_type, or tags columns
        -- We'll store the prompts as different prompt_types
        
        -- STAGE 1: STRUCTURE EXTRACTION - Standard
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'structure_extraction_standard',
            'structure',
            'universal',
            '1.0',
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
            true
        );

        -- STAGE 1: STRUCTURE EXTRACTION - Retry
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'structure_extraction_retry',
            'structure',
            'universal',
            '1.0',
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
            false
        );

        -- STAGE 2: PRODUCT EXTRACTION - Standard (using position prompt_type)
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'product_extraction_planogram',
            'position',
            'universal',
            '1.0',
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
            true
        );

        -- STAGE 2: PRODUCT EXTRACTION - Retry
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'product_extraction_retry',
            'position',
            'universal',
            '1.0',
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
            false
        );

        -- STAGE 3: DETAIL ENHANCEMENT - Standard
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'detail_enhancement_standard',
            'detail',
            'universal',
            '1.0',
            'Look at this retail shelf image.

We have already identified and located these products:

{COMPLETE_PRODUCT_LIST}
Example format:
Shelf 1:
- Position 1: Coca-Cola 330ml (6 facings) - Left section
- Position 2: [Empty space]
- Position 3: Pepsi Max 500ml (4 facings) - Center section
- Position 4: Fanta Orange (3 facings) - Center section

Shelf 2:
- Position 1: Budweiser (8 facings) - Left section
[etc...]

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
            true
        );

        -- STAGE 3: DETAIL ENHANCEMENT - Retry
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'detail_enhancement_retry',
            'detail',
            'universal',
            '1.0',
            'Look at this retail shelf image.

We have already identified and located these products:

{COMPLETE_PRODUCT_LIST}
Example format:
Shelf 1:
- Position 1: Coca-Cola 330ml (6 facings) - Left section
- Position 2: [Empty space]
- Position 3: Pepsi Max 500ml (4 facings) - Center section
- Position 4: Fanta Orange (3 facings) - Center section

Shelf 2:
- Position 1: Budweiser (8 facings) - Left section
[etc...]

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

Process EVERY product in the list systematically.

{IF_RETRY}
PREVIOUS ATTEMPT RESULTS:
{PREVIOUS_DETAILS_BY_PRODUCT}

For each product, we have marked what''s still missing or uncertain.
You should:
- Verify all previously extracted details by looking at the image yourself
- Fill in any missing information
- Correct anything that seems wrong based on what you see
- Report "not visible" only if you truly cannot see the information

You are free to disagree with previous extractions if you see differently in the image.
{/IF_RETRY}',
            false
        );

        -- Visual Comparison Agent
        INSERT INTO prompt_templates (
            template_id,
            prompt_type,
            model_type,
            prompt_version,
            prompt_content,
            is_active
        ) VALUES (
            'visual_comparison_agent',
            'validation',
            'universal',
            '1.0',
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
            true
        );

        RAISE NOTICE 'Prompts inserted into old schema format (prompt_content column)';
        
    ELSIF EXISTS (SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'prompt_templates' 
                 AND column_name = 'prompt_text') THEN
        
        RAISE NOTICE 'You have the new schema format. Please use insert_planogram_prompts.sql instead';
        
    ELSE
        RAISE EXCEPTION 'prompt_templates table not found';
    END IF;
END $$;

-- Insert orchestrator prompts into meta_prompts table (this table schema should be consistent)
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