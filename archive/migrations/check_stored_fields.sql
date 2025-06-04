-- Check what fields were actually stored for structure extraction
SELECT 
    template_id,
    name,
    jsonb_pretty(fields) as fields_formatted
FROM prompt_templates
WHERE template_id = 'structure_extraction_standard_v2';