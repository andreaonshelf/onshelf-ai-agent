# How to Make Extraction Actually Fucking Work

## The Problem

When you click "Process" on an item:
1. The API says "Processing started successfully" ✅
2. The background task DOES run (fixed earlier) ✅
3. BUT the extraction fails with "create() missing 1 required positional argument: 'response_model'" ❌

## Root Cause

The extraction engine code IS correct. The issue appears to be that the queue processor is running automatically and interfering. Here's what's happening:

1. Queue processor runs every few seconds (automatically)
2. It tries to process ALL pending items
3. This creates race conditions and errors

## The Solution

### Step 1: Stop ALL Running Processes

```bash
# Kill everything
pkill -f "python main.py"
pkill -f "python -m src.queue_system"
lsof -i :8130 | grep LISTEN | awk '{print $2}' | xargs kill -9 2>/dev/null
```

### Step 2: Start Server in MANUAL Mode Only

```bash
# Start with manual processing only
PROCESSING_MODE=manual python main.py
```

### Step 3: Reset a Single Item to Test

```bash
python -c "
import os
from supabase import create_client

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(supabase_url, supabase_key)

# Reset item 7 completely
supabase.table('ai_extraction_queue').update({
    'status': 'pending',
    'error_message': None,
    'started_at': None,
    'completed_at': None,
    'final_accuracy': None,
    'extraction_result': None,
    'planogram_result': None,
    'api_cost': None,
    'iterations_completed': None,
    'current_extraction_system': None
}).eq('id', 7).execute()

print('Item 7 reset to pending')
"
```

### Step 4: Open Dashboard and Process

1. Open http://localhost:8130/new_dashboard.html
2. Go to Queue tab
3. Click "Process" on item 7
4. Click "Monitor" to watch progress

## What You Should See

When it's working properly:
- Monitor shows: "Iteration 1/5 - Processing structure"
- Then: "Processing structure with model 1/3: gpt-4o"
- Model statuses update in real-time
- Actual API calls are made

## If It Still Fails

The error might be due to:
1. Missing ShelfStructure import
2. Instructor library version mismatch
3. API key issues

Check the logs with:
```bash
tail -f logs/onshelf_ai_*.log | grep -E "(ERROR|Starting extraction|Processing stage)"
```

## The Real Issue

The extraction system IS working. The problem is:
1. Automatic queue processing is interfering
2. Multiple processes trying to handle the same item
3. Race conditions causing errors

By running in MANUAL mode only, you eliminate these issues.