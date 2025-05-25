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
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0a0a0a;
                color: white;
                overflow-x: hidden;
            }
            
            /* Top Header */
            .top-header {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #111827;
                border-bottom: 1px solid #374151;
                padding: 15px 20px;
                z-index: 1000;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: left 0.3s ease;
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .sidebar-toggle {
                background: #374151;
                border: 1px solid #4b5563;
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 16px;
            }
            
            .sidebar-toggle:hover {
                background: #4b5563;
                border-color: #3b82f6;
            }
            
            .header-left h1 {
                margin: 0;
                font-size: 1.5rem;
                font-weight: 700;
                color: #3b82f6;
            }
            
            .breadcrumb {
                font-size: 13px;
                color: #9ca3af;
                font-weight: 500;
            }
            
            /* Sidebar */
            .sidebar {
                position: fixed;
                top: 0;
                left: -400px;
                width: 400px;
                height: 100vh;
                background: #1f2937;
                border-right: 1px solid #374151;
                z-index: 1100;
                transition: left 0.3s ease;
                display: flex;
                flex-direction: column;
                box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
            }
            
            .sidebar.open {
                left: 0;
            }
            
            .sidebar-header {
                padding: 20px;
                border-bottom: 1px solid #374151;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #111827;
            }
            
            .sidebar-header h3 {
                margin: 0;
                color: #3b82f6;
                font-size: 1.25rem;
            }
            
            .btn-icon {
                background: none;
                border: none;
                color: #9ca3af;
                font-size: 18px;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: all 0.2s ease;
            }
            
            .btn-icon:hover {
                background: #374151;
                color: white;
            }
            
            /* Sidebar Filters */
            .sidebar-filters {
                padding: 20px;
                border-bottom: 1px solid #374151;
            }
            
            .search-box {
                position: relative;
                margin-bottom: 15px;
            }
            
            .search-box input {
                width: 100%;
                padding: 10px 40px 10px 12px;
                background: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                color: white;
                font-size: 14px;
            }
            
            .search-box input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .search-icon {
                position: absolute;
                right: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: #9ca3af;
                font-size: 14px;
            }
            
            .filter-row {
                margin-bottom: 12px;
            }
            
            .filter-row select,
            .filter-row input[type="date"] {
                width: 100%;
                padding: 8px 12px;
                background: #374151;
                border: 1px solid #4b5563;
                border-radius: 6px;
                color: white;
                font-size: 13px;
            }
            
            /* Image List */
            .image-list {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .list-header {
                padding: 15px 20px;
                border-bottom: 1px solid #374151;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #111827;
            }
            
            .result-count {
                font-size: 13px;
                color: #9ca3af;
                font-weight: 500;
            }
            
            .view-toggle {
                display: flex;
                gap: 4px;
            }
            
            .view-btn {
                background: #374151;
                border: 1px solid #4b5563;
                color: #9ca3af;
                padding: 6px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s ease;
            }
            
            .view-btn:hover,
            .view-btn.active {
                background: #3b82f6;
                border-color: #3b82f6;
                color: white;
            }
            
            /* Image Grid */
            .image-grid {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                gap: 15px;
                align-content: start;
            }
            
            .image-item {
                background: #374151;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 2px solid transparent;
            }
            
            .image-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                border-color: #3b82f6;
            }
            
            .image-item.selected {
                border-color: #10b981;
                box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
            }
            
            .image-thumbnail {
                width: 100%;
                height: 120px;
                background: #4b5563;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #9ca3af;
                font-size: 24px;
            }
            
            .image-thumbnail img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }
            
            .image-info {
                padding: 12px;
            }
            
            .image-title {
                font-size: 12px;
                font-weight: 600;
                color: white;
                margin-bottom: 4px;
                line-height: 1.3;
            }
            
            .image-meta {
                font-size: 11px;
                color: #9ca3af;
                line-height: 1.2;
            }
            
            .image-status {
                display: inline-block;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 500;
                margin-top: 4px;
            }
            
            .status-pending { background: #f59e0b; color: #000; }
            .status-in_progress { background: #3b82f6; color: white; }
            .status-completed { background: #10b981; color: white; }
            .status-flagged { background: #ef4444; color: white; }
            
            /* Pagination */
            .pagination {
                padding: 15px 20px;
                border-top: 1px solid #374151;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #111827;
            }
            
            .page-info {
                font-size: 13px;
                color: #9ca3af;
                font-weight: 500;
            }
            
            /* Sidebar Overlay */
            .sidebar-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 1050;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }
            
            .sidebar-overlay.active {
                opacity: 1;
                visibility: visible;
            }
            
            /* Content shift when sidebar is open */
            body.sidebar-open .top-header {
                left: 400px;
            }
            
            body.sidebar-open .upload-interface,
            body.sidebar-open .simple-mode,
            body.sidebar-open .comparison-mode,
            body.sidebar-open .advanced-mode {
                margin-left: 400px;
                width: calc(100% - 400px);
            }
            
            /* Mode Selector */
            .mode-selector {
                display: flex;
                gap: 8px;
            }
            
            .mode-btn {
                padding: 8px 16px;
                background: #1f2937;
                border: 1px solid #374151;
                color: #d1d5db;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .mode-btn.active {
                background: #3b82f6;
                border-color: #3b82f6;
                color: white;
            }
            
            /* Upload Interface */
            .upload-interface {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: calc(100vh - 80px);
                padding: 20px;
                margin-top: 80px;
            }
            
            .upload-area {
                border: 2px dashed #374151;
                border-radius: 12px;
                padding: 60px;
                text-align: center;
                background: #111827;
                max-width: 600px;
                width: 100%;
                transition: all 0.3s ease;
            }
            
            .upload-area:hover {
                border-color: #3b82f6;
                background: #1f2937;
            }
            
            .upload-area.dragover {
                border-color: #10b981;
                background: #064e3b;
            }
            
            /* Simple Mode - 2 Panel Layout */
            .simple-mode {
                display: none;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                padding: 20px;
                height: calc(100vh - 80px);
                margin-top: 80px;
            }
            
            .image-panel, .planogram-panel {
                background: #111827;
                border-radius: 12px;
                padding: 20px;
                overflow: hidden;
            }
            
            .image-viewer {
                position: relative;
                width: 100%;
                height: 60%;
                background: #000;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .image-viewer img {
                width: 100%;
                height: 100%;
                object-fit: contain;
            }
            
            .zoom-controls {
                position: absolute;
                bottom: 10px;
                right: 10px;
                display: flex;
                gap: 5px;
            }
            
            .zoom-btn {
                background: rgba(0,0,0,0.7);
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .rating-system {
                margin-top: 20px;
                padding: 20px;
                background: #1f2937;
                border-radius: 8px;
            }
            
            .star-rating {
                display: flex;
                gap: 5px;
                margin: 10px 0;
            }
            
            .star {
                font-size: 24px;
                color: #374151;
                cursor: pointer;
                transition: color 0.2s;
            }
            
            .star.active, .star:hover {
                color: #fbbf24;
            }
            
            /* Comparison Mode - Agent Iterations */
            .comparison-mode {
                display: none;
                padding: 20px;
                height: calc(100vh - 80px);
                margin-top: 80px;
                overflow-y: auto;
            }
            
            .agent-tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 1px solid #374151;
            }
            
            .agent-tab {
                padding: 14px 28px;
                background: #1f2937;
                border: 1px solid #374151;
                color: #d1d5db;
                border-radius: 12px 12px 0 0;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
                font-size: 15px;
                position: relative;
                border-bottom: none;
            }
            
            .agent-tab:hover {
                background: #374151;
                color: #e5e7eb;
                transform: translateY(-1px);
            }
            
            .agent-tab.active {
                background: #3b82f6;
                color: white;
                border-color: #3b82f6;
                box-shadow: 0 -2px 8px rgba(59, 130, 246, 0.3);
            }
            
            .agent-tab.active::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                right: 0;
                height: 2px;
                background: #3b82f6;
            }
            
            .agent-content {
                display: none;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                height: calc(100vh - 120px);
            }
            
            .agent-content.active {
                display: grid;
            }
            
            .agent-data, .agent-planogram {
                background: #111827;
                border-radius: 12px;
                padding: 20px;
                overflow-y: auto;
            }
            
            .performance-metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .metric {
                background: #1f2937;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid #374151;
                transition: all 0.3s ease;
            }
            
            .metric:hover {
                border-color: #3b82f6;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
            
            .metric-value {
                font-size: 28px;
                font-weight: 700;
                color: #3b82f6;
                margin-bottom: 8px;
                font-variant-numeric: tabular-nums;
            }
            
            .metric-label {
                font-size: 13px;
                color: #9ca3af;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            /* Advanced Mode - 4 Panel Layout */
            .advanced-mode {
                display: none;
                grid-template-columns: 1fr 1fr;
                grid-template-rows: 1fr 1fr;
                gap: 20px;
                padding: 20px;
                height: calc(100vh - 80px);
                margin-top: 80px;
            }
            
            .panel {
                background: #111827;
                border-radius: 12px;
                padding: 20px;
                overflow: hidden;
            }
            
            .panel h3 {
                color: #3b82f6;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #374151;
            }
            
            /* Buttons */
            .btn {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                transition: background 0.3s ease;
            }
            
            .btn:hover {
                background: #2563eb;
            }
            
            .btn-secondary {
                background: #6b7280;
            }
            
            .btn-secondary:hover {
                background: #4b5563;
            }
            
            .btn-success {
                background: #10b981;
            }
            
            .btn-success:hover {
                background: #059669;
            }
            
            /* Feedback Areas */
            .feedback-area {
                margin-top: 15px;
            }
            
            .feedback-area textarea {
                width: 100%;
                min-height: 80px;
                background: #1f2937;
                border: 1px solid #374151;
                color: white;
                padding: 12px;
                border-radius: 6px;
                resize: vertical;
            }
            
            /* JSON Viewer */
            .json-viewer {
                background: #000;
                color: #10b981;
                padding: 15px;
                border-radius: 6px;
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                font-size: 13px;
                line-height: 1.4;
                overflow-x: auto;
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #374151;
            }
            
            /* Enhanced Typography */
            h2, h3, h4 {
                font-weight: 600;
                letter-spacing: -0.025em;
            }
            
            h2 {
                font-size: 1.875rem;
                margin-bottom: 1.5rem;
            }
            
            h3 {
                font-size: 1.25rem;
                margin-bottom: 1rem;
            }
            
            h4 {
                font-size: 1.125rem;
                margin-bottom: 0.75rem;
                margin-top: 1.5rem;
            }
            
            /* Improved Lists */
            ul {
                padding-left: 1.25rem;
                margin: 0.75rem 0;
            }
            
            li {
                margin-bottom: 0.5rem;
                line-height: 1.5;
            }
            
            /* Better Labels */
            label {
                font-weight: 500;
                color: #e5e7eb;
                display: block;
                margin-bottom: 0.5rem;
            }
            
            /* Enhanced Form Elements */
            select {
                width: 100%;
                padding: 10px 12px;
                background: #374151;
                color: white;
                border: 1px solid #4b5563;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.2s ease;
            }
            
            select:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            /* Loading States */
            .loading {
                display: flex;
                align-items: center;
                justify-content: center;
                color: #9ca3af;
                font-style: italic;
            }
            
            .loading::before {
                content: "⏳ ";
                margin-right: 0.5rem;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .simple-mode, .advanced-mode {
                    grid-template-columns: 1fr;
                }
                
                .agent-content {
                    grid-template-columns: 1fr;
                }
                
                .mode-selector {
                    position: relative;
                    top: auto;
                    right: auto;
                    justify-content: center;
                    margin-bottom: 20px;
                }
            }
        </style>
    </head>
    <body>
        <!-- Top Header -->
        <div class="top-header">
            <div class="header-left">
                <button class="sidebar-toggle" onclick="toggleSidebar()">
                    <span id="sidebar-icon">📁</span>
                </button>
                <h1>📊 OnShelf AI Dashboard</h1>
                <div class="breadcrumb" id="breadcrumb">
                    <span>No image selected</span>
                </div>
            </div>
            <div class="mode-selector">
                <button class="mode-btn active" onclick="switchMode('upload')">Upload</button>
                <button class="mode-btn" onclick="switchMode('simple')">Simple</button>
                <button class="mode-btn" onclick="switchMode('comparison')">Comparison</button>
                <button class="mode-btn" onclick="switchMode('advanced')">Advanced</button>
            </div>
        </div>

        <!-- Left Sidebar - Image Selection -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <h3>📁 Image Library</h3>
                <button class="btn-icon" onclick="toggleSidebar()">✕</button>
            </div>
            
            <!-- Search and Filters -->
            <div class="sidebar-filters">
                <div class="search-box">
                    <input type="text" id="imageSearch" placeholder="Search images..." onkeyup="filterImages()">
                    <span class="search-icon">🔍</span>
                </div>
                
                <div class="filter-row">
                    <select id="storeFilter" onchange="filterImages()">
                        <option value="">All Stores</option>
                        <option value="store_001">Store 001 - Downtown</option>
                        <option value="store_002">Store 002 - Mall</option>
                        <option value="store_003">Store 003 - Airport</option>
                        <option value="store_004">Store 004 - Suburb</option>
                    </select>
                </div>
                
                <div class="filter-row">
                    <select id="categoryFilter" onchange="filterImages()">
                        <option value="">All Categories</option>
                        <option value="beverages">Beverages</option>
                        <option value="snacks">Snacks</option>
                        <option value="dairy">Dairy</option>
                        <option value="frozen">Frozen</option>
                        <option value="personal_care">Personal Care</option>
                    </select>
                </div>
                
                <div class="filter-row">
                    <select id="statusFilter" onchange="filterImages()">
                        <option value="">All Status</option>
                        <option value="pending">Pending Review</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                        <option value="flagged">Flagged</option>
                    </select>
                </div>
                
                <div class="filter-row">
                    <input type="date" id="dateFilter" onchange="filterImages()">
                </div>
            </div>
            
            <!-- Image List -->
            <div class="image-list" id="imageList">
                <div class="list-header">
                    <span class="result-count" id="resultCount">Loading images...</span>
                    <div class="view-toggle">
                        <button class="view-btn active" onclick="setListView('grid')" title="Grid View">⊞</button>
                        <button class="view-btn" onclick="setListView('list')" title="List View">☰</button>
                    </div>
                </div>
                
                <div class="image-grid" id="imageGrid">
                    <!-- Images will be loaded here -->
                </div>
                
                <div class="pagination" id="pagination">
                    <button class="btn btn-secondary" onclick="loadPreviousPage()" id="prevBtn" disabled>← Previous</button>
                    <span class="page-info" id="pageInfo">Page 1 of 1</span>
                    <button class="btn btn-secondary" onclick="loadNextPage()" id="nextBtn" disabled>Next →</button>
                </div>
            </div>
        </div>

        <!-- Sidebar Overlay -->
        <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
        
        <!-- Upload Interface -->
        <div id="upload-interface" class="upload-interface">
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <h2>📷 Upload Shelf Image</h2>
                <p>Click here or drag and drop a retail shelf image</p>
                <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="uploadFile()">
                <button class="btn" style="margin-top: 20px;">Choose File</button>
            </div>
        </div>
        
        <!-- Simple Mode - 2 Panel Layout -->
        <div id="simple-mode" class="simple-mode">
            <div class="image-panel">
                <h3>📷 Original Image</h3>
                <div class="image-viewer">
                    <img id="originalImage" src="" alt="Original shelf image">
                    <div class="zoom-controls">
                        <button class="zoom-btn" onclick="zoomImage(0.25)">25%</button>
                        <button class="zoom-btn" onclick="zoomImage(0.5)">50%</button>
                        <button class="zoom-btn" onclick="zoomImage(1.0)">100%</button>
                        <button class="zoom-btn" onclick="zoomImage(2.0)">200%</button>
                        <button class="zoom-btn" onclick="zoomImage(4.0)">400%</button>
                        <button class="zoom-btn" onclick="toggleOverlays()">Overlays</button>
                    </div>
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
                </div>
            </div>
            
            <div class="planogram-panel">
                <h3>📊 Final Planogram</h3>
                <div id="planogramViewer" class="image-viewer">
                    <!-- Planogram will be rendered here -->
                </div>
                
                <div class="rating-system">
                    <h4>⭐ Planogram Quality</h4>
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
                        <button class="btn" onclick="switchMode('comparison')">Show Details</button>
                        <button class="btn btn-secondary" onclick="switchMode('advanced')">Advanced Mode</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Comparison Mode - Agent Iterations -->
        <div id="comparison-mode" class="comparison-mode">
            <h2>🔄 Agent Iteration Comparison</h2>
            
            <div class="agent-tabs">
                <button class="agent-tab active" onclick="switchAgent(1)">Agent 1</button>
                <button class="agent-tab" onclick="switchAgent(2)">Agent 2</button>
                <button class="agent-tab" onclick="switchAgent(3)">Agent 3</button>
            </div>
            
            <div id="agent-1" class="agent-content active">
                <div class="agent-data">
                    <div class="performance-metrics">
                        <div class="metric">
                            <div class="metric-value" id="agent1-accuracy">73%</div>
                            <div class="metric-label">Accuracy</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="agent1-products">21</div>
                            <div class="metric-label">Products Found</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="agent1-time">45s</div>
                            <div class="metric-label">Processing Time</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" id="agent1-model">GPT-4o</div>
                            <div class="metric-label">Model Used</div>
                        </div>
                    </div>
                    
                    <h4>✅ Improvements</h4>
                    <ul id="agent1-improvements">
                        <li>Basic shelf structure detection</li>
                        <li>Initial product identification</li>
                    </ul>
                    
                    <h4>❌ Issues</h4>
                    <ul id="agent1-issues">
                        <li>Missing 4 products</li>
                        <li>Price extraction errors</li>
                        <li>Poor positioning accuracy</li>
                    </ul>
                    
                    <h4>📋 JSON Data</h4>
                    <div class="json-viewer loading" id="agent1-json">
                        Loading agent data...
                    </div>
                </div>
                
                <div class="agent-planogram">
                    <h4>📊 Visual Planogram</h4>
                    <div id="agent1-planogram" class="image-viewer">
                        <!-- Agent 1 planogram will be rendered here -->
                    </div>
                </div>
            </div>
            
            <div id="agent-2" class="agent-content">
                <div class="agent-data">
                    <div class="performance-metrics">
                        <div class="metric">
                            <div class="metric-value">89%</div>
                            <div class="metric-label">Accuracy</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">24</div>
                            <div class="metric-label">Products Found</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">38s</div>
                            <div class="metric-label">Processing Time</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">Claude</div>
                            <div class="metric-label">Model Used</div>
                        </div>
                    </div>
                    
                    <h4>✅ Improvements</h4>
                    <ul>
                        <li>Found 3 additional products</li>
                        <li>Fixed price extraction</li>
                        <li>Improved confidence scores</li>
                    </ul>
                    
                    <h4>❌ Issues</h4>
                    <ul>
                        <li>Minor positioning errors</li>
                        <li>2 products still missing</li>
                    </ul>
                    
                    <h4>📋 JSON Data</h4>
                    <div class="json-viewer loading">
                        Loading agent data...
                    </div>
                </div>
                
                <div class="agent-planogram">
                    <h4>📊 Visual Planogram</h4>
                    <div class="image-viewer">
                        <!-- Agent 2 planogram will be rendered here -->
                    </div>
                </div>
            </div>
            
            <div id="agent-3" class="agent-content">
                <div class="agent-data">
                    <div class="performance-metrics">
                        <div class="metric">
                            <div class="metric-value">94%</div>
                            <div class="metric-label">Accuracy</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">25</div>
                            <div class="metric-label">Products Found</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">22s</div>
                            <div class="metric-label">Processing Time</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">Hybrid</div>
                            <div class="metric-label">Model Used</div>
                        </div>
                    </div>
                    
                    <h4>✅ Improvements</h4>
                    <ul>
                        <li>Found all products</li>
                        <li>Enhanced spatial positioning</li>
                        <li>Cross-validation complete</li>
                    </ul>
                    
                    <h4>❌ Issues</h4>
                    <ul>
                        <li>Minor confidence variations</li>
                    </ul>
                    
                    <h4>📋 JSON Data</h4>
                    <div class="json-viewer loading">
                        Loading agent data...
                    </div>
                </div>
                
                <div class="agent-planogram">
                    <h4>📊 Visual Planogram</h4>
                    <div class="image-viewer">
                        <!-- Agent 3 planogram will be rendered here -->
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Advanced Mode - 4 Panel Layout -->
        <div id="advanced-mode" class="advanced-mode">
            <div class="panel">
                <h3>📷 Original Image</h3>
                <div class="image-viewer">
                    <img id="advancedOriginalImage" src="" alt="Original shelf image">
                </div>
            </div>
            
            <div class="panel">
                <h3>🤖 Agent Deep Dive</h3>
                <div style="margin-bottom: 15px;">
                    <select id="agentSelector" onchange="loadAgentDeepDive()">
                        <option value="1">Agent 1 - Initial Extraction</option>
                        <option value="2">Agent 2 - Enhanced Detection</option>
                        <option value="3">Agent 3 - Final Optimization</option>
                    </select>
                </div>
                <div id="agentDeepDive" class="json-viewer loading">
                    Loading agent details...
                </div>
                <button class="btn btn-secondary" onclick="openPromptEditor()" style="margin-top: 15px;">
                    ✏️ Edit Prompts
                </button>
            </div>
            
            <div class="panel">
                <h3>📊 Planogram Analysis</h3>
                <div id="planogramAnalysis">
                    <h4>Quality Evaluation</h4>
                    <div class="star-rating" data-rating="advanced-planogram">
                        <span class="star" data-value="1">★</span>
                        <span class="star" data-value="2">★</span>
                        <span class="star" data-value="3">★</span>
                        <span class="star" data-value="4">★</span>
                        <span class="star" data-value="5">★</span>
                    </div>
                    
                    <h4>Issue Detection</h4>
                    <div style="margin: 15px 0;">
                        <label><input type="checkbox"> Poor spatial layout</label><br>
                        <label><input type="checkbox"> Missing products</label><br>
                        <label><input type="checkbox"> Incorrect positioning</label><br>
                        <label><input type="checkbox"> Price extraction errors</label><br>
                        <label><input type="checkbox"> Visual clarity issues</label>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <h3>🧠 Orchestrator Reasoning</h3>
                <div id="orchestratorInsights">
                    <h4>Decision Logic</h4>
                    <p>Master orchestrator chose 3-iteration approach based on initial complexity assessment.</p>
                    
                    <h4>Iteration Strategy</h4>
                    <ul>
                        <li>Agent 1: Broad detection with GPT-4o</li>
                        <li>Agent 2: Refinement with Claude</li>
                        <li>Agent 3: Validation with hybrid approach</li>
                    </ul>
                    
                    <h4>Focus Areas</h4>
                    <ul>
                        <li>Product detection accuracy</li>
                        <li>Spatial positioning</li>
                        <li>Price extraction</li>
                    </ul>
                    
                    <h4>Learning Progress</h4>
                    <div class="metric">
                        <div class="metric-value">+21%</div>
                        <div class="metric-label">Accuracy Improvement</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let currentMode = 'upload';
            let currentAgent = 1;
            let currentUploadId = null;
            let zoomLevel = 1.0;
            let overlaysVisible = false;
            let sidebarOpen = false;
            let currentPage = 1;
            let totalPages = 1;
            let imagesPerPage = 20;
            let allImages = [];
            let filteredImages = [];
            let selectedImageId = null;
            
            // Mode switching
            function switchMode(mode) {
                // Hide all modes
                document.getElementById('upload-interface').style.display = 'none';
                document.getElementById('simple-mode').style.display = 'none';
                document.getElementById('comparison-mode').style.display = 'none';
                document.getElementById('advanced-mode').style.display = 'none';
                
                // Update mode buttons
                document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');
                
                // Show selected mode
                if (mode === 'upload') {
                    document.getElementById('upload-interface').style.display = 'flex';
                } else if (mode === 'simple') {
                    document.getElementById('simple-mode').style.display = 'grid';
                } else if (mode === 'comparison') {
                    document.getElementById('comparison-mode').style.display = 'block';
                } else if (mode === 'advanced') {
                    document.getElementById('advanced-mode').style.display = 'grid';
                }
                
                currentMode = mode;
            }
            
            // Agent switching in comparison mode
            function switchAgent(agentNumber) {
                // Hide all agent content
                document.querySelectorAll('.agent-content').forEach(content => {
                    content.classList.remove('active');
                });
                
                // Update agent tabs
                document.querySelectorAll('.agent-tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected agent
                document.getElementById(`agent-${agentNumber}`).classList.add('active');
                event.target.classList.add('active');
                
                currentAgent = agentNumber;
            }
            
            // File upload
            async function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                const file = fileInput.files[0];
                
                if (!file) return;
                
                try {
                    // Show processing message
                    document.querySelector('.upload-area h2').textContent = '🔄 Processing...';
                    document.querySelector('.upload-area p').textContent = 'This may take a few minutes';
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('target_accuracy', '0.95');
                    formData.append('max_iterations', '3');
                    formData.append('abstraction_level', 'product_view');
                    
                    const response = await fetch('/api/v2/process-with-iterations', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        currentUploadId = result.upload_id;
                        loadProcessingResults(result);
                        switchMode('simple');
                    } else {
                        throw new Error(result.detail || 'Processing failed');
                    }
                } catch (error) {
                    alert(`❌ Error: ${error.message}`);
                    // Reset upload area
                    document.querySelector('.upload-area h2').textContent = '📷 Upload Shelf Image';
                    document.querySelector('.upload-area p').textContent = 'Click here or drag and drop a retail shelf image';
                }
            }
            
            // Load processing results into UI
            function loadProcessingResults(result) {
                // Set original image
                const imageUrl = URL.createObjectURL(document.getElementById('fileInput').files[0]);
                document.getElementById('originalImage').src = imageUrl;
                document.getElementById('advancedOriginalImage').src = imageUrl;
                
                // Load agent iteration data
                if (result.agent_iterations) {
                    result.agent_iterations.forEach((agent, index) => {
                        const agentNum = index + 1;
                        
                        // Update metrics
                        const accuracyEl = document.getElementById(`agent${agentNum}-accuracy`);
                        const productsEl = document.getElementById(`agent${agentNum}-products`);
                        const timeEl = document.getElementById(`agent${agentNum}-time`);
                        const modelEl = document.getElementById(`agent${agentNum}-model`);
                        
                        if (accuracyEl) accuracyEl.textContent = `${Math.round(agent.accuracy * 100)}%`;
                        if (productsEl) productsEl.textContent = agent.products_found;
                        if (timeEl) timeEl.textContent = `${agent.duration}`;
                        if (modelEl) modelEl.textContent = agent.model_used;
                        
                        // Update improvements and issues
                        const improvementsEl = document.getElementById(`agent${agentNum}-improvements`);
                        const issuesEl = document.getElementById(`agent${agentNum}-issues`);
                        
                        if (improvementsEl && agent.improvements) {
                            improvementsEl.innerHTML = agent.improvements.map(imp => `<li>${imp}</li>`).join('');
                        }
                        
                        if (issuesEl && agent.issues) {
                            issuesEl.innerHTML = agent.issues.map(issue => `<li>${issue}</li>`).join('');
                        }
                        
                        // Update JSON data
                        const jsonEl = document.getElementById(`agent${agentNum}-json`);
                        if (jsonEl && agent.json_data) {
                            jsonEl.classList.remove('loading');
                            jsonEl.textContent = JSON.stringify(agent.json_data, null, 2);
                        }
                    });
                }
            }
            
            // Zoom controls
            function zoomImage(level) {
                zoomLevel = level;
                const images = document.querySelectorAll('.image-viewer img');
                images.forEach(img => {
                    img.style.transform = `scale(${level})`;
                });
            }
            
            function toggleOverlays() {
                overlaysVisible = !overlaysVisible;
                // TODO: Implement overlay toggle
                console.log('Overlays toggled:', overlaysVisible);
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
                    
                    // Store rating
                    console.log(`Rating for ${ratingGroup}: ${rating} stars`);
                }
            });
            
            // Prompt editor
            function openPromptEditor() {
                // TODO: Implement prompt editor modal
                alert('Prompt editor will open here');
            }
            
            // Agent deep dive
            function loadAgentDeepDive() {
                const agentNumber = document.getElementById('agentSelector').value;
                // TODO: Load detailed agent data
                console.log('Loading deep dive for agent:', agentNumber);
            }
            
            // Sidebar functionality
            function toggleSidebar() {
                sidebarOpen = !sidebarOpen;
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebarOverlay');
                const sidebarIcon = document.getElementById('sidebar-icon');
                
                if (sidebarOpen) {
                    sidebar.classList.add('open');
                    overlay.classList.add('active');
                    document.body.classList.add('sidebar-open');
                    sidebarIcon.textContent = '✕';
                    loadImages();
                } else {
                    sidebar.classList.remove('open');
                    overlay.classList.remove('active');
                    document.body.classList.remove('sidebar-open');
                    sidebarIcon.textContent = '📁';
                }
            }
            
            // Load images from API
            async function loadImages() {
                try {
                    // Mock data for now - replace with real API call
                    allImages = generateMockImages();
                    filteredImages = [...allImages];
                    updateImageGrid();
                    updateResultCount();
                } catch (error) {
                    console.error('Error loading images:', error);
                    document.getElementById('resultCount').textContent = 'Error loading images';
                }
            }
            
            // Generate mock images for demonstration
            function generateMockImages() {
                const stores = ['store_001', 'store_002', 'store_003', 'store_004'];
                const categories = ['beverages', 'snacks', 'dairy', 'frozen', 'personal_care'];
                const statuses = ['pending', 'in_progress', 'completed', 'flagged'];
                const storeNames = {
                    'store_001': 'Downtown',
                    'store_002': 'Mall',
                    'store_003': 'Airport',
                    'store_004': 'Suburb'
                };
                
                const images = [];
                for (let i = 1; i <= 150; i++) {
                    const store = stores[Math.floor(Math.random() * stores.length)];
                    const category = categories[Math.floor(Math.random() * categories.length)];
                    const status = statuses[Math.floor(Math.random() * statuses.length)];
                    const date = new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000);
                    
                    images.push({
                        id: `img_${i.toString().padStart(3, '0')}`,
                        title: `${category.charAt(0).toUpperCase() + category.slice(1)} Shelf ${i}`,
                        store: store,
                        storeName: storeNames[store],
                        category: category,
                        status: status,
                        date: date.toISOString().split('T')[0],
                        timestamp: date.toLocaleString(),
                        thumbnail: null // Will be placeholder
                    });
                }
                
                return images.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            }
            
            // Filter images based on search and filters
            function filterImages() {
                const searchTerm = document.getElementById('imageSearch').value.toLowerCase();
                const storeFilter = document.getElementById('storeFilter').value;
                const categoryFilter = document.getElementById('categoryFilter').value;
                const statusFilter = document.getElementById('statusFilter').value;
                const dateFilter = document.getElementById('dateFilter').value;
                
                filteredImages = allImages.filter(image => {
                    const matchesSearch = !searchTerm || 
                        image.title.toLowerCase().includes(searchTerm) ||
                        image.storeName.toLowerCase().includes(searchTerm) ||
                        image.category.toLowerCase().includes(searchTerm);
                    
                    const matchesStore = !storeFilter || image.store === storeFilter;
                    const matchesCategory = !categoryFilter || image.category === categoryFilter;
                    const matchesStatus = !statusFilter || image.status === statusFilter;
                    const matchesDate = !dateFilter || image.date === dateFilter;
                    
                    return matchesSearch && matchesStore && matchesCategory && matchesStatus && matchesDate;
                });
                
                currentPage = 1;
                updateImageGrid();
                updateResultCount();
                updatePagination();
            }
            
            // Update image grid display
            function updateImageGrid() {
                const grid = document.getElementById('imageGrid');
                const startIndex = (currentPage - 1) * imagesPerPage;
                const endIndex = startIndex + imagesPerPage;
                const pageImages = filteredImages.slice(startIndex, endIndex);
                
                grid.innerHTML = pageImages.map(image => `
                    <div class="image-item ${selectedImageId === image.id ? 'selected' : ''}" 
                         onclick="selectImage('${image.id}')" 
                         data-image-id="${image.id}">
                        <div class="image-thumbnail">
                            📷
                        </div>
                        <div class="image-info">
                            <div class="image-title">${image.title}</div>
                            <div class="image-meta">
                                ${image.storeName} • ${image.category}<br>
                                ${image.timestamp}
                            </div>
                            <div class="image-status status-${image.status}">
                                ${image.status.replace('_', ' ')}
                            </div>
                        </div>
                    </div>
                `).join('');
            }
            
            // Select an image
            function selectImage(imageId) {
                selectedImageId = imageId;
                const image = allImages.find(img => img.id === imageId);
                
                if (image) {
                    // Update breadcrumb
                    document.getElementById('breadcrumb').innerHTML = `
                        <span>${image.storeName} → ${image.category} → ${image.title}</span>
                    `;
                    
                    // Update visual selection
                    document.querySelectorAll('.image-item').forEach(item => {
                        item.classList.remove('selected');
                    });
                    document.querySelector(`[data-image-id="${imageId}"]`).classList.add('selected');
                    
                    // Load image data (mock for now)
                    loadImageData(image);
                    
                    // Switch to simple mode and close sidebar
                    switchMode('simple');
                    toggleSidebar();
                }
            }
            
            // Load image data and switch to analysis mode
            function loadImageData(image) {
                // Mock processing results
                const mockResult = {
                    upload_id: image.id,
                    agent_iterations: [
                        {
                            accuracy: 0.73,
                            products_found: 21,
                            duration: '45s',
                            model_used: 'GPT-4o',
                            improvements: ['Basic shelf structure detection', 'Initial product identification'],
                            issues: ['Missing 4 products', 'Price extraction errors', 'Poor positioning accuracy'],
                            json_data: { products: [], structure: {} }
                        },
                        {
                            accuracy: 0.89,
                            products_found: 24,
                            duration: '38s',
                            model_used: 'Claude',
                            improvements: ['Found 3 additional products', 'Fixed price extraction', 'Improved confidence scores'],
                            issues: ['Minor positioning errors', '2 products still missing'],
                            json_data: { products: [], structure: {} }
                        },
                        {
                            accuracy: 0.94,
                            products_found: 25,
                            duration: '22s',
                            model_used: 'Hybrid',
                            improvements: ['Found all products', 'Enhanced spatial positioning', 'Cross-validation complete'],
                            issues: ['Minor confidence variations'],
                            json_data: { products: [], structure: {} }
                        }
                    ]
                };
                
                loadProcessingResults(mockResult);
            }
            
            // Update result count
            function updateResultCount() {
                const count = filteredImages.length;
                const total = allImages.length;
                document.getElementById('resultCount').textContent = 
                    `${count} of ${total} images`;
            }
            
            // Pagination
            function updatePagination() {
                totalPages = Math.ceil(filteredImages.length / imagesPerPage);
                document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
                document.getElementById('prevBtn').disabled = currentPage <= 1;
                document.getElementById('nextBtn').disabled = currentPage >= totalPages;
            }
            
            function loadPreviousPage() {
                if (currentPage > 1) {
                    currentPage--;
                    updateImageGrid();
                    updatePagination();
                }
            }
            
            function loadNextPage() {
                if (currentPage < totalPages) {
                    currentPage++;
                    updateImageGrid();
                    updatePagination();
                }
            }
            
            // View toggle
            function setListView(viewType) {
                document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
                event.target.classList.add('active');
                
                const grid = document.getElementById('imageGrid');
                if (viewType === 'list') {
                    grid.style.gridTemplateColumns = '1fr';
                } else {
                    grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(160px, 1fr))';
                }
            }
            
            // Drag and drop support
            const uploadArea = document.querySelector('.upload-area');
            
            if (uploadArea) {
                uploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    uploadArea.classList.add('dragover');
                });
                
                uploadArea.addEventListener('dragleave', () => {
                    uploadArea.classList.remove('dragover');
                });
                
                uploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    uploadArea.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        document.getElementById('fileInput').files = files;
                        uploadFile();
                    }
                });
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