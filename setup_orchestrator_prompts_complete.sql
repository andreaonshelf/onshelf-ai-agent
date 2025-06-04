-- =====================================================
-- OnShelf AI Extraction Prompts - Complete Setup
-- =====================================================
-- This file:
-- 1. Adds missing columns for orchestrator prompts
-- 2. Clears existing prompts for fresh start
-- 3. Inserts all prompts from refined complete set
-- 4. Uses proper field definitions with Instructor schema
-- 5. No fake performance data
-- =====================================================

BEGIN;

-- =====================================================
-- STEP 1: Add Missing Columns for Orchestrator Support
-- =====================================================

-- Add context column for storing prompt context variables
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS context JSONB DEFAULT '{}'::jsonb;

-- Add variables column for storing available template variables
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS variables JSONB DEFAULT '[]'::jsonb;

-- Add retry_config column for retry-specific settings
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS retry_config JSONB DEFAULT '{}'::jsonb;

-- Add meta_prompt_id for linking to meta-prompts table
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS meta_prompt_id UUID;

-- Add extraction_config for stage-specific configurations
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS extraction_config JSONB DEFAULT '{}'::jsonb;

-- Add template column for storing raw template with {IF_RETRY} blocks
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS template TEXT;

-- Add is_template flag to distinguish between plain prompts and templates
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT FALSE;

-- Add retry_count to track how many times a prompt has been used in retries
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Add parent_template_id for linking retry prompts to their base prompts
ALTER TABLE prompt_templates 
ADD COLUMN IF NOT EXISTS parent_template_id VARCHAR(255);

-- =====================================================
-- STEP 2: Clear Existing Prompts for Fresh Start
-- =====================================================

DELETE FROM prompt_templates;

-- =====================================================
-- STEP 3: Insert All Prompts from Refined Complete Set
-- =====================================================

