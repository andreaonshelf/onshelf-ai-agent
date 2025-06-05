# OnShelf AI Extraction Prompts - Refined Complete Set

## STAGE 1: STRUCTURE EXTRACTION

### Extraction Prompt:
```
Analyze this retail shelf image to identify the physical structure.

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
{/IF_RETRY}
```

### Instructor Fields (UI Schema Builder):

**structure_extraction** (Object - nested) ✓ Required
- Description: Complete shelf structure analysis

Nested fields within structure_extraction:
- **shelf_structure** (Object - nested) ✓ Required
  - Description: Physical structure of the shelf fixture
  - Nested fields:
    - **total_shelves** (Number - integer) ✓ Required
      - Description: Total number of horizontal shelves
    - **fixture_id** (Text - string) ✓ Required
      - Description: Unique identifier for this shelf fixture (e.g., "store123_aisle5_bay2")
    - **shelf_numbers** (List - array) ✓ Required
      - Description: List of shelf numbers from bottom to top (must have length = total_shelves)
      - Example: [1, 2, 3] for 3 shelves
    - **shelf_type** (Literal["wall_shelf", "gondola", "end_cap", "cooler", "freezer", "bin", "pegboard", "other"]) ✓ Required
      - Description: Type of fixture
    - **width_meters** (Decimal - float) ✓ Required
      - Description: Estimated width of fixture in meters
    - **height_meters** (Decimal - float) ✓ Required
      - Description: Estimated height of fixture in meters
    - **shelves** (List - array) ✓ Required
      - Description: Detailed information for each shelf level
      - Array item type: Object (nested) with fields:
        - **shelf_number** (Number - integer) ✓ Required
          - Description: Shelf identifier (1=bottom, counting up)
        - **has_price_rail** (Yes/No - boolean) ✓ Required
          - Description: Whether shelf has price label strip/rail
        - **special_features** (Text - string) ☐ Optional
          - Description: Unusual characteristics (slanted, wire mesh, divided sections, damaged)
        - **has_empty_spaces** (Yes/No - boolean) ✓ Required
          - Description: Whether significant gaps exist on this shelf
        - **empty_space_details** (Object - nested) ☐ Optional when has_empty_spaces=true
          - Description: Details about empty spaces
          - Nested fields:
            - **sections_with_gaps** (List - array) ✓ Required
              - Array item type: Literal["left", "center", "right"]
            - **estimated_total_gap_cm** (Decimal - float) ✓ Required
              - Description: Total empty space in centimeters
    - **non_product_elements** (Object - nested) ✓ Required
      - Description: Items on shelves that are not products
      - Nested fields:
        - **security_devices** (List - array) ☐ Optional
          - Description: Security measures (grids, magnetic tags, plastic cases, bottle locks)
          - Array item type: Object with:
            - **type** (Text - string) - Type of security device
            - **location** (Text - string) - Where on shelf it's located
        - **promotional_materials** (List - array) ☐ Optional
          - Description: Marketing materials (shelf wobblers, hanging signs, price cards, banners)
          - Array item type: Object with:
            - **type** (Text - string) - Type of promotional material
            - **location** (Text - string) - Where positioned
            - **text_visible** (Text - string) - Any readable promotional text
        - **shelf_equipment** (List - array) ☐ Optional
          - Description: Shelf organization tools (dividers, pushers, price rails, shelf strips)
          - Array item type: Object with:
            - **type** (Text - string) - Type of equipment
            - **location** (Text - string) - Where installed

---

## STAGE 2: PRODUCT EXTRACTION

