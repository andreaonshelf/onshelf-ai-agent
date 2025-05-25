"""
OnShelf AI - Queue Review Dashboard
Main FastAPI application with progressive debugging interface for reviewing extraction results
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os

from src.config import SystemConfig

# Initialize FastAPI app
app = FastAPI(
    title="OnShelf AI - Queue Review Dashboard",
    description="Review and analysis tool for extraction results with progressive disclosure",
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
from src.api.progressive_debugger import router as progressive_router
app.include_router(progressive_router)

# Include strategic interface
from src.api.strategic_interface import router as strategic_router
app.include_router(strategic_router)

# Include planogram rendering
from src.api.planogram_renderer import router as planogram_router
app.include_router(planogram_router)

# Include queue management API
from src.api.queue_management import router as queue_router
app.include_router(queue_router)

# Serve static files (for the UI)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Main dashboard interface with progressive disclosure"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OnShelf AI - Extraction Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8fafc;
                color: #1e293b;
                line-height: 1.6;
            }
            
            /* Layout Structure */
            .app-container {
                display: flex;
                height: 100vh;
                overflow: hidden;
            }
            
            /* Left Sidebar - Image Selection */
            .left-sidebar {
                width: 400px;
                background: white;
                border-right: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                transition: transform 0.3s ease;
                z-index: 100;
            }
            
            .left-sidebar.collapsed {
                transform: translateX(-380px);
                width: 20px;
            }
            
            .sidebar-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                background: #f8fafc;
            }
            
            .sidebar-toggle {
                position: absolute;
                right: -20px;
                top: 20px;
                width: 20px;
                height: 40px;
                background: #3b82f6;
                color: white;
                border: none;
                cursor: pointer;
                border-radius: 0 4px 4px 0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
            }
            
            .filters-section {
                padding: 15px 20px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .filter-group {
                margin-bottom: 15px;
            }
            
            .filter-group label {
                display: block;
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                margin-bottom: 5px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .filter-group select,
            .filter-group input {
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            
            .search-box {
                position: relative;
            }
            
            .search-box input {
                padding-left: 35px;
            }
            
            .search-box::before {
                content: "🔍";
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                font-size: 14px;
            }
            
            .view-toggle {
                display: flex;
                gap: 5px;
                margin-top: 10px;
            }
            
            .view-toggle button {
                flex: 1;
                padding: 6px 12px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 4px;
                font-size: 12px;
                cursor: pointer;
            }
            
            .view-toggle button.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            .images-container {
                flex: 1;
                overflow-y: auto;
                padding: 10px;
            }
            
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 10px;
            }
            
            .image-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .image-item {
                border: 2px solid transparent;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.2s ease;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .image-item:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .image-item.selected {
                border-color: #10b981;
                background: #f0fdf4;
            }
            
            .image-item.grid-view {
                aspect-ratio: 1;
            }
            
            .image-item.list-view {
                display: flex;
                padding: 8px;
                align-items: center;
                gap: 10px;
            }
            
            .image-thumbnail {
                width: 100%;
                height: 100%;
                object-fit: cover;
                background: #f1f5f9;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
            }
            
            .image-item.list-view .image-thumbnail {
                width: 60px;
                height: 60px;
                border-radius: 4px;
                flex-shrink: 0;
            }
            
            .image-info {
                padding: 8px;
                font-size: 12px;
            }
            
            .image-item.list-view .image-info {
                padding: 0;
                flex: 1;
            }
            
            .image-title {
                font-weight: 600;
                margin-bottom: 2px;
                color: #1e293b;
            }
            
            .image-meta {
                color: #64748b;
                font-size: 11px;
            }
            
            .status-badge {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-top: 4px;
            }
            
            .status-pending { background: #fef3c7; color: #92400e; }
            .status-processing { background: #dbeafe; color: #1e40af; }
            .status-completed { background: #d1fae5; color: #065f46; }
            .status-failed { background: #fee2e2; color: #991b1b; }
            .status-review { background: #fde68a; color: #92400e; }
            
            .pagination {
                padding: 15px 20px;
                border-top: 1px solid #e2e8f0;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: #64748b;
            }
            
            .pagination-controls {
                display: flex;
                gap: 5px;
            }
            
            .pagination-controls button {
                padding: 4px 8px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .pagination-controls button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .pagination-controls button.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            /* Main Content Area */
            .main-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            /* Header */
            .header {
                background: white;
                border-bottom: 1px solid #e2e8f0;
                padding: 20px 30px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .header h1 {
                font-size: 24px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .mode-selector {
                display: flex;
                gap: 10px;
            }
            
            .mode-btn {
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                background: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
            }
            
            .mode-btn:hover {
                background: #f8fafc;
                border-color: #3b82f6;
            }
            
            .mode-btn.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
            }
            
            /* Breadcrumb */
            .breadcrumb {
                padding: 15px 30px;
                background: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                font-size: 14px;
                color: #64748b;
            }
            
            /* Content Area */
            .content-area {
                flex: 1;
                overflow: hidden;
                position: relative;
            }
            
            /* Queue Interface */
            .queue-interface {
                padding: 30px;
                height: 100%;
                overflow-y: auto;
            }
            
            .queue-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border-left: 4px solid #3b82f6;
            }
            
            .stat-card.review { border-left-color: #f59e0b; }
            .stat-card.processing { border-left-color: #3b82f6; }
            .stat-card.completed { border-left-color: #10b981; }
            .stat-card.failed { border-left-color: #ef4444; }
            
            .stat-number {
                font-size: 32px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .stat-label {
                font-size: 14px;
                color: #64748b;
                margin-top: 5px;
            }
            
            .queue-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
            }
            
            .queue-item {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 2px solid transparent;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .queue-item:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            
            .queue-item.selected {
                border-color: #10b981;
                background: #f0fdf4;
            }
            
            .queue-item.priority {
                border-left: 4px solid #f59e0b;
            }
            
            .item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            
            .item-title {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
            }
            
            .item-status {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .item-meta {
                font-size: 14px;
                color: #64748b;
                margin-bottom: 15px;
                line-height: 1.5;
            }
            
            .item-accuracy {
                margin: 15px 0;
            }
            
            .accuracy-bar {
                width: 100%;
                height: 8px;
                background: #e2e8f0;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 5px;
            }
            
            .accuracy-fill {
                height: 100%;
                background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
                transition: width 0.3s ease;
            }
            
            .accuracy-text {
                font-size: 12px;
                font-weight: 600;
                color: #1e293b;
            }
            
            .system-selection {
                margin: 15px 0;
                padding: 15px;
                background: #f8fafc;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
            }
            
            .system-label {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .system-checkboxes {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .system-checkbox {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .system-checkbox input[type="checkbox"] {
                width: 16px;
                height: 16px;
            }
            
            .system-checkbox label {
                font-size: 14px;
                font-weight: 500;
                color: #1e293b;
                cursor: pointer;
            }
            
            .system-description {
                font-size: 12px;
                color: #64748b;
                margin-left: 24px;
                margin-top: -4px;
            }
            
            .item-actions {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            .btn {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                justify-content: center;
            }
            
            .btn-primary {
                background: #3b82f6;
                color: white;
            }
            
            .btn-primary:hover {
                background: #2563eb;
            }
            
            .btn-success {
                background: #10b981;
                color: white;
            }
            
            .btn-success:hover {
                background: #059669;
            }
            
            .btn-secondary {
                background: #6b7280;
                color: white;
            }
            
            .btn-secondary:hover {
                background: #4b5563;
            }
            
            .btn-warning {
                background: #f59e0b;
                color: white;
            }
            
            .btn-warning:hover {
                background: #d97706;
            }
            
            /* Simple Mode - 2 Panel Layout */
            .simple-mode {
                display: none;
                height: 100%;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                padding: 20px;
            }
            
            .simple-mode.active {
                display: grid;
            }
            
            .image-panel,
            .planogram-panel {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .panel-header {
                padding: 20px;
                border-bottom: 1px solid #e2e8f0;
                background: #f8fafc;
            }
            
            .panel-header h3 {
                font-size: 18px;
                font-weight: 600;
                color: #1e293b;
                margin: 0;
            }
            
            .panel-content {
                flex: 1;
                padding: 20px;
                overflow: auto;
            }
            
            .image-viewer {
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f8fafc;
                border-radius: 6px;
                overflow: hidden;
                position: relative;
            }
            
            .image-viewer img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                transition: transform 0.3s ease;
            }
            
            .image-controls {
                position: absolute;
                bottom: 10px;
                right: 10px;
                display: flex;
                gap: 5px;
                background: rgba(0,0,0,0.7);
                border-radius: 6px;
                padding: 5px;
            }
            
            .control-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            
            .control-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .rating-system {
                margin-top: 20px;
                padding: 20px;
                background: #f8fafc;
                border-radius: 6px;
            }
            
            .rating-system h4 {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 10px;
            }
            
            .star-rating {
                display: flex;
                gap: 5px;
                margin-bottom: 15px;
            }
            
            .star {
                font-size: 24px;
                color: #d1d5db;
                cursor: pointer;
                transition: color 0.2s ease;
            }
            
            .star:hover,
            .star.active {
                color: #fbbf24;
            }
            
            .feedback-area {
                margin-top: 15px;
            }
            
            .feedback-area label {
                display: block;
                font-size: 14px;
                font-weight: 500;
                color: #374151;
                margin-bottom: 5px;
            }
            
            .feedback-area textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                resize: vertical;
                min-height: 80px;
            }
            
            /* Comparison Mode */
            .comparison-mode {
                display: none;
                height: 100%;
                padding: 20px;
                overflow-y: auto;
            }
            
            .comparison-mode.active {
                display: block;
            }
            
            .agent-tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .agent-tab {
                padding: 12px 20px;
                border: none;
                background: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                color: #64748b;
                border-bottom: 2px solid transparent;
                transition: all 0.2s ease;
            }
            
            .agent-tab:hover {
                color: #3b82f6;
            }
            
            .agent-tab.active {
                color: #3b82f6;
                border-bottom-color: #3b82f6;
            }
            
            .agent-content {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                padding: 20px;
            }
            
            .agent-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background: #f8fafc;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
            }
            
            .metric-value {
                font-size: 24px;
                font-weight: 700;
                color: #1e293b;
            }
            
            .metric-label {
                font-size: 12px;
                color: #64748b;
                margin-top: 5px;
            }
            
            .extraction-results {
                margin-top: 20px;
            }
            
            .results-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }
            
            .result-card {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
            }
            
            .result-card h5 {
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 10px;
            }
            
            .result-details {
                font-size: 12px;
                color: #64748b;
                line-height: 1.4;
            }
            
            /* Advanced Mode */
            .advanced-mode {
                display: none;
                height: 100%;
                padding: 20px;
                overflow-y: auto;
            }
            
            .advanced-mode.active {
                display: block;
            }
            
            .advanced-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 1fr 1fr;
                gap: 20px;
                height: 100%;
            }
            
            .advanced-panel {
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .technical-analysis {
                padding: 20px;
                overflow-y: auto;
            }
            
            .analysis-section {
                margin-bottom: 25px;
            }
            
            .analysis-section h4 {
                font-size: 16px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 10px;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 5px;
            }
            
            .analysis-data {
                font-family: 'Monaco', 'Menlo', monospace;
                font-size: 12px;
                background: #f8fafc;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #e2e8f0;
                overflow-x: auto;
            }
            
            .orchestrator-panel {
                padding: 20px;
            }
            
            .orchestrator-flow {
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            
            .flow-step {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px;
                background: #f8fafc;
                border-radius: 6px;
                border-left: 4px solid #3b82f6;
            }
            
            .flow-step.completed {
                border-left-color: #10b981;
                background: #f0fdf4;
            }
            
            .flow-step.failed {
                border-left-color: #ef4444;
                background: #fef2f2;
            }
            
            .step-icon {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
                color: white;
                background: #3b82f6;
            }
            
            .flow-step.completed .step-icon {
                background: #10b981;
            }
            
            .flow-step.failed .step-icon {
                background: #ef4444;
            }
            
            .step-details {
                flex: 1;
            }
            
            .step-title {
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
            }
            
            .step-description {
                font-size: 12px;
                color: #64748b;
            }
            
            .step-timing {
                font-size: 11px;
                color: #9ca3af;
            }
            
            /* Responsive Design */
            @media (max-width: 1200px) {
                .left-sidebar {
                    width: 300px;
                }
                
                .advanced-grid {
                    grid-template-columns: 1fr;
                    grid-template-rows: repeat(4, 1fr);
                }
            }
            
            @media (max-width: 768px) {
                .left-sidebar {
                    position: absolute;
                    left: 0;
                    top: 0;
                    height: 100%;
                    z-index: 1000;
                    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
                }
                
                .simple-mode {
                    grid-template-columns: 1fr;
                    grid-template-rows: 1fr 1fr;
                }
                
                .queue-grid {
                    grid-template-columns: 1fr;
                }
                
                .queue-stats {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            /* Loading States */
            .loading {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
                color: #64748b;
            }
            
            .loading::before {
                content: "";
                width: 20px;
                height: 20px;
                border: 2px solid #e2e8f0;
                border-top: 2px solid #3b82f6;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Empty States */
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #64748b;
            }
            
            .empty-state h3 {
                font-size: 18px;
                margin-bottom: 10px;
                color: #374151;
            }
            
            .empty-state p {
                font-size: 14px;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <div class="app-container">
            <!-- Left Sidebar - Image Selection -->
            <div class="left-sidebar" id="leftSidebar">
                <button class="sidebar-toggle" onclick="toggleSidebar()">◀</button>
                
                <div class="sidebar-header">
                    <h3>📁 Image Library</h3>
                    <p style="font-size: 12px; color: #64748b; margin-top: 5px;">
                        Select an image to analyze
                    </p>
                </div>
                
                <div class="filters-section">
                    <div class="filter-group">
                        <label>Search</label>
                        <div class="search-box">
                            <input type="text" id="searchInput" placeholder="Search images..." onkeyup="filterImages()">
                        </div>
                    </div>
                    
                    <div class="filter-group">
                        <label>Store</label>
                        <select id="storeFilter" onchange="filterImages()">
                            <option value="">All Stores</option>
                            <option value="walmart">Walmart</option>
                            <option value="target">Target</option>
                            <option value="kroger">Kroger</option>
                            <option value="safeway">Safeway</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Category</label>
                        <select id="categoryFilter" onchange="filterImages()">
                            <option value="">All Categories</option>
                            <option value="beverages">Beverages</option>
                            <option value="snacks">Snacks</option>
                            <option value="dairy">Dairy</option>
                            <option value="frozen">Frozen</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Status</label>
                        <select id="statusFilter" onchange="filterImages()">
                            <option value="">All Status</option>
                            <option value="pending">Pending</option>
                            <option value="processing">Processing</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                            <option value="review">Needs Review</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label>Date</label>
                        <input type="date" id="dateFilter" onchange="filterImages()">
                    </div>
                    
                    <div class="view-toggle">
                        <button class="active" onclick="setViewMode('grid')">Grid</button>
                        <button onclick="setViewMode('list')">List</button>
                    </div>
                </div>
                
                <div class="images-container">
                    <div id="imageGrid" class="image-grid">
                        <!-- Images will be loaded here -->
                    </div>
                </div>
                
                <div class="pagination">
                    <span id="paginationInfo">1-20 of 156 images</span>
                    <div class="pagination-controls">
                        <button onclick="previousPage()" id="prevBtn">‹</button>
                        <button class="active">1</button>
                        <button>2</button>
                        <button>3</button>
                        <button onclick="nextPage()" id="nextBtn">›</button>
                    </div>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="main-content">
                <!-- Header -->
                <div class="header">
                    <h1>🤖 OnShelf AI Dashboard</h1>
                    <div class="mode-selector">
                        <button class="mode-btn active" onclick="switchMode('queue')">Queue</button>
                        <button class="mode-btn" onclick="switchMode('simple')">Simple</button>
                        <button class="mode-btn" onclick="switchMode('comparison')">Comparison</button>
                        <button class="mode-btn" onclick="switchMode('advanced')">Advanced</button>
                    </div>
                </div>
                
                <!-- Breadcrumb -->
                <div class="breadcrumb">
                    <span id="breadcrumb">Extraction Queue</span>
                </div>
                
                <!-- Content Area -->
                <div class="content-area">
                    <!-- Queue Interface -->
                    <div id="queue-interface" class="queue-interface">
                        <div class="queue-stats">
                            <div class="stat-card review">
                                <div class="stat-number" id="reviewCount">0</div>
                                <div class="stat-label">Needs Review</div>
                            </div>
                            <div class="stat-card processing">
                                <div class="stat-number" id="processingCount">0</div>
                                <div class="stat-label">Processing</div>
                            </div>
                            <div class="stat-card completed">
                                <div class="stat-number" id="completedCount">0</div>
                                <div class="stat-label">Completed</div>
                            </div>
                            <div class="stat-card failed">
                                <div class="stat-number" id="failedCount">0</div>
                                <div class="stat-label">Failed</div>
                            </div>
                        </div>
                        
                        <div id="queueGrid" class="queue-grid">
                            <!-- Queue items will be loaded here -->
                        </div>
                    </div>
                    
                    <!-- Simple Mode - 2 Panel Layout -->
                    <div id="simple-mode" class="simple-mode">
                        <div class="image-panel">
                            <div class="panel-header">
                                <h3>📷 Original Image</h3>
                            </div>
                            <div class="panel-content">
                                <div class="image-viewer">
                                    <img id="originalImage" src="" alt="Original shelf image" style="display: none;">
                                    <div id="imageLoading" class="loading">Loading image...</div>
                                    <div class="image-controls">
                                        <button class="control-btn" onclick="zoomImage(0.5)">50%</button>
                                        <button class="control-btn" onclick="zoomImage(1.0)">100%</button>
                                        <button class="control-btn" onclick="zoomImage(2.0)">200%</button>
                                        <button class="control-btn" onclick="toggleOverlays()">Overlays</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="planogram-panel">
                            <div class="panel-header">
                                <h3>📊 Generated Planogram</h3>
                            </div>
                            <div class="panel-content">
                                <div id="planogramViewer" class="image-viewer">
                                    <div class="loading">Loading planogram...</div>
                                </div>
                                
                                <div class="rating-system">
                                    <h4>⭐ Extraction Quality</h4>
                                    <div class="star-rating" data-rating="extraction">
                                        <span class="star" data-value="1">★</span>
                                        <span class="star" data-value="2">★</span>
                                        <span class="star" data-value="3">★</span>
                                        <span class="star" data-value="4">★</span>
                                        <span class="star" data-value="5">★</span>
                                    </div>
                                    
                                    <div class="feedback-area">
                                        <label>What worked well:</label>
                                        <textarea id="workedWell" placeholder="Describe what the AI did correctly..."></textarea>
                                    </div>
                                    
                                    <h4 style="margin-top: 20px;">⭐ Planogram Quality</h4>
                                    <div class="star-rating" data-rating="planogram">
                                        <span class="star" data-value="1">★</span>
                                        <span class="star" data-value="2">★</span>
                                        <span class="star" data-value="3">★</span>
                                        <span class="star" data-value="4">★</span>
                                        <span class="star" data-value="5">★</span>
                                    </div>
                                    
                                    <div class="feedback-area">
                                        <label>Needs improvement:</label>
                                        <textarea id="needsImprovement" placeholder="Describe what needs to be fixed..."></textarea>
                                    </div>
                                    
                                    <div style="margin-top: 20px; display: flex; gap: 10px;">
                                        <button class="btn btn-primary" onclick="switchMode('comparison')">Show Details</button>
                                        <button class="btn btn-secondary" onclick="switchMode('advanced')">Advanced Mode</button>
                                        <button class="btn btn-secondary" onclick="switchMode('queue')">Back to Queue</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Comparison Mode - System Comparison -->
                    <div id="comparison-mode" class="comparison-mode">
                        <div class="agent-tabs">
                            <button class="agent-tab active" onclick="switchAgent('agent1')">Agent 1: Custom Consensus</button>
                            <button class="agent-tab" onclick="switchAgent('agent2')">Agent 2: LangGraph</button>
                            <button class="agent-tab" onclick="switchAgent('agent3')">Agent 3: Hybrid</button>
                        </div>
                        
                        <div id="agent1" class="agent-content">
                            <div class="agent-metrics">
                                <div class="metric-card">
                                    <div class="metric-value" id="agent1Accuracy">87%</div>
                                    <div class="metric-label">Accuracy</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent1Speed">2.3s</div>
                                    <div class="metric-label">Processing Time</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent1Cost">£0.12</div>
                                    <div class="metric-label">API Cost</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent1Products">5</div>
                                    <div class="metric-label">Products Found</div>
                                </div>
                            </div>
                            
                            <div class="extraction-results">
                                <h4>Extraction Results</h4>
                                <div id="agent1Results" class="results-grid">
                                    <!-- Results will be loaded here -->
                                </div>
                            </div>
                        </div>
                        
                        <div id="agent2" class="agent-content" style="display: none;">
                            <div class="agent-metrics">
                                <div class="metric-card">
                                    <div class="metric-value" id="agent2Accuracy">92%</div>
                                    <div class="metric-label">Accuracy</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent2Speed">4.1s</div>
                                    <div class="metric-label">Processing Time</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent2Cost">£0.18</div>
                                    <div class="metric-label">API Cost</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent2Products">6</div>
                                    <div class="metric-label">Products Found</div>
                                </div>
                            </div>
                            
                            <div class="extraction-results">
                                <h4>Extraction Results</h4>
                                <div id="agent2Results" class="results-grid">
                                    <!-- Results will be loaded here -->
                                </div>
                            </div>
                        </div>
                        
                        <div id="agent3" class="agent-content" style="display: none;">
                            <div class="agent-metrics">
                                <div class="metric-card">
                                    <div class="metric-value" id="agent3Accuracy">95%</div>
                                    <div class="metric-label">Accuracy</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent3Speed">3.7s</div>
                                    <div class="metric-label">Processing Time</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent3Cost">£0.15</div>
                                    <div class="metric-label">API Cost</div>
                                </div>
                                <div class="metric-card">
                                    <div class="metric-value" id="agent3Products">7</div>
                                    <div class="metric-label">Products Found</div>
                                </div>
                            </div>
                            
                            <div class="extraction-results">
                                <h4>Extraction Results</h4>
                                <div id="agent3Results" class="results-grid">
                                    <!-- Results will be loaded here -->
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; display: flex; gap: 10px;">
                            <button class="btn btn-secondary" onclick="switchMode('simple')">Simple View</button>
                            <button class="btn btn-secondary" onclick="switchMode('advanced')">Advanced Mode</button>
                            <button class="btn btn-secondary" onclick="switchMode('queue')">Back to Queue</button>
                        </div>
                    </div>
                    
                    <!-- Advanced Mode - 4 Panel Technical Deep Dive -->
                    <div id="advanced-mode" class="advanced-mode">
                        <div class="advanced-grid">
                            <!-- Original Image Panel -->
                            <div class="advanced-panel">
                                <div class="panel-header">
                                    <h3>📷 Original Image Analysis</h3>
                                </div>
                                <div class="panel-content">
                                    <div class="image-viewer">
                                        <img id="advancedOriginalImage" src="" alt="Original image">
                                        <div class="image-controls">
                                            <button class="control-btn" onclick="zoomImage(0.5)">50%</button>
                                            <button class="control-btn" onclick="zoomImage(1.0)">100%</button>
                                            <button class="control-btn" onclick="zoomImage(2.0)">200%</button>
                                            <button class="control-btn" onclick="toggleOverlays()">Overlays</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Agent Deep Dive Panel -->
                            <div class="advanced-panel">
                                <div class="panel-header">
                                    <h3>🔍 Agent Deep Dive</h3>
                                </div>
                                <div class="technical-analysis">
                                    <div class="analysis-section">
                                        <h4>Model Performance</h4>
                                        <div class="analysis-data" id="modelPerformance">
                                            Loading performance data...
                                        </div>
                                    </div>
                                    
                                    <div class="analysis-section">
                                        <h4>Confidence Scores</h4>
                                        <div class="analysis-data" id="confidenceScores">
                                            Loading confidence data...
                                        </div>
                                    </div>
                                    
                                    <div class="analysis-section">
                                        <h4>Error Analysis</h4>
                                        <div class="analysis-data" id="errorAnalysis">
                                            Loading error analysis...
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Planogram Analysis Panel -->
                            <div class="advanced-panel">
                                <div class="panel-header">
                                    <h3>📊 Planogram Analysis</h3>
                                </div>
                                <div class="panel-content">
                                    <div id="advancedPlanogramViewer" class="image-viewer">
                                        <div class="loading">Loading planogram...</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Orchestrator Panel -->
                            <div class="advanced-panel">
                                <div class="panel-header">
                                    <h3>⚙️ System Orchestrator</h3>
                                </div>
                                <div class="orchestrator-panel">
                                    <div class="orchestrator-flow" id="orchestratorFlow">
                                        <!-- Flow steps will be loaded here -->
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 20px; display: flex; gap: 10px;">
                            <button class="btn btn-secondary" onclick="switchMode('simple')">Simple View</button>
                            <button class="btn btn-secondary" onclick="switchMode('comparison')">Comparison Mode</button>
                            <button class="btn btn-secondary" onclick="switchMode('queue')">Back to Queue</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Global state
            let currentMode = 'queue';
            let selectedItemId = null;
            let queueData = [];
            let imageData = [];
            let filteredImages = [];
            let currentPage = 1;
            let itemsPerPage = 20;
            let viewMode = 'grid';
            let sidebarCollapsed = false;
            let zoomLevel = 1.0;
            let overlaysVisible = false;
            let currentAgent = 'agent1';
            
            // Initialize application
            document.addEventListener('DOMContentLoaded', function() {
                // Collapse sidebar by default on queue page
                sidebarCollapsed = true;
                const sidebar = document.getElementById('leftSidebar');
                const toggle = sidebar.querySelector('.sidebar-toggle');
                sidebar.classList.add('collapsed');
                toggle.innerHTML = '▶';
                
                loadQueue();
                loadImages();
            });
            
            // Sidebar management
            function toggleSidebar() {
                const sidebar = document.getElementById('leftSidebar');
                const toggle = sidebar.querySelector('.sidebar-toggle');
                
                sidebarCollapsed = !sidebarCollapsed;
                
                if (sidebarCollapsed) {
                    sidebar.classList.add('collapsed');
                    toggle.innerHTML = '▶';
                } else {
                    sidebar.classList.remove('collapsed');
                    toggle.innerHTML = '◀';
                }
            }
            
            // Mode switching
            function switchMode(mode) {
                // Hide all modes
                document.getElementById('queue-interface').style.display = 'none';
                document.getElementById('simple-mode').classList.remove('active');
                document.getElementById('comparison-mode').classList.remove('active');
                document.getElementById('advanced-mode').classList.remove('active');
                
                // Update mode buttons
                document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');
                
                // Manage sidebar based on mode
                const sidebar = document.getElementById('leftSidebar');
                const toggle = sidebar.querySelector('.sidebar-toggle');
                
                // Show selected mode
                if (mode === 'queue') {
                    document.getElementById('queue-interface').style.display = 'block';
                    updateBreadcrumb('Extraction Queue');
                    
                    // Collapse sidebar for queue mode (not needed)
                    if (!sidebarCollapsed) {
                        sidebarCollapsed = true;
                        sidebar.classList.add('collapsed');
                        toggle.innerHTML = '▶';
                    }
                } else if (mode === 'simple') {
                    document.getElementById('simple-mode').classList.add('active');
                    updateBreadcrumb(`Extraction #${selectedItemId} - Simple Analysis`);
                    loadSimpleModeData();
                    
                    // Expand sidebar for analysis modes (image selection needed)
                    if (sidebarCollapsed) {
                        sidebarCollapsed = false;
                        sidebar.classList.remove('collapsed');
                        toggle.innerHTML = '◀';
                    }
                } else if (mode === 'comparison') {
                    document.getElementById('comparison-mode').classList.add('active');
                    updateBreadcrumb(`Extraction #${selectedItemId} - System Comparison`);
                    loadComparisonModeData();
                    
                    // Expand sidebar for analysis modes
                    if (sidebarCollapsed) {
                        sidebarCollapsed = false;
                        sidebar.classList.remove('collapsed');
                        toggle.innerHTML = '◀';
                    }
                } else if (mode === 'advanced') {
                    document.getElementById('advanced-mode').classList.add('active');
                    updateBreadcrumb(`Extraction #${selectedItemId} - Advanced Analysis`);
                    loadAdvancedModeData();
                    
                    // Expand sidebar for analysis modes
                    if (sidebarCollapsed) {
                        sidebarCollapsed = false;
                        sidebar.classList.remove('collapsed');
                        toggle.innerHTML = '◀';
                    }
                }
                
                currentMode = mode;
            }
            
            function updateBreadcrumb(text) {
                document.getElementById('breadcrumb').innerHTML = `<span>${text}</span>`;
            }
            
            // Load queue data
            async function loadQueue() {
                try {
                    console.log('🔄 Loading queue data from API...');
                    const response = await fetch('/api/queue/items');
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    queueData = data.items || [];
                    
                    console.log(`✅ Successfully loaded ${queueData.length} real queue items from database`);
                    console.log('Queue items:', queueData.map(item => `#${item.id} (${item.status})`).join(', '));
                    
                    updateQueueStats();
                    renderQueue();
                    
                } catch (error) {
                    console.error('❌ Failed to load queue data:', error);
                    
                    // Show error state instead of mock data
                    queueData = [];
                    updateQueueStats();
                    renderQueueError(error.message);
                }
            }
            
            // Load images for sidebar
            async function loadImages() {
                try {
                    console.log('🔄 Loading image data from API...');
                    const response = await fetch('/api/queue/items');
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const data = await response.json();
                    imageData = data.items || [];
                    filteredImages = [...imageData];
                    
                    console.log(`✅ Successfully loaded ${imageData.length} real images for sidebar`);
                    renderImages();
                    
                } catch (error) {
                    console.error('❌ Failed to load image data:', error);
                    
                    // Show error state instead of mock data
                    imageData = [];
                    filteredImages = [];
                    renderImagesError(error.message);
                }
            }
            

            
            // Update queue statistics
            function updateQueueStats() {
                const stats = {
                    review: queueData.filter(item => item.human_review_required).length,
                    processing: queueData.filter(item => item.status === 'processing').length,
                    completed: queueData.filter(item => item.status === 'completed').length,
                    failed: queueData.filter(item => item.status === 'failed').length
                };
                
                document.getElementById('reviewCount').textContent = stats.review;
                document.getElementById('processingCount').textContent = stats.processing;
                document.getElementById('completedCount').textContent = stats.completed;
                document.getElementById('failedCount').textContent = stats.failed;
            }
            
            // Render queue error
            function renderQueueError(errorMessage) {
                const grid = document.getElementById('queueGrid');
                grid.innerHTML = `
                    <div class="empty-state" style="grid-column: 1 / -1;">
                        <h3>❌ Failed to Load Queue</h3>
                        <p>Error: ${errorMessage}</p>
                        <button class="btn btn-primary" onclick="loadQueue()" style="margin-top: 15px;">🔄 Retry</button>
                    </div>
                `;
            }
            
            // Render queue items
            function renderQueue() {
                const grid = document.getElementById('queueGrid');
                
                if (queueData.length === 0) {
                    grid.innerHTML = `
                        <div class="empty-state" style="grid-column: 1 / -1;">
                            <h3>📭 No Queue Items</h3>
                            <p>No extraction items found in the queue. Upload some images to get started.</p>
                        </div>
                    `;
                    return;
                }
                
                grid.innerHTML = queueData.map(item => `
                    <div class="queue-item ${item.human_review_required ? 'priority' : ''} ${selectedItemId === item.id ? 'selected' : ''}" 
                         onclick="selectQueueItem(${item.id})" 
                         data-item-id="${item.id}">
                        <div class="item-header">
                            <div class="item-title">Extraction #${item.id}</div>
                            <div class="item-status ${getStatusClass(item.status)}">${getStatusText(item.status)}</div>
                        </div>
                        
                        <div class="item-meta">
                            Created: ${new Date(item.created_at).toLocaleDateString()}<br>
                            ${item.comparison_group_id ? `Group: ${item.comparison_group_id}` : 'Not processed'}
                            ${item.human_review_required ? '<br><strong>⚠️ Needs Human Review</strong>' : ''}
                        </div>
                        
                        ${item.final_accuracy !== null ? `
                            <div class="item-accuracy">
                                <div class="accuracy-bar">
                                    <div class="accuracy-fill" style="width: ${item.final_accuracy * 100}%"></div>
                                </div>
                                <div class="accuracy-text">${Math.round(item.final_accuracy * 100)}%</div>
                            </div>
                        ` : ''}
                        
                        ${item.status === 'pending' ? `
                            <div class="system-selection">
                                <div class="system-label">Select Extraction Systems:</div>
                                <div class="system-checkboxes">
                                    <div class="system-checkbox">
                                        <input type="checkbox" id="custom_${item.id}" value="custom_consensus" 
                                               onchange="updateSystemSelection(${item.id})" checked>
                                        <label for="custom_${item.id}">Custom Consensus</label>
                                    </div>
                                    <div class="system-description">Direct API calls with weighted voting</div>
                                    
                                    <div class="system-checkbox">
                                        <input type="checkbox" id="langgraph_${item.id}" value="langgraph" 
                                               onchange="updateSystemSelection(${item.id})">
                                        <label for="langgraph_${item.id}">LangGraph</label>
                                    </div>
                                    <div class="system-description">Professional workflow orchestration</div>
                                    
                                    <div class="system-checkbox">
                                        <input type="checkbox" id="hybrid_${item.id}" value="hybrid" 
                                               onchange="updateSystemSelection(${item.id})">
                                        <label for="hybrid_${item.id}">Hybrid</label>
                                    </div>
                                    <div class="system-description">Combines both approaches</div>
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="item-actions">
                            ${item.status === 'pending' ? `
                                <button class="btn btn-primary" onclick="startProcessing(${item.id})">Start Processing</button>
                            ` : `
                                <button class="btn btn-success" onclick="viewResults(${item.id})">View Results</button>
                            `}
                            ${item.status === 'completed' ? `
                                <button class="btn btn-secondary" onclick="reprocess(${item.id})">Reprocess</button>
                            ` : ''}
                        </div>
                    </div>
                `).join('');
            }
            
            // Render images error
            function renderImagesError(errorMessage) {
                const container = document.getElementById('imageGrid');
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>❌ Failed to Load Images</h3>
                        <p>Error: ${errorMessage}</p>
                        <button class="btn btn-primary" onclick="loadImages()" style="margin-top: 15px;">🔄 Retry</button>
                    </div>
                `;
            }
            
            // Render images in sidebar
            function renderImages() {
                const container = document.getElementById('imageGrid');
                const startIndex = (currentPage - 1) * itemsPerPage;
                const endIndex = startIndex + itemsPerPage;
                const pageImages = filteredImages.slice(startIndex, endIndex);
                
                container.className = viewMode === 'grid' ? 'image-grid' : 'image-list';
                
                if (pageImages.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <h3>📭 No Images</h3>
                            <p>No images available. Upload some images to get started.</p>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = pageImages.map(image => `
                    <div class="image-item ${viewMode}-view ${selectedItemId === image.id ? 'selected' : ''}" 
                         onclick="selectImage(${image.id})">
                        <div class="image-thumbnail">
                            <img src="/api/queue/image/${image.id}" alt="Queue item ${image.id}" 
                                 style="width: 100%; height: 100%; object-fit: cover;" 
                                 onerror="this.style.display='none'; this.parentElement.innerHTML='📷';">
                        </div>
                        <div class="image-info">
                            <div class="image-title">Extraction #${image.id}</div>
                            <div class="image-meta">
                                ${image.ready_media_id ? `Media: ${image.ready_media_id.substring(0, 8)}...` : 'No media ID'}<br>
                                ${new Date(image.created_at).toLocaleDateString()}
                                <div class="status-badge status-${image.status}">${image.status}</div>
                            </div>
                        </div>
                    </div>
                `).join('');
                
                updatePagination();
            }
            
            // Image selection
            function selectImage(imageId) {
                selectedItemId = imageId;
                
                // Update visual selection in sidebar
                document.querySelectorAll('.image-item').forEach(item => {
                    item.classList.remove('selected');
                });
                event.target.closest('.image-item').classList.add('selected');
                
                // Auto-switch to simple mode and load the image
                switchMode('simple');
                
                // Close sidebar on mobile
                if (window.innerWidth <= 768) {
                    toggleSidebar();
                }
            }
            
            // Load data for different modes
            async function loadSimpleModeData() {
                if (!selectedItemId) return;
                
                try {
                    // Load original image
                    const imageElement = document.getElementById('originalImage');
                    const loadingElement = document.getElementById('imageLoading');
                    
                    imageElement.onload = function() {
                        loadingElement.style.display = 'none';
                        imageElement.style.display = 'block';
                    };
                    
                    imageElement.onerror = function() {
                        loadingElement.innerHTML = 'Failed to load image';
                    };
                    
                    imageElement.src = `/api/queue/image/${selectedItemId}`;
                    
                    // Load planogram
                    const planogramViewer = document.getElementById('planogramViewer');
                    try {
                        const planogramResponse = await fetch(`/api/planogram/${selectedItemId}/render?format=svg&abstraction_level=product_view`);
                        if (planogramResponse.ok) {
                            const svgContent = await planogramResponse.text();
                            planogramViewer.innerHTML = svgContent;
                        } else {
                            planogramViewer.innerHTML = '<div class="loading">Planogram not available</div>';
                        }
                    } catch (error) {
                        planogramViewer.innerHTML = '<div class="loading">Failed to load planogram</div>';
                    }
                    
                } catch (error) {
                    console.error('Error loading simple mode data:', error);
                }
            }
            
            async function loadComparisonModeData() {
                if (!selectedItemId) return;
                
                // Load comparison data for each agent
                try {
                    // This would normally fetch real comparison data
                    // For now, we'll use the existing mock data structure
                    console.log('Loading comparison data for item:', selectedItemId);
                    
                    // Load results for each agent
                    await loadAgentResults('agent1');
                    await loadAgentResults('agent2');
                    await loadAgentResults('agent3');
                    
                } catch (error) {
                    console.error('Error loading comparison data:', error);
                }
            }
            
            async function loadAdvancedModeData() {
                if (!selectedItemId) return;
                
                try {
                    // Load original image in advanced mode
                    const advancedImage = document.getElementById('advancedOriginalImage');
                    advancedImage.src = `/api/queue/image/${selectedItemId}`;
                    
                    // Load planogram in advanced mode
                    const advancedPlanogram = document.getElementById('advancedPlanogramViewer');
                    try {
                        const planogramResponse = await fetch(`/api/planogram/${selectedItemId}/render?format=svg&abstraction_level=sku_view`);
                        if (planogramResponse.ok) {
                            const svgContent = await planogramResponse.text();
                            advancedPlanogram.innerHTML = svgContent;
                        } else {
                            advancedPlanogram.innerHTML = '<div class="loading">Planogram not available</div>';
                        }
                    } catch (error) {
                        advancedPlanogram.innerHTML = '<div class="loading">Failed to load planogram</div>';
                    }
                    
                    // Load technical analysis data
                    await loadTechnicalAnalysis();
                    await loadOrchestratorFlow();
                    
                } catch (error) {
                    console.error('Error loading advanced mode data:', error);
                }
            }
            
            async function loadAgentResults(agentId) {
                const resultsContainer = document.getElementById(`${agentId}Results`);
                
                if (!selectedItemId) {
                    resultsContainer.innerHTML = '<div class="loading">No item selected</div>';
                    return;
                }
                
                try {
                    // Try to load real comparison results
                    const response = await fetch(`/api/queue/comparison/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Process real comparison data here
                        resultsContainer.innerHTML = '<div class="loading">Real comparison data loaded</div>';
                    } else {
                        resultsContainer.innerHTML = '<div class="loading">No comparison data available yet</div>';
                    }
                } catch (error) {
                    console.error('Failed to load agent results:', error);
                    resultsContainer.innerHTML = '<div class="loading">Failed to load comparison data</div>';
                }
            }
            
            async function loadTechnicalAnalysis() {
                if (!selectedItemId) {
                    document.getElementById('modelPerformance').innerHTML = 'No item selected';
                    document.getElementById('confidenceScores').innerHTML = 'No item selected';
                    document.getElementById('errorAnalysis').innerHTML = 'No item selected';
                    return;
                }
                
                try {
                    // Try to load real technical analysis data
                    const response = await fetch(`/api/queue/analysis/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Process real analysis data here
                        document.getElementById('modelPerformance').innerHTML = 'Real performance data loaded';
                        document.getElementById('confidenceScores').innerHTML = 'Real confidence data loaded';
                        document.getElementById('errorAnalysis').innerHTML = 'Real error analysis loaded';
                    } else {
                        document.getElementById('modelPerformance').innerHTML = 'No analysis data available yet';
                        document.getElementById('confidenceScores').innerHTML = 'No confidence data available yet';
                        document.getElementById('errorAnalysis').innerHTML = 'No error analysis available yet';
                    }
                } catch (error) {
                    console.error('Failed to load technical analysis:', error);
                    document.getElementById('modelPerformance').innerHTML = 'Failed to load performance data';
                    document.getElementById('confidenceScores').innerHTML = 'Failed to load confidence data';
                    document.getElementById('errorAnalysis').innerHTML = 'Failed to load error analysis';
                }
            }
            
            async function loadOrchestratorFlow() {
                const flowContainer = document.getElementById('orchestratorFlow');
                
                if (!selectedItemId) {
                    flowContainer.innerHTML = '<div class="loading">No item selected</div>';
                    return;
                }
                
                try {
                    // Try to load real orchestrator flow data
                    const response = await fetch(`/api/queue/flow/${selectedItemId}`);
                    if (response.ok) {
                        const data = await response.json();
                        // Process real flow data here
                        flowContainer.innerHTML = '<div class="loading">Real orchestrator flow loaded</div>';
                    } else {
                        flowContainer.innerHTML = '<div class="loading">No flow data available yet</div>';
                    }
                } catch (error) {
                    console.error('Failed to load orchestrator flow:', error);
                    flowContainer.innerHTML = '<div class="loading">Failed to load flow data</div>';
                }
            }
            
            // Agent switching in comparison mode
            function switchAgent(agentId) {
                // Hide all agent content
                document.querySelectorAll('.agent-content').forEach(content => {
                    content.style.display = 'none';
                });
                
                // Update tab states
                document.querySelectorAll('.agent-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected agent
                document.getElementById(agentId).style.display = 'block';
                event.target.classList.add('active');
                
                currentAgent = agentId;
            }
            
            // Helper functions
            function getStatusClass(status) {
                const classes = {
                    'pending': 'status-pending',
                    'processing': 'status-processing',
                    'completed': 'status-completed',
                    'failed': 'status-failed'
                };
                return classes[status] || 'status-pending';
            }
            
            function getStatusText(status) {
                const texts = {
                    'pending': 'Pending',
                    'processing': 'Processing',
                    'completed': 'Completed',
                    'failed': 'Failed'
                };
                return texts[status] || 'Unknown';
            }
            
            // Queue item selection
            function selectQueueItem(itemId) {
                selectedItemId = itemId;
                
                // Update visual selection
                document.querySelectorAll('.queue-item').forEach(item => {
                    item.classList.remove('selected');
                });
                document.querySelector(`[data-item-id="${itemId}"]`).classList.add('selected');
                
                // Update breadcrumb
                updateBreadcrumb(`Extraction #${itemId} Selected`);
            }
            
            // System selection update
            function updateSystemSelection(itemId) {
                const checkboxes = document.querySelectorAll(`input[onchange="updateSystemSelection(${itemId})"]`);
                const selectedSystems = Array.from(checkboxes)
                    .filter(cb => cb.checked)
                    .map(cb => cb.value);
                
                // Update the item data
                const item = queueData.find(item => item.id === itemId);
                if (item) {
                    item.selected_systems = selectedSystems;
                }
                
                console.log(`Updated systems for item ${itemId}:`, selectedSystems);
            }
            
            // Processing actions
            async function startProcessing(itemId) {
                const item = queueData.find(item => item.id === itemId);
                if (!item || item.selected_systems.length === 0) {
                    alert('Please select at least one extraction system');
                    return;
                }
                
                try {
                    const response = await fetch(`/api/queue/process/${itemId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ systems: item.selected_systems })
                    });
                    
                    if (response.ok) {
                        // Update item status
                        item.status = 'processing';
                        renderQueue();
                        updateQueueStats();
                    } else {
                        throw new Error('Failed to start processing');
                    }
                } catch (error) {
                    console.error('Error starting processing:', error);
                    alert('Failed to start processing. Please try again.');
                }
            }
            
            async function viewResults(itemId) {
                selectedItemId = itemId;
                switchMode('simple');
            }
            
            async function reprocess(itemId) {
                if (confirm('Are you sure you want to reprocess this extraction?')) {
                    try {
                        const response = await fetch(`/api/queue/reprocess/${itemId}`, {
                            method: 'POST'
                        });
                        
                        if (response.ok) {
                            loadQueue(); // Reload queue
                        } else {
                            throw new Error('Failed to start reprocessing');
                        }
                    } catch (error) {
                        console.error('Error reprocessing:', error);
                        alert('Failed to start reprocessing. Please try again.');
                    }
                }
            }
            
            // Image filtering
            function filterImages() {
                const searchTerm = document.getElementById('searchInput').value.toLowerCase();
                const storeFilter = document.getElementById('storeFilter').value;
                const categoryFilter = document.getElementById('categoryFilter').value;
                const statusFilter = document.getElementById('statusFilter').value;
                const dateFilter = document.getElementById('dateFilter').value;
                
                filteredImages = imageData.filter(image => {
                    // Search filter
                    if (searchTerm && !image.title.toLowerCase().includes(searchTerm)) return false;
                    
                    // Store filter
                    if (storeFilter && image.store !== storeFilter) return false;
                    
                    // Category filter
                    if (categoryFilter && image.category !== categoryFilter) return false;
                    
                    // Status filter
                    if (statusFilter && image.status !== statusFilter) return false;
                    
                    // Date filter
                    if (dateFilter) {
                        const imageDate = new Date(image.created_at).toISOString().split('T')[0];
                        if (imageDate !== dateFilter) return false;
                    }
                    
                    return true;
                });
                
                currentPage = 1;
                renderImages();
            }
            
            // View mode switching
            function setViewMode(mode) {
                viewMode = mode;
                
                // Update button states
                document.querySelectorAll('.view-toggle button').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                renderImages();
            }
            
            // Pagination
            function updatePagination() {
                const totalPages = Math.ceil(filteredImages.length / itemsPerPage);
                const startItem = (currentPage - 1) * itemsPerPage + 1;
                const endItem = Math.min(currentPage * itemsPerPage, filteredImages.length);
                
                document.getElementById('paginationInfo').textContent = 
                    `${startItem}-${endItem} of ${filteredImages.length} images`;
                
                document.getElementById('prevBtn').disabled = currentPage === 1;
                document.getElementById('nextBtn').disabled = currentPage === totalPages;
            }
            
            function previousPage() {
                if (currentPage > 1) {
                    currentPage--;
                    renderImages();
                }
            }
            
            function nextPage() {
                const totalPages = Math.ceil(filteredImages.length / itemsPerPage);
                if (currentPage < totalPages) {
                    currentPage++;
                    renderImages();
                }
            }
            
            // Image controls
            function zoomImage(level) {
                zoomLevel = level;
                const images = document.querySelectorAll('.image-viewer img');
                images.forEach(img => {
                    img.style.transform = `scale(${level})`;
                });
            }
            
            function toggleOverlays() {
                overlaysVisible = !overlaysVisible;
                console.log('Overlays toggled:', overlaysVisible);
                // This would toggle overlay visibility in a real implementation
            }
            
            // Star rating system
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('star')) {
                    const rating = e.target.dataset.value;
                    const ratingGroup = e.target.parentElement.dataset.rating;
                    
                    // Update visual state
                    const stars = e.target.parentElement.querySelectorAll('.star');
                    stars.forEach((star, index) => {
                        if (index < rating) {
                            star.classList.add('active');
                        } else {
                            star.classList.remove('active');
                        }
                    });
                    
                    console.log(`Rating for ${ratingGroup}: ${rating} stars`);
                }
            });
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
        "architecture": "queue_review_dashboard",
        "features": [
            "queue_management",
            "multi_system_selection",
            "progressive_disclosure",
            "human_evaluation"
        ]
    }

@app.get("/api/status")
async def api_status():
    """API status and capabilities"""
    return {
        "api_version": "2.0.0",
        "interface_modes": ["queue", "simple", "comparison", "advanced"],
        "extraction_systems": ["custom_consensus", "langgraph", "hybrid"],
        "evaluation_system": "human_in_the_loop",
        "database": "supabase_integration"
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