-- STAGE 1: Structure Extraction (Standard)
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    context,
    variables,
    extraction_config
) VALUES (
    'structure_extraction_v1',
    'structure',
    'universal',
    '1.0',
    'You are an expert at analyzing retail shelf images to understand their structure.

Analyze this shelf image and identify:
1. The overall shelf structure (number of shelves, dimensions)
2. Major sections or zones on each shelf
3. Product placement patterns

Focus on the physical layout, not individual products.

Output the shelf structure as a JSON object.',
    true,
    'Structure Extraction - Standard',
    'Extracts shelf structure and layout information',
    '[
        {
            "name": "shelf_structure",
            "type": "object",
            "description": "Complete shelf structure analysis",
            "required": true,
            "nested_fields": [
                {
                    "name": "total_shelves",
                    "type": "integer",
                    "description": "Number of shelves in the image",
                    "required": true
                },
                {
                    "name": "shelf_dimensions",
                    "type": "object",
                    "description": "Estimated dimensions of the shelf unit",
                    "required": true,
                    "nested_fields": [
                        {
                            "name": "width",
                            "type": "number",
                            "description": "Estimated width in relative units",
                            "required": true
                        },
                        {
                            "name": "height",
                            "type": "number",
                            "description": "Estimated height in relative units",
                            "required": true
                        }
                    ]
                },
                {
                    "name": "shelves",
                    "type": "array",
                    "description": "Details for each shelf",
                    "required": true,
                    "items": {
                        "type": "object",
                        "nested_fields": [
                            {
                                "name": "shelf_number",
                                "type": "integer",
                                "description": "Shelf number from top (1) to bottom",
                                "required": true
                            },
                            {
                                "name": "height_percentage",
                                "type": "number",
                                "description": "Height of shelf as percentage of total",
                                "required": true
                            },
                            {
                                "name": "sections",
                                "type": "array",
                                "description": "Sections within the shelf",
                                "required": true,
                                "items": {
                                    "type": "object",
                                    "nested_fields": [
                                        {
                                            "name": "section_id",
                                            "type": "string",
                                            "description": "Unique identifier for section",
                                            "required": true
                                        },
                                        {
                                            "name": "start_percentage",
                                            "type": "number",
                                            "description": "Starting position as percentage from left",
                                            "required": true
                                        },
                                        {
                                            "name": "end_percentage",
                                            "type": "number",
                                            "description": "Ending position as percentage from left",
                                            "required": true
                                        },
                                        {
                                            "name": "product_category",
                                            "type": "string",
                                            "description": "General category of products in section",
                                            "required": false
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        }
    ]'::jsonb,
    'structure_extraction',
    ARRAY['structure', 'extraction', 'stage1'],
    true,
    true,
    NULL,
    false,
    '{}'::jsonb,
    '[]'::jsonb,
    '{
        "stage": 1,
        "temperature": 0.3,
        "max_tokens": 2000
    }'::jsonb
);

-- STAGE 1: Structure Extraction (Retry Variant)
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    parent_template_id,
    context,
    variables,
    extraction_config,
    retry_config
) VALUES (
    'structure_extraction_retry_v1',
    'structure',
    'universal',
    '1.0',
    'Previous structure extraction had issues. Please carefully re-analyze this shelf image.

IMPORTANT CORRECTIONS NEEDED:
- Count ALL visible shelves from top to bottom
- Ensure shelf dimensions are realistic
- Check that section percentages add up correctly
- Verify all shelves are included

Analyze the shelf structure again and provide:
1. Total number of shelves (count carefully)
2. Shelf dimensions and proportions
3. Clear section divisions on each shelf

Double-check your shelf count before responding.',
    true,
    'Structure Extraction - Retry',
    'Retry variant for structure extraction with error corrections',
    '[
        {
            "name": "shelf_structure",
            "type": "object",
            "description": "Complete shelf structure analysis",
            "required": true,
            "nested_fields": [
                {
                    "name": "total_shelves",
                    "type": "integer",
                    "description": "Number of shelves in the image",
                    "required": true
                },
                {
                    "name": "shelf_dimensions",
                    "type": "object",
                    "description": "Estimated dimensions of the shelf unit",
                    "required": true,
                    "nested_fields": [
                        {
                            "name": "width",
                            "type": "number",
                            "description": "Estimated width in relative units",
                            "required": true
                        },
                        {
                            "name": "height",
                            "type": "number",
                            "description": "Estimated height in relative units",
                            "required": true
                        }
                    ]
                },
                {
                    "name": "shelves",
                    "type": "array",
                    "description": "Details for each shelf",
                    "required": true,
                    "items": {
                        "type": "object",
                        "nested_fields": [
                            {
                                "name": "shelf_number",
                                "type": "integer",
                                "description": "Shelf number from top (1) to bottom",
                                "required": true
                            },
                            {
                                "name": "height_percentage",
                                "type": "number",
                                "description": "Height of shelf as percentage of total",
                                "required": true
                            },
                            {
                                "name": "sections",
                                "type": "array",
                                "description": "Sections within the shelf",
                                "required": true,
                                "items": {
                                    "type": "object",
                                    "nested_fields": [
                                        {
                                            "name": "section_id",
                                            "type": "string",
                                            "description": "Unique identifier for section",
                                            "required": true
                                        },
                                        {
                                            "name": "start_percentage",
                                            "type": "number",
                                            "description": "Starting position as percentage from left",
                                            "required": true
                                        },
                                        {
                                            "name": "end_percentage",
                                            "type": "number",
                                            "description": "Ending position as percentage from left",
                                            "required": true
                                        },
                                        {
                                            "name": "product_category",
                                            "type": "string",
                                            "description": "General category of products in section",
                                            "required": false
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ]
        }
    ]'::jsonb,
    'structure_extraction',
    ARRAY['structure', 'extraction', 'stage1', 'retry'],
    true,
    true,
    NULL,
    false,
    'structure_extraction_v1',
    '{}'::jsonb,
    '[]'::jsonb,
    '{
        "stage": 1,
        "temperature": 0.1,
        "max_tokens": 2000,
        "is_retry": true
    }'::jsonb,
    '{
        "max_retries": 2,
        "backoff_multiplier": 1.5
    }'::jsonb
);

-- STAGE 2: Product Extraction (Standard)
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    context,
    variables,
    extraction_config
) VALUES (
    'product_extraction_v1',
    'products',
    'universal',
    '1.0',
    'Given this shelf structure, identify all products in the image:

{shelf_structure}

For each product, provide:
1. Product name and brand
2. Exact shelf and section location
3. Number of facings (visible units)
4. Position within the section

Focus on accuracy over speed. Double-check product counts.',
    true,
    'Product Extraction - Standard',
    'Extracts detailed product information based on shelf structure',
    '[
        {
            "name": "products",
            "type": "array",
            "description": "All products identified in the image",
            "required": true,
            "items": {
                "type": "object",
                "nested_fields": [
                    {
                        "name": "product_id",
                        "type": "string",
                        "description": "Unique identifier for the product",
                        "required": true
                    },
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Product name",
                        "required": true
                    },
                    {
                        "name": "brand",
                        "type": "string",
                        "description": "Brand name",
                        "required": true
                    },
                    {
                        "name": "shelf_number",
                        "type": "integer",
                        "description": "Shelf number where product is located",
                        "required": true
                    },
                    {
                        "name": "section_id",
                        "type": "string",
                        "description": "Section ID within the shelf",
                        "required": true
                    },
                    {
                        "name": "facings",
                        "type": "integer",
                        "description": "Number of visible product facings",
                        "required": true
                    },
                    {
                        "name": "position_in_section",
                        "type": "object",
                        "description": "Position within the section",
                        "required": true,
                        "nested_fields": [
                            {
                                "name": "x_percentage",
                                "type": "number",
                                "description": "Horizontal position as percentage within section",
                                "required": true
                            },
                            {
                                "name": "y_percentage",
                                "type": "number",
                                "description": "Vertical position as percentage within shelf",
                                "required": true
                            }
                        ]
                    },
                    {
                        "name": "size",
                        "type": "string",
                        "description": "Product size/volume if visible",
                        "required": false
                    },
                    {
                        "name": "price",
                        "type": "string",
                        "description": "Price if visible",
                        "required": false
                    }
                ]
            }
        }
    ]'::jsonb,
    'product_extraction',
    ARRAY['products', 'extraction', 'stage2'],
    true,
    true,
    NULL,
    false,
    '{}'::jsonb,
    '[
        {
            "name": "shelf_structure",
            "type": "object",
            "description": "Shelf structure from previous stage"
        }
    ]'::jsonb,
    '{
        "stage": 2,
        "temperature": 0.3,
        "max_tokens": 4000
    }'::jsonb
);

-- STAGE 2: Product Extraction (Retry Variant)
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    parent_template_id,
    context,
    variables,
    extraction_config,
    retry_config
) VALUES (
    'product_extraction_retry_v1',
    'products',
    'universal',
    '1.0',
    'Previous product extraction had errors. Please re-analyze carefully.

Shelf structure:
{shelf_structure}

CRITICAL FIXES NEEDED:
- Ensure ALL visible products are captured
- Verify facing counts are accurate
- Check product placement matches actual positions
- Don''t miss products at shelf edges

Re-extract all products with special attention to:
1. Complete product coverage
2. Accurate facing counts
3. Correct shelf/section assignments',
    true,
    'Product Extraction - Retry',
    'Retry variant for product extraction with error focus',
    '[
        {
            "name": "products",
            "type": "array",
            "description": "All products identified in the image",
            "required": true,
            "items": {
                "type": "object",
                "nested_fields": [
                    {
                        "name": "product_id",
                        "type": "string",
                        "description": "Unique identifier for the product",
                        "required": true
                    },
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Product name",
                        "required": true
                    },
                    {
                        "name": "brand",
                        "type": "string",
                        "description": "Brand name",
                        "required": true
                    },
                    {
                        "name": "shelf_number",
                        "type": "integer",
                        "description": "Shelf number where product is located",
                        "required": true
                    },
                    {
                        "name": "section_id",
                        "type": "string",
                        "description": "Section ID within the shelf",
                        "required": true
                    },
                    {
                        "name": "facings",
                        "type": "integer",
                        "description": "Number of visible product facings",
                        "required": true
                    },
                    {
                        "name": "position_in_section",
                        "type": "object",
                        "description": "Position within the section",
                        "required": true,
                        "nested_fields": [
                            {
                                "name": "x_percentage",
                                "type": "number",
                                "description": "Horizontal position as percentage within section",
                                "required": true
                            },
                            {
                                "name": "y_percentage",
                                "type": "number",
                                "description": "Vertical position as percentage within shelf",
                                "required": true
                            }
                        ]
                    },
                    {
                        "name": "size",
                        "type": "string",
                        "description": "Product size/volume if visible",
                        "required": false
                    },
                    {
                        "name": "price",
                        "type": "string",
                        "description": "Price if visible",
                        "required": false
                    }
                ]
            }
        }
    ]'::jsonb,
    'product_extraction',
    ARRAY['products', 'extraction', 'stage2', 'retry'],
    true,
    true,
    NULL,
    false,
    'product_extraction_v1',
    '{}'::jsonb,
    '[
        {
            "name": "shelf_structure",
            "type": "object",
            "description": "Shelf structure from previous stage"
        }
    ]'::jsonb,
    '{
        "stage": 2,
        "temperature": 0.1,
        "max_tokens": 4000,
        "is_retry": true
    }'::jsonb,
    '{
        "max_retries": 2,
        "backoff_multiplier": 1.5
    }'::jsonb
);

