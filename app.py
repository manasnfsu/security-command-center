#!/usr/bin/env python3
"""
System Monitor Dashboard - Streamlit Cloud Edition
Reads monitoring data from Firebase Firestore
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
# FIREBASE INITIALIZATION
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
                st.success(f"✅ Loading Firebase credentials from: {path}")
                cred = credentials.Certificate(path)
                break
        
        if cred is None and hasattr(st, 'secrets') and "firebase" in st.secrets:
            st.success("✅ Loading Firebase credentials from Streamlit secrets")
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
        st.success("✅ Firebase connected successfully!")
        return db
        
    except Exception as e:
        st.error(f"Firebase initialization error: {e}")
        return None

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================
@st.cache_data(ttl=30)
def fetch_all_documents(collection_name, limit=2000):
    """Fetch all documents from a collection without timestamp filtering"""
    try:
        db = st.session_state.get('firestore_db')
        if db is None:
            return pd.DataFrame()
        
        # Simple query without timestamp filter first
        docs = db.collection(collection_name).limit(limit).stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data['_id'] = doc.id
            data.append(doc_data)
        
        if data:
            df = pd.DataFrame(data)
            # Convert timestamp if it exists
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Error fetching {collection_name}: {str(e)[:100]}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_collection_by_time(collection_name, hours=24, limit=2000):
    """Fetch documents from last N hours"""
    try:
        db = st.session_state.get('firestore_db')
        if db is None:
            return pd.DataFrame()
        
        # Calculate cutoff time
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()
        
        # Try to query with timestamp filter
        try:
            docs = db.collection(collection_name)\
                .where(filter=firestore.FieldFilter("timestamp", ">=", cutoff_str))\
                .limit(limit)\
                .stream()
        except:
            # Fallback to get all if timestamp filter fails
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
                # Filter by time in pandas if Firestore filter didn't work
                if hours < 168:  # Only filter if not "all time"
                    df = df[df['timestamp'] >= cutoff]
            return df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Error in time filter for {collection_name}: {str(e)[:100]}")
        # Fallback to get all documents
        return fetch_all_documents(collection_name, limit)

def get_collection_count(collection_name):
    """Get count of documents in a collection"""
    try:
        db = st.session_state.get('firestore_db')
        if db is None:
            return 0
        
        # Use aggregation query for count
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
    """Render dashboard header"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🖥️ System Monitor Dashboard")
        st.caption("Real-time system monitoring and threat detection")
    
    with col2:
        hours = st.selectbox(
            "⏱️ Time Range",
            [6, 12, 24, 48, 168, 720, 8760],
            format_func=lambda x: {
                6: "Last 6 hours", 
                12: "Last 12 hours", 
                24: "Last 24 hours", 
                48: "Last 2 days", 
                168: "Last 7 days", 
                720: "Last 30 days",
                8760: "All time"
            }[x],
            index=2
        )
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    return hours

