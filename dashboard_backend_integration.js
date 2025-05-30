// Backend Integration Code for OnShelf Dashboard
// Add this code to new_dashboard.html to implement proper backend saving

// 1. Replace the existing handleSaveConfiguration function with this enhanced version
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

// 2. Add function to save individual stage prompts
const handleSaveStagePrompt = async (stage) => {
    const stageConfig = stageConfigs[stage] || {
        prompt_text: promptText,
        fields: fields,
        prompt_id: selectedPrompt?.id,
        model_type: selectedModel || 'universal'
    };
    
    if (!stageConfig.prompt_text) {
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
                model_type: stageConfig.model_type,
                prompt_content: stageConfig.prompt_text,
                prompt_version: '1.0'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            
            // Update stage configuration with saved prompt ID
            const updatedConfig = {
                ...stageConfig,
                prompt_id: result.prompt_id,
                saved: true,
                savedAt: new Date().toISOString()
            };
            
            setStageConfigs({
                ...stageConfigs,
                [stage]: updatedConfig
            });
            
            // Update UI to show saved state
            updateStageStatus(stage, 'saved');
            
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

// 3. Add save button for each stage in the UI
const StageTabWithSaveButton = ({ stage, isActive, onClick }) => {
    const isSaved = stageConfigs[stage]?.saved;
    
    return (
        <div className="stage-tab-container">
            <div
                className={`stage-tab ${isActive ? 'active' : ''} ${isSaved ? 'saved' : ''}`}
                onClick={onClick}
            >
                {stage.label}
                {isSaved && <span className="saved-indicator">✓</span>}
            </div>
            {isActive && (
                <button
                    className="btn btn-sm btn-primary save-stage-btn"
                    onClick={(e) => {
                        e.stopPropagation();
                        handleSaveStagePrompt(stage.id);
                    }}
                    style={{ marginLeft: '8px' }}
                >
                    Save {stage.label}
                </button>
            )}
        </div>
    );
};

// 4. Configuration Preview Component
const ConfigurationPreview = ({ config, onClose }) => {
    if (!config) return null;
    
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content configuration-preview" onClick={(e) => e.stopPropagation()}>
                <h2>Configuration Preview</h2>
                
                <div className="config-summary">
                    <h3>Summary</h3>
                    <p><strong>Name:</strong> {config.name || 'Unnamed Configuration'}</p>
                    <p><strong>Description:</strong> {config.description || 'No description'}</p>
                    <p><strong>System:</strong> {config.system}</p>
                    <p><strong>Budget:</strong> ${config.max_budget}</p>
                    <p><strong>Stages Configured:</strong> {Object.keys(config.stages || {}).length}/4</p>
                </div>
                
                <div className="config-details">
                    <h3>Stage Details</h3>
                    {Object.entries(config.stages || {}).map(([stage, data]) => (
                        <div key={stage} className="stage-preview">
                            <h4>{stage.charAt(0).toUpperCase() + stage.slice(1)}</h4>
                            <div className="stage-info">
                                <p><strong>Model:</strong> {data.model_type || 'universal'}</p>
                                <p><strong>Fields:</strong> {data.fields?.length || 0}</p>
                                <p><strong>Saved:</strong> {data.saved ? 'Yes' : 'No'}</p>
                                <details>
                                    <summary>Prompt Preview</summary>
                                    <pre className="prompt-preview">{data.prompt_text?.substring(0, 300)}...</pre>
                                </details>
                                <details>
                                    <summary>Fields</summary>
                                    <ul>
                                        {data.fields?.map((field, idx) => (
                                            <li key={idx}>{field.name} ({field.type})</li>
                                        ))}
                                    </ul>
                                </details>
                            </div>
                        </div>
                    ))}
                </div>
                
                <div className="config-actions">
                    <button 
                        className="btn btn-primary"
                        onClick={() => exportConfiguration(config)}
                    >
                        Export Configuration
                    </button>
                    <button 
                        className="btn btn-secondary"
                        onClick={() => testConfiguration(config)}
                    >
                        Test Configuration
                    </button>
                    <button 
                        className="btn btn-secondary"
                        onClick={onClose}
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

// 5. Helper functions
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

const updateStageStatus = (stage, status) => {
    const stageTab = document.querySelector(`[data-stage="${stage}"]`);
    if (stageTab) {
        stageTab.classList.remove('pending', 'saved', 'error');
        stageTab.classList.add(status);
    }
};

const showConfigurationPreview = (config) => {
    const previewContainer = document.getElementById('configuration-preview-container');
    if (previewContainer) {
        ReactDOM.render(
            <ConfigurationPreview 
                config={config} 
                onClose={() => ReactDOM.unmountComponentAtNode(previewContainer)}
            />,
            previewContainer
        );
    }
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

const testConfiguration = async (config) => {
    // Could open a test modal or redirect to test page
    const testUrl = `/test?config=${encodeURIComponent(JSON.stringify(config))}`;
    window.open(testUrl, '_blank');
};

// 6. Load saved configurations
const loadSavedConfigurations = async () => {
    try {
        const response = await fetch(`${API_BASE}/prompts/configurations`);
        if (response.ok) {
            const data = await response.json();
            return data.configurations || [];
        }
    } catch (error) {
        console.error('Error loading configurations:', error);
    }
    return [];
};

// 7. Load a specific configuration
const loadConfiguration = async (configId) => {
    try {
        const response = await fetch(`${API_BASE}/prompts/configurations/${configId}`);
        if (response.ok) {
            const config = await response.json();
            
            // Apply configuration to UI
            setSelectedSystem(config.system);
            setMaxBudget(config.max_budget);
            
            // Load stage configurations
            Object.entries(config.stages || {}).forEach(([stage, data]) => {
                stageConfigs[stage] = data;
            });
            
            showNotification('Configuration loaded successfully!', 'success');
            
            // Update current stage display
            if (config.stages[activeStage]) {
                const stageData = config.stages[activeStage];
                setPromptText(stageData.prompt_text || '');
                setFields(stageData.fields || []);
                setSelectedPrompt(stageData.prompt_id ? { id: stageData.prompt_id } : null);
            }
        }
    } catch (error) {
        console.error('Error loading configuration:', error);
        showNotification('Error loading configuration', 'error');
    }
};

// 8. Enhanced CSS styles to add to the dashboard
const additionalStyles = `
<style>
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

/* Stage tab container */
.stage-tab-container {
    display: inline-flex;
    align-items: center;
    margin-right: 8px;
}

/* Configuration management styles */
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

.stage-info ul {
    margin: 10px 0;
    padding-left: 20px;
}
</style>
`;

// Export everything for integration
const backendIntegration = {
    handleSaveConfiguration,
    handleSaveStagePrompt,
    StageTabWithSaveButton,
    ConfigurationPreview,
    showNotification,
    updateStageStatus,
    showConfigurationPreview,
    exportConfiguration,
    testConfiguration,
    loadSavedConfigurations,
    loadConfiguration,
    additionalStyles
};

// Add this to window for easy access
window.OnShelfBackendIntegration = backendIntegration;