#!/usr/bin/env python3
'''
Example migration for: ./trace_fake_data_insertion.py
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
    # supabase.table('ai_extraction_queue').update({'status': 'completed'}).eq('id', 9).execute()
    
    # NEW WAY (SAFE):
    try:
        # This will create backup, validate data, and create audit log
        result = DataProtection.safe_update(
            supabase,
            'ai_extraction_queue',
            9,
            {'status': 'completed'}
        )
        print(f"Safely updated record")
    except DataProtectionError as e:
        print(f"Update blocked: {e}")

@protected_database_operation  # Alternative decorator
def insert_test_data_safely():
    '''Example of safe test data insertion'''
    
    # OLD WAY (DANGEROUS):
    # test_data = {'name': 'Coca Cola', 'price': 2.99}
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
    print(f"Environment: {env_config.environment}")
    print(f"Can modify data: {env_config.can_modify_data()}")
    
    # Only run dangerous operations in development
    if env_config.is_development:
        update_queue_item_safely()
        insert_test_data_safely()
    else:
        print("Dangerous operations skipped in this environment")
    
    # Safe operations can run anywhere
    data = read_only_operation()
    print(f"Found {len(data)} completed items")
