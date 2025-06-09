"""
Data Protection Layer V2
Enhanced protection with environment-aware configuration
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

# Handle imports based on what's available
try:
    from ..environment_config.environment import get_environment_config
    env_config = get_environment_config()
except ImportError:
    # Fallback for standalone usage
    class MockEnvConfig:
        def __init__(self):
            self.environment = os.getenv('ENVIRONMENT', 'development')
            self.is_production = self.environment == 'production'
            self.is_development = self.environment == 'development'
            
        def can_modify_data(self):
            return self.environment != 'production'
            
        def get_protected_records(self, table):
            if table == 'ai_extraction_queue':
                return [9]
            return []
            
        def get_test_patterns(self):
            return [
                'coca cola', 'pepsi', 'sprite', 'mountain dew',
                'test product', 'dummy', 'fake', 'placeholder',
                'example', 'demo', 'mock'
            ]
    
    env_config = MockEnvConfig()

logger = logging.getLogger(__name__)

class DataProtectionError(Exception):
    """Raised when data protection rules are violated"""
    pass

class DataProtection:
    """Enhanced data protection with environment awareness"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.env_config = env_config
        
    def check_environment(self) -> None:
        """Ensure operations are allowed in current environment"""
        if self.env_config.is_production and not self.env_config.can_modify_data():
            raise DataProtectionError(
                "Data modification is not allowed in production environment. "
                "Use a development or staging environment for testing."
            )
    
    def validate_data(self, data: Dict[str, Any], table_name: str) -> None:
        """Validate data before insertion/update"""
        # Get test patterns from config
        test_patterns = self.env_config.get_test_patterns()
        
        # Check for test patterns
        data_str = json.dumps(data).lower()
        for pattern in test_patterns:
            if pattern.lower() in data_str:
                # In production, always block
                if self.env_config.is_production:
                    raise DataProtectionError(
                        f"Test data pattern '{pattern}' detected in production. "
                        f"Cannot save test data to {table_name}."
                    )
                # In other environments, warn
                else:
                    logger.warning(
                        f"Test data pattern '{pattern}' detected in {table_name}. "
                        "Consider using proper test fixtures."
                    )
        
        # Additional validation for extraction results
        if table_name == 'ai_extraction_queue' and 'extraction_result' in data:
            self._validate_extraction_result(data['extraction_result'])
    
    def _validate_extraction_result(self, result: Any) -> None:
        """Validate extraction result data"""
        if not isinstance(result, dict):
            return
            
        # Check for suspicious patterns
        result_str = json.dumps(result).lower()
        
        # Check for exactly these test products
        test_products = [
            'coca cola classic',
            'pepsi regular',
            'sprite lemon-lime',
            'mountain dew'
        ]
        
        matches = sum(1 for product in test_products if product in result_str)
        if matches >= 3:  # If 3+ test products found, it's likely test data
            if self.env_config.is_production:
                raise DataProtectionError(
                    "Extraction result appears to contain test data. "
                    "Multiple known test products detected."
                )
            else:
                logger.warning("Extraction result may contain test data")
    
    def protect_update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Protect database updates"""
        # Check if this is a protected record
        protected_ids = self.env_config.get_protected_records(table)
        if record_id in protected_ids:
            logger.warning(
                f"Attempting to update protected record: {table}:{record_id}"
            )
            
            # In production, block the update
            if self.env_config.is_production:
                raise DataProtectionError(
                    f"Record {table}:{record_id} is protected. "
                    "This record contains valuable production data. "
                    "Contact admin if update is necessary."
                )
            
            # In development, require confirmation
            if self.env_config.is_development:
                if not self._confirm_protected_update(table, record_id):
                    raise DataProtectionError("Update cancelled by user")
        
        # Validate the data
        self.validate_data(data, table)
        
        # Create audit entry
        audit_entry = self._create_audit_entry(table, record_id, 'update', data)
        
        return audit_entry
    
    def _confirm_protected_update(self, table: str, record_id: Any) -> bool:
        """Ask for confirmation before updating protected records"""
        print(f"\n⚠️  WARNING: Attempting to update protected record")
        print(f"Table: {table}")
        print(f"Record ID: {record_id}")
        print(f"This record is protected because it contains valuable data")
        
        # In CI/automated environments, deny
        if os.getenv('CI') or os.getenv('AUTOMATED'):
            return False
            
        response = input("Type 'YES' to proceed: ")
        return response == 'YES'
    
    def _create_audit_entry(self, table: str, record_id: Any, 
                           action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create audit log entry"""
        audit_entry = {
            'table_name': table,
            'record_id': record_id,
            'action': action,
            'data_hash': hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.env_config.environment,
            'user': os.getenv('USER', 'unknown'),
            'protected_record': record_id in self.env_config.get_protected_records(table)
        }
        
        logger.info(f"Audit: {action} on {table}:{record_id}", extra=audit_entry)
        
        # In production, also save to audit table
        if self.env_config.is_production and self.supabase:
            try:
                self.supabase.table('audit_log').insert(audit_entry).execute()
            except Exception as e:
                logger.error(f"Failed to save audit log: {e}")
        
        return audit_entry
    
    def create_backup(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        """Create backup before modification"""
        if not self.supabase:
            logger.warning("No supabase client available for backup")
            return None
            
        try:
            # Get current data
            result = self.supabase.table(table).select('*').eq('id', record_id).execute()
            
            if result.data:
                backup = {
                    'table_name': table,
                    'record_id': record_id,
                    'data': result.data[0],
                    'backup_time': datetime.utcnow().isoformat(),
                    'environment': self.env_config.environment,
                    'backup_reason': 'pre_update_backup'
                }
                
                # Save backup
                if self.env_config.is_production or getattr(self.env_config, 'backup_before_update', True):
                    try:
                        self.supabase.table('data_backups').insert(backup).execute()
                        logger.info(f"Created backup for {table}:{record_id}")
                    except:
                        # If backup table doesn't exist, save to file
                        backup_dir = Path('backups')
                        backup_dir.mkdir(exist_ok=True)
                        backup_file = backup_dir / f"{table}_{record_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        with open(backup_file, 'w') as f:
                            json.dump(backup, f, indent=2)
                        logger.info(f"Created file backup: {backup_file}")
                
                return backup
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            
        return None
    
    @classmethod
    def safe_update(cls, supabase_client, table: str, record_id: Any, 
                   data: Dict[str, Any], force: bool = False) -> Any:
        """Perform a safe update with protection checks"""
        protection = cls(supabase_client)
        
        # Skip protection if forced (only in non-production)
        if force and not protection.env_config.is_production:
            logger.warning(f"Forcing update to {table}:{record_id} (protection bypassed)")
            return supabase_client.table(table).update(data).eq('id', record_id).execute()
        
        # Check environment
        protection.check_environment()
        
        # Create backup
        backup = protection.create_backup(table, record_id)
        
        # Validate and protect
        audit = protection.protect_update(table, record_id, data)
        
        # Perform update
        try:
            result = supabase_client.table(table).update(data).eq('id', record_id).execute()
            logger.info(f"Successfully updated {table}:{record_id}")
            
            # Log success to audit
            protection._create_audit_entry(table, record_id, 'update_success', {
                'rows_affected': len(result.data) if result.data else 0
            })
            
            return result
        except Exception as e:
            logger.error(f"Update failed: {e}")
            
            # Log failure to audit
            protection._create_audit_entry(table, record_id, 'update_failed', {
                'error': str(e)
            })
            
            if backup:
                logger.info(f"Backup available from: {backup['backup_time']}")
            raise
    
    @classmethod
    def safe_insert(cls, supabase_client, table: str, data: Dict[str, Any]) -> Any:
        """Perform a safe insert with protection checks"""
        protection = cls(supabase_client)
        
        # Check environment
        protection.check_environment()
        
        # Validate data
        protection.validate_data(data, table)
        
        # Create audit entry
        audit = protection._create_audit_entry(table, 'new', 'insert', data)
        
        # Perform insert
        try:
            result = supabase_client.table(table).insert(data).execute()
            logger.info(f"Successfully inserted into {table}")
            
            # Log success
            if result.data and len(result.data) > 0:
                new_id = result.data[0].get('id', 'unknown')
                protection._create_audit_entry(table, new_id, 'insert_success', {
                    'record_created': True
                })
            
            return result
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            protection._create_audit_entry(table, 'failed', 'insert_failed', {
                'error': str(e)
            })
            raise
    
    @staticmethod
    def require_confirmation(operation: str, details: str) -> bool:
        """Require user confirmation for dangerous operations"""
        print(f"\n⚠️  WARNING: {operation}")
        print(f"Details: {details}")
        
        # In automated environments, deny by default
        if os.getenv('CI') or os.getenv('AUTOMATED'):
            print("Automated environment detected - operation denied")
            return False
            
        response = input("Type 'YES' to proceed: ")
        return response == 'YES'

# Enhanced decorators
def protected_database_operation(func):
    """Decorator to protect database operations"""
    def wrapper(*args, **kwargs):
        # Check environment
        if env_config.is_production:
            raise DataProtectionError(
                f"Function {func.__name__} cannot run in production. "
                "This is a protective measure to prevent data loss."
            )
        
        # Log the operation
        logger.info(f"Executing protected operation: {func.__name__}")
        
        # Add warning for development
        if env_config.is_development:
            logger.warning(
                f"Running {func.__name__} in development mode. "
                "Ensure you're using development database."
            )
        
        return func(*args, **kwargs)
    
    return wrapper

def require_backup(func):
    """Decorator to ensure backup before operation"""
    def wrapper(self, *args, **kwargs):
        # If method has table and record_id arguments
        if hasattr(self, 'create_backup') and len(args) >= 2:
            table, record_id = args[0], args[1]
            backup = self.create_backup(table, record_id)
            if backup:
                logger.info(f"Backup created before {func.__name__}")
        
        return func(self, *args, **kwargs)
    
    return wrapper