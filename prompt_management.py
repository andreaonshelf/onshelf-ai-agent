"""
OnShelf AI Prompt Management Sidebar
Provides a sidebar interface for managing prompts and extraction systems
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

def render_prompt_management_sidebar(supabase_client):
    """Render the prompt management sidebar"""
    
    with st.sidebar:
        st.markdown("### 🎛️ Prompt Management")
        
        # System Selection
        st.markdown("#### System Selection")
        selected_system = st.radio(
            "Extraction System",
            ["Hybrid", "GPT-4o", "Claude", "Gemini"],
            horizontal=True
        )
        
        # Prompt Selection
        st.markdown("#### Prompt Selection")
        prompt_templates = get_prompt_templates(supabase_client)
        
        if not prompt_templates.empty:
            # Filter templates by selected system
            system_templates = prompt_templates[
                (prompt_templates['model_type'] == selected_system.lower()) |
                (prompt_templates['model_type'] == 'universal')
            ]
            
            # Group by prompt type
            prompt_types = system_templates['prompt_type'].unique()
            selected_type = st.selectbox("Prompt Type", prompt_types)
            
            # Show active prompt for selected type
            active_prompt = system_templates[
                (system_templates['prompt_type'] == selected_type) &
                (system_templates['is_active'] == True)
            ]
            
            if not active_prompt.empty:
                st.markdown("##### Active Prompt")
                st.markdown(f"**Version:** {active_prompt.iloc[0]['prompt_version']}")
                st.markdown(f"**Score:** {active_prompt.iloc[0]['performance_score']:.2f}")
                st.markdown(f"**Uses:** {active_prompt.iloc[0]['usage_count']}")
                
                # Show prompt content in expandable section
                with st.expander("View Prompt Content"):
                    st.text_area(
                        "Prompt Content",
                        value=active_prompt.iloc[0]['prompt_content'],
                        height=200,
                        disabled=True
                    )
            
            # Version History
            st.markdown("##### Version History")
            version_history = system_templates[
                system_templates['prompt_type'] == selected_type
            ].sort_values('created_at', ascending=False)
            
            for _, version in version_history.iterrows():
                status = "🟢" if version['is_active'] else "⚪"
                feedback = "🔄" if version['created_from_feedback'] else "✏️"
                
                with st.container():
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.write(f"{status}")
                    with col2:
                        st.write(f"v{version['prompt_version']} ({feedback})")
                        st.caption(f"Score: {version['performance_score']:.2f} | Uses: {version['usage_count']}")
            
            # Quick Actions
            st.markdown("#### Quick Actions")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 Edit Prompt", use_container_width=True):
                    st.session_state['editing_prompt'] = True
            with col2:
                if st.button("🧪 Test Prompt", use_container_width=True):
                    st.session_state['testing_prompt'] = True
            
            # Batch Operations
            st.markdown("#### Batch Operations")
            if st.button("📊 Compare Versions", use_container_width=True):
                st.session_state['comparing_versions'] = True
            
            if st.button("📈 Performance Analysis", use_container_width=True):
                st.session_state['analyzing_performance'] = True
        else:
            st.info("No prompt templates available")

def get_prompt_templates(supabase_client):
    """Get prompt templates from database"""
    if not supabase_client:
        return pd.DataFrame()
    
    try:
        result = supabase_client.table("prompt_templates") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to fetch prompt templates: {e}")
        return pd.DataFrame()

def edit_prompt_modal():
    """Render the prompt editing modal"""
    if st.session_state.get('editing_prompt'):
        with st.form("edit_prompt_form"):
            st.markdown("### ✏️ Edit Prompt")
            
            prompt_type = st.selectbox(
                "Prompt Type",
                ["Structure Analysis", "Position Analysis", "Quantity Analysis", "Detail Analysis"]
            )
            
            model_type = st.selectbox(
                "Model Type",
                ["Universal", "GPT-4o Specific", "Claude Specific", "Gemini Specific"]
            )
            
            prompt_content = st.text_area(
                "Prompt Content",
                height=300,
                placeholder="Enter your prompt here..."
            )
            
            description = st.text_input(
                "Description",
                placeholder="Brief description of changes"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Save & Activate", type="primary")
            with col2:
                cancel = st.form_submit_button("❌ Cancel")
            
            if submit:
                # TODO: Implement prompt saving logic
                st.success("Prompt saved and activated!")
                st.session_state['editing_prompt'] = False
            
            if cancel:
                st.session_state['editing_prompt'] = False

def test_prompt_modal():
    """Render the prompt testing modal"""
    if st.session_state.get('testing_prompt'):
        with st.form("test_prompt_form"):
            st.markdown("### 🧪 Test Prompt")
            
            test_image = st.file_uploader("Upload Test Image", type=['jpg', 'jpeg', 'png'])
            
            if test_image:
                st.image(test_image, caption="Test Image")
            
            col1, col2 = st.columns(2)
            with col1:
                run_test = st.form_submit_button("▶️ Run Test", type="primary")
            with col2:
                cancel = st.form_submit_button("❌ Cancel")
            
            if run_test:
                # TODO: Implement prompt testing logic
                st.info("Test results would appear here")
            
            if cancel:
                st.session_state['testing_prompt'] = False

def compare_versions_modal():
    """Render the version comparison modal"""
    if st.session_state.get('comparing_versions'):
        with st.form("compare_versions_form"):
            st.markdown("### 📊 Compare Versions")
            
            # TODO: Implement version comparison logic
            
            if st.form_submit_button("❌ Close"):
                st.session_state['comparing_versions'] = False

def performance_analysis_modal():
    """Render the performance analysis modal"""
    if st.session_state.get('analyzing_performance'):
        with st.form("performance_analysis_form"):
            st.markdown("### 📈 Performance Analysis")
            
            # TODO: Implement performance analysis logic
            
            if st.form_submit_button("❌ Close"):
                st.session_state['analyzing_performance'] = False 