-- STAGE 3: Detail Enhancement (Standard)
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    context,
    variables,
    extraction_config
) VALUES (
    'detail_enhancement_v1',
    'details',
    'universal',
    '1.0',
    'Enhance the product details with additional information.

Current products:
{products}

For each product, add:
1. Detailed category classification
2. Package type and size details
3. Any visible promotional tags
4. Precise color/variant information
5. Stock level indicators

Maintain all existing data while adding enhancements.',
    true,
    'Detail Enhancement - Standard',
    'Enhances product information with additional details',
    '[
        {
            "name": "enhanced_products",
            "type": "array",
            "description": "Products with enhanced details",
            "required": true,
            "items": {
                "type": "object",
                "nested_fields": [
                    {
                        "name": "product_id",
                        "type": "string",
                        "description": "Unique identifier for the product",
                        "required": true
                    },
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Product name",
                        "required": true
                    },
                    {
                        "name": "brand",
                        "type": "string",
                        "description": "Brand name",
                        "required": true
                    },
                    {
                        "name": "category",
                        "type": "string",
                        "description": "Product category",
                        "required": true
                    },
                    {
                        "name": "subcategory",
                        "type": "string",
                        "description": "Product subcategory",
                        "required": false
                    },
                    {
                        "name": "shelf_number",
                        "type": "integer",
                        "description": "Shelf number where product is located",
                        "required": true
                    },
                    {
                        "name": "section_id",
                        "type": "string",
                        "description": "Section ID within the shelf",
                        "required": true
                    },
                    {
                        "name": "facings",
                        "type": "integer",
                        "description": "Number of visible product facings",
                        "required": true
                    },
                    {
                        "name": "position_in_section",
                        "type": "object",
                        "description": "Position within the section",
                        "required": true,
                        "nested_fields": [
                            {
                                "name": "x_percentage",
                                "type": "number",
                                "description": "Horizontal position as percentage within section",
                                "required": true
                            },
                            {
                                "name": "y_percentage",
                                "type": "number",
                                "description": "Vertical position as percentage within shelf",
                                "required": true
                            }
                        ]
                    },
                    {
                        "name": "size",
                        "type": "string",
                        "description": "Product size/volume",
                        "required": false
                    },
                    {
                        "name": "price",
                        "type": "string",
                        "description": "Price if visible",
                        "required": false
                    },
                    {
                        "name": "package_type",
                        "type": "string",
                        "description": "Type of packaging",
                        "required": false
                    },
                    {
                        "name": "variant",
                        "type": "string",
                        "description": "Product variant/flavor",
                        "required": false
                    },
                    {
                        "name": "promotional_tags",
                        "type": "array",
                        "description": "Any promotional tags visible",
                        "required": false,
                        "items": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "stock_level",
                        "type": "string",
                        "description": "Observed stock level",
                        "required": false
                    }
                ]
            }
        }
    ]'::jsonb,
    'detail_enhancement',
    ARRAY['details', 'enhancement', 'stage3'],
    true,
    true,
    NULL,
    false,
    '{}'::jsonb,
    '[
        {
            "name": "products",
            "type": "array",
            "description": "Products from previous stage"
        }
    ]'::jsonb,
    '{
        "stage": 3,
        "temperature": 0.3,
        "max_tokens": 4000
    }'::jsonb
);

