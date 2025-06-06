/**
 * Script to import field definitions into the UI Schema Builder
 * 
 * Usage:
 * 1. Load the dashboard in your browser
 * 2. Open the browser console
 * 3. Paste this script
 * 4. Call importFieldsForStage('structure_v1') or any other stage
 */

// Field definitions for each stage (loaded from the JSON files)
const stageFields = {
    structure_v1: {
        "name": "structure_extraction",
        "type": "object",
        "description": "Complete shelf structure analysis",
        "required": true,
        "sort_order": 0,
        "nested_fields": [/* ... full structure from ui_schema_structure_v1.json ... */]
    },
    product_v1: {
        "name": "product_extraction",
        "type": "object",
        "description": "Complete product extraction for ALL shelves in the fixture",
        "required": true,
        "sort_order": 0,
        "nested_fields": [/* ... full structure from ui_schema_product_v1.json ... */]
    },
    detail_v1: {
        "name": "detail_enhancement",
        "type": "object",
        "description": "Enhanced details for ALL products from Stage 2, maintaining exact structure",
        "required": true,
        "sort_order": 0,
        "nested_fields": [/* ... full structure from ui_schema_detail_v1.json ... */]
    },
    visual_v1: {
        "name": "visual_comparison",
        "type": "object",
        "description": "Comparison between original photo and generated planogram",
        "required": true,
        "sort_order": 0,
        "nested_fields": [/* ... full structure from ui_schema_visual_v1.json ... */]
    }
};

/**
 * Recursively create field elements in the UI Schema Builder
 */
function createFieldElement(field, parentContainer = null) {
    // If no parent container, use the main fields container
    if (!parentContainer) {
        parentContainer = document.getElementById('fields-container');
    }
    
    // Create the field element
    const fieldEl = document.createElement('div');
    fieldEl.className = 'field-item';
    fieldEl.draggable = true;
    fieldEl.dataset.fieldName = field.name;
    fieldEl.dataset.sortOrder = field.sort_order;
    
    // Create the field content
    const fieldContent = document.createElement('div');
    fieldContent.className = 'field-content';
    
    // Add drag handle
    const dragHandle = document.createElement('span');
    dragHandle.className = 'drag-handle';
    dragHandle.textContent = '☰';
    fieldContent.appendChild(dragHandle);
    
    // Add field info
    const fieldInfo = document.createElement('div');
    fieldInfo.className = 'field-info';
    fieldInfo.innerHTML = `
        <div class="field-header">
            <span class="field-name">${field.name}</span>
            <span class="field-type">(${field.type}${field.list_item_type ? ' of ' + field.list_item_type : ''})</span>
            ${field.required ? '<span class="required">*</span>' : ''}
        </div>
        <div class="field-description">${field.description || ''}</div>
    `;
    fieldContent.appendChild(fieldInfo);
    
    // Add edit button
    const editBtn = document.createElement('button');
    editBtn.className = 'edit-field-btn';
    editBtn.textContent = 'Edit';
    editBtn.onclick = () => editField(field);
    fieldContent.appendChild(editBtn);
    
    // Add delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-field-btn';
    deleteBtn.textContent = '×';
    deleteBtn.onclick = () => {
        if (confirm(`Delete field "${field.name}"?`)) {
            fieldEl.remove();
        }
    };
    fieldContent.appendChild(deleteBtn);
    
    fieldEl.appendChild(fieldContent);
    
    // If this field has nested fields, create a container for them
    if (field.nested_fields && field.nested_fields.length > 0) {
        const nestedContainer = document.createElement('div');
        nestedContainer.className = 'nested-fields';
        nestedContainer.style.marginLeft = '20px';
        
        // Sort nested fields by sort_order
        const sortedNested = [...field.nested_fields].sort((a, b) => a.sort_order - b.sort_order);
        
        // Recursively add nested fields
        sortedNested.forEach(nestedField => {
            createFieldElement(nestedField, nestedContainer);
        });
        
        fieldEl.appendChild(nestedContainer);
    }
    
    // Add the field to the parent container
    parentContainer.appendChild(fieldEl);
}

