-- Create audit tables for data protection
-- This prevents accidental data loss like what happened to queue item 9

-- 1. Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    user_id TEXT,
    ip_address INET,
    user_agent TEXT,
    environment TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Index for performance
    INDEX idx_audit_table_record (table_name, record_id),
    INDEX idx_audit_timestamp (timestamp DESC)
);

-- 2. Create data backups table
CREATE TABLE IF NOT EXISTS data_backups (
    id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    backup_data JSONB NOT NULL,
    backup_reason TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days'),
    
    -- Index for cleanup
    INDEX idx_backup_expires (expires_at)
);

-- 3. Create function to audit queue changes
CREATE OR REPLACE FUNCTION audit_queue_changes() 
RETURNS TRIGGER AS $$
DECLARE
    changed_fields TEXT[];
    old_json JSONB;
    new_json JSONB;
BEGIN
    -- Convert to JSONB for comparison
    old_json := to_jsonb(OLD);
    new_json := to_jsonb(NEW);
    
    -- Find changed fields
    SELECT ARRAY_AGG(key) INTO changed_fields
    FROM (
        SELECT key 
        FROM jsonb_each_text(old_json)
        WHERE old_json->key IS DISTINCT FROM new_json->key
    ) changes;
    
    -- Insert audit record
    INSERT INTO audit_log (
        table_name, 
        record_id, 
        action, 
        old_data, 
        new_data,
        changed_fields,
        user_id,
        environment
    ) VALUES (
        TG_TABLE_NAME,
        NEW.id,
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN old_json ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN new_json ELSE NULL END,
        changed_fields,
        current_user,
        current_setting('app.environment', true)
    );
    
    -- Auto-backup if extraction_result is being changed
    IF TG_OP = 'UPDATE' AND 'extraction_result' = ANY(changed_fields) THEN
        INSERT INTO data_backups (
            table_name,
            record_id,
            backup_data,
            backup_reason,
            created_by
        ) VALUES (
            TG_TABLE_NAME,
            OLD.id,
            old_json,
            'Automatic backup before extraction_result update',
            current_user
        );
    END IF;
    
    -- Prevent test data in production
    IF current_setting('app.environment', true) = 'production' THEN
        IF NEW.extraction_result IS NOT NULL THEN
            -- Check for known test patterns
            IF NEW.extraction_result::text ~* '(coca.?cola|pepsi|sprite|mountain.?dew)' 
               AND NEW.extraction_result::text ~* '355ml' THEN
                RAISE EXCEPTION 'Test data patterns detected in production update';
            END IF;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Create trigger on ai_extraction_queue
DROP TRIGGER IF EXISTS audit_queue_trigger ON ai_extraction_queue;
CREATE TRIGGER audit_queue_trigger
AFTER INSERT OR UPDATE OR DELETE ON ai_extraction_queue
FOR EACH ROW EXECUTE FUNCTION audit_queue_changes();

-- 5. Create view to see recent dangerous changes
CREATE OR REPLACE VIEW dangerous_changes AS
SELECT 
    al.timestamp,
    al.table_name,
    al.record_id,
    al.action,
    al.changed_fields,
    al.user_id,
    CASE 
        WHEN al.new_data::text ~* 'test|fake|dummy|placeholder' THEN 'Test data detected'
        WHEN 'extraction_result' = ANY(al.changed_fields) AND al.old_data IS NOT NULL THEN 'Overwrote existing extraction'
        WHEN 'status' = ANY(al.changed_fields) AND al.old_data->>'status' = 'completed' THEN 'Modified completed item'
        ELSE NULL
    END as warning
FROM audit_log al
WHERE al.timestamp > NOW() - INTERVAL '7 days'
AND (
    al.new_data::text ~* 'test|fake|dummy|placeholder'
    OR ('extraction_result' = ANY(al.changed_fields) AND al.old_data IS NOT NULL)
    OR ('status' = ANY(al.changed_fields) AND al.old_data->>'status' = 'completed')
)
ORDER BY al.timestamp DESC;

-- 6. Create function to restore from backup
CREATE OR REPLACE FUNCTION restore_from_backup(
    p_backup_id BIGINT
) RETURNS BOOLEAN AS $$
DECLARE
    v_backup RECORD;
    v_sql TEXT;
BEGIN
    -- Get backup
    SELECT * INTO v_backup FROM data_backups WHERE id = p_backup_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Backup % not found', p_backup_id;
    END IF;
    
    -- Build dynamic SQL to restore
    v_sql := format(
        'UPDATE %I SET %s WHERE id = %s',
        v_backup.table_name,
        (
            SELECT string_agg(
                format('%I = %L', key, value),
                ', '
            )
            FROM jsonb_each_text(v_backup.backup_data)
            WHERE key != 'id'
        ),
        v_backup.record_id
    );
    
    -- Execute restore
    EXECUTE v_sql;
    
    -- Log the restore
    INSERT INTO audit_log (
        table_name,
        record_id,
        action,
        new_data,
        user_id,
        environment
    ) VALUES (
        v_backup.table_name,
        v_backup.record_id,
        'RESTORE',
        v_backup.backup_data,
        current_user,
        'restore_operation'
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 7. Add comment to warn about queue item 9
COMMENT ON TABLE ai_extraction_queue IS 
'Extraction queue. WARNING: Item 9 contains valuable Co-op production data that was overwritten by test data on 2025-06-09. Do not modify without backup!';

-- 8. Grant appropriate permissions
GRANT SELECT ON audit_log TO authenticated;
GRANT SELECT ON data_backups TO authenticated;
GRANT SELECT ON dangerous_changes TO authenticated;