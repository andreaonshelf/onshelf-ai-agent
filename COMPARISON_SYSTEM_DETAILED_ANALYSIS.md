# Comparison System Detailed Analysis

## Current Implementation Analysis

### 1. Comparison Model and Prompt

**Model Used**: `gpt-4-vision-preview` (HARDCODED)
- Location: `src/comparison/image_comparison_agent.py` line 93
- Not configurable through UI or model configuration
- Always uses temperature=0 for consistency

**Current Comparison Prompt**:
```python
"""
Analyze this retail shelf image and compare it to the following planogram description:

PLANOGRAM DESCRIPTION:
{planogram_description}

SHELF STRUCTURE:
- Total shelves: {structure_context.shelf_count}
- Estimated products per shelf: {structure_context.products_per_shelf_estimate}

Please identify:
1. MATCHES: Products that are correctly positioned according to the planogram
2. MISMATCHES: Products in wrong positions or incorrectly identified
3. MISSING: Products in the planogram but not visible in the image
4. EXTRA: Products visible in the image but not in the planogram

For each product, provide:
- Shelf number (counting from top)
- Position on shelf (counting from left)
- Product name/brand
- Confidence score (0-1)
- Any issues or discrepancies

Format your response as JSON with keys: matches, mismatches, missing_products, extra_products
"""
```

### 2. What Actually Happens in Steps 5-6

**Step 5: Master sends to comparison**
```python
comparison_result = await self.comparison_agent.compare_image_vs_planogram(
    original_image=images['enhanced'],  # Original shelf photo (bytes)
    planogram=planogram_result.planogram,  # VisualPlanogram object with SVG
    structure_context=structure_context  # Shelf count and dimensions
)
```

**Step 6: Current Process**
1. The planogram SVG is NOT converted to an image
2. Instead, it's converted to TEXT description:
   ```
   Shelf 1: Position 1: Coca Cola (3 facings), Position 2: Pepsi (2 facings)...
   Shelf 2: Position 1: Sprite (1 facing), Position 2: Fanta (2 facings)...
   ```
3. GPT-4 Vision sees:
   - The original shelf image (visual)
   - The planogram as text description (not visual)
4. Returns structured comparison data

### 3. Visual Similarity Metrics

**Current Status**: NO visual similarity metrics are used!
- No SSIM (Structural Similarity Index)
- No perceptual hashing
- No pixel-level comparison
- No image-to-image comparison

The system uses only:
- Count-based metrics: `matches / (matches + mismatches + missing)`
- Position-based validation from GPT-4 Vision's text response

### 4. Abstraction Levels

**Currently Implemented**:
1. **Brand View**: Groups all products by brand
   - Shows brand blocks with total facings
   - Aggregates across shelves
   
2. **Product View**: Individual products with facings
   - Shows each unique product
   - Groups multiple facings together
   
3. **SKU View**: Individual facing level
   - Shows each facing separately
   - Most detailed view

**Current Usage**: HARDCODED to "product_view" in master orchestrator

## Required UI Additions

### 1. Comparison Configuration Section
```javascript
// In Extraction Config UI
const ComparisonConfig = () => {
  return (
    <div className="comparison-config">
      <h3>Planogram Comparison Settings</h3>
      
      {/* Model Selection */}
      <label>Comparison Model:</label>
      <select value={comparisonModel} onChange={setComparisonModel}>
        <option value="gpt-4-vision-preview">GPT-4 Vision</option>
        <option value="claude-3-opus">Claude 3 Opus (Vision)</option>
        <option value="gemini-pro-vision">Gemini Pro Vision</option>
      </select>
      
      {/* Comparison Prompt */}
      <label>Comparison Prompt:</label>
      <textarea 
        value={comparisonPrompt}
        onChange={setComparisonPrompt}
        rows={15}
        placeholder="Enter the prompt for comparing image to planogram..."
      />
      
      {/* Abstraction Level */}
      <label>Planogram Abstraction Level:</label>
      <select value={abstractionLevel} onChange={setAbstractionLevel}>
        <option value="brand_view">Brand View (Grouped by Brand)</option>
        <option value="product_view">Product View (Individual Products)</option>
        <option value="sku_view">SKU View (Individual Facings)</option>
      </select>
      
      {/* Visual Comparison Toggle */}
      <label>
        <input 
          type="checkbox" 
          checked={useVisualComparison}
          onChange={setUseVisualComparison}
        />
        Use Direct Visual Comparison (Generate PNG from planogram)
      </label>
    </div>
  );
};
```

### 2. Backend Changes Needed

