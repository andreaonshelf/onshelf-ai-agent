"""
OnShelf AI Agent Dashboard
Real-time monitoring and validation interface
"""

import streamlit as st
import asyncio
import websockets
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(
    page_title="OnShelf AI Agent Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.agent-processing { animation: pulse 2s infinite; color: #3b82f6; }
.accuracy-excellent { color: #059669; font-weight: bold; }
.accuracy-good { color: #0d9488; }
.accuracy-poor { color: #dc2626; }
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🧠 OnShelf AI Agent Dashboard")
st.markdown("**Real-time monitoring of self-debugging extraction system**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Connection settings
    api_host = st.text_input("API Host", value="localhost")
    api_port = st.number_input("API Port", value=8000, min_value=1, max_value=65535)
    
    # Monitoring options
    st.subheader("📊 Monitoring Options")
    auto_refresh = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Refresh interval (seconds)", 1, 10, 3)
    
    # Agent filter
    st.subheader("🔍 Filter")
    status_filter = st.multiselect(
        "Agent Status",
        ["running", "completed", "escalated", "failed"],
        default=["running", "completed"]
    )

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["🔄 Active Agents", "📊 Analytics", "🖼️ Visual Validator", "📋 Queue"])

# Tab 1: Active Agents
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Agents", "3", "+2")
    with col2:
        st.metric("Avg Accuracy", "94.2%", "+2.1%")
    with col3:
        st.metric("Success Rate", "92%", "+5%")
    with col4:
        st.metric("Avg Iterations", "2.3", "-0.2")
    
    st.markdown("---")
    
    # Active agents table
    st.subheader("🤖 Active Agents")
    
    # Mock data for demonstration
    agents_data = pd.DataFrame({
        "Agent ID": ["agent_001", "agent_002", "agent_003"],
        "Upload ID": ["upload_123", "upload_124", "upload_125"],
        "Status": ["🔄 Running", "✅ Completed", "⚠️ Escalated"],
        "Iteration": [3, 2, 5],
        "Current Accuracy": ["87%", "96%", "82%"],
        "Duration": ["1m 23s", "2m 15s", "3m 45s"],
        "Issues": [3, 0, 7]
    })
    
    st.dataframe(agents_data, use_container_width=True)
    
    # Real-time agent detail
    st.subheader("📡 Real-time Agent Progress")
    
    selected_agent = st.selectbox("Select Agent", ["agent_001", "agent_002", "agent_003"])
    
    if selected_agent == "agent_001":
        # Progress bar
        progress = st.progress(0.6, text="Iteration 3/5")
        
        # Current status
        status_col1, status_col2 = st.columns(2)
        
        with status_col1:
            st.info("**Current Step**: Product Extraction")
            st.warning("**Issues Found**: 3 mismatches")
        
        with status_col2:
            st.success("**Current Accuracy**: 87%")
            st.info("**Est. Completion**: 45 seconds")
        
        # Iteration timeline
        st.markdown("#### 🔄 Iteration Timeline")
        
        timeline_data = pd.DataFrame({
            "Iteration": [1, 2, 3],
            "Accuracy": [73, 84, 87],
            "Duration (s)": [45, 38, 42],
            "Issues": [12, 5, 3]
        })
        
        fig = px.line(timeline_data, x="Iteration", y="Accuracy", 
                     title="Accuracy Progression", markers=True)
        fig.add_hline(y=95, line_dash="dash", line_color="green", 
                     annotation_text="Target: 95%")
        st.plotly_chart(fig, use_container_width=True)

# Tab 2: Analytics
with tab2:
    st.subheader("📈 System Performance Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")
    
    # Performance metrics
    metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
    
    with metrics_col1:
        st.metric("Total Processed", "1,234", help="Total uploads processed")
    with metrics_col2:
        st.metric("Success Rate", "91.5%", help="Achieved target accuracy")
    with metrics_col3:
        st.metric("Avg API Cost", "£0.32", help="Per extraction")
    with metrics_col4:
        st.metric("Human Reviews", "8.5%", help="Required escalation")
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Daily success rate
        daily_data = pd.DataFrame({
            "Date": pd.date_range(start="2024-01-01", periods=30),
            "Success Rate": [88 + i % 10 for i in range(30)]
        })
        
        fig1 = px.area(daily_data, x="Date", y="Success Rate", 
                      title="Daily Success Rate Trend")
        fig1.add_hline(y=90, line_dash="dash", line_color="red",
                      annotation_text="Target: 90%")
        st.plotly_chart(fig1, use_container_width=True)
    
    with chart_col2:
        # Iteration distribution
        iteration_data = pd.DataFrame({
            "Iterations": [1, 2, 3, 4, 5],
            "Count": [450, 520, 180, 60, 24]
        })
        
        fig2 = px.bar(iteration_data, x="Iterations", y="Count",
                     title="Iteration Distribution")
        st.plotly_chart(fig2, use_container_width=True)
    
    # Model performance
    st.subheader("🤖 Model Performance")
    
    model_data = pd.DataFrame({
        "Model": ["Claude-3 Sonnet", "GPT-4o", "Gemini 2.0"],
        "Tasks": [850, 1200, 450],
        "Avg Accuracy": [94.5, 93.2, 91.8],
        "Avg Cost": [0.12, 0.15, 0.08]
    })
    
    st.dataframe(model_data, use_container_width=True)

# Tab 3: Visual Validator
with tab3:
    st.subheader("🖼️ Visual Comparison Tool")
    
    # Upload selector
    validation_upload = st.selectbox(
        "Select Upload for Validation",
        ["upload_123 - Tesco Camden", "upload_124 - M&S Blackheath", "upload_125 - Sainsbury's Richmond"]
    )
    
    # Three column layout
    col1, col2, col3 = st.columns([1, 2, 2])
    
    with col1:
        st.markdown("### 📋 Extraction Summary")
        st.info("""
        **Products**: 24  
        **Shelves**: 3  
        **Accuracy**: 94%  
        **Iteration**: 2/5  
        **Status**: Running
        """)
        
        st.markdown("### 🔍 Issues Found")
        st.error("❌ Missing: Coca-Cola 2L")
        st.warning("⚠️ Wrong position: Pepsi Max")
        st.warning("⚠️ Facing count: Sprite (3 vs 4)")
    
    with col2:
        st.markdown("### 📷 Original Image")
        st.image("https://via.placeholder.com/400x600.png?text=Original+Shelf+Image", 
                use_column_width=True)
        
        with st.expander("🔍 AI Detection Overlays"):
            st.markdown("""
            - 🟢 High confidence (>90%)
            - 🟡 Medium confidence (70-90%)
            - 🔴 Low confidence (<70%)
            """)
    
    with col3:
        st.markdown("### 🏗️ Generated Planogram")
        st.image("https://via.placeholder.com/400x600.png?text=AI+Generated+Planogram", 
                use_column_width=True)
        
        with st.expander("📊 Planogram Legend"):
            st.markdown("""
            - 🟩 Matched correctly
            - 🟨 Position mismatch
            - 🟥 Missing product
            - ⬜ Empty space
            """)
    
    # Action buttons
    st.markdown("---")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("✅ Approve", type="primary", use_container_width=True):
            st.success("Extraction approved!")
    
    with action_col2:
        if st.button("🔄 Re-run Iteration", use_container_width=True):
            st.info("Starting new iteration...")
    
    with action_col3:
        if st.button("✏️ Manual Corrections", use_container_width=True):
            st.info("Opening correction interface...")
    
    with action_col4:
        if st.button("⚠️ Escalate to Human", use_container_width=True):
            st.warning("Escalated for human review")

# Tab 4: Queue Management
with tab4:
    st.subheader("📋 Processing Queue")
    
    # Queue filters
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        queue_status = st.selectbox("Status", ["All", "Pending", "Processing", "Completed"])
    
    with filter_col2:
        store_filter = st.text_input("Store Name")
    
    with filter_col3:
        priority_filter = st.selectbox("Priority", ["All", "High", "Medium", "Low"])
    
    # Queue table
    queue_data = pd.DataFrame({
        "Upload ID": ["upload_126", "upload_127", "upload_128", "upload_129"],
        "Store": ["Tesco Express Camden", "M&S Food Hall", "Sainsbury's Local", "Co-op Richmond"],
        "Category": ["Beverages", "Ready Meals", "Snacks", "Beverages"],
        "Priority": ["🔴 High", "🟡 Medium", "🟡 Medium", "🟢 Low"],
        "Status": ["Pending", "Pending", "Processing", "Pending"],
        "SLA": ["2h", "4h", "3h", "8h"],
        "Created": ["10:23 AM", "10:45 AM", "11:02 AM", "11:15 AM"]
    })
    
    st.dataframe(queue_data, use_container_width=True)
    
    # Bulk actions
    st.markdown("### 🎯 Bulk Actions")
    
    bulk_col1, bulk_col2, bulk_col3 = st.columns(3)
    
    with bulk_col1:
        if st.button("▶️ Process Selected", type="primary", use_container_width=True):
            st.success("Processing 4 uploads...")
    
    with bulk_col2:
        if st.button("⏸️ Pause Queue", use_container_width=True):
            st.warning("Queue paused")
    
    with bulk_col3:
        if st.button("📊 Export Results", use_container_width=True):
            st.info("Exporting results...")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    OnShelf AI Agent System v1.0.0 | 
    <a href='#'>Documentation</a> | 
    <a href='#'>API Status</a> | 
    <a href='#'>Support</a>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh logic
if auto_refresh:
    time_placeholder = st.empty()
    time_placeholder.text(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    # This would trigger a rerun after the interval
    # In production, you'd use st.experimental_rerun() with a timer 