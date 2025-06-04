-- Fix prompts to EXACTLY match the OnShelf AI Extraction Prompts document
-- Delete all existing prompts and recreate with exact specifications

-- First clear everything
DELETE FROM prompt_templates;

-- STAGE 1: STRUCTURE EXTRACTION
INSERT INTO prompt_templates (
    template_id,
    name,
    description,
    prompt_template,
    field_definitions,
    stage_type,
    prompt_type,
    is_active,
    version,
    performance_score,
    avg_usage_count
) VALUES (
    'structure_extraction_v1',
    'Structure Extraction',
    'Stage 1: Identify physical shelf structure',
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
    jsonb_build_object(
        'type', 'object',
        'properties', jsonb_build_object(
            'structure_extraction', jsonb_build_object(
                'type', 'object',
                'description', 'Complete shelf structure analysis',
                'required', true,
                'properties', jsonb_build_object(
                    'shelf_structure', jsonb_build_object(
                        'type', 'object',
                        'description', 'Physical structure of the shelf fixture',
                        'required', true,
                        'properties', jsonb_build_object(
                            'total_shelves', jsonb_build_object(
                                'type', 'integer',
                                'description', 'Total number of horizontal shelves',
                                'required', true
                            ),
                            'shelf_type', jsonb_build_object(
                                'type', 'string',
                                'description', 'Type of fixture (wall_shelf, gondola, end_cap, cooler, freezer, bin, pegboard, other)',
                                'required', true,
                                'enum', jsonb_build_array('wall_shelf', 'gondola', 'end_cap', 'cooler', 'freezer', 'bin', 'pegboard', 'other')
                            ),
                            'width_meters', jsonb_build_object(
                                'type', 'number',
                                'description', 'Estimated width of fixture in meters',
                                'required', true
                            ),
                            'height_meters', jsonb_build_object(
                                'type', 'number',
                                'description', 'Estimated height of fixture in meters',
                                'required', true
                            ),
                            'shelves', jsonb_build_object(
                                'type', 'array',
                                'description', 'Detailed information for each shelf level',
                                'required', true,
                                'items', jsonb_build_object(
                                    'type', 'object',
                                    'properties', jsonb_build_object(
                                        'shelf_number', jsonb_build_object(
                                            'type', 'integer',
                                            'description', 'Shelf identifier (1=bottom, counting up)',
                                            'required', true
                                        ),
                                        'has_price_rail', jsonb_build_object(
                                            'type', 'boolean',
                                            'description', 'Whether shelf has price label strip/rail',
                                            'required', true
                                        ),
                                        'special_features', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Unusual characteristics (slanted, wire mesh, divided sections, damaged)',
                                            'required', false
                                        )
                                    )
                                )
                            ),
                            'non_product_elements', jsonb_build_object(
                                'type', 'object',
                                'description', 'Items on shelves that are not products',
                                'required', true,
                                'properties', jsonb_build_object(
                                    'security_devices', jsonb_build_object(
                                        'type', 'array',
                                        'description', 'Security measures (grids, magnetic tags, plastic cases, bottle locks)',
                                        'required', false,
                                        'items', jsonb_build_object(
                                            'type', 'object',
                                            'properties', jsonb_build_object(
                                                'type', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Type of security device'
                                                ),
                                                'location', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Where on shelf it''s located'
                                                )
                                            )
                                        )
                                    ),
                                    'promotional_materials', jsonb_build_object(
                                        'type', 'array',
                                        'description', 'Marketing materials (shelf wobblers, hanging signs, price cards, banners)',
                                        'required', false,
                                        'items', jsonb_build_object(
                                            'type', 'object',
                                            'properties', jsonb_build_object(
                                                'type', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Type of promotional material'
                                                ),
                                                'location', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Where positioned'
                                                ),
                                                'text_visible', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Any readable promotional text'
                                                )
                                            )
                                        )
                                    ),
                                    'shelf_equipment', jsonb_build_object(
                                        'type', 'array',
                                        'description', 'Shelf organization tools (dividers, pushers, price rails, shelf strips)',
                                        'required', false,
                                        'items', jsonb_build_object(
                                            'type', 'object',
                                            'properties', jsonb_build_object(
                                                'type', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Type of equipment'
                                                ),
                                                'location', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'Where installed'
                                                )
                                            )
                                        )
                                    ),
                                    'empty_spaces', jsonb_build_object(
                                        'type', 'array',
                                        'description', 'Significant gaps or out-of-stock areas',
                                        'required', false,
                                        'items', jsonb_build_object(
                                            'type', 'object',
                                            'properties', jsonb_build_object(
                                                'shelf_number', jsonb_build_object(
                                                    'type', 'integer',
                                                    'description', 'Which shelf has the gap'
                                                ),
                                                'section', jsonb_build_object(
                                                    'type', 'string',
                                                    'description', 'left, center, or right section',
                                                    'enum', jsonb_build_array('left', 'center', 'right')
                                                ),
                                                'estimated_width_cm', jsonb_build_object(
                                                    'type', 'number',
                                                    'description', 'Approximate gap width'
                                                )
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ),
        'required', jsonb_build_array('structure_extraction')
    ),
    'structure',
    'initial',
    true,
    '1.0',
    0.85,
    150
);

-- STAGE 2: PRODUCT EXTRACTION
INSERT INTO prompt_templates (
    template_id,
    name,
    description,
    prompt_template,
    field_definitions,
    stage_type,
    prompt_type,
    is_active,
    version,
    performance_score,
    avg_usage_count
) VALUES (
    'product_extraction_v1',
    'Product Extraction',
    'Stage 2: Extract products from shelf',
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
    jsonb_build_object(
        'type', 'object',
        'properties', jsonb_build_object(
            'shelf_extraction', jsonb_build_object(
                'type', 'object',
                'description', 'Products extracted from a single shelf',
                'required', true,
                'properties', jsonb_build_object(
                    'shelf_number', jsonb_build_object(
                        'type', 'integer',
                        'description', 'Which shelf this extraction is for (1=bottom)',
                        'required', true
                    ),
                    'products', jsonb_build_object(
                        'type', 'array',
                        'description', 'All products found on this shelf',
                        'required', true,
                        'items', jsonb_build_object(
                            'type', 'object',
                            'properties', jsonb_build_object(
                                'position', jsonb_build_object(
                                    'type', 'integer',
                                    'description', 'Sequential position from left to right',
                                    'required', true
                                ),
                                'section', jsonb_build_object(
                                    'type', 'string',
                                    'description', 'Shelf section (left, center, or right)',
                                    'required', true,
                                    'enum', jsonb_build_array('left', 'center', 'right')
                                ),
                                'brand', jsonb_build_object(
                                    'type', 'string',
                                    'description', 'Product brand name',
                                    'required', true
                                ),
                                'name', jsonb_build_object(
                                    'type', 'string',
                                    'description', 'Product name or variant',
                                    'required', true
                                ),
                                'product_type', jsonb_build_object(
                                    'type', 'string',
                                    'description', 'Package type (can, bottle, box, pouch, jar, other)',
                                    'required', true,
                                    'enum', jsonb_build_array('can', 'bottle', 'box', 'pouch', 'jar', 'other')
                                ),
                                'facings', jsonb_build_object(
                                    'type', 'integer',
                                    'description', 'Number of units visible from front',
                                    'required', true
                                ),
                                'stack', jsonb_build_object(
                                    'type', 'integer',
                                    'description', 'Vertical stacking count (usually 1)',
                                    'required', true
                                )
                            ),
                            'required', jsonb_build_array('position', 'section', 'brand', 'name', 'product_type', 'facings', 'stack')
                        )
                    ),
                    'empty_positions', jsonb_build_object(
                        'type', 'array',
                        'description', 'Position numbers where gaps exist',
                        'required', false,
                        'items', jsonb_build_object(
                            'type', 'integer'
                        )
                    )
                ),
                'required', jsonb_build_array('shelf_number', 'products')
            )
        ),
        'required', jsonb_build_array('shelf_extraction')
    ),
    'products',
    'initial',
    true,
    '1.0',
    0.82,
    200
);

-- STAGE 3: DETAIL ENHANCEMENT (Standard Prompt)
INSERT INTO prompt_templates (
    template_id,
    name,
    description,
    prompt_template,
    field_definitions,
    stage_type,
    prompt_type,
    is_active,
    version,
    performance_score,
    avg_usage_count
) VALUES (
    'detail_extraction_v1',
    'Detail Enhancement',
    'Stage 3: Extract detailed product information',
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
    jsonb_build_object(
        'type', 'object',
        'properties', jsonb_build_object(
            'detail_extraction', jsonb_build_object(
                'type', 'object',
                'description', 'Detailed product information extraction',
                'required', true,
                'properties', jsonb_build_object(
                    'product_details_list', jsonb_build_object(
                        'type', 'array',
                        'description', 'Detailed information for all products',
                        'required', true,
                        'items', jsonb_build_object(
                            'type', 'object',
                            'properties', jsonb_build_object(
                                'product_identification', jsonb_build_object(
                                    'type', 'object',
                                    'description', 'Product location and identity',
                                    'required', true,
                                    'properties', jsonb_build_object(
                                        'shelf_number', jsonb_build_object(
                                            'type', 'integer',
                                            'description', 'Which shelf the product is on',
                                            'required', true
                                        ),
                                        'position', jsonb_build_object(
                                            'type', 'integer',
                                            'description', 'Product position on shelf',
                                            'required', true
                                        ),
                                        'brand', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Product brand name',
                                            'required', true
                                        ),
                                        'name', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Product name or variant',
                                            'required', true
                                        )
                                    ),
                                    'required', jsonb_build_array('shelf_number', 'position', 'brand', 'name')
                                ),
                                'pricing', jsonb_build_object(
                                    'type', 'object',
                                    'description', 'Price information',
                                    'required', true,
                                    'properties', jsonb_build_object(
                                        'regular_price', jsonb_build_object(
                                            'type', 'number',
                                            'description', 'Standard price',
                                            'required', false
                                        ),
                                        'promotional_price', jsonb_build_object(
                                            'type', 'number',
                                            'description', 'Sale or discounted price',
                                            'required', false
                                        ),
                                        'promotion_text', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Promotional offer text (e.g., "3 for £5")',
                                            'required', false
                                        ),
                                        'currency', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Currency code (GBP, EUR, USD)',
                                            'required', true,
                                            'enum', jsonb_build_array('GBP', 'EUR', 'USD', 'other')
                                        ),
                                        'price_visible', jsonb_build_object(
                                            'type', 'boolean',
                                            'description', 'Whether price is visible in image',
                                            'required', true
                                        )
                                    ),
                                    'required', jsonb_build_array('currency', 'price_visible')
                                ),
                                'package_info', jsonb_build_object(
                                    'type', 'object',
                                    'description', 'Package details',
                                    'required', true,
                                    'properties', jsonb_build_object(
                                        'package_type', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Type of container (can, bottle, box, pouch, jar, other)',
                                            'required', true,
                                            'enum', jsonb_build_array('can', 'bottle', 'box', 'pouch', 'jar', 'other')
                                        ),
                                        'size', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Package size (e.g., 330ml, 750ml, 1L)',
                                            'required', false
                                        ),
                                        'unit_count', jsonb_build_object(
                                            'type', 'integer',
                                            'description', 'Number of units in multipack',
                                            'required', false
                                        ),
                                        'unit_size', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Size of individual units in multipack',
                                            'required', false
                                        ),
                                        'total_volume', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Total volume calculation',
                                            'required', false
                                        )
                                    ),
                                    'required', jsonb_build_array('package_type')
                                ),
                                'dimensions', jsonb_build_object(
                                    'type', 'object',
                                    'description', 'Physical size characteristics',
                                    'required', true,
                                    'properties', jsonb_build_object(
                                        'width_relative', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Width compared to shelf average (narrow, normal, wide)',
                                            'required', true,
                                            'enum', jsonb_build_array('narrow', 'normal', 'wide')
                                        ),
                                        'height_relative', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Height compared to shelf average (short, medium, tall)',
                                            'required', true,
                                            'enum', jsonb_build_array('short', 'medium', 'tall')
                                        ),
                                        'width_cm', jsonb_build_object(
                                            'type', 'number',
                                            'description', 'Estimated width in centimeters',
                                            'required', false
                                        ),
                                        'height_cm', jsonb_build_object(
                                            'type', 'number',
                                            'description', 'Estimated height in centimeters',
                                            'required', false
                                        )
                                    ),
                                    'required', jsonb_build_array('width_relative', 'height_relative')
                                ),
                                'visual_info', jsonb_build_object(
                                    'type', 'object',
                                    'description', 'Visual appearance',
                                    'required', true,
                                    'properties', jsonb_build_object(
                                        'primary_color', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Most dominant package color',
                                            'required', true
                                        ),
                                        'secondary_color', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Second most prominent color',
                                            'required', true
                                        ),
                                        'finish', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Surface finish (metallic, matte, glossy, transparent)',
                                            'required', false,
                                            'enum', jsonb_build_array('metallic', 'matte', 'glossy', 'transparent')
                                        )
                                    ),
                                    'required', jsonb_build_array('primary_color', 'secondary_color')
                                ),
                                'extraction_quality', jsonb_build_object(
                                    'type', 'object',
                                    'description', 'Quality assessment',
                                    'required', true,
                                    'properties', jsonb_build_object(
                                        'visibility', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'How well product is visible (clearly_visible, partially_obscured, mostly_hidden)',
                                            'required', true,
                                            'enum', jsonb_build_array('clearly_visible', 'partially_obscured', 'mostly_hidden')
                                        ),
                                        'confidence', jsonb_build_object(
                                            'type', 'string',
                                            'description', 'Extraction confidence level (high, medium, low)',
                                            'required', true,
                                            'enum', jsonb_build_array('high', 'medium', 'low')
                                        ),
                                        'issues', jsonb_build_object(
                                            'type', 'array',
                                            'description', 'Any extraction problems encountered',
                                            'required', false,
                                            'items', jsonb_build_object(
                                                'type', 'string'
                                            )
                                        )
                                    ),
                                    'required', jsonb_build_array('visibility', 'confidence')
                                )
                            ),
                            'required', jsonb_build_array('product_identification', 'pricing', 'package_info', 'dimensions', 'visual_info', 'extraction_quality')
                        )
                    )
                ),
                'required', jsonb_build_array('product_details_list')
            )
        ),
        'required', jsonb_build_array('detail_extraction')
    ),
    'details',
    'initial',
    true,
    '1.0',
    0.78,
    180
);

