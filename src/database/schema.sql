-- OnShelf AI Agent Database Schema
-- Integrates with existing OnShelf database structure

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS onshelf_core;

-- =====================================================
-- AI AGENT TRACKING TABLES
-- =====================================================

-- Agent orchestration tracking
CREATE TABLE IF NOT EXISTS onshelf_core.ai_agents (
    agent_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    upload_id TEXT NOT NULL REFERENCES onshelf_core.uploads(upload_id),
    status TEXT NOT NULL CHECK (status IN ('initializing', 'running', 'completed', 'failed', 'escalated')),
    target_accuracy DECIMAL(3,2) NOT NULL DEFAULT 0.95,
    final_accuracy DECIMAL(3,2),
    iterations_completed INTEGER DEFAULT 0,
    max_iterations INTEGER NOT NULL DEFAULT 5,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_duration_seconds INTEGER,
    total_api_costs DECIMAL(8,2) DEFAULT 0.00,
    escalation_reason TEXT,
    human_review_required BOOLEAN DEFAULT FALSE,
    confidence_in_result DECIMAL(3,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Indexes
    INDEX idx_agents_upload_id ON onshelf_core.ai_agents(upload_id),
    INDEX idx_agents_status ON onshelf_core.ai_agents(status),
    INDEX idx_agents_started_at ON onshelf_core.ai_agents(started_at)
);

-- Agent iteration tracking
CREATE TABLE IF NOT EXISTS onshelf_core.agent_iterations (
    iteration_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    agent_id TEXT NOT NULL REFERENCES onshelf_core.ai_agents(agent_id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    extraction_steps JSONB NOT NULL,
    extraction_result JSONB NOT NULL,
    planogram_data JSONB NOT NULL,
    mismatch_analysis JSONB NOT NULL,
    accuracy_achieved DECIMAL(3,2) NOT NULL,
    issues_found INTEGER DEFAULT 0,
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    models_used JSONB,
    iteration_duration_seconds INTEGER,
    api_costs JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(agent_id, iteration_number),
    
    -- Indexes
    INDEX idx_iterations_agent_id ON onshelf_core.agent_iterations(agent_id),
    INDEX idx_iterations_accuracy ON onshelf_core.agent_iterations(accuracy_achieved)
);

-- Generated planograms
CREATE TABLE IF NOT EXISTS onshelf_core.generated_planograms (
    planogram_id TEXT PRIMARY KEY,
    extraction_id TEXT NOT NULL,
    agent_id TEXT REFERENCES onshelf_core.ai_agents(agent_id),
    iteration_number INTEGER,
    planogram_data JSONB NOT NULL,
    canvas_javascript TEXT,
    svg_data TEXT,
    accuracy_score DECIMAL(3,2),
    total_products INTEGER,
    total_facings INTEGER,
    space_utilization DECIMAL(5,2),
    validation_results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_planograms_agent_id ON onshelf_core.generated_planograms(agent_id),
    INDEX idx_planograms_extraction_id ON onshelf_core.generated_planograms(extraction_id)
);

-- Mismatch tracking for analysis
CREATE TABLE IF NOT EXISTS onshelf_core.mismatch_issues (
    issue_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    agent_id TEXT NOT NULL REFERENCES onshelf_core.ai_agents(agent_id) ON DELETE CASCADE,
    iteration_number INTEGER NOT NULL,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    location TEXT NOT NULL,
    description TEXT,
    root_cause TEXT CHECK (root_cause IN ('structure_error', 'extraction_error', 'visualization_error', 'coordinate_error', 'quantity_error', 'price_error')),
    confidence DECIMAL(3,2),
    accuracy_impact DECIMAL(3,2),
    suggested_fix TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_mismatches_agent_id ON onshelf_core.mismatch_issues(agent_id),
    INDEX idx_mismatches_severity ON onshelf_core.mismatch_issues(severity)
);

-- =====================================================
-- VIEWS FOR ANALYTICS
-- =====================================================

-- Agent performance view
CREATE OR REPLACE VIEW onshelf_core.v_agent_performance AS
SELECT 
    a.agent_id,
    a.upload_id,
    a.status,
    a.final_accuracy,
    a.iterations_completed,
    a.processing_duration_seconds,
    a.total_api_costs,
    a.human_review_required,
    COUNT(DISTINCT ai.iteration_id) as total_iterations,
    AVG(ai.accuracy_achieved) as avg_iteration_accuracy,
    MAX(ai.accuracy_achieved) as best_iteration_accuracy,
    SUM(ai.issues_found) as total_issues_found,
    u.store_id,
    u.created_at as upload_date
FROM onshelf_core.ai_agents a
LEFT JOIN onshelf_core.agent_iterations ai ON a.agent_id = ai.agent_id
LEFT JOIN onshelf_core.uploads u ON a.upload_id = u.upload_id
GROUP BY a.agent_id, u.store_id, u.created_at;

-- Daily agent statistics
CREATE OR REPLACE VIEW onshelf_core.v_daily_agent_stats AS
SELECT 
    DATE(started_at) as date,
    COUNT(*) as total_agents,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
    COUNT(CASE WHEN status = 'escalated' THEN 1 END) as escalated,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
    AVG(CASE WHEN status = 'completed' THEN final_accuracy END) as avg_accuracy,
    AVG(iterations_completed) as avg_iterations,
    AVG(processing_duration_seconds) as avg_duration_seconds,
    SUM(total_api_costs) as total_api_costs,
    COUNT(CASE WHEN final_accuracy >= target_accuracy THEN 1 END)::FLOAT / 
        NULLIF(COUNT(CASE WHEN status IN ('completed', 'escalated') THEN 1 END), 0) as success_rate
FROM onshelf_core.ai_agents
GROUP BY DATE(started_at)
ORDER BY date DESC;

-- =====================================================
-- FUNCTIONS FOR PUBLIC SCHEMA ACCESS
-- =====================================================

-- Start AI agent function
CREATE OR REPLACE FUNCTION public.start_ai_agent(
    p_upload_id TEXT,
    p_target_accuracy DECIMAL(3,2) DEFAULT 0.95,
    p_max_iterations INTEGER DEFAULT 5
) RETURNS TEXT AS $$
DECLARE
    v_agent_id TEXT;
BEGIN
    v_agent_id := gen_random_uuid()::TEXT;
    
    INSERT INTO onshelf_core.ai_agents(
        agent_id, 
        upload_id, 
        status, 
        target_accuracy, 
        max_iterations
    ) VALUES (
        v_agent_id, 
        p_upload_id, 
        'initializing', 
        p_target_accuracy, 
        p_max_iterations
    );
    
    RETURN v_agent_id;
END;
$$ LANGUAGE plpgsql;

-- Save agent result function
CREATE OR REPLACE FUNCTION public.save_agent_result(
    p_agent_id TEXT,
    p_final_accuracy DECIMAL(3,2),
    p_iterations_completed INTEGER,
    p_processing_duration INTEGER,
    p_escalation_reason TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE onshelf_core.ai_agents
    SET 
        status = CASE 
            WHEN p_escalation_reason IS NOT NULL THEN 'escalated'
            WHEN p_final_accuracy >= target_accuracy THEN 'completed'
            ELSE 'completed'
        END,
        final_accuracy = p_final_accuracy,
        iterations_completed = p_iterations_completed,
        processing_duration_seconds = p_processing_duration,
        escalation_reason = p_escalation_reason,
        human_review_required = (p_escalation_reason IS NOT NULL),
        completed_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Get agent status function
CREATE OR REPLACE FUNCTION public.get_agent_status(p_agent_id TEXT)
RETURNS TABLE(
    status TEXT,
    current_accuracy DECIMAL(3,2),
    iterations_completed INTEGER,
    latest_issues INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.status,
        COALESCE(
            (SELECT accuracy_achieved 
             FROM onshelf_core.agent_iterations 
             WHERE agent_id = p_agent_id 
             ORDER BY iteration_number DESC 
             LIMIT 1),
            0.0
        ) as current_accuracy,
        a.iterations_completed,
        COALESCE(
            (SELECT issues_found 
             FROM onshelf_core.agent_iterations 
             WHERE agent_id = p_agent_id 
             ORDER BY iteration_number DESC 
             LIMIT 1),
            0
        ) as latest_issues
    FROM onshelf_core.ai_agents a
    WHERE a.agent_id = p_agent_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Update agent status based on iterations
CREATE OR REPLACE FUNCTION onshelf_core.update_agent_from_iteration()
RETURNS TRIGGER AS $$
BEGIN
    -- Update agent accuracy and iteration count
    UPDATE onshelf_core.ai_agents
    SET 
        iterations_completed = NEW.iteration_number,
        status = CASE 
            WHEN NEW.accuracy_achieved >= target_accuracy THEN 'completed'
            WHEN status NOT IN ('failed', 'escalated') THEN 'running'
            ELSE status
        END
    WHERE agent_id = NEW.agent_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_agent_from_iteration
AFTER INSERT ON onshelf_core.agent_iterations
FOR EACH ROW
EXECUTE FUNCTION onshelf_core.update_agent_from_iteration();

-- =====================================================
-- PERMISSIONS (adjust based on your user structure)
-- =====================================================

-- Grant permissions to application user
GRANT USAGE ON SCHEMA onshelf_core TO authenticated;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA onshelf_core TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated; 