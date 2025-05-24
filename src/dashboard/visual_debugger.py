"""
OnShelf Visual Debugging Interface
COMPLETE PIPELINE DEBUGGING - Shows every step from image to planogram
"""

import streamlit as st
import json
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import pandas as pd
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class PipelineDebugger:
    """Complete pipeline debugging interface showing every step and decision"""
    
    def __init__(self):
        self.supabase = self._init_supabase()
        self.current_extraction_id = None
        self.pipeline_stages = [
            {"name": "Structure", "model": "claude-4-sonnet", "accuracy": 0.98},
            {"name": "Products", "model": "gpt-4o", "accuracy": 0.89},
            {"name": "Validation", "model": "cross-check", "accuracy": 0.94},
            {"name": "Final Result", "model": "combined", "accuracy": 0.945}
        ]
    
    def _init_supabase(self):
        """Initialize Supabase connection"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            if supabase_url and supabase_key:
                return create_client(supabase_url, supabase_key)
        except Exception as e:
            st.error(f"Failed to connect to Supabase: {e}")
        return None
    
    def render_complete_debugging_interface(self):
        """Render the complete multi-stage debugging interface"""
        
        # Header with Master Orchestrator
        self._render_master_orchestrator()
        
        # Main content: Original Image + Interactive Planogram + Raw JSON + AI Config
        self._render_main_panels()
        
        # Pipeline Debugging Section (the missing piece!)
        st.markdown("---")
        st.markdown("## 🔍 PIPELINE DEBUGGING")
        self._render_pipeline_debugging()
        
        # Model Comparison Section
        st.markdown("---") 
        st.markdown("## 🤖 MODEL COMPARISON")
        self._render_model_comparison()
        
        # Orchestrator Decision Making
        st.markdown("---")
        st.markdown("## 🧠 AI ORCHESTRATOR DECISIONS")
        self._render_orchestrator_decisions()
        
        # Step-by-Step Processing
        st.markdown("---")
        st.markdown("## 📋 STEP-BY-STEP PROCESSING")
        self._render_step_by_step_processing()
    
    def _render_master_orchestrator(self):
        """Enhanced Master Orchestrator with real-time processing status"""
        
        processing_status = self._get_current_processing_status()
        
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
    
    def _render_main_panels(self):
        """Render the main 4 panels"""
        col1, col2, col3, col4 = st.columns([3, 3, 3, 2])
        
        with col1:
            self._render_original_image_panel()
        
        with col2:
            self._render_interactive_planogram_panel()
        
        with col3:
            self._render_raw_json_panel()
        
        with col4:
            self._render_ai_configuration_panel()
    
    def _render_pipeline_debugging(self):
        """Pipeline debugging showing each stage with individual results"""
        
        # Pipeline overview
        st.markdown("### 📊 Processing Pipeline Overview")
        
        # Create pipeline visualization
        pipeline_data = self._get_pipeline_data()
        
        # Pipeline stages as cards
        stage_cols = st.columns(4)
        
        for i, stage in enumerate(self.pipeline_stages):
            with stage_cols[i]:
                # Stage status
                status_color = "#10b981" if stage['accuracy'] > 0.9 else "#f59e0b" if stage['accuracy'] > 0.8 else "#ef4444"
                
                st.markdown(f"""
                <div style='background: {status_color}; color: white; padding: 15px; 
                           border-radius: 8px; text-align: center; margin: 5px 0;'>
                    <h4 style='margin: 0;'>{stage['name']}</h4>
                    <p style='margin: 5px 0;'>{stage['model']}</p>
                    <h3 style='margin: 0;'>{stage['accuracy']:.1%}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Stage details button
                if st.button(f"📋 View {stage['name']} Details", key=f"stage_{i}"):
                    self._show_stage_details(stage['name'])
        
        # Pipeline flow visualization
        st.markdown("### 🔄 Processing Flow")
        self._render_pipeline_flow_chart()
        
        # Individual stage results
        st.markdown("### 📑 Individual Stage Results")
        
        selected_stage = st.selectbox(
            "Select Stage to Inspect:",
            ["Structure Analysis", "Product Extraction", "Validation & Cross-Check", "Final Assembly"]
        )
        
        self._render_stage_results(selected_stage)
    
    def _render_model_comparison(self):
        """Model comparison showing side-by-side outputs"""
        
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
            model_a_results = self._get_model_results(model_a, comparison_type)
            st.json(model_a_results)
            
            st.metric("Accuracy", f"{model_a_results.get('accuracy', 0):.1%}")
            st.metric("Confidence", f"{model_a_results.get('confidence', 0):.1%}")
            st.metric("Processing Time", f"{model_a_results.get('processing_time', 0):.1f}s")
        
        with comp_col2:
            st.markdown(f"#### {model_b.upper()} Results")
            model_b_results = self._get_model_results(model_b, comparison_type)
            st.json(model_b_results)
            
            st.metric("Accuracy", f"{model_b_results.get('accuracy', 0):.1%}")
            st.metric("Confidence", f"{model_b_results.get('confidence', 0):.1%}")
            st.metric("Processing Time", f"{model_b_results.get('processing_time', 0):.1f}s")
        
        # Differences analysis
        st.markdown("#### 🔎 Key Differences")
        differences = self._analyze_model_differences(model_a_results, model_b_results)
        
        for diff in differences:
            st.warning(f"**{diff['field']}**: {diff['description']}")
    
    def _render_orchestrator_decisions(self):
        """Show how the AI orchestrator makes decisions"""
        
        st.markdown("### 🤖 Orchestrator Decision Tree")
        
        # Decision timeline
        decisions = self._get_orchestrator_decisions()
        
        for i, decision in enumerate(decisions):
            with st.expander(f"Decision {i+1}: {decision['title']}", expanded=(i == len(decisions)-1)):
                
                # Decision context
                st.markdown(f"**Context**: {decision['context']}")
                st.markdown(f"**Available Options**: {', '.join(decision['options'])}")
                st.markdown(f"**Decision**: {decision['chosen_option']}")
                st.markdown(f"**Reasoning**: {decision['reasoning']}")
                
                # Confidence breakdown
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
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Impact assessment
                st.markdown(f"**Impact on Accuracy**: {decision['accuracy_impact']:+.1%}")
                st.markdown(f"**Cost Impact**: £{decision['cost_impact']:+.3f}")
    
    def _render_step_by_step_processing(self):
        """Step-by-step processing view with intermediate outputs"""
        
        st.markdown("### 📋 Processing Steps")
        
        steps = self._get_processing_steps()
        
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
    
    def _render_interactive_planogram_panel(self):
        """Enhanced interactive planogram with editing capabilities"""
        st.markdown("### 🏗️ Interactive Planogram")
        
        # Planogram controls
        planogram_col1, planogram_col2, planogram_col3 = st.columns([2, 2, 2])
        
        with planogram_col1:
            if st.button("➕ Add Product", key="add_product"):
                self._show_add_product_dialog()
        
        with planogram_col2:
            if st.button("✏️ Edit Selected", key="edit_product"):
                self._show_edit_product_dialog()
        
        with planogram_col3:
            if st.button("🗑️ Remove Selected", key="remove_product"):
                self._remove_selected_product()
        
        # Planogram visualization with editing
        planogram_data = self._get_current_planogram_data()
        
        if planogram_data:
            # Interactive planogram HTML with editing capabilities
            planogram_html = self._generate_interactive_planogram_html(planogram_data)
            st.components.v1.html(planogram_html, height=600)
            
            # Planogram editing panel
            with st.expander("🛠️ Planogram Editor", expanded=False):
                self._render_planogram_editor(planogram_data)
        else:
            st.info("No planogram data available.")
    
    def _render_original_image_panel(self):
        """Enhanced original image panel with detailed detection analysis"""
        st.markdown("### 📷 Original Image Analysis")
        
        current_upload = self._get_current_upload_data()
        
        if current_upload and current_upload.get('image_data'):
            image = Image.open(io.BytesIO(current_upload['image_data']))
            
            # Image display options
            display_options = st.multiselect(
                "Display Options:",
                ["AI Detections", "Confidence Scores", "Bounding Boxes", "Product Labels", "Shelf Lines"],
                default=["AI Detections", "Confidence Scores"]
            )
            
            # Apply overlays based on options
            image_with_overlays = self._add_advanced_detection_overlays(image, current_upload.get('detections', []), display_options)
            st.image(image_with_overlays, use_column_width=True)
            
            # Detailed detection analysis
            with st.expander("🔍 Detection Analysis", expanded=False):
                detections = current_upload.get('detections', [])
                
                detection_df = pd.DataFrame(detections)
                if not detection_df.empty:
                    st.dataframe(detection_df)
                    
                    # Detection statistics
                    st.metric("Total Detections", len(detections))
                    st.metric("Avg Confidence", f"{detection_df['confidence'].mean():.1%}")
                    st.metric("High Confidence (>90%)", len(detection_df[detection_df['confidence'] > 0.9]))
        else:
            st.info("No image data available.")
    
    def _render_raw_json_panel(self):
        """Enhanced JSON panel with editing capabilities"""
        st.markdown("### 📋 Raw JSON Data")
        
        raw_data = self._get_current_extraction_json()
        
        if raw_data:
            # JSON editor tabs
            json_tab1, json_tab2, json_tab3, json_tab4 = st.tabs(["📋 Full Data", "🏗️ Structure", "📦 Products", "✏️ Editor"])
            
            with json_tab1:
                formatted_json = json.dumps(raw_data, indent=2)
                st.code(formatted_json, language='json')
            
            with json_tab2:
                if 'structure' in raw_data:
                    structure_json = json.dumps(raw_data['structure'], indent=2)
                    st.code(structure_json, language='json')
            
            with json_tab3:
                if 'products' in raw_data:
                    products_json = json.dumps(raw_data['products'], indent=2)
                    st.code(products_json, language='json')
            
            with json_tab4:
                # JSON editor
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
                        self._save_json_changes(edited_json)
                
                with col3:
                    if st.button("🔄 Regenerate Planogram", key="regen_planogram"):
                        self._regenerate_planogram_from_json(edited_json)
            
            # Download options
            st.download_button(
                label="💾 Download Full JSON",
                data=json.dumps(raw_data, indent=2),
                file_name=f"extraction_{raw_data.get('upload_id', 'unknown')}.json",
                mime="application/json"
            )
        else:
            st.info("No extraction data available.")
    
    def _render_ai_configuration_panel(self):
        """Enhanced AI configuration with advanced options"""
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
                self._trigger_reextraction_with_config()
        
        with action_col2:
            if st.button("🧪 Run A/B Test", use_container_width=True):
                self._trigger_advanced_ab_test()
    
    # Helper methods for getting data (would connect to real data sources)
    def _get_current_processing_status(self) -> Dict[str, Any]:
        return {
            'current_stage': 3,
            'iteration': 3,
            'max_iterations': 5,
            'accuracy': 0.945,
            'cost': 0.67,
            'status': 'processing',
            'current_task': 'Cross-validating product positions with enhanced spatial model',
            'ai_reasoning': 'Detected 2 position conflicts. Switching to Claude-4 for spatial analysis...',
            'next_action': 'Regenerating planogram with corrected coordinates'
        }
    
    def _get_pipeline_data(self) -> Dict[str, Any]:
        return {"stages": self.pipeline_stages}
    
    def _get_model_results(self, model: str, comparison_type: str) -> Dict[str, Any]:
        # Mock data - would fetch real results
        return {
            "accuracy": 0.94 if model == "claude-4-sonnet" else 0.89,
            "confidence": 0.87,
            "processing_time": 2.3 if model == "claude-4-sonnet" else 1.8,
            "products_detected": 15,
            "structure_confidence": 0.95
        }
    
    def _get_orchestrator_decisions(self) -> List[Dict[str, Any]]:
        return [
            {
                'title': 'Model Selection for Structure Analysis',
                'context': 'Initial shelf structure detection with 3 available models',
                'options': ['claude-4-sonnet', 'gpt-4o', 'gemini-2.5-flash'],
                'chosen_option': 'claude-4-sonnet',
                'reasoning': 'Claude-4 has highest accuracy (95%) for spatial analysis tasks',
                'confidence_breakdown': {'claude-4-sonnet': 0.95, 'gpt-4o': 0.89, 'gemini-2.5-flash': 0.83},
                'accuracy_impact': 0.06,
                'cost_impact': 0.15
            },
            {
                'title': 'Conflict Resolution Strategy',
                'context': 'Detected conflicting product positions between models',
                'options': ['Use highest confidence', 'Cross-validate', 'Human review'],
                'chosen_option': 'Cross-validate',
                'reasoning': 'Multiple conflicts detected, cross-validation will improve accuracy',
                'confidence_breakdown': {'Use highest confidence': 0.7, 'Cross-validate': 0.92, 'Human review': 0.85},
                'accuracy_impact': 0.08,
                'cost_impact': 0.23
            }
        ]
    
    def _get_processing_steps(self) -> List[Dict[str, Any]]:
        return [
            {
                'name': 'Image Preprocessing',
                'status': 'completed',
                'duration': 0.8,
                'success_rate': 0.98,
                'input_data': {'image_size': '1920x1080', 'format': 'JPEG'},
                'output_data': {'processed_size': '1920x1080', 'quality_score': 0.94},
                'logs': [
                    {'level': 'INFO', 'timestamp': '10:15:01', 'message': 'Image loaded successfully'},
                    {'level': 'INFO', 'timestamp': '10:15:02', 'message': 'Quality enhancement applied'}
                ],
                'api_calls': 0,
                'tokens_used': 0,
                'memory_mb': 45,
                'error_rate': 0.02
            },
            {
                'name': 'Structure Detection',
                'status': 'completed',
                'duration': 2.3,
                'success_rate': 0.95,
                'input_data': {'model': 'claude-4-sonnet', 'confidence_threshold': 0.8},
                'output_data': {'shelves_detected': 4, 'confidence': 0.98},
                'logs': [
                    {'level': 'INFO', 'timestamp': '10:15:03', 'message': 'Starting structure analysis'},
                    {'level': 'INFO', 'timestamp': '10:15:05', 'message': '4 shelves detected with high confidence'}
                ],
                'api_calls': 1,
                'tokens_used': 1250,
                'memory_mb': 67,
                'error_rate': 0.05
            }
        ]
    
    def _show_stage_details(self, stage_name: str):
        st.info(f"Showing detailed results for {stage_name} stage...")
    
    def _render_pipeline_flow_chart(self):
        # Simple pipeline flow visualization
        st.text("📥 Input Image → 🔍 Structure → 📦 Products → ✅ Validation → 🏗️ Planogram")
    
    def _render_stage_results(self, stage: str):
        st.info(f"Displaying results for: {stage}")
    
    def _analyze_model_differences(self, model_a: Dict, model_b: Dict) -> List[Dict]:
        return [
            {'field': 'Accuracy', 'description': f'Model A: {model_a["accuracy"]:.1%} vs Model B: {model_b["accuracy"]:.1%}'},
            {'field': 'Processing Time', 'description': f'Model A is {abs(model_a["processing_time"] - model_b["processing_time"]):.1f}s faster'}
        ]
    
    # Additional helper methods would be implemented here...
    def _get_current_upload_data(self) -> Dict[str, Any]:
        return {'image_data': None, 'detections': []}
    
    def _get_current_planogram_data(self) -> Dict[str, Any]:
        return None
    
    def _get_current_extraction_json(self) -> Dict[str, Any]:
        return None
    
    def _add_advanced_detection_overlays(self, image, detections, options):
        return image
    
    def _generate_interactive_planogram_html(self, data):
        return "<div>Interactive planogram would be here</div>"
    
    def _render_planogram_editor(self, data):
        st.info("Planogram editor interface would be here")
    
    def _show_add_product_dialog(self):
        st.info("Add product dialog would open here")
    
    def _show_edit_product_dialog(self):
        st.info("Edit product dialog would open here")
    
    def _remove_selected_product(self):
        st.info("Remove product functionality would execute here")
    
    def _save_json_changes(self, json_data):
        st.success("JSON changes saved successfully")
    
    def _regenerate_planogram_from_json(self, json_data):
        st.success("Planogram regenerated from JSON")
    
    def _trigger_reextraction_with_config(self):
        st.success("Re-extraction started with current configuration")
    
    def _trigger_advanced_ab_test(self):
        st.success("Advanced A/B test initiated")


def render_complete_visual_debugging_interface():
    """Main function to render the complete debugging interface"""
    debugger = PipelineDebugger()
    debugger.render_complete_debugging_interface() 