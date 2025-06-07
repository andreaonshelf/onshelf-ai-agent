1-- Create tables for image quality analysis and model performance tracking

-- Image Quality Analysis Table
CREATE TABLE IF NOT EXISTS image_quality_analysis (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(255),
    filename VARCHAR(255),
    
    -- Quality Metrics (0-100 scale)
    brightness FLOAT,
    contrast FLOAT,
    sharpness FLOAT,
    noise_level FLOAT,
    color_saturation FLOAT,
    edge_density FLOAT,
    occlusion_score FLOAT,
    overall_quality FLOAT,
    
    -- Detected Issues
    issues JSONB DEFAULT '{}',
    
    -- Recommendations
    recommended_system VARCHAR(50),
    recommended_models JSONB DEFAULT '{}',
    confidence FLOAT,
    
    -- Metadata
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Performance Feedback Table
CREATE TABLE IF NOT EXISTS model_performance_feedback (
    id SERIAL PRIMARY KEY,
    image_id VARCHAR(255),
    upload_id VARCHAR(255),
    
    -- Image quality metrics at time of extraction
    image_metrics JSONB,
    
    -- Actual performance results
    actual_performance JSONB,  -- {model_name: accuracy_score}
    
    -- Which models were used
    models_used JSONB,
    system_used VARCHAR(50),
    
    -- Extraction results
    extraction_success BOOLEAN,
    extraction_accuracy FLOAT,
    extraction_time FLOAT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model Performance Statistics (Aggregated)
CREATE TABLE IF NOT EXISTS model_performance_stats (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(50),
    
    -- Performance by image quality
    performance_by_quality JSONB DEFAULT '{}',  -- {quality_range: {accuracy, count, avg_time}}
    
    -- Performance by issue type
    performance_by_issue JSONB DEFAULT '{}',  -- {issue_type: {accuracy, count, avg_time}}
    
    -- Overall stats
    total_uses INTEGER DEFAULT 0,
    avg_accuracy FLOAT,
    avg_processing_time FLOAT,
    
    -- Last updated
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Image Quality Patterns (for learning)
CREATE TABLE IF NOT EXISTS image_quality_patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(100),
    
    -- Pattern definition
    quality_conditions JSONB,  -- {brightness: [min, max], contrast: [min, max], etc}
    detected_issues JSONB,     -- [list of common issues]
    
    -- Best performing configuration
    best_system VARCHAR(50),
    best_models JSONB,
    avg_accuracy FLOAT,
    sample_count INTEGER,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_image_quality_upload_id ON image_quality_analysis(upload_id);
CREATE INDEX IF NOT EXISTS idx_image_quality_overall ON image_quality_analysis(overall_quality);
CREATE INDEX IF NOT EXISTS idx_image_quality_analyzed_at ON image_quality_analysis(analyzed_at);

CREATE INDEX IF NOT EXISTS idx_performance_feedback_image_id ON model_performance_feedback(image_id);
CREATE INDEX IF NOT EXISTS idx_performance_feedback_created ON model_performance_feedback(created_at);

CREATE INDEX IF NOT EXISTS idx_performance_stats_model ON model_performance_stats(model_name);

-- Function to update model performance stats
CREATE OR REPLACE FUNCTION update_model_performance_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- This would aggregate performance data and update the stats table
    -- Implementation depends on specific requirements
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update stats when new feedback is added
CREATE TRIGGER update_performance_stats_trigger
AFTER INSERT ON model_performance_feedback
FOR EACH ROW
EXECUTE FUNCTION update_model_performance_stats();