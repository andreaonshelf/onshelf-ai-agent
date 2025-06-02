// Enhanced UI Implementation for Prompt Management
// This code should be integrated into new_dashboard.html

// 1. Enhanced handleSaveConfiguration function that saves to backend
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
        name: configName || `Configuration ${new Date().toISOString()}`,
        description: configDescription || '',
        system: selectedSystem,
        max_budget: maxBudget,
        stages: {}
    };
    
    // Get saved prompts for each stage from localStorage or state
    for (const stage of stages) {
        const stageData = localStorage.getItem(`stage_${stage}_data`);
        if (stageData) {
            fullConfig.stages[stage] = JSON.parse(stageData);
        }
    }
    
    try {
        // Save configuration to backend
        const response = await fetch('/api/prompts/save-default-config', {
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
            
            // Update configuration preview
            updateConfigurationPreview(fullConfig);
        } else {
            alert('Failed to save configuration');
        }
    } catch (error) {
        console.error('Error saving configuration:', error);
        alert('Error saving configuration');
    }
};

// 2. Save individual stage prompt
const handleSaveStagePrompt = async (stage) => {
    const stageConfig = {
        prompt_id: selectedPrompt?.id,
        prompt_text: promptText,
        model_type: selectedModel || 'universal',
        fields: fields,
        schema: schemaContent
    };
    
    try {
        // Save prompt to backend
        const response = await fetch('/api/prompts/save', {
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
            
            // Save to localStorage for current session
            localStorage.setItem(`stage_${stage}_data`, JSON.stringify({
                ...stageConfig,
                prompt_id: result.prompt_id,
                saved: true,
                savedAt: new Date().toISOString()
            }));
            
            // Update UI to show saved state
            updateStageStatus(stage, 'saved');
            
            // Show success message
            showNotification(`${stage} prompt saved successfully!`, 'success');
        } else {
            showNotification('Failed to save prompt', 'error');
        }
    } catch (error) {
        console.error('Error saving prompt:', error);
        showNotification('Error saving prompt', 'error');
    }
};

// 3. Configuration Preview Component
const ConfigurationPreview = ({ config }) => {
    const [expanded, setExpanded] = useState(false);
    
    return (
        <div className="configuration-preview">
            <h3>Configuration Preview</h3>
            <div className="config-summary">
                <p><strong>Name:</strong> {config.name || 'Unnamed Configuration'}</p>
                <p><strong>System:</strong> {config.system}</p>
                <p><strong>Budget:</strong> ${config.max_budget}</p>
                <p><strong>Stages Configured:</strong> {Object.keys(config.stages || {}).length}/4</p>
            </div>
            
            <button 
                className="btn btn-secondary"
                onClick={() => setExpanded(!expanded)}
            >
                {expanded ? 'Hide Details' : 'Show Details'}
            </button>
            
            {expanded && (
                <div className="config-details">
                    {Object.entries(config.stages || {}).map(([stage, data]) => (
                        <div key={stage} className="stage-preview">
                            <h4>{stage.charAt(0).toUpperCase() + stage.slice(1)}</h4>
                            <p><strong>Model:</strong> {data.model_type}</p>
                            <p><strong>Fields:</strong> {data.fields?.length || 0}</p>
                            <details>
                                <summary>Prompt Preview</summary>
                                <pre>{data.prompt_text?.substring(0, 200)}...</pre>
                            </details>
                        </div>
                    ))}
                </div>
            )}
            
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
            </div>
        </div>
    );
};

// 4. Enhanced Interface Components
const StageConfigurationPanel = ({ stage, onSave }) => {
    const [promptText, setPromptText] = useState('');
    const [selectedPrompt, setSelectedPrompt] = useState(null);
    const [fields, setFields] = useState([]);
    const [schemaContent, setSchemaContent] = useState('');
    const [isSaved, setIsSaved] = useState(false);
    
    // Load saved data if exists
    useEffect(() => {
        const savedData = localStorage.getItem(`stage_${stage}_data`);
        if (savedData) {
            const data = JSON.parse(savedData);
            setPromptText(data.prompt_text || '');
            setSelectedPrompt(data.prompt_id ? { id: data.prompt_id } : null);
            setFields(data.fields || []);
            setSchemaContent(data.schema || '');
            setIsSaved(data.saved || false);
        }
    }, [stage]);
    
    const handleSave = async () => {
        await handleSaveStagePrompt(stage);
        setIsSaved(true);
        if (onSave) onSave(stage);
    };
    
    return (
        <div className={`stage-panel ${isSaved ? 'saved' : ''}`}>
            <div className="stage-header">
                <h3>{stage.charAt(0).toUpperCase() + stage.slice(1)} Stage</h3>
                {isSaved && <span className="saved-indicator">✓ Saved</span>}
            </div>
            
            <div className="prompt-section">
                <label>Prompt Template</label>
                <textarea
                    value={promptText}
                    onChange={(e) => setPromptText(e.target.value)}
                    rows={10}
                    placeholder="Enter your prompt template..."
                />
            </div>
            
            <div className="fields-section">
                <FieldEditor 
                    fields={fields}
                    onChange={setFields}
                />
            </div>
            
            <div className="schema-section">
                <label>Pydantic Schema</label>
                <textarea
                    value={schemaContent}
                    onChange={(e) => setSchemaContent(e.target.value)}
                    rows={8}
                    placeholder="Define your Pydantic schema..."
                />
            </div>
            
            <div className="stage-actions">
                <button 
                    className="btn btn-primary"
                    onClick={handleSave}
                >
                    Save {stage} Configuration
                </button>
                <button 
                    className="btn btn-secondary"
                    onClick={() => testStagePrompt(stage, promptText)}
                >
                    Test Prompt
                </button>
            </div>
        </div>
    );
};

// 5. Configuration Management Panel
const ConfigurationManagementPanel = () => {
    const [configurations, setConfigurations] = useState([]);
    const [selectedConfig, setSelectedConfig] = useState(null);
    const [configName, setConfigName] = useState('');
    const [configDescription, setConfigDescription] = useState('');
    
    // Load existing configurations
    useEffect(() => {
        loadConfigurations();
    }, []);
    
    const loadConfigurations = async () => {
        try {
            const response = await fetch('/api/prompts/configurations');
            if (response.ok) {
                const data = await response.json();
                setConfigurations(data.configurations || []);
            }
        } catch (error) {
            console.error('Error loading configurations:', error);
        }
    };
    
    const loadConfiguration = async (configId) => {
        try {
            const response = await fetch(`/api/prompts/configurations/${configId}`);
            if (response.ok) {
                const config = await response.json();
                
                // Load configuration into UI
                Object.entries(config.stages || {}).forEach(([stage, data]) => {
                    localStorage.setItem(`stage_${stage}_data`, JSON.stringify(data));
                });
                
                // Update UI state
                setSelectedConfig(config);
                showNotification('Configuration loaded successfully!', 'success');
                
                // Trigger UI refresh
                window.dispatchEvent(new Event('configurationLoaded'));
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            showNotification('Error loading configuration', 'error');
        }
    };
    
    return (
        <div className="configuration-management">
            <h2>Configuration Management</h2>
            
            <div className="config-form">
                <input
                    type="text"
                    placeholder="Configuration Name"
                    value={configName}
                    onChange={(e) => setConfigName(e.target.value)}
                />
                <textarea
                    placeholder="Description (optional)"
                    value={configDescription}
                    onChange={(e) => setConfigDescription(e.target.value)}
                    rows={3}
                />
            </div>
            
            <div className="saved-configurations">
                <h3>Saved Configurations</h3>
                {configurations.map(config => (
                    <div key={config.id} className="config-item">
                        <h4>{config.name}</h4>
                        <p>{config.description}</p>
                        <p>Created: {new Date(config.created_at).toLocaleDateString()}</p>
                        <button onClick={() => loadConfiguration(config.id)}>
                            Load
                        </button>
                    </div>
                ))}
            </div>
            
            {selectedConfig && (
                <ConfigurationPreview config={selectedConfig} />
            )}
        </div>
    );
};

// 6. Helper Functions
const showNotification = (message, type = 'info') => {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
};

const updateStageStatus = (stage, status) => {
    // Update visual indicator for stage
    const stageElement = document.querySelector(`[data-stage="${stage}"]`);
    if (stageElement) {
        stageElement.classList.remove('pending', 'saved', 'error');
        stageElement.classList.add(status);
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
    // Open test modal or redirect to test page
    window.location.href = `/test?config=${encodeURIComponent(JSON.stringify(config))}`;
};

const testStagePrompt = async (stage, promptText) => {
    try {
        const response = await fetch('/api/prompts/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt_content: promptText,
                test_image_id: 'sample_shelf_001'
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            // Show test results in modal
            showTestResults(result.test_results);
        }
    } catch (error) {
        console.error('Error testing prompt:', error);
        showNotification('Error testing prompt', 'error');
    }
};

const showTestResults = (results) => {
    // Create modal to show test results
    const modal = document.createElement('div');
    modal.className = 'modal test-results-modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h3>Test Results</h3>
            <div class="test-metrics">
                <p>Estimated Cost: $${results.estimated_cost}</p>
                <p>Predicted Accuracy: ${results.predicted_accuracy}%</p>
                <p>Processing Time: ${results.processing_time_estimate}s</p>
            </div>
            <div class="test-suggestions">
                <h4>Suggestions:</h4>
                <ul>
                    ${results.suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
            <button onclick="this.closest('.modal').remove()">Close</button>
        </div>
    `;
    document.body.appendChild(modal);
};

// 7. CSS Styles to add
const enhancedStyles = `
<style>
/* Configuration Preview Styles */
.configuration-preview {
    background-color: #2d2d30;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 20px;
    margin: 20px 0;
}

.config-summary {
    margin-bottom: 15px;
}

.config-details {
    margin-top: 15px;
    border-top: 1px solid #444;
    padding-top: 15px;
}

.stage-preview {
    background-color: #1e1e1e;
    padding: 10px;
    margin: 10px 0;
    border-radius: 4px;
}

/* Stage Panel Styles */
.stage-panel {
    border: 2px solid #444;
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
    transition: all 0.3s ease;
}

.stage-panel.saved {
    border-color: #10b981;
    background-color: rgba(16, 185, 129, 0.1);
}

.saved-indicator {
    color: #10b981;
    font-weight: bold;
    margin-left: 10px;
}

/* Notification Styles */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 4px;
    z-index: 10000;
    animation: slideIn 0.3s ease;
}

.notification-success {
    background-color: #10b981;
    color: white;
}

.notification-error {
    background-color: #ef4444;
    color: white;
}

.notification-info {
    background-color: #3b82f6;
    color: white;
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

/* Modal Styles */
.modal {
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

.modal-content {
    background-color: #2d2d30;
    padding: 30px;
    border-radius: 8px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
}

/* Configuration Management Styles */
.configuration-management {
    background-color: #2d2d30;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}

.config-form {
    margin-bottom: 20px;
}

.config-form input,
.config-form textarea {
    width: 100%;
    margin-bottom: 10px;
    padding: 8px;
    background-color: #1e1e1e;
    border: 1px solid #444;
    border-radius: 4px;
    color: white;
}

.saved-configurations {
    margin-top: 20px;
}

.config-item {
    background-color: #1e1e1e;
    padding: 15px;
    margin: 10px 0;
    border-radius: 4px;
    border: 1px solid #444;
}

.config-item h4 {
    margin: 0 0 10px 0;
    color: #3b82f6;
}

/* Stage Status Indicators */
[data-stage] {
    position: relative;
}

[data-stage]::before {
    content: '';
    position: absolute;
    left: -10px;
    top: 50%;
    transform: translateY(-50%);
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #666;
}

[data-stage].saved::before {
    background-color: #10b981;
}

[data-stage].error::before {
    background-color: #ef4444;
}

[data-stage].pending::before {
    background-color: #f59e0b;
}
</style>
`;

// Export for use in main application
export {
    handleSaveConfiguration,
    handleSaveStagePrompt,
    ConfigurationPreview,
    StageConfigurationPanel,
    ConfigurationManagementPanel,
    enhancedStyles
};