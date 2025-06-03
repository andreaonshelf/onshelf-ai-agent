# OnShelf AI Planogram Visualization System - Detailed Briefing

## Executive Summary

The OnShelf AI planogram visualization system transforms retail shelf photographs into structured, grid-based visual representations. This document explains EXACTLY how we visualize shelf data, which is critical for LLMs to understand what information they need to extract from images.

## Core Visualization Principles

### 1. Grid-Based Layout System

Our visualization uses a **2D grid system** where:
- **X-axis (horizontal)**: Represents product positions from left to right
- **Y-axis (vertical)**: Represents stack levels (for products stacked in depth)

```
Grid Visualization:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  1  │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  → Grid Positions
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘
```

### 2. Cumulative Positioning Algorithm

**CRITICAL CONCEPT**: We do NOT use direct position mapping. Instead, we use **cumulative positioning**.

#### How It Works:
1. Start at grid position 1
2. Place product based on its facing count
3. Increment position by the number of facings
4. Continue until all products are placed

#### Example:
```
Product Data:
- Coke Zero: 3 facings
- Sprite: 2 facings  
- Empty slot
- Pepsi: 3 facings

Grid Result:
[Coke][Coke][Coke][Sprite][Sprite][Empty][Pepsi][Pepsi][Pepsi]
  1     2     3      4       5       6      7      8      9
```

### 3. Facing Distribution Rules

**Each facing gets its own grid cell**. This is non-negotiable.

#### What We Need from LLMs:
```json
{
  "product": "Coca-Cola Zero 330ml",
  "quantity": {
    "columns": 3,    // This means 3 horizontal slots
    "total_facings": 3
  }
}
```

#### How We Visualize:
- NOT: One cell labeled "3×1"
- YES: Three separate cells, each showing the same product

### 4. Stacking Visualization

Products can be stacked vertically (representing depth on shelf).

#### What We Need from LLMs:
```json
{
  "product": "Red Bull Energy Drink",
  "quantity": {
    "columns": 2,     // 2 facings wide
    "stack": 2,       // 2 rows deep
    "total_facings": 4  // 2×2 = 4 total
  }
}
```

#### How We Visualize:
```
Row 2: [Red Bull F1] [Red Bull F2]
Row 1: [Red Bull F1] [Red Bull F2]
```

### 5. Section Organization (Hidden from Users)

Products are organized into three sections per shelf, but this is **invisible to users**.

#### What We Need from LLMs:
```json
{
  "shelf_number": 1,
  "sections": {
    "Left": [...],    // Products in left third
    "Center": [...],  // Products in middle third
    "Right": [...]    // Products in right third
  }
}
```

#### Processing Order:
Always Left → Center → Right to ensure consistent positioning.

## Detailed JSON Structure Requirements

### 1. Product Structure
```json
{
  "type": "product",
  "position": 1,  // Sequential number in section
  "data": {
    "id": "unique_product_id",
    "brand": "Coca-Cola",
    "name": "Coke Zero Sugar 330ml",
    "price": 1.29,
    "quantity": {
      "columns": 3,      // CRITICAL: Number of horizontal slots
      "stack": 1,        // CRITICAL: Number of vertical rows
      "total_facings": 3 // Must equal columns × stack
    },
    "position": {
      "shelf_level": 1,      // 1 = bottom shelf
      "position_on_shelf": 1, // Sequential position
      "section": {
        "vertical": "Left"   // Left/Center/Right
      }
    },
    "visual": {
      "confidence_color": "#22c55e"  // Pre-calculated color
    },
    "metadata": {
      "extraction_confidence": 0.98,
      "color": "black and red",      // Actual package color
      "volume": "330ml"
    }
  }
}
```

### 2. Empty Slot Structure
```json
{
  "type": "empty",
  "position": 6,
  "reason": "gap_detected"
}
```

### 3. Complete Shelf Structure
```json
{
  "shelves": {
    "1": {
      "shelf_number": 1,
      "sections": {
        "Left": [
          // Products with positions 1, 2, 3...
        ],
        "Center": [
          // Products with positions 4, 5, 6...
        ],
        "Right": [
          // Products with positions 7, 8, 9...
        ]
      },
      "total_positions": 9,
      "product_count": 7,
      "empty_count": 2
    }
  }
}
```

