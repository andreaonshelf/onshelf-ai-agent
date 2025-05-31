# Backend Model Integration - Complete Implementation

## Overview
This document summarizes the full backend implementation to support the frontend model configurations, including model selection per stage, temperature control, orchestrator selection, and usage analytics.

## Changes Implemented

### 1. Database Schema Updates

#### Model Configuration Storage
- Added `model_config` JSONB column to `ai_extraction_queue` table
- Stores temperature, orchestrator model/prompt, and stage-specific model selections

#### Model Usage Analytics Tables
- **model_usage**: Tracks individual model API calls
  - Queue item ID, stage, model, provider
  - Token counts, response time, cost
  - Success/failure tracking
- **configuration_usage**: Tracks configuration performance
  - Times used, average accuracy/cost/duration
  - Success rate tracking
- **Views**: `model_performance_analytics` and `configuration_performance`

### 2. API Updates

#### Queue Management (`src/api/queue_management.py`)
- Updated `/queue/process/{item_id}` endpoint to accept:
  - `temperature`: Model creativity setting (0-1)
  - `orchestrator_model`: Which model manages the process
  - `orchestrator_prompt`: Custom instructions for orchestrator
  - `stage_models`: Dict mapping stages to model arrays
- Stores configuration in `model_config` column

### 3. Orchestrator Updates

#### Extraction Orchestrator (`src/orchestrator/extraction_orchestrator.py`)
- Loads model configuration from queue item
- `_select_model_for_agent()` now uses configured models
- Maps frontend model IDs to backend enums
- Passes temperature to extraction engine
- Supports stage-specific model selection

#### Master Orchestrator (`src/orchestrator/master_orchestrator.py`)
- Accepts queue_item_id to initialize with correct config
- Creates extraction orchestrator per run with config

### 4. Extraction Engine Updates

#### Modular Extraction Engine (`src/extraction/engine.py`)
- Accepts temperature parameter in constructor
- Passes temperature to all API calls
- Logs model usage for analytics

### 5. Model Usage Tracking

#### Model Usage Tracker (`src/utils/model_usage_tracker.py`)
- Logs each model API call with metrics
- Tracks configuration usage and performance
- Updates aggregate statistics

### 6. Frontend Integration

#### Dashboard Updates (`new_dashboard.html`)
- Sends full model configuration when processing
- Loads saved configuration from localStorage
- Includes all model selections and settings

## Model ID Mappings

Frontend model IDs are mapped to backend implementations:

```python
# OpenAI models
"gpt-4.1" -> GPT4O_LATEST
"gpt-4o" -> GPT4O_LATEST
"o3" -> GPT4O_LATEST

# Anthropic models  
"claude-3-5-sonnet-v2" -> CLAUDE_3_SONNET
"claude-4-opus" -> CLAUDE_3_SONNET

# Google models
"gemini-2.5-pro" -> GEMINI_PRO
```

## Usage Flow

1. **Configuration Creation**:
   - User selects models per stage in UI
   - Sets temperature and orchestrator
   - Saves configuration

2. **Processing**:
   - Queue page loads saved configuration
   - Sends full config when processing items
   - Backend stores in `model_config` column

3. **Execution**:
   - Orchestrator loads config from queue item
   - Uses specified models for each stage
   - Applies temperature to API calls
   - Logs usage for analytics

4. **Analytics**:
   - Model usage tracked per call
   - Configuration performance aggregated
   - Available through views for dashboards

## Database Migration

Run these SQL scripts to set up the schema:

```bash
# Add model_config column
psql $DATABASE_URL < add_model_config_column.sql

# Create analytics tables
psql $DATABASE_URL < create_model_usage_tables.sql
```

## Testing

1. Create a configuration with specific models
2. Process a queue item
3. Check `model_usage` table for entries
4. Verify models match configuration

## Next Steps

1. Create analytics dashboard using the views
2. Add cost optimization recommendations
3. Implement A/B testing for configurations
4. Add model fallback chains for reliability