-- STAGE 3: Detail Enhancement (Retry)
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    parent_template_id,
    context,
    variables,
    extraction_config,
    retry_config
) VALUES (
    'detail_enhancement_retry_v1',
    'details',
    'universal',
    '1.0',
    'Previous detail enhancement was incomplete. Please carefully re-examine.

Products to enhance:
{products}

FOCUS ON:
- Adding missing category information
- Identifying all visible package details
- Capturing promotional information
- Noting stock levels accurately

Ensure NO details are missed this time.',
    true,
    'Detail Enhancement - Retry',
    'Retry variant for detail enhancement',
    '[
        {
            "name": "enhanced_products",
            "type": "array",
            "description": "Products with enhanced details",
            "required": true,
            "items": {
                "type": "object",
                "nested_fields": [
                    {
                        "name": "product_id",
                        "type": "string",
                        "description": "Unique identifier for the product",
                        "required": true
                    },
                    {
                        "name": "name",
                        "type": "string",
                        "description": "Product name",
                        "required": true
                    },
                    {
                        "name": "brand",
                        "type": "string",
                        "description": "Brand name",
                        "required": true
                    },
                    {
                        "name": "category",
                        "type": "string",
                        "description": "Product category",
                        "required": true
                    },
                    {
                        "name": "subcategory",
                        "type": "string",
                        "description": "Product subcategory",
                        "required": false
                    },
                    {
                        "name": "shelf_number",
                        "type": "integer",
                        "description": "Shelf number where product is located",
                        "required": true
                    },
                    {
                        "name": "section_id",
                        "type": "string",
                        "description": "Section ID within the shelf",
                        "required": true
                    },
                    {
                        "name": "facings",
                        "type": "integer",
                        "description": "Number of visible product facings",
                        "required": true
                    },
                    {
                        "name": "position_in_section",
                        "type": "object",
                        "description": "Position within the section",
                        "required": true,
                        "nested_fields": [
                            {
                                "name": "x_percentage",
                                "type": "number",
                                "description": "Horizontal position as percentage within section",
                                "required": true
                            },
                            {
                                "name": "y_percentage",
                                "type": "number",
                                "description": "Vertical position as percentage within shelf",
                                "required": true
                            }
                        ]
                    },
                    {
                        "name": "size",
                        "type": "string",
                        "description": "Product size/volume",
                        "required": false
                    },
                    {
                        "name": "price",
                        "type": "string",
                        "description": "Price if visible",
                        "required": false
                    },
                    {
                        "name": "package_type",
                        "type": "string",
                        "description": "Type of packaging",
                        "required": false
                    },
                    {
                        "name": "variant",
                        "type": "string",
                        "description": "Product variant/flavor",
                        "required": false
                    },
                    {
                        "name": "promotional_tags",
                        "type": "array",
                        "description": "Any promotional tags visible",
                        "required": false,
                        "items": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "stock_level",
                        "type": "string",
                        "description": "Observed stock level",
                        "required": false
                    }
                ]
            }
        }
    ]'::jsonb,
    'detail_enhancement',
    ARRAY['details', 'enhancement', 'stage3', 'retry'],
    true,
    true,
    NULL,
    false,
    'detail_enhancement_v1',
    '{}'::jsonb,
    '[
        {
            "name": "products",
            "type": "array",
            "description": "Products from previous stage"
        }
    ]'::jsonb,
    '{
        "stage": 3,
        "temperature": 0.1,
        "max_tokens": 4000,
        "is_retry": true
    }'::jsonb,
    '{
        "max_retries": 2,
        "backoff_multiplier": 1.5
    }'::jsonb
);

