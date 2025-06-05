-- Standalone SQL file for creating iterations table and related analytics tables
-- Execute this entire file in Supabase SQL Editor

-- 1. Create iterations table for tracking extraction attempts
CREATE TABLE IF NOT EXISTS iterations (
    id SERIAL PRIMARY KEY,
    extraction_run_id VARCHAR(255) REFERENCES extraction_runs(run_id),
    queue_item_id INTEGER REFERENCES ai_extraction_queue(id),
    iteration_number INTEGER NOT NULL,
    stage VARCHAR(50) NOT NULL CHECK (stage IN ('structure', 'products', 'details', 'comparison', 'validation')),
    model_used VARCHAR(100),
    model_index INTEGER,
    
    -- Prompt tracking
    prompt_template_id VARCHAR(255),
    actual_prompt TEXT,
    retry_context JSONB,
    retry_blocks_activated TEXT[],
    
    -- Visual feedback
    visual_feedback_received JSONB,
    visual_comparison_result JSONB,
    
    -- Orchestrator decisions
    orchestrator_decision JSONB,
    retry_reason VARCHAR(255),
    
    -- Results
    extraction_result JSONB,
    products_found INTEGER,
    accuracy_score DECIMAL(3,2),
    confidence_score DECIMAL(3,2),
    
    -- Performance metrics
    duration_ms INTEGER,
    api_cost DECIMAL(10,4),
    tokens_used INTEGER,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'started' CHECK (status IN ('started', 'completed', 'failed', 'retrying')),
    error_type VARCHAR(100),
    error_message TEXT,
    success BOOLEAN DEFAULT false,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT fk_extraction_run FOREIGN KEY (extraction_run_id) REFERENCES extraction_runs(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_queue_item FOREIGN KEY (queue_item_id) REFERENCES ai_extraction_queue(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_iterations_extraction_run ON iterations(extraction_run_id);
CREATE INDEX IF NOT EXISTS idx_iterations_queue_item ON iterations(queue_item_id);
CREATE INDEX IF NOT EXISTS idx_iterations_stage ON iterations(stage);
CREATE INDEX IF NOT EXISTS idx_iterations_model ON iterations(model_used);
CREATE INDEX IF NOT EXISTS idx_iterations_status ON iterations(status);
CREATE INDEX IF NOT EXISTS idx_iterations_created ON iterations(created_at);
CREATE INDEX IF NOT EXISTS idx_iterations_retry_reason ON iterations(retry_reason);

-- 2. Create prompt execution log for detailed prompt analysis
CREATE TABLE IF NOT EXISTS prompt_execution_log (
    id SERIAL PRIMARY KEY,
    iteration_id INTEGER REFERENCES iterations(id) ON DELETE CASCADE,
    prompt_template_hash BIGINT,
    retry_blocks_activated TEXT[],
    prompt_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompt_execution_iteration ON prompt_execution_log(iteration_id);
CREATE INDEX IF NOT EXISTS idx_prompt_execution_blocks ON prompt_execution_log(retry_blocks_activated);

-- 3. Create visual feedback log for tracking feedback impact
CREATE TABLE IF NOT EXISTS visual_feedback_log (
    id SERIAL PRIMARY KEY,
    iteration_id INTEGER REFERENCES iterations(id) ON DELETE CASCADE,
    from_model_index INTEGER,
    to_model_index INTEGER,
    feedback_type VARCHAR(50),
    issues_identified INTEGER,
    high_confidence_issues INTEGER,
    feedback_summary JSONB,
    impact_on_accuracy DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visual_feedback_iteration ON visual_feedback_log(iteration_id);
CREATE INDEX IF NOT EXISTS idx_visual_feedback_type ON visual_feedback_log(feedback_type);

-- 4. Create orchestrator decisions log
CREATE TABLE IF NOT EXISTS orchestrator_decisions (
    id SERIAL PRIMARY KEY,
    iteration_id INTEGER REFERENCES iterations(id) ON DELETE CASCADE,
    decision_type VARCHAR(50) CHECK (decision_type IN ('retry', 'continue', 'stop', 'skip')),
    reasoning JSONB,
    factors_considered JSONB,
    threshold_values JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orchestrator_decisions_iteration ON orchestrator_decisions(iteration_id);
CREATE INDEX IF NOT EXISTS idx_orchestrator_decisions_type ON orchestrator_decisions(decision_type);

-- 5. Create materialized view for extraction analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS extraction_analytics_summary AS
SELECT 
    er.run_id,
    er.system_type,
    er.started_at,
    er.status as run_status,
    COUNT(DISTINCT i.id) as total_iterations,
    COUNT(DISTINCT CASE WHEN i.stage = 'structure' THEN i.id END) as structure_iterations,
    COUNT(DISTINCT CASE WHEN i.stage = 'products' THEN i.id END) as products_iterations,
    COUNT(DISTINCT CASE WHEN i.stage = 'details' THEN i.id END) as details_iterations,
    AVG(i.accuracy_score) as avg_accuracy,
    SUM(i.api_cost) as total_cost,
    SUM(i.duration_ms) as total_duration_ms,
    COUNT(DISTINCT i.retry_reason) as unique_retry_reasons,
    COUNT(CASE WHEN i.visual_feedback_received IS NOT NULL THEN 1 END) as iterations_with_visual_feedback,
    MAX(i.products_found) as max_products_found,
    COUNT(CASE WHEN i.success THEN 1 END)::FLOAT / NULLIF(COUNT(i.id), 0) as success_rate
FROM extraction_runs er
LEFT JOIN iterations i ON er.run_id = i.extraction_run_id
GROUP BY er.run_id, er.system_type, er.started_at, er.status;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_analytics_summary_run ON extraction_analytics_summary(run_id);
CREATE INDEX IF NOT EXISTS idx_analytics_summary_started ON extraction_analytics_summary(started_at);

-- 6. Helper functions for analytics queries

-- Function to get extraction flow for a specific run
CREATE OR REPLACE FUNCTION get_extraction_flow(p_run_id VARCHAR(255))
RETURNS TABLE (
    iteration_id INTEGER,
    stage VARCHAR(50),
    model_used VARCHAR(100),
    iteration_number INTEGER,
    retry_reason VARCHAR(255),
    accuracy_score DECIMAL(3,2),
    products_found INTEGER,
    duration_ms INTEGER,
    has_visual_feedback BOOLEAN,
    success BOOLEAN,
    started_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.stage,
        i.model_used,
        i.iteration_number,
        i.retry_reason,
        i.accuracy_score,
        i.products_found,
        i.duration_ms,
        i.visual_feedback_received IS NOT NULL,
        i.success,
        i.started_at
    FROM iterations i
    WHERE i.extraction_run_id = p_run_id
    ORDER BY i.started_at;
END;
$$ LANGUAGE plpgsql;

-- Function to get retry effectiveness
CREATE OR REPLACE FUNCTION get_retry_effectiveness(p_days INTEGER DEFAULT 7)
RETURNS TABLE (
    retry_reason VARCHAR(255),
    total_uses INTEGER,
    success_count INTEGER,
    success_rate DECIMAL(3,2),
    avg_accuracy_improvement DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH retry_data AS (
        SELECT 
            i1.retry_reason,
            i1.accuracy_score as retry_accuracy,
            LAG(i2.accuracy_score) OVER (PARTITION BY i1.extraction_run_id, i1.stage ORDER BY i1.iteration_number) as prev_accuracy
        FROM iterations i1
        JOIN iterations i2 ON i1.extraction_run_id = i2.extraction_run_id 
            AND i1.stage = i2.stage 
            AND i1.iteration_number = i2.iteration_number + 1
        WHERE i1.retry_reason IS NOT NULL
            AND i1.created_at >= NOW() - INTERVAL '1 day' * p_days
    )
    SELECT 
        retry_reason,
        COUNT(*)::INTEGER as total_uses,
        COUNT(CASE WHEN retry_accuracy > prev_accuracy THEN 1 END)::INTEGER as success_count,
        (COUNT(CASE WHEN retry_accuracy > prev_accuracy THEN 1 END)::FLOAT / COUNT(*))::DECIMAL(3,2) as success_rate,
        AVG(retry_accuracy - prev_accuracy)::DECIMAL(3,2) as avg_accuracy_improvement
    FROM retry_data
    GROUP BY retry_reason
    ORDER BY total_uses DESC;
END;
$$ LANGUAGE plpgsql;

-- 7. Grant permissions
GRANT ALL ON iterations TO authenticated;
GRANT ALL ON prompt_execution_log TO authenticated;
GRANT ALL ON visual_feedback_log TO authenticated;
GRANT ALL ON orchestrator_decisions TO authenticated;
GRANT ALL ON extraction_analytics_summary TO authenticated;

-- Enable RLS
ALTER TABLE iterations ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_execution_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE visual_feedback_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE orchestrator_decisions ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow all operations for authenticated users" ON iterations
    FOR ALL USING (true);

CREATE POLICY "Allow all operations for authenticated users" ON prompt_execution_log
    FOR ALL USING (true);

CREATE POLICY "Allow all operations for authenticated users" ON visual_feedback_log
    FOR ALL USING (true);

CREATE POLICY "Allow all operations for authenticated users" ON orchestrator_decisions
    FOR ALL USING (true);

-- Refresh materialized view (run this periodically)
REFRESH MATERIALIZED VIEW extraction_analytics_summary;