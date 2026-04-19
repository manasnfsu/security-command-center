#!/usr/bin/env python3
"""
System Monitor Dashboard - Streamlit Cloud Edition
Reads monitoring data from Firebase Firestore
Based on the working OT-IoT example pattern
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import time

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="System Monitor Dashboard",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS FOR HACKER STYLE (Like the OT-IoT example)
# ============================================
typewriter_css = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
}

/* Typewriter Container */
.typewriter {
    color: #00ff88;
    font-family: 'Courier New', monospace;
    font-size: 32px;
    width: 100%;
    overflow: hidden;
    white-space: nowrap;
    border-right: 3px solid #00ff88;
    animation: typing 4s steps(30, end), blink 0.7s infinite;
    margin: 0 auto;
    text-align: center;
    padding-top: 15px;
}

/* Typing animation */
@keyframes typing {
    from { width: 0 }
    to { width: 100% }
}

/* Cursor blink */
@keyframes blink {
    from { border-color: transparent }
    to { border-color: #00ff88; }
}

/* Metric cards */
.metric-card {
    background: rgba(0, 255, 136, 0.1);
    border: 1px solid #00ff88;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
}

/* Alert styling */
.stAlert {
    border-left: 5px solid #00ff88;
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #1a1a2e;
}
::-webkit-scrollbar-thumb {
    background: #00ff88;
    border-radius: 4px;
}
</style>
"""

st.markdown(typewriter_css, unsafe_allow_html=True)

