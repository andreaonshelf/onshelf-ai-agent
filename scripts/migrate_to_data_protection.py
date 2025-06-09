#!/usr/bin/env python3
"""
Migrate existing scripts to use data protection
"""
import os
import re
from pathlib import Path
from typing import List, Tuple

def find_scripts_needing_protection() -> List[Tuple[str, List[str]]]:
    """Find all scripts that need data protection"""
    scripts_to_update = []
    
    # Patterns that indicate database operations
    dangerous_patterns = [
        (r'supabase\.table\(.*\)\.update\(', 'Direct update without protection'),
        (r'supabase\.table\(.*\)\.delete\(', 'Direct delete without protection'),
        (r'supabase\.table\(.*\)\.insert\(', 'Direct insert without validation'),
        (r'\.eq\(["\']id["\']\s*,\s*\d+\)', 'Hardcoded ID reference'),
        (r'test.*data.*=.*\{', 'Test data definition'),
        (r'fake.*data.*=.*\{', 'Fake data definition'),
    ]
    
    # Skip these directories
    skip_dirs = {'QUARANTINE_dangerous_scripts', '.git', '__pycache__', 'node_modules', '.venv'}
    
    for root, dirs, files in os.walk('.'):
        # Remove skip directories from search
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                # Skip this script and already protected files
                if file == 'migrate_to_data_protection.py' or 'protection' in file:
                    continue
                
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    found_issues = []
                    for pattern, description in dangerous_patterns:
                        if re.search(pattern, content):
                            found_issues.append(description)
                    
                    if found_issues:
                        scripts_to_update.append((filepath, found_issues))
                        
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
    
    return scripts_to_update

def generate_migration_report(scripts: List[Tuple[str, List[str]]]) -> str:
    """Generate a report of scripts needing updates"""
    report = ["# Data Protection Migration Report\n"]
    report.append(f"Found {len(scripts)} scripts needing protection updates\n")
    
    # Group by directory
    by_directory = {}
    for filepath, issues in scripts:
        directory = os.path.dirname(filepath) or '.'
        if directory not in by_directory:
            by_directory[directory] = []
        by_directory[directory].append((filepath, issues))
    
    # Generate report by directory
    for directory, files in sorted(by_directory.items()):
        report.append(f"\n## {directory}/")
        report.append(f"{len(files)} files need updates\n")
        
        for filepath, issues in files:
            filename = os.path.basename(filepath)
            report.append(f"### {filename}")
            for issue in issues:
                report.append(f"- {issue}")
            report.append("")
    
    # Add migration instructions
    report.append("\n## Migration Instructions\n")
    report.append("1. **For Update Operations:**")
    report.append("   ```python")
    report.append("   # Before:")
    report.append("   supabase.table('queue').update(data).eq('id', 9).execute()")
    report.append("   ")
    report.append("   # After:")
    report.append("   from src.database.protection_v2 import DataProtection")
    report.append("   DataProtection.safe_update(supabase, 'queue', 9, data)")
    report.append("   ```\n")
    
    report.append("2. **For Insert Operations:**")
    report.append("   ```python")
    report.append("   # Before:")
    report.append("   supabase.table('queue').insert(data).execute()")
    report.append("   ")
    report.append("   # After:")
    report.append("   from src.database.protection_v2 import DataProtection")
    report.append("   DataProtection.safe_insert(supabase, 'queue', data)")
    report.append("   ```\n")
    
    report.append("3. **For Test Data:**")
    report.append("   ```python")
    report.append("   # Before:")
    report.append("   test_data = {'name': 'Coca Cola', ...}")
    report.append("   ")
    report.append("   # After:")
    report.append("   from tests.fixtures.test_data import TestDataFactory")
    report.append("   test_data = TestDataFactory.create_test_extraction()")
    report.append("   ```\n")
    
    report.append("4. **Add Environment Check:**")
    report.append("   ```python")
    report.append("   from src.config.environment import require_production_check")
    report.append("   ")
    report.append("   @require_production_check")
    report.append("   def dangerous_function():")
    report.append("       # This won't run in production")
    report.append("   ```")
    
    return '\n'.join(report)

