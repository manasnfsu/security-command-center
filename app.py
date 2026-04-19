#!/usr/bin/env python3
"""
System Monitor Dashboard - Streamlit Cloud Edition
Reads monitoring data from Firebase Firestore
Displays: Network, Processes, Files, USB DLP, Threats, Performance
"""

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import json
from collections import Counter, defaultdict
import hashlib

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
# FIREBASE INITIALIZATION
# ============================================
def init_firebase():
    """Initialize Firebase using Streamlit secrets"""
    try:
        # Check if already initialized
        if not firebase_admin._apps:
            # Get credentials from secrets
            firebase_creds = st.secrets["firebase"]
            
            # Convert to proper format if needed
            cred_dict = {
                "type": firebase_creds.get("type"),
                "project_id": firebase_creds.get("project_id"),
                "private_key_id": firebase_creds.get("private_key_id"),
                "private_key": firebase_creds.get("private_key").replace('\\n', '\n'),
                "client_email": firebase_creds.get("client_email"),
                "client_id": firebase_creds.get("client_id"),
                "auth_uri": firebase_creds.get("auth_uri"),
                "token_uri": firebase_creds.get("token_uri"),
                "auth_provider_x509_cert_url": firebase_creds.get("auth_provider_x509_cert_url"),
                "client_x509_cert_url": firebase_creds.get("client_x509_cert_url")
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        st.info("Please add Firebase credentials to Streamlit secrets")
        return None

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================
@st.cache_data(ttl=30)
def fetch_collection(db, collection_name, limit=1000):
    """Fetch data from Firestore collection"""
    try:
        if db is None:
            return pd.DataFrame()
        
        docs = db.collection(collection_name).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            data.append(doc_data)
        
        if data:
            df = pd.DataFrame(data)
            # Convert timestamp strings to datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching {collection_name}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_time_range_data(db, collection_name, hours=24):
    """Fetch data for last N hours"""
    try:
        if db is None:
            return pd.DataFrame()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        docs = db.collection(collection_name).where('timestamp', '>=', cutoff.isoformat()).stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            data.append(doc_data)
        
        if data:
            df = pd.DataFrame(data)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# ============================================
# DASHBOARD COMPONENTS
# ============================================
def render_header():
    """Render dashboard header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🖥️ System Monitor Dashboard")
        st.caption("Real-time system monitoring and threat detection")
    
    with col2:
        hours = st.selectbox(
            "Time Range",
            [1, 6, 12, 24, 48, 168],
            format_func=lambda x: f"Last {x} hours" if x < 24 else f"Last {x//24} days",
            index=3
        )
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    return hours

def render_stats_cards(db, hours):
    """Render statistics cards"""
    st.subheader("📊 System Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Get counts from different collections
    alerts_df = get_time_range_data(db, 'alerts', hours)
    packets_df = get_time_range_data(db, 'network_packets', hours)
    processes_df = get_time_range_data(db, 'processes', hours)
    threats_df = get_time_range_data(db, 'network_threats', hours)
    usb_devices_df = get_time_range_data(db, 'usb_devices', hours)
    
    with col1:
        st.metric(
            "🚨 Active Alerts",
            len(alerts_df[alerts_df.get('resolved', 0) == 0]) if not alerts_df.empty else 0,
            delta=None
        )
    
    with col2:
        st.metric(
            "📦 Network Packets",
            f"{len(packets_df):,}",
            delta=None
        )
    
    with col3:
        st.metric(
            "🔄 Active Processes",
            len(processes_df) if not processes_df.empty else 0,
            delta=None
        )
    
    with col4:
        st.metric(
            "⚠️ Threats Detected",
            len(threats_df[threats_df.get('status', 'OPEN') == 'OPEN']) if not threats_df.empty else 0,
            delta=None
        )
    
    with col5:
        st.metric(
            "💾 USB Devices",
            len(usb_devices_df[usb_devices_df.get('event_type') == 'CONNECTED']) if not usb_devices_df.empty else 0,
            delta=None
        )

def render_network_analysis(db, hours):
    """Render network monitoring section"""
    st.subheader("🌐 Network Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📡 Network Packets", "🌍 DNS Queries", "🌐 HTTP Traffic", "📊 Flow Stats"])
    
    packets_df = get_time_range_data(db, 'network_packets', hours)
    dns_df = get_time_range_data(db, 'dns_queries', hours)
    http_df = get_time_range_data(db, 'http_transactions', hours)
    flows_df = get_time_range_data(db, 'network_flows', hours)
    
    with tab1:
        if not packets_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Packet type distribution
                packet_types = packets_df['packet_type'].value_counts().head(10)
                fig = px.pie(values=packet_types.values, names=packet_types.index, title="Packet Types")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Top source IPs
                top_src = packets_df['ip_src'].value_counts().head(10)
                fig = px.bar(x=top_src.values, y=top_src.index, orientation='h', title="Top Source IPs")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent packets
            st.subheader("Recent Network Packets")
            recent = packets_df.nlargest(20, 'timestamp')[['timestamp', 'packet_type', 'ip_src', 'ip_dst', 'tcp_srcport', 'tcp_dstport']]
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No network packet data available")
    
    with tab2:
        if not dns_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top DNS queries
                top_dns = dns_df['query_name'].value_counts().head(10)
                fig = px.bar(x=top_dns.values, y=top_dns.index, orientation='h', title="Top DNS Queries")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # DNS query timeline
                dns_over_time = dns_df.set_index('timestamp').resample('1min').size()
                fig = px.line(x=dns_over_time.index, y=dns_over_time.values, title="DNS Queries Over Time")
                st.plotly_chart(fig, use_container_width=True)
            
            # Suspicious DNS (high entropy)
            if 'entropy' in dns_df.columns:
                suspicious = dns_df[dns_df['entropy'] > 4.0].nlargest(10, 'entropy')
                if not suspicious.empty:
                    st.subheader("⚠️ High Entropy DNS Queries (Potential Tunneling)")
                    st.dataframe(suspicious[['timestamp', 'query_name', 'entropy', 'process_name']], use_container_width=True)
        else:
            st.info("No DNS query data available")
    
    with tab3:
        if not http_df.empty:
            # Top HTTP hosts
            top_hosts = http_df['host'].value_counts().head(10)
            fig = px.bar(x=top_hosts.values, y=top_hosts.index, orientation='h', title="Top HTTP Hosts")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent HTTP transactions
            recent_http = http_df.nlargest(20, 'timestamp')[['timestamp', 'method', 'host', 'uri', 'process_name']]
            st.dataframe(recent_http, use_container_width=True)
        else:
            st.info("No HTTP transaction data available")
    
    with tab4:
        if not flows_df.empty:
            # Protocol distribution
            proto_dist = flows_df['protocol'].value_counts()
            fig = px.pie(values=proto_dist.values, names=proto_dist.index, title="Flow Protocols")
            st.plotly_chart(fig, use_container_width=True)
            
            # Top applications
            top_apps = flows_df['application'].value_counts().head(10)
            fig = px.bar(x=top_apps.values, y=top_apps.index, orientation='h', title="Top Applications")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No flow data available")

def render_process_monitor(db, hours):
    """Render process monitoring section"""
    st.subheader("🔧 Process Monitoring")
    
    processes_df = get_time_range_data(db, 'processes', hours)
    process_events_df = get_time_range_data(db, 'process_events', hours)
    
    if not processes_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top processes by CPU
            if 'cpu_percent' in processes_df.columns:
                top_cpu = processes_df.nlargest(10, 'cpu_percent')[['name', 'cpu_percent', 'memory_percent', 'pid']]
                fig = px.bar(x=top_cpu['cpu_percent'], y=top_cpu['name'], orientation='h', title="Top Processes by CPU %")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top processes by memory
            if 'memory_percent' in processes_df.columns:
                top_mem = processes_df.nlargest(10, 'memory_percent')[['name', 'memory_percent', 'cpu_percent', 'pid']]
                fig = px.bar(x=top_mem['memory_percent'], y=top_mem['name'], orientation='h', title="Top Processes by Memory %")
                st.plotly_chart(fig, use_container_width=True)
        
        # Process events timeline
        if not process_events_df.empty:
            events_by_type = process_events_df['event_type'].value_counts()
            fig = px.pie(values=events_by_type.values, names=events_by_type.index, title="Process Events")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent processes
        st.subheader("Recent Processes")
        recent_procs = processes_df.nlargest(20, 'timestamp')[['timestamp', 'name', 'pid', 'username', 'cpu_percent', 'memory_percent']]
        st.dataframe(recent_procs, use_container_width=True)
    else:
        st.info("No process data available")

def render_file_monitor(db, hours):
    """Render file system monitoring section"""
    st.subheader("📁 File System Monitoring")
    
    file_ops_df = get_time_range_data(db, 'file_operations', hours)
    file_system_df = get_time_range_data(db, 'file_system', hours)
    
    if not file_ops_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # File operations by type
            ops_count = file_ops_df['operation'].value_counts()
            fig = px.bar(x=ops_count.index, y=ops_count.values, title="File Operations")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # File operations over time
            ops_over_time = file_ops_df.set_index('timestamp').resample('5min').size()
            fig = px.line(x=ops_over_time.index, y=ops_over_time.values, title="File Operations Over Time")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent file operations
        st.subheader("Recent File Operations")
        recent_ops = file_ops_df.nlargest(20, 'timestamp')[['timestamp', 'operation', 'file_path', 'process_name']]
        st.dataframe(recent_ops, use_container_width=True)
    else:
        st.info("No file operation data available")

def render_usb_dlp(db, hours):
    """Render USB DLP monitoring section"""
    st.subheader("💾 USB & DLP Monitoring")
    
    usb_devices_df = get_time_range_data(db, 'usb_devices', hours)
    usb_files_df = get_time_range_data(db, 'usb_file_activity', hours)
    
    if not usb_devices_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # USB device events
            device_events = usb_devices_df['event_type'].value_counts()
            fig = px.pie(values=device_events.values, names=device_events.index, title="USB Device Events")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Recent USB devices
            recent_devices = usb_devices_df.nlargest(10, 'timestamp')[['timestamp', 'event_type', 'drive_letter', 'volume_label', 'capacity_gb']]
            st.dataframe(recent_devices, use_container_width=True)
    
    if not usb_files_df.empty:
        st.subheader("USB File Activity")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # File operations on USB
            file_ops = usb_files_df['operation'].value_counts()
            fig = px.bar(x=file_ops.index, y=file_ops.values, title="USB File Operations")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Risk levels
            risk_levels = usb_files_df['risk_level'].value_counts()
            fig = px.pie(values=risk_levels.values, names=risk_levels.index, title="Risk Levels")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent USB file activity
        recent_files = usb_files_df.nlargest(20, 'timestamp')[['timestamp', 'operation', 'file_path', 'risk_level']]
        st.dataframe(recent_files, use_container_width=True)
    else:
        st.info("No USB activity data available")

def render_threats_alerts(db, hours):
    """Render threats and alerts section"""
    st.subheader("⚠️ Threats & Alerts")
    
    threats_df = get_time_range_data(db, 'network_threats', hours)
    alerts_df = get_time_range_data(db, 'alerts', hours)
    
    tab1, tab2 = st.tabs(["🚨 Active Threats", "📋 Alert History"])
    
    with tab1:
        if not threats_df.empty:
            open_threats = threats_df[threats_df.get('status', 'OPEN') == 'OPEN']
            
            if not open_threats.empty:
                # Threat summary
                threat_types = open_threats['threat_type'].value_counts()
                fig = px.bar(x=threat_types.values, y=threat_types.index, orientation='h', title="Threat Types")
                st.plotly_chart(fig, use_container_width=True)
                
                # Severity distribution
                severity_dist = open_threats['severity'].value_counts()
                colors = {'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'yellow'}
                fig = px.pie(values=severity_dist.values, names=severity_dist.index, title="Threat Severity", color=severity_dist.index, color_discrete_map=colors)
                st.plotly_chart(fig, use_container_width=True)
                
                # Detailed threats table
                st.subheader("Open Threats")
                st.dataframe(
                    open_threats[['timestamp', 'threat_type', 'severity', 'process_name', 'remote_ip', 'remote_port', 'status']],
                    use_container_width=True
                )
            else:
                st.success("✅ No open threats detected")
        else:
            st.info("No threat data available")
    
    with tab2:
        if not alerts_df.empty:
            # Alerts over time
            alerts_over_time = alerts_df.set_index('timestamp').resample('1h').size()
            fig = px.line(x=alerts_over_time.index, y=alerts_over_time.values, title="Alert Timeline")
            st.plotly_chart(fig, use_container_width=True)
            
            # Alert types
            alert_types = alerts_df['alert_type'].value_counts().head(10)
            fig = px.bar(x=alert_types.values, y=alert_types.index, orientation='h', title="Alert Types")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent alerts
            st.subheader("Recent Alerts")
            recent_alerts = alerts_df.nlargest(50, 'timestamp')[['timestamp', 'alert_type', 'severity', 'description']]
            st.dataframe(recent_alerts, use_container_width=True)
        else:
            st.info("No alert data available")

def render_performance(db, hours):
    """Render performance metrics section"""
    st.subheader("📈 System Performance")
    
    perf_df = get_time_range_data(db, 'performance', hours)
    
    if not perf_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU usage over time
            fig = px.line(perf_df, x='timestamp', y='cpu_percent', title="CPU Usage %")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Memory usage over time
            fig = px.line(perf_df, x='timestamp', y='memory_percent', title="Memory Usage %")
            st.plotly_chart(fig, use_container_width=True)
        
        # Network I/O
        if 'net_io_sent' in perf_df.columns and 'net_io_recv' in perf_df.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Calculate rates
                perf_df['net_io_sent_rate'] = perf_df['net_io_sent'].diff() / 60
                perf_df['net_io_recv_rate'] = perf_df['net_io_recv'].diff() / 60
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['net_io_sent_rate'], name='Sent (bytes/s)', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['net_io_recv_rate'], name='Received (bytes/s)', line=dict(color='green')))
                fig.update_layout(title="Network I/O Rate")
                st.plotly_chart(fig, use_container_width=True)
        
        # Current metrics
        st.subheader("Current Metrics")
        latest = perf_df.iloc[-1] if not perf_df.empty else None
        
        if latest is not None:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("CPU Usage", f"{latest.get('cpu_percent', 0):.1f}%")
            with col2:
                st.metric("Memory Usage", f"{latest.get('memory_percent', 0):.1f}%")
            with col3:
                st.metric("Processes", f"{latest.get('processes_count', 0):,}")
            with col4:
                st.metric("Uptime", f"{latest.get('uptime', 0):.1f} hours")
    else:
        st.info("No performance data available")

def render_software_hardware(db, hours):
    """Render software and hardware inventory"""
    st.subheader("💻 Software & Hardware Inventory")
    
    tab1, tab2 = st.tabs(["📦 Software", "🖥️ Hardware"])
    
    with tab1:
        software_df = get_time_range_data(db, 'software', hours)
        software_events_df = get_time_range_data(db, 'software_events', hours)
        
        if not software_df.empty:
            # Software count by publisher
            publishers = software_df['publisher'].value_counts().head(15)
            fig = px.bar(x=publishers.values, y=publishers.index, orientation='h', title="Top Publishers")
            st.plotly_chart(fig, use_container_width=True)
            
            # Recent software events
            if not software_events_df.empty:
                st.subheader("Software Installation/Removal Events")
                recent_events = software_events_df.nlargest(20, 'timestamp')[['timestamp', 'event_type', 'name', 'version']]
                st.dataframe(recent_events, use_container_width=True)
            
            # Software list
            with st.expander("All Installed Software"):
                st.dataframe(software_df[['name', 'version', 'publisher', 'install_date']], use_container_width=True)
        else:
            st.info("No software inventory data available")
    
    with tab2:
        cpu_df = get_time_range_data(db, 'cpu_info', hours)
        memory_df = get_time_range_data(db, 'memory_info', hours)
        disks_df = get_time_range_data(db, 'disks', hours)
        
        if not cpu_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                latest_cpu = cpu_df.iloc[-1] if not cpu_df.empty else None
                if latest_cpu is not None:
                    st.metric("CPU", latest_cpu.get('name', 'Unknown')[:50])
                    st.metric("Cores", f"{latest_cpu.get('cores', 0)} physical / {latest_cpu.get('logical_cores', 0)} logical")
                    st.metric("Max Frequency", f"{latest_cpu.get('max_freq', 0)} MHz")
            
            with col2:
                if not memory_df.empty:
                    latest_mem = memory_df.iloc[-1]
                    st.metric("Total Memory", f"{latest_mem.get('total', 0):.1f} GB")
                    st.metric("Available Memory", f"{latest_mem.get('available', 0):.1f} GB")
                    st.metric("Memory Usage", f"{latest_mem.get('percent', 0):.1f}%")
        
        if not disks_df.empty:
            st.subheader("Disk Information")
            st.dataframe(disks_df[['device', 'mountpoint', 'total', 'used', 'free', 'percent']], use_container_width=True)

# ============================================
# MAIN FUNCTION
# ============================================
def main():
    # Initialize Firebase
    db = init_firebase()
    
    if db is None:
        st.error("""
        ❌ Firebase connection failed!
        
        Please configure Firebase credentials in Streamlit secrets:
        
        1. Go to your app dashboard on Streamlit Cloud
        2. Navigate to Settings → Secrets
        3. Add your Firebase service account credentials as:
        
        ```toml
        [firebase]
        type = "service_account"
        project_id = "your-project-id"
        private_key_id = "..."
        private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
        client_email = "firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com"
        client_id = "..."
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "..."
