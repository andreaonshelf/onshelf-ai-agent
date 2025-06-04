# Complete Extraction Flow Trace

## Overview
This document traces the EXACT flow of what happens during extraction, from when `process_queue_item` is called through all components, prompts, and AI calls.

## 1. Entry Point: Queue Processing API

### Location: `src/api/queue_processing.py`

**Line 22-90**: `process_queue_item()` endpoint
- Receives: `item_id`, `system`, `max_budget`, `configuration`
- Updates queue status to "processing"
- Initializes monitoring data
- Calls `run_extraction()` in background task

**Line 93-200**: `run_extraction()` async function
- Creates `MasterOrchestrator` instance (line 108)
- Calls `orchestrator.achieve_target_accuracy()` (line 130) with:
  - `upload_id`
  - `target_accuracy=0.95`
  - `max_iterations=5`
  - `queue_item_id`
  - `system` (e.g., "custom_consensus")
  - `configuration` (UI settings including prompts)

## 2. Master Orchestrator

### Location: `src/orchestrator/master_orchestrator.py`

**Line 52-518**: `achieve_target_accuracy()` method
- **Line 62-77**: Checks if stage-based execution is configured
  - If `stages` and `stage_models` exist in config → uses stage-based pipeline
  - Otherwise → uses iteration-based approach

### Iteration-Based Flow (Default):

**Line 114-129**: Initialize extraction orchestrator
- Creates `ExtractionOrchestrator` instance with queue_item_id
- **IMPORTANT**: Loads configuration into orchestrator:
  ```python
  self.extraction_orchestrator.model_config = configuration
  self.extraction_orchestrator.temperature = configuration.get('temperature', 0.7)
  self.extraction_orchestrator.orchestrator_model = configuration.get('orchestrator_model', 'claude-4-opus')
  self.extraction_orchestrator.orchestrator_prompt = configuration.get('orchestrator_prompt', '')
  self.extraction_orchestrator.stage_models = configuration.get('stage_models', {})
  ```

**Line 163-419**: Main iteration loop
- For each iteration (1 to max_iterations):
  
  **Line 205-214**: Calls `extraction_orchestrator.extract_with_cumulative_learning()`
  - Passes: image, iteration number, previous attempts, focus areas, locked positions
  
  **Line 250-257**: Generates planogram for visual comparison
  
  **Line 285-292**: Performs AI visual comparison (if planogram PNG available)
  - Uses configured comparison model
  
  **Line 305-310**: Analyzes accuracy and failure areas

## 3. Extraction Orchestrator

### Location: `src/orchestrator/extraction_orchestrator.py`

**Line 26-55**: Constructor
- **Line 39-41**: Loads model configuration from queue item if provided
- **Line 43-44**: Initializes `ModularExtractionEngine` with temperature
- **Line 47-48**: Passes queue context to engine

**Line 386-429**: `_load_model_config()` method
- Loads from Supabase `ai_extraction_queue.model_config`
- Sets:
  - `temperature`
  - `orchestrator_model`
  - `orchestrator_prompt`
  - `stage_models`
  - `stage_configs`
  - **Line 410-418**: Extracts `stage_prompts` and `stage_fields` from configuration

**Line 56-115**: `extract_with_cumulative_learning()` method
- **Line 78-84**: Structure analysis (first iteration only)
- **Line 95-100**: Executes agent with context via `_execute_agent_with_context()`

**Line 167-220**: `_execute_agent_with_context()` method
- **Line 197-203**: Calls `_execute_shelf_by_shelf_extraction()`

**Line 473-628**: `_execute_shelf_by_shelf_extraction()` method - **KEY METHOD**
- **Line 486-494**: Checks for custom prompt:
  ```python
  if hasattr(self, 'stage_prompts') and 'products' in self.stage_prompts:
      shelf_prompt_template = self.stage_prompts['products']  # FROM UI CONFIG
  else:
      shelf_prompt_template = prompt_templates.get_template("shelf_by_shelf_extraction")  # HARDCODED
  ```
- **Line 512-537**: Processes {IF_RETRY} blocks in prompt
- **Line 563-578**: Executes extraction with configured model:
  ```python
  shelf_result, api_cost = await self.extraction_engine.execute_with_model_id(
      model_id=model_id,
      prompt=shelf_prompt,
      images={"main": image},
      output_schema="List[ProductExtraction]"
  )
  ```

## 4. Extraction Engine (Actual AI Calls)

### Location: `src/extraction/engine.py`

**Line 458-478**: `execute_with_model_id()` method
- Maps frontend model IDs to API model names
- Routes to appropriate provider method

**Line 639-776**: `_execute_with_claude_internal()` method
- **Line 710-740**: Makes actual API call to Claude:
  ```python
  response = self.anthropic_client.messages.create(
      model=api_model,
      max_tokens=6000,
      temperature=self.temperature,
      messages=messages,
      response_model=List[ProductExtraction]  # Structured output
  )
  ```

**Line 783-881**: `_execute_with_gpt4o_internal()` method
- **Line 823-829**: Makes actual API call to GPT-4:
  ```python
  response = self.openai_client.chat.completions.create(
      model=api_model,
      messages=messages,
      response_model=List[ProductExtraction],
      max_tokens=6000,
      temperature=self.temperature
  )
  ```

## 5. Prompt Sources

### Hardcoded Prompts
**Location**: `src/extraction/prompts.py`
- `PromptTemplates` class contains hardcoded templates
- Used as fallback when no UI configuration exists

### UI-Configured Prompts
**Location**: Database `prompt_templates` table
- Loaded via `src/api/prompt_management.py`
- Stored in `configuration` object passed through the flow
- Accessed via `stage_prompts` dictionary in extraction orchestrator

## Summary of Prompt Usage

1. **Structure Stage**: 
   - Checks `stage_prompts['structure']` first (UI)
   - Falls back to `PromptTemplates.get_template('scaffolding_analysis')` (hardcoded)

2. **Products Stage**:
   - Checks `stage_prompts['products']` first (UI)
   - Falls back to `PromptTemplates.get_template('shelf_by_shelf_extraction')` (hardcoded)

3. **Details Stage**:
   - Checks `stage_prompts['details']` first (UI)
   - Falls back to `PromptTemplates.get_template('details_extraction')` (hardcoded)

## Data Flow

1. **Configuration flows down**:
   - Queue API → Master Orchestrator → Extraction Orchestrator → Extraction Engine

2. **Key configuration includes**:
   - `temperature`: Controls AI randomness
   - `stage_models`: Which AI models to use for each stage
   - `stage_prompts`: Custom prompts from UI
   - `comparison_config`: Visual comparison settings

3. **Results flow up**:
   - Extraction Engine → Extraction Orchestrator → Master Orchestrator → Queue API
   - Each level adds metadata and tracking

## AI Calls Per Iteration

For a typical 4-shelf image with iteration-based approach:

1. **Structure Analysis**: 1 AI call (Claude)
2. **Product Extraction**: 4 AI calls (1 per shelf)
3. **Visual Comparison**: 1 AI call (GPT-4 Vision)

Total: ~6 AI calls per iteration

## Model Selection

Models are selected based on:
1. UI configuration in `stage_models`
2. Fallback to hardcoded defaults in `_select_model_for_agent()`
3. Model mapping in `_get_api_model_name()`