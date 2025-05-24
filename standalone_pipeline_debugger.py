"""
OnShelf AI Agent Pipeline Debugger - STANDALONE VERSION
Complete multi-stage debugging interface showing every step from image to planogram
"""

import streamlit as st
import json
import pandas as pd
from typing import Dict, Any, List
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="OnShelf AI Agent Pipeline Debugger",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme
st.markdown("""
<style>
.stApp {
    background-color: #1a1b1e;
    color: #ffffff;
}

.stSelectbox > div > div {
    background-color: #2d2d30;
    color: #ffffff;
}

.stTextArea > div > div > textarea {
    background-color: #2d2d30;
    color: #ffffff;
}

.stCode {
    background-color: #1e1e1e !important;
    color: #d4d4d4 !important;
}

.pipeline-stage {
    background-color: #374151;
    border: 2px solid #4b5563;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    text-align: center;
}

.pipeline-stage.success {
    border-color: #10b981;
    background-color: #065f46;
}

.pipeline-stage.warning {
    border-color: #f59e0b;
    background-color: #92400e;
}

.pipeline-stage.error {
    border-color: #ef4444;
    background-color: #991b1b;
}
</style>
""", unsafe_allow_html=True)

# Mock data for demonstration
MOCK_PIPELINE_DATA = {
    "upload_id": "abc123",
    "processing_status": {
        "current_stage": 3,
        "iteration": 3,
        "max_iterations": 5,
        "accuracy": 0.945,
        "cost": 0.67,
        "status": "processing",
        "current_task": "Cross-validating product positions with enhanced spatial model",
        "ai_reasoning": "Detected 2 position conflicts. Switching to Claude-4 for spatial analysis...",
        "next_action": "Regenerating planogram with corrected coordinates"
    },
    "model_results": {
        "claude-4-sonnet": {
            "stage": "Structure Analysis",
            "accuracy": 0.98,
            "confidence": 0.95,
            "processing_time": 2.3,
            "products_detected": 15,
            "structure_confidence": 0.98,
            "results": {
                "shelf_count": 4,
                "height": "2.1m",
                "width": "1.5m",
                "shelves": [
                    {"id": 1, "height": 0.4, "products": 3},
                    {"id": 2, "height": 0.4, "products": 4},
                    {"id": 3, "height": 0.4, "products": 4},
                    {"id": 4, "height": 0.4, "products": 4}
                ]
            }
        },
        "gpt-4o": {
            "stage": "Product Extraction",
            "accuracy": 0.89,
            "confidence": 0.87,
            "processing_time": 1.8,
            "products_detected": 14,
            "structure_confidence": 0.85,
            "results": {
                "products": [
                    {"name": "Coca-Cola Original 330ml", "price": 1.25, "confidence": 0.96, "shelf": 2},
                    {"name": "Pepsi Max 330ml", "price": 1.89, "confidence": 0.82, "shelf": 2},
                    {"name": "Red Bull Energy 250ml", "price": 1.89, "confidence": 0.91, "shelf": 4},
                    {"name": "Monster Energy Ultra", "price": 2.15, "confidence": 0.87, "shelf": 3}
                ]
            }
        },
        "gemini-2.5-flash": {
            "stage": "OCR & Validation",
            "accuracy": 0.87,
            "confidence": 0.83,
            "processing_time": 1.2,
            "products_detected": 13,
            "structure_confidence": 0.89,
            "results": {
                "ocr_results": [
                    {"text": "Coca-Cola", "confidence": 0.98, "position": {"x": 120, "y": 340}},
                    {"text": "£1.25", "confidence": 0.94, "position": {"x": 125, "y": 380}},
                    {"text": "Pepsi", "confidence": 0.85, "position": {"x": 220, "y": 340}}
                ]
            }
        }
    },
    "orchestrator_decisions": [
        {
            "title": "Model Selection for Structure Analysis",
            "context": "Initial shelf structure detection with 3 available models",
            "options": ["claude-4-sonnet", "gpt-4o", "gemini-2.5-flash"],
            "chosen_option": "claude-4-sonnet",
            "reasoning": "Claude-4 has highest accuracy (98%) for spatial analysis tasks",
            "confidence_breakdown": {"claude-4-sonnet": 0.95, "gpt-4o": 0.89, "gemini-2.5-flash": 0.83},
            "accuracy_impact": 0.06,
            "cost_impact": 0.15
        },
        {
            "title": "Conflict Resolution Strategy",
            "context": "Detected conflicting product positions between models",
            "options": ["Use highest confidence", "Cross-validate", "Human review"],
            "chosen_option": "Cross-validate",
            "reasoning": "Multiple conflicts detected, cross-validation will improve accuracy",
            "confidence_breakdown": {"Use highest confidence": 0.7, "Cross-validate": 0.92, "Human review": 0.85},
            "accuracy_impact": 0.08,
            "cost_impact": 0.23
        }
    ],
    "processing_steps": [
        {
            "name": "Image Preprocessing",
            "status": "completed",
            "duration": 0.8,
            "success_rate": 0.98,
            "input_data": {"image_size": "1920x1080", "format": "JPEG"},
            "output_data": {"processed_size": "1920x1080", "quality_score": 0.94},
            "logs": [
                {"level": "INFO", "timestamp": "10:15:01", "message": "Image loaded successfully"},
                {"level": "INFO", "timestamp": "10:15:02", "message": "Quality enhancement applied"}
            ],
            "api_calls": 0,
            "tokens_used": 0,
            "memory_mb": 45,
            "error_rate": 0.02
        },
        {
            "name": "Structure Detection",
            "status": "completed",
            "duration": 2.3,
            "success_rate": 0.95,
            "input_data": {"model": "claude-4-sonnet", "confidence_threshold": 0.8},
            "output_data": {"shelves_detected": 4, "confidence": 0.98},
            "logs": [
                {"level": "INFO", "timestamp": "10:15:03", "message": "Starting structure analysis"},
                {"level": "INFO", "timestamp": "10:15:05", "message": "4 shelves detected with high confidence"}
            ],
            "api_calls": 1,
            "tokens_used": 1250,
            "memory_mb": 67,
            "error_rate": 0.05
        },
        {
            "name": "Product Extraction",
            "status": "processing",
            "duration": 1.8,
            "success_rate": 0.89,
            "input_data": {"model": "gpt-4o", "products_to_extract": 15},
            "output_data": {"products_found": 14, "confidence": 0.87},
            "logs": [
                {"level": "INFO", "timestamp": "10:15:06", "message": "Starting product extraction"},
                {"level": "WARNING", "timestamp": "10:15:07", "message": "Low confidence on 2 products"}
            ],
            "api_calls": 1,
            "tokens_used": 2100,
            "memory_mb": 89,
            "error_rate": 0.11
        }
    ],
    "planogram_data": {
        "shelves": [
            {
                "number": 1,
                "products": [
                    {"name": "Sprite 330ml", "price": 1.15, "facings": 2, "status": "mismatch", "confidence": 0.88},
                    {"name": "MISSING PRODUCT", "price": 0, "facings": 0, "status": "missing", "confidence": 0.0}
                ]
            },
            {
                "number": 2,
                "products": [
                    {"name": "Coca-Cola Original 330ml", "price": 1.45, "facings": 6, "status": "correct", "confidence": 0.96},
                    {"name": "Pepsi Max 330ml", "price": 1.89, "facings": 3, "status": "mismatch", "confidence": 0.82}
                ]
            },
            {
                "number": 3,
                "products": [
                    {"name": "Monster Energy Ultra", "price": 2.15, "facings": 3, "status": "correct", "confidence": 0.87},
                    {"name": "Rockstar Energy", "price": 1.99, "facings": 4, "status": "correct", "confidence": 0.91}
                ]
            },
            {
                "number": 4,
                "products": [
                    {"name": "Empty Space", "price": 0, "facings": 0, "status": "empty", "confidence": 0.0},
                    {"name": "Red Bull Energy 250ml", "price": 1.89, "facings": 6, "status": "correct", "confidence": 0.91}
                ]
            }
        ]
    },
    "extraction_json": {
        "upload_id": "abc123",
        "extraction_results": {
            "structure": {
                "shelf_count": 4,
                "height": "2.1m",
                "width": "1.5m",
                "confidence": 0.98
            },
            "products": [
                {
                    "id": "p5",
                    "name": "Coca-Cola Original 330ml",
                    "brand": "Coca-Cola",
                    "price": 1.25,
                    "shelf": 2,
                    "section": "left",
                    "facings": 6,
                    "confidence": 0.96,
                    "coordinates": {"x": 120, "y": 340, "width": 180, "height": 240}
                }
            ]
        }
    }
}

