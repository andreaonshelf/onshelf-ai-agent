# Dashboard Backend Integration Patch

This document shows how to integrate the backend saving functionality into `new_dashboard.html`.

## 1. Add the Configuration Preview Container

Add this right after the main app container in your HTML:

```html
<!-- Add this after <div id="app"></div> -->
<div id="configuration-preview-container"></div>
```

## 2. Replace the handleSaveConfiguration Function

Find the existing `handleSaveConfiguration` function (around line 1225) and replace it with:

```javascript
const handleSaveConfiguration = async () => {
    // Validate schema first
    const isValid = await validateSchema();
    if (!isValid) {
        alert('Schema validation failed. Please check your field definitions.');
        return;
    }
    
    // Collect all stage configurations
    const stages = ['structure', 'products', 'details', 'validation'];
    const fullConfig = {
        name: prompt('Enter configuration name:') || `Config ${new Date().toISOString()}`,
        description: prompt('Enter configuration description (optional):') || '',
        system: selectedSystem,
        max_budget: maxBudget,
        stages: {}
    };
    
    // Get configurations for all stages
    for (const stage of stages) {
        const stageData = stageConfigs[stage];
        if (stageData) {
            fullConfig.stages[stage] = stageData;
        }
    }
    
    try {
        // Save configuration to backend
        const response = await fetch(`${API_BASE}/prompts/save-default-config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                configuration: fullConfig,
                name: fullConfig.name,
                description: fullConfig.description
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Configuration saved successfully!');
            localStorage.setItem('extraction_config', JSON.stringify(fullConfig));
            
            // Show configuration preview
            showConfigurationPreview(fullConfig);
        } else {
            const error = await response.json();
            alert('Failed to save configuration: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        alert('Error saving configuration: ' + error.message);
    }
};
```

## 3. Add the Save Stage Prompt Function

Add this function after the handleSaveConfiguration function:

```javascript
const handleSaveStagePrompt = async (stage) => {
    const currentConfig = {
        prompt_text: promptText,
        fields: fields,
        prompt_id: selectedPrompt?.id,
        model_type: selectedModel || 'universal'
    };
    
    if (!currentConfig.prompt_text) {
        alert('Please enter prompt text before saving');
        return;
    }
    
    try {
        // Save prompt to backend
        const response = await fetch(`${API_BASE}/prompts/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt_type: stage,
                model_type: currentConfig.model_type,
                prompt_content: currentConfig.prompt_text,
                prompt_version: '1.0'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Update stage configuration with saved prompt ID
            const updatedConfig = {
                ...currentConfig,
                prompt_id: result.prompt_id,
                saved: true,
                savedAt: new Date().toISOString()
            };
            
            setStageConfigs({
                ...stageConfigs,
                [stage]: updatedConfig
            });
            
            // Show success notification
            showNotification(`${stage} prompt saved successfully!`, 'success');
        } else {
            const error = await response.json();
            showNotification('Failed to save prompt: ' + (error.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Error saving prompt:', error);
        showNotification('Error saving prompt: ' + error.message, 'error');
    }
};
```

## 4. Update the Stage Tabs

Replace the stage tab rendering (around line 1378) with:

```javascript
{stages.map((stage, index) => (
    <div 
        key={stage.id} 
        style={{ 
            position: 'relative', 
            display: 'inline-flex',
            alignItems: 'center',
            opacity: draggedStage === index ? '0.5' : '1',
            transform: dragOverIndex === index ? 'translateX(5px)' : 'translateX(0)',
            transition: 'transform 0.2s'
        }}
        draggable
        onDragStart={(e) => handleDragStart(e, index)}
        onDragOver={(e) => handleDragOver(e, index)}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(e, index)}
        onDragEnd={handleDragEnd}
    >
        <div
            className={`stage-tab ${activeStage === stage.id ? 'active' : ''} ${stageConfigs[stage.id]?.saved ? 'saved' : ''}`}
            onClick={() => setActiveStage(stage.id)}
            data-stage={stage.id}
            style={{ 
                paddingRight: stage.removable ? '30px' : '16px',
                cursor: 'move',
                userSelect: 'none'
            }}
        >
            <span style={{ marginRight: '6px', opacity: '0.5', fontSize: '12px' }}>⋮⋮</span>
            {stage.label}
            {stageConfigs[stage.id]?.saved && <span className="saved-indicator">✓</span>}
        </div>
        {activeStage === stage.id && (
            <button
                className="save-stage-btn"
                onClick={(e) => {
                    e.stopPropagation();
                    handleSaveStagePrompt(stage.id);
                }}
                style={{ marginLeft: '8px' }}
            >
                Save {stage.label}
            </button>
        )}
        {stage.removable && (
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    if (confirm(`Remove stage "${stage.label}"?`)) {
                        handleRemoveStage(stage.id);
                    }
                }}
                style={{
                    position: 'absolute',
                    right: '4px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: '#94a3b8',
                    border: 'none',
                    color: 'white',
                    cursor: 'pointer',
                    padding: '2px 6px',
                    fontSize: '14px',
                    borderRadius: '3px',
                    lineHeight: '1',
                    fontWeight: 'bold',
                    height: '20px',
                    width: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    opacity: '0.7',
                    transition: 'opacity 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.opacity = '1'}
                onMouseLeave={(e) => e.target.style.opacity = '0.7'}
                title="Remove stage"
            >
                ×
            </button>
        )}
    </div>
))}
```

## 5. Add Helper Functions

Add these helper functions before the ConfigPage component:

```javascript
const showNotification = (message, type = 'info') => {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 4px;
        z-index: 10000;
        animation: slideIn 0.3s ease;
        background-color: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
};

const showConfigurationPreview = (config) => {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="configuration-preview">
            <h2>Configuration Preview</h2>
            
            <div class="config-summary">
                <h3>Summary</h3>
                <p><strong>Name:</strong> ${config.name || 'Unnamed Configuration'}</p>
                <p><strong>Description:</strong> ${config.description || 'No description'}</p>
                <p><strong>System:</strong> ${config.system}</p>
                <p><strong>Budget:</strong> $${config.max_budget}</p>
                <p><strong>Stages Configured:</strong> ${Object.keys(config.stages || {}).length}/4</p>
            </div>
            
            <div class="config-details">
                <h3>Stage Details</h3>
                ${Object.entries(config.stages || {}).map(([stage, data]) => `
                    <div class="stage-preview">
                        <h4>${stage.charAt(0).toUpperCase() + stage.slice(1)}</h4>
                        <div class="stage-info">
                            <p><strong>Model:</strong> ${data.model_type || 'universal'}</p>
                            <p><strong>Fields:</strong> ${data.fields?.length || 0}</p>
                            <p><strong>Saved:</strong> ${data.saved ? 'Yes' : 'No'}</p>
                            <details>
                                <summary>Prompt Preview</summary>
                                <pre class="prompt-preview">${data.prompt_text?.substring(0, 300)}...</pre>
                            </details>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div class="config-actions">
                <button class="btn btn-primary" onclick="exportConfiguration(${JSON.stringify(config).replace(/"/g, '&quot;')})">
                    Export Configuration
                </button>
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                    Close
                </button>
            </div>
        </div>
    `;
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    document.body.appendChild(modal);
};

const exportConfiguration = (config) => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `onshelf-config-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
};
```

## 6. Add the Additional Styles

Add these styles to your existing `<style>` section:

```css
/* Save button styles */
.save-stage-btn {
    padding: 4px 12px;
    font-size: 13px;
    background-color: #3b82f6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
}

