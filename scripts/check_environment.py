#!/usr/bin/env python3
"""
Environment Setup Checker
Verifies that environment separation is properly configured
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.environment_config.environment import get_environment_config
    from src.database.protection_v2 import DataProtection
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure you're in the project root directory")
    sys.exit(1)

def check_environment():
    """Check environment configuration"""
    print("=== Environment Configuration Check ===\n")
    
    # Get config
    try:
        config = get_environment_config()
        print(f"✅ Environment detected: {config.environment}")
        print(f"✅ Is Production: {config.is_production}")
        print(f"✅ Can Modify Data: {config.can_modify_data}")
        print(f"✅ Database URL: {config.database_url.split('@')[0] if '@' in config.database_url else 'Configured'}")
        
        # Check protected records
        protected = config.get_protected_records('ai_extraction_queue')
        print(f"✅ Protected queue items: {protected}")
        
        # Check test patterns
        patterns = config.get_test_patterns()
        print(f"✅ Test patterns configured: {len(patterns)} patterns")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Check .env file
    print("\n=== Environment File Check ===")
    env_file = Path('.env')
    
    if env_file.exists():
        print("✅ .env file exists")
        
        # Check critical variables
        required_vars = ['ENVIRONMENT', 'SUPABASE_URL', 'SUPABASE_SERVICE_KEY']
        missing = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            print(f"❌ Missing required variables: {missing}")
        else:
            print("✅ All required variables set")
    else:
        print("❌ No .env file found")
        print("Run: cp .env.development.template .env")
        return False
    
    # Test data protection
    print("\n=== Data Protection Check ===")
    
    try:
        # This should work in development
        protection = DataProtection()
        print("✅ Data protection initialized")
        
        # Test validation
        test_data = {"name": "Test Product", "brand": "TestCo"}
        try:
            protection.validate_data(test_data, "test_table")
            print("✅ Test data validation passed")
        except Exception as e:
            print(f"⚠️  Test data validation warning: {e}")
            
    except Exception as e:
        print(f"❌ Data protection error: {e}")
        return False
    
    print("\n=== Safety Recommendations ===")
    
    if config.is_production:
        print("🚨 PRODUCTION ENVIRONMENT DETECTED 🚨")
        print("- Data modifications are restricted")
        print("- Be extremely careful with any operations")
        print("- Consider switching to development for testing")
    elif config.is_development:
        print("✅ Development environment - safe for testing")
        print("- Remember to use test fixtures for test data")
        print("- Don't use real production IDs in tests")
    else:
        print(f"ℹ️  {config.environment} environment")
    
    return True

if __name__ == "__main__":
    success = check_environment()
    sys.exit(0 if success else 1)