def render_master_orchestrator():
    """Master Orchestrator with real-time processing status"""
    
    processing_status = MOCK_PIPELINE_DATA["processing_status"]
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; margin-bottom: 20px; color: white;'>
        <h2 style='margin: 0;'>🧠 MASTER ORCHESTRATOR</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
    
    with col1:
        st.metric("Current Stage", f"{processing_status['current_stage']}/4")
        
    with col2:
        st.metric("Iteration", f"{processing_status['iteration']}/{processing_status['max_iterations']}")
        
    with col3:
        st.metric("Overall Accuracy", f"{processing_status['accuracy']:.1%}")
        
    with col4:
        st.metric("API Cost", f"£{processing_status['cost']:.2f}")
        
    with col5:
        status_color = "🟢" if processing_status['status'] == 'success' else "🟡" if processing_status['status'] == 'processing' else "🔴"
        st.metric("Status", f"{status_color} {processing_status['status'].title()}")
    
    # Current processing details
    if processing_status['status'] == 'processing':
        st.info(f"**Current Task**: {processing_status['current_task']}")
        st.info(f"**AI Reasoning**: {processing_status['ai_reasoning']}")
        st.info(f"**Next Action**: {processing_status['next_action']}")

def render_pipeline_debugging():
    """Pipeline debugging showing each stage with individual results"""
    
    st.markdown("## 🔍 PIPELINE DEBUGGING")
    st.markdown("### 📊 Processing Pipeline Overview")
    
    # Pipeline stages as cards
    stage_cols = st.columns(4)
    
    stages = [
        {"name": "Structure", "model": "claude-4-sonnet", "accuracy": 0.98},
        {"name": "Products", "model": "gpt-4o", "accuracy": 0.89},
        {"name": "Validation", "model": "cross-check", "accuracy": 0.94},
        {"name": "Final Result", "model": "combined", "accuracy": 0.945}
    ]
    
    for i, stage in enumerate(stages):
        with stage_cols[i]:
            status_color = "#10b981" if stage['accuracy'] > 0.9 else "#f59e0b" if stage['accuracy'] > 0.8 else "#ef4444"
            
            st.markdown(f"""
            <div style='background: {status_color}; color: white; padding: 15px; 
                       border-radius: 8px; text-align: center; margin: 5px 0;'>
                <h4 style='margin: 0;'>{stage['name']}</h4>
                <p style='margin: 5px 0;'>{stage['model']}</p>
                <h3 style='margin: 0;'>{stage['accuracy']:.1%}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"📋 View {stage['name']} Details", key=f"stage_{i}"):
                st.session_state.selected_stage = stage['name']
    
    # Pipeline flow visualization
    st.markdown("### 🔄 Processing Flow")
    st.text("📥 Input Image → 🔍 Structure → 📦 Products → ✅ Validation → 🏗️ Planogram")
    
    # Individual stage results
    st.markdown("### 📑 Individual Stage Results")
    
    selected_stage = st.selectbox(
        "Select Stage to Inspect:",
        ["Structure Analysis", "Product Extraction", "Validation & Cross-Check", "Final Assembly"]
    )
    
    if selected_stage == "Structure Analysis":
        st.json(MOCK_PIPELINE_DATA["model_results"]["claude-4-sonnet"]["results"])
    elif selected_stage == "Product Extraction":
        st.json(MOCK_PIPELINE_DATA["model_results"]["gpt-4o"]["results"])

def render_model_comparison():
    """Model comparison showing side-by-side outputs"""
    
    st.markdown("## 🤖 MODEL COMPARISON")
    st.markdown("### 🔍 Model Output Comparison")
    
    # Model selector
    col1, col2, col3 = st.columns(3)
    
    with col1:
        model_a = st.selectbox("Model A:", ["claude-4-sonnet", "gpt-4o", "gemini-2.5-flash"], key="model_a")
    
    with col2:
        model_b = st.selectbox("Model B:", ["gpt-4o", "claude-4-sonnet", "gemini-2.5-flash"], key="model_b")
    
    with col3:
        comparison_type = st.selectbox("Compare:", ["Structure", "Products", "Confidence", "JSON Output"])
    
    # Side-by-side comparison
    comp_col1, comp_col2 = st.columns(2)
    
    with comp_col1:
        st.markdown(f"#### {model_a.upper()} Results")
        model_a_results = MOCK_PIPELINE_DATA["model_results"].get(model_a, {})
        st.json(model_a_results)
        
        if model_a_results:
            st.metric("Accuracy", f"{model_a_results.get('accuracy', 0):.1%}")
            st.metric("Confidence", f"{model_a_results.get('confidence', 0):.1%}")
            st.metric("Processing Time", f"{model_a_results.get('processing_time', 0):.1f}s")
    
    with comp_col2:
        st.markdown(f"#### {model_b.upper()} Results")
        model_b_results = MOCK_PIPELINE_DATA["model_results"].get(model_b, {})
        st.json(model_b_results)
        
        if model_b_results:
            st.metric("Accuracy", f"{model_b_results.get('accuracy', 0):.1%}")
            st.metric("Confidence", f"{model_b_results.get('confidence', 0):.1%}")
            st.metric("Processing Time", f"{model_b_results.get('processing_time', 0):.1f}s")

def render_orchestrator_decisions():
    """Show how the AI orchestrator makes decisions"""
    
    st.markdown("## 🧠 AI ORCHESTRATOR DECISIONS")
    st.markdown("### 🤖 Orchestrator Decision Tree")
    
    decisions = MOCK_PIPELINE_DATA["orchestrator_decisions"]
    
    for i, decision in enumerate(decisions):
        with st.expander(f"Decision {i+1}: {decision['title']}", expanded=(i == len(decisions)-1)):
            
            st.markdown(f"**Context**: {decision['context']}")
            st.markdown(f"**Available Options**: {', '.join(decision['options'])}")
            st.markdown(f"**Decision**: {decision['chosen_option']}")
            st.markdown(f"**Reasoning**: {decision['reasoning']}")
            
            # Confidence breakdown chart
            confidence_data = decision['confidence_breakdown']
            
            fig = go.Figure(data=go.Bar(
                x=list(confidence_data.keys()),
                y=list(confidence_data.values()),
                marker_color=['#10b981' if v == max(confidence_data.values()) else '#6b7280' for v in confidence_data.values()]
            ))
            
            fig.update_layout(
                title="Decision Confidence Scores",
                xaxis_title="Options",
                yaxis_title="Confidence Score",
                height=300,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown(f"**Impact on Accuracy**: {decision['accuracy_impact']:+.1%}")
            st.markdown(f"**Cost Impact**: £{decision['cost_impact']:+.3f}")

def render_step_by_step_processing():
    """Step-by-step processing view with intermediate outputs"""
    
    st.markdown("## 📋 STEP-BY-STEP PROCESSING")
    st.markdown("### 📋 Processing Steps")
    
    steps = MOCK_PIPELINE_DATA["processing_steps"]
    
    for i, step in enumerate(steps):
        
        # Step header
        step_col1, step_col2, step_col3 = st.columns([6, 2, 2])
        
        with step_col1:
            status_icon = "✅" if step['status'] == 'completed' else "🔄" if step['status'] == 'processing' else "⏳"
            st.markdown(f"#### {status_icon} Step {i+1}: {step['name']}")
        
        with step_col2:
            st.metric("Duration", f"{step['duration']:.1f}s")
        
        with step_col3:
            st.metric("Success Rate", f"{step['success_rate']:.1%}")
        
        # Step details
        with st.expander(f"View Step {i+1} Details", expanded=False):
            
            # Input/Output
            input_col, output_col = st.columns(2)
            
            with input_col:
                st.markdown("**Input Data:**")
                st.json(step['input_data'])
            
            with output_col:
                st.markdown("**Output Data:**")
                st.json(step['output_data'])
            
            # Processing logs
            st.markdown("**Processing Logs:**")
            for log in step['logs']:
                log_level_color = {"INFO": "🔵", "WARNING": "🟡", "ERROR": "🔴"}.get(log['level'], "⚪")
                st.text(f"{log_level_color} {log['timestamp']} - {log['message']}")
            
            # Performance metrics
            st.markdown("**Performance Metrics:**")
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("API Calls", step['api_calls'])
            with metric_col2:
                st.metric("Tokens Used", step['tokens_used'])
            with metric_col3:
                st.metric("Memory Usage", f"{step['memory_mb']} MB")
            with metric_col4:
                st.metric("Error Rate", f"{step['error_rate']:.1%}")

def render_main_panels():
    """Render the main 4 panels"""
    col1, col2, col3, col4 = st.columns([3, 3, 3, 2])
    
    with col1:
        render_original_image_panel()
    
    with col2:
        render_interactive_planogram_panel()
    
    with col3:
        render_raw_json_panel()
    
    with col4:
        render_ai_configuration_panel()

def render_original_image_panel():
    """Original image panel with detection overlays"""
    st.markdown("### 📷 Original Image Analysis")
    
    # Display options
    display_options = st.multiselect(
        "Display Options:",
        ["AI Detections", "Confidence Scores", "Bounding Boxes", "Product Labels", "Shelf Lines"],
        default=["AI Detections", "Confidence Scores"]
    )
    
    # Placeholder image
    st.info("📷 Original shelf image would be displayed here with AI detection overlays")
    
    # Detection analysis
    with st.expander("🔍 Detection Analysis", expanded=False):
        detections = [
            {"name": "Coca-Cola", "confidence": 0.96, "x": 120, "y": 340},
            {"name": "Pepsi", "confidence": 0.82, "x": 220, "y": 340},
            {"name": "Red Bull", "confidence": 0.91, "x": 320, "y": 340}
        ]
        
        detection_df = pd.DataFrame(detections)
        st.dataframe(detection_df)
        
        st.metric("Total Detections", len(detections))
        st.metric("Avg Confidence", f"{detection_df['confidence'].mean():.1%}")
        st.metric("High Confidence (>90%)", len(detection_df[detection_df['confidence'] > 0.9]))

def render_interactive_planogram_panel():
    """Interactive planogram with editing capabilities"""
    st.markdown("### 🏗️ Interactive Planogram")
    
    # Planogram controls
    planogram_col1, planogram_col2, planogram_col3 = st.columns([2, 2, 2])
    
    with planogram_col1:
        if st.button("➕ Add Product", key="add_product"):
            st.success("Add product dialog would open")
    
    with planogram_col2:
        if st.button("✏️ Edit Selected", key="edit_product"):
            st.success("Edit product dialog would open")
    
    with planogram_col3:
        if st.button("🗑️ Remove Selected", key="remove_product"):
            st.success("Product removed")
    
    # Planogram visualization
    planogram_data = MOCK_PIPELINE_DATA["planogram_data"]
    
    st.markdown("#### 📋 Shelf Breakdown")
    for shelf in planogram_data.get('shelves', []):
        with st.expander(f"Shelf {shelf['number']} ({len(shelf['products'])} products)"):
            for product in shelf['products']:
                status_icon = "🟩" if product['status'] == 'correct' else "🟨" if product['status'] == 'mismatch' else "🟥"
                st.write(f"{status_icon} **{product['name']}** - £{product['price']} - {product['facings']} facings - {product['confidence']:.1%}")

def render_raw_json_panel():
    """JSON panel with editing capabilities"""
    st.markdown("### 📋 Raw JSON Data")
    
    raw_data = MOCK_PIPELINE_DATA["extraction_json"]
    
    # JSON editor tabs
    json_tab1, json_tab2, json_tab3, json_tab4 = st.tabs(["📋 Full Data", "🏗️ Structure", "📦 Products", "✏️ Editor"])
    
    with json_tab1:
        st.code(json.dumps(raw_data, indent=2), language='json')
    
    with json_tab2:
        if 'structure' in raw_data.get('extraction_results', {}):
            st.code(json.dumps(raw_data['extraction_results']['structure'], indent=2), language='json')
    
    with json_tab3:
        if 'products' in raw_data.get('extraction_results', {}):
            st.code(json.dumps(raw_data['extraction_results']['products'], indent=2), language='json')
    
    with json_tab4:
        st.markdown("**Edit JSON Data:**")
        edited_json = st.text_area(
            "JSON Editor:",
            value=json.dumps(raw_data, indent=2),
            height=400,
            key="json_editor"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Validate JSON", key="validate_json"):
                try:
                    json.loads(edited_json)
                    st.success("✅ Valid JSON")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON: {e}")
        
        with col2:
            if st.button("💾 Save Changes", key="save_json"):
                st.success("JSON changes saved successfully")
        
        with col3:
            if st.button("🔄 Regenerate Planogram", key="regen_planogram"):
                st.success("Planogram regenerated from JSON")
    
    # Download options
    st.download_button(
        label="💾 Download Full JSON",
        data=json.dumps(raw_data, indent=2),
        file_name=f"extraction_{raw_data.get('upload_id', 'unknown')}.json",
        mime="application/json"
    )

def render_ai_configuration_panel():
    """AI configuration with advanced options"""
    st.markdown("### ⚙️ AI Configuration")
    
    # Model selection with performance indicators
    st.markdown("**Model Selection & Performance:**")
    
    models_data = [
        {"name": "claude-4-sonnet", "accuracy": 0.95, "cost": 0.45, "speed": 2.3},
        {"name": "gpt-4o", "accuracy": 0.89, "cost": 0.32, "speed": 1.8},
        {"name": "gemini-2.5-flash", "accuracy": 0.87, "cost": 0.18, "speed": 1.2}
    ]
    
    for model in models_data:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
        
        with col1:
            st.selectbox(f"{model['name']}:", [model['name']], key=f"model_{model['name']}")
        
        with col2:
            st.metric("Accuracy", f"{model['accuracy']:.1%}")
        
        with col3:
            st.metric("Cost", f"£{model['cost']}")
        
        with col4:
            st.metric("Speed", f"{model['speed']}s")
    
    # Advanced configuration
    with st.expander("🔧 Advanced Configuration", expanded=False):
        
        st.slider("Confidence Threshold", 0.0, 1.0, 0.8, 0.05, key="confidence_threshold")
        st.slider("Max Iterations", 1, 10, 5, 1, key="max_iterations")
        st.slider("Cost Limit (£)", 0.0, 5.0, 1.0, 0.1, key="cost_limit")
        
        st.multiselect(
            "Processing Steps:",
            ["Structure Analysis", "Product Detection", "OCR", "Validation", "Cross-Reference"],
            default=["Structure Analysis", "Product Detection", "OCR", "Validation"]
        )
        
        st.text_area(
            "Custom System Prompt:",
            value="You are an expert retail shelf analyzer...",
            height=100,
            key="custom_prompt"
        )
    
    # Action buttons
    st.markdown("---")
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("⚡ Re-extract with Config", type="primary", use_container_width=True):
            st.success("Re-extraction started with current configuration")
    
    with action_col2:
        if st.button("🧪 Run A/B Test", use_container_width=True):
            st.success("Advanced A/B test initiated")

# Main application
def main():
    # Header
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h2 style='color: white; margin: 0;'>🔍 OnShelf ADMIN Pipeline Debugging Tool</h2>
        <p style='color: #e5e7eb; margin: 5px 0 0 0;'>Complete multi-stage debugging - from image to planogram</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload selector
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        selected_upload = st.selectbox(
            "Upload ID:",
            ["abc123 - Tesco Express Camden High Street", 
             "def456 - Sainsbury's Local Kings Road",
             "ghi789 - Co-op Richmond Park",
             "06701796-e1f5-4951-abe8-f229a166997b - Live Processing"],
            key="upload_selector"
        )
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_btn"):
            st.rerun()
    
    with col3:
        if st.button("📊 Export All", key="export_all"):
            st.success("📥 Complete debug data exported")
    
    with col4:
        if st.button("🚨 Alert", key="alert_btn"):
            st.warning("⚠️ Alert sent to monitoring team")
    
    st.markdown("---")
    
    # Master Orchestrator
    render_master_orchestrator()
    
    # Main content panels
    render_main_panels()
    
    # Pipeline debugging sections
    render_pipeline_debugging()
    render_model_comparison()
    render_orchestrator_decisions()
    render_step_by_step_processing()
    
    # Enhanced debugging controls
    st.markdown("---")
    st.markdown("### 🔧 Advanced Debug Controls")
    
    debug_col1, debug_col2, debug_col3, debug_col4, debug_col5 = st.columns(5)
    
    with debug_col1:
        if st.button("🏃 Force Re-run", type="primary", key="force_rerun"):
            st.success("✅ Complete pipeline re-run initiated")
    
    with debug_col2:
        if st.button("⚡ Quick Fix", key="quick_fix"):
            st.info("🔧 Auto-fixing detected issues across all stages")
    
    with debug_col3:
        if st.button("🔀 Model Switch", key="model_switch"):
            st.info("🤖 Switching to backup model configuration")
    
    with debug_col4:
        if st.button("📊 Export Pipeline", key="export_pipeline"):
            st.info("📥 Exporting complete pipeline data and logs")
    
    with debug_col5:
        if st.button("🚨 Human Review", key="human_review"):
            st.warning("⚠️ Escalating to human review with full context")
    
    # Performance metrics footer
    st.markdown("---")
    
    perf_col1, perf_col2, perf_col3, perf_col4, perf_col5 = st.columns(5)
    
    with perf_col1:
        st.metric("Total Processing Time", "12.4s", delta="-2.1s")
    
    with perf_col2:
        st.metric("API Cost", "£0.67", delta="+£0.12")
    
    with perf_col3:
        st.metric("Overall Accuracy", "94.5%", delta="+3.2%")
    
    with perf_col4:
        st.metric("Iterations Used", "3/5", delta="0")
    
    with perf_col5:
        st.metric("Confidence Score", "94.5%", delta="+1.8%")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6b7280; font-size: 12px;'>
    OnShelf AI Agent Pipeline Debugger v1.2.0 | Connected to Production Database | 
    Real-time Pipeline Debugging | 
    <a href='https://github.com/andreaonshelf/onshelf-ai-agent' style='color: #3b82f6;'>GitHub</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 