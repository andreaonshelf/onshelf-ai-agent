"""
OnShelf AI - Complete Architecture Overhaul
Main FastAPI application with progressive debugging interface
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from src.config import SystemConfig
from src.api.progressive_debugger import router as progressive_router

# Initialize FastAPI app
app = FastAPI(
    title="OnShelf AI - Progressive Debugger",
    description="Four-level orchestration system with human-in-the-loop evaluation",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(progressive_router)

# Include strategic interface
from src.api.strategic_interface import router as strategic_router
app.include_router(strategic_router)

# Serve static files (for the UI)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the progressive debugger interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OnShelf AI - Progressive Debugger</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #0a0a0a;
                color: white;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .upload-area {
                border: 2px dashed #374151;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                margin-bottom: 20px;
                background: #111827;
            }
            .upload-area:hover {
                border-color: #3b82f6;
                background: #1f2937;
            }
            .btn {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
            }
            .btn:hover {
                background: #2563eb;
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .feature {
                background: #111827;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #374151;
            }
            .feature h3 {
                color: #3b82f6;
                margin-top: 0;
            }
            .system-option {
                background: #1f2937;
                padding: 15px;
                border-radius: 8px;
                border: 2px solid #374151;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .system-option:hover {
                border-color: #3b82f6;
                background: #111827;
            }
            .system-option.selected {
                border-color: #10b981;
                background: #064e3b;
            }
            .system-option h4 {
                margin: 0 0 8px 0;
                color: #3b82f6;
            }
            .system-option p {
                margin: 0 0 8px 0;
                color: #d1d5db;
            }
            .system-option small {
                color: #9ca3af;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 OnShelf AI - Progressive Debugger</h1>
                <p>Four-level orchestration system with human-in-the-loop evaluation</p>
            </div>
            
            <div class="system-selector" style="margin-bottom: 20px;">
                <h3>🎯 Strategic System Selection</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div class="system-option" onclick="selectSystem('custom')">
                        <h4>🔧 Custom Consensus</h4>
                        <p>Direct API calls, maximum control</p>
                        <small>Best for: Cost control, fast debugging</small>
                    </div>
                    <div class="system-option" onclick="selectSystem('langgraph')">
                        <h4>🏢 LangGraph Framework</h4>
                        <p>Professional workflow management</p>
                        <small>Best for: Enterprise deployment</small>
                    </div>
                    <div class="system-option" onclick="selectSystem('hybrid')">
                        <h4>🚀 Hybrid System</h4>
                        <p>Custom logic + LangChain power</p>
                        <small>Best for: Maximum capability</small>
                    </div>
                </div>
                <div style="text-align: center;">
                    <label>
                        <input type="checkbox" id="runComparison" checked> 
                        Run Strategic Comparison (All Three Systems)
                    </label>
                </div>
            </div>
            
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <h3>📷 Upload Shelf Image</h3>
                <p>Click here or drag and drop a retail shelf image</p>
                <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="uploadFile()">
                <button class="btn">Choose File</button>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>🔄 Multiple Agent Iterations</h3>
                    <p>Compare Agent 1 vs Agent 2 vs Agent 3 results side-by-side with cumulative learning</p>
                </div>
                
                <div class="feature">
                    <h3>📊 Planogram Quality Evaluation</h3>
                    <p>Rate and provide feedback on planogram generation quality separate from extraction</p>
                </div>
                
                <div class="feature">
                    <h3>✏️ Interactive Prompt Editing</h3>
                    <p>Edit agent prompts and immediately test changes with A/B testing</p>
                </div>
                
                <div class="feature">
                    <h3>👤 Human-in-the-Loop Feedback</h3>
                    <p>Simple mode for basic evaluation, advanced mode for detailed debugging</p>
                </div>
                
                <div class="feature">
                    <h3>🎯 Progressive Disclosure</h3>
                    <p>Three interface modes: Simple, Comparison, and Advanced for different user types</p>
                </div>
                
                <div class="feature">
                    <h3>🏗️ Three-Level Abstraction</h3>
                    <p>Switch between Brand View, Product View, and SKU View planograms</p>
                </div>
                
                <div class="feature">
                    <h3>✏️ Direct Prompt Control</h3>
                    <p>Edit prompts directly, test A/B variations, and manually override AI selections</p>
                </div>
                
                <div class="feature">
                    <h3>🧪 A/B Testing Interface</h3>
                    <p>Compare prompt performance side-by-side with real-time testing capabilities</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 40px;">
                <button onclick="showPromptManager()" class="btn" style="background: #10b981;">
                    🎛️ Open Prompt Manager
                </button>
            </div>
        </div>
        
        <script>
            let selectedSystem = 'custom';
            
            function selectSystem(systemType) {
                selectedSystem = systemType;
                
                // Update visual selection
                document.querySelectorAll('.system-option').forEach(option => {
                    option.classList.remove('selected');
                });
                event.target.closest('.system-option').classList.add('selected');
                
                // Uncheck comparison mode when selecting specific system
                document.getElementById('runComparison').checked = false;
            }
            
            function showPromptManager() {
                // Create prompt manager interface
                const promptManagerHTML = `
                    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                        <div style="background: #111827; padding: 30px; border-radius: 12px; width: 90%; max-width: 1200px; max-height: 90%; overflow-y: auto;">
                            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 20px;">
                                <h2 style="margin: 0; color: #3b82f6;">🎛️ Prompt Management Center</h2>
                                <button onclick="closePromptManager()" style="background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-left: auto;">✕ Close</button>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                                <!-- Left Panel: Prompt Editor -->
                                <div style="background: #1f2937; padding: 20px; border-radius: 8px;">
                                    <h3 style="color: #10b981; margin-top: 0;">✏️ Edit Prompts</h3>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #d1d5db;">Prompt Type:</label>
                                        <select id="promptType" style="width: 100%; padding: 8px; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 4px;">
                                            <option value="structure_analysis">Structure Analysis</option>
                                            <option value="position_analysis">Position Analysis</option>
                                            <option value="quantity_analysis">Quantity Analysis</option>
                                            <option value="detail_analysis">Detail Analysis</option>
                                        </select>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #d1d5db;">Model Type:</label>
                                        <select id="modelType" style="width: 100%; padding: 8px; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 4px;">
                                            <option value="universal">Universal (All Models)</option>
                                            <option value="gpt4o">GPT-4o Specific</option>
                                            <option value="claude">Claude Specific</option>
                                            <option value="gemini">Gemini Specific</option>
                                        </select>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #d1d5db;">Prompt Content:</label>
                                        <textarea id="promptContent" rows="10" style="width: 100%; padding: 8px; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 4px; font-family: monospace;" placeholder="Enter your prompt content here..."></textarea>
                                    </div>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <label style="display: block; margin-bottom: 5px; color: #d1d5db;">Description (Optional):</label>
                                        <input type="text" id="promptDescription" style="width: 100%; padding: 8px; background: #374151; color: white; border: 1px solid #4b5563; border-radius: 4px;" placeholder="Describe your changes...">
                                    </div>
                                    
                                    <div style="display: flex; gap: 10px;">
                                        <button onclick="savePrompt()" class="btn" style="background: #10b981;">💾 Save & Activate</button>
                                        <button onclick="testPrompt()" class="btn" style="background: #3b82f6;">🧪 Test Prompt</button>
                                        <button onclick="loadCurrentPrompt()" class="btn" style="background: #6b7280;">📥 Load Current</button>
                                    </div>
                                </div>
                                
                                <!-- Right Panel: Version Management -->
                                <div style="background: #1f2937; padding: 20px; border-radius: 8px;">
                                    <h3 style="color: #10b981; margin-top: 0;">📚 Version History</h3>
                                    
                                    <div style="margin-bottom: 15px;">
                                        <button onclick="loadPromptVersions()" class="btn" style="background: #3b82f6; width: 100%;">🔄 Refresh Versions</button>
                                    </div>
                                    
                                    <div id="promptVersions" style="max-height: 400px; overflow-y: auto;">
                                        <p style="color: #9ca3af; text-align: center;">Click "Refresh Versions" to load prompt history</p>
                                    </div>
                                    
                                    <div style="margin-top: 20px;">
                                        <h4 style="color: #10b981;">🤖 AI Suggestions</h4>
                                        <div style="margin-bottom: 10px;">
                                            <button onclick="getSuggestions('performance')" class="btn" style="background: #8b5cf6; font-size: 12px;">📊 Performance Based</button>
                                            <button onclick="getSuggestions('errors')" class="btn" style="background: #ef4444; font-size: 12px;">🐛 Error Based</button>
                                            <button onclick="getSuggestions('feedback')" class="btn" style="background: #f59e0b; font-size: 12px;">💬 Feedback Based</button>
                                        </div>
                                        <div id="suggestions" style="background: #374151; padding: 10px; border-radius: 4px; min-height: 60px; color: #d1d5db; font-size: 12px;">
                                            AI suggestions will appear here...
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.insertAdjacentHTML('beforeend', promptManagerHTML);
            }
            
            function closePromptManager() {
                const modal = document.querySelector('[style*="position: fixed"]');
                if (modal) modal.remove();
            }
            
            async function savePrompt() {
                const promptType = document.getElementById('promptType').value;
                const modelType = document.getElementById('modelType').value;
                const promptContent = document.getElementById('promptContent').value;
                const description = document.getElementById('promptDescription').value;
                
                if (!promptContent.trim()) {
                    alert('Please enter prompt content');
                    return;
                }
                
                try {
                    const formData = new FormData();
                    formData.append('prompt_type', promptType);
                    formData.append('model_type', modelType);
                    formData.append('new_content', promptContent);
                    formData.append('description', description);
                    
                    const response = await fetch('/api/strategic/prompt/edit', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(`✅ Prompt saved successfully!\\nVersion: ${result.new_version}\\nActivated: ${result.activated}`);
                        loadPromptVersions(); // Refresh the version list
                    } else {
                        alert(`❌ Failed to save prompt: ${result.detail || 'Unknown error'}`);
                    }
                } catch (error) {
                    alert(`❌ Error saving prompt: ${error.message}`);
                }
            }
            
            async function testPrompt() {
                const promptType = document.getElementById('promptType').value;
                const modelType = document.getElementById('modelType').value;
                const promptContent = document.getElementById('promptContent').value;
                
                if (!promptContent.trim()) {
                    alert('Please enter prompt content to test');
                    return;
                }
                
                // For testing, we need an image - prompt user to upload one
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.onchange = async (e) => {
                    const file = e.target.files[0];
                    if (!file) return;
                    
                    try {
                        const formData = new FormData();
                        formData.append('prompt_type', promptType);
                        formData.append('model_type', modelType);
                        formData.append('prompt_content', promptContent);
                        formData.append('test_image', file);
                        
                        const response = await fetch('/api/strategic/prompt/test', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            const testResults = result.test_results;
                            alert(`🧪 Test Results:\\n` +
                                  `Accuracy: ${(testResults.accuracy * 100).toFixed(1)}%\\n` +
                                  `Confidence: ${(testResults.confidence * 100).toFixed(1)}%\\n` +
                                  `Processing Time: ${testResults.processing_time_ms}ms\\n` +
                                  `Quality: ${testResults.result_quality}\\n\\n` +
                                  `Recommendations:\\n${result.recommendations.join('\\n')}`);
                        } else {
                            alert(`❌ Test failed: ${result.detail || 'Unknown error'}`);
                        }
                    } catch (error) {
                        alert(`❌ Error testing prompt: ${error.message}`);
                    }
                };
                input.click();
            }
            
            async function loadCurrentPrompt() {
                const promptType = document.getElementById('promptType').value;
                const modelType = document.getElementById('modelType').value;
                
                try {
                    const response = await fetch(`/api/strategic/prompt/versions?prompt_type=${promptType}&model_type=${modelType}`);
                    const result = await response.json();
                    
                    if (result.versions && result.versions.length > 0) {
                        // Find the active version
                        const activeVersion = result.versions.find(v => v.is_active);
                        if (activeVersion) {
                            document.getElementById('promptContent').value = activeVersion.full_content;
                            document.getElementById('promptDescription').value = `Loaded from ${activeVersion.prompt_version}`;
                        } else {
                            alert('No active version found for this prompt type and model');
                        }
                    } else {
                        alert('No versions found for this prompt type and model');
                    }
                } catch (error) {
                    alert(`❌ Error loading prompt: ${error.message}`);
                }
            }
            
            async function loadPromptVersions() {
                const promptType = document.getElementById('promptType').value;
                const modelType = document.getElementById('modelType').value;
                
                try {
                    const response = await fetch(`/api/strategic/prompt/versions?prompt_type=${promptType}&model_type=${modelType}`);
                    const result = await response.json();
                    
                    const versionsDiv = document.getElementById('promptVersions');
                    
                    if (result.versions && result.versions.length > 0) {
                        versionsDiv.innerHTML = result.versions.map(version => `
                            <div style="background: ${version.is_active ? '#065f46' : '#374151'}; padding: 10px; margin-bottom: 10px; border-radius: 4px; border: ${version.is_active ? '2px solid #10b981' : '1px solid #4b5563'};">
                                <div style="display: flex; justify-content: between; align-items: center;">
                                    <strong style="color: ${version.is_active ? '#10b981' : '#3b82f6'};">
                                        ${version.prompt_version} ${version.is_active ? '(ACTIVE)' : ''}
                                    </strong>
                                    <small style="color: #9ca3af;">${new Date(version.created_at).toLocaleDateString()}</small>
                                </div>
                                <p style="margin: 5px 0; font-size: 12px; color: #d1d5db;">${version.prompt_content}</p>
                                <div style="font-size: 11px; color: #9ca3af;">
                                    Score: ${(version.performance_score * 100).toFixed(1)}% | 
                                    Usage: ${version.usage_count} | 
                                    Corrections: ${(version.correction_rate * 100).toFixed(1)}%
                                </div>
                                <div style="margin-top: 8px;">
                                    ${!version.is_active ? `<button onclick="activateVersion('${version.prompt_id}')" style="background: #10b981; color: white; border: none; padding: 4px 8px; border-radius: 3px; font-size: 11px; cursor: pointer;">Activate</button>` : ''}
                                    <button onclick="loadVersionContent('${version.full_content}')" style="background: #3b82f6; color: white; border: none; padding: 4px 8px; border-radius: 3px; font-size: 11px; cursor: pointer; margin-left: 5px;">Load</button>
                                </div>
                            </div>
                        `).join('');
                    } else {
                        versionsDiv.innerHTML = '<p style="color: #9ca3af; text-align: center;">No versions found</p>';
                    }
                } catch (error) {
                    document.getElementById('promptVersions').innerHTML = `<p style="color: #ef4444;">Error loading versions: ${error.message}</p>`;
                }
            }
            
            async function activateVersion(promptId) {
                try {
                    const formData = new FormData();
                    formData.append('prompt_id', promptId);
                    formData.append('reason', 'Manual activation via UI');
                    
                    const response = await fetch('/api/strategic/prompt/activate', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        alert(`✅ Prompt version activated successfully!`);
                        loadPromptVersions(); // Refresh the list
                    } else {
                        alert(`❌ Failed to activate version: ${result.detail || 'Unknown error'}`);
                    }
                } catch (error) {
                    alert(`❌ Error activating version: ${error.message}`);
                }
            }
            
            function loadVersionContent(content) {
                document.getElementById('promptContent').value = content;
                document.getElementById('promptDescription').value = 'Loaded from version history';
            }
            
            async function getSuggestions(basedOn) {
                const promptType = document.getElementById('promptType').value;
                const modelType = document.getElementById('modelType').value;
                
                try {
                    const response = await fetch(`/api/strategic/prompt/suggestions?prompt_type=${promptType}&model_type=${modelType}&based_on=${basedOn}`);
                    const result = await response.json();
                    
                    const suggestionsDiv = document.getElementById('suggestions');
                    
                    if (result.suggestions && result.suggestions.length > 0) {
                        suggestionsDiv.innerHTML = result.suggestions.map(suggestion => `
                            <div style="margin-bottom: 8px; padding: 8px; background: #4b5563; border-radius: 3px;">
                                <strong style="color: #10b981;">${suggestion.type}:</strong>
                                <p style="margin: 4px 0; font-size: 11px;">${suggestion.suggestion}</p>
                                <small style="color: #9ca3af;">Priority: ${suggestion.priority}</small>
                            </div>
                        `).join('');
                    } else {
                        suggestionsDiv.innerHTML = 'No suggestions available for this configuration.';
                    }
                } catch (error) {
                    document.getElementById('suggestions').innerHTML = `Error loading suggestions: ${error.message}`;
                }
            }
            
            async function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                const file = fileInput.files[0];
                const runComparison = document.getElementById('runComparison').checked;
                
                if (!file) return;
                
                const formData = new FormData();
                formData.append('file', file);
                
                let endpoint, processingMessage;
                
                if (runComparison) {
                    // Strategic comparison mode
                    formData.append('systems', 'custom,langgraph,hybrid');
                    endpoint = '/api/strategic/extract-comparison';
                    processingMessage = '🔄 Running strategic comparison across all three systems...';
                } else {
                    // Single system mode
                    formData.append('system_type', selectedSystem);
                    endpoint = '/api/strategic/extract-single';
                    processingMessage = `🔄 Processing with ${selectedSystem} system...`;
                }
                
                try {
                    document.body.innerHTML = `<div style="text-align: center; padding: 100px;"><h2>${processingMessage}</h2><p>This may take a few minutes</p></div>`;
                    
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        if (runComparison) {
                            displayComparisonResults(result);
                        } else {
                            displaySingleResults(result);
                        }
                    } else {
                        throw new Error(result.detail || 'Processing failed');
                    }
                } catch (error) {
                    document.body.innerHTML = `<div style="text-align: center; padding: 100px; color: #ef4444;"><h2>❌ Error</h2><p>${error.message}</p><button onclick="location.reload()" class="btn">Try Again</button></div>`;
                }
            }
            
            function displaySingleResults(result) {
                const html = `
                    <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
                        <h1>✅ ${result.system_name} Processing Complete</h1>
                        
                        <div style="background: #111827; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3>📊 Results Summary</h3>
                            <p><strong>System:</strong> ${result.system_name}</p>
                            <p><strong>Accuracy:</strong> ${(result.extraction_result.overall_accuracy * 100).toFixed(1)}%</p>
                            <p><strong>Products Found:</strong> ${result.extraction_result.products_found}</p>
                            <p><strong>Consensus Reached:</strong> ${result.extraction_result.consensus_reached ? '✅ Yes' : '❌ No'}</p>
                            <p><strong>Processing Time:</strong> ${result.processing_time.toFixed(1)}s</p>
                            <p><strong>Total Cost:</strong> $${result.cost_breakdown.total_cost.toFixed(3)}</p>
                        </div>
                        
                        <div style="background: #111827; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3>🏗️ Architecture Benefits</h3>
                            <ul>
                                ${result.architecture_benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                            </ul>
                            <p><strong>Complexity:</strong> ${result.complexity_rating} | <strong>Control Level:</strong> ${result.control_level}</p>
                        </div>
                        
                        <div style="background: #111827; padding: 20px; border-radius: 8px;">
                            <h3>📦 Extracted Products</h3>
                            <p>Found ${result.extraction_result.products_found} products across ${result.extraction_result.structure.shelf_count || 'unknown'} shelves</p>
                            <details>
                                <summary>View detailed extraction data</summary>
                                <pre style="background: #000; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px;">
${JSON.stringify(result.extraction_result, null, 2)}
                                </pre>
                            </details>
                        </div>
                        
                        <button onclick="location.reload()" class="btn" style="margin-top: 20px;">Process Another Image</button>
                    </div>
                `;
                document.body.innerHTML = html;
            }
            
            function displayComparisonResults(result) {
                const systems = Object.keys(result.system_results);
                const successfulSystems = systems.filter(s => result.system_results[s].success);
                
                const html = `
                    <div style="max-width: 1400px; margin: 0 auto; padding: 20px;">
                        <h1>🎯 Strategic System Comparison Complete</h1>
                        
                        <div style="background: #111827; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3>📊 Comparison Summary</h3>
                            <p><strong>Systems Compared:</strong> ${systems.length}</p>
                            <p><strong>Successful Systems:</strong> ${successfulSystems.length}</p>
                            ${result.comparison_summary.best_accuracy ? `<p><strong>Best Accuracy:</strong> ${result.comparison_summary.best_accuracy.system} (${(result.comparison_summary.best_accuracy.score * 100).toFixed(1)}%)</p>` : ''}
                            ${result.comparison_summary.fastest_processing ? `<p><strong>Fastest Processing:</strong> ${result.comparison_summary.fastest_processing.system} (${result.comparison_summary.fastest_processing.time.toFixed(1)}s)</p>` : ''}
                        </div>
                        
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 20px;">
                            ${systems.map(systemType => {
                                const systemResult = result.system_results[systemType];
                                if (!systemResult.success) {
                                    return `
                                        <div style="background: #7f1d1d; padding: 20px; border-radius: 8px; border: 2px solid #dc2626;">
                                            <h3>❌ ${systemResult.system_name}</h3>
                                            <p><strong>Status:</strong> Failed</p>
                                            <p><strong>Error:</strong> ${systemResult.error}</p>
                                        </div>
                                    `;
                                }
                                
                                return `
                                    <div style="background: #111827; padding: 20px; border-radius: 8px; border: 2px solid #374151;">
                                        <h3>✅ ${systemResult.system_name}</h3>
                                        <p><strong>Accuracy:</strong> ${(systemResult.accuracy * 100).toFixed(1)}%</p>
                                        <p><strong>Products Found:</strong> ${systemResult.products_found}</p>
                                        <p><strong>Processing Time:</strong> ${systemResult.processing_time.toFixed(1)}s</p>
                                        <p><strong>Total Cost:</strong> $${systemResult.total_cost.toFixed(3)}</p>
                                        <p><strong>Consensus Rate:</strong> ${(systemResult.consensus_rate * 100).toFixed(1)}%</p>
                                        
                                        <h4>🏗️ Architecture</h4>
                                        <p><strong>Complexity:</strong> ${systemResult.complexity_rating}</p>
                                        <p><strong>Control:</strong> ${systemResult.control_level}</p>
                                        
                                        <details style="margin-top: 10px;">
                                            <summary>View Benefits</summary>
                                            <ul style="margin: 10px 0;">
                                                ${systemResult.architecture_benefits.map(benefit => `<li style="font-size: 14px;">${benefit}</li>`).join('')}
                                            </ul>
                                        </details>
                                        
                                        <details style="margin-top: 10px;">
                                            <summary>View Extraction Data</summary>
                                            <pre style="background: #000; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 10px; max-height: 200px;">
${JSON.stringify(systemResult.extraction_data, null, 2)}
                                            </pre>
                                        </details>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                        
                        ${result.strategic_insights.recommendations.length > 0 ? `
                        <div style="background: #111827; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                            <h3>💡 Strategic Recommendations</h3>
                            <ul>
                                ${result.strategic_insights.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                        
                        <div style="background: #111827; padding: 20px; border-radius: 8px;">
                            <h3>🎯 Use Case Guidance</h3>
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
                                ${Object.entries(result.strategic_insights.use_case_guidance || {}).map(([useCase, recommendation]) => `
                                    <div style="background: #1f2937; padding: 15px; border-radius: 6px;">
                                        <h4 style="margin: 0 0 8px 0; color: #3b82f6;">${useCase.replace(/_/g, ' ').toUpperCase()}</h4>
                                        <p style="margin: 0; font-size: 14px;">${recommendation}</p>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                        
                        <button onclick="location.reload()" class="btn" style="margin-top: 20px;">Run Another Comparison</button>
                    </div>
                `;
                document.body.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "four_level_orchestration",
        "features": [
            "cumulative_learning",
            "planogram_abstraction",
            "human_evaluation",
            "progressive_disclosure"
        ]
    }

@app.get("/api/status")
async def api_status():
    """API status and capabilities"""
    return {
        "api_version": "2.0.0",
        "orchestration_levels": 4,
        "abstraction_levels": ["brand_view", "product_view", "sku_view"],
        "interface_modes": ["simple", "comparison", "advanced"],
        "evaluation_system": "human_in_the_loop",
        "feedback_system": "cumulative_learning"
    }

if __name__ == "__main__":
    config = SystemConfig()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 