-- Orchestrator: Master Orchestrator Prompt
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    context,
    variables,
    extraction_config
) VALUES (
    'master_orchestrator_v1',
    'orchestrator',
    'universal',
    '1.0',
    'You are the master orchestrator for shelf image analysis.

Current state:
- Stage: {current_stage}
- Iteration: {iteration}
- Previous accuracy: {previous_accuracy}

{IF_RETRY}
Previous attempt failed with:
{error_details}
{END_IF_RETRY}

Decide the next action:
1. Continue to next stage
2. Retry current stage
3. Request human intervention
4. Mark as complete

Base your decision on accuracy thresholds and error patterns.',
    true,
    'Master Orchestrator',
    'Controls the overall extraction pipeline flow',
    '[
        {
            "name": "decision",
            "type": "object",
            "description": "Orchestration decision",
            "required": true,
            "nested_fields": [
                {
                    "name": "action",
                    "type": "string",
                    "description": "Next action to take",
                    "required": true,
                    "enum": ["continue", "retry", "escalate", "complete"]
                },
                {
                    "name": "reason",
                    "type": "string",
                    "description": "Reason for the decision",
                    "required": true
                },
                {
                    "name": "confidence",
                    "type": "number",
                    "description": "Confidence in decision (0-1)",
                    "required": true
                },
                {
                    "name": "retry_prompt_id",
                    "type": "string",
                    "description": "Specific retry prompt to use if retrying",
                    "required": false
                },
                {
                    "name": "next_stage",
                    "type": "string",
                    "description": "Next stage if continuing",
                    "required": false
                }
            ]
        }
    ]'::jsonb,
    'orchestrator',
    ARRAY['orchestrator', 'master', 'pipeline'],
    true,
    true,
    'You are the master orchestrator for shelf image analysis.

