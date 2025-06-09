# CRITICAL SECURITY REPORT: Test Data Overwriting Production Data

## Executive Summary
A critical data integrity issue was discovered where test/debug scripts can overwrite real production extraction data. Queue item 9's real Co-op extraction results were replaced with fake soda products, destroying valuable production data.

## Root Cause Analysis

### 1. The Incident
- **What happened**: Real extraction data for Co-op Food - Greenwich was overwritten with test data
- **When**: June 9, 2025, after the real extraction completed on June 8
- **How**: Script `add_test_extraction_data.py` directly updated the database
- **Impact**: Lost real extraction results worth $0.12 in API costs and ~45 minutes processing time

### 2. The Culprit Script
```python
# add_test_extraction_data.py - Line 96
result = supabase.table("ai_extraction_queue").update({
    "extraction_result": test_extraction,  # OVERWRITES REAL DATA!
    "planogram_result": test_planogram,
    # ...
}).eq("id", 9).execute()  # HARDCODED PRODUCTION ID!
```

## Security Vulnerabilities Identified

### 1. **No Environment Separation**
- Same database for development and production
- No safeguards against modifying production data
- Test scripts mixed with production code

### 2. **Unrestricted Database Access**
- Direct write access to all tables
- No row-level security policies
- Service key exposed in multiple scripts

### 3. **No Audit Trail**
- Can't track who ran destructive scripts
- No backup before overwrites
- No change history

### 4. **Poor Code Organization**
- 15+ scripts that can modify/delete data
- Test utilities mixed with production code
- No clear separation of concerns

## Other Dangerous Scripts Found

1. **HARD_RESET_ALL_DATA.py** - Resets ALL queue items
2. **clear_all_fake_data.py** - Deletes data based on patterns
3. **reset_fake_completed.py** - Modifies completed items
4. **cleanup_fake_data.sql** - Direct SQL deletions
5. **delete_all_prompts.sql** - Can wipe prompt configurations

## Immediate Actions Required

### 1. **Secure the Database**
```sql
-- Create read-only role for development
CREATE ROLE dev_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dev_readonly;

-- Add row-level security
ALTER TABLE ai_extraction_queue ENABLE ROW LEVEL SECURITY;

-- Create policy to prevent test data updates on production items
CREATE POLICY no_test_updates ON ai_extraction_queue
  FOR UPDATE USING (
    NOT (extraction_result::text LIKE '%test%' AND status = 'completed')
  );
```

### 2. **Implement Environment Separation**
```python
# config.py
import os

class Config:
    @staticmethod
    def get_db_url():
        env = os.getenv('ENVIRONMENT', 'development')
        if env == 'production':
            return os.getenv('SUPABASE_URL')
        else:
            return os.getenv('SUPABASE_DEV_URL')  # Separate dev database
    
    @staticmethod
    def can_modify_data():
        return os.getenv('ENVIRONMENT') != 'production'
```

### 3. **Add Data Protection Layer**
```python
# src/database/protection.py
from datetime import datetime
import json

class DataProtection:
    @staticmethod
    def backup_before_update(supabase, table, id, data):
        """Create backup before any update"""
        # Get current data
        current = supabase.table(table).select('*').eq('id', id).execute()
        
        if current.data:
            # Store backup
            backup = {
                'table_name': table,
                'record_id': id,
                'original_data': current.data[0],
                'update_data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'user': os.getenv('USER', 'unknown')
            }
            
            supabase.table('data_backups').insert(backup).execute()
            
        return True
    
    @staticmethod
    def prevent_test_data_in_production(data):
        """Check if data contains obvious test patterns"""
        test_patterns = [
            'Coca Cola', 'Pepsi', 'test', 'dummy', 'fake',
            'placeholder', 'example', 'demo'
        ]
        
        data_str = json.dumps(data).lower()
        for pattern in test_patterns:
            if pattern.lower() in data_str:
                raise ValueError(f"Test data pattern '{pattern}' detected - cannot save to production")
```

### 4. **Create Development Fixtures**
```python
# tests/fixtures.py
class TestDataFactory:
    """Use this for testing instead of modifying production data"""
    
    @staticmethod
    def create_test_extraction():
        return {
            "id": "test_" + str(uuid.uuid4()),
            "is_test_data": True,  # Always mark test data
            "extraction_result": {
                # ... test data ...
            }
        }
```

### 5. **Implement Audit Logging**
```sql
-- Create audit table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id INTEGER,
    action TEXT NOT NULL,
    old_data JSONB,
    new_data JSONB,
    user_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create trigger for queue updates
CREATE OR REPLACE FUNCTION audit_queue_changes() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, user_id)
    VALUES (
        'ai_extraction_queue',
        NEW.id,
        TG_OP,
        to_jsonb(OLD),
        to_jsonb(NEW),
        current_user
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_queue_trigger
AFTER UPDATE ON ai_extraction_queue
FOR EACH ROW EXECUTE FUNCTION audit_queue_changes();
```

## Long-term Recommendations

### 1. **Separate Environments**
- Production database with restricted access
- Staging database for integration testing  
- Local development databases
- Test data clearly marked with `is_test_data` flag

### 2. **Access Control**
- Production write access only through API
- Required approval for direct database modifications
- Service accounts with minimal required permissions
- Regular access audits

### 3. **Code Organization**
```
project/
├── src/              # Production code only
├── scripts/
│   ├── production/   # Production scripts (require approval)
│   └── development/  # Dev/debug scripts (cannot run in prod)
├── tests/            # Test code with fixtures
└── migrations/       # Controlled database changes
```

### 4. **Data Recovery Process**
- Automated backups before any updates
- Point-in-time recovery capability
- Clear rollback procedures
- Regular backup testing

### 5. **Monitoring & Alerts**
- Alert on unexpected data modifications
- Monitor for test data patterns in production
- Track API costs vs data changes
- Regular data integrity checks

## Recovery Plan for Item 9

Since the real extraction data is lost, options are:

1. **Re-extract**: Process the image again with current system
2. **Check backups**: Look for database backups from June 8
3. **Log recovery**: Reconstruct from extraction logs if available
4. **Accept loss**: Document the incident and move forward

## Conclusion

This incident highlights critical security and data integrity issues. The ability for debug scripts to overwrite production data without any safeguards is unacceptable. Immediate implementation of the security measures above is essential to prevent future data loss.

**Priority**: CRITICAL  
**Estimated data loss**: $0.12 API cost + 45 minutes processing + invaluable production data  
**Risk of recurrence**: HIGH without immediate action