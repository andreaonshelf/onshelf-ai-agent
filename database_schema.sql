-- OnShelf AI Database Schema
-- Prompt Management System for Model-Specific Optimization

-- Human Corrections Table
CREATE TABLE IF NOT EXISTS human_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id TEXT NOT NULL,
    correction_type TEXT NOT NULL, -- 'missed_product', 'wrong_position', 'wrong_price', etc.
    original_ai_result JSONB NOT NULL,
    human_correction JSONB NOT NULL,
    correction_context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Prompt Templates Table
CREATE TABLE IF NOT EXISTS prompt_templates (
    prompt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id TEXT NOT NULL,
    prompt_type TEXT NOT NULL, -- 'structure', 'position', 'quantity', 'detail', 'validation'
    model_type TEXT NOT NULL,  -- 'gpt4o', 'claude', 'gemini', 'universal'
    prompt_version TEXT NOT NULL,
    prompt_content TEXT NOT NULL,
    performance_score DECIMAL(4,3) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    correction_rate DECIMAL(4,3) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT false,
    created_from_feedback BOOLEAN DEFAULT false,
    parent_prompt_id UUID REFERENCES prompt_templates(prompt_id),
    retailer_context TEXT[],
    category_context TEXT[],
    avg_token_cost DECIMAL(6,4),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Prompt Performance Tracking
CREATE TABLE IF NOT EXISTS prompt_performance (
    performance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID REFERENCES prompt_templates(prompt_id),
    upload_id TEXT NOT NULL,
    model_type TEXT NOT NULL,
    prompt_type TEXT NOT NULL,
    accuracy_score DECIMAL(4,3),
    processing_time_ms INTEGER,
    token_usage INTEGER,
    api_cost DECIMAL(6,4),
    human_corrections_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extraction Results for Analysis
CREATE TABLE IF NOT EXISTS extraction_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_id TEXT NOT NULL,
    comparison_group_id TEXT,
    system_type TEXT NOT NULL, -- 'custom', 'langgraph', 'hybrid'
    overall_accuracy DECIMAL(4,3),
    consensus_reached BOOLEAN,
    processing_time_seconds DECIMAL(8,3),
    total_cost DECIMAL(6,4),
    iteration_count INTEGER,
    structure_data JSONB,
    positions_data JSONB,
    quantities_data JSONB,
    details_data JSONB,
    validation_result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_prompt_performance ON prompt_templates(model_type, prompt_type, performance_score DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_context ON prompt_templates USING GIN(retailer_context, category_context);
CREATE INDEX IF NOT EXISTS idx_prompt_active ON prompt_templates(prompt_type, model_type, is_active);
CREATE INDEX IF NOT EXISTS idx_corrections_type ON human_corrections(correction_type, created_at);
CREATE INDEX IF NOT EXISTS idx_performance_tracking ON prompt_performance(prompt_id, created_at);
CREATE INDEX IF NOT EXISTS idx_extraction_results_system ON extraction_results(system_type, created_at);

-- Views for Analytics
CREATE OR REPLACE VIEW prompt_analytics AS
SELECT 
    pt.prompt_type,
    pt.model_type,
    pt.prompt_version,
    pt.performance_score,
    pt.usage_count,
    pt.correction_rate,
    AVG(pp.accuracy_score) as avg_accuracy,
    AVG(pp.processing_time_ms) as avg_processing_time,
    AVG(pp.api_cost) as avg_cost,
    COUNT(pp.performance_id) as total_uses
FROM prompt_templates pt
LEFT JOIN prompt_performance pp ON pt.prompt_id = pp.prompt_id
WHERE pt.is_active = true
GROUP BY pt.prompt_id, pt.prompt_type, pt.model_type, pt.prompt_version, 
         pt.performance_score, pt.usage_count, pt.correction_rate;

CREATE OR REPLACE VIEW correction_trends AS
SELECT 
    correction_type,
    DATE_TRUNC('day', created_at) as correction_date,
    COUNT(*) as correction_count,
    COUNT(DISTINCT upload_id) as affected_uploads
FROM human_corrections
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY correction_type, DATE_TRUNC('day', created_at)
ORDER BY correction_date DESC, correction_count DESC;

-- Functions for Prompt Selection
CREATE OR REPLACE FUNCTION get_best_prompt(
    p_prompt_type TEXT,
    p_model_type TEXT,
    p_context TEXT[] DEFAULT NULL
) RETURNS TABLE(
    prompt_id UUID,
    prompt_content TEXT,
    performance_score DECIMAL(4,3)
) AS $$
BEGIN
    -- First try model-specific prompt
    RETURN QUERY
    SELECT pt.prompt_id, pt.prompt_content, pt.performance_score
    FROM prompt_templates pt
    WHERE pt.prompt_type = p_prompt_type
      AND pt.model_type = p_model_type
      AND pt.is_active = true
      AND (p_context IS NULL OR pt.retailer_context && p_context OR pt.category_context && p_context)
    ORDER BY pt.performance_score DESC, pt.created_at DESC
    LIMIT 1;
    
    -- If no model-specific prompt found, try universal
    IF NOT FOUND THEN
        RETURN QUERY
        SELECT pt.prompt_id, pt.prompt_content, pt.performance_score
        FROM prompt_templates pt
        WHERE pt.prompt_type = p_prompt_type
          AND pt.model_type = 'universal'
          AND pt.is_active = true
        ORDER BY pt.performance_score DESC, pt.created_at DESC
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to Update Prompt Performance
CREATE OR REPLACE FUNCTION update_prompt_performance(
    p_prompt_id UUID,
    p_accuracy DECIMAL(4,3),
    p_had_corrections BOOLEAN DEFAULT false
) RETURNS VOID AS $$
BEGIN
    -- Update usage count and performance score
    UPDATE prompt_templates 
    SET 
        usage_count = usage_count + 1,
        performance_score = (
            (performance_score * usage_count + p_accuracy) / (usage_count + 1)
        ),
        correction_rate = CASE 
            WHEN p_had_corrections THEN 
                (correction_rate * usage_count + 1.0) / (usage_count + 1)
            ELSE 
                (correction_rate * usage_count) / (usage_count + 1)
        END
    WHERE prompt_id = p_prompt_id;
END;
$$ LANGUAGE plpgsql; 