# Typewriter header
st.markdown(
    """
    <div class="typewriter">
        🔐 System Monitor & Threat Detection Console
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# FIREBASE INITIALIZATION (Like OT-IoT but for Firestore)
# ============================================
@st.cache_resource
def init_firebase():
    """Initialize Firebase using JSON file from repo"""
    try:
        if firebase_admin._apps:
            return firestore.client()
        
        # Look for Firebase credentials file
        json_paths = [
            'firebase_credentials.json',
            'firebase.json',
            'credentials.json'
        ]
        
        cred = None
        for path in json_paths:
            if os.path.exists(path):
                st.success(f"✅ Firebase connected using: {path}")
                cred = credentials.Certificate(path)
                break
        
        if cred is None and hasattr(st, 'secrets') and "firebase" in st.secrets:
            st.success("✅ Firebase connected using Streamlit secrets")
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
        
        if cred is None:
            st.error("""
            ❌ Firebase credentials not found!
            
            Please add `firebase_credentials.json` to your repository root.
            """)
            return None
        
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        # Test connection
        st.success("✅ Firebase Firestore connected successfully!")
        return db
        
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        return None

# ============================================
# DATA FETCHING FUNCTIONS (Based on OT-IoT pattern)
# ============================================
@st.cache_data(ttl=30)
def fetch_collection_data(collection_name, limit=2000):
    """
    Fetch data from Firestore collection
    Similar to fetch_raw_data in OT-IoT example
    """
    try:
        db = st.session_state.get('firestore_db')
        if db is None:
            return pd.DataFrame()
        
        # Get documents
        docs = db.collection(collection_name).limit(limit).stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            data.append(doc_data)
        
        if data:
            df = pd.DataFrame(data)
            # Convert timestamp if exists
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
        
    except Exception as e:
        st.warning(f"Error fetching {collection_name}: {str(e)[:100]}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_collection_by_time(collection_name, hours=24, limit=2000):
    """
    Fetch data for last N hours
    """
    try:
        db = st.session_state.get('firestore_db')
        if db is None:
            return pd.DataFrame()
        
        # Calculate cutoff
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        # Try to filter by timestamp
        try:
            docs = db.collection(collection_name)\
                .where(filter=firestore.FieldFilter("timestamp", ">=", cutoff_str))\
                .limit(limit)\
                .stream()
        except:
            # Fallback to get all
            docs = db.collection(collection_name).limit(limit).stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            data.append(doc_data)
        
        if data:
            df = pd.DataFrame(data)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # Filter in pandas if needed
                if hours < 168:
                    df = df[df['timestamp'] >= cutoff]
            return df
        return pd.DataFrame()
        
    except Exception as e:
        return fetch_collection_data(collection_name, limit)

def get_collection_count(collection_name):
    """Get total document count in collection"""
    try:
        db = st.session_state.get('firestore_db')
        if db is None:
            return 0
        
        # Use aggregation for count
        try:
            count_query = db.collection(collection_name).count()
            result = count_query.get()
            return result[0][0]
        except:
            # Fallback to limit query
            docs = db.collection(collection_name).limit(1000).stream()
            return sum(1 for _ in docs)
    except:
        return 0

# ============================================
# DASHBOARD COMPONENTS
# ============================================
def render_header():
    """Render dashboard header with time range selector"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("### 📊 System Overview")
        st.caption("Real-time monitoring and threat detection")
    
    with col2:
        hours = st.selectbox(
            "⏱️ Time Range",
            [1, 6, 12, 24, 48, 168, 720],
            format_func=lambda x: {
                1: "Last hour", 
                6: "Last 6 hours", 
                12: "Last 12 hours", 
                24: "Last 24 hours", 
                48: "Last 2 days", 
                168: "Last 7 days",
                720: "Last 30 days"
            }[x],
            index=3
        )
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    return hours

def render_stats_cards(hours):
    """Render statistics cards - similar to OT-IoT metrics"""
    st.markdown("### 📈 Live Statistics")
    
    with st.spinner("Loading data..."):
        # Fetch all collections
        alerts_df = fetch_collection_by_time('alerts', hours)
        packets_df = fetch_collection_by_time('network_packets', hours)
        threats_df = fetch_collection_by_time('network_threats', hours)
        dns_df = fetch_collection_by_time('dns_queries', hours)
        processes_df = fetch_collection_data('processes', 500)
        usb_df = fetch_collection_by_time('usb_devices', hours)
    
    # Create metrics row
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        alert_count = len(alerts_df)
        st.metric(
            "🚨 Alerts", 
            alert_count,
            delta="Active" if alert_count > 0 else None,
            help="Total security alerts"
        )
    
    with col2:
        packet_count = len(packets_df)
        st.metric(
            "📦 Packets", 
            f"{packet_count:,}" if packet_count > 0 else "0",
            help="Network packets captured"
        )
    
    with col3:
        threat_count = len(threats_df)
        st.metric(
            "⚠️ Threats", 
            threat_count,
            delta="Open" if threat_count > 0 else None,
            help="Detected threats"
        )
    
    with col4:
        dns_count = len(dns_df)
        st.metric(
            "🌐 DNS", 
            f"{dns_count:,}" if dns_count > 0 else "0",
            help="DNS queries"
        )
    
    with col5:
        proc_count = len(processes_df)
        st.metric(
            "🔄 Processes", 
            proc_count,
            help="Running processes"
        )
    
    with col6:
        usb_count = len(usb_df)
        st.metric(
            "💾 USB", 
            usb_count,
            help="USB devices"
        )
    
    # Show debug info if no data
    if alert_count == 0 and hours < 168:
        with st.expander("ℹ️ No data? Click to check database status"):
            st.info("Checking Firebase collections...")
            collections_to_check = ['alerts', 'network_packets', 'network_threats', 'dns_queries']
            for coll in collections_to_check:
                count = get_collection_count(coll)
                if count > 0:
                    st.success(f"✅ {coll}: {count} documents found")
                else:
                    st.warning(f"⚠️ {coll}: No documents found")
            
            st.markdown("**💡 Tips:**")
            st.markdown("- Try selecting 'Last 30 days' or 'All time'")
            st.markdown("- Check if your monitor agent is running and sending data")
            st.markdown("- Verify Firebase credentials have read access")

def render_alerts_section(hours):
    """Render alerts and threats section - similar to OT-IoT anomaly display"""
    st.markdown("### 🚨 Security Alerts & Threats")
    
    with st.spinner("Loading alerts..."):
        alerts_df = fetch_collection_by_time('alerts', hours, limit=500)
        threats_df = fetch_collection_by_time('network_threats', hours, limit=500)
    
    tab1, tab2 = st.tabs(["📋 Recent Alerts", "⚠️ Active Threats"])
    
    with tab1:
        if not alerts_df.empty:
            # Alert timeline chart
            alerts_over_time = alerts_df.set_index('timestamp').resample('1h').size()
            if len(alerts_over_time) > 1:
                fig = px.line(
                    x=alerts_over_time.index, 
                    y=alerts_over_time.values, 
                    title="Alert Timeline",
                    labels={'x': 'Time', 'y': 'Alert Count'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#00ff88'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Alert types distribution
            alert_types = alerts_df['alert_type'].value_counts().head(10)
            if not alert_types.empty:
                fig = px.bar(
                    x=alert_types.values, 
                    y=alert_types.index, 
                    orientation='h',
                    title="Alert Types Distribution",
                    labels={'x': 'Count', 'y': 'Alert Type'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#00ff88'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Alert table
            st.markdown("#### Recent Alerts")
            display_cols = ['timestamp', 'alert_type', 'severity', 'description']
            available_cols = [col for col in display_cols if col in alerts_df.columns]
            if available_cols:
                st.dataframe(
                    alerts_df[available_cols].head(50),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("📭 No alerts found in selected time range")
    
    with tab2:
        if not threats_df.empty:
            open_threats = threats_df[threats_df.get('status', 'OPEN') == 'OPEN'] if 'status' in threats_df.columns else threats_df
            
            if not open_threats.empty:
                # Threat severity distribution
                if 'severity' in open_threats.columns:
                    severity_colors = {'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'yellow'}
                    severity_counts = open_threats['severity'].value_counts()
                    fig = px.pie(
                        values=severity_counts.values,
                        names=severity_counts.index,
                        title="Threat Severity Distribution",
                        color=severity_counts.index,
                        color_discrete_map=severity_colors
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Threats table
                st.markdown("#### Active Threats")
                display_cols = ['timestamp', 'threat_type', 'severity', 'process_name', 'remote_ip']
                available_cols = [col for col in display_cols if col in open_threats.columns]
                if available_cols:
                    st.dataframe(
                        open_threats[available_cols].head(50),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.success("✅ No open threats detected")
        else:
            st.info("📭 No threat data found")

def render_network_section(hours):
    """Render network analysis section"""
    st.markdown("### 🌐 Network Traffic Analysis")
    
    with st.spinner("Loading network data..."):
        packets_df = fetch_collection_by_time('network_packets', hours, limit=1000)
        dns_df = fetch_collection_by_time('dns_queries', hours, limit=500)
    
    if not packets_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Packet type distribution
            if 'packet_type' in packets_df.columns:
                packet_types = packets_df['packet_type'].value_counts()
                if not packet_types.empty:
                    fig = px.pie(
                        values=packet_types.values,
                        names=packet_types.index,
                        title="Packet Type Distribution"
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#00ff88'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top source IPs
            if 'ip_src' in packets_df.columns:
                top_src = packets_df['ip_src'].value_counts().head(10)
                if not top_src.empty:
                    fig = px.bar(
                        x=top_src.values,
                        y=top_src.index,
                        orientation='h',
                        title="Top Source IPs",
                        labels={'x': 'Packet Count', 'y': 'IP Address'}
                    )
                    fig.update_layout(
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#00ff88'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Packet timeline
        if len(packets_df) > 1:
            packets_over_time = packets_df.set_index('timestamp').resample('5min').size()
            if len(packets_over_time) > 1:
                fig = px.line(
                    x=packets_over_time.index,
                    y=packets_over_time.values,
                    title="Network Traffic Over Time",
                    labels={'x': 'Time', 'y': 'Packets per 5min'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#00ff88'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent packets
        with st.expander("📡 Recent Network Packets"):
            display_cols = ['timestamp', 'packet_type', 'ip_src', 'ip_dst']
            available_cols = [col for col in display_cols if col in packets_df.columns]
            if available_cols:
                st.dataframe(packets_df[available_cols].head(30), use_container_width=True, hide_index=True)
    else:
        st.info("📭 No network packet data available")
    
    # DNS Section
    if not dns_df.empty:
        st.markdown("#### DNS Queries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            top_dns = dns_df['query_name'].value_counts().head(10)
            if not top_dns.empty:
                fig = px.bar(
                    x=top_dns.values,
                    y=top_dns.index,
                    orientation='h',
                    title="Top DNS Queries",
                    labels={'x': 'Query Count', 'y': 'Domain'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#00ff88'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'entropy' in dns_df.columns:
                suspicious = dns_df[dns_df['entropy'] > 4.0]
                if not suspicious.empty:
                    st.warning(f"⚠️ {len(suspicious)} high-entropy DNS queries detected (potential tunneling)")
        
        with st.expander("🌍 Recent DNS Queries"):
            display_cols = ['timestamp', 'query_name', 'entropy']
            available_cols = [col for col in display_cols if col in dns_df.columns]
            if available_cols:
                st.dataframe(dns_df[available_cols].head(30), use_container_width=True, hide_index=True)

def render_performance_section(hours):
    """Render performance metrics section"""
    st.markdown("### 📈 System Performance")
    
    with st.spinner("Loading performance data..."):
        perf_df = fetch_collection_by_time('performance', hours, limit=500)
    
    if not perf_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'cpu_percent' in perf_df.columns:
                fig = px.line(
                    perf_df,
                    x='timestamp',
                    y='cpu_percent',
                    title="CPU Usage %",
                    labels={'timestamp': 'Time', 'cpu_percent': 'CPU %'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#00ff88'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'memory_percent' in perf_df.columns:
                fig = px.line(
                    perf_df,
                    x='timestamp',
                    y='memory_percent',
                    title="Memory Usage %",
                    labels={'timestamp': 'Time', 'memory_percent': 'Memory %'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#00ff88'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Current metrics
        latest = perf_df.iloc[-1] if not perf_df.empty else None
        if latest is not None:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current CPU", f"{latest.get('cpu_percent', 0):.1f}%")
            with col2:
                st.metric("Current Memory", f"{latest.get('memory_percent', 0):.1f}%")
            with col3:
                st.metric("Processes", f"{latest.get('processes_count', 0):,}")
            with col4:
                uptime = latest.get('uptime', 0)
                st.metric("Uptime", f"{uptime:.1f}h" if uptime < 24 else f"{uptime/24:.1f}d")
    else:
        st.info("📭 No performance data available")

def render_sidebar():
    """Render sidebar with system info - similar to OT-IoT sidebar"""
    with st.sidebar:
        st.markdown("### 🔐 System Monitor")
        st.markdown("---")
        
        db = st.session_state.get('firestore_db')
        if db:
            st.success("✅ Firebase Connected")
        else:
            st.error("❌ Firebase Disconnected")
        
        st.markdown("---")
        st.markdown("### 📊 Database Status")
        
        # Show collection counts
        collections = {
            "Alerts": "alerts",
            "Network Packets": "network_packets",
            "Threats": "network_threats",
            "DNS Queries": "dns_queries",
            "Processes": "processes",
            "USB Devices": "usb_devices"
        }
        
        for name, coll in collections.items():
            count = get_collection_count(coll)
            if count > 0:
                st.caption(f"📁 {name}: {count:,}")
            else:
                st.caption(f"📁 {name}: 0")
        
        st.markdown("---")
        st.markdown("### ℹ️ System Info")
        st.caption("Monitoring network traffic, processes, USB devices, and security threats")
        st.caption(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.markdown("---")
        st.markdown("### 🛡️ Features")
        st.markdown("""
        - Real-time threat detection
        - Network traffic analysis
        - Process monitoring
        - USB device tracking
        - DNS query inspection
        - Performance metrics
        """)

# ============================================
# MAIN FUNCTION (Like OT-IoT main)
# ============================================
def main():
    # Initialize Firebase
    if 'firestore_db' not in st.session_state:
        db = init_firebase()
        st.session_state['firestore_db'] = db
    
    db = st.session_state['firestore_db']
    
    if db is None:
        st.error("Failed to connect to Firebase. Please check credentials.")
        st.stop()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    hours = render_header()
    
    # Dashboard sections
    render_stats_cards(hours)
    st.markdown("---")
    render_alerts_section(hours)
    st.markdown("---")
    render_network_section(hours)
    st.markdown("---")
    render_performance_section(hours)
    
    # Footer
    st.markdown("---")
    st.caption(f"🖥️ System Monitor Dashboard | Data from Firebase Firestore | Time range: Last {hours} hours")

if __name__ == "__main__":
    main()
