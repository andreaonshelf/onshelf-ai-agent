# Interactive Planogram System - Developer Guide

## Overview

This document explains how the interactive planogram system works, including product positioning logic, grid calculations, and key learnings from development. This is essential reading for any developer working on the planogram functionality.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Product Positioning Logic](#product-positioning-logic)
3. [Grid Calculation System](#grid-calculation-system)
4. [Data Flow](#data-flow)
5. [Key Learnings & Gotchas](#key-learnings--gotchas)
6. [Debugging Guide](#debugging-guide)
7. [Future Improvements](#future-improvements)

## System Architecture

### Components Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Backend API   │    │   JSON Data      │    │   Frontend      │
│ (planogram_     │───▶│   Structure      │───▶│   Grid          │
│  editor.py)     │    │                  │    │   Renderer      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Files

- **`src/api/planogram_editor.py`**: Backend API that generates JSON planogram data
- **`main.py`**: Frontend HTML/CSS/JavaScript grid renderer (lines 4400-5000)
- **`static/components/InteractivePlanogram.js`**: React component (alternative renderer)
- **`static/css/planogram.css`**: Planogram-specific styling

## Product Positioning Logic

### Section System (Hidden from UI)

The backend organizes products into **three logical sections per shelf**:

```json
{
  "shelf_number": 1,
  "sections": {
    "Left": [products...],    // Left third of shelf
    "Center": [products...],  // Middle third of shelf  
    "Right": [products...]    // Right third of shelf
  }
}
```

**Why sections exist:**
- **AI Guidance**: Helps AI extraction identify products by shelf region
- **Spatial Organization**: Provides logical grouping for complex shelves
- **Processing Order**: Ensures consistent left-to-right product placement

**Why sections are hidden from UI:**
- **User Simplicity**: Users see one continuous shelf, not artificial divisions
- **Visual Continuity**: Products flow naturally across the entire shelf width
- **Implementation Detail**: Sections are an internal organizational tool, not a user feature

The frontend **deliberately ignores section boundaries** and renders products as one continuous grid:

```javascript
// Process sections in order but render as unified shelf
['Left', 'Center', 'Right'].forEach(sectionName => {
    // Products are placed continuously regardless of section
    section.forEach(slot => {
        // currentGridPosition increments across ALL sections
        currentGridPosition += facings;
    });
});
```

### Critical Concept: JSON Position vs Grid Position

**This is the most important concept to understand:**

```javascript
// JSON Position: Where the product starts in the original data
// Grid Position: Actual visual slots the product occupies

// Example: Pepsi Max at JSON position 4 with 3 facings
JSON Position: 4
Grid Positions: 4, 5, 6 (occupies 3 slots)
```

### Positioning Algorithm

```javascript
// 1. CUMULATIVE POSITIONING (not JSON position-based)
let currentGridPosition = 1; // Start at grid position 1

// 2. Process each section in order: Left → Center → Right
['Left', 'Center', 'Right'].forEach(sectionName => {
    section.forEach(slot => {
        if (slot.type === 'product') {
            const facings = slot.data.quantity?.columns || 1;
            
            // Place product starting at currentGridPosition
            placeProductInGrid(product, currentGridPosition);
            
            // Move to next available position
            currentGridPosition += facings;
        } else if (slot.type === 'empty') {
            // Empty slot takes 1 position
            currentGridPosition += 1;
        }
    });
});
```

### Facing Distribution

Each product with multiple facings gets **individual grid cells**:

```javascript
// Product: Coca-Cola with 3 facings at grid position 1
// Result: 3 separate cells, each showing "Coca-Cola"
Grid Cell 1: [Coca-Cola] [F1]
Grid Cell 2: [Coca-Cola] [F2] 
Grid Cell 3: [Coca-Cola] [F3]

// NOT: One cell with "3×1" label
```

### Stacking Logic

Products can stack vertically:

```javascript
// Red Bull: 2×2 (2 facings × 2 stack)
// Creates 4 total cells in a 2×2 arrangement:

Row 1: [Red Bull F1] [Red Bull F2]
Row 2: [Red Bull F1] [Red Bull F2]
```

## Grid Calculation System

### Global Width Consistency

**All shelves must have the same width** - this was a critical requirement:

```javascript
// Calculate GLOBAL dimensions across ALL shelves
let globalMaxPosition = 8; // Minimum shelf width

shelves.forEach(shelf => {
    let shelfGridPosition = 1;
    
    // Calculate cumulative positions for this shelf
    shelf.sections.forEach(section => {
        section.forEach(slot => {
            if (slot.type === 'product') {
                const facings = slot.data.quantity?.columns || 1;
                shelfGridPosition += facings;
            } else if (slot.type === 'empty') {
                shelfGridPosition += 1;
            }
        });
    });
    
    const shelfTotalSlots = shelfGridPosition - 1;
    globalMaxPosition = Math.max(globalMaxPosition, shelfTotalSlots);
});

// ALL shelves use globalMaxPosition for consistent width
```

### Individual Shelf Heights

While width is global, **each shelf calculates its own height**:

```javascript
// Calculate ACTUAL stack height for THIS shelf (not global)
let actualShelfStackHeight = 1;
shelf.sections.forEach(section => {
    section.forEach(slot => {
        if (slot.type === 'product') {
            const stackHeight = slot.data.quantity?.stack || 1;
            actualShelfStackHeight = Math.max(actualShelfStackHeight, stackHeight);
        }
    });
});
```

### Empty Slots

Empty slots are **truly transparent** - no borders, no text:

```css
.empty-cell {
    background: transparent;
    border: none;
    height: 48px;
    width: 100%;
}
```

## Data Flow

### 1. Backend Data Generation

```python
# src/api/planogram_editor.py
def get_demo_planogram_data():
    return {
        "shelves": {
            "1": {
                "shelf_number": 1,
                "sections": {
                    "Left": [
                        {
                            "type": "product",
                            "position": 1,  # JSON sequence position
                            "data": {
                                "brand": "Coca-Cola",
                                "name": "Coke Zero 330ml",
                                "quantity": {
                                    "columns": 3,  # 3 facings
                                    "stack": 1     # 1 row high
                                }
                            }
                        }
                    ]
                }
            }
        }
    }
```

### 2. Frontend Grid Creation

```javascript
// main.py - createSimpleGridPlanogram()
function createSimpleGridPlanogram(container, planogramData) {
    // 1. Calculate global dimensions
    const globalMaxPosition = calculateGlobalDimensions(shelves);
    
    // 2. Create each shelf with consistent width
    shelves.forEach(shelf => {
        const shelfDiv = createGlobalConsistentShelfGrid(
            shelf, 
            globalMaxPosition,  // Same for all shelves
            globalMaxStackHeight
        );
    });
}
```

### 3. Grid Population

```javascript
// Create 2D grid array
const grid = createGlobal2DGrid(shelf, globalMaxPosition, globalMaxStackHeight);

// Fill with products using cumulative positioning
placeProductInGlobalGrid(grid, product, currentGridPosition);

// Render visual cells
grid.forEach(row => {
    row.forEach(cell => {
        const visualCell = createGlobalGridCell(cell);
        gridContainer.appendChild(visualCell);
    });
});
```

## Key Learnings & Gotchas

### 1. Position Decoupling (CRITICAL)

**Problem**: Initially tried to use JSON `position` field directly for grid placement.

**Solution**: Decouple JSON position from grid position using cumulative calculation.

```javascript
// WRONG: Using JSON position directly
const gridCol = product.position - 1;

// RIGHT: Using cumulative positioning
let currentGridPosition = 1;
currentGridPosition += facings; // Increment by facings count
```

### 2. Global Width Consistency

**Problem**: Shelves had different widths, making the planogram look uneven.

**Solution**: Calculate maximum width across ALL shelves and apply to every shelf.

### 3. Facing Visualization

**Problem**: Showing "3×1" labels instead of actual individual facings.

**Solution**: Each facing gets its own grid cell with the same product information.

### 4. Empty Slot Handling

**Problem**: Empty slots had borders and text, making them visible.

**Solution**: Truly transparent empty cells with no visual elements.

### 5. Stacking Logic

**Problem**: Stacking was treated as a label rather than actual vertical arrangement.

**Solution**: Create proper 2D grid with stack levels as rows.

### 6. Color Mapping Consistency

**Problem**: Multiple `getConfidenceColor` functions with different thresholds.

**Solution**: Ensure frontend and backend use identical color mapping logic.

### 7. Section Abstraction Design Decision

**Design Choice**: Hide section boundaries from user interface.

**Rationale**: 
- Sections (Left/Center/Right) are an **AI extraction aid**, not a user feature
- Users expect to see shelves as continuous horizontal spaces
- Section boundaries would create artificial visual breaks
- Real retail shelves don't have visible "left/center/right" divisions

**Implementation**: 
- Backend maintains sections for AI processing consistency
- Frontend processes sections in order but renders unified grid
- No visual indicators of section boundaries
- Products flow naturally across entire shelf width

**Alternative Considered**: Show section dividers as visual separators
**Rejected Because**: Would confuse users and create unnecessary visual clutter

## Debugging Guide

### Console Logging

The system includes comprehensive logging:

```javascript
// Grid calculation debugging
console.log(`📏 Global dimensions: ${globalMaxPosition} positions × ${globalMaxStackHeight} stack`);

// Product placement debugging  
console.log(`📦 PRODUCT: ${product.brand} ${product.name}`);
console.log(`📐 Facings: ${facings} → will occupy grid slots ${currentGridPosition} to ${currentGridPosition + facings - 1}`);

// Color debugging
console.log(`🎨 Color source: ${product.visual?.confidence_color ? 'JSON visual.confidence_color' : 'calculated from confidence'} = ${confidenceColor}`);
```

### Common Issues

1. **Products not showing**: Check cumulative position calculation
2. **Wrong colors**: Verify color mapping function matches backend
3. **Uneven shelf widths**: Ensure global dimension calculation is correct
4. **Missing facings**: Check that each facing gets its own grid cell
5. **Stacking not working**: Verify 2D grid creation and stack height calculation

### Debug Commands

```javascript
// In browser console:
// 1. Check grid contents
console.log('Grid contents:', grid);

// 2. Check product data
console.log('Product data:', product);

// 3. Check global dimensions
console.log('Global dimensions:', globalMaxPosition, globalMaxStackHeight);
```

## Data Structure Reference

### Shelf Structure with Sections

```json
{
  "shelves": {
    "1": {
      "shelf_number": 1,
      "sections": {
        "Left": [
          {
            "type": "product",
            "position": 1,
            "data": { /* product data */ }
          },
          {
            "type": "empty",
            "position": 2
          }
        ],
        "Center": [
          {
            "type": "product", 
            "position": 3,
            "data": { /* product data */ }
          }
        ],
        "Right": [
          {
            "type": "product",
            "position": 4, 
            "data": { /* product data */ }
          }
        ]
      }
    }
  }
}
```

**Section Processing Order**: Always Left → Center → Right to ensure consistent positioning.

**Section Purpose**: Internal organization for AI extraction - **not visible to users**.

### Product Data Structure

```json
{
  "type": "product",
  "position": 1,
  "data": {
    "id": "coke_zero_1",
    "brand": "Coca-Cola",
    "name": "Coke Zero Sugar 330ml",
    "price": 1.29,
    "quantity": {
      "stack": 1,        // Vertical stacking (rows)
      "columns": 3,      // Horizontal facings (columns)
      "total_facings": 3 // Total units visible
    },
    "visual": {
      "confidence_color": "#22c55e"  // Demo: confidence color
    },
    "metadata": {
      "extraction_confidence": 0.94,
      "color": "black and red",      // Real: actual packaging color
      "volume": "330ml"
    }
  }
}
```

### Grid Cell Structure

```javascript
{
  type: 'product',
  product: productData,
  jsonPosition: 1,        // Original JSON position
  gridPosition: 3,        // Actual grid slot (1-based)
  stackLevel: 1,          // Which stack level (1-based)
  facingIndex: 2,         // Which facing (1-based)
  totalFacings: 3,        // Total facings for this product
  totalStack: 1,          // Total stack height for this product
  cellId: "coke-JSON1-GRID3-F2S1"  // Unique identifier
}
```

## Future Improvements

### 1. Click-to-Edit Functionality

The grid is ready for click-to-edit:

```javascript
// Already implemented click handlers
cell.addEventListener('click', () => {
    console.log('Product clicked:', product);
    // TODO: Open edit modal
});
```

### 2. Drag and Drop

Grid structure supports drag and drop:

```javascript
// TODO: Implement drag handlers
cell.addEventListener('dragstart', handleDragStart);
cell.addEventListener('drop', handleDrop);
```

### 3. Real-time Updates

Backend integration ready:

```javascript
// TODO: WebSocket integration for real-time updates
function updateProductPosition(productId, newPosition) {
    // Update grid
    // Send to backend
}
```

### 4. Gap Detection Enhancement

Current gap detection is basic:

```javascript
// TODO: Intelligent gap detection
// - Detect missing products based on expected shelf density
// - Highlight unusual gaps
// - Suggest product placement
```

## Performance Considerations

### 1. Grid Size Limits

Current system handles up to ~20 products per shelf efficiently. For larger shelves:

- Consider virtualization for 50+ products
- Implement lazy loading for off-screen cells
- Add pagination for very wide shelves

### 2. Memory Usage

Each grid cell creates DOM elements. For optimization:

- Reuse cell elements when possible
- Implement cell pooling for large grids
- Consider Canvas rendering for very large planograms

## Testing

### Unit Tests Needed

```javascript
// TODO: Add tests for:
describe('Planogram Grid System', () => {
  test('calculates global dimensions correctly', () => {});
  test('places products in correct grid positions', () => {});
  test('handles stacking properly', () => {});
  test('maintains shelf width consistency', () => {});
});
```

### Integration Tests

```javascript
// TODO: Add tests for:
describe('Planogram Integration', () => {
  test('renders complete planogram from JSON', () => {});
  test('handles empty slots correctly', () => {});
  test('applies correct colors', () => {});
});
```

---

## Quick Reference

### Key Functions

- `createSimpleGridPlanogram()`: Main entry point
- `createGlobalConsistentShelfGrid()`: Creates individual shelf
- `createGlobal2DGrid()`: Builds 2D array from JSON
- `placeProductInGlobalGrid()`: Places products using cumulative positioning
- `createGlobalGridCell()`: Renders individual cells

### Key Concepts

- **Cumulative Positioning**: Grid positions calculated by adding facings, not using JSON positions
- **Global Width**: All shelves have same width (maximum across all shelves)
- **Individual Heights**: Each shelf calculates its own height based on stacking
- **Facing Distribution**: Each facing gets its own grid cell
- **True Transparency**: Empty slots are completely invisible

### Debug Checklist

1. ✅ Global dimensions calculated correctly?
2. ✅ Cumulative positioning working?
3. ✅ Each facing has its own cell?
4. ✅ Colors match JSON data?
5. ✅ Empty slots are transparent?
6. ✅ Stacking displays properly?

---

*This README should be updated as the system evolves. Always test changes against the demo data to ensure consistency.* 