"""
Data Protection Layer
Prevents accidental modification of production data
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
from ..config import get_config, require_non_production

logger = logging.getLogger(__name__)

class DataProtectionError(Exception):
    """Raised when data protection rules are violated"""
    pass

class DataProtection:
    """Protects production data from accidental modification"""
    
    # Test data patterns that should never appear in production
    TEST_PATTERNS = [
        'coca cola', 'pepsi', 'sprite', 'mountain dew',  # Known test products
        'test product', 'dummy', 'fake', 'placeholder',
        'example', 'demo', 'mock'
    ]
    
    # Protected production IDs (add more as needed)
    PROTECTED_IDS = {
        'ai_extraction_queue': [9],  # Co-op extraction that was overwritten
    }
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.config = get_config()
        self.environment = self.config.environment.value
        self.is_production = self.config.is_production
        
    def check_environment(self) -> None:
        """Ensure we're not in production for dangerous operations"""
        try:
            require_non_production("Database modification")
        except EnvironmentError as e:
            raise DataProtectionError(str(e))
    
    def validate_data(self, data: Dict[str, Any], table_name: str) -> None:
        """Validate data before insertion/update"""
        # Check for test patterns
        data_str = json.dumps(data).lower()
        for pattern in self.TEST_PATTERNS:
            if pattern in data_str:
                raise DataProtectionError(
                    f"Test data pattern '{pattern}' detected. "
                    f"Cannot save test data to {table_name}. "
                    "Use proper test fixtures instead."
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
            raise DataProtectionError(
                "Extraction result appears to contain test data. "
                "Multiple known test products detected."
            )
    
    def protect_update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Protect database updates"""
        # Check if this is a protected record
        if table in self.PROTECTED_IDS and record_id in self.PROTECTED_IDS[table]:
            logger.warning(
                f"Attempting to update protected record: {table}:{record_id}"
            )
            
            # In production, block the update
            if self.is_production:
                raise DataProtectionError(
                    f"Record {table}:{record_id} is protected. "
                    "This record contains valuable production data. "
                    "Contact admin if update is necessary."
                )
        
        # Validate the data
        self.validate_data(data, table)
        
        # Create audit entry
        audit_entry = {
            'table_name': table,
            'record_id': record_id,
            'action': 'update',
            'data_hash': hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest(),
            'timestamp': datetime.utcnow().isoformat(),
            'environment': self.environment,
            'user': os.getenv('USER', 'unknown')
        }
        
        logger.info(f"Data update audit: {audit_entry}")
        
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
                    'environment': self.environment
                }
                
                # Store backup (in production, this would go to a backup table)
                logger.info(f"Created backup for {table}:{record_id}")
                return backup
                
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            
        return None
    
    @staticmethod
    def safe_update(supabase_client, table: str, record_id: Any, 
                   data: Dict[str, Any], force: bool = False) -> Any:
        """Perform a safe update with protection checks"""
        protection = DataProtection(supabase_client)
        
        # Skip protection in test environment or if forced
        if force and protection.environment != 'production':
            logger.warning(f"Forcing update to {table}:{record_id} (protection bypassed)")
            return supabase_client.table(table).update(data).eq('id', record_id).execute()
        
        # Create backup
        backup = protection.create_backup(table, record_id)
        
        # Validate and protect
        audit = protection.protect_update(table, record_id, data)
        
        # Perform update
        try:
            result = supabase_client.table(table).update(data).eq('id', record_id).execute()
            logger.info(f"Successfully updated {table}:{record_id}")
            return result
        except Exception as e:
            logger.error(f"Update failed: {e}")
            if backup:
                logger.info(f"Backup available: {backup['backup_time']}")
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

# Example usage wrapper for scripts
def protected_database_operation(func):
    """Decorator to protect database operations"""
    def wrapper(*args, **kwargs):
        protection = DataProtection()
        
        # Check environment
        if protection.is_production:
            raise DataProtectionError(
                f"Function {func.__name__} cannot run in production. "
                "This is a protective measure to prevent data loss."
            )
        
        # Log the operation
        logger.info(f"Executing protected operation: {func.__name__}")
        
        return func(*args, **kwargs)
    
    return wrapper