Current state:
- Stage: {current_stage}
- Iteration: {iteration}
- Previous accuracy: {previous_accuracy}

{IF_RETRY}
Previous attempt failed with:
{error_details}
{END_IF_RETRY}

Decide the next action:
1. Continue to next stage
2. Retry current stage
3. Request human intervention
4. Mark as complete

Base your decision on accuracy thresholds and error patterns.',
    true,
    '{
        "accuracy_thresholds": {
            "structure": 0.9,
            "products": 0.85,
            "details": 0.8
        }
    }'::jsonb,
    '[
        {
            "name": "current_stage",
            "type": "string",
            "description": "Current pipeline stage"
        },
        {
            "name": "iteration",
            "type": "integer",
            "description": "Current iteration number"
        },
        {
            "name": "previous_accuracy",
            "type": "number",
            "description": "Accuracy from previous attempt"
        },
        {
            "name": "error_details",
            "type": "string",
            "description": "Details of previous errors"
        }
    ]'::jsonb,
    '{
        "temperature": 0.2,
        "max_tokens": 1000
    }'::jsonb
);

-- Orchestrator: Extraction Orchestrator
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    context,
    variables,
    extraction_config
) VALUES (
    'extraction_orchestrator_v1',
    'orchestrator',
    'universal',
    '1.0',
    'Manage the extraction process for stage: {stage_name}

Input data:
{input_data}

{IF_RETRY}
Previous extraction issues:
{extraction_errors}
- Missing products: {missing_count}
- Incorrect positions: {position_errors}
{END_IF_RETRY}

Select the appropriate extraction approach and parameters.
Consider using stricter prompts for retries.',
    true,
    'Extraction Orchestrator',
    'Manages individual extraction stages',
    '[
        {
            "name": "extraction_plan",
            "type": "object",
            "description": "Plan for extraction",
            "required": true,
            "nested_fields": [
                {
                    "name": "prompt_id",
                    "type": "string",
                    "description": "Prompt template to use",
                    "required": true
                },
                {
                    "name": "model_parameters",
                    "type": "object",
                    "description": "Model parameters",
                    "required": true,
                    "nested_fields": [
                        {
                            "name": "temperature",
                            "type": "number",
                            "description": "Temperature setting",
                            "required": true
                        },
                        {
                            "name": "max_tokens",
                            "type": "integer",
                            "description": "Maximum tokens",
                            "required": true
                        }
                    ]
                },
                {
                    "name": "focus_areas",
                    "type": "array",
                    "description": "Areas to focus on",
                    "required": false,
                    "items": {
                        "type": "string"
                    }
                },
                {
                    "name": "validation_rules",
                    "type": "array",
                    "description": "Validation rules to apply",
                    "required": true,
                    "items": {
                        "type": "string"
                    }
                }
            ]
        }
    ]'::jsonb,
    'orchestrator',
    ARRAY['orchestrator', 'extraction', 'stage-specific'],
    true,
    true,
    'Manage the extraction process for stage: {stage_name}