-- STAGE 3: DETAIL ENHANCEMENT (Retry Prompt)
INSERT INTO prompt_templates (
    template_id,
    name,
    description,
    prompt_template,
    field_definitions,
    stage_type,
    prompt_type,
    is_active,
    version,
    performance_score,
    avg_usage_count
) VALUES (
    'detail_extraction_retry_v1',
    'Detail Enhancement Retry',
    'Stage 3: Retry detail extraction with previous context',
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
    NULL, -- Same schema as detail_extraction_v1
    'details',
    'retry',
    true,
    '1.0',
    0.85,
    50
);

-- COMPARISON AGENT (Visual Validator)
INSERT INTO prompt_templates (
    template_id,
    name,
    description,
    prompt_template,
    field_definitions,
    stage_type,
    prompt_type,
    is_active,
    version,
    performance_score,
    avg_usage_count
) VALUES (
    'comparison_agent_v1',
    'Visual Comparison Agent',
    'Compare generated planogram with original photo',
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
    jsonb_build_object(
        'type', 'object',
        'properties', jsonb_build_object(
            'comparison_results', jsonb_build_object(
                'type', 'object',
                'description', 'Visual comparison between planogram and photo',
                'required', true,
                'properties', jsonb_build_object(
                    'overall_accuracy', jsonb_build_object(
                        'type', 'number',
                        'description', 'Overall accuracy percentage (0-100)',
                        'required', true,
                        'minimum', 0,
                        'maximum', 100
                    ),
                    'shelf_count_match', jsonb_build_object(
                        'type', 'boolean',
                        'description', 'Whether shelf count matches between images',
                        'required', true
                    ),
                    'product_presence_match', jsonb_build_object(
                        'type', 'boolean',
                        'description', 'Whether all major products are present',
                        'required', true
                    ),
                    'positioning_match', jsonb_build_object(
                        'type', 'boolean',
                        'description', 'Whether product positions are correct',
                        'required', true
                    ),
                    'proportions_match', jsonb_build_object(
                        'type', 'boolean',
                        'description', 'Whether product widths match shelf space',
                        'required', true
                    ),
                    'gaps_match', jsonb_build_object(
                        'type', 'boolean',
                        'description', 'Whether empty spaces are correctly placed',
                        'required', true
                    ),
                    'visual_mismatches', jsonb_build_object(
                        'type', 'array',
                        'description', 'List of specific visual mismatches found',
                        'required', true,
                        'items', jsonb_build_object(
                            'type', 'object',
                            'properties', jsonb_build_object(
                                'issue_type', jsonb_build_object(
                                    'type', 'string',
                                    'description', 'Type of mismatch',
                                    'enum', jsonb_build_array('wrong_shelf', 'missing_product', 'extra_product', 'wrong_position', 'wrong_size', 'missing_gap', 'extra_gap')
                                ),
                                'description', jsonb_build_object(
                                    'type', 'string',
                                    'description', 'Detailed description of the issue'
                                ),
                                'shelf_number', jsonb_build_object(
                                    'type', 'integer',
                                    'description', 'Which shelf has the issue'
                                ),
                                'position', jsonb_build_object(
                                    'type', 'integer',
                                    'description', 'Position on shelf where issue occurs'
                                )
                            ),
                            'required', jsonb_build_array('issue_type', 'description')
                        )
                    ),
                    'suggested_fixes', jsonb_build_object(
                        'type', 'string',
                        'description', 'Specific corrections to improve accuracy',
                        'required', true
                    ),
                    'confidence', jsonb_build_object(
                        'type', 'string',
                        'description', 'Confidence in comparison results',
                        'required', true,
                        'enum', jsonb_build_array('HIGH', 'MEDIUM', 'LOW')
                    )
                ),
                'required', jsonb_build_array('overall_accuracy', 'shelf_count_match', 'product_presence_match', 'positioning_match', 'proportions_match', 'gaps_match', 'visual_mismatches', 'suggested_fixes', 'confidence')
            )
        ),
        'required', jsonb_build_array('comparison_results')
    ),
    'validation',
    'initial',
    true,
    '1.0',
    0.90,
    120
);

