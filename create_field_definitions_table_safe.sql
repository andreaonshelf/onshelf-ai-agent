-- Create field_definitions table for storing extraction field descriptions
-- These definitions help the AI understand what to extract

DO $$ 
BEGIN
    -- Check if table exists before creating it
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'field_definitions'
    ) THEN
        CREATE TABLE field_definitions (
            -- Primary key
            id SERIAL PRIMARY KEY,
            
            -- Field identification
            field_name VARCHAR(100) NOT NULL UNIQUE,
            display_name VARCHAR(255) NOT NULL,
            
            -- The definition that will be sent to the AI
            definition TEXT NOT NULL,
            
            -- Examples to help the AI
            examples TEXT,
            
            -- Field metadata
            data_type VARCHAR(50) DEFAULT 'string', -- string, number, boolean, array, object
            is_required BOOLEAN DEFAULT FALSE,
            default_value TEXT,
            
            -- Categorization
            category VARCHAR(50) DEFAULT 'product', -- product, shelf, price, promotion, etc.
            
            -- Usage tracking
            usage_count INTEGER DEFAULT 0,
            
            -- Metadata
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE,
            
            -- Additional metadata as JSONB
            validation_rules JSONB,
            metadata JSONB
        );

        -- Create indexes
        CREATE INDEX idx_field_definitions_field_name ON field_definitions(field_name);
        CREATE INDEX idx_field_definitions_category ON field_definitions(category);
        CREATE INDEX idx_field_definitions_is_active ON field_definitions(is_active);

        -- Add comment
        COMMENT ON TABLE field_definitions IS 'Stores definitions for extraction fields to help AI understand what to extract';
        
        RAISE NOTICE 'field_definitions table created successfully';
    ELSE
        RAISE NOTICE 'field_definitions table already exists';
    END IF;

    -- Check if we need to add the updated_at trigger
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.triggers 
        WHERE trigger_name = 'update_field_definitions_updated_at'
    ) THEN
        -- First check if the trigger function exists
        IF EXISTS (
            SELECT 1 
            FROM pg_proc 
            WHERE proname = 'update_updated_at_column'
        ) THEN
            CREATE TRIGGER update_field_definitions_updated_at 
                BEFORE UPDATE ON field_definitions 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
            RAISE NOTICE 'Trigger update_field_definitions_updated_at created';
        ELSE
            RAISE NOTICE 'Trigger function update_updated_at_column does not exist, skipping trigger creation';
        END IF;
    END IF;
END $$;

-- Insert sample field definitions only if the table is empty
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM field_definitions LIMIT 1) THEN
        INSERT INTO field_definitions (field_name, display_name, definition, examples, data_type, category) VALUES
        ('product_name', 'Product Name', 'The full name of the product as displayed on the packaging, including brand and variant', 'Examples: "Coca-Cola Zero Sugar 330ml", "Walkers Ready Salted Crisps 32.5g"', 'string', 'product'),
        ('brand', 'Brand', 'The manufacturer or brand name of the product', 'Examples: "Coca-Cola", "Walkers", "Cadbury"', 'string', 'product'),
        ('price', 'Price', 'The displayed price of the product in the local currency', 'Examples: "£1.50", "€2.99", "$3.49"', 'string', 'price'),
        ('position', 'Position', 'The location of the product on the shelf', 'Object with shelf_number and position_on_shelf', 'object', 'shelf'),
        ('facings', 'Number of Facings', 'The number of identical products displayed face-forward on the shelf. Count how many times the same product appears side by side', 'Examples: If Coca-Cola appears 3 times in a row, facings = 3', 'integer', 'shelf'),
        ('stack', 'Stack/Depth', 'The number of products stacked behind the front-facing product', 'If products are stacked 2 deep, stack = 2', 'integer', 'shelf');
        
        RAISE NOTICE 'Sample field definitions inserted';
    ELSE
        RAISE NOTICE 'Field definitions already exist, skipping sample data';
    END IF;
END $$;