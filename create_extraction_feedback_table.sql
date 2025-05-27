-- Create extraction_feedback table for storing human feedback on extractions
-- This table captures ratings, comments, and learning data from human reviewers

CREATE TABLE IF NOT EXISTS extraction_feedback (
    -- Primary key
    id SERIAL PRIMARY KEY,
    
    -- Foreign keys
    queue_item_id INTEGER NOT NULL,
    upload_id VARCHAR(255) NOT NULL,
    
    -- Ratings (1-5 stars)
    extraction_rating INTEGER NOT NULL CHECK (extraction_rating >= 1 AND extraction_rating <= 5),
    planogram_rating INTEGER NOT NULL CHECK (planogram_rating >= 1 AND planogram_rating <= 5),
    
    -- Feedback text
    worked_well TEXT,
    needs_improvement TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL DEFAULT 'human_reviewer',
    
    -- Indexes for common queries
    CONSTRAINT fk_feedback_queue_item FOREIGN KEY (queue_item_id) REFERENCES ai_extraction_queue(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_extraction_feedback_queue_item_id ON extraction_feedback(queue_item_id);
CREATE INDEX idx_extraction_feedback_upload_id ON extraction_feedback(upload_id);
CREATE INDEX idx_extraction_feedback_created_at ON extraction_feedback(created_at);
CREATE INDEX idx_extraction_feedback_ratings ON extraction_feedback(extraction_rating, planogram_rating);

-- Create GIN index for metadata
CREATE INDEX idx_extraction_feedback_metadata ON extraction_feedback USING GIN (metadata);

-- Add comments for documentation
COMMENT ON TABLE extraction_feedback IS 'Stores human feedback on extraction and planogram quality';
COMMENT ON COLUMN extraction_feedback.queue_item_id IS 'Reference to the queue item being evaluated';
COMMENT ON COLUMN extraction_feedback.upload_id IS 'Reference to the uploaded image';
COMMENT ON COLUMN extraction_feedback.extraction_rating IS 'Star rating (1-5) for extraction quality';
COMMENT ON COLUMN extraction_feedback.planogram_rating IS 'Star rating (1-5) for planogram quality';
COMMENT ON COLUMN extraction_feedback.worked_well IS 'Text description of what worked well';
COMMENT ON COLUMN extraction_feedback.needs_improvement IS 'Text description of what needs improvement';
COMMENT ON COLUMN extraction_feedback.metadata IS 'Additional metadata including accuracy, system used, etc.';
COMMENT ON COLUMN extraction_feedback.created_by IS 'Identifier of the reviewer (future: actual user ID)';

-- Create view for feedback analytics
CREATE OR REPLACE VIEW feedback_analytics AS
SELECT 
    ef.queue_item_id,
    ef.upload_id,
    COUNT(*) as feedback_count,
    AVG(ef.extraction_rating) as avg_extraction_rating,
    AVG(ef.planogram_rating) as avg_planogram_rating,
    AVG((ef.extraction_rating + ef.planogram_rating) / 2.0) as avg_overall_rating,
    MIN(ef.created_at) as first_feedback_at,
    MAX(ef.created_at) as latest_feedback_at,
    array_agg(DISTINCT ef.created_by) as reviewers,
    COUNT(CASE WHEN ef.extraction_rating <= 2 THEN 1 END) as low_extraction_count,
    COUNT(CASE WHEN ef.planogram_rating <= 2 THEN 1 END) as low_planogram_count
FROM extraction_feedback ef
GROUP BY ef.queue_item_id, ef.upload_id;

COMMENT ON VIEW feedback_analytics IS 'Aggregated feedback statistics per queue item';