.save-stage-btn:hover {
    background-color: #2563eb;
}

/* Saved indicator */
.saved-indicator {
    color: #10b981;
    font-weight: bold;
    margin-left: 6px;
}

.stage-tab.saved {
    border-color: #10b981;
    background-color: rgba(16, 185, 129, 0.1);
}

/* Configuration preview modal */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.configuration-preview {
    background-color: white;
    padding: 30px;
    border-radius: 8px;
    max-width: 800px;
    max-height: 80vh;
    overflow-y: auto;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.config-summary {
    background-color: #f8fafc;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 20px;
}

.stage-preview {
    background-color: #f8fafc;
    padding: 15px;
    margin: 10px 0;
    border-radius: 6px;
    border: 1px solid #e2e8f0;
}

.stage-preview h4 {
    margin: 0 0 10px 0;
    color: #3b82f6;
}

.prompt-preview {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Notification styles */
.notification {
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.config-actions {
    display: flex;
    gap: 10px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e2e8f0;
}

.stage-info {
    font-size: 14px;
    color: #64748b;
}

.stage-info details {
    margin-top: 10px;
}

.stage-info summary {
    cursor: pointer;
    font-weight: 500;
    color: #334155;
}
```

## 7. Update the Save Configuration Button

Update the save configuration button to also show a "View Last Config" option:

```javascript
<div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
    <button className="btn btn-primary" onClick={handleSaveConfiguration}>
        Save Configuration
    </button>
    <button className="btn btn-secondary" onClick={() => {
        const savedConfig = localStorage.getItem('extraction_config');
        if (savedConfig) {
            showConfigurationPreview(JSON.parse(savedConfig));
        } else {
            alert('No saved configuration found');
        }
    }}>
        View Last Config
    </button>
    <button className="btn btn-secondary">
        Load Previous Config
    </button>
</div>
```

## 8. Initialize stageConfigs State

Make sure to add `stageConfigs` to your state initialization:

```javascript
const [stageConfigs, setStageConfigs] = useState({});
```

## Testing the Integration

1. **Test Stage Saving**: Click on each stage tab and configure the prompt. Click "Save [Stage Name]" to save individually.

2. **Test Configuration Saving**: After configuring all stages, click "Save Configuration". You'll be prompted for a name and description.

3. **Test Configuration Preview**: After saving, a preview modal will show all your configured stages.

4. **Test Export**: From the preview modal, click "Export Configuration" to download as JSON.

5. **Verify Backend Storage**: Check your database to ensure prompts are being saved to the `meta_prompts` table.

## Troubleshooting

If you encounter issues:

1. Check the browser console for errors
2. Verify the API endpoints are accessible
3. Ensure your Supabase connection is configured
4. Check that the `meta_prompts` table exists in your database

## Next Steps

1. Implement configuration loading from the database
2. Add version history for prompts
3. Implement A/B testing for different configurations
4. Add performance tracking for saved configurations