#!/usr/bin/env python3
"""
Set up environment separation for the project
"""
import os
import shutil
from pathlib import Path

def setup_environment_files():
    """Set up environment configuration files"""
    print("=== Setting Up Environment Separation ===\n")
    
    # Check current .env file
    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  Found existing .env file")
        
        # Create backup
        backup_name = '.env.backup_before_separation'
        shutil.copy('.env', backup_name)
        print(f"✅ Created backup: {backup_name}")
        
        # Check if ENVIRONMENT is set
        with open('.env', 'r') as f:
            content = f.read()
            
        has_environment = 'ENVIRONMENT=' in content
        
        if not has_environment:
            print("\n❌ WARNING: No ENVIRONMENT variable found in .env")
            print("Adding ENVIRONMENT=development to .env")
            
            with open('.env', 'a') as f:
                f.write('\n# Environment Configuration (CRITICAL)\n')
                f.write('ENVIRONMENT=development\n')
    else:
        print("❌ No .env file found")
        print("Creating .env from development template...")
        
        # Copy development template
        if Path('.env.development.template').exists():
            shutil.copy('.env.development.template', '.env')
            print("✅ Created .env from development template")
            print("⚠️  Please update the values in .env with your actual credentials")
        else:
            print("❌ No development template found")
    
    print("\n=== Environment Templates ===")
    print("✅ Created .env.development.template")
    print("✅ Created .env.production.template")
    print("✅ Created environment configuration in src/config/")

def create_gitignore_updates():
    """Update .gitignore for environment files"""
    gitignore_additions = """
# Environment files (never commit these!)
.env
.env.local
.env.production
.env.staging
.env.development

# But allow templates
!.env.*.template

# Backup files
*.backup
.env.backup*

# Data protection
backups/
QUARANTINE_dangerous_scripts/

# Audit logs
audit_logs/
*.audit.json
"""
    
    gitignore_path = Path('.gitignore')
    
    if gitignore_path.exists():
        with open('.gitignore', 'r') as f:
            current = f.read()
        
        # Check if already has env protection
        if '.env.production' not in current:
            print("\n=== Updating .gitignore ===")
            with open('.gitignore', 'a') as f:
                f.write('\n# Data Protection and Environment Separation\n')
                f.write(gitignore_additions)
            print("✅ Updated .gitignore with environment protections")
    else:
        print("\n=== Creating .gitignore ===")
        with open('.gitignore', 'w') as f:
            f.write(gitignore_additions)
        print("✅ Created .gitignore with environment protections")

def create_environment_checker():
    """Create a script to verify environment setup"""
    checker_content = '''#!/usr/bin/env python3
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
    from src.config.environment import get_environment_config
    from src.database.protection_v2 import DataProtection
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    print("Please ensure you're in the project root directory")
    sys.exit(1)

def check_environment():
    """Check environment configuration"""
    print("=== Environment Configuration Check ===\\n")
    
    # Get config
    try:
        config = get_environment_config()
        print(f"✅ Environment detected: {config.environment}")
        print(f"✅ Is Production: {config.is_production}")
        print(f"✅ Can Modify Data: {config.can_modify_data()}")
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
    print("\\n=== Environment File Check ===")
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
    print("\\n=== Data Protection Check ===")
    
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
    
    print("\\n=== Safety Recommendations ===")
    
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
'''
    
    # Create checker script
    checker_path = Path('scripts/check_environment.py')
    checker_path.write_text(checker_content)
    os.chmod(checker_path, 0o755)
    print("\n✅ Created scripts/check_environment.py")

