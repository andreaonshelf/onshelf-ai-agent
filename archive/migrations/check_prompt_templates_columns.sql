-- Check if prompt_templates table exists and show its columns
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM 
    information_schema.columns
WHERE 
    table_name = 'prompt_templates'
ORDER BY 
    ordinal_position;

-- If the above returns nothing, check if the table exists at all
SELECT 
    table_name 
FROM 
    information_schema.tables 
WHERE 
    table_name = 'prompt_templates';

-- Also check if there's an older version with different column names
SELECT 
    c.column_name,
    c.data_type,
    t.table_name
FROM 
    information_schema.columns c
JOIN 
    information_schema.tables t ON c.table_name = t.table_name
WHERE 
    c.column_name IN ('prompt_text', 'prompt_content')
    AND t.table_schema = 'public'
ORDER BY 
    t.table_name, c.column_name;