#!/usr/bin/env python3
"""
System Monitor Dashboard - Streamlit Cloud Edition
Reads monitoring data from Firebase Firestore
Supports Firebase credentials from JSON file in repo
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
import os
from collections import Counter, defaultdict

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
@st.cache_resource
def init_firebase():
    """Initialize Firebase using JSON file from repo or secrets"""
    try:
        # Check if already initialized
        if firebase_admin._apps:
            return firestore.client()
        
        # Method 1: Try to load from JSON file in repo
        json_paths = [
            'firebase_credentials.json',
            'firebase.json',
            'credentials.json',
            'config/firebase_credentials.json'
        ]
        
        cred = None
        for path in json_paths:
            if os.path.exists(path):
                st.info(f"✅ Loading Firebase credentials from: {path}")
                cred = credentials.Certificate(path)
                break
        
        # Method 2: Try Streamlit secrets (fallback)
        if cred is None and st.secrets:
            try:
                if "firebase" in st.secrets:
                    st.info("✅ Loading Firebase credentials from Streamlit secrets")
                    firebase_creds = st.secrets["firebase"]
                    cred = credentials.Certificate(firebase_creds)
            except:
                pass
        
        # Method 3: Try environment variable
        if cred is None:
            firebase_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
            if firebase_json:
                st.info("✅ Loading Firebase credentials from environment variable")
                cred_dict = json.loads(firebase_json)
                cred = credentials.Certificate(cred_dict)
        
        if cred is None:
            st.error("""
            ❌ Firebase credentials not found!
            
            Please add `firebase_credentials.json` to your repository root.
            
            **How to get the file:**
            1. Go to Firebase Console → Project Settings → Service Accounts
            2. Click "Generate New Private Key"
            3. Download the JSON file
            4. Rename it to `firebase_credentials.json`
            5. Add it to your Git repository root
            """)
            return None
        
        firebase_admin.initialize_app(cred)
        return firestore.client()
        
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        return None

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================
@st.cache_data(ttl=30)
def fetch_collection(db, collection_name, limit=2000):
    """Fetch data from Firestore collection"""
    try:
        if db is None:
            return pd.DataFrame()
        
        # Try to get recent documents first
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
        # Don't show error for missing collections
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_time_range_data(db, collection_name, hours=24):
    """Fetch data for last N hours"""
    try:
        if db is None:
            return pd.DataFrame()
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        docs = db.collection(collection_name).where('timestamp', '>=', cutoff.isoformat()).limit(5000).stream()
        
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

def get_collection_stats(db):
    """Get counts for all collections"""
    collections = [
        'alerts', 'network_packets', 'processes', 'network_threats',
        'usb_devices', 'dns_queries', 'http_transactions', 'file_operations'
    ]
    
    stats = {}
    for coll in collections:
        try:
            count = db.collection(coll).count().get()[0][0]
            stats[coll] = count
        except:
            stats[coll] = 0
    
    return stats

# ============================================
# DASHBOARD COMPONENTS
# ============================================
def render_header():
    """Render dashboard header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🖥️ System Monitor Dashboard")
        st.caption("Real-time system monitoring and threat detection | Data from Firebase")
    
    with col2:
        hours = st.selectbox(
            "⏱️ Time Range",
            [1, 6, 12, 24, 48, 168],
            format_func=lambda x: f"Last {x} hours" if x < 24 else f"Last {x//24} days",
            index=3
        )
    
    with col3:
        col3_1, col3_2 = st.columns(2)
        with col3_1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col3_2:
            if st.button("📊 Stats", use_container_width=True):
                st.cache_data.clear()
    
    return hours

def render_stats_cards(db, hours):
    """Render statistics cards"""
    st.subheader("📊 System Overview")
    
    # Get counts from different collections
    with st.spinner("Loading stats..."):
        alerts_df = get_time_range_data(db, 'alerts', hours)
        packets_df = get_time_range_data(db, 'network_packets', hours)
        processes_df = get_time_range_data(db, 'processes', hours)
        threats_df = get_time_range_data(db, 'network_threats', hours)
        usb_devices_df = get_time_range_data(db, 'usb_devices', hours)
        dns_df = get_time_range_data(db, 'dns_queries', hours)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        active_alerts = len(alerts_df[alerts_df.get('resolved', 0) == 0]) if not alerts_df.empty else 0
        st.metric(
            "🚨 Active Alerts",
            active_alerts,
            delta=None,
            help="Unresolved alerts"
        )
    
    with col2:
        st.metric(
            "📦 Packets",
            f"{len(packets_df):,}",
            delta=None,
            help=f"Network packets in last {hours} hours"
        )
    
    with col3:
        st.metric(
            "🔄 Processes",
            len(processes_df) if not processes_df.empty else 0,
            delta=None,
            help="Currently running processes"
        )
    
    with col4:
        open_threats = len(threats_df[threats_df.get('status', 'OPEN') == 'OPEN']) if not threats_df.empty else 0
        st.metric(
            "⚠️ Open Threats",
            open_threats,
            delta=None,
            help="Active security threats"
        )
    
    with col5:
        usb_count = len(usb_devices_df[usb_devices_df.get('event_type') == 'CONNECTED']) if not usb_devices_df.empty else 0
        st.metric(
            "💾 USB Devices",
            usb_count,
            delta=None,
            help="Connected USB devices"
        )
    
    with col6:
        st.metric(
            "🌐 DNS Queries",
            f"{len(dns_df):,}",
            delta=None,
            help=f"DNS queries in last {hours} hours"
        )