Input data:
{input_data}

{IF_RETRY}
Previous extraction issues:
{extraction_errors}
- Missing products: {missing_count}
- Incorrect positions: {position_errors}
{END_IF_RETRY}

Select the appropriate extraction approach and parameters.
Consider using stricter prompts for retries.',
    true,
    '{}'::jsonb,
    '[
        {
            "name": "stage_name",
            "type": "string",
            "description": "Name of current stage"
        },
        {
            "name": "input_data",
            "type": "object",
            "description": "Input data for stage"
        },
        {
            "name": "extraction_errors",
            "type": "array",
            "description": "Previous extraction errors"
        },
        {
            "name": "missing_count",
            "type": "integer",
            "description": "Count of missing items"
        },
        {
            "name": "position_errors",
            "type": "integer",
            "description": "Count of position errors"
        }
    ]'::jsonb,
    '{
        "temperature": 0.2,
        "max_tokens": 1000
    }'::jsonb
);

-- Orchestrator: Comparison Orchestrator
INSERT INTO prompt_templates (
    template_id,
    prompt_type,
    model_type,
    prompt_version,
    prompt_text,
    is_active,
    name,
    description,
    fields,
    stage_type,
    tags,
    is_system_generated,
    is_public,
    template,
    is_template,
    context,
    variables,
    extraction_config
) VALUES (
    'comparison_orchestrator_v1',
    'orchestrator',
    'universal',
    '1.0',
    'Compare extraction results with the visual planogram.

Extraction data:
{extraction_data}

Planogram representation:
{planogram_data}

{IF_RETRY}
Previous comparison found these mismatches:
{mismatch_details}
{END_IF_RETRY}

Identify discrepancies and calculate accuracy.
Focus on:
1. Product count accuracy
2. Position accuracy
3. Facing count accuracy',
    true,
    'Comparison Orchestrator',
    'Manages visual comparison and accuracy calculation',
    '[
        {
            "name": "comparison_result",
            "type": "object",
            "description": "Comparison analysis results",
            "required": true,
            "nested_fields": [
                {
                    "name": "overall_accuracy",
                    "type": "number",
                    "description": "Overall accuracy score (0-1)",
                    "required": true
                },
                {
                    "name": "accuracy_breakdown",
                    "type": "object",
                    "description": "Accuracy by category",
                    "required": true,
                    "nested_fields": [
                        {
                            "name": "product_count",
                            "type": "number",
                            "description": "Product count accuracy",
                            "required": true
                        },
                        {
                            "name": "positions",
                            "type": "number",
                            "description": "Position accuracy",
                            "required": true
                        },
                        {
                            "name": "facings",
                            "type": "number",
                            "description": "Facing count accuracy",
                            "required": true
                        }
                    ]
                },
                {
                    "name": "mismatches",
                    "type": "array",
                    "description": "List of mismatches found",
                    "required": true,
                    "items": {
                        "type": "object",
                        "nested_fields": [
                            {
                                "name": "type",
                                "type": "string",
                                "description": "Type of mismatch",
                                "required": true
                            },
                            {
                                "name": "severity",
                                "type": "string",
                                "description": "Severity level",
                                "required": true,
                                "enum": ["critical", "high", "medium", "low"]
                            },
                            {
                                "name": "description",
                                "type": "string",
                                "description": "Description of mismatch",
                                "required": true
                            },
                            {
                                "name": "location",
                                "type": "string",
                                "description": "Location of mismatch",
                                "required": true
                            }
                        ]
                    }
                },
                {
                    "name": "recommendations",
                    "type": "array",
                    "description": "Recommendations for improvement",
                    "required": true,
                    "items": {
                        "type": "string"
                    }
                }
            ]
        }
    ]'::jsonb,
    'orchestrator',
    ARRAY['orchestrator', 'comparison', 'validation'],
    true,
    true,
    'Compare extraction results with the visual planogram.

