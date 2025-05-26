-- Create missing extraction_logs table
CREATE TABLE IF NOT EXISTS extraction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_item_id INTEGER REFERENCES ai_extraction_queue(id),
    timestamp TIMESTAMP DEFAULT NOW(),
    level TEXT,
    component TEXT,
    message TEXT,
    details JSONB
);

-- Create index for performance
CREATE INDEX idx_logs_queue_item ON extraction_logs(queue_item_id);
CREATE INDEX idx_logs_timestamp ON extraction_logs(timestamp);

-- Create trigger to automatically queue approved uploads
CREATE OR REPLACE FUNCTION create_queue_entry_on_approval()
RETURNS TRIGGER AS $$
BEGIN
    -- When an upload is marked as approved/completed, create queue entry
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        INSERT INTO ai_extraction_queue (
            upload_id,
            status,
            ready_media_id,
            enhanced_image_path,
            current_extraction_system,
            created_at,
            processing_attempts
        ) VALUES (
            NEW.id,
            'pending',
            NEW.id,
            NEW.file_path,
            'custom_consensus',
            NOW(),
            0
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on uploads table
DROP TRIGGER IF EXISTS trigger_queue_on_approval ON uploads;
CREATE TRIGGER trigger_queue_on_approval
    AFTER UPDATE ON uploads
    FOR EACH ROW
    EXECUTE FUNCTION create_queue_entry_on_approval();