# Field Verification Report: Database vs EXTRACTION_PROMPTS_FINAL.md

## Summary of Discrepancies

### 1. Structure v1
**Status**: ✅ MOSTLY CORRECT (with duplicates)

The database appears to have TWO entries for Structure v1:
1. First entry: Missing root wrapper `structure_extraction`
2. Second entry: Has correct structure with `structure_extraction` wrapper

**Issues in first entry**:
- ❌ Missing root object `structure_extraction` - fields start directly with `shelf_structure`
- ❌ Missing `allowed_values` for `sections_with_gaps` literal field
- ❌ Wrong required flags on nested object fields (type, location, text_visible should be required)

**Second entry appears correct** with proper nesting.

### 2. Product v1 
**Status**: ❌ MISSING ROOT WRAPPER

**Major Issue**:
- ❌ Missing root object `product_extraction` - fields start directly with `fixture_id`, `total_shelves`, `shelves`

**Minor Issues**:
- ❌ Missing `extraction_notes` field in shelf objects
- ❌ Missing `estimated_product_spaces` field in gaps objects
- ✅ All other fields are correctly structured

### 3. Detail v1
**Status**: ✅ COMPLETE AND CORRECT (with duplicates)

The database has TWO entries for Detail v1:
1. First entry: Missing root wrapper and many fields
2. Second entry: Complete with all fields

**Second entry is perfect** with:
- ✅ All pricing fields including new ones (price_tag_location, price_attribution_confidence, etc.)
- ✅ All package_info fields including new ones (size_read_location, size_read_confidence, etc.)  
- ✅ Physical characteristics fields with dimension_confidence
- ✅ Visual fields with finish enum
- ✅ Quality fields with issues array

**First entry is incomplete** - missing root wrapper and many detail fields.

### 4. Visual v1
**Status**: ❌ WRONG STRUCTURE

The database has TWO very different structures for Visual v1:

**First entry** (incorrect):
- Has fields: match_confidence, matched_products, unmatched_products, discrepancies
- This appears to be an old/different schema

**Second entry** (also incorrect):
- Has `planogram_layout` and `comparison_results` structure
- This is for planogram generation, NOT the visual comparison from EXTRACTION_PROMPTS_FINAL.md

**Expected structure** should be:
```
visual_comparison (object)
  - overview (object)
    - total_products_photo (integer)
    - total_products_planogram (integer) 
    - overall_alignment (literal: good/moderate/poor)
  - shelf_mismatches (list)
    - product, issue_type, photo_location, planogram_location, confidence, details
  - critical_issues (list of strings)
```

## Recommended Actions

1. **Remove duplicate entries** - Each prompt type should have only one entry

2. **Fix Product v1**: Add root wrapper
   ```json
   {
     "name": "product_extraction",
     "type": "object",
     "description": "Complete product extraction for ALL shelves in the fixture",
     "required": true,
     "nested_fields": [/* current fields */]
   }
   ```

3. **Fix Visual v1**: Replace with correct comparison structure from EXTRACTION_PROMPTS_FINAL.md

4. **Add missing fields**:
   - Product v1: `extraction_notes` and `estimated_product_spaces`
   - Structure v1: Fix required flags on nested fields

5. **Keep the correct entries**:
   - Structure v1: Keep the second entry (with structure_extraction wrapper)
   - Detail v1: Keep the second entry (complete with all fields)

## Database Inconsistencies Found

- Multiple entries for same prompt types (structure and detail have 2 entries each)
- Visual v1 has wrong schema entirely (planogram generation instead of comparison)
- Product v1 missing root wrapper that other stages have
- Some enum fields stored as "enum" type, others as "literal" type (should be consistent)