def render_network_analysis(db, hours):
    """Render network monitoring section"""
    st.subheader("🌐 Network Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📡 Packets", "🌍 DNS", "🌐 HTTP", "📊 Flows"])
    
    with st.spinner("Loading network data..."):
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
                if not packet_types.empty:
                    fig = px.pie(values=packet_types.values, names=packet_types.index, title="Packet Types")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No packet type data")
            
            with col2:
                # Top source IPs
                if 'ip_src' in packets_df.columns:
                    top_src = packets_df['ip_src'].value_counts().head(10)
                    if not top_src.empty:
                        fig = px.bar(x=top_src.values, y=top_src.index, orientation='h', title="Top Source IPs")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No IP data")
            
            # Recent packets
            with st.expander("Recent Network Packets", expanded=False):
                recent = packets_df.nlargest(20, 'timestamp')[['timestamp', 'packet_type', 'ip_src', 'ip_dst', 'tcp_srcport', 'tcp_dstport']]
                st.dataframe(recent, use_container_width=True)
        else:
            st.info("📭 No network packet data available for this time range")
    
    with tab2:
        if not dns_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top DNS queries
                top_dns = dns_df['query_name'].value_counts().head(10)
                if not top_dns.empty:
                    fig = px.bar(x=top_dns.values, y=top_dns.index, orientation='h', title="Top DNS Queries")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # DNS query timeline
                dns_over_time = dns_df.set_index('timestamp').resample('1min').size()
                if not dns_over_time.empty:
                    fig = px.line(x=dns_over_time.index, y=dns_over_time.values, title="DNS Queries Over Time")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Suspicious DNS (high entropy)
            if 'entropy' in dns_df.columns:
                suspicious = dns_df[dns_df['entropy'] > 4.0].nlargest(10, 'entropy')
                if not suspicious.empty:
                    st.warning("⚠️ High Entropy DNS Queries (Potential Tunneling)")
                    st.dataframe(suspicious[['timestamp', 'query_name', 'entropy', 'process_name']], use_container_width=True)
        else:
            st.info("📭 No DNS query data available")
    
    with tab3:
        if not http_df.empty:
            # Top HTTP hosts
            top_hosts = http_df['host'].value_counts().head(10)
            if not top_hosts.empty:
                fig = px.bar(x=top_hosts.values, y=top_hosts.index, orientation='h', title="Top HTTP Hosts")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent HTTP transactions
            with st.expander("Recent HTTP Transactions", expanded=False):
                recent_http = http_df.nlargest(20, 'timestamp')[['timestamp', 'method', 'host', 'uri', 'process_name']]
                st.dataframe(recent_http, use_container_width=True)
        else:
            st.info("📭 No HTTP transaction data available")
    
    with tab4:
        if not flows_df.empty:
            # Protocol distribution
            if 'protocol' in flows_df.columns:
                proto_dist = flows_df['protocol'].value_counts()
                if not proto_dist.empty:
                    fig = px.pie(values=proto_dist.values, names=proto_dist.index, title="Flow Protocols")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Top applications
            if 'application' in flows_df.columns:
                top_apps = flows_df['application'].value_counts().head(10)
                if not top_apps.empty:
                    fig = px.bar(x=top_apps.values, y=top_apps.index, orientation='h', title="Top Applications")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No flow data available")

