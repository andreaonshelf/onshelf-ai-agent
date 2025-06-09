#!/usr/bin/env python3
"""Fix queue item 9 by resetting it and trying to process it again"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
from src.config import SystemConfig
from src.orchestrator.system_dispatcher import SystemDispatcher

# Load environment variables
load_dotenv()

async def fix_queue_item_9():
    print("Fix: Queue Item 9")
    print("=" * 60)
    
    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    supabase = create_client(url, key)
    
    # 1. Reset queue item 9 status to pending
    print("Step 1: Resetting queue item 9 status to pending...")
    
    try:
        response = supabase.table("ai_extraction_queue").update({
            "status": "pending",
            "error_message": None,
            "processing_attempts": 0,
            "failed_at": None
        }).eq("id", 9).execute()
        
        if response.data:
            print("✅ Queue item 9 reset to pending status")
        else:
            print("❌ Failed to reset queue item 9")
            return
            
    except Exception as e:
        print(f"❌ Error resetting queue item: {e}")
        return
    
    # 2. Verify the configuration is still correct
    print("\nStep 2: Verifying configuration...")
    
    response = supabase.table("ai_extraction_queue").select("*").eq("id", 9).execute()
    if not response.data:
        print("❌ Queue item 9 not found")
        return
        
    queue_item = response.data[0]
    extraction_config = queue_item.get('extraction_config', {})
    
    if not extraction_config.get('stages'):
        print("❌ No stages in extraction_config")
        return
        
    structure_config = extraction_config['stages'].get('structure', {})
    if not structure_config.get('fields'):
        print("❌ No fields in structure stage")
        return
        
    print(f"✅ Configuration verified:")
    print(f"  - Stages: {list(extraction_config['stages'].keys())}")
    print(f"  - Structure fields: {len(structure_config['fields'])}")
    
    # 3. Try processing manually using SystemDispatcher
    print("\nStep 3: Processing manually with SystemDispatcher...")
    
    try:
        config = SystemConfig()
        
        # Create SystemDispatcher
        dispatcher = SystemDispatcher(config, queue_item_id=9)
        
        # Extract configuration like the queue processor does
        model_config = queue_item.get('model_config', {})
        configuration = extraction_config if extraction_config.get('stages') else model_config
        system = configuration.get('system') or queue_item.get('current_extraction_system', 'custom_consensus')
        upload_id = queue_item['upload_id']
        
        print(f"Processing with system: {system}")
        print(f"Upload ID: {upload_id}")
        print(f"Configuration type: {'extraction_config' if extraction_config.get('stages') else 'model_config'}")
        
        # Mark as processing in database first
        supabase.table("ai_extraction_queue").update({
            "status": "processing"
        }).eq("id", 9).execute()
        
        # Process with master orchestrator
        result = await dispatcher.achieve_target_accuracy(
            upload_id=upload_id,
            queue_item_id=9,
            system=system,
            configuration=configuration
        )
        
        print(f"✅ Processing completed successfully!")
        print(f"Final accuracy: {getattr(result, 'final_accuracy', 'N/A')}")
        
        # Mark as completed
        supabase.table("ai_extraction_queue").update({
            "status": "completed",
            "completed_at": "now()",
            "final_accuracy": getattr(result, 'final_accuracy', 0.0),
            "extraction_result": getattr(result, 'extraction_result', {}) if hasattr(result, 'extraction_result') else {},
            "planogram_result": getattr(result, 'planogram_result', {}) if hasattr(result, 'planogram_result') else {}
        }).eq("id", 9).execute()
        
        print("✅ Queue item 9 marked as completed in database")
        
    except Exception as e:
        print(f"❌ Processing failed: {e}")
        
        # Mark as failed again
        supabase.table("ai_extraction_queue").update({
            "status": "failed",
            "error_message": str(e),
            "failed_at": "now()"
        }).eq("id", 9).execute()
        
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_queue_item_9())