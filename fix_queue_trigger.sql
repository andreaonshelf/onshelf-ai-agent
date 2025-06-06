-- Fix the trigger to properly set enhanced_image_path for new queue entries

CREATE OR REPLACE FUNCTION create_queue_entry_on_approval()
RETURNS TRIGGER AS $$
DECLARE
    v_image_path TEXT;
BEGIN
    -- When an upload is marked as approved/completed, create queue entry
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        -- Get the image path from media_files table
        SELECT file_path INTO v_image_path
        FROM media_files
        WHERE upload_id = NEW.id
        AND file_path IS NOT NULL
        ORDER BY created_at ASC
        LIMIT 1;
        
        -- Only create queue entry if we found an image
        IF v_image_path IS NOT NULL THEN
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
                v_image_path,  -- Use the path from media_files
                'custom_consensus',
                NOW(),
                0
            );
        ELSE
            -- Log warning if no image found
            RAISE WARNING 'No image path found for upload %', NEW.id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
DROP TRIGGER IF EXISTS trigger_queue_on_approval ON uploads;
CREATE TRIGGER trigger_queue_on_approval
    AFTER UPDATE ON uploads
    FOR EACH ROW
    EXECUTE FUNCTION create_queue_entry_on_approval();