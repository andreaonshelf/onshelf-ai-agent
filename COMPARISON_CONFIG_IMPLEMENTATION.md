# Comparison Configuration Implementation

## Summary of Changes

This document summarizes the backend changes made to support the comparison configuration UI that was previously implemented in `new_dashboard.html`.

## 1. Comparison Agent Updates

### File: `src/comparison/image_comparison_agent.py`

**Changes Made:**
- Added new parameters to `compare_image_vs_planogram()`:
  - `model_id`: Configurable comparison model (no longer hardcoded to GPT-4)
  - `custom_prompt`: Editable comparison prompt from UI
  - `use_visual_comparison`: Toggle for visual vs text-based comparison
  - `abstraction_layers`: List of enabled abstraction layers

- Implemented model mapping for different providers:
  ```python
  model_mapping = {
      "gpt-4-vision-preview": "gpt-4-vision-preview",
      "claude-3-opus": "claude-3-opus-20240229", 
      "claude-4-opus": "claude-4-opus-20250514",
      "gemini-pro-vision": "gemini-pro-vision"
  }
  ```

- Added new `_compare_with_visual_planogram()` method:
  - Converts SVG planogram to PNG using cairosvg
  - Sends both images to vision model for direct comparison
  - Falls back to text-based comparison if conversion fails

## 2. Master Orchestrator Updates

### File: `src/orchestrator/master_orchestrator.py`

**Changes Made:**
- Reads comparison configuration from the model config
- Passes comparison settings to the comparison agent:
  ```python
  comparison_config = configuration.get('comparison_config', {})
  
  comparison_result = await self.comparison_agent.compare_image_vs_planogram(
      original_image=images['enhanced'],
      planogram=planogram_result.planogram,
      structure_context=structure_context,
      model_id=comparison_config.get('model'),
      custom_prompt=comparison_config.get('prompt'),
      use_visual_comparison=comparison_config.get('use_visual_comparison', False),
      abstraction_layers=comparison_config.get('abstraction_layers', [])
  )
  ```

- Maps abstraction layers to planogram generation levels:
  - `brand` → `brand_view`
  - `product` → `product_view`
  - `confidence` → `product_view` (with confidence coloring)
  - `price_range` → `product_view` (with price info)
  - `category` → `product_view` (with category grouping)

## 3. Dependencies Added

### File: `requirements.txt`
- Added `cairosvg>=2.7.0` for SVG to PNG conversion

## 4. How It Works

### Visual Comparison Mode
When enabled, the system:
1. Converts the planogram SVG to PNG using cairosvg
2. Sends both the original photo and planogram image to the vision model
3. Uses a specialized prompt focused on visual comparison
4. Returns structured comparison results

### Text-Based Comparison Mode (Default)
When disabled or on fallback:
1. Converts planogram to text description (shelf-by-shelf listing)
2. Sends original photo + text description to vision model
3. Uses existing comparison logic

### Model Selection
- Supports GPT-4 Vision, Claude 3/4 Opus, and Gemini Pro Vision
- Falls back to GPT-4 Vision if selected model is not implemented
- Maintains backward compatibility with existing code

## 5. Integration with UI

The backend now expects the following structure from the UI in the `comparison_config` object:

```javascript
comparison_config: {
    model: 'gpt-4-vision-preview',  // Selected comparison model
    prompt: 'Custom comparison prompt...', // Custom prompt or default
    use_visual_comparison: true,  // Toggle visual mode
    abstraction_layers: [  // Enabled layers
        { id: 'confidence', label: 'Confidence Levels', enabled: true, color: '#3b82f6' },
        { id: 'brand', label: 'Brand Grouping', enabled: true, color: '#16a34a' }
    ]
}
```

## 6. Testing the Implementation

To test the new comparison configuration:

1. **Visual Comparison Mode**:
   ```bash
   # Install cairosvg if not already installed
   pip install cairosvg
   ```

2. **Different Models**:
   - Select different vision models in the UI
   - Currently only GPT-4 Vision is fully implemented
   - Other models will fall back to GPT-4 with a warning

3. **Custom Prompts**:
   - Edit the comparison prompt in the UI
   - Use placeholders: `{planogram_description}`, `{shelf_count}`, `{products_per_shelf_estimate}`

4. **Abstraction Layers**:
   - Enable different layers to change planogram generation
   - First enabled layer determines the abstraction level

## 7. Future Enhancements

1. **Implement Claude Vision API** when available
2. **Add more visual similarity metrics**:
   - SSIM (Structural Similarity Index)
   - Perceptual hashing
   - Pixel-level comparison
3. **Support multiple abstraction layers** in a single planogram
4. **Add confidence thresholds** for comparison results

## 8. Backward Compatibility

The implementation maintains full backward compatibility:
- If no comparison config is provided, uses defaults
- If visual comparison fails, falls back to text-based
- If selected model is unavailable, falls back to GPT-4 Vision