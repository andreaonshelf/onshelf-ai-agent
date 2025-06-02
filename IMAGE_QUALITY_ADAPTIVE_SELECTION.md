# Image Quality Adaptive Model Selection

## Overview

The system now includes intelligent image quality analysis that automatically recommends the best extraction system and models based on the characteristics of each shelf image.

## How It Works

1. **Image Analysis**: When an image is uploaded or selected, the system analyzes:
   - Brightness levels
   - Sharpness/blur
   - Contrast
   - Noise levels
   - Edge density (clutter)
   - Color saturation
   - Occlusions
   - Specific issues (shadows, reflections, etc.)

2. **Smart Recommendations**: Based on the analysis, the system recommends:
   - Best extraction system (Custom Consensus, LangGraph, or Hybrid)
   - Optimal model for each extraction phase:
     - Structure analysis
     - Product extraction
     - Detail enhancement

3. **Learning System**: The system tracks performance and learns over time:
   - Stores actual extraction results vs predictions
   - Updates model performance profiles
   - Improves recommendations based on historical data

## Model Selection Logic

### High-Quality Images (>70% quality score)
- **System**: Custom Consensus (fastest, most efficient)
- **Models**: Standard high-accuracy configuration
- **Use case**: Well-lit, clear shelf images

### Medium-Quality Images (40-70% quality score)
- **System**: Hybrid (adaptive approach)
- **Models**: Mixed based on specific issues
- **Use case**: Some shadows, minor blur, or partial occlusions

### Low-Quality Images (<40% quality score)
- **System**: LangGraph (most robust)
- **Models**: Specialized for challenging conditions
- **Use case**: Dark, blurry, heavily cluttered shelves

## Model Profiles

### GPT-4 Vision
- **Strengths**: High-quality images, clear details, standard layouts
- **Weaknesses**: Very dark images, extreme blur
- **Best for**: Product details, price extraction

### Claude 3
- **Strengths**: Complex scenes, cluttered shelves, shadows
- **Weaknesses**: Low contrast images
- **Best for**: Structure analysis, understanding layout

### Gemini Vision
- **Strengths**: Dark images, reflections, varied lighting
- **Weaknesses**: Extremely cluttered scenes
- **Best for**: Challenging lighting conditions

## UI Features

1. **Queue View**: 
   - Image quality indicators on each queue item
   - Auto-recommendations when selecting items

2. **Smart Recommendations Panel**:
   - Shows quality score and detected issues
   - Displays recommended configuration
   - One-click to apply recommendations

3. **Manual Analysis**:
   - "Analyze Image" button for on-demand analysis
   - Detailed quality metrics display

## API Endpoints

### `POST /api/image/analyze-quality`
Analyzes an uploaded image and returns quality metrics and recommendations.

### `GET /api/image/quality-stats`
Returns aggregated statistics about image quality and model performance.

### `POST /api/image/learn-performance`
Updates the learning system with actual extraction results.

## Database Schema

New tables added:
- `image_quality_analysis`: Stores quality metrics for each image
- `model_performance_feedback`: Tracks actual vs predicted performance
- `model_performance_stats`: Aggregated performance statistics
- `image_quality_patterns`: Learned patterns for optimization

## Future Enhancements

1. **Automatic Pre-processing**: Apply image enhancements before extraction
2. **Multi-region Analysis**: Different recommendations for different shelf sections
3. **Real-time Performance Tracking**: Live dashboard of model performance
4. **Custom Model Training**: Train specialized models for specific store types
5. **Batch Optimization**: Analyze multiple images to find optimal settings

## Benefits

1. **Higher Accuracy**: Better model selection leads to improved extraction results
2. **Cost Optimization**: Use expensive models only when needed
3. **Faster Processing**: Route simple images to faster models
4. **Reduced Errors**: Proactively handle challenging images
5. **Continuous Improvement**: System gets smarter over time