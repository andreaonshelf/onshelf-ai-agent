// Dashboard crash fix patch
// This patch adds proper error handling and prevents infinite loops

// 1. Fix for circular reference detection
const safeStringify = (obj) => {
    const seen = new WeakSet();
    return JSON.stringify(obj, (key, value) => {
        if (typeof value === "object" && value !== null) {
            if (seen.has(value)) {
                return "[Circular Reference]";
            }
            seen.add(value);
        }
        return value;
    });
};

// 2. Fix for safe field loading
const loadFieldsSafely = async (extractionType) => {
    try {
        // Add timeout to prevent hanging
        const timeout = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), 5000)
        );
        
        // The actual fetch - this needs to be fixed in the dashboard
        const response = await Promise.race([
            fetch(`/api/field-definitions?extraction_type=${extractionType}`),
            timeout
        ]);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Validate the data structure
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid response format');
        }
        
        // Extract fields safely
        const fields = data.definitions || data.fields || [];
        
        // Check for circular references
        try {
            safeStringify(fields);
        } catch (e) {
            throw new Error('Fields contain circular references');
        }
        
        return fields;
        
    } catch (error) {
        console.error('Error loading fields:', error);
        // Return empty array instead of crashing
        return [];
    }
};

// 3. Fix for safe field rendering
const renderFieldsSafely = (fields, level = 0, visited = new Set()) => {
    if (level > 10) {
        console.warn('Maximum nesting depth reached');
        return null;
    }
    
    return fields.map((field, index) => {
        // Create unique key for this field
        const fieldKey = `${field.name || 'unnamed'}-${index}-${level}`;
        
        // Check if we've already visited this field (circular reference)
        if (visited.has(field)) {
            console.warn('Circular reference detected in field:', field.name);
            return null;
        }
        
        // Add to visited set
        visited.add(field);
        
        // Render the field
        const rendered = (
            <div key={fieldKey}>
                {/* Field content */}
                {field.nested_fields && Array.isArray(field.nested_fields) && 
                    renderFieldsSafely(field.nested_fields, level + 1, new Set(visited))
                }
            </div>
        );
        
        // Remove from visited set
        visited.delete(field);
        
        return rendered;
    });
};

// 4. The main fix that needs to be applied to the dashboard
const dashboardFixes = {
    // Replace the existing extraction type change handler
    handleExtractionTypeChange: async function(extractionType) {
        try {
            this.setState({ loading: true, error: null });
            
            if (!extractionType) {
                this.setState({ fields: [], loading: false });
                return;
            }
            
            // Use safe loading
            const fields = await loadFieldsSafely(extractionType);
            
            // Update state safely
            this.setState({ 
                fields: fields,
                loading: false,
                selectedExtractionType: extractionType
            });
            
        } catch (error) {
            console.error('Error in extraction type change:', error);
            this.setState({ 
                error: error.message,
                fields: [],
                loading: false 
            });
        }
    },
    
    // Add error boundary
    componentDidCatch: function(error, errorInfo) {
        console.error('Component error:', error, errorInfo);
        this.setState({ 
            error: 'An error occurred while rendering. Please refresh the page.',
            fields: [] 
        });
    }
};

console.log('Dashboard fix patch loaded. Apply these fixes to prevent crashes.');