def create_example_migration(original_file: str) -> str:
    """Create an example of how to migrate a file"""
    example = f"""#!/usr/bin/env python3
'''
Example migration for: {original_file}
This shows how to update the script to use data protection
'''

import os
from supabase import create_client

# NEW: Import data protection
from src.database.protection_v2 import DataProtection, protected_database_operation
from src.config.environment import get_environment_config, require_production_check
from tests.fixtures.test_data import TestDataFactory

# Get environment config
env_config = get_environment_config()

# Initialize Supabase with environment awareness
url = env_config.database_url
key = env_config.database_key
supabase = create_client(url, key)

@require_production_check  # This decorator prevents running in production
def update_queue_item_safely():
    '''Example of safe update'''
    
    # OLD WAY (DANGEROUS):
    # supabase.table('ai_extraction_queue').update({{'status': 'completed'}}).eq('id', 9).execute()
    
    # NEW WAY (SAFE):
    try:
        # This will create backup, validate data, and create audit log
        result = DataProtection.safe_update(
            supabase,
            'ai_extraction_queue',
            9,
            {{'status': 'completed'}}
        )
        print(f"Safely updated record")
    except DataProtectionError as e:
        print(f"Update blocked: {{e}}")

@protected_database_operation  # Alternative decorator
def insert_test_data_safely():
    '''Example of safe test data insertion'''
    
    # OLD WAY (DANGEROUS):
    # test_data = {{'name': 'Coca Cola', 'price': 2.99}}
    # supabase.table('products').insert(test_data).execute()
    
    # NEW WAY (SAFE):
    # Use test fixtures instead
    test_extraction = TestDataFactory.create_test_extraction()
    
    # If you must insert to database, use safe_insert
    if env_config.is_development:
        DataProtection.safe_insert(
            supabase,
            'test_extractions',  # Use test table
            test_extraction
        )

def read_only_operation():
    '''Reading data is always safe'''
    # No protection needed for SELECT queries
    result = supabase.table('ai_extraction_queue').select('*').eq('status', 'completed').execute()
    return result.data

if __name__ == '__main__':
    # Log current environment
    print(f"Environment: {{env_config.environment}}")
    print(f"Can modify data: {{env_config.can_modify_data()}}")
    
    # Only run dangerous operations in development
    if env_config.is_development:
        update_queue_item_safely()
        insert_test_data_safely()
    else:
        print("Dangerous operations skipped in this environment")
    
    # Safe operations can run anywhere
    data = read_only_operation()
    print(f"Found {{len(data)}} completed items")
"""
    return example

def main():
    print("=== Data Protection Migration Tool ===\n")
    
    # Find scripts needing updates
    scripts = find_scripts_needing_protection()
    
    if not scripts:
        print("✅ No scripts found that need protection updates!")
        return
    
    print(f"Found {len(scripts)} scripts that need data protection updates\n")
    
    # Generate report
    report = generate_migration_report(scripts)
    
    # Save report
    with open('DATA_PROTECTION_MIGRATION_REPORT.md', 'w') as f:
        f.write(report)
    
    print("📄 Migration report saved to: DATA_PROTECTION_MIGRATION_REPORT.md")
    
    # Create example migration
    if scripts:
        example_file = scripts[0][0]
        example = create_example_migration(example_file)
        
        with open('EXAMPLE_MIGRATION.py', 'w') as f:
            f.write(example)
        
        print("📄 Example migration saved to: EXAMPLE_MIGRATION.py")
    
    # Show summary
    print("\n=== Summary ===")
    print(f"Total scripts to update: {len(scripts)}")
    print("\nTop issues found:")
    
    issue_counts = {}
    for _, issues in scripts:
        for issue in issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
    
    for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {issue}: {count} occurrences")
    
    print("\nNext steps:")
    print("1. Review DATA_PROTECTION_MIGRATION_REPORT.md")
    print("2. Update scripts following EXAMPLE_MIGRATION.py")
    print("3. Test thoroughly in development before production")

if __name__ == "__main__":
    main()