### Extraction Prompt:
```
STAGE 2: PRODUCT EXTRACTION

Analyze this retail shelf image to identify the products present on the shelf. 

We have already identified that {TOTAL_SHELVES} horizontal shelves exist, numbered from bottom (1) to top ({TOTAL_SHELVES}).

WHAT YOU'RE BUILDING:
You are extracting product data that will be converted into a planogram. A planogram is a visual diagram showing product placement on shelves - like a map of the shelf. Your data will become a grid where each product facing gets its own cell.

HOW YOUR EXTRACTION BECOMES VISUAL:
- Each product facing (unit visible from front) = one cell in the grid
- Position 1,2,3 = left-to-right order in the planogram
- Gaps in position numbers = empty space in the visual
- Example: If you extract positions 1,2,5, the planogram shows: [Prod1][Prod2][Empty][Empty][Prod5]

EXTRACT:
1. Scan left to right, identify each distinct product
2. Count facings (units visible from front only)
3. Number products sequentially: 1, 2, 3, 4... (continuous numbering)
4. Track significant gaps between products separately (will be recorded in gaps array)
5. Note section: Left | Center | Right (divide shelf in thirds)

CRITICAL: Missing positions create gaps in the planogram. Only skip numbers if there's actual empty space on the shelf.

HANDLE THESE SITUATIONS:
- Shelf completely blocked: Mark extraction_status as "blocked"
- Shelf not visible: Mark extraction_status as "not_visible"
- Products knocked over/pile: Note in extraction_notes
- Bottom shelf cut off: Extract visible shelves only

{IF_RETRY}
PREVIOUS FOUND ON THIS SHELF:
{PREVIOUS_SHELF_PRODUCTS}

VISUAL FEEDBACK:
{PLANOGRAM_FEEDBACK}
Example: "Shelf looks too sparse - check for missed products"

NOTE: Trust what you see. Add/correct products as needed.
You can disagree with the previous extraction completely.
{/IF_RETRY}
```

### Instructor Fields (UI Schema Builder):

**product_extraction** (Object - nested) ✓ Required
- Description: Complete product extraction for ALL shelves in the fixture

Nested fields within product_extraction:
- **fixture_id** (Text - string) ✓ Required
  - Description: Unique identifier for this extraction (e.g., "store123_aisle5_bay2")
  
- **total_shelves** (Number - integer) ✓ Required
  - Description: Total number of shelves being extracted (MUST equal {TOTAL_SHELVES} from Stage 1)
  - Min: 1, Max: 10
  
- **shelves** (List - array) ✓ Required
  - Description: Product data for each shelf (MUST have exactly total_shelves entries)
  - VALIDATION: Array length MUST equal total_shelves value
  - Array item type: Object (nested) with fields:
    
    - **shelf_number** (Number - integer) ✓ Required
      - Description: Which shelf this is (MUST match position in array + 1)
      - Min: 1
      
    - **extraction_status** (Literal["has_products", "empty_shelf", "not_visible", "blocked"]) ✓ Required
      - Description: Status of this shelf extraction
      
    - **products** (List - array) ✓ Required when extraction_status="has_products"
      - Description: All products found on this specific shelf
      - Array item type: Object (nested) with fields:
        - **position** (Number - integer) ✓ Required
          - Description: Sequential position from left to right on THIS shelf
          - Min: 1
        - **section** (Literal["left", "center", "right"]) ✓ Required
          - Description: Which third of the shelf this product is in
        - **brand** (Text - string) ✓ Required
          - Description: Product brand name
        - **name** (Text - string) ✓ Required
          - Description: Product name or variant
        - **product_type** (Literal["can", "bottle", "box", "pouch", "jar", "other"]) ✓ Required
          - Description: Package type
        - **facings** (Number - integer) ✓ Required
          - Description: Number of units visible from front
          - Min: 1, Max: 20
        - **stack** (Number - integer) ✓ Required
          - Description: Number of units stacked vertically
          - Min: 1, Max: 5

    - **gaps** (List - array) ☐ Optional
      - Description: Empty spaces between products on this shelf
      - Array item type: Object with fields:
        - **after_position** (Number - integer) ✓ Required
          - Description: Gap appears after this position number
        - **gap_size** (Literal["small", "medium", "large"]) ✓ Required
          - Description: Approximate size of the gap
        - **estimated_product_spaces** (Number - integer) ✓ Required
          - Description: How many products could fit in this gap
          - Min: 1, Max: 10

    - **extraction_notes** (Text - string) ☐ Optional
      - Description: Any issues or observations about this shelf (e.g., "products fallen over", "heavy shadows on right side")

---

## STAGE 3: DETAIL ENHANCEMENT

