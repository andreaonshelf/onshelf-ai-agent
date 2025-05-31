-- Create table to track model usage per extraction
CREATE TABLE IF NOT EXISTS model_usage (
    id SERIAL PRIMARY KEY,
    queue_item_id INTEGER REFERENCES ai_extraction_queue(id),
    extraction_run_id TEXT,
    stage TEXT NOT NULL, -- 'structure', 'products', 'details', 'validation', 'orchestrator'
    model_id TEXT NOT NULL, -- 'gpt-4o', 'claude-4-opus', etc.
    model_provider TEXT NOT NULL, -- 'openai', 'anthropic', 'google'
    iteration_number INTEGER,
    temperature FLOAT DEFAULT 0.7,
    
    -- Request/Response details
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Performance metrics
    response_time_ms INTEGER,
    api_cost DECIMAL(10, 4),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for analytics
    INDEX idx_model_usage_queue_item (queue_item_id),
    INDEX idx_model_usage_stage (stage),
    INDEX idx_model_usage_model (model_id),
    INDEX idx_model_usage_created (created_at)
);

-- Create table for configuration analytics
CREATE TABLE IF NOT EXISTS configuration_usage (
    id SERIAL PRIMARY KEY,
    configuration_name TEXT,
    configuration_id TEXT,
    
    -- Overall config
    system TEXT, -- 'custom_consensus', 'langgraph', 'hybrid'
    orchestrator_model TEXT,
    orchestrator_prompt TEXT,
    temperature FLOAT,
    max_budget DECIMAL(10, 2),
    
    -- Stage configurations (JSONB for flexibility)
    stage_models JSONB, -- {"structure": ["gpt-4o", "claude-4-opus"], "products": [...]}
    
    -- Usage tracking
    times_used INTEGER DEFAULT 1,
    last_used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance aggregates (updated as runs complete)
    avg_accuracy FLOAT,
    avg_cost DECIMAL(10, 4),
    avg_duration_seconds INTEGER,
    successful_runs INTEGER DEFAULT 0,
    failed_runs INTEGER DEFAULT 0,
    
    INDEX idx_configuration_usage_name (configuration_name),
    INDEX idx_configuration_usage_system (system)
);

-- Create view for model performance analytics
CREATE OR REPLACE VIEW model_performance_analytics AS
SELECT 
    mu.model_id,
    mu.model_provider,
    mu.stage,
    COUNT(*) as usage_count,
    AVG(mu.api_cost) as avg_cost_per_call,
    SUM(mu.api_cost) as total_cost,
    AVG(mu.response_time_ms) as avg_response_time_ms,
    AVG(mu.total_tokens) as avg_tokens_used,
    SUM(CASE WHEN mu.success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate,
    
    -- Join with queue results for accuracy metrics
    AVG(q.final_accuracy) as avg_extraction_accuracy,
    COUNT(DISTINCT mu.queue_item_id) as unique_extractions
FROM 
    model_usage mu
    LEFT JOIN ai_extraction_queue q ON mu.queue_item_id = q.id
GROUP BY 
    mu.model_id, mu.model_provider, mu.stage;

-- Create view for configuration performance
CREATE OR REPLACE VIEW configuration_performance AS
SELECT 
    cu.configuration_name,
    cu.system,
    cu.orchestrator_model,
    cu.times_used,
    cu.avg_accuracy,
    cu.avg_cost,
    cu.avg_duration_seconds,
    cu.successful_runs,
    cu.failed_runs,
    CASE 
        WHEN (cu.successful_runs + cu.failed_runs) > 0 
        THEN cu.successful_runs::FLOAT / (cu.successful_runs + cu.failed_runs)
        ELSE 0 
    END as success_rate,
    cu.stage_models
FROM 
    configuration_usage cu
ORDER BY 
    cu.times_used DESC;

-- Function to log model usage
CREATE OR REPLACE FUNCTION log_model_usage(
    p_queue_item_id INTEGER,
    p_extraction_run_id TEXT,
    p_stage TEXT,
    p_model_id TEXT,
    p_model_provider TEXT,
    p_iteration_number INTEGER,
    p_temperature FLOAT,
    p_prompt_tokens INTEGER,
    p_completion_tokens INTEGER,
    p_response_time_ms INTEGER,
    p_api_cost DECIMAL,
    p_success BOOLEAN,
    p_error_message TEXT DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    v_usage_id INTEGER;
BEGIN
    INSERT INTO model_usage (
        queue_item_id,
        extraction_run_id,
        stage,
        model_id,
        model_provider,
        iteration_number,
        temperature,
        prompt_tokens,
        completion_tokens,
        total_tokens,
        response_time_ms,
        api_cost,
        success,
        error_message
    ) VALUES (
        p_queue_item_id,
        p_extraction_run_id,
        p_stage,
        p_model_id,
        p_model_provider,
        p_iteration_number,
        p_temperature,
        p_prompt_tokens,
        p_completion_tokens,
        p_prompt_tokens + p_completion_tokens,
        p_response_time_ms,
        p_api_cost,
        p_success,
        p_error_message
    ) RETURNING id INTO v_usage_id;
    
    RETURN v_usage_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update configuration usage stats
CREATE OR REPLACE FUNCTION update_configuration_stats(
    p_configuration_name TEXT,
    p_accuracy FLOAT,
    p_cost DECIMAL,
    p_duration_seconds INTEGER,
    p_success BOOLEAN
) RETURNS VOID AS $$
BEGIN
    UPDATE configuration_usage
    SET 
        times_used = times_used + 1,
        last_used_at = NOW(),
        avg_accuracy = CASE 
            WHEN avg_accuracy IS NULL THEN p_accuracy
            ELSE ((avg_accuracy * (times_used - 1)) + p_accuracy) / times_used
        END,
        avg_cost = CASE 
            WHEN avg_cost IS NULL THEN p_cost
            ELSE ((avg_cost * (times_used - 1)) + p_cost) / times_used
        END,
        avg_duration_seconds = CASE 
            WHEN avg_duration_seconds IS NULL THEN p_duration_seconds
            ELSE ((avg_duration_seconds * (times_used - 1)) + p_duration_seconds) / times_used::INTEGER
        END,
        successful_runs = successful_runs + CASE WHEN p_success THEN 1 ELSE 0 END,
        failed_runs = failed_runs + CASE WHEN NOT p_success THEN 1 ELSE 0 END
    WHERE configuration_name = p_configuration_name;
END;
$$ LANGUAGE plpgsql;

-- Add comments
COMMENT ON TABLE model_usage IS 'Tracks individual model API calls for analytics and cost tracking';
COMMENT ON TABLE configuration_usage IS 'Tracks configuration performance and usage patterns';
COMMENT ON VIEW model_performance_analytics IS 'Aggregated model performance metrics for analytics dashboards';
COMMENT ON VIEW configuration_performance IS 'Configuration effectiveness metrics for optimization';