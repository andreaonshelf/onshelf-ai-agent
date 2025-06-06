# Dashboard Crash Fix for Product v1 Selection

## Problem Summary

The dashboard crashes when selecting "Product v1" from the dropdown. This is likely caused by:

1. **Missing API endpoint**: The dashboard tries to fetch field definitions from an endpoint that doesn't exist
2. **Circular references**: The field data structure might contain circular references
3. **Infinite render loop**: React might be getting stuck in an infinite render loop

## Root Causes Identified

1. **API Mismatch**: The field_definitions API expects different parameters than what the UI is sending
2. **Data Structure Issues**: The field definitions table doesn't have an `extraction_type` column
3. **Missing Error Handling**: The dashboard doesn't handle API errors gracefully

## Solutions

### 1. Fix the API Call

The dashboard should use the correct API endpoint:
```javascript
// Instead of: /api/field_definitions/product_v1
// Use: /api/field-definitions?category=product
```

### 2. Add Error Boundaries

Wrap the field rendering in an error boundary to prevent crashes:
```javascript
class FieldErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    
    static getDerivedStateFromError(error) {
        return { hasError: true };
    }
    
    componentDidCatch(error, errorInfo) {
        console.error('Field rendering error:', error, errorInfo);
    }
    
    render() {
        if (this.state.hasError) {
            return <div>Error loading fields. Please try again.</div>;
        }
        return this.props.children;
    }
}
```

### 3. Safe Field Loading Function

```javascript
const loadFieldsSafely = async (extractionType) => {
    try {
        // Map extraction types to categories
        const typeToCategory = {
            'product_v1': 'product',
            'shelf_v1': 'shelf',
            'price_v1': 'price'
        };
        
        const category = typeToCategory[extractionType] || extractionType;
        
        // Use the correct API endpoint
        const response = await fetch(`/api/field-definitions?organized=true`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Extract fields for the specific category
        if (data.categories) {
            const categoryData = data.categories.find(c => c.name === category);
            return categoryData ? categoryData.fields : [];
        }
        
        return data.definitions || [];
        
    } catch (error) {
        console.error('Error loading fields:', error);
        return [];
    }
};
```

### 4. Prevent Circular References

```javascript
const sanitizeFields = (fields, visited = new WeakSet()) => {
    return fields.map(field => {
        if (visited.has(field)) {
            return { ...field, nested_fields: [] };
        }
        
        visited.add(field);
        
        const sanitized = { ...field };
        if (sanitized.nested_fields && Array.isArray(sanitized.nested_fields)) {
            sanitized.nested_fields = sanitizeFields(sanitized.nested_fields, visited);
        }
        
        return sanitized;
    });
};
```

### 5. Update the Dashboard Component

The main fix needed in the dashboard:

```javascript
// In the extraction type change handler
const handleExtractionTypeChange = async (newType) => {
    try {
        setLoading(true);
        setError(null);
        
        const fields = await loadFieldsSafely(newType);
        const sanitized = sanitizeFields(fields);
        
        setFields(sanitized);
        setSelectedExtractionType(newType);
        
    } catch (error) {
        console.error('Error changing extraction type:', error);
        setError('Failed to load fields. Please try again.');
        setFields([]);
    } finally {
        setLoading(false);
    }
};
```

## Quick Fix

If you need an immediate fix without modifying the entire dashboard, add this script before the dashboard loads:

```javascript
// Override fetch to intercept problematic API calls
const originalFetch = window.fetch;
window.fetch = async (url, ...args) => {
    // Intercept field_definitions calls
    if (url.includes('/api/field_definitions/')) {
        const extractionType = url.split('/').pop();
        // Redirect to the correct endpoint
        return originalFetch(`/api/field-definitions?organized=true`, ...args);
    }
    return originalFetch(url, ...args);
};
```

## Testing

1. Open the dashboard
2. Select "Product v1" from the dropdown
3. Verify that fields load without crashing
4. Check browser console for any errors

## Long-term Solution

1. Update the field_definitions table to include an extraction_type column
2. Create proper API endpoints for each extraction type
3. Add comprehensive error handling throughout the dashboard
4. Implement proper loading states and error messages