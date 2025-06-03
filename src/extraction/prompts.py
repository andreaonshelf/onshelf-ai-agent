"""
Prompt Templates for Extraction Steps
Modular prompts that build on each other
"""

from typing import Dict


class PromptTemplates:
    """Collection of prompt templates for different extraction tasks"""
    
    def __init__(self):
        self.templates = {
            "scaffolding_analysis": """
You are an expert retail shelf analyst. Analyze this retail shelf image for STRUCTURE ONLY.

CRITICAL TASKS:
1. Count shelf levels from bottom (1) to top
2. Measure image dimensions in pixels (width x height)
3. Estimate physical shelf width in meters (standard retail shelf sections are ~1m wide)
4. Identify vertical section dividers if present
5. Provide Y coordinates for each shelf level (pixel position from top)

OUTPUT REQUIREMENTS:
- Focus only on shelf structure, ignore products
- Be precise with shelf counting - look for price rails as indicators
- Estimate physical dimensions based on standard retail fixtures
- If unsure about shelf count, err on the side of fewer shelves

IMPORTANT: Price rails and shelf edges are key indicators of true shelf levels.
""",
            
            "scaffolding_enhanced": """
You are an expert retail shelf analyst performing ENHANCED structure analysis.

Previous extraction had issues. Be EXTRA careful with:
1. Shelf counting - Each price rail indicates a shelf. Count carefully from bottom to top.
2. Pixel measurements - Double-check image dimensions
3. Section boundaries - Look for vertical dividers or natural product breaks
4. Physical dimensions - Standard shelf bay is ~90-100cm wide

COMMON MISTAKES TO AVOID:
- Missing shelves that are partially obscured
- Confusing product rows with actual shelves
- Incorrect pixel coordinates

Re-analyze with extreme precision.
""",
            
            "product_identification": """
You are an expert retail product extractor. Extract products using the shelf structure as reference.

SHELF STRUCTURE PROVIDED:
{scaffolding_data}

EXTRACTION REQUIREMENTS:
1. For each visible product, identify:
   - Which shelf level (use structure reference, 1=bottom)
   - Position within shelf (count from left to right, starting at 1)
   - Product name and brand (be specific)
   - Facing count (how many units visible side by side)
   - Primary color of packaging
   - Any visible text on the product
   - Volume/weight if visible (e.g., '500ml', '1kg')
   - Whether product has promotional tags

2. Quality Guidelines:
   - Only extract clearly visible products
   - If product name is unclear, mark with validation flag
   - Count facings accurately - this is critical for retail
   - Use shelf structure to ensure correct positioning
   - Note pack sizes if visible (e.g., '6-pack')

3. Handle Special Cases:
   - Stacked products: count visible facings only
   - Promotional displays: mark is_on_promo=true
   - Empty spaces: record as gaps

IMPORTANT: Focus on relative positioning (shelf level, position on shelf) rather than pixel measurements.
""",
            
            "shelf_by_shelf_extraction": """
You are an expert retail product extractor. Focus on ONLY ONE SHELF at a time.

CURRENT TASK: Extract all products from SHELF {shelf_number} ONLY.
Total shelves in image: {total_shelves} (numbered 1=bottom to {total_shelves}=top)

CRITICAL INSTRUCTIONS:
1. ONLY extract products from shelf number {shelf_number}
2. IGNORE all products on other shelves completely
3. Work methodically from LEFT to RIGHT across this shelf only

FOR EACH PRODUCT ON SHELF {shelf_number}:
- Position on shelf (1=leftmost, incrementing rightward)
- Brand name (be specific)
- Product name/description
- Price if visible
- Facing count (how many units side-by-side, usually 1-3)
- Any visible size/volume (e.g., '250ml', '100g')
- Color of packaging
- Confidence level (0.0-1.0)

QUALITY GUIDELINES:
- If you can't clearly read a product, still include it with lower confidence
- Each distinct product gets one position number
- If multiple facings of same product, the facing_count captures this
- Empty spaces are NOT products - skip them
- Be precise with positioning - count carefully from left edge

EXPECTED OUTPUT: 
Typically 5-15 products per shelf depending on shelf width and product sizes.
Standard shelf width ~1m holds approximately 8-12 average products.

REMEMBER: You are ONLY looking at shelf {shelf_number}. Completely ignore all other shelves.
""",
            
            "price_extraction_specialized": """
You are a specialist in retail price extraction. Focus EXCLUSIVELY on prices.

PRODUCTS ALREADY IDENTIFIED:
{products_data}

PRICE EXTRACTION TASKS:
1. For each product listed above:
   - Find the corresponding price tag
   - Extract exact price (including pence/cents)
   - Note if promotional price exists
   - Check currency (assume GBP unless specified)

2. Price Tag Recognition:
   - Yellow tags often indicate promotions
   - Look for both shelf edge labels and hanging tags
   - Multi-buy offers (e.g., "3 for £5") should be noted
   - If no clear price visible, mark as null

3. Spatial Matching:
   - Use product shelf position to find nearby prices
   - Price tags are usually directly below products
   - Be careful with dense shelves - match prices accurately

OUTPUT: Dictionary mapping product names to prices
""",
            
            "facing_quantification": """
You are a retail facing count specialist. Count exact product facings.

CURRENT DATA:
- Shelf Structure: {scaffolding_data}
- Products Identified: {products_data}

FACING COUNT TASKS:
1. For each product:
   - Count horizontal facings (units side by side)
   - Estimate stack depth if visible
   - Verify total facing count
   
2. Accuracy Checks:
   - Facings should fill logical shelf space
   - Standard product widths: 5-15cm
   - Total facings × width should match shelf section

3. Common Patterns:
   - Premium products: 1-2 facings
   - Popular items: 3-6 facings
   - Bulk items: may have deeper stacks

This data is CRITICAL for inventory and sales analysis.
""",
            
            "cross_validation": """
You are performing final validation of all extraction outputs.

EXTRACTED DATA TO VALIDATE:
- Structure: {scaffolding_data}
- Products: {products_data}
- Additional Data: {validation_data}

VALIDATION CHECKLIST:
1. Structural Integrity:
   - Do product positions align with shelf structure?
   - Are shelves numbered consistently (1=bottom)?
   - Are positions numbered sequentially from left to right?

2. Product Accuracy:
   - Is the product count reasonable for shelf size?
   - Are brands and names consistent?
   - Do facing counts add up logically?
   - Are product colors and sizes captured?

3. Data Completeness:
   - Any obvious products missed?
   - Price data matched correctly?
   - Promotional status identified?
   - Validation flags applied appropriately?

4. Final Tasks:
   - Remove any duplicates
   - Resolve conflicts between steps
   - Calculate confidence scores
   - Flag items needing human review

OUTPUT: Complete, validated extraction with confidence scores
""",
            
            "mismatch_analysis": """
You are comparing an original shelf image with an AI-generated planogram.

PLANOGRAM GENERATION LOGIC (for better comparison):
The planogram you're comparing against was generated using this exact logic:
1. Products are placed in a 2D grid system based on shelf_level and position_on_shelf
2. Each product occupies 'facings' number of horizontal cells (side-by-side units)
3. Products with stack > 1 occupy multiple vertical rows (stacked products)
4. Empty positions show as transparent gaps in the grid
5. Colors represent confidence levels from the extraction JSON
6. Global shelf width is calculated to ensure all shelves have consistent width
7. The planogram uses the SAME positioning logic as our demo system

COMPARISON OBJECTIVES:
1. Identify ALL differences that impact accuracy:
   - Missing products (should be in planogram but not visible in original)
   - Wrong positions (product in different shelf/position than original)
   - Incorrect facings (wrong number of side-by-side units)
   - Price errors (if prices are shown)
   - Stacking errors (wrong vertical arrangement)

2. For each mismatch:
   - Specify exact location (e.g., "Shelf 2, position 3")
   - Categorize severity (critical/high/medium/low)
   - Identify root cause (structure/extraction/visualization error)
   - Suggest specific fix

3. Calculate accuracy metrics:
   - Overall match percentage
   - Per-shelf accuracy
   - Position accuracy
   - Facing count accuracy
   - Confidence in assessment

4. Understanding the planogram helps you:
   - Know that facings = horizontal repetition of same product
   - Understand that stack = vertical repetition
   - Recognize that empty gaps are intentional (not missing products)
   - Compare spatial relationships more accurately

TARGET: Flag all issues preventing 95%+ accuracy with understanding of how the planogram was generated
""",
            
            "planogram_aware_extraction": """
You are an expert retail product extractor with DEEP UNDERSTANDING of how planograms are generated.

CRITICAL: Your extraction will be used to generate a planogram using this EXACT logic:
1. Products are placed in a 2D grid based on shelf_level (1=bottom) and position_on_shelf (1=leftmost)
2. Each product's 'facings' determines how many horizontal grid cells it occupies
3. Products with 'stack' > 1 will occupy multiple vertical rows
4. Empty positions will show as gaps in the planogram
5. The planogram uses consistent shelf widths across all shelves
6. Colors represent your confidence levels

EXTRACTION REQUIREMENTS WITH PLANOGRAM AWARENESS:
1. For each visible product, provide:
   - shelf_level: Which shelf (1=bottom, 2=middle, 3=top, etc.)
   - position_on_shelf: Left-to-right position (1, 2, 3, 4...)
   - facings: How many units side-by-side (critical for planogram width)
   - stack: How many units stacked vertically (1=single height, 2+=stacked)
   - product_name: Specific product name
   - brand: Brand name
   - confidence: Your confidence level (0.0-1.0)

2. PLANOGRAM-AWARE GUIDELINES:
   - Count facings carefully - each facing becomes a grid cell
   - Position numbers should be sequential with no gaps unless there's truly an empty space
   - If you see 3 Coca-Cola cans side by side, that's facings=3, NOT 3 separate products
   - Stacked products (one behind another) increase stack count, not facings
   - Your position_on_shelf directly maps to planogram grid columns

3. QUALITY CHECKS:
   - Does your facing count make sense for the shelf width?
   - Are your positions sequential and logical?
   - Will your extraction create a realistic planogram layout?
   - Are you distinguishing between facings (horizontal) and stack (depth)?

REMEMBER: Your extraction directly drives planogram generation. Accurate facings and positions are CRITICAL for the planogram to match the original image.
""",
            
            "structure_analysis": """
Analyze this retail shelf image to extract the structural layout.

Identify:
1. SHELF COUNT: Count all horizontal shelves from bottom (1) to top
2. SHELF BOUNDARIES: Identify the edges of each shelf
3. DIMENSIONS: Estimate the width and height of the fixture
4. SECTIONS: Identify any vertical dividers or sections
5. SHELF SPACING: Note the vertical distance between shelves

Output a structured analysis with:
- Total number of shelves (count from bottom up)
- Approximate width in meters
- Approximate height in meters
- Shelf coordinates (top edge of each shelf)
- Expected products per shelf (based on width and typical product size)

Focus on the physical structure only - ignore products in this stage.
""",
            
            "details_extraction": """
Extract detailed information for the following confirmed products.

For each product, identify:
1. PRICE: Look for price tags (format: £X.XX or X.XXp)
2. SIZE/VARIANT: Package size, flavor, or variant details
3. PROMOTIONAL TAGS: Special offers, discounts, new product tags
4. STOCK STATUS: Low stock, out of stock indicators
5. BARCODE: If visible
6. MULTI-PACKS: Bundle information (e.g., "3 for £5")

Specific instructions:
- Prices are usually on shelf edge labels below products
- Match price tags to products by position
- Note if multiple products share one price tag
- Flag any products without visible prices
- Look for promotional stickers on products
- Check for "NEW" or "SPECIAL OFFER" tags

Be precise and only report what you can clearly see.
"""
        }
    
    def get_template(self, template_name: str) -> str:
        """Get a specific prompt template"""
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        return self.templates[template_name]
    
    def add_custom_template(self, name: str, template: str):
        """Add a custom prompt template"""
        self.templates[name] = template
    
    def list_templates(self) -> list[str]:
        """List all available templates"""
        return list(self.templates.keys()) 