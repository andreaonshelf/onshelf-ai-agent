# UI Schema Import Guide

## Overview

This guide explains how to import the field definitions from EXTRACTION_PROMPTS_FINAL.md into the UI Schema Builder.

## Generated Files

1. **ui_schema_structure_v1.json** - Structure extraction stage fields
2. **ui_schema_product_v1.json** - Product extraction stage fields  
3. **ui_schema_detail_v1.json** - Detail enhancement stage fields
4. **ui_schema_visual_v1.json** - Visual comparison stage fields
5. **ui_schema_all_stages.json** - All stages combined for reference

## Field Format

Each field follows this exact structure expected by the UI:

```json
{
  "name": "field_name",
  "type": "string|integer|float|boolean|list|object|literal|enum",
  "description": "Field description",
  "required": true/false,
  "nested_fields": [...],  // for object types
  "list_item_type": "string|integer|etc",  // for list types
  "allowed_values": ["value1", "value2"],  // for literal/enum types
  "sort_order": 0
}
```

## Key Conversions Made

1. **Literal Types**: Converted `Literal["value1", "value2"]` to:
   ```json
   {
     "type": "literal",
     "allowed_values": ["value1", "value2"]
   }
   ```

2. **Nested Objects**: Properly structured with `nested_fields` array

3. **List Types**: Include `list_item_type` to specify what the list contains

4. **Min/Max Constraints**: Added to descriptions (e.g., "Min: 1, Max: 10")

5. **Required/Optional**: Converted ✓/☐ notation to boolean `required` field

## How to Import

### Method 1: Manual Copy/Paste

1. Open the dashboard with Schema Builder
2. Click "Import Fields" or similar button
3. Copy the contents of the appropriate JSON file
4. Paste into the import dialog
5. Click Import

### Method 2: Using the Test Page

1. Open `test_ui_schema_import.html` in your browser
2. Select the stage you want
3. Click "Copy JSON for UI Import"
4. Paste into the dashboard's import feature

### Method 3: Browser Console

1. Open the dashboard in your browser
2. Open browser developer console (F12)
3. Load `import_fields_to_ui.js` script
4. Run: `importFieldsForStage('structure_v1')` (or other stage name)

### Method 4: Direct Database Insert

Use the JSON files with your existing database insertion logic to create field definitions.

## Stage-Specific Notes

### Structure v1
- Root field: `structure_extraction`
- Includes shelf counting, fixture details, non-product elements
- Complex nested structure for shelf details

### Product v1
- Root field: `product_extraction`
- MUST maintain consistency with Structure stage (total_shelves)
- Includes product positions, facings, gaps

### Detail v1
- Root field: `detail_enhancement`
- References products from Product stage by index
- Includes pricing, package info, physical characteristics

### Visual v1
- Root field: `visual_comparison`
- Compares photo to planogram
- Tracks mismatches and issues

## Validation Rules

1. **Stage Consistency**: 
   - `fixture_id` must match across stages
   - `total_shelves` must match across stages
   - Array lengths must match declared counts

2. **Position References**:
   - Product stage: positions are sequential per shelf
   - Detail stage: references by shelf_index and product_index

3. **Required Conditional Fields**:
   - Some fields are required only when parent conditions are met
   - Example: `products` array required when `extraction_status="has_products"`

## Troubleshooting

### Fields Not Displaying Correctly
- Ensure `type` field matches UI expectations
- Check that `nested_fields` is an array, not an object
- Verify `sort_order` values for proper ordering

### Literal/Enum Types Not Working
- Must use `type: "literal"` with `allowed_values` array
- Don't use `enum` type - use `literal` instead

### Nested Fields Not Showing
- Parent field must have `type: "object"`
- Include `nested_fields` array with child fields
- Each nested field needs its own complete structure

## Example Usage

```javascript
// Load structure fields
const structureFields = require('./ui_schema_structure_v1.json');

// Insert into database or UI
await insertFieldDefinition({
  stage: 'structure_v1',
  fields: structureFields,
  version: '1.0'
});
```

## Next Steps

1. Import fields for each stage into the UI
2. Test that all nested structures render correctly
3. Verify drag-and-drop reordering works
4. Save configurations with proper field definitions
5. Test extraction with the imported schemas