import asyncio
import os
from supabase import create_client

# Get Supabase credentials
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

async def test_extraction():
    if not supabase_url or not supabase_key:
        print("Missing Supabase credentials")
        return
        
    supabase = create_client(supabase_url, supabase_key)
    
    # Get a pending item
    result = supabase.table("ai_extraction_queue").select("*").eq("status", "pending").limit(1).execute()
    
    if not result.data:
        print("No pending items found")
        return
        
    item = result.data[0]
    print(f"Testing extraction for item {item['id']}, upload {item['upload_id']}")
    
    # Import required modules
    from src.config import SystemConfig
    from src.orchestrator.system_dispatcher import SystemDispatcher
    from src.utils import logger
    
    try:
        # Initialize
        config = SystemConfig()
        config.max_budget = 2.0
        
        # Create dispatcher
        dispatcher = SystemDispatcher(config, supabase_client=supabase)
        
        print("Dispatcher created, starting extraction...")
        
        # Try to run extraction
        result = await dispatcher.achieve_target_accuracy(
            upload_id=item['upload_id'],
            target_accuracy=0.95,
            max_iterations=5,
            queue_item_id=item['id'],
            system='custom_consensus',
            configuration={}
        )
        
        print(f"Extraction completed! Accuracy: {result.final_accuracy}")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print("\nFull traceback:")
        print(traceback.format_exc())

# Run the test
asyncio.run(test_extraction())