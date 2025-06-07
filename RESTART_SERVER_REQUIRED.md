# SERVER RESTART REQUIRED

The extraction system fixes have been applied to the following files:

1. **src/systems/langgraph_system.py** - Fixed dynamic model builder parameter order
2. **src/systems/hybrid_system.py** - Fixed dynamic model builder parameter order  
3. **src/orchestrator/extraction_orchestrator.py** - Fixed dynamic model builder parameter order
4. **src/api/queue_management.py** - Fixed batch-configure to build stages with prompts

## To apply the fixes:

1. **Stop the current server** (Ctrl+C in the terminal running the server)
2. **Restart the server**: `python main.py`

## What was fixed:

- The 'str' object has no attribute 'get' error was caused by passing parameters in wrong order to DynamicModelBuilder
- Configurations now properly include stages with prompt texts and fields
- Added visual comparison stage to all configurations

## Additional Notes:

- The Gemini quota errors in the latest logs are a separate issue (API limits)
- The 2 failed queue items have been fixed and can be reprocessed after restart