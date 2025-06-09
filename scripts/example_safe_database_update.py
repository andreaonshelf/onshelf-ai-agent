#!/usr/bin/env python3
"""
Example: Safe Database Operations
Shows how to properly interact with the database using protection
"""
import os
from pathlib import Path
import sys
import uuid

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from src.environment_config.environment import get_environment_config, require_production_check
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
    print("\n=== Safe Update Example ===")
    
    # Never hardcode IDs - get them from queries or parameters
    # For this example, we'll find a pending record (NOT ID 9 which is protected)
    result = supabase.table('ai_extraction_queue').select('id').eq('status', 'pending').neq('id', 9).limit(1).execute()
    
    if not result.data:
        print("No suitable records found to update")
        return
    
    record_id = result.data[0]['id']
    
    try:
        # Safe update with protection
        update_data = {
            'status': 'processing'
            # Only use columns that actually exist
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
    print("\n=== Safe Insert Example ===")
    
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
        'upload_id': f"test-{uuid.uuid4()}",
        'ready_media_id': f"test-media-{uuid.uuid4()}",  # Required field
        'status': 'pending',
        'enhanced_image_path': '/test/path/example.jpg'  # Required field
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
    print("\n=== Safe Read Example ===")
    
    # Reading doesn't need protection
    result = supabase.table('ai_extraction_queue').select(
        'id, status, upload_id, created_at'
    ).limit(5).order('created_at', desc=True).execute()
    
    if result.data:
        print(f"✅ Found {len(result.data)} recent records:")
        for item in result.data:
            print(f"   - {item['id']}: Upload {item.get('upload_id', 'Unknown')} ({item['status']})")
    else:
        print("No records found")

def cleanup_test_data(record_id):
    """Clean up test data after example"""
    if record_id and env_config.is_development:
        try:
            # In development, we can delete test data
            # Only delete if it was created by this script (has test upload ID)
            result = supabase.table('ai_extraction_queue').delete().eq('id', record_id).like('upload_id', 'test-%').execute()
            if result.data:
                print(f"\n✅ Cleaned up test record {record_id}")
        except:
            pass

if __name__ == "__main__":
    # Always show current environment
    print(f"Environment: {env_config.environment}")
    print(f"Can modify data: {env_config.can_modify_data}")
    
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
        print("\n⚠️  Skipping write operations in production environment")
