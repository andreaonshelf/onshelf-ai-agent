#!/usr/bin/env python3
"""
Fix for the missing model_config column issue.
This script updates the code to handle both model_config and extraction_config columns
to maintain backward compatibility while the migration is pending.
"""

import os

def fix_processor_py():
    """Fix processor.py to handle missing model_config column"""
    file_path = "/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src/queue_system/processor.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix line 124 to use extraction_config as fallback
    old_line = "configuration = queue_item.get('model_config', {})"
    new_line = "configuration = queue_item.get('model_config') or queue_item.get('extraction_config', {})"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(file_path, 'w') as f:
            f.write(content)
        print("✓ Fixed processor.py to handle missing model_config column")
    else:
        print("✗ Could not find the exact line to replace in processor.py")
        print("  Looking for alternative fix...")
        
        # Alternative fix
        alt_old = "queue_item.get('model_config', {})"
        alt_new = "(queue_item.get('model_config') or queue_item.get('extraction_config', {}))"
        
        if alt_old in content:
            content = content.replace(alt_old, alt_new)
            with open(file_path, 'w') as f:
                f.write(content)
            print("✓ Applied alternative fix to processor.py")

def fix_queue_management_py():
    """Fix queue_management.py to save to both columns"""
    file_path = "/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram/src/api/queue_management.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find where model_config is being set in updates
    lines = content.split('\n')
    modified = False
    
    for i, line in enumerate(lines):
        if "'model_config':" in line and "'extraction_config':" not in line:
            # Check if the next line doesn't already have extraction_config
            next_lines = '\n'.join(lines[i:i+5])
            if "'extraction_config':" not in next_lines:
                # Add extraction_config as duplicate
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + f"'extraction_config': model_config,  # Duplicate for backward compatibility"
                lines.insert(i + 1, new_line)
                modified = True
                print(f"✓ Added extraction_config duplicate at line {i+1}")
    
    if modified:
        content = '\n'.join(lines)
        with open(file_path, 'w') as f:
            f.write(content)
        print("✓ Fixed queue_management.py to save to both columns")
    else:
        print("ℹ️  queue_management.py may already be fixed or needs manual review")

def main():
    print("Applying fixes for missing model_config column...\n")
    
    fix_processor_py()
    fix_queue_management_py()
    
    print("\n✅ Fixes applied!")
    print("\nNote: These are temporary fixes. The proper solution is to run the migration:")
    print("  ALTER TABLE ai_extraction_queue ADD COLUMN IF NOT EXISTS model_config JSONB DEFAULT '{}'::jsonb;")
    print("\nYou can run this in your Supabase SQL Editor.")

if __name__ == "__main__":
    main()