### Extraction Prompt:
```
STAGE 3: DETAIL ENHANCEMENT

Look at this retail shelf image.

We have already identified and located these products:

{COMPLETE_PRODUCT_LIST}
Example format:
=== FIXTURE: store123_aisle5_bay2 ===
Total Shelves: 3

SHELF 1 (Bottom):
- Product 1: Coca-Cola Zero (6 facings) - Left section
- Product 2: [Gap - 2 product spaces]
- Product 3: Pepsi Max (4 facings) - Center section
- Product 4: Fanta Orange (3 facings) - Center section

SHELF 2:
- Product 1: Budweiser (8 facings) - Left section
- Product 2: Heineken (6 facings) - Center section

SHELF 3 (Top):
[Empty shelf - no products]

YOUR TASK:
Add details to EACH product above IN ORDER. You cannot skip, add, or remove products.

For each product, find it in the image and extract:

PRICING (check shelf edge labels):
□ Regular price: £_____ 
□ Price tag location: directly_below | left_of_product | right_of_product | distant | not_visible
□ Confidence this price belongs to THIS product: certain | likely | uncertain
□ If uncertain, which product might this price belong to: _____
□ Promotional price: £_____ (if different)
□ Promotion text: _____ (e.g., "3 for £5")
□ Currency: GBP | EUR | USD | other

VERIFICATION NOTES:
- If price tag is between two products, note which product it's closer to
- If no direct price visible, note where you looked
- Multi-packs often share one price tag for the group

PACKAGE DETAILS (read from product):
□ Package size: _____ (e.g., "330ml", "750ml", "6-pack")
□ Size location on package: front_label | side_visible | cap/lid | not_visible
□ Confidence in size reading: certain | likely | uncertain
□ If multipack: unit size and count
□ Multiple units visible: Yes/No (helps verify if truly multipack)
□ Total volume: _____ (e.g., "6 × 330ml = 1,980ml")

PHYSICAL CHARACTERISTICS:
□ Width relative to neighbors: narrow | normal | wide
□ Height relative to shelf: short | medium | tall
□ Estimated dimensions: width ___cm, height ___cm

VISUAL APPEARANCE:
□ Primary color: _____ (most dominant)
□ Secondary color: _____ (second most prominent)
□ Package finish: metallic | matte | glossy | transparent

EXTRACTION QUALITY:
□ Visibility: clearly_visible | partially_obscured | mostly_hidden
□ Confidence: high | medium | low
□ Issues: _____ (e.g., "price tag torn")

Process EVERY product systematically.

{IF_RETRY}
PREVIOUS ATTEMPT RESULTS:
{PREVIOUS_DETAILS_BY_PRODUCT}

Issues identified:
- Missing details for: {INCOMPLETE_PRODUCTS}
- Low confidence items: {LOW_CONFIDENCE_PRODUCTS}

Fill in missing information and verify previous extractions.
{/IF_RETRY}
```

### Instructor Fields (UI Schema Builder):

**detail_enhancement** (Object - nested) ✓ Required
- Description: Enhanced details for ALL products from Stage 2, maintaining exact structure

Nested fields within detail_enhancement:
- **fixture_id** (Text - string) ✓ Required
  - Description: Must match Stage 2's fixture_id exactly
  
- **total_shelves** (Number - integer) ✓ Required
  - Description: Must match Stage 2's total_shelves exactly
  
