#!/usr/bin/env python3
"""
Attempt to recover the original Co-op extraction data for queue item 9
"""
import os
import json
import re
from datetime import datetime
from supabase import create_client

# Get Supabase credentials
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_KEY')

if not url or not key:
    print("Missing Supabase credentials")
    exit(1)

# Initialize client
supabase = create_client(url, key)

def check_database_backups():
    """Check if there are any backups in the database"""
    print("\n1. Checking for database backups...")
    
    # Check if backup tables exist
    try:
        result = supabase.table('data_backups').select('*').eq('table_name', 'ai_extraction_queue').eq('record_id', 9).execute()
        if result.data:
            print(f"   ✓ Found {len(result.data)} backups for queue item 9")
            return result.data
        else:
            print("   ✗ No backups found in data_backups table")
    except:
        print("   ✗ data_backups table does not exist")
    
    return None

def check_audit_logs():
    """Check audit logs for the original data"""
    print("\n2. Checking audit logs...")
    
    try:
        result = supabase.table('audit_log').select('*').eq('table_name', 'ai_extraction_queue').eq('record_id', 9).order('timestamp', desc=True).execute()
        if result.data:
            print(f"   ✓ Found {len(result.data)} audit entries")
            
            # Look for the update that added test data
            for entry in result.data:
                if entry.get('new_data') and 'Coca Cola' in str(entry.get('new_data', '')):
                    print("   ✓ Found the update that added test data")
                    if entry.get('old_data'):
                        print("   ✓ Original data might be in old_data field!")
                        return entry['old_data']
            
            print("   ✗ Could not find the specific update")
        else:
            print("   ✗ No audit logs found")
    except:
        print("   ✗ audit_log table does not exist")
    
    return None

def check_log_files():
    """Search log files for the original extraction data"""
    print("\n3. Checking log files...")
    
    log_patterns = [
        r'"products":\s*\[(.*?)\]',
        r'Extracted products:.*?(\[.*?\])',
        r'product.*?Co-op.*?(\{.*?\})',
    ]
    
    log_dir = 'logs'
    if os.path.exists(log_dir):
        for log_file in os.listdir(log_dir):
            if log_file.startswith('onshelf_ai_202506'):  # June 2025 logs
                log_path = os.path.join(log_dir, log_file)
                print(f"   Checking {log_file}...")
                
                try:
                    with open(log_path, 'r') as f:
                        content = f.read()
                        
                    # Look for extraction completion around 23:03:02
                    if '23:03:02' in content and 'queue.*9' in content:
                        print(f"   ✓ Found extraction completion in {log_file}")
                        
                        # Try to extract product data
                        for pattern in log_patterns:
                            matches = re.findall(pattern, content, re.DOTALL)
                            if matches:
                                print(f"   ✓ Found potential product data!")
                                return matches
                except Exception as e:
                    print(f"   ✗ Error reading {log_file}: {e}")
    
    return None

def check_supabase_logs():
    """Check if Supabase has transaction logs"""
    print("\n4. Checking Supabase transaction logs...")
    
    # This would require Supabase dashboard access
    print("   ℹ️  Transaction logs require Supabase dashboard access")
    print("   ℹ️  Check: https://app.supabase.com/project/[project-id]/logs/explorer")
    print("   ℹ️  Look for UPDATE queries on 2025-06-09 targeting ai_extraction_queue id=9")
    
    return None

def attempt_reconstruction():
    """Try to reconstruct based on typical Co-op products"""
    print("\n5. Attempting reconstruction based on store type...")
    
    print("   ℹ️  Queue item 9 was for Co-op Food - Greenwich - Trafalgar Road")
    print("   ℹ️  Typical Co-op products might include:")
    print("      - Co-op own brand items")
    print("      - Common UK grocery products")
    print("      - Fresh produce, dairy, beverages")
    
    # Check if we have the original image
    result = supabase.table('ai_extraction_queue').select('ready_media_id,enhanced_image_path,upload_id').eq('id', 9).execute()
    if result.data and result.data[0]:
        ready_media_id = result.data[0].get('ready_media_id')
        enhanced_path = result.data[0].get('enhanced_image_path')
        upload_id = result.data[0].get('upload_id')
        
        if ready_media_id or enhanced_path or upload_id:
            print(f"   ✓ Original image reference found: upload_id={upload_id}, media_id={ready_media_id}")
            print("   ℹ️  Could re-process the image to recover data")
            return True
    
    return False

def main():
    print("=== ATTEMPTING DATA RECOVERY FOR QUEUE ITEM 9 ===")
    print("Lost: Real Co-op extraction data")
    print("Replaced with: Test data (Coca Cola, Pepsi, etc.)")
    print("Date of incident: 2025-06-09")
    
    # Try various recovery methods
    backup_data = check_database_backups()
    audit_data = check_audit_logs()
    log_data = check_log_files()
    supabase_data = check_supabase_logs()
    can_reprocess = attempt_reconstruction()
    
    print("\n=== RECOVERY OPTIONS ===")
    
    if backup_data:
        print("✅ Database backup available - can restore")
    elif audit_data:
        print("✅ Audit log contains original data - can restore")
    elif log_data:
        print("⚠️  Partial data found in logs - manual reconstruction needed")
    elif can_reprocess:
        print("✅ Original image available - can re-extract")
    else:
        print("❌ No automatic recovery possible")
        print("\nManual options:")
        print("1. Check Supabase dashboard for transaction logs")
        print("2. Check if team members have local database dumps")
        print("3. Re-process the image through the extraction pipeline")
    
    print("\n=== PREVENTION MEASURES IMPLEMENTED ===")
    print("✓ Dangerous scripts quarantined")
    print("✓ Data protection layer created")
    print("✓ Audit logging SQL ready to deploy")
    print("✓ Safety guidelines documented")
    
    print("\n=== NEXT STEPS ===")
    print("1. Deploy audit logging: psql < create_audit_tables.sql")
    print("2. Update all scripts to use DataProtection class")
    print("3. Set up separate development database")
    print("4. Implement approval process for production changes")
    print("5. Re-extract queue item 9 to recover real data")

if __name__ == "__main__":
    main()