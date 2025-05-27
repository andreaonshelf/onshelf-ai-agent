-- Create extraction_runs table for tracking extraction pipeline state
-- This table stores detailed information about each extraction run including stages, metrics, and results

CREATE TABLE IF NOT EXISTS extraction_runs (
    -- Primary key
    run_id VARCHAR(255) PRIMARY KEY,
    
    -- Foreign keys
    queue_item_id INTEGER NOT NULL,
    upload_id VARCHAR(255) NOT NULL,
    
    -- Run metadata
    status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'requires_review')),
    current_stage VARCHAR(50) NOT NULL CHECK (current_stage IN ('queued', 'initializing', 'structure_extraction', 'product_extraction', 'detail_extraction', 'validation', 'human_review', 'completed', 'failed')),
    system VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    
    -- Stage-specific data
    stages JSONB NOT NULL DEFAULT '{}',
    
    -- Overall metrics
    overall_metrics JSONB NOT NULL DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    -- Error tracking
    error_message TEXT,
    
    -- Result data
    result_data JSONB,
    
    -- Indexes for common queries
    CONSTRAINT fk_queue_item FOREIGN KEY (queue_item_id) REFERENCES ai_extraction_queue(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_extraction_runs_queue_item_id ON extraction_runs(queue_item_id);
CREATE INDEX idx_extraction_runs_upload_id ON extraction_runs(upload_id);
CREATE INDEX idx_extraction_runs_status ON extraction_runs(status);
CREATE INDEX idx_extraction_runs_created_at ON extraction_runs(created_at);
CREATE INDEX idx_extraction_runs_current_stage ON extraction_runs(current_stage);

-- Create GIN indexes for JSONB columns for efficient querying
CREATE INDEX idx_extraction_runs_stages ON extraction_runs USING GIN (stages);
CREATE INDEX idx_extraction_runs_overall_metrics ON extraction_runs USING GIN (overall_metrics);
CREATE INDEX idx_extraction_runs_result_data ON extraction_runs USING GIN (result_data);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_extraction_runs_updated_at 
    BEFORE UPDATE ON extraction_runs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE extraction_runs IS 'Tracks the state and progress of extraction pipeline runs';
COMMENT ON COLUMN extraction_runs.run_id IS 'Unique identifier for the extraction run';
COMMENT ON COLUMN extraction_runs.queue_item_id IS 'Reference to the queue item being processed';
COMMENT ON COLUMN extraction_runs.upload_id IS 'Reference to the uploaded image';
COMMENT ON COLUMN extraction_runs.status IS 'Overall status of the extraction run';
COMMENT ON COLUMN extraction_runs.current_stage IS 'Current stage in the extraction pipeline';
COMMENT ON COLUMN extraction_runs.system IS 'Extraction system used (custom_consensus, langgraph, hybrid)';
COMMENT ON COLUMN extraction_runs.configuration IS 'Complete extraction configuration including models and prompts';
COMMENT ON COLUMN extraction_runs.stages IS 'Detailed metrics and data for each stage';
COMMENT ON COLUMN extraction_runs.overall_metrics IS 'Aggregated metrics for the entire run';
COMMENT ON COLUMN extraction_runs.error_message IS 'Error message if the run failed';
COMMENT ON COLUMN extraction_runs.result_data IS 'Final results including accuracy and planogram reference';