## Visualization Rules

### 1. Global Width Consistency
- All shelves MUST have the same width
- Width = maximum positions across all shelves
- Minimum width = 8 grid positions

### 2. Color Coding by Confidence
```
≥95% confidence: #22c55e (Green)
≥85% confidence: #3b82f6 (Blue)  
≥70% confidence: #f59e0b (Orange)
<70% confidence: #ef4444 (Red)
```

### 3. Standard Dimensions
- Shelf width: 250cm default
- Product width: 8cm per facing
- Gap width: 2cm between products
- Shelf height: 30cm

### 4. Empty Slot Handling
- Completely transparent (no borders)
- Takes exactly 1 grid position
- No visual elements

## Critical Information for LLM Extraction

### What We MUST Have:

1. **Exact Facing Count**
   - Count side-by-side product units
   - Each facing = one grid cell
   - Never combine facings into one cell

2. **Stack Information**
   - Count vertical/depth arrangements
   - Stack of 2 = product goes 2 deep
   - Affects cell height, not width

3. **Sequential Positioning**
   - Products numbered sequentially within sections
   - Gaps create empty slots
   - Position numbers can have gaps

4. **Section Assignment**
   - Assign products to Left/Center/Right
   - Based on physical shelf location
   - Critical for processing order

### Common Extraction Patterns:

1. **Multiple Facings**:
   ```
   Observation: "Coca-Cola takes up significant space"
   Extraction: columns: 3 (not "large" or "multiple")
   ```

2. **Stacked Products**:
   ```
   Observation: "Red Bull cans are stacked 2 deep"
   Extraction: stack: 2, columns: 2
   ```

3. **Gaps**:
   ```
   Observation: "Empty space between products"
   Extraction: {"type": "empty", "position": X}
   ```

## Visualization Example

### Input JSON:
```json
{
  "shelf_number": 1,
  "sections": {
    "Left": [
      {"type": "product", "position": 1, "data": {"name": "Coke Zero", "quantity": {"columns": 3}}},
      {"type": "product", "position": 2, "data": {"name": "Sprite", "quantity": {"columns": 2}}}
    ],
    "Center": [
      {"type": "empty", "position": 3},
      {"type": "product", "position": 4, "data": {"name": "Pepsi Max", "quantity": {"columns": 3}}}
    ]
  }
}
```

### Resulting Grid:
```
┌──────┬──────┬──────┬───────┬───────┬───────┬──────┬──────┬──────┐
│ Coke │ Coke │ Coke │Sprite │Sprite │ Empty │Pepsi │Pepsi │Pepsi │
│ Zero │ Zero │ Zero │       │       │       │ Max  │ Max  │ Max  │
│  F1  │  F2  │  F3  │  F1   │  F2   │       │  F1  │  F2  │  F3  │
└──────┴──────┴──────┴───────┴───────┴───────┴──────┴──────┴──────┘
Grid:  1      2      3      4       5       6      7      8      9
```

## Key Takeaways for LLM Prompting

1. **Be Specific with Numbers**
   - Not "multiple facings" → Exact number: "columns": 3
   - Not "stacked" → Exact stack count: "stack": 2

2. **Maintain Sequential Order**
   - Process left to right
   - Number positions sequentially
   - Include empty slots in sequence

3. **Understand Grid Impact**
   - 3 facings = 3 grid cells
   - 2×2 stacking = 4 total cells in 2×2 arrangement
   - Empty = 1 grid cell

4. **Section Assignment Matters**
   - Affects processing order
   - Ensures consistent layout
   - Hidden from final visualization

## Conclusion

This visualization system requires precise, structured data from LLMs. The grid-based approach with cumulative positioning ensures accurate representation of retail shelves. By understanding these exact requirements, LLMs can provide the detailed JSON structure needed for accurate planogram generation.

Remember: **Every facing gets its own cell, positions are cumulative, and precision in the data structure directly translates to accuracy in visualization.**