def render_threats_alerts(db, hours):
    """Render threats and alerts section"""
    st.subheader("⚠️ Security Threats & Alerts")
    
    with st.spinner("Loading threats..."):
        threats_df = get_time_range_data(db, 'network_threats', hours)
        alerts_df = get_time_range_data(db, 'alerts', hours)
    
    tab1, tab2 = st.tabs(["🚨 Active Threats", "📋 Alert History"])
    
    with tab1:
        if not threats_df.empty:
            open_threats = threats_df[threats_df.get('status', 'OPEN') == 'OPEN']
            
            if not open_threats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Threat summary
                    threat_types = open_threats['threat_type'].value_counts()
                    if not threat_types.empty:
                        fig = px.bar(x=threat_types.values, y=threat_types.index, orientation='h', title="Threat Types")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Severity distribution
                    severity_dist = open_threats['severity'].value_counts()
                    if not severity_dist.empty:
                        colors = {'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'blue'}
                        fig = px.pie(values=severity_dist.values, names=severity_dist.index, title="Threat Severity", 
                                    color=severity_dist.index, color_discrete_map=colors)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Detailed threats table
                st.subheader("Open Threats")
                display_cols = ['timestamp', 'threat_type', 'severity', 'process_name', 'remote_ip', 'remote_port']
                available_cols = [col for col in display_cols if col in open_threats.columns]
                st.dataframe(open_threats[available_cols], use_container_width=True)
            else:
                st.success("✅ No open threats detected")
        else:
            st.info("📭 No threat data available")
    
    with tab2:
        if not alerts_df.empty:
            # Alerts over time
            alerts_over_time = alerts_df.set_index('timestamp').resample('1h').size()
            if not alerts_over_time.empty:
                fig = px.line(x=alerts_over_time.index, y=alerts_over_time.values, title="Alert Timeline")
                st.plotly_chart(fig, use_container_width=True)
            
            # Alert types
            alert_types = alerts_df['alert_type'].value_counts().head(10)
            if not alert_types.empty:
                fig = px.bar(x=alert_types.values, y=alert_types.index, orientation='h', title="Alert Types")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent alerts
            with st.expander("Recent Alerts", expanded=True):
                recent_alerts = alerts_df.nlargest(50, 'timestamp')[['timestamp', 'alert_type', 'severity', 'description']]
                st.dataframe(recent_alerts, use_container_width=True)
        else:
            st.info("📭 No alert data available")

def render_performance(db, hours):
    """Render performance metrics section"""
    st.subheader("📈 System Performance")
    
    with st.spinner("Loading performance data..."):
        perf_df = get_time_range_data(db, 'performance', hours)
    
    if not perf_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU usage over time
            if 'cpu_percent' in perf_df.columns:
                fig = px.line(perf_df, x='timestamp', y='cpu_percent', title="CPU Usage %")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Memory usage over time
            if 'memory_percent' in perf_df.columns:
                fig = px.line(perf_df, x='timestamp', y='memory_percent', title="Memory Usage %")
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
        st.info("📭 No performance data available")

def render_realtime_monitor(db):
    """Render real-time monitoring section"""
    st.subheader("🔄 Real-time Activity")
    
    # Auto-refresh checkbox
    auto_refresh = st.checkbox("Auto-refresh (every 10 seconds)", value=False)
    
    if auto_refresh:
        time.sleep(10)
        st.rerun()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Recent alerts
        alerts_df = fetch_collection(db, 'alerts', limit=20)
        if not alerts_df.empty:
            st.markdown("**Latest Alerts**")
            st.dataframe(alerts_df[['timestamp', 'alert_type', 'severity']].head(10), use_container_width=True)
    
    with col2:
        # Recent threats
        threats_df = fetch_collection(db, 'network_threats', limit=20)
        if not threats_df.empty:
            st.markdown("**Latest Threats**")
            st.dataframe(threats_df[['timestamp', 'threat_type', 'severity']].head(10), use_container_width=True)

# ============================================
# SIDEBAR
# ============================================
def render_sidebar(db):
    """Render sidebar with additional info"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=80)
        st.markdown("## System Monitor")
        st.markdown("---")
        
        # Firebase status
        if db:
            st.success("✅ Firebase Connected")
        else:
            st.error("❌ Firebase Disconnected")
        
        st.markdown("---")
        
        # Data sources
        st.markdown("### 📊 Data Sources")
        collections = [
            "alerts", "network_packets", "processes", "network_threats",
            "usb_devices", "dns_queries", "http_transactions", "file_operations",
            "performance", "software", "hardware"
        ]
        
        for coll in collections:
            try:
                count = db.collection(coll).count().get()[0][0] if db else 0
                st.caption(f"📁 {coll}: {count:,} records")
            except:
                st.caption(f"📁 {coll}: 0 records")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("Monitors network traffic, processes, files, USB devices, and security threats")
        st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# ============================================
# MAIN FUNCTION
# ============================================
def main():
    # Initialize Firebase
    db = init_firebase()
    
    if db is None:
        st.stop()
    
    # Render sidebar
    render_sidebar(db)
    
    # Main content
    hours = render_header()
    render_stats_cards(db, hours)
    render_network_analysis(db, hours)
    render_threats_alerts(db, hours)
    render_performance(db, hours)
    
    # Optional: Real-time monitor
    with st.expander("🔄 Real-time Activity Monitor", expanded=False):
        render_realtime_monitor(db)
    
    # Footer
    st.markdown("---")
    st.caption(f"""
    🖥️ **System Monitor Dashboard** | Data from Firebase Firestore | 
    Time range: Last {hours} hours | 
    Page refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

if __name__ == "__main__":
    main()