- **shelves_enhanced** (List - array) ✓ Required
  - Description: Enhanced details for each shelf (MUST have same length as Stage 2's shelves array)
  - Array item type: Object (nested) with fields:
    
    - **shelf_number** (Number - integer) ✓ Required
      - Description: Must match Stage 2's shelf_number for this array position
      
    - **products_enhanced** (List - array) ☐ Optional
      - Description: Required only when Stage 2's extraction_status="has_products". When shelf was empty, this array should be omitted or empty
      - Array item type: Object (nested) with fields:
        
        - **product_reference** (Object - nested) ✓ Required
          - Description: Identifies which Stage 2 product this enhances
          - Nested fields:
            - **shelf_index** (Number - integer) ✓ Required
              - Description: Index in Stage 2's shelves array (0-based)
            - **product_index** (Number - integer) ✓ Required
              - Description: Index in that shelf's products array (0-based)
            - **position** (Number - integer) ✓ Required
              - Description: Position from Stage 2 (for validation)
            - **brand** (Text - string) ✓ Required
              - Description: Brand from Stage 2 (for validation)
            - **name** (Text - string) ✓ Required
              - Description: Name from Stage 2 (for validation)
        
        - **pricing** (Object - nested) ✓ Required:
          - Description: Price information
          - **regular_price** (Decimal - float) ☐ Optional
            - Min: 0, Max: 1000
          - **promotional_price** (Decimal - float) ☐ Optional
            - Min: 0, Max: 1000
          - **promotion_text** (Text - string) ☐ Optional
          - **currency** (Literal["GBP", "EUR", "USD", "other"]) ✓ Required
          - **price_visible** (Yes/No - boolean) ✓ Required
          - **price_not_visible_reason** (Text - string) ☐ Optional
            - Description: Why price couldn't be extracted (only fill if price_visible is false)
          - **price_tag_location** (Literal["directly_below", "left_of_product", "right_of_product", "distant", "not_visible"]) ✓ Required
            - Description: Where the price tag is positioned relative to this product
          - **price_attribution_confidence** (Literal["certain", "likely", "uncertain"]) ✓ Required
            - Description: How confident that this price belongs to this specific product
          - **possible_price_owner** (Text - string) ☐ Optional
            - Description: If uncertain, which nearby product might this price actually belong to
        
        - **package_info** (Object - nested) ✓ Required:
          - Description: Package details
          - **size** (Text - string) ☐ Optional
          - **unit_count** (Number - integer) ☐ Optional
          - **unit_size** (Text - string) ☐ Optional
          - **total_volume** (Text - string) ☐ Optional
          - **size_visible** (Yes/No - boolean) ✓ Required
          - **size_not_visible_reason** (Text - string) ☐ Optional
            - Description: Why size couldn't be read (only fill if size_visible is false)
          - **size_read_location** (Literal["front_label", "side_visible", "cap_lid", "not_visible"]) ✓ Required
            - Description: Where on the package the size information was read from
          - **size_read_confidence** (Literal["certain", "likely", "uncertain"]) ✓ Required
            - Description: Confidence in the size reading accuracy
          - **multiple_units_visible** (Yes/No - boolean) ✓ Required
            - Description: Can you see multiple individual units (helps verify multipack claims)
        
        - **physical** (Object - nested) ✓ Required:
          - Description: Physical characteristics
          - **width_relative** (Literal["narrow", "normal", "wide"]) ✓ Required
          - **height_relative** (Literal["short", "medium", "tall"]) ✓ Required
          - **width_cm** (Decimal - float) ✓ Required
            - Min: 1, Max: 100
          - **height_cm** (Decimal - float) ✓ Required
            - Min: 1, Max: 50
          - **dimension_confidence** (Literal["measured", "estimated", "rough_guess"]) ✓ Required
            - Description: Confidence in dimension estimates
        
        - **visual** (Object - nested) ✓ Required:
          - Description: Visual appearance
          - **primary_color** (Text - string) ✓ Required
          - **secondary_color** (Text - string) ✓ Required
          - **finish** (Literal["metallic", "matte", "glossy", "transparent", "mixed"]) ✓ Required
        
        - **quality** (Object - nested) ✓ Required:
          - Description: Extraction quality
          - **visibility** (Literal["clearly_visible", "partially_obscured", "mostly_hidden"]) ✓ Required
          - **confidence** (Literal["high", "medium", "low"]) ✓ Required
          - **issues** (List - array) ☐ Optional

---

## VISUAL COMPARISON

### Comparison Prompt:
```
Compare the original shelf photo with the generated planogram visualization.

CHECK THESE SPECIFIC THINGS:

1. SHELF ASSIGNMENT: Do all products appear on the correct shelf?
   - List any products that are on a different shelf in the photo vs planogram
   
2. QUANTITY CHECK: Are the facing counts roughly correct?
   - List any products where quantity is significantly off (±3 or more)
   
3. POSITION CHECK: Are products in the right general area of each shelf?
   - List any products that are in wrong section (left/center/right)
   
4. MISSING PRODUCTS: Any obvious products in photo but not in planogram?
   - List only if clearly visible and significant
   
5. EXTRA PRODUCTS: Any products in planogram but not visible in photo?
   - List only if you're confident they're not there

For each issue found, specify:
- What: [Product name]
- Where in photo: [Shelf X, Position Y]
- Where in planogram: [Shelf X, Position Y]
- Confidence: [High/Medium/Low]
```

### Instructor Fields (UI Schema Builder):

**visual_comparison** (Object - nested) ✓ Required
- Description: Comparison between original photo and generated planogram

Nested fields within visual_comparison:
- **overview** (Object - nested) ✓ Required
  - Description: Overall comparison metrics
  - Nested fields:
    - **total_products_photo** (Number - integer) ✓ Required
      - Description: Total products counted in original photo
    - **total_products_planogram** (Number - integer) ✓ Required
      - Description: Total products shown in planogram
    - **overall_alignment** (Literal["good", "moderate", "poor"]) ✓ Required
      - Description: Overall quality assessment

- **shelf_mismatches** (List - array) ☐ Optional
  - Description: Specific products with placement or quantity issues
  - Array item type: Object (nested) with fields:
    - **product** (Text - string) ✓ Required
      - Description: Product name
    - **issue_type** (Literal["wrong_shelf", "wrong_quantity", "wrong_position", "missing", "extra"]) ✓ Required
      - Description: Type of mismatch
    - **photo_location** (Object - nested) ✓ Required
      - Description: Where product appears in photo
      - Nested fields:
        - **shelf** (Number - integer) ✓ Required
          - Description: Shelf number in photo
        - **position** (Number - integer) ✓ Required
          - Description: Position number in photo
    - **planogram_location** (Object - nested) ✓ Required
      - Description: Where product appears in planogram
      - Nested fields:
        - **shelf** (Number - integer) ✓ Required
          - Description: Shelf number in planogram
        - **position** (Number - integer) ✓ Required
          - Description: Position number in planogram
    - **confidence** (Literal["high", "medium", "low"]) ✓ Required
      - Description: Confidence in this mismatch
    - **details** (Text - string) ☐ Optional
      - Description: Additional context about the mismatch

- **critical_issues** (List - array) ☐ Optional
  - Description: Major structural problems
  - Array item type: Text (string)

---

## ORCHESTRATOR PROMPTS

### MASTER ORCHESTRATOR (User Customization)
```
Guide the extraction pipeline with these priorities:

{USER_PRIORITIES}

Examples:
- "Prioritize accuracy over cost for alcohol products"
- "Use faster models after 3 iterations"
- "Focus on price accuracy for promotional items"
- "Stop if accuracy plateaus for 2 iterations"
- "Premium spirits need 95%+ accuracy"
```

### EXTRACTION ORCHESTRATOR (User Guidelines)
```
Apply these extraction guidelines:

{USER_GUIDELINES}

Examples:
- "Pay extra attention to promotional pricing"
- "Beverage shelves often have security devices"
- "This store uses digital price tags"
- "Products are tightly packed on bottom shelves"
- "Watch for multipack vs single unit confusion"
```

---

## USAGE GUIDELINES

### Key Principles
1. **Structure Stage**: Pure shelf counting - no product knowledge needed
2. **Product Stage**: Explain planogram impact to improve position/facing accuracy
3. **Detail Stage**: Enhance locked products with visual attributes, maintain planogram context
4. **Orchestrators**: Use actual performance data and visual feedback

### Planogram Context Distribution
- **Structure Stage**: No planogram context needed
- **Product Stage**: Full planogram explanation
- **Detail Stage**: Light planogram context
- **Extraction Orchestrator**: Full planogram understanding
- **Comparison Agent**: Visual comparison only

### Retry Strategy
- Include FULL original prompt in retry attempts
- Add retry context as additional information
- Make clear that LLM can disagree with previous attempts
- Previous data is reference only, not constraint

### Model Selection (Master Orchestrator)
- Track performance by stage AND product category
- Consider cost vs accuracy improvement
- Stop when improvements < 5% per iteration

### Instructor Integration
- Each stage has clearly defined fields in hierarchical format
- Store both prompt text AND field structure in database
- Maintain consistency across all stages

Remember: The goal is accurate shelf data that creates useful planogram visualizations for retail decision-making.