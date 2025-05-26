# Live Prompt Monitoring System

## Overview

The debug interface now includes **real-time prompt monitoring** that shows exactly which prompts are being used by each AI model during live extractions. This provides unprecedented visibility into the extraction process and helps understand how different models approach the same task.

## Features

### 🤖 Real-Time Prompt Display
- **Live Updates**: Shows prompts as they're being used during extraction
- **Model Identification**: Each prompt is color-coded by AI model:
  - 🟢 **GPT-4o/GPT-4o-Latest**: Green
  - 🔵 **Claude-3.5-Sonnet**: Blue  
  - 🟡 **Gemini-2.0-Flash**: Orange
- **Step Context**: Shows which extraction step is using the prompt
- **Agent Tracking**: Identifies which agent/iteration is running the prompt

### 📋 Prompt Content Viewing
- **Truncated Preview**: Shows first 300 characters for quick overview
- **Full Content Modal**: Click "View Full Prompt" to see complete prompt
- **Copy Functionality**: Copy prompts to clipboard for analysis
- **Timestamp Tracking**: Shows exactly when each prompt was used

### 🔄 Smart Management
- **Auto-Cleanup**: Keeps only last 10 prompts to avoid memory issues
- **Newest First**: Most recent prompts appear at the top
- **Unique Tracking**: Replaces prompts from same model/step combination

## Enhanced Prompt Templates

### New Planogram-Aware Prompts
The system now includes enhanced prompt templates that explain planogram generation logic to AI models:

#### `planogram_aware_extraction`
- Explains how extraction data becomes planograms
- Details the 2D grid system (shelf_level × position_on_shelf)
- Clarifies facings vs. stacking concepts
- Provides quality checks for planogram compatibility

#### Enhanced `mismatch_analysis`
- Includes planogram generation logic explanation
- Helps AI understand how to compare planograms vs. original images
- Provides context for spatial relationships and grid positioning

## Benefits for Accuracy

### 🎯 **Improved Model Understanding**
By explaining planogram generation logic to AI models:
- Models understand that their extraction directly drives visual output
- Better distinction between facings (horizontal) and stacking (vertical)
- More accurate position numbering and spatial relationships
- Quality self-checks during extraction

### 🔍 **Better Debugging**
- See exactly what instructions each model receives
- Compare prompt variations between different systems
- Identify prompt optimization opportunities
- Track prompt evolution during iterations

### 📊 **Enhanced Comparison Analysis**
- AI comparison agents understand planogram structure
- More accurate mismatch identification
- Better root cause analysis for accuracy issues
- Improved feedback for next iterations

## Usage in Debug Interface

### Accessing Live Prompts
1. Start a debug session for any extraction
2. The "🤖 Live Prompt Monitoring" panel appears automatically
3. Prompts appear in real-time as models execute

### Viewing Prompt Details
- **Quick View**: See truncated prompt content in the main panel
- **Full View**: Click "📄 View Full Prompt" for complete content
- **Copy**: Click "📋 Copy" to copy prompt to clipboard

### Understanding the Display
```
🤖 GPT-4o • Step: scaffolding • Template: scaffolding_analysis • Agent: agent_1
[Timestamp: 14:32:15]

You are an expert retail shelf analyst. Analyze this retail shelf image for STRUCTURE ONLY.

CRITICAL TASKS:
1. Count shelf levels from bottom (1) to top
2. Measure image dimensions in pixels (width x height)
...
```

## Technical Implementation

### WebSocket Integration
- Prompts are sent via WebSocket as `prompt_used` events
- Real-time updates without page refresh
- Minimal performance impact on extraction

### Data Structure
```javascript
{
    type: 'prompt_used',
    model: 'GPT-4o',
    step: 'scaffolding',
    prompt_template: 'scaffolding_analysis',
    prompt_content: 'Full prompt text...',
    agent_id: 'agent_1'
}
```

### Frontend Components
- `displayLivePrompt()`: Main display function
- `expandPrompt()`: Full content modal
- `copyPrompt()`: Clipboard functionality
- Auto-cleanup and memory management

## Future Enhancements

### Planned Features
- **Prompt Performance Tracking**: Link prompts to accuracy outcomes
- **Template Comparison**: Side-by-side prompt template analysis
- **Prompt Optimization Suggestions**: AI-driven prompt improvements
- **Historical Prompt Analysis**: Track prompt evolution over time

### Integration Opportunities
- **Human Learning System**: Feed prompt performance back to learning
- **A/B Testing**: Compare different prompt variations
- **Cost Analysis**: Track API costs per prompt template
- **Quality Metrics**: Correlate prompt content with extraction quality

## Impact on System Performance

This feature significantly improves the extraction system by:

1. **🎯 Better AI Understanding**: Models know how their output becomes planograms
2. **🔍 Enhanced Debugging**: Real-time visibility into AI decision-making
3. **📈 Improved Accuracy**: Planogram-aware prompts lead to better extractions
4. **🔄 Faster Iteration**: Quick identification of prompt-related issues
5. **📚 Knowledge Transfer**: Understanding successful prompt patterns

The live prompt monitoring bridges the gap between AI processing and human understanding, making the entire extraction system more transparent and debuggable. 