def render_stats_cards(hours):
    """Render statistics cards"""
    st.subheader("📊 System Overview")
    
    with st.spinner("Loading statistics..."):
        # Fetch data from collections
        alerts_df = fetch_collection_by_time('alerts', hours)
        packets_df = fetch_collection_by_time('network_packets', hours)
        processes_df = fetch_all_documents('processes', 500)
        threats_df = fetch_collection_by_time('network_threats', hours)
        dns_df = fetch_collection_by_time('dns_queries', hours)
        usb_df = fetch_collection_by_time('usb_devices', hours)
        http_df = fetch_collection_by_time('http_transactions', hours)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        alert_count = len(alerts_df)
        st.metric("🚨 Alerts", alert_count, 
                 delta="Total" if alert_count > 0 else None)
    
    with col2:
        packet_count = len(packets_df)
        st.metric("📦 Packets", f"{packet_count:,}" if packet_count > 0 else "0")
    
    with col3:
        proc_count = len(processes_df)
        st.metric("🔄 Processes", proc_count)
    
    with col4:
        threat_count = len(threats_df)
        st.metric("⚠️ Threats", threat_count)
    
    with col5:
        dns_count = len(dns_df)
        st.metric("🌐 DNS", f"{dns_count:,}" if dns_count > 0 else "0")
    
    with col6:
        usb_count = len(usb_df)
        st.metric("💾 USB", usb_count)
    
    # Show if data is loading properly
    if alert_count == 0 and hours < 168:
        st.info(f"💡 No alerts found in the last {hours} hours. Try selecting 'All time' or check if data exists in Firebase.")
        with st.expander("Debug: Check available data"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("Available collections with data:")
                collections = ['alerts', 'network_packets', 'network_threats', 'dns_queries', 'usb_devices']
                for coll in collections:
                    count = get_collection_count(coll)
                    if count > 0:
                        st.success(f"✅ {coll}: {count} documents")
                    else:
                        st.warning(f"⚠️ {coll}: No documents found")
            
            with col2:
                st.write("Sample alert document:")
                sample = fetch_all_documents('alerts', 5)
                if not sample.empty:
                    st.dataframe(sample.head(2))

def render_network_analysis(hours):
    """Render network monitoring section"""
    st.subheader("🌐 Network Analysis")
    
    tab1, tab2, tab3 = st.tabs(["📡 Network Packets", "🌍 DNS Queries", "🌐 HTTP Traffic"])
    
    with tab1:
        with st.spinner("Loading network data..."):
            packets_df = fetch_collection_by_time('network_packets', hours, limit=1000)
        
        if not packets_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                if 'packet_type' in packets_df.columns:
                    packet_types = packets_df['packet_type'].value_counts().head(10)
                    if not packet_types.empty:
                        fig = px.pie(values=packet_types.values, names=packet_types.index, title="Packet Types")
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'ip_src' in packets_df.columns:
                    top_src = packets_df['ip_src'].value_counts().head(10)
                    if not top_src.empty:
                        fig = px.bar(x=top_src.values, y=top_src.index, orientation='h', title="Top Source IPs")
                        st.plotly_chart(fig, use_container_width=True)
            
            # Packet timeline
            if len(packets_df) > 1:
                packets_over_time = packets_df.set_index('timestamp').resample('1min').size()
                if not packets_over_time.empty:
                    fig = px.line(x=packets_over_time.index, y=packets_over_time.values, title="Packet Rate (per minute)")
                    st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Recent Network Packets"):
                display_cols = ['timestamp', 'packet_type', 'ip_src', 'ip_dst']
                available_cols = [col for col in display_cols if col in packets_df.columns]
                st.dataframe(packets_df[available_cols].head(20), use_container_width=True)
        else:
            st.info("📭 No network packet data available for this time range")
    
    with tab2:
        with st.spinner("Loading DNS data..."):
            dns_df = fetch_collection_by_time('dns_queries', hours, limit=1000)
        
        if not dns_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                top_dns = dns_df['query_name'].value_counts().head(10)
                if not top_dns.empty:
                    fig = px.bar(x=top_dns.values, y=top_dns.index, orientation='h', title="Top DNS Queries")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if len(dns_df) > 1:
                    dns_over_time = dns_df.set_index('timestamp').resample('5min').size()
                    if not dns_over_time.empty:
                        fig = px.line(x=dns_over_time.index, y=dns_over_time.values, title="DNS Query Rate")
                        st.plotly_chart(fig, use_container_width=True)
            
            # Suspicious DNS (high entropy)
            if 'entropy' in dns_df.columns:
                suspicious = dns_df[dns_df['entropy'] > 4.0].nlargest(10, 'entropy')
                if not suspicious.empty:
                    st.warning("⚠️ High Entropy DNS Queries (Potential Tunneling)")
                    st.dataframe(suspicious[['timestamp', 'query_name', 'entropy']], use_container_width=True)
        else:
            st.info("📭 No DNS query data available")
    
    with tab3:
        with st.spinner("Loading HTTP data..."):
            http_df = fetch_collection_by_time('http_transactions', hours, limit=500)
        
        if not http_df.empty:
            # Top HTTP hosts
            top_hosts = http_df['host'].value_counts().head(10)
            if not top_hosts.empty:
                fig = px.bar(x=top_hosts.values, y=top_hosts.index, orientation='h', title="Top HTTP Hosts")
                st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("Recent HTTP Transactions"):
                st.dataframe(http_df[['timestamp', 'method', 'host', 'uri']].head(20), use_container_width=True)
        else:
            st.info("📭 No HTTP transaction data available")

def render_threats_alerts(hours):
    """Render threats and alerts section"""
    st.subheader("⚠️ Security Threats & Alerts")
    
    tab1, tab2 = st.tabs(["🚨 Active Threats", "📋 Alert History"])
    
    with tab1:
        with st.spinner("Loading threats..."):
            threats_df = fetch_collection_by_time('network_threats', hours, limit=500)
        
        if not threats_df.empty:
            open_threats = threats_df[threats_df.get('status', 'OPEN') == 'OPEN'] if 'status' in threats_df.columns else threats_df
            
            if not open_threats.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    threat_types = open_threats['threat_type'].value_counts()
                    if not threat_types.empty:
                        fig = px.bar(x=threat_types.values, y=threat_types.index, orientation='h', title="Threat Types")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if 'severity' in open_threats.columns:
                        severity_dist = open_threats['severity'].value_counts()
                        if not severity_dist.empty:
                            colors = {'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'green'}
                            fig = px.pie(values=severity_dist.values, names=severity_dist.index, title="Threat Severity")
                            st.plotly_chart(fig, use_container_width=True)
                
                # Display threats table
                display_cols = ['timestamp', 'threat_type', 'severity', 'process_name', 'remote_ip', 'remote_port']
                available_cols = [col for col in display_cols if col in open_threats.columns]
                st.dataframe(open_threats[available_cols], use_container_width=True)
            else:
                st.success("✅ No open threats detected")
        else:
            st.info("📭 No threat data available")
    
    with tab2:
        with st.spinner("Loading alerts..."):
            alerts_df = fetch_collection_by_time('alerts', hours, limit=1000)
        
        if not alerts_df.empty:
            # Alert timeline
            if len(alerts_df) > 1:
                alerts_over_time = alerts_df.set_index('timestamp').resample('1h').size()
                if not alerts_over_time.empty:
                    fig = px.line(x=alerts_over_time.index, y=alerts_over_time.values, title="Alert Timeline")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Alert types distribution
            alert_types = alerts_df['alert_type'].value_counts().head(10)
            if not alert_types.empty:
                fig = px.bar(x=alert_types.values, y=alert_types.index, orientation='h', title="Top Alert Types")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent alerts
            with st.expander("Recent Alerts", expanded=True):
                display_cols = ['timestamp', 'alert_type', 'severity', 'description']
                available_cols = [col for col in display_cols if col in alerts_df.columns]
                if available_cols:
                    st.dataframe(alerts_df[available_cols].head(50), use_container_width=True)
                else:
                    st.dataframe(alerts_df.head(50), use_container_width=True)
        else:
            st.info("📭 No alert data available")

def render_performance(hours):
    """Render performance metrics section"""
    st.subheader("📈 System Performance")
    
    with st.spinner("Loading performance data..."):
        perf_df = fetch_collection_by_time('performance', hours, limit=500)
    
    if not perf_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'cpu_percent' in perf_df.columns:
                fig = px.line(perf_df, x='timestamp', y='cpu_percent', title="CPU Usage %")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
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
                uptime = latest.get('uptime', 0)
                st.metric("Uptime", f"{uptime:.1f} hours" if uptime < 24 else f"{uptime/24:.1f} days")
    else:
        st.info("📭 No performance data available")

def render_usb_monitoring(hours):
    """Render USB monitoring section"""
    st.subheader("💾 USB Device Monitoring")
    
    with st.spinner("Loading USB data..."):
        usb_devices_df = fetch_collection_by_time('usb_devices', hours, limit=500)
        usb_files_df = fetch_collection_by_time('usb_file_activity', hours, limit=500)
    
    if not usb_devices_df.empty or not usb_files_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            if not usb_devices_df.empty and 'event_type' in usb_devices_df.columns:
                device_events = usb_devices_df['event_type'].value_counts()
                if not device_events.empty:
                    fig = px.pie(values=device_events.values, names=device_events.index, title="USB Device Events")
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not usb_files_df.empty and 'risk_level' in usb_files_df.columns:
                risk_levels = usb_files_df['risk_level'].value_counts()
                if not risk_levels.empty:
                    fig = px.bar(x=risk_levels.values, y=risk_levels.index, orientation='h', title="File Risk Levels")
                    st.plotly_chart(fig, use_container_width=True)
        
        if not usb_devices_df.empty:
            with st.expander("Recent USB Devices"):
                display_cols = ['timestamp', 'event_type', 'drive_letter', 'volume_label']
                available_cols = [col for col in display_cols if col in usb_devices_df.columns]
                st.dataframe(usb_devices_df[available_cols].head(20), use_container_width=True)
        
        if not usb_files_df.empty:
            with st.expander("Recent USB File Activity"):
                display_cols = ['timestamp', 'operation', 'file_path', 'risk_level']
                available_cols = [col for col in display_cols if col in usb_files_df.columns]
                if available_cols:
                    st.dataframe(usb_files_df[available_cols].head(30), use_container_width=True)
                else:
                    st.dataframe(usb_files_df.head(30), use_container_width=True)
    else:
        st.info("📭 No USB monitoring data available")

def render_sidebar():
    """Render sidebar"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=80)
        st.markdown("## System Monitor")
        st.markdown("---")
        
        db = st.session_state.get('firestore_db')
        if db:
            st.success("✅ Firebase Connected")
            
            # Show total counts
            st.markdown("### 📊 Database Stats")
            collections = {
                "Alerts": "alerts",
                "Network Packets": "network_packets",
                "Processes": "processes",
                "Threats": "network_threats",
                "DNS Queries": "dns_queries",
                "USB Devices": "usb_devices",
                "HTTP": "http_transactions"
            }
            
            for name, coll in collections.items():
                count = get_collection_count(coll)
                if count > 0:
                    st.caption(f"📁 {name}: {count:,}")
        else:
            st.error("❌ Firebase Disconnected")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("Monitors network traffic, processes, files, USB devices, and security threats")
        
        # Show last update time
        st.caption(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Data source info
        with st.expander("📖 Data Sources"):
            st.markdown("""
            - **Alerts**: Security alerts from all monitors
            - **Network Packets**: Captured network traffic
            - **DNS Queries**: DNS lookup requests
            - **Threats**: Detected security threats
            - **USB Devices**: Connected USB devices
            - **Performance**: System performance metrics
            """)

# ============================================
# MAIN FUNCTION
# ============================================
def main():
    # Initialize Firebase and store in session state
    if 'firestore_db' not in st.session_state:
        db = init_firebase()
        st.session_state['firestore_db'] = db
    
    db = st.session_state['firestore_db']
    
    if db is None:
        st.error("Failed to connect to Firebase. Please check your credentials.")
        st.stop()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    hours = render_header()
    
    # Dashboard sections
    render_stats_cards(hours)
    render_network_analysis(hours)
    render_threats_alerts(hours)
    render_performance(hours)
    render_usb_monitoring(hours)
    
    # Footer
    st.markdown("---")
    st.caption(f"System Monitor Dashboard | Data from Firebase Firestore | Time range: {hours} hours")

if __name__ == "__main__":
    main()
