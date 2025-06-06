-- Fix the trigger to properly create queue entries when media is approved

-- First, create the trigger function that watches for media approval
CREATE OR REPLACE FUNCTION create_queue_entry_on_media_approval()
RETURNS TRIGGER AS $$
DECLARE
    v_upload_id TEXT;
    v_existing_queue_id INTEGER;
BEGIN
    -- When a media file is marked as approved, create queue entry
    IF NEW.approval_status = 'approved' AND (OLD.approval_status IS NULL OR OLD.approval_status != 'approved') THEN
        -- Get the upload_id from this media file
        v_upload_id := NEW.upload_id;
        
        -- Check if queue entry already exists for this upload
        SELECT id INTO v_existing_queue_id
        FROM ai_extraction_queue
        WHERE upload_id = v_upload_id
        LIMIT 1;
        
        -- Only create queue entry if it doesn't exist
        IF v_existing_queue_id IS NULL AND v_upload_id IS NOT NULL THEN
            INSERT INTO ai_extraction_queue (
                upload_id,
                status,
                ready_media_id,
                enhanced_image_path,
                current_extraction_system,
                created_at,
                processing_attempts
            ) VALUES (
                v_upload_id,
                'pending',
                NEW.media_id,
                NEW.file_path,
                'custom_consensus',
                NOW(),
                0
            );
            
            RAISE NOTICE 'Created queue entry for approved media % with upload %', NEW.media_id, v_upload_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop old trigger if it exists
DROP TRIGGER IF EXISTS trigger_queue_on_media_approval ON media_files;

-- Create the trigger on media_files table
CREATE TRIGGER trigger_queue_on_media_approval
    AFTER UPDATE ON media_files
    FOR EACH ROW
    EXECUTE FUNCTION create_queue_entry_on_media_approval();

-- Also update the uploads trigger to handle the case where entire upload is marked as completed
CREATE OR REPLACE FUNCTION create_queue_entry_on_upload_approval()
RETURNS TRIGGER AS $$
DECLARE
    v_image_path TEXT;
    v_media_id TEXT;
    v_existing_queue_id INTEGER;
BEGIN
    -- When an upload is marked with approval_status = 'approved', create queue entry
    IF NEW.approval_status = 'approved' AND (OLD.approval_status IS NULL OR OLD.approval_status != 'approved') THEN
        -- Check if queue entry already exists
        SELECT id INTO v_existing_queue_id
        FROM ai_extraction_queue
        WHERE upload_id = NEW.id
        LIMIT 1;
        
        IF v_existing_queue_id IS NULL THEN
            -- Get the first approved image from media_files
            SELECT file_path, media_id INTO v_image_path, v_media_id
            FROM media_files
            WHERE upload_id = NEW.id
            AND approval_status = 'approved'
            AND file_path IS NOT NULL
            ORDER BY created_at ASC
            LIMIT 1;
            
            -- Create queue entry if we found an approved image
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
                    v_media_id,
                    v_image_path,
                    'custom_consensus',
                    NOW(),
                    0
                );
                
                RAISE NOTICE 'Created queue entry for approved upload %', NEW.id;
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop and recreate trigger on uploads table
DROP TRIGGER IF EXISTS trigger_queue_on_upload_approval ON uploads;
CREATE TRIGGER trigger_queue_on_upload_approval
    AFTER UPDATE ON uploads
    FOR EACH ROW
    EXECUTE FUNCTION create_queue_entry_on_upload_approval();

-- Now add all currently approved items that are missing from the queue
INSERT INTO ai_extraction_queue (
    upload_id,
    status,
    ready_media_id,
    enhanced_image_path,
    current_extraction_system,
    created_at,
    processing_attempts
)
SELECT DISTINCT
    m.upload_id,
    'pending',
    m.media_id,
    m.file_path,
    'custom_consensus',
    NOW(),
    0
FROM media_files m
WHERE m.approval_status = 'approved'
AND m.file_path IS NOT NULL
AND NOT EXISTS (
    SELECT 1 
    FROM ai_extraction_queue q 
    WHERE q.upload_id = m.upload_id
)
AND m.upload_id IS NOT NULL;