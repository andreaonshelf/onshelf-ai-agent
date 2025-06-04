-- Check the current structure of prompt_templates table
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns
WHERE table_schema = 'public' 
AND table_name = 'prompt_templates'
ORDER BY ordinal_position;

-- Check if the update trigger function exists
SELECT 
    proname AS function_name,
    pg_get_functiondef(oid) AS function_definition
FROM pg_proc
WHERE proname = 'update_updated_at_column';

-- Check existing triggers on the table
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'prompt_templates';