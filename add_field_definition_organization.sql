-- Add category, sort_order, and parent_field columns to field_definitions table

DO $$
BEGIN
    -- Add category column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'field_definitions' 
        AND column_name = 'category'
    ) THEN
        ALTER TABLE field_definitions 
        ADD COLUMN category VARCHAR(100);
        
        -- Set default categories for existing fields
        UPDATE field_definitions 
        SET category = CASE
            WHEN field_name IN ('product_name', 'brand', 'variant', 'size', 'flavor') THEN 'Product Info'
            WHEN field_name IN ('price', 'promotion', 'discount') THEN 'Pricing'
            WHEN field_name IN ('facings', 'shelf_position', 'section', 'row', 'column') THEN 'Shelf Layout'
            WHEN field_name IN ('stock_level', 'out_of_stock') THEN 'Inventory'
            ELSE 'Other'
        END
        WHERE category IS NULL;
    END IF;

    -- Add sort_order column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'field_definitions' 
        AND column_name = 'sort_order'
    ) THEN
        ALTER TABLE field_definitions 
        ADD COLUMN sort_order INTEGER DEFAULT 999;
        
        -- Set default sort orders
        UPDATE field_definitions 
        SET sort_order = CASE
            WHEN field_name = 'product_name' THEN 1
            WHEN field_name = 'brand' THEN 2
            WHEN field_name = 'variant' THEN 3
            WHEN field_name = 'size' THEN 4
            WHEN field_name = 'price' THEN 5
            WHEN field_name = 'facings' THEN 1
            WHEN field_name = 'shelf_position' THEN 2
            WHEN field_name = 'section' THEN 3
            ELSE 99
        END
        WHERE sort_order = 999;
    END IF;

    -- Add parent_field column if it doesn't exist (for nested fields)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'field_definitions' 
        AND column_name = 'parent_field'
    ) THEN
        ALTER TABLE field_definitions 
        ADD COLUMN parent_field VARCHAR(100);
    END IF;
END $$;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_field_definitions_category ON field_definitions(category);
CREATE INDEX IF NOT EXISTS idx_field_definitions_sort_order ON field_definitions(sort_order);
CREATE INDEX IF NOT EXISTS idx_field_definitions_parent_field ON field_definitions(parent_field);