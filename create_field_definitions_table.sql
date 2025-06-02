-- Create field_definitions table for storing extraction field descriptions
-- These definitions help the AI understand what to extract

CREATE TABLE IF NOT EXISTS field_definitions (
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
    field_type VARCHAR(50) DEFAULT 'string', -- string, number, boolean, array, object
    is_required BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    
    -- Categorization
    category VARCHAR(50) DEFAULT 'product', -- product, shelf, price, promotion, etc.
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX idx_field_definitions_field_name ON field_definitions(field_name);
CREATE INDEX idx_field_definitions_category ON field_definitions(category);
CREATE INDEX idx_field_definitions_is_active ON field_definitions(is_active);

-- Add trigger for updated_at
CREATE TRIGGER update_field_definitions_updated_at 
    BEFORE UPDATE ON field_definitions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert common field definitions
INSERT INTO field_definitions (field_name, display_name, definition, examples, field_type, category) VALUES
('product_name', 'Product Name', 'The full name of the product as displayed on the packaging, including brand and variant', 'Examples: "Coca-Cola Zero Sugar 330ml", "Walkers Ready Salted Crisps 32.5g"', 'string', 'product'),
('brand', 'Brand', 'The manufacturer or brand name of the product', 'Examples: "Coca-Cola", "Walkers", "Cadbury"', 'string', 'product'),
('price', 'Price', 'The displayed price of the product in the local currency', 'Examples: "£1.50", "€2.99", "$3.49"', 'string', 'price'),
('shelf_position', 'Shelf Position', 'The position of the product on the shelf, counting from left to right and top to bottom', 'Examples: "Shelf 2, Position 5", "Top shelf, 3rd from left"', 'string', 'shelf'),
('facings', 'Number of Facings', 'The number of identical products displayed face-forward on the shelf. Count how many times the same product appears side by side', 'Examples: If Coca-Cola appears 3 times in a row, facings = 3', 'number', 'shelf'),
('stock_level', 'Stock Level', 'Visual estimate of how full the product section is (full, partial, low, empty)', 'Examples: "full", "75%", "low stock", "out of stock"', 'string', 'shelf'),
('promotion', 'Promotion', 'Any promotional labels, stickers, or signs associated with the product', 'Examples: "2 for £3", "Buy One Get One Free", "20% OFF"', 'string', 'promotion'),
('size', 'Product Size', 'The size, weight, or volume of the product as displayed on packaging', 'Examples: "330ml", "1L", "200g", "Family Size"', 'string', 'product'),
('barcode', 'Barcode', 'The barcode number if visible on the product', 'Examples: "5000112637922", "8710398606211"', 'string', 'product'),
('category', 'Product Category', 'The general category or type of product', 'Examples: "Soft Drinks", "Snacks", "Chocolate", "Cleaning Products"', 'string', 'product');

-- Add comments
COMMENT ON TABLE field_definitions IS 'Stores definitions for extraction fields to help AI understand what to extract';
COMMENT ON COLUMN field_definitions.definition IS 'Clear explanation of what this field represents, sent to AI';
COMMENT ON COLUMN field_definitions.examples IS 'Concrete examples to guide the AI extraction';