Extraction data:
{extraction_data}

Planogram representation:
{planogram_data}

{IF_RETRY}
Previous comparison found these mismatches:
{mismatch_details}
{END_IF_RETRY}

Identify discrepancies and calculate accuracy.
Focus on:
1. Product count accuracy
2. Position accuracy
3. Facing count accuracy',
    true,
    '{
        "accuracy_weights": {
            "product_count": 0.4,
            "positions": 0.4,
            "facings": 0.2
        }
    }'::jsonb,
    '[
        {
            "name": "extraction_data",
            "type": "object",
            "description": "Extracted data to compare"
        },
        {
            "name": "planogram_data",
            "type": "object",
            "description": "Planogram representation"
        },
        {
            "name": "mismatch_details",
            "type": "array",
            "description": "Previous mismatch details"
        }
    ]'::jsonb,
    '{
        "temperature": 0.1,
        "max_tokens": 2000
    }'::jsonb
);

-- =====================================================
-- STEP 4: Create indexes for better performance
-- =====================================================

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_prompt_templates_template_id ON prompt_templates(template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_prompt_type ON prompt_templates(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_stage_type ON prompt_templates(stage_type);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_is_active ON prompt_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_parent_template ON prompt_templates(parent_template_id);

-- =====================================================
-- STEP 5: Verify the setup
-- =====================================================

-- Show summary of inserted prompts
SELECT 
    prompt_type,
    stage_type,
    COUNT(*) as count,
    array_agg(name ORDER BY name) as prompt_names
FROM prompt_templates
GROUP BY prompt_type, stage_type
ORDER BY 
    CASE 
        WHEN stage_type = 'structure_extraction' THEN 1
        WHEN stage_type = 'product_extraction' THEN 2
        WHEN stage_type = 'detail_enhancement' THEN 3
        WHEN stage_type = 'orchestrator' THEN 4
        ELSE 5
    END;

-- Show the structure of the prompt_templates table
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'prompt_templates'
ORDER BY ordinal_position;

COMMIT;

-- End of setup script