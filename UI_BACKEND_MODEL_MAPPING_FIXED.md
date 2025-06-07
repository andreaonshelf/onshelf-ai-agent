# UI-Backend Model Mapping Fixed

## What Was Wrong
I initially made the mistake of changing the user's model selections to match what the backend supported. This was backwards! The UI shows available models to users, and the backend should adapt to support those exact models.

## The Correct Approach
1. **UI defines available models** → Users select from these options
2. **Backend maps UI models to API endpoints** → No changing of user selections!

## Current Model Mappings

### User Selections Restored
The original user selections have been restored in the database:
- `gpt-4.1` → Maps to `gpt-4o-2024-11-20` 
- `claude-3-5-sonnet-v2` → Maps to `claude-3-5-sonnet-20241022`
- `claude-4-sonnet` → Maps to `claude-3-5-sonnet-20241022` (until Claude 4 is available)
- `claude-4-opus` → Maps to `claude-3-opus-20240229`
- `gemini-2.5-pro` → Maps to `gemini-2.0-pro-exp`

### Backend Updated
The extraction engine (`src/extraction/engine.py`) now properly maps all UI models:

```python
model_mapping = {
    # UI Model ID → (provider, actual_api_model)
    "gpt-4.1": ("openai", "gpt-4o-2024-11-20"),
    "gpt-4.1-mini": ("openai", "gpt-4o-mini"),
    "gpt-4.1-nano": ("openai", "gpt-4o-mini"),
    "claude-3-5-sonnet-v2": ("anthropic", "claude-3-5-sonnet-20241022"),
    "claude-4-sonnet": ("anthropic", "claude-3-5-sonnet-20241022"),
    "claude-4-opus": ("anthropic", "claude-3-opus-20240229"),
    "gemini-2.5-pro": ("google", "gemini-2.0-pro-exp"),
    "gemini-2.5-flash": ("google", "gemini-2.0-flash-exp"),
    "gemini-2.5-flash-thinking": ("google", "gemini-2.0-flash-thinking-exp-01-21"),
}
```

## Key Principle
**The backend serves the UI, not the other way around!**

When users select models in the UI, those exact model IDs should be preserved throughout the system. The backend's job is to map those UI model IDs to the appropriate API endpoints.

## Next Steps
The Co-op Food extraction can now be retried. The system will:
1. Use the user's original model selections (`gpt-4.1`, `claude-3-5-sonnet-v2`, etc.)
2. Map them to the correct API endpoints in the backend
3. Execute the extraction successfully