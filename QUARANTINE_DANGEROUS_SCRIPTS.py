#!/usr/bin/env python3
"""
Identify and quarantine dangerous scripts that can modify production data
"""
import os
import shutil
from datetime import datetime
import re

# Dangerous patterns to look for
DANGEROUS_PATTERNS = [
    r'\.update\s*\(',  # Direct database updates
    r'\.delete\s*\(',  # Direct database deletes
    r'\.insert\s*\(',  # Direct inserts (could be test data)
    r'HARD_RESET',     # Hard reset operations
    r'clear_all',      # Clear all operations
    r'fake_data',      # Fake data operations
    r'test_extraction.*\.py$',  # Test extraction scripts
    r'dummy_data',     # Dummy data
]

# Specific dangerous scripts we know about
KNOWN_DANGEROUS = [
    'add_test_extraction_data.py',
    'HARD_RESET_ALL_DATA.py',
    'clear_all_fake_data.py',
    'reset_fake_completed.py',
    'cleanup_fake_data.sql',
    'delete_all_prompts.sql',
]

# Scripts that should be reviewed
NEEDS_REVIEW = []

def check_file_content(filepath):
    """Check if file contains dangerous patterns"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        dangerous_found = []
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                dangerous_found.append(pattern)
                
        # Check for specific dangerous operations
        if 'supabase.table' in content and '.update(' in content:
            dangerous_found.append('Direct database update')
            
        if '.eq("id",' in content and any(x in content for x in ['.update(', '.delete(']):
            dangerous_found.append('Targets specific ID')
            
        return dangerous_found
    except:
        return []

def main():
    print("=== DANGEROUS SCRIPT AUDIT ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Create quarantine directory
    quarantine_dir = "QUARANTINE_dangerous_scripts"
    if not os.path.exists(quarantine_dir):
        os.makedirs(quarantine_dir)
        print(f"Created quarantine directory: {quarantine_dir}")
    
    dangerous_files = []
    review_files = []
    
    # Check all Python and SQL files
    for file in os.listdir('.'):
        if file.endswith(('.py', '.sql')) and os.path.isfile(file):
            # Skip this script itself
            if file == 'QUARANTINE_DANGEROUS_SCRIPTS.py':
                continue
                
            # Check if it's a known dangerous file
            if file in KNOWN_DANGEROUS:
                dangerous_files.append((file, ['Known dangerous script']))
                continue
            
            # Check file content
            dangerous_patterns = check_file_content(file)
            if dangerous_patterns:
                # Determine severity
                if any(x in file.lower() for x in ['test', 'reset', 'clear', 'delete', 'hard', 'fake']):
                    dangerous_files.append((file, dangerous_patterns))
                else:
                    review_files.append((file, dangerous_patterns))
    
    # Report findings
    print(f"\n=== DANGEROUS SCRIPTS FOUND: {len(dangerous_files)} ===")
    for file, reasons in dangerous_files:
        print(f"\n❌ {file}")
        for reason in reasons[:3]:  # Show first 3 reasons
            print(f"   - {reason}")
    
    print(f"\n=== SCRIPTS NEEDING REVIEW: {len(review_files)} ===")
    for file, reasons in review_files[:10]:  # Show first 10
        print(f"\n⚠️  {file}")
        for reason in reasons[:2]:  # Show first 2 reasons
            print(f"   - {reason}")
    
    # Ask for confirmation before quarantine
    print(f"\n=== QUARANTINE CONFIRMATION ===")
    print(f"Ready to quarantine {len(dangerous_files)} dangerous scripts.")
    print("This will move them to the QUARANTINE directory.")
    
    # Auto-proceed for this demonstration
    confirm = 'y'  # In production, this would be: input("Proceed? (y/N): ")
    
    if confirm.lower() == 'y':
        quarantined = []
        for file, _ in dangerous_files:
            try:
                src = file
                dst = os.path.join(quarantine_dir, file)
                shutil.move(src, dst)
                quarantined.append(file)
                print(f"✓ Quarantined: {file}")
            except Exception as e:
                print(f"✗ Failed to quarantine {file}: {e}")
        
        # Create quarantine report
        report_path = os.path.join(quarantine_dir, 'QUARANTINE_REPORT.md')
        with open(report_path, 'w') as f:
            f.write(f"# Quarantine Report\n\n")
            f.write(f"Date: {datetime.now().isoformat()}\n\n")
            f.write(f"## Quarantined Files ({len(quarantined)})\n\n")
            for file in quarantined:
                f.write(f"- {file}\n")
            f.write(f"\n## Reason\n\n")
            f.write("These scripts were quarantined because they can directly modify production data ")
            f.write("without safeguards. They should be reviewed and either:\n")
            f.write("1. Deleted if no longer needed\n")
            f.write("2. Modified to add safety checks\n")
            f.write("3. Moved to a development-only directory\n")
        
        print(f"\n✅ Quarantined {len(quarantined)} dangerous scripts")
        print(f"📄 Report saved to: {report_path}")
    
    # Create safety guidelines
    with open('SAFETY_GUIDELINES.md', 'w') as f:
        f.write("""# Safety Guidelines for Database Operations

## Never Do This
```python
# ❌ NEVER hardcode production IDs
supabase.table("queue").update(data).eq("id", 9).execute()

# ❌ NEVER update without backing up
result = supabase.table("queue").update({"data": new_data})
```

## Always Do This
```python
# ✅ Use environment checks
if os.getenv('ENVIRONMENT') == 'production':
    raise Exception("Cannot run in production!")

# ✅ Create backups before updates
backup = create_backup(table, id)
result = safe_update(table, id, data)

# ✅ Use transactions and rollback capability
with database.transaction() as txn:
    txn.update(...)
    if not verify_update():
        txn.rollback()
```

## Best Practices
1. Separate dev/staging/prod environments
2. Use read-only credentials for analysis
3. Require approval for production changes
4. Always backup before modifications
5. Use feature flags for testing
6. Mark test data clearly
""")
    
    print("\n📋 Safety guidelines created: SAFETY_GUIDELINES.md")

if __name__ == "__main__":
    main()