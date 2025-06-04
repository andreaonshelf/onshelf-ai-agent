# Pydantic Schema Alignment Summary

## Current Situation

The `prompt_templates` table in the database currently has:
- A `fields` column containing custom field definitions in a proprietary format
- NO `field_schema` column (which the code expects to contain JSON Schema format)

## The Mismatch

1. **Database has**: `fields` column with custom format like:
   ```json
   [
     {
       "name": "structure_extraction",
       "type": "object",
       "description": "Complete shelf structure analysis",
       "required": true,
       "nested_fields": [...]
     }
   ]
   ```

2. **Code expects**: `field_schema` column with standard JSON Schema format like:
   ```json
   {
     "type": "object",
     "properties": {
       "structure_extraction": {
         "type": "object",
         "description": "Complete shelf structure analysis",
         "properties": {...},
         "required": [...]
       }
     },
     "required": ["structure_extraction"]
   }
   ```

## Required Actions

### Option 1: Add field_schema column (Recommended)
1. Add the `field_schema` column to the database:
   ```sql
   ALTER TABLE prompt_templates ADD COLUMN IF NOT EXISTS field_schema JSONB;
   ```

2. Run the conversion script I created (`update_field_schemas.sql`) which converts all existing `fields` data to proper JSON Schema format and populates the new column.

3. The code will then work as expected with the JSON Schema format.

### Option 2: Update the code to use existing fields column
1. Modify the extraction engine and related code to work with the custom `fields` format
2. Update the field schema builder to convert from custom format to Pydantic models on the fly

## Files Created

1. **`convert_fields_to_schema.py`** - Python script that:
   - Reads existing `fields` data
   - Converts to JSON Schema format
   - Generates SQL update statements

2. **`update_field_schemas.sql`** - SQL file containing:
   - DDL to add `field_schema` column
   - UPDATE statements to populate it with converted data

## Next Steps

To implement Option 1 (recommended):
1. Execute the SQL file directly in your Supabase dashboard:
   - Go to your Supabase project
   - Navigate to SQL Editor
   - Copy and paste the contents of `update_field_schemas.sql`
   - Execute the script

2. Once the column is added and populated, the schema alignment will be complete.

## Verification

After running the SQL updates, you can verify with:
```sql
SELECT 
    name,
    jsonb_typeof(field_schema) as schema_type,
    jsonb_array_length(jsonb_path_query_array(field_schema, '$.properties.*')) as property_count
FROM prompt_templates
WHERE field_schema IS NOT NULL;
```

This should show all prompts with their JSON Schema properly populated.