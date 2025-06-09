"""
Environment Configuration and Protection
Ensures proper separation between development, staging, and production
"""
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EnvironmentConfig:
    """Manages environment-specific configuration and protection"""
    
    # Valid environments
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    PRODUCTION = 'production'
    TEST = 'test'
    
    VALID_ENVIRONMENTS = [DEVELOPMENT, STAGING, PRODUCTION, TEST]
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.config = self._load_config()
        self._validate_environment()
        
    def _detect_environment(self) -> str:
        """Detect current environment from various sources"""
        # 1. Check explicit ENVIRONMENT variable
        env = os.getenv('ENVIRONMENT', '').lower()
        if env in self.VALID_ENVIRONMENTS:
            return env
            
        # 2. Check for production indicators
        if any([
            os.getenv('PRODUCTION') == 'true',
            os.getenv('NODE_ENV') == 'production',
            os.getenv('VERCEL_ENV') == 'production',
            os.getenv('RAILWAY_ENVIRONMENT') == 'production'
        ]):
            return self.PRODUCTION
            
        # 3. Check for CI/CD environment
        if any([
            os.getenv('CI') == 'true',
            os.getenv('GITHUB_ACTIONS') == 'true',
            os.getenv('GITLAB_CI') == 'true'
        ]):
            return self.TEST
            
        # 4. Default to development
        logger.warning("No environment specified, defaulting to development")
        return self.DEVELOPMENT
    
    def _load_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration"""
        config_dir = Path(__file__).parent
        config_file = config_dir / f'env.{self.environment}.json'
        
        # Load base config
        base_config = {}
        base_file = config_dir / 'env.base.json'
        if base_file.exists():
            with open(base_file) as f:
                base_config = json.load(f)
        
        # Load environment-specific config
        env_config = {}
        if config_file.exists():
            with open(config_file) as f:
                env_config = json.load(f)
        else:
            logger.warning(f"No config file found for {self.environment}: {config_file}")
        
        # Merge configs (env overrides base)
        return {**base_config, **env_config}
    
    def _validate_environment(self):
        """Validate environment setup"""
        if self.environment == self.PRODUCTION:
            # Production checks
            required_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
            missing = [var for var in required_vars if not os.getenv(var)]
            if missing:
                raise EnvironmentError(
                    f"Production environment missing required variables: {missing}"
                )
                
            # Ensure we're using production database
            db_url = os.getenv('SUPABASE_URL', '')
            if 'localhost' in db_url or '127.0.0.1' in db_url:
                raise EnvironmentError(
                    "Production environment cannot use localhost database!"
                )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == self.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == self.DEVELOPMENT
    
    @property
    def is_test(self) -> bool:
        """Check if running in test environment"""
        return self.environment == self.TEST
    
    @property
    def can_modify_data(self) -> bool:
        """Check if data modification is allowed"""
        return self.config.get('allow_data_modification', False)
    
    @property
    def require_confirmation(self) -> bool:
        """Check if dangerous operations require confirmation"""
        return self.config.get('require_confirmation', True)
    
    @property
    def database_url(self) -> str:
        """Get appropriate database URL for environment"""
        if self.environment == self.PRODUCTION:
            return os.getenv('SUPABASE_URL', '')
        elif self.environment == self.STAGING:
            return os.getenv('SUPABASE_STAGING_URL', os.getenv('SUPABASE_URL', ''))
        elif self.environment == self.TEST:
            return os.getenv('SUPABASE_TEST_URL', 'mock://test')
        else:  # development
            return os.getenv('SUPABASE_DEV_URL', os.getenv('SUPABASE_URL', ''))
    
    @property
    def database_key(self) -> str:
        """Get appropriate database key for environment"""
        if self.environment == self.PRODUCTION:
            return os.getenv('SUPABASE_SERVICE_KEY', '')
        elif self.environment == self.STAGING:
            return os.getenv('SUPABASE_STAGING_KEY', os.getenv('SUPABASE_SERVICE_KEY', ''))
        elif self.environment == self.TEST:
            return 'test-key'
        else:  # development
            return os.getenv('SUPABASE_DEV_KEY', os.getenv('SUPABASE_SERVICE_KEY', ''))
    
    def get_protected_records(self, table: str) -> list:
        """Get list of protected record IDs for a table"""
        protected = self.config.get('protected_records', {})
        return protected.get(table, [])
    
    def is_protected_record(self, table: str, record_id: Any) -> bool:
        """Check if a specific record is protected"""
        return record_id in self.get_protected_records(table)
    
    def get_test_patterns(self) -> list:
        """Get patterns that indicate test data"""
        return self.config.get('test_data_patterns', [])
    
    def log_configuration(self):
        """Log current configuration (safely)"""
        safe_config = {
            'environment': self.environment,
            'is_production': self.is_production,
            'can_modify_data': self.can_modify_data,
            'require_confirmation': self.require_confirmation,
            'protected_tables': list(self.config.get('protected_records', {}).keys()),
            'database_url': self.database_url.split('@')[0] if '@' in self.database_url else 'configured'
        }
        logger.info(f"Environment configuration: {json.dumps(safe_config, indent=2)}")
        return safe_config

# Global instance
_env_config = None

def get_environment_config() -> EnvironmentConfig:
    """Get or create environment configuration singleton"""
    global _env_config
    if _env_config is None:
        _env_config = EnvironmentConfig()
    return _env_config

# Convenience functions
def is_production() -> bool:
    """Quick check if in production"""
    return get_environment_config().is_production

def is_development() -> bool:
    """Quick check if in development"""
    return get_environment_config().is_development

def can_modify_data() -> bool:
    """Quick check if data modification is allowed"""
    return get_environment_config().can_modify_data

def require_production_check(func):
    """Decorator to prevent function execution in production"""
    def wrapper(*args, **kwargs):
        if is_production():
            raise EnvironmentError(
                f"Function {func.__name__} cannot be executed in production environment. "
                "Set ENVIRONMENT=development to proceed."
            )
        return func(*args, **kwargs)
    return wrapper

def require_environment_check(allowed_environments: list):
    """Decorator to restrict function to specific environments"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_env = get_environment_config().environment
            if current_env not in allowed_environments:
                raise EnvironmentError(
                    f"Function {func.__name__} can only run in {allowed_environments}. "
                    f"Current environment: {current_env}"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator