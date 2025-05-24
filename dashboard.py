"""
OnShelf AI Agent Dashboard
Real-time monitoring and validation interface with REAL DATA from Supabase
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

# Initialize Supabase connection
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        # Get from environment variables first
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        # Try Streamlit secrets if env vars not found
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
@st.cache_data(ttl=10)  # Cache for 10 seconds
def get_api_stats():
    """Get real-time stats from API"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Get queue data
def get_queue_data(_supabase):
    """Get real queue data from ai_extraction_queue"""
    if not _supabase:
        return pd.DataFrame()
    
    try:
        result = _supabase.table("ai_extraction_queue") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(100) \
            .execute()
        
        if result.data:
            return pd.DataFrame(result.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to fetch queue data: {e}")
        return pd.DataFrame()

# Get processing stats
def get_processing_stats(_supabase):
    """Get processing statistics"""
    if not _supabase:
        return {}
    
    try:
        # Get stats from the queue
        total_result = _supabase.table("ai_extraction_queue").select("id", count="exact").execute()
        pending_result = _supabase.table("ai_extraction_queue").select("id", count="exact").eq("status", "pending").execute()
        processing_result = _supabase.table("ai_extraction_queue").select("id", count="exact").eq("status", "processing").execute()
        completed_result = _supabase.table("ai_extraction_queue").select("id", count="exact").eq("status", "completed").execute()
        
        # Since final_accuracy doesn't exist, we'll set it to 0 for now
        avg_accuracy = 0
        
        return {
            'total_processed': total_result.count or 0,
            'pending': pending_result.count or 0,
            'processing': processing_result.count or 0,
            'completed': completed_result.count or 0,
            'avg_accuracy': avg_accuracy,
            'success_rate': (completed_result.count / max(1, total_result.count)) * 100 if total_result.count else 0
        }
    except Exception as e:
        st.error(f"Failed to fetch processing stats: {e}")
        return {}

# Initialize
supabase = init_supabase()

# Title
st.title("🧠 OnShelf AI Agent Dashboard")
st.markdown("**Real-time monitoring of self-debugging extraction system**")

# Connection status
if supabase:
    st.success("✅ Connected to Supabase")
else:
    st.error("❌ Not connected to database - showing limited functionality")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
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
queue_df = get_queue_data(supabase)
processing_stats = get_processing_stats(supabase)

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["🔄 Queue Status", "📊 Analytics", "🖼️ Processing Results", "📋 System Status"])

# Tab 1: Queue Status (REAL DATA)
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total in Queue", processing_stats.get('total_processed', 0))
    with col2:
        st.metric("Pending", processing_stats.get('pending', 0))
    with col3:
        st.metric("Processing", processing_stats.get('processing', 0))
    with col4:
        st.metric("Completed", processing_stats.get('completed', 0))
    
    if processing_stats.get('avg_accuracy', 0) > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Accuracy", f"{processing_stats.get('avg_accuracy', 0):.1%}")
        with col2:
            st.metric("Success Rate", f"{processing_stats.get('success_rate', 0):.1%}")
    
    st.markdown("---")
    
    # Real queue data table
    st.subheader("📋 AI Extraction Queue (REAL DATA)")
    
    if not queue_df.empty:
        # Format the dataframe for display
        display_df = queue_df.copy()
        
        # Add status icons
        status_icons = {
            'pending': '⏳ Pending',
            'processing': '🔄 Processing', 
            'completed': '✅ Completed',
            'failed': '❌ Failed'
        }
        
        display_df['Status'] = display_df['status'].map(lambda x: status_icons.get(x, x))
        
        # Format timestamps
        if 'created_at' in display_df.columns:
            display_df['Created'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        # Select relevant columns
        columns_to_show = []
        if 'id' in display_df.columns:
            columns_to_show.append('id')
        if 'ready_media_id' in display_df.columns:
            columns_to_show.append('ready_media_id')
        columns_to_show.extend(['Status', 'Created'])
        
        if 'final_accuracy' in display_df.columns:
            display_df['Accuracy'] = display_df['final_accuracy'].apply(
                lambda x: f"{x:.1%}" if pd.notnull(x) else "N/A"
            )
            columns_to_show.append('Accuracy')
        
        if 'processing_duration_seconds' in display_df.columns:
            display_df['Duration'] = display_df['processing_duration_seconds'].apply(
                lambda x: f"{x}s" if pd.notnull(x) else "N/A"
            )
            columns_to_show.append('Duration')
        
        # Filter columns that actually exist
        columns_to_show = [col for col in columns_to_show if col in display_df.columns]
        
        st.dataframe(display_df[columns_to_show], use_container_width=True)
        
        # Add action button for stuck items
        st.subheader("🔧 Queue Actions")
        
        # Identify stuck items (processing for more than 10 minutes or failed)
        from datetime import datetime, timedelta
        import pytz
        
        stuck_items = []
        for _, item in queue_df.iterrows():
            if item['status'] == 'failed':
                stuck_items.append(item)
            elif item['status'] == 'processing':
                # Check if started_at exists and processing for too long
                if item.get('started_at'):
                    started_at = pd.to_datetime(item['started_at'])
                    if started_at.tzinfo is None:
                        started_at = started_at.tz_localize('UTC')
                    
                    # If processing for more than 10 minutes, consider it stuck
                    if datetime.now(pytz.UTC) - started_at > timedelta(minutes=10):
                        stuck_items.append(item)
                else:
                    # No started_at but status is processing = stuck
                    stuck_items.append(item)
        
        if stuck_items:
            st.warning(f"Found {len(stuck_items)} stuck item(s)")
            
            # Show stuck items summary
            for item in stuck_items:
                status_icon = '❌' if item['status'] == 'failed' else '⏱️'
                st.write(f"{status_icon} **ID {item['id']}**: {item.get('ready_media_id', 'Unknown')[:30]}... - {item['status'].title()}")
            
            # Single button to reset all stuck items
            if st.button("🔄 Reset All Stuck Items", type="primary"):
                reset_count = 0
                for item in stuck_items:
                    result = supabase.table("ai_extraction_queue") \
                        .update({
                            "status": "pending",
                            "error_message": None,
                            "started_at": None,
                            "processed_at": None,
                            "agent_id": None
                        }) \
                        .eq("id", item['id']) \
                        .execute()
                    reset_count += 1
                
                st.success(f"✅ Reset {reset_count} stuck item(s) to pending")
                st.rerun()
        else:
            st.info("✅ No stuck items found")
        
        st.markdown("---")
        
        # Show specific queue item details if processing
        processing_items = queue_df[queue_df['status'] == 'processing']
        if not processing_items.empty:
            st.subheader("🔄 Currently Processing")
            for _, item in processing_items.iterrows():
                with st.expander(f"Processing: {item.get('ready_media_id', item.get('id', 'Unknown'))}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Started:** {item.get('started_at', 'Unknown')}")
                        st.write(f"**Agent ID:** {item.get('agent_id', 'N/A')}")
                    with col2:
                        st.write(f"**Ready Media ID:** {item.get('ready_media_id', 'N/A')}")
                        if item.get('current_accuracy'):
                            st.write(f"**Current Accuracy:** {item['current_accuracy']:.1%}")
    else:
        st.info("🔍 No queue data found. Make sure:")
        st.markdown("""
        - Supabase connection is working
        - `ai_extraction_queue` table exists
        - There are items in the queue to process
        """)
        
        if st.button("🧪 Add Test Queue Item"):
            st.info("This would add a test item to the queue in production")

# Tab 2: Analytics (REAL DATA)
with tab2:
    st.subheader("📈 System Performance Analytics")
    
    if not queue_df.empty:
        # Processing over time
        if 'created_at' in queue_df.columns:
            queue_df['created_date'] = pd.to_datetime(queue_df['created_at']).dt.date
            daily_counts = queue_df.groupby(['created_date', 'status']).size().reset_index(name='count')
            
            if not daily_counts.empty:
                fig = px.bar(daily_counts, x='created_date', y='count', color='status',
                           title="Daily Processing Volume by Status")
                st.plotly_chart(fig, use_container_width=True)
        
        # Accuracy distribution
        completed_items = queue_df[queue_df['status'] == 'completed']
        if not completed_items.empty and 'final_accuracy' in completed_items.columns:
            accuracies = completed_items['final_accuracy'].dropna()
            if not accuracies.empty:
                fig = px.histogram(accuracies, nbins=20, title="Accuracy Distribution")
                fig.add_vline(x=0.95, line_dash="dash", line_color="green", 
                            annotation_text="Target: 95%")
                st.plotly_chart(fig, use_container_width=True)
        
        # Processing duration analysis
        if 'processing_duration_seconds' in completed_items.columns:
            durations = completed_items['processing_duration_seconds'].dropna()
            if not durations.empty:
                fig = px.box(y=durations, title="Processing Duration Distribution")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 No data available for analytics yet")

# Tab 3: Processing Results (REAL DATA)
with tab3:
    st.subheader("🖼️ Recent Processing Results")
    
    if not queue_df.empty:
        completed_items = queue_df[queue_df['status'] == 'completed'].head(10)
        
        if not completed_items.empty:
            for _, item in completed_items.iterrows():
                accuracy = item.get('final_accuracy')
                accuracy_display = f"{accuracy:.1%}" if accuracy is not None else "N/A"
                with st.expander(f"✅ {item.get('ready_media_id', item.get('id', 'Unknown'))} - {accuracy_display} accuracy"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Processing Details:**")
                        st.write(f"Agent ID: {item.get('agent_id', 'N/A')}")
                        st.write(f"Iterations: {item.get('iterations_completed', 'N/A')}")
                        st.write(f"Duration: {item.get('processing_duration_seconds', 'N/A')}s")
                    
                    with col2:
                        st.write("**Quality Metrics:**")
                        st.write(f"Accuracy: {accuracy_display}")
                        api_cost = item.get('api_cost')
                        api_cost_display = f"£{api_cost:.3f}" if api_cost is not None else "N/A"
                        st.write(f"API Cost: {api_cost_display}")
                        st.write(f"Human Review: {'Yes' if item.get('human_review_required') else 'No'}")
                    
                    with col3:
                        st.write("**Timestamps:**")
                        st.write(f"Created: {item.get('created_at', 'N/A')}")
                        st.write(f"Completed: {item.get('completed_at', 'N/A')}")
                        
                        if item.get('escalation_reason'):
                            st.warning(f"Escalation: {item['escalation_reason']}")
        else:
            st.info("🕐 No completed processing results yet")
    else:
        st.info("📋 No processing data available")

# Tab 4: System Status (REAL DATA)
with tab4:
    st.subheader("🖥️ System Status")
    
    # API Status
    if api_stats:
        st.success("✅ API Server Online")
        
        with st.expander("API Details"):
            st.json(api_stats)
            
        # Queue processor status
        if 'queue_processor' in api_stats.get('stats', {}):
            queue_stats = api_stats['stats']['queue_processor']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Queue Processor", "Running" if queue_stats.get('is_running') else "Stopped")
            with col2:
                st.metric("Items Processed", queue_stats.get('items_processed', 0))
            with col3:
                uptime = queue_stats.get('uptime_seconds', 0)
                st.metric("Uptime", f"{uptime/60:.1f} min" if uptime > 0 else "N/A")
    else:
        st.error("❌ API Server Offline")
        st.info("Make sure the OnShelf AI Agent API is running on localhost:8000")
    
    # Database Status
    if supabase:
        st.success("✅ Supabase Database Connected")
        
        # Test a simple query
        try:
            test_result = supabase.table("ai_extraction_queue").select("id", count="exact").limit(1).execute()
            st.info(f"📊 Database accessible - {test_result.count} total queue items")
        except Exception as e:
            st.error(f"❌ Database query failed: {e}")
    else:
        st.error("❌ Supabase Database Not Connected")
    
    # Environment Check
    st.subheader("🔧 Environment Configuration")
    
    env_status = {
        "SUPABASE_URL": "✅" if os.getenv('SUPABASE_URL') else "❌",
        "SUPABASE_SERVICE_KEY": "✅" if os.getenv('SUPABASE_SERVICE_KEY') else "❌", 
        "OPENAI_API_KEY": "✅" if os.getenv('OPENAI_API_KEY') else "❌",
        "ANTHROPIC_API_KEY": "✅" if os.getenv('ANTHROPIC_API_KEY') else "❌",
        "GOOGLE_API_KEY": "✅" if os.getenv('GOOGLE_API_KEY') else "❌"
    }
    
    for key, status in env_status.items():
        st.write(f"{status} {key}")

# Footer
st.markdown("---")
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
st.markdown(
    f"""
    <div style='text-align: center; color: gray;'>
    OnShelf AI Agent System v1.1.0 | Last updated: {current_time} | 
    <a href='https://github.com/andreaonshelf/onshelf-ai-agent'>GitHub</a>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh logic
if auto_refresh and supabase:
    import time
    time.sleep(refresh_interval)
    st.rerun() 