-- ORCHESTRATOR PROMPTS (these don't have field definitions as they're system prompts)
INSERT INTO prompt_templates (
    template_id,
    name,
    description,
    prompt_template,
    field_definitions,
    stage_type,
    prompt_type,
    is_active,
    version
) VALUES 
(
    'master_orchestrator_v1',
    'Master Orchestrator',
    'Guide the extraction pipeline with user priorities',
    'Guide the extraction pipeline with these priorities:

{USER_PRIORITIES}

Examples:
- "Prioritize accuracy over cost for alcohol products"
- "Use faster models after 3 iterations"
- "Focus on price accuracy for promotional items"
- "Stop if accuracy plateaus for 2 iterations"
- "Premium spirits need 95%+ accuracy"',
    NULL,
    'orchestration',
    'system',
    true,
    '1.0'
),
(
    'extraction_orchestrator_v1',
    'Extraction Orchestrator',
    'Apply extraction guidelines',
    'Apply these extraction guidelines:

{USER_GUIDELINES}

Examples:
- "Pay extra attention to promotional pricing"
- "Beverage shelves often have security devices"
- "This store uses digital price tags"
- "Products are tightly packed on bottom shelves"
- "Watch for multipack vs single unit confusion"',
    NULL,
    'orchestration',
    'system',
    true,
    '1.0'
);

-- Verify the results
SELECT 
    template_id,
    name,
    stage_type,
    prompt_type,
    CASE 
        WHEN field_definitions IS NULL THEN 'No schema'
        ELSE jsonb_pretty(field_definitions)
    END as schema_preview
FROM prompt_templates
ORDER BY 
    CASE stage_type
        WHEN 'structure' THEN 1
        WHEN 'products' THEN 2
        WHEN 'details' THEN 3
        WHEN 'validation' THEN 4
        WHEN 'orchestration' THEN 5
    END,
    prompt_type;