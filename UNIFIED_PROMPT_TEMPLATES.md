# Unified Prompt Templates with Retry Sections

## Structure Extraction Prompt Template

```
=== INITIAL EXTRACTION ===
Analyze this retail shelf image to identify the physical shelf structure.

COUNT AND DESCRIBE:
1. Number of shelves: Count each level from bottom (1) to top
2. Fixture measurements: Width and height in meters
3. Fixture type: wall_shelf | gondola | end_cap | cooler | other
4. For each shelf: Note price rails and unusual features

Be precise with shelf count - this determines product organization.

=== RETRY EXTRACTION (IF CONFIDENCE < 0.8) ===
Re-analyze the shelf structure focusing on problem areas.

PREVIOUS FOUND: {shelf_count} shelves, {width}m wide
ISSUES: {confidence_issues}

FOCUS ON:
- {specific_issue_1}
- {specific_issue_2}

Double-check shelf edges and price rails carefully.
```

## Products Extraction Prompt Template

```
=== INITIAL EXTRACTION ===
Extract products from shelf {shelf_number} of {total_shelves}.

For each product identify:
- Position (1, 2, 3... left to right)
- Brand and product name
- Facing count (units visible from front)
- Section: Left | Center | Right

=== RETRY EXTRACTION (IF NEEDED) ===
Re-examine shelf {shelf_number} to improve extraction.

CONFIRMED PRODUCTS (keep these):
{high_confidence_products}

PROBLEM AREAS:
{low_confidence_positions}

SPECIFIC FOCUS:
- Check {problem_area_1} for missed products
- Verify facing count for {uncertain_product}
- Look behind {obstruction} if visible
```

## Details Enhancement Prompt Template

```
=== INITIAL EXTRACTION ===
Add details for: {brand} {name} at position {position}

Extract:
- Price (check shelf edge labels)
- Size/Volume (e.g., "330ml")
- Package color
- Confidence level

=== RETRY EXTRACTION (IF INCOMPLETE) ===
Re-examine product details.

ALREADY FOUND: {existing_details}
STILL MISSING: {missing_attributes}

LOOK SPECIFICALLY:
- {where_to_find_price}
- {size_verification_tip}
```