def create_example_safe_script():
    """Create an example of a safe database script"""
    example_content = '''#!/usr/bin/env python3
"""
Example: Safe Database Operations
Shows how to properly interact with the database using protection
"""
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from src.config.environment import get_environment_config, require_production_check
from src.database.protection_v2 import DataProtection, DataProtectionError
from tests.fixtures.test_data import TestDataFactory

# Get environment configuration
env_config = get_environment_config()
print(f"Running in {env_config.environment} environment")

# Initialize Supabase with environment-aware settings
supabase = create_client(env_config.database_url, env_config.database_key)

@require_production_check
def example_safe_update():
    """Example of safely updating a record"""
    print("\\n=== Safe Update Example ===")
    
    # Never hardcode IDs - get them from queries or parameters
    # For this example, we'll find a test record
    result = supabase.table('ai_extraction_queue').select('id').eq('is_test_data', True).limit(1).execute()
    
    if not result.data:
        print("No test records found to update")
        return
    
    record_id = result.data[0]['id']
    
    try:
        # Safe update with protection
        update_data = {
            'status': 'processing',
            'updated_by': 'safe_example_script'
        }
        
        result = DataProtection.safe_update(
            supabase,
            'ai_extraction_queue',
            record_id,
            update_data
        )
        
        print(f"✅ Safely updated record {record_id}")
        
    except DataProtectionError as e:
        print(f"❌ Update blocked by protection: {e}")
    except Exception as e:
        print(f"❌ Update failed: {e}")

def example_safe_insert():
    """Example of safely inserting test data"""
    print("\\n=== Safe Insert Example ===")
    
    if env_config.is_production:
        print("❌ Cannot insert test data in production")
        return
    
    # Use test fixtures
    test_data = TestDataFactory.create_test_extraction(
        store_name="Safe Test Store",
        products_count=3
    )
    
    # Extract just the data we need
    insert_data = {
        'upload_id': test_data['upload_id'],
        'status': 'pending',
        'is_test_data': True,
        'test_reason': 'safe_example_script'
    }
    
    try:
        result = DataProtection.safe_insert(
            supabase,
            'ai_extraction_queue',
            insert_data
        )
        
        if result.data:
            print(f"✅ Safely inserted test record: {result.data[0]['id']}")
            # Track for cleanup
            return result.data[0]['id']
            
    except DataProtectionError as e:
        print(f"❌ Insert blocked by protection: {e}")
    except Exception as e:
        print(f"❌ Insert failed: {e}")
    
    return None

def example_safe_read():
    """Reading is always safe"""
    print("\\n=== Safe Read Example ===")
    
    # Reading doesn't need protection
    result = supabase.table('ai_extraction_queue').select(
        'id, status, store_name, created_at'
    ).limit(5).order('created_at', desc=True).execute()
    
    if result.data:
        print(f"✅ Found {len(result.data)} recent records:")
        for item in result.data:
            print(f"   - {item['id']}: {item.get('store_name', 'Unknown')} ({item['status']})")
    else:
        print("No records found")

def cleanup_test_data(record_id):
    """Clean up test data after example"""
    if record_id and env_config.is_development:
        try:
            # In development, we can delete test data
            result = supabase.table('ai_extraction_queue').delete().eq('id', record_id).eq('is_test_data', True).execute()
            print(f"\\n✅ Cleaned up test record {record_id}")
        except:
            pass

if __name__ == "__main__":
    # Always show current environment
    env_config.log_configuration()
    
    # Safe read works in any environment
    example_safe_read()
    
    # These only work in non-production
    if not env_config.is_production:
        example_safe_update()
        test_id = example_safe_insert()
        
        # Clean up
        if test_id:
            cleanup_test_data(test_id)
    else:
        print("\\n⚠️  Skipping write operations in production environment")
'''
    
    example_path = Path('scripts/example_safe_database_update.py')
    example_path.write_text(example_content)
    os.chmod(example_path, 0o755)
    print("✅ Created scripts/example_safe_database_update.py")

def main():
    """Set up environment separation"""
    
    # Set up environment files
    setup_environment_files()
    
    # Update .gitignore
    create_gitignore_updates()
    
    # Create helper scripts
    create_environment_checker()
    create_example_safe_script()
    
    print("\n=== Environment Separation Setup Complete ===")
    print("\nNext steps:")
    print("1. Check your environment: python scripts/check_environment.py")
    print("2. Review and update .env with your actual credentials")
    print("3. NEVER commit .env files to git")
    print("4. Use different databases for dev/staging/production")
    print("5. Run migrations: python scripts/migrate_to_data_protection.py")
    print("\nFor examples, see: scripts/example_safe_database_update.py")

if __name__ == "__main__":
    main()