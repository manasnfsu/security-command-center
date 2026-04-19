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
        
        # Try Streamlit secrets as fallback
        if cred is None and hasattr(st, 'secrets') and "firebase" in st.secrets:
            st.success("✅ Loading Firebase credentials from Streamlit secrets")
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
        
        if cred is None:
            st.error("""
            ❌ Firebase credentials not found!
            
            Please add `firebase_credentials.json` to your repository root.
            
            **How to get the file:**
            1. Go to Firebase Console → Project Settings → Service Accounts
            2. Click "Generate New Private Key"
            3. Download the JSON file
            4. Rename it to `firebase_credentials.json`
            5. Add it to your Git repository
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
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        return pd.DataFrame()
    except Exception as e:
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
    
    with st.spinner("Loading statistics..."):
        alerts_df = get_time_range_data(db, 'alerts', hours)
        packets_df = get_time_range_data(db, 'network_packets', hours)
        processes_df = get_time_range_data(db, 'processes', hours)
        threats_df = get_time_range_data(db, 'network_threats', hours)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_alerts = len(alerts_df[alerts_df.get('resolved', 0) == 0]) if not alerts_df.empty else 0
        st.metric("🚨 Active Alerts", active_alerts)
    
    with col2:
        st.metric("📦 Network Packets", f"{len(packets_df):,}")
    
    with col3:
        st.metric("🔄 Active Processes", len(processes_df) if not processes_df.empty else 0)
    
    with col4:
        open_threats = len(threats_df[threats_df.get('status', 'OPEN') == 'OPEN']) if not threats_df.empty else 0
        st.metric("⚠️ Open Threats", open_threats)

def render_network_analysis(db, hours):
    """Render network monitoring section"""
    st.subheader("🌐 Network Analysis")
    
    with st.spinner("Loading network data..."):
        packets_df = get_time_range_data(db, 'network_packets', hours)
        dns_df = get_time_range_data(db, 'dns_queries', hours)
    
    if not packets_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Packet type distribution
            if 'packet_type' in packets_df.columns:
                packet_types = packets_df['packet_type'].value_counts().head(10)
                if not packet_types.empty:
                    fig = px.pie(values=packet_types.values, names=packet_types.index, title="Packet Types")
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top source IPs
            if 'ip_src' in packets_df.columns:
                top_src = packets_df['ip_src'].value_counts().head(10)
                if not top_src.empty:
                    fig = px.bar(x=top_src.values, y=top_src.index, orientation='h', title="Top Source IPs")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Recent packets
        with st.expander("Recent Network Packets"):
            recent = packets_df.nlargest(20, 'timestamp')[['timestamp', 'packet_type', 'ip_src', 'ip_dst']]
            st.dataframe(recent, use_container_width=True)
    else:
        st.info("No network packet data available")
    
    if not dns_df.empty:
        st.subheader("DNS Queries")
        
        # Suspicious DNS (high entropy)
        if 'entropy' in dns_df.columns:
            suspicious = dns_df[dns_df['entropy'] > 4.0].nlargest(10, 'entropy')
            if not suspicious.empty:
                st.warning("⚠️ High Entropy DNS Queries (Potential Tunneling)")
                st.dataframe(suspicious[['timestamp', 'query_name', 'entropy']], use_container_width=True)

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
                    threat_types = open_threats['threat_type'].value_counts()
                    if not threat_types.empty:
                        fig = px.bar(x=threat_types.values, y=threat_types.index, orientation='h', title="Threat Types")
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    severity_dist = open_threats['severity'].value_counts()
                    if not severity_dist.empty:
                        colors = {'HIGH': 'red', 'MEDIUM': 'orange', 'LOW': 'blue'}
                        fig = px.pie(values=severity_dist.values, names=severity_dist.index, title="Threat Severity")
                        st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(open_threats[['timestamp', 'threat_type', 'severity', 'remote_ip']], use_container_width=True)
            else:
                st.success("✅ No open threats detected")
        else:
            st.info("No threat data available")
    
    with tab2:
        if not alerts_df.empty:
            # Alerts over time
            alerts_over_time = alerts_df.set_index('timestamp').resample('1h').size()
            if not alerts_over_time.empty:
                fig = px.line(x=alerts_over_time.index, y=alerts_over_time.values, title="Alert Timeline")
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent alerts
            st.dataframe(alerts_df.nlargest(50, 'timestamp')[['timestamp', 'alert_type', 'severity', 'description']], use_container_width=True)
        else:
            st.info("No alert data available")

def render_performance(db, hours):
    """Render performance metrics section"""
    st.subheader("📈 System Performance")
    
    with st.spinner("Loading performance data..."):
        perf_df = get_time_range_data(db, 'performance', hours)
    
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
        latest = perf_df.iloc[-1] if not perf_df.empty else None
        if latest is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CPU Usage", f"{latest.get('cpu_percent', 0):.1f}%")
            with col2:
                st.metric("Memory Usage", f"{latest.get('memory_percent', 0):.1f}%")
            with col3:
                st.metric("Processes", f"{latest.get('processes_count', 0):,}")
    else:
        st.info("No performance data available")

def render_sidebar(db):
    """Render sidebar"""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=80)
        st.markdown("## System Monitor")
        st.markdown("---")
        
        if db:
            st.success("✅ Firebase Connected")
        else:
            st.error("❌ Firebase Disconnected")
        
        st.markdown("---")
        st.markdown("### 📊 Available Data")
        
        collections = ["alerts", "network_packets", "processes", "network_threats", "dns_queries", "performance"]
        for coll in collections:
            try:
                if db:
                    count = len(fetch_collection(db, coll, limit=100))
                    st.caption(f"📁 {coll}: {count} records")
            except:
                pass
        
        st.markdown("---")
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
    
    # Footer
    st.markdown("---")
    st.caption(f"System Monitor Dashboard | Data from Firebase Firestore | Time range: Last {hours} hours")

if __name__ == "__main__":
    main()
