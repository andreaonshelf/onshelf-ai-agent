-- Check existing constraints on prompt_templates
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conrelid = 'prompt_templates'::regclass
ORDER BY conname;

-- Check which columns have unique constraints
SELECT 
    a.attname as column_name,
    i.indisunique as is_unique,
    i.indisprimary as is_primary
FROM pg_index i
JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
WHERE i.indrelid = 'prompt_templates'::regclass
AND (i.indisunique = true OR i.indisprimary = true);

-- Since there's no unique constraint on template_id, let's insert without ON CONFLICT
-- Or we can add a unique constraint on template_id first

-- Option 1: Add unique constraint on template_id
ALTER TABLE prompt_templates 
ADD CONSTRAINT prompt_templates_template_id_unique 
UNIQUE(template_id);

-- Now we can insert with ON CONFLICT