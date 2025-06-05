-- Create iterations table for detailed stage-by-stage tracking
-- This enables tracking where extractions get stuck and what feedback is passed between models

CREATE TABLE IF NOT EXISTS iterations (
    id SERIAL PRIMARY KEY,
    extraction_run_id VARCHAR(255) REFERENCES extraction_runs(run_id),
    queue_item_id INTEGER REFERENCES ai_extraction_queue(id),
    
    -- Iteration context
    iteration_number INTEGER NOT NULL,
    stage VARCHAR(50) NOT NULL CHECK (stage IN ('structure', 'products', 'details', 'comparison')),
    model_used VARCHAR(100),
    model_index INTEGER, -- Which model in the stage (1st, 2nd, 3rd)
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Status tracking
    status VARCHAR(50) CHECK (status IN ('started', 'completed', 'failed', 'retry')),
    success BOOLEAN,
    
    -- Prompt details
    prompt_template_id UUID REFERENCES prompt_templates(prompt_id),
    actual_prompt TEXT, -- The exact prompt sent including {IF_RETRY} blocks
    retry_context JSONB, -- What retry blocks were activated
    
    -- Visual feedback (for products/details stages)
    visual_feedback_received JSONB, -- Feedback from previous model
    visual_comparison_result JSONB, -- Comparison after this model
    planogram_generated BOOLEAN DEFAULT FALSE,
    
    -- Results
    extraction_result JSONB,
    products_found INTEGER,
    accuracy_score FLOAT,
    confidence_scores JSONB, -- Per-product confidence
    
    -- Orchestrator decisions
    orchestrator_decision JSONB, -- Why retry? Why stop?
    retry_reason TEXT,
    improvements_from_previous JSONB,
    
    -- Performance
    api_cost DECIMAL(10, 4),
    tokens_used INTEGER,
    
    -- Error tracking
    error_type VARCHAR(100),
    error_message TEXT,
    error_details JSONB,
    
    -- Indexes for analytics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_iterations_run_id ON iterations(extraction_run_id);
CREATE INDEX idx_iterations_queue_item ON iterations(queue_item_id);
CREATE INDEX idx_iterations_stage ON iterations(stage);
CREATE INDEX idx_iterations_model ON iterations(model_used);
CREATE INDEX idx_iterations_status ON iterations(status);
CREATE INDEX idx_iterations_created ON iterations(created_at);
CREATE INDEX idx_iterations_stage_model ON iterations(stage, model_used, model_index);

-- GIN indexes for JSONB columns
CREATE INDEX idx_iterations_visual_feedback ON iterations USING GIN (visual_feedback_received);
CREATE INDEX idx_iterations_orchestrator ON iterations USING GIN (orchestrator_decision);

-- View for stage performance analysis
CREATE OR REPLACE VIEW stage_performance_analysis AS
SELECT 
    stage,
    model_used,
    model_index,
    COUNT(*) as attempts,
    AVG(CASE WHEN success THEN 1 ELSE 0 END) * 100 as success_rate,
    AVG(duration_ms) as avg_duration_ms,
    AVG(accuracy_score) as avg_accuracy,
    AVG(products_found) as avg_products_found,
    AVG(api_cost) as avg_cost,
    COUNT(CASE WHEN visual_feedback_received IS NOT NULL THEN 1 END) as with_feedback_count
FROM iterations
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY stage, model_used, model_index
ORDER BY stage, model_index;

-- View for retry pattern analysis
CREATE OR REPLACE VIEW retry_pattern_analysis AS
SELECT 
    stage,
    retry_reason,
    COUNT(*) as retry_count,
    AVG(CASE WHEN i2.success THEN 1 ELSE 0 END) * 100 as retry_success_rate
FROM iterations i1
LEFT JOIN iterations i2 ON 
    i1.extraction_run_id = i2.extraction_run_id 
    AND i1.stage = i2.stage 
    AND i2.iteration_number = i1.iteration_number + 1
WHERE i1.status = 'retry'
GROUP BY stage, retry_reason
ORDER BY retry_count DESC;

-- Function to track iteration
CREATE OR REPLACE FUNCTION track_iteration(
    p_extraction_run_id VARCHAR(255),
    p_queue_item_id INTEGER,
    p_iteration_number INTEGER,
    p_stage VARCHAR(50),
    p_model_used VARCHAR(100),
    p_model_index INTEGER,
    p_prompt_template_id UUID,
    p_actual_prompt TEXT,
    p_retry_context JSONB,
    p_visual_feedback JSONB DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_iteration_id INTEGER;
BEGIN
    INSERT INTO iterations (
        extraction_run_id,
        queue_item_id,
        iteration_number,
        stage,
        model_used,
        model_index,
        prompt_template_id,
        actual_prompt,
        retry_context,
        visual_feedback_received,
        status
    ) VALUES (
        p_extraction_run_id,
        p_queue_item_id,
        p_iteration_number,
        p_stage,
        p_model_used,
        p_model_index,
        p_prompt_template_id,
        p_actual_prompt,
        p_retry_context,
        p_visual_feedback,
        'started'
    ) RETURNING id INTO v_iteration_id;
    
    RETURN v_iteration_id;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE iterations IS 'Detailed tracking of each extraction attempt including visual feedback and retry decisions';
COMMENT ON COLUMN iterations.visual_feedback_received IS 'Visual comparison feedback received from previous model attempt';
COMMENT ON COLUMN iterations.actual_prompt IS 'The exact prompt sent to the model including processed {IF_RETRY} blocks';
COMMENT ON COLUMN iterations.orchestrator_decision IS 'Detailed reasoning for retry/continue/stop decisions';