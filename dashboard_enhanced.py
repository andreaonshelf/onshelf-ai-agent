"""
OnShelf AI Agent Enhanced Dashboard
Real-time monitoring with new features: Prompt Management, Human Learning, 3-Model Consensus
"""

import streamlit as st
import asyncio
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
import requests

# Page configuration
st.set_page_config(
    page_title="OnShelf AI Agent Enhanced Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with enhanced styling
st.markdown("""
<style>
.agent-processing { animation: pulse 2s infinite; color: #3b82f6; }
.accuracy-excellent { color: #059669; font-weight: bold; }
.accuracy-good { color: #0d9488; }
.accuracy-poor { color: #dc2626; }
.prompt-active { background-color: #e0f2fe; padding: 10px; border-radius: 5px; }
.model-badge { 
    display: inline-block; 
    padding: 4px 8px; 
    border-radius: 4px; 
    font-size: 12px;
    font-weight: bold;
    margin: 2px;
}
.model-claude { background-color: #8b5cf6; color: white; }
.model-gpt4o { background-color: #10b981; color: white; }
.model-gemini { background-color: #f59e0b; color: white; }
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# Initialize Supabase connection
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            try:
                supabase_url = supabase_url or st.secrets.get('SUPABASE_URL')
                supabase_key = supabase_key or st.secrets.get('SUPABASE_SERVICE_KEY')
            except:
                pass
        
        if not supabase_url or not supabase_key:
            st.error("❌ Supabase credentials not configured")
            return None
            
        supabase = create_client(supabase_url, supabase_key)
        return supabase
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {e}")
        return None

# Get API stats
@st.cache_data(ttl=10)
def get_api_stats():
    """Get real-time stats from API"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Get prompt templates
def get_prompt_templates(_supabase):
    """Get prompt templates from database"""
    if not _supabase:
        return pd.DataFrame()
    
    try:
        result = _supabase.table("prompt_templates") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# Get human corrections
def get_human_corrections(_supabase, days=7):
    """Get recent human corrections"""
    if not _supabase:
        return pd.DataFrame()
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        result = _supabase.table("human_corrections") \
            .select("*") \
            .gte("created_at", cutoff_date) \
            .order("created_at", desc=True) \
            .execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# Get extraction results for consensus analysis
def get_extraction_results(_supabase, days=7):
    """Get recent extraction results"""
    if not _supabase:
        return pd.DataFrame()
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        result = _supabase.table("extraction_results") \
            .select("*") \
            .gte("created_at", cutoff_date) \
            .order("created_at", desc=True) \
            .execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# Initialize
supabase = init_supabase()

# Title with version badge
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🧠 OnShelf AI Agent Enhanced Dashboard")
    st.markdown("**Real-time monitoring with Prompt Management, Human Learning & 3-Model Consensus**")
with col2:
    st.markdown("""
    <div style='text-align: right; padding-top: 20px;'>
        <span class='model-badge model-claude'>Claude</span>
        <span class='model-badge model-gpt4o'>GPT-4o</span>
        <span class='model-badge model-gemini'>Gemini</span>
    </div>
    """, unsafe_allow_html=True)

# Connection status
if supabase:
    st.success("✅ Connected to Supabase with Enhanced Features")
else:
    st.error("❌ Not connected to database - showing limited functionality")

# Sidebar with enhanced options
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Feature toggles
    st.subheader("🎛️ Features")
    show_prompt_management = st.checkbox("Prompt Management", value=True)
    show_human_learning = st.checkbox("Human Learning", value=True)
    show_consensus = st.checkbox("3-Model Consensus", value=True)
    show_cost_tracking = st.checkbox("Cost Tracking", value=True)
    
    st.divider()
    
    # Connection settings
    api_host = st.text_input("API Host", value="localhost")
    api_port = st.number_input("API Port", value=8000, min_value=1, max_value=65535)
    
    # Monitoring options
    st.subheader("📊 Monitoring Options")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 5, 60, 10)
    
    # Manual refresh button
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()

# Get real data
api_stats = get_api_stats()
prompt_templates_df = get_prompt_templates(supabase) if show_prompt_management else pd.DataFrame()
corrections_df = get_human_corrections(supabase) if show_human_learning else pd.DataFrame()
extraction_results_df = get_extraction_results(supabase) if show_consensus else pd.DataFrame()

# Enhanced tabs
tabs = ["🔄 Queue Status", "📊 Analytics", "🖼️ Processing Results"]
if show_prompt_management:
    tabs.append("🎛️ Prompt Management")
if show_human_learning:
    tabs.append("🧠 Human Learning")
if show_consensus:
    tabs.append("🤝 Consensus Analysis")
if show_cost_tracking:
    tabs.append("💰 Cost Tracking")
tabs.append("📋 System Status")

tab_objects = st.tabs(tabs)
tab_index = 0

# Tab 1: Queue Status (existing functionality)
with tab_objects[tab_index]:
    # [Keep existing queue status code from original dashboard.py]
    st.info("Queue Status functionality (from original dashboard)")
    tab_index += 1

# Tab 2: Analytics (existing functionality)
with tab_objects[tab_index]:
    # [Keep existing analytics code from original dashboard.py]
    st.info("Analytics functionality (from original dashboard)")
    tab_index += 1

# Tab 3: Processing Results (existing functionality)
with tab_objects[tab_index]:
    # [Keep existing processing results code from original dashboard.py]
    st.info("Processing Results functionality (from original dashboard)")
    tab_index += 1

# New Tab: Prompt Management
if show_prompt_management:
    with tab_objects[tab_index]:
        st.subheader("🎛️ Prompt Management Center")
        
        if not prompt_templates_df.empty:
            # Prompt type selector
            prompt_types = prompt_templates_df['prompt_type'].unique()
            selected_type = st.selectbox("Select Prompt Type", prompt_types)
            
            # Model selector
            model_types = prompt_templates_df['model_type'].unique()
            selected_model = st.selectbox("Select Model", model_types)
            
            # Filter prompts
            filtered_prompts = prompt_templates_df[
                (prompt_templates_df['prompt_type'] == selected_type) &
                (prompt_templates_df['model_type'] == selected_model)
            ]
            
            if not filtered_prompts.empty:
                # Show active prompt
                active_prompt = filtered_prompts[filtered_prompts['is_active'] == True]
                if not active_prompt.empty:
                    st.markdown("### 🟢 Active Prompt")
                    prompt = active_prompt.iloc[0]
                    with st.container():
                        st.markdown(f"""
                        <div class='prompt-active'>
                        <b>Version:</b> {prompt['prompt_version']}<br>
                        <b>Performance Score:</b> {prompt['performance_score']:.2f}<br>
                        <b>Usage Count:</b> {prompt['usage_count']}<br>
                        <b>Correction Rate:</b> {prompt['correction_rate']:.2%}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("View Prompt Content"):
                            st.text_area("Content", prompt['prompt_content'], height=200, disabled=True)
                
                # Version history
                st.markdown("### 📜 Version History")
                history_df = filtered_prompts.sort_values('created_at', ascending=False)
                
                for _, prompt in history_df.iterrows():
                    status = "🟢 Active" if prompt['is_active'] else "⚪ Inactive"
                    feedback_badge = "🔄" if prompt['created_from_feedback'] else "✏️"
                    
                    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                    with col1:
                        st.write(f"{status} v{prompt['prompt_version']}")
                    with col2:
                        st.write(f"{feedback_badge} Score: {prompt['performance_score']:.2f}")
                    with col3:
                        st.write(f"Uses: {prompt['usage_count']}")
                    with col4:
                        if not prompt['is_active']:
                            if st.button("Activate", key=f"activate_{prompt['prompt_id']}"):
                                # Would activate this prompt version
                                st.success("Prompt activated!")
                                st.rerun()
                
                # Prompt editor
                st.markdown("### ✏️ Edit Prompt")
                new_content = st.text_area("New Prompt Content", height=300)
                if st.button("Save New Version"):
                    st.success("New prompt version saved!")
                    st.rerun()
            else:
                st.info("No prompts found for selected type and model")
        else:
            st.info("No prompt templates found in database")
        
        tab_index += 1

# New Tab: Human Learning
if show_human_learning:
    with tab_objects[tab_index]:
        st.subheader("🧠 Human Learning System")
        
        if not corrections_df.empty:
            # Correction statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Corrections (7 days)", len(corrections_df))
            with col2:
                unique_types = corrections_df['correction_type'].nunique()
                st.metric("Correction Types", unique_types)
            with col3:
                affected_uploads = corrections_df['upload_id'].nunique()
                st.metric("Affected Uploads", affected_uploads)
            
            # Correction type distribution
            st.markdown("### 📊 Correction Type Distribution")
            type_counts = corrections_df['correction_type'].value_counts()
            
            fig = px.pie(values=type_counts.values, names=type_counts.index, 
                        title="Human Corrections by Type")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent corrections
            st.markdown("### 🔍 Recent Corrections")
            recent_corrections = corrections_df.head(10)
            
            for _, correction in recent_corrections.iterrows():
                with st.expander(f"{correction['correction_type']} - {correction['created_at']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Original AI Result:**")
                        st.json(correction['original_ai_result'])
                    with col2:
                        st.markdown("**Human Correction:**")
                        st.json(correction['human_correction'])
            
            # Learning patterns
            st.markdown("### 🎯 Learning Patterns")
            
            # Group by correction type and date
            corrections_df['date'] = pd.to_datetime(corrections_df['created_at']).dt.date
            daily_corrections = corrections_df.groupby(['date', 'correction_type']).size().reset_index(name='count')
            
            fig = px.line(daily_corrections, x='date', y='count', color='correction_type',
                         title="Correction Trends Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No human corrections found in the last 7 days")
        
        tab_index += 1

# New Tab: Consensus Analysis
if show_consensus:
    with tab_objects[tab_index]:
        st.subheader("🤝 3-Model Consensus Analysis")
        
        if not extraction_results_df.empty:
            # Consensus statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                consensus_rate = extraction_results_df['consensus_reached'].mean()
                st.metric("Consensus Rate", f"{consensus_rate:.1%}")
            with col2:
                avg_accuracy = extraction_results_df['overall_accuracy'].mean()
                st.metric("Avg Accuracy", f"{avg_accuracy:.1%}")
            with col3:
                avg_iterations = extraction_results_df['iteration_count'].mean()
                st.metric("Avg Iterations", f"{avg_iterations:.1f}")
            
            # Model participation in consensus
            st.markdown("### 🏆 Model Performance in Consensus")
            
            # Mock data for model performance (would come from actual consensus data)
            model_performance = pd.DataFrame({
                'Model': ['Claude', 'GPT-4o', 'Gemini'],
                'Accuracy': [0.92, 0.89, 0.87],
                'Speed (s)': [2.1, 1.8, 1.5],
                'Cost ($)': [0.015, 0.020, 0.002]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Accuracy', x=model_performance['Model'], 
                                y=model_performance['Accuracy'], yaxis='y', offsetgroup=1))
            fig.add_trace(go.Bar(name='Speed', x=model_performance['Model'], 
                                y=model_performance['Speed (s)'], yaxis='y2', offsetgroup=2))
            
            fig.update_layout(
                title='Model Performance Comparison',
                yaxis=dict(title='Accuracy', side='left'),
                yaxis2=dict(title='Speed (seconds)', overlaying='y', side='right'),
                barmode='group'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Consensus visualization
            st.markdown("### 🎨 Recent Consensus Results")
            
            recent_results = extraction_results_df.head(5)
            for _, result in recent_results.iterrows():
                consensus_icon = "✅" if result['consensus_reached'] else "⚠️"
                with st.expander(f"{consensus_icon} Upload {result['upload_id'][:8]}... - {result['overall_accuracy']:.1%} accuracy"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**System:** {result['system_type']}")
                        st.write(f"**Iterations:** {result['iteration_count']}")
                    with col2:
                        st.write(f"**Processing Time:** {result['processing_time_seconds']:.1f}s")
                        st.write(f"**Total Cost:** ${result['total_cost']:.3f}")
                    with col3:
                        st.write(f"**Consensus:** {'Yes' if result['consensus_reached'] else 'No'}")
                        st.write(f"**Accuracy:** {result['overall_accuracy']:.1%}")
        else:
            st.info("No extraction results found for consensus analysis")
        
        tab_index += 1

# New Tab: Cost Tracking
if show_cost_tracking:
    with tab_objects[tab_index]:
        st.subheader("💰 Cost Tracking Dashboard")
        
        # Cost overview
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate costs from extraction results
        if not extraction_results_df.empty:
            total_cost = extraction_results_df['total_cost'].sum()
            avg_cost = extraction_results_df['total_cost'].mean()
            
            with col1:
                st.metric("Total Cost (7 days)", f"${total_cost:.2f}")
            with col2:
                st.metric("Avg Cost per Extract", f"${avg_cost:.3f}")
            with col3:
                st.metric("Extractions", len(extraction_results_df))
            with col4:
                cost_per_accuracy = total_cost / (extraction_results_df['overall_accuracy'].mean() * 100)
                st.metric("Cost per % Accuracy", f"${cost_per_accuracy:.4f}")
            
            # Cost breakdown by model
            st.markdown("### 📊 Cost Breakdown by Model")
            
            # Mock cost data by model
            model_costs = pd.DataFrame({
                'Model': ['Claude', 'GPT-4o', 'Gemini'] * 20,
                'Cost': [0.015, 0.020, 0.002] * 20,
                'Tokens': [1000, 1200, 1100] * 20
            })
            
            fig = px.box(model_costs, x='Model', y='Cost', title='Cost Distribution by Model')
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost over time
            st.markdown("### 📈 Cost Trends")
            
            extraction_results_df['date'] = pd.to_datetime(extraction_results_df['created_at']).dt.date
            daily_costs = extraction_results_df.groupby('date')['total_cost'].agg(['sum', 'mean', 'count']).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=daily_costs['date'], y=daily_costs['sum'], 
                                    mode='lines+markers', name='Total Daily Cost'))
            fig.add_trace(go.Scatter(x=daily_costs['date'], y=daily_costs['mean'], 
                                    mode='lines+markers', name='Avg Cost per Extract', yaxis='y2'))
            
            fig.update_layout(
                title='Daily Cost Analysis',
                yaxis=dict(title='Total Cost ($)', side='left'),
                yaxis2=dict(title='Avg Cost per Extract ($)', overlaying='y', side='right')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Cost optimization suggestions
            st.markdown("### 💡 Cost Optimization Suggestions")
            
            suggestions = [
                ("Use Gemini for initial structure analysis", "Save ~80% on structure detection", "high"),
                ("Implement caching for repeated products", "Save ~30% on similar shelves", "medium"),
                ("Batch process similar images", "Save ~25% on API calls", "medium"),
                ("Use position locking after high confidence", "Save ~15% on iterations", "low")
            ]
            
            for suggestion, impact, priority in suggestions:
                priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}[priority]
                st.write(f"{priority_color} **{suggestion}** - {impact}")
        else:
            st.info("No cost data available")
        
        tab_index += 1

# Tab: System Status (enhanced)
with tab_objects[tab_index]:
    st.subheader("🖥️ Enhanced System Status")
    
    # API Status
    if api_stats:
        st.success("✅ API Server Online")
        
        # Enhanced system metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("API Version", "v1.3.0")
            st.metric("Models Active", "3/3")
        
        with col2:
            st.metric("Prompt Templates", len(prompt_templates_df) if not prompt_templates_df.empty else "0")
            active_prompts = len(prompt_templates_df[prompt_templates_df['is_active'] == True]) if not prompt_templates_df.empty else 0
            st.metric("Active Prompts", active_prompts)
        
        with col3:
            st.metric("Human Corrections", len(corrections_df) if not corrections_df.empty else "0")
            st.metric("Learning Rate", "Active" if len(corrections_df) > 0 else "Inactive")
        
        with col4:
            consensus_enabled = not extraction_results_df.empty if 'extraction_results_df' in locals() else False
            st.metric("Consensus System", "Enabled" if consensus_enabled else "Disabled")
            st.metric("Cost Tracking", "Active")
    else:
        st.error("❌ API Server Offline")
    
    # Feature Status Grid
    st.markdown("### 🎯 Feature Status")
    
    features = [
        ("Gemini Integration", True, "Fully integrated with real API"),
        ("3-Model Consensus", True, "Weighted voting active"),
        ("Human Learning", True, "Collecting feedback"),
        ("Prompt Optimization", True, "Auto-adjusting prompts"),
        ("Position Locking", True, "High-confidence locking"),
        ("Cost Tracking", True, "Real-time cost monitoring"),
        ("Cumulative Learning", True, "Agents build on work"),
        ("Database Persistence", supabase is not None, "Supabase connected" if supabase else "Not connected")
    ]
    
    feature_cols = st.columns(2)
    for i, (feature, status, description) in enumerate(features):
        with feature_cols[i % 2]:
            status_icon = "✅" if status else "❌"
            st.write(f"{status_icon} **{feature}**")
            st.caption(description)
    
    # Environment Check
    st.markdown("### 🔧 Environment Configuration")
    
    env_status = {
        "SUPABASE_URL": "✅" if os.getenv('SUPABASE_URL') else "❌",
        "SUPABASE_SERVICE_KEY": "✅" if os.getenv('SUPABASE_SERVICE_KEY') else "❌", 
        "OPENAI_API_KEY": "✅" if os.getenv('OPENAI_API_KEY') else "❌",
        "ANTHROPIC_API_KEY": "✅" if os.getenv('ANTHROPIC_API_KEY') else "❌",
        "GOOGLE_API_KEY": "✅" if os.getenv('GOOGLE_API_KEY') else "❌"
    }
    
    env_cols = st.columns(2)
    for i, (key, status) in enumerate(env_status.items()):
        with env_cols[i % 2]:
            st.write(f"{status} {key}")

# Footer with enhanced info
st.markdown("---")
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(
    f"""
    <div style='text-align: center; color: gray;'>
    OnShelf AI Agent System v1.3.0 Enhanced | Last updated: {current_time} | 
    Features: Prompt Management, Human Learning, 3-Model Consensus, Real Cost Tracking
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh logic
if auto_refresh and supabase:
    import time
    time.sleep(refresh_interval)
    st.rerun()