/**
 * Import fields for a specific stage
 */
async function importFieldsForStage(stageName) {
    try {
        // Check if we're in the dashboard
        const fieldsContainer = document.getElementById('fields-container');
        if (!fieldsContainer) {
            console.error('Fields container not found. Make sure you are in the dashboard.');
            return;
        }
        
        // Load the field definition for this stage
        let fieldDef;
        
        // Try to load from JSON file first
        try {
            const response = await fetch(`ui_schema_${stageName}.json`);
            fieldDef = await response.json();
        } catch (e) {
            // Fall back to hardcoded definitions
            fieldDef = stageFields[stageName];
        }
        
        if (!fieldDef) {
            console.error(`No field definition found for stage: ${stageName}`);
            return;
        }
        
        // Clear existing fields (optional - comment out if you want to append)
        if (confirm(`This will replace all existing fields with ${stageName} fields. Continue?`)) {
            fieldsContainer.innerHTML = '';
        } else {
            return;
        }
        
        // Create the root field element
        createFieldElement(fieldDef);
        
        console.log(`Successfully imported fields for ${stageName}`);
        
        // Update the stage selector if it exists
        const stageSelector = document.querySelector('select[name="stage"]');
        if (stageSelector) {
            stageSelector.value = stageName;
        }
        
    } catch (error) {
        console.error('Error importing fields:', error);
    }
}

/**
 * Edit a field (opens the edit modal)
 */
function editField(field) {
    // This would open the edit modal with the field data
    // In the actual implementation, this would integrate with the existing editFieldModal
    console.log('Edit field:', field);
    
    // If the dashboard has an edit function, call it
    if (typeof window.openEditFieldModal === 'function') {
        window.openEditFieldModal(field);
    } else {
        alert('Edit functionality not available. Field data logged to console.');
    }
}

/**
 * Export current fields to JSON
 */
function exportCurrentFields() {
    const fieldsContainer = document.getElementById('fields-container');
    if (!fieldsContainer) {
        console.error('Fields container not found');
        return;
    }
    
    const fields = [];
    const fieldElements = fieldsContainer.querySelectorAll('.field-item');
    
    fieldElements.forEach(el => {
        const field = extractFieldFromElement(el);
        if (field) {
            fields.push(field);
        }
    });
    
    const json = JSON.stringify(fields, null, 2);
    console.log('Current fields:', json);
    
    // Copy to clipboard
    navigator.clipboard.writeText(json).then(() => {
        alert('Fields exported to clipboard');
    });
    
    return fields;
}

/**
 * Extract field data from a DOM element
 */
function extractFieldFromElement(element) {
    const field = {
        name: element.dataset.fieldName,
        type: element.querySelector('.field-type')?.textContent?.replace(/[()]/g, '').trim(),
        description: element.querySelector('.field-description')?.textContent?.trim(),
        required: element.querySelector('.required') !== null,
        sort_order: parseInt(element.dataset.sortOrder || 0)
    };
    
    // Check for nested fields
    const nestedContainer = element.querySelector('.nested-fields');
    if (nestedContainer) {
        field.nested_fields = [];
        const nestedElements = nestedContainer.querySelectorAll(':scope > .field-item');
        nestedElements.forEach(nestedEl => {
            const nestedField = extractFieldFromElement(nestedEl);
            if (nestedField) {
                field.nested_fields.push(nestedField);
            }
        });
    }
    
    return field;
}

// Log available functions
console.log(`
Field Import Functions Available:
- importFieldsForStage('structure_v1') - Import Structure v1 fields
- importFieldsForStage('product_v1') - Import Product v1 fields  
- importFieldsForStage('detail_v1') - Import Detail v1 fields
- importFieldsForStage('visual_v1') - Import Visual v1 fields
- exportCurrentFields() - Export current fields to JSON
`);