#### A. Make Comparison Model Configurable
```python
# In image_comparison_agent.py
async def compare_image_vs_planogram(self, 
                                   original_image: bytes,
                                   planogram: VisualPlanogram,
                                   structure_context: ShelfStructure,
                                   model_id: str = None,
                                   custom_prompt: str = None) -> ImageComparison:
    
    # Use configured model or default
    comparison_model = model_id or "gpt-4-vision-preview"
    
    # Map to actual model names
    model_mapping = {
        "gpt-4-vision-preview": "gpt-4-vision-preview",
        "claude-3-opus": "claude-3-opus-20240229",
        "gemini-pro-vision": "gemini-pro-vision"
    }
```

#### B. Add Visual Comparison Mode
```python
async def compare_with_visual_planogram(self, 
                                      original_image: bytes,
                                      planogram: VisualPlanogram) -> ImageComparison:
    # Convert SVG to PNG
    planogram_png = self._svg_to_png(planogram.svg_data)
    
    # Use image-to-image prompt
    visual_prompt = """
    Compare these two images:
    1. Original retail shelf photo
    2. Generated planogram representation
    
    The planogram is a simplified visual representation showing product positions.
    Each colored rectangle represents a product with its brand/name.
    
    Analyze:
    - Are products in the correct positions?
    - Are the right products identified?
    - What's missing or incorrect?
    
    Consider that the planogram is abstract - focus on:
    - Relative positions (left/right, shelf level)
    - Product identification accuracy
    - Facing counts
    
    Return structured comparison with confidence scores.
    """
```

#### C. Pass Configuration Through Pipeline
```python
# In master_orchestrator.py
comparison_result = await self.comparison_agent.compare_image_vs_planogram(
    original_image=images['enhanced'],
    planogram=planogram_result.planogram,
    structure_context=structure_context,
    model_id=configuration.get('comparison_model'),
    custom_prompt=configuration.get('comparison_prompt'),
    use_visual=configuration.get('use_visual_comparison', False)
)
```

## Recommended Implementation

### 1. Direct Visual Comparison Implementation
```python
import cairosvg
from PIL import Image
import io

class VisualComparisonEngine:
    def svg_to_image(self, svg_data: str, width: int = 800, height: int = 600) -> bytes:
        """Convert SVG planogram to PNG image"""
        png_data = cairosvg.svg2png(
            bytestring=svg_data.encode('utf-8'),
            output_width=width,
            output_height=height
        )
        return png_data
    
    async def compare_images(self, original: bytes, planogram: bytes, model: str) -> dict:
        """Direct image-to-image comparison"""
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": self.visual_comparison_prompt},
                {"type": "image", "image": original},
                {"type": "image", "image": planogram}
            ]
        }]
        
        # Call appropriate vision model
        return await self.call_vision_model(model, messages)
```

### 2. Default Visual Comparison Prompt
```python
DEFAULT_VISUAL_COMPARISON_PROMPT = """
You are comparing a retail shelf photo with its planogram representation.

IMAGE 1: Actual shelf photograph
IMAGE 2: Planogram (simplified visual diagram)

The planogram shows:
- Colored rectangles for products
- Text labels with product names
- Products arranged on shelf lines

Please analyze:
1. POSITION ACCURACY: Are products in the same relative positions?
2. PRODUCT IDENTIFICATION: Are the products correctly identified?
3. FACING COUNTS: Do the number of facings match?
4. MISSING/EXTRA: Any products in one image but not the other?

Important: The planogram is abstract - focus on logical arrangement, not visual appearance.

Provide structured output with:
- Overall accuracy score (0-100%)
- Per-shelf accuracy breakdown
- Specific discrepancies found
- Confidence in your assessment
"""
```

### 3. UI Configuration Storage
```javascript
// Add to model_config when processing
const processQueueItem = async (itemId) => {
  const config = {
    // Existing config...
    comparison_config: {
      model: selectedComparisonModel,
      prompt: customComparisonPrompt || DEFAULT_COMPARISON_PROMPT,
      abstraction_level: selectedAbstractionLevel,
      use_visual_comparison: useVisualComparison,
      visual_similarity_threshold: 0.85
    }
  };
  
  // Send to backend
  await api.processQueue(itemId, config);
};
```

## Summary of Findings

1. **Current State**: 
   - Comparison uses GPT-4 Vision (hardcoded)
   - Converts planogram to text, not image
   - No visual similarity metrics
   - Abstraction level fixed to "product_view"

2. **What's Missing**:
   - UI controls for comparison configuration
   - Model selection for comparison
   - Editable comparison prompts
   - Abstraction level selection
   - Direct visual comparison option

3. **Quick Wins**:
   - Add comparison prompt to UI (like other stage prompts)
   - Make comparison model selectable
   - Add abstraction level dropdown
   - Store in model_config with other settings

4. **Recommended Priority**:
   - **High**: Surface comparison prompt in UI
   - **High**: Implement visual comparison mode
   - **Medium**: Make comparison model configurable
   - **Low**: Add abstraction level controls