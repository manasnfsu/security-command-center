#!/usr/bin/env python3
"""
NEUROFENCE2 FIREBASE DASHBOARD - Streamlit Cloud Edition
Fetches and displays data from NeuroFence2 Firebase Realtime Database
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
from datetime import datetime, timedelta
import json
import hashlib
import time
from collections import defaultdict, Counter
import re
import numpy as np

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="NeuroFence2 Security Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# FIREBASE CONFIGURATION
# ============================================
FIREBASE_HOST = "neurofence2-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_AUTH = "AIzaSyCbT1wnRE9OO_yv2LjqSIyK1InddRgDFsY"
FIREBASE_BASE_URL = f"https://{FIREBASE_HOST}"

# Collection paths in Firebase
FIREBASE_COLLECTIONS = {
    'network_packets': 'network_packets',
    'network_flows': 'network_flows',
    'dns_queries': 'dns_queries',
    'http_transactions': 'http_transactions',
    'processes': 'processes',
    'process_events': 'process_events',
    'file_operations': 'file_operations',
    'file_system': 'file_system',
    'registry_keys': 'registry_keys',
    'hardware': 'hardware',
    'cpu_info': 'cpu_info',
    'memory_info': 'memory_info',
    'disks': 'disks',
    'software': 'software',
    'software_events': 'software_events',
    'performance': 'performance',
    'firewall_rules': 'firewall_rules',
    'firewall_changes': 'firewall_changes',
    'system_events': 'system_events',
    'alerts': 'alerts',
    'usb_devices': 'usb_devices',
    'usb_file_activity': 'usb_file_activity',
    'network_threats': 'network_threats'
}

# ============================================
# CUSTOM CSS FOR DARK CYBER THEME
# ============================================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #0f1235 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 39, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0, 255, 255, 0.2);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(20, 30, 70, 0.8), rgba(15, 20, 50, 0.8));
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 255, 255, 0.3);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s;
        text-align: center;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #00ffff;
        box-shadow: 0 8px 25px rgba(0, 255, 255, 0.2);
    }
    
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        color: #00ffff;
    }
    
    .metric-label {
        font-size: 14px;
        color: #888;
        margin-top: 5px;
    }
    
    /* Threat card */
    .threat-critical {
        background: linear-gradient(135deg, rgba(255, 0, 0, 0.2), rgba(139, 0, 0, 0.2));
        border-left: 4px solid #ff0000;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .threat-high {
        background: linear-gradient(135deg, rgba(255, 69, 0, 0.2), rgba(204, 51, 0, 0.2));
        border-left: 4px solid #ff4500;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .threat-medium {
        background: linear-gradient(135deg, rgba(255, 170, 0, 0.2), rgba(204, 136, 0, 0.2));
        border-left: 4px solid #ffaa00;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .threat-low {
        background: linear-gradient(135deg, rgba(0, 255, 255, 0.1), rgba(0, 136, 136, 0.1));
        border-left: 4px solid #00ffff;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #00ffff !important;
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
    }
    
    /* Dataframe styling */
    .dataframe {
        background: rgba(15, 20, 45, 0.9) !important;
        border-radius: 10px;
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #00ffff, #0088ff);
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
    }
    
    /* Alert badge */
    .alert-badge {
        display: inline-block;
        background: #ff0000;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        text-align: center;
        font-size: 12px;
        line-height: 20px;
        margin-left: 5px;
    }
    
    /* Status indicators */
    .status-online {
        color: #00ff00;
        text-shadow: 0 0 5px #00ff00;
    }
    
    /* Refresh button */
    .refresh-button {
        text-align: right;
        margin-bottom: 10px;
    }
    
    /* Divider */
    hr {
        border-color: rgba(0, 255, 255, 0.3);
        margin: 20px 0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #00ffff;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FIREBASE DATA FETCHING FUNCTIONS
# ============================================

@st.cache_data(ttl=30, show_spinner=False)
def fetch_firebase_collection(collection_name, limit=500):
    """
    Fetch data from Firebase Realtime Database collection
    Returns DataFrame with all records
    """
    try:
        # Build URL for the collection
        url = f"{FIREBASE_BASE_URL}/{collection_name}.json?auth={FIREBASE_AUTH}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            # Parse the nested structure
            records = []
            
            if isinstance(data, dict):
                for device_name, device_data in data.items():
                    if isinstance(device_data, dict):
                        for batch_id, batch_data in device_data.items():
                            if isinstance(batch_data, dict) and 'records' in batch_data:
                                # This is a batch structure
                                for record in batch_data.get('records', []):
                                    if isinstance(record, dict):
                                        record['_device'] = device_name
                                        record['_batch_id'] = batch_id
                                        records.append(record)
                            elif isinstance(batch_data, dict) and 'records' not in batch_data:
                                # This might be an individual record
                                batch_data['_device'] = device_name
                                batch_data['_batch_id'] = batch_id
                                records.append(batch_data)
            
            # Also handle case where data is directly an array
            elif isinstance(data, list):
                records = data
            
            df = pd.DataFrame(records)
            
            # Convert timestamp columns to datetime
            timestamp_cols = ['timestamp', '_uploaded_at', '_stored_at', 'first_seen', 'last_seen', 'created_time']
            for col in timestamp_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Limit records
            if len(df) > limit:
                df = df.head(limit)
            
            return df
        else:
            st.error(f"Failed to fetch {collection_name}: {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error fetching {collection_name}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_all_collections():
    """Fetch data from all collections"""
    data = {}
    
    for name, path in FIREBASE_COLLECTIONS.items():
        df = fetch_firebase_collection(path)
        if not df.empty:
            data[name] = df
    
    return data


def get_collection_stats(df):
    """Get statistics for a collection"""
    if df.empty:
        return {
            'total': 0,
            'unique_devices': 0,
            'date_range': 'No data'
        }
    
    total = len(df)
    unique_devices = df['_device'].nunique() if '_device' in df.columns else 0
    
    date_range = 'No data'
    if 'timestamp' in df.columns:
        min_date = df['timestamp'].min()
        max_date = df['timestamp'].max()
        if pd.notna(min_date) and pd.notna(max_date):
            date_range = f"{min_date.strftime('%Y-%m-%d %H:%M')} to {max_date.strftime('%Y-%m-%d %H:%M')}"
    
    return {
        'total': total,
        'unique_devices': unique_devices,
        'date_range': date_range
    }

# ============================================
# DASHBOARD PAGES
# ============================================

def dashboard_overview(all_data):
    """Main dashboard overview"""
    st.markdown("<h1 style='text-align: center;'>NeuroFence2 Security Dashboard</h1>", unsafe_allow_html=True)
    
    # Calculate total metrics across all collections
    total_records = sum(len(df) for df in all_data.values())
    total_devices = set()
    for df in all_data.values():
        if '_device' in df.columns:
            total_devices.update(df['_device'].unique())
    
    # Alert statistics
    alert_stats = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    if 'alerts' in all_data and not all_data['alerts'].empty:
        alerts_df = all_data['alerts']
        if 'severity' in alerts_df.columns:
            alert_stats = alerts_df['severity'].value_counts().to_dict()
    
    # Threat statistics
    threat_count = 0
    if 'network_threats' in all_data and not all_data['network_threats'].empty:
        threat_count = len(all_data['network_threats'])
    
    # USB events count
    usb_count = 0
    if 'usb_devices' in all_data and not all_data['usb_devices'].empty:
        usb_count = len(all_data['usb_devices'])
    
    # Display metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_records:,}</div>
            <div class="metric-label">Total Records</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(total_devices)}</div>
            <div class="metric-label">Active Devices</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #ff4444;">{alert_stats.get('CRITICAL', 0)}</div>
            <div class="metric-label">Critical Alerts</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #ffaa00;">{threat_count}</div>
            <div class="metric-label">Network Threats</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{usb_count}</div>
            <div class="metric-label">USB Events</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Alert Timeline Chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 Alert Timeline")
        if 'alerts' in all_data and not all_data['alerts'].empty:
            alerts_df = all_data['alerts']
            if 'timestamp' in alerts_df.columns and 'severity' in alerts_df.columns:
                alerts_df['date'] = alerts_df['timestamp'].dt.date
                timeline = alerts_df.groupby(['date', 'severity']).size().unstack(fill_value=0)
                
                fig = go.Figure()
                for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    if severity in timeline.columns:
                        fig.add_trace(go.Scatter(
                            x=timeline.index,
                            y=timeline[severity],
                            name=severity,
                            mode='lines+markers',
                            line=dict(width=2)
                        ))
                
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Date",
                    yaxis_title="Alert Count",
                    legend_title="Severity"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No timestamp or severity data in alerts")
        else:
            st.info("No alert data available")
    
    with col2:
        st.markdown("### 📊 Alert Distribution")
        if 'alerts' in all_data and not all_data['alerts'].empty:
            alerts_df = all_data['alerts']
            if 'severity' in alerts_df.columns:
                severity_counts = alerts_df['severity'].value_counts()
                
                colors = {
                    'CRITICAL': '#ff0000',
                    'HIGH': '#ff4500',
                    'MEDIUM': '#ffaa00',
                    'LOW': '#00ffff'
                }
                
                fig = go.Figure(data=[go.Pie(
                    labels=severity_counts.index,
                    values=severity_counts.values,
                    hole=0.4,
                    marker_colors=[colors.get(s, '#888') for s in severity_counts.index]
                )])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No severity data in alerts")
        else:
            st.info("No alert data available")
    
    # Recent Alerts Section
    st.markdown("### 🔔 Recent Security Alerts")
    if 'alerts' in all_data and not all_data['alerts'].empty:
        alerts_df = all_data['alerts'].sort_values('timestamp', ascending=False).head(20)
        
        for _, alert in alerts_df.iterrows():
            severity = alert.get('severity', 'MEDIUM')
            severity_class = f"threat-{severity.lower()}" if severity.lower() in ['critical', 'high', 'medium', 'low'] else "threat-medium"
            
            timestamp = alert.get('timestamp', '')
            if pd.notna(timestamp):
                timestamp_str = str(timestamp)[:19]
            else:
                timestamp_str = 'Unknown'
            
            alert_type = alert.get('alert_type', 'Unknown Alert')
            description = alert.get('description', 'No description')[:150]
            source = alert.get('source', 'Unknown')
            
            st.markdown(f"""
            <div class="{severity_class}">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>[{severity}]</strong> {alert_type}</span>
                    <span style="font-size: 11px; color: #888;">{timestamp_str}</span>
                </div>
                <div style="font-size: 12px; margin-top: 5px;">{description}</div>
                <div style="font-size: 11px; color: #888; margin-top: 5px;">Source: {source}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No alerts found")
    
    st.markdown("---")
    
    # Collection Summary
    st.markdown("### 📁 Data Collection Summary")
    
    summary_data = []
    for name, df in all_data.items():
        stats = get_collection_stats(df)
        summary_data.append({
            'Collection': name.replace('_', ' ').title(),
            'Records': stats['total'],
            'Devices': stats['unique_devices'],
            'Date Range': stats['date_range']
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)


def alerts_page(all_data):
    """Alerts analysis page"""
    st.markdown("<h1 style='text-align: center;'>Alert Analysis Center</h1>", unsafe_allow_html=True)
    
    if 'alerts' not in all_data or all_data['alerts'].empty:
        st.warning("No alert data available")
        return
    
    alerts_df = all_data['alerts'].copy()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severities = ['All'] + sorted(alerts_df['severity'].unique().tolist()) if 'severity' in alerts_df.columns else ['All']
        severity_filter = st.selectbox("Severity", severities)
    
    with col2:
        sources = ['All'] + sorted(alerts_df['source'].unique().tolist()) if 'source' in alerts_df.columns else ['All']
        source_filter = st.selectbox("Source", sources)
    
    with col3:
        if 'timestamp' in alerts_df.columns:
            min_date = alerts_df['timestamp'].min().date()
            max_date = alerts_df['timestamp'].max().date()
            date_range = st.date_input("Date Range", [min_date, max_date])
    
    # Apply filters
    filtered_df = alerts_df.copy()
    if severity_filter != 'All':
        filtered_df = filtered_df[filtered_df['severity'] == severity_filter]
    if source_filter != 'All':
        filtered_df = filtered_df[filtered_df['source'] == source_filter]
    if 'timestamp' in alerts_df.columns and len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['timestamp'].dt.date >= date_range[0]) &
            (filtered_df['timestamp'].dt.date <= date_range[1])
        ]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alerts", len(filtered_df))
    with col2:
        critical_count = len(filtered_df[filtered_df['severity'] == 'CRITICAL']) if 'severity' in filtered_df.columns else 0
        st.metric("Critical", critical_count, delta_color="off")
    with col3:
        high_count = len(filtered_df[filtered_df['severity'] == 'HIGH']) if 'severity' in filtered_df.columns else 0
        st.metric("High", high_count)
    with col4:
        st.metric("Devices", filtered_df['_device'].nunique() if '_device' in filtered_df.columns else 0)
    
    # Alert by source chart
    if 'source' in filtered_df.columns:
        st.markdown("### 📊 Alerts by Source")
        source_counts = filtered_df['source'].value_counts().head(10)
        fig = go.Figure(data=[go.Bar(x=source_counts.values, y=source_counts.index, orientation='h', marker_color='#00ffff')])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Alert timeline
    if 'timestamp' in filtered_df.columns:
        st.markdown("### 📈 Alert Timeline")
        filtered_df['hour'] = filtered_df['timestamp'].dt.hour
        hourly = filtered_df.groupby('hour').size()
        
        fig = go.Figure(data=[go.Scatter(x=hourly.index, y=hourly.values, mode='lines+markers', line=dict(color='#00ffff', width=2))])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Hour of Day", yaxis_title="Alert Count")
        st.plotly_chart(fig, use_container_width=True)
    
    # Alert details table
    st.markdown("### 📋 Alert Details")
    display_cols = ['timestamp', 'severity', 'alert_type', 'source', 'description']
    available_cols = [col for col in display_cols if col in filtered_df.columns]
    if available_cols:
        st.dataframe(filtered_df[available_cols].head(100), use_container_width=True)
    else:
        st.dataframe(filtered_df.head(100), use_container_width=True)


def network_page(all_data):
    """Network monitoring page"""
    st.markdown("<h1 style='text-align: center;'>Network Monitoring</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 Network Packets")
        if 'network_packets' in all_data and not all_data['network_packets'].empty:
            packets_df = all_data['network_packets']
            st.metric("Total Packets", len(packets_df))
            
            if 'ip_src' in packets_df.columns:
                top_src = packets_df['ip_src'].value_counts().head(10)
                fig = go.Figure(data=[go.Bar(x=top_src.values, y=top_src.index, orientation='h', marker_color='#00ffff')])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Top Source IPs")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No network packet data")
    
    with col2:
        st.markdown("### 🌐 Network Threats")
        if 'network_threats' in all_data and not all_data['network_threats'].empty:
            threats_df = all_data['network_threats']
            st.metric("Total Threats", len(threats_df))
            
            if 'threat_type' in threats_df.columns:
                threat_types = threats_df['threat_type'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=threat_types.index, values=threat_types.values, hole=0.3)])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Threat Types")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No network threat data")
    
    st.markdown("---")
    
    # DNS Queries
    st.markdown("### 🔍 DNS Queries")
    if 'dns_queries' in all_data and not all_data['dns_queries'].empty:
        dns_df = all_data['dns_queries']
        if 'query_name' in dns_df.columns:
            top_domains = dns_df['query_name'].value_counts().head(15)
            fig = go.Figure(data=[go.Bar(x=top_domains.values, y=top_domains.index, orientation='h', marker_color='#ffaa00')])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=500)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No DNS query data")
    
    # HTTP Transactions
    st.markdown("### 🌍 HTTP Transactions")
    if 'http_transactions' in all_data and not all_data['http_transactions'].empty:
        http_df = all_data['http_transactions']
        if 'host' in http_df.columns:
            top_hosts = http_df['host'].value_counts().head(10)
            fig = go.Figure(data=[go.Bar(x=top_hosts.values, y=top_hosts.index, orientation='h', marker_color='#00ff00')])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No HTTP transaction data")


def endpoint_page(all_data):
    """Endpoint security page"""
    st.markdown("<h1 style='text-align: center;'>Endpoint Security</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Processes")
        if 'processes' in all_data and not all_data['processes'].empty:
            processes_df = all_data['processes']
            st.metric("Total Process Records", len(processes_df))
            
            if 'name' in processes_df.columns:
                top_processes = processes_df['name'].value_counts().head(10)
                fig = go.Figure(data=[go.Bar(x=top_processes.values, y=top_processes.index, orientation='h', marker_color='#00ffff')])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Top Processes")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No process data")
    
    with col2:
        st.markdown("### 🔄 Process Events")
        if 'process_events' in all_data and not all_data['process_events'].empty:
            events_df = all_data['process_events']
            if 'event_type' in events_df.columns:
                event_types = events_df['event_type'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=event_types.index, values=event_types.values, hole=0.3)])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Process Events")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No process event data")
    
    st.markdown("---")
    
    # File Operations
    st.markdown("### 📁 File Operations")
    if 'file_operations' in all_data and not all_data['file_operations'].empty:
        files_df = all_data['file_operations']
        if 'operation' in files_df.columns:
            operations = files_df['operation'].value_counts()
            fig = go.Figure(data=[go.Bar(x=operations.index, y=operations.values, marker_color='#ffaa00')])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="File Operations")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show recent file operations
            st.markdown("#### Recent File Operations")
            display_cols = ['timestamp', 'operation', 'file_path', 'file_size']
            available_cols = [col for col in display_cols if col in files_df.columns]
            if available_cols:
                st.dataframe(files_df[available_cols].head(50), use_container_width=True)
    else:
        st.info("No file operation data")
    
    # Registry Changes
    st.markdown("### 📝 Registry Changes")
    if 'registry_keys' in all_data and not all_data['registry_keys'].empty:
        registry_df = all_data['registry_keys']
        if 'operation' in registry_df.columns:
            reg_ops = registry_df['operation'].value_counts()
            fig = go.Figure(data=[go.Bar(x=reg_ops.index, y=reg_ops.values, marker_color='#00ff00')])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Registry Operations")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No registry data")


def usb_page(all_data):
    """USB monitoring page"""
    st.markdown("<h1 style='text-align: center;'>USB Device Monitoring</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 USB Devices")
        if 'usb_devices' in all_data and not all_data['usb_devices'].empty:
            usb_df = all_data['usb_devices']
            st.metric("Total USB Events", len(usb_df))
            
            if 'event_type' in usb_df.columns:
                events = usb_df['event_type'].value_counts()
                fig = go.Figure(data=[go.Pie(labels=events.index, values=events.values, hole=0.3)])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="USB Events")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No USB device data")
    
    with col2:
        st.markdown("### 📄 USB File Activity")
        if 'usb_file_activity' in all_data and not all_data['usb_file_activity'].empty:
            file_df = all_data['usb_file_activity']
            st.metric("Total File Activities", len(file_df))
            
            if 'risk_level' in file_df.columns:
                risk_levels = file_df['risk_level'].value_counts()
                colors = {'HIGH': '#ff0000', 'MEDIUM': '#ffaa00', 'LOW': '#00ff00'}
                fig = go.Figure(data=[go.Bar(x=risk_levels.index, y=risk_levels.values, marker_color=[colors.get(r, '#888') for r in risk_levels.index])])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Risk Levels")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No USB file activity data")
    
    st.markdown("---")
    
    # USB File Activity Details
    if 'usb_file_activity' in all_data and not all_data['usb_file_activity'].empty:
        st.markdown("### 🔍 USB File Activity Details")
        file_df = all_data['usb_file_activity']
        
        # Filter by risk level
        risk_filter = st.selectbox("Filter by Risk Level", ['All', 'HIGH', 'MEDIUM', 'LOW'])
        if risk_filter != 'All':
            file_df = file_df[file_df['risk_level'] == risk_filter]
        
        display_cols = ['timestamp', 'operation', 'file_path', 'risk_level', 'file_size']
        available_cols = [col for col in display_cols if col in file_df.columns]
        if available_cols:
            st.dataframe(file_df[available_cols].head(100), use_container_width=True)
    
    # USB Devices Table
    if 'usb_devices' in all_data and not all_data['usb_devices'].empty:
        st.markdown("### 📋 USB Device History")
        usb_df = all_data['usb_devices']
        display_cols = ['timestamp', 'event_type', 'drive_letter', 'volume_label', 'capacity_gb']
        available_cols = [col for col in display_cols if col in usb_df.columns]
        if available_cols:
            st.dataframe(usb_df[available_cols].head(100), use_container_width=True)


def hardware_page(all_data):
    """Hardware and software inventory page"""
    st.markdown("<h1 style='text-align: center;'>Hardware & Software Inventory</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🖥️ Hardware Information")
        if 'hardware' in all_data and not all_data['hardware'].empty:
            hardware_df = all_data['hardware']
            st.metric("Total Hardware Records", len(hardware_df))
            
            if 'component_type' in hardware_df.columns:
                components = hardware_df['component_type'].value_counts()
                fig = go.Figure(data=[go.Bar(x=components.values, y=components.index, orientation='h', marker_color='#00ffff')])
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hardware data")
        
        st.markdown("### 💾 CPU Information")
        if 'cpu_info' in all_data and not all_data['cpu_info'].empty:
            cpu_df = all_data['cpu_info']
            if 'name' in cpu_df.columns:
                st.write(f"**CPU:** {cpu_df.iloc[0].get('name', 'Unknown')}")
            if 'cores' in cpu_df.columns:
                st.write(f"**Cores:** {cpu_df.iloc[0].get('cores', 'Unknown')}")
            if 'usage_percent' in cpu_df.columns:
                st.write(f"**Current Usage:** {cpu_df.iloc[0].get('usage_percent', 0)}%")
        else:
            st.info("No CPU data")
    
    with col2:
        st.markdown("### 💾 Memory Information")
        if 'memory_info' in all_data and not all_data['memory_info'].empty:
            mem_df = all_data['memory_info']
            if 'total' in mem_df.columns:
                st.write(f"**Total Memory:** {mem_df.iloc[0].get('total', 0)} GB")
            if 'used' in mem_df.columns:
                st.write(f"**Used Memory:** {mem_df.iloc[0].get('used', 0)} GB")
            if 'percent' in mem_df.columns:
                st.write(f"**Usage Percentage:** {mem_df.iloc[0].get('percent', 0)}%")
        else:
            st.info("No memory data")
        
        st.markdown("### 💽 Disk Information")
        if 'disks' in all_data and not all_data['disks'].empty:
            disks_df = all_data['disks']
            for _, disk in disks_df.iterrows():
                st.write(f"**{disk.get('device', 'Unknown')}:** {disk.get('total', 0)} GB total, {disk.get('used', 0)} GB used")
        else:
            st.info("No disk data")
    
    st.markdown("---")
    
    # Software Inventory
    st.markdown("### 📦 Software Inventory")
    if 'software' in all_data and not all_data['software'].empty:
        software_df = all_data['software']
        st.metric("Total Software Records", len(software_df))
        
        if 'name' in software_df.columns:
            top_software = software_df['name'].value_counts().head(20)
            fig = go.Figure(data=[go.Bar(x=top_software.values, y=top_software.index, orientation='h', marker_color='#ffaa00')])
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        # Software events
        if 'software_events' in all_data and not all_data['software_events'].empty:
            st.markdown("### 📋 Software Events")
            events_df = all_data['software_events']
            display_cols = ['timestamp', 'event_type', 'name', 'version']
            available_cols = [col for col in display_cols if col in events_df.columns]
            if available_cols:
                st.dataframe(events_df[available_cols].head(50), use_container_width=True)
    else:
        st.info("No software data")


def performance_page(all_data):
    """Performance monitoring page"""
    st.markdown("<h1 style='text-align: center;'>Performance Monitoring</h1>", unsafe_allow_html=True)
    
    if 'performance' in all_data and not all_data['performance'].empty:
        perf_df = all_data['performance'].sort_values('timestamp')
        
        # Performance metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'cpu_percent' in perf_df.columns:
                avg_cpu = perf_df['cpu_percent'].mean()
                st.metric("Avg CPU Usage", f"{avg_cpu:.1f}%")
        with col2:
            if 'memory_percent' in perf_df.columns:
                avg_mem = perf_df['memory_percent'].mean()
                st.metric("Avg Memory Usage", f"{avg_mem:.1f}%")
        with col3:
            if 'processes_count' in perf_df.columns:
                avg_procs = perf_df['processes_count'].mean()
                st.metric("Avg Processes", f"{avg_procs:.0f}")
        
        st.markdown("---")
        
        # CPU Usage Chart
        if 'cpu_percent' in perf_df.columns and 'timestamp' in perf_df.columns:
            st.markdown("### 📈 CPU Usage Over Time")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['cpu_percent'], mode='lines', name='CPU %', line=dict(color='#00ffff', width=2)))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Time", yaxis_title="CPU %")
            st.plotly_chart(fig, use_container_width=True)
        
        # Memory Usage Chart
        if 'memory_percent' in perf_df.columns:
            st.markdown("### 📈 Memory Usage Over Time")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['memory_percent'], mode='lines', name='Memory %', line=dict(color='#ffaa00', width=2)))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Time", yaxis_title="Memory %")
            st.plotly_chart(fig, use_container_width=True)
        
        # Disk I/O Chart
        if 'disk_io_read' in perf_df.columns and 'disk_io_write' in perf_df.columns:
            st.markdown("### 📈 Disk I/O Activity")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['disk_io_read'], mode='lines', name='Read MB/s', line=dict(color='#00ff00', width=2)))
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['disk_io_write'], mode='lines', name='Write MB/s', line=dict(color='#ff0000', width=2)))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Time", yaxis_title="MB/s")
            st.plotly_chart(fig, use_container_width=True)
        
        # Network I/O Chart
        if 'net_io_sent' in perf_df.columns and 'net_io_recv' in perf_df.columns:
            st.markdown("### 📈 Network I/O Activity")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['net_io_sent'], mode='lines', name='Sent MB/s', line=dict(color='#00ffff', width=2)))
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['net_io_recv'], mode='lines', name='Received MB/s', line=dict(color='#ffaa00', width=2)))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Time", yaxis_title="MB/s")
            st.plotly_chart(fig, use_container_width=True)
        
        # Process Count
        if 'processes_count' in perf_df.columns:
            st.markdown("### 📈 Process Count Over Time")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['processes_count'], mode='lines', name='Processes', line=dict(color='#ff00ff', width=2)))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Time", yaxis_title="Process Count")
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent performance data
        st.markdown("### 📋 Recent Performance Data")
        display_cols = ['timestamp', 'cpu_percent', 'memory_percent', 'processes_count']
        available_cols = [col for col in display_cols if col in perf_df.columns]
        if available_cols:
            st.dataframe(perf_df[available_cols].tail(50), use_container_width=True)
    else:
        st.info("No performance data available")


def devices_page(all_data):
    """Devices/Aggregators page"""
    st.markdown("<h1 style='text-align: center;'>Connected Devices</h1>", unsafe_allow_html=True)
    
    # Collect all unique devices
    all_devices = set()
    device_stats = defaultdict(lambda: {'collections': set(), 'total_records': 0})
    
    for collection_name, df in all_data.items():
        if '_device' in df.columns:
            for device in df['_device'].unique():
                all_devices.add(device)
                device_stats[device]['collections'].add(collection_name)
                device_stats[device]['total_records'] += len(df[df['_device'] == device])
    
    if not all_devices:
        st.info("No device data found")
        return
    
    st.markdown(f"### 🖥️ Active Devices ({len(all_devices)})")
    
    # Display device cards
    for device in sorted(all_devices):
        stats = device_stats[device]
        
        st.markdown(f"""
        <div class="agent-card" style="background: rgba(20, 30, 70, 0.8); border-radius: 15px; padding: 15px; margin: 10px 0; border: 1px solid rgba(0, 255, 255, 0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong style="color: #00ffff; font-size: 16px;">🖥️ {device}</strong><br>
                    <span style="font-size: 12px; color: #888;">Collections: {', '.join(list(stats['collections'])[:5])}{'...' if len(stats['collections']) > 5 else ''}</span><br>
                    <span style="font-size: 12px; color: #888;">Total Records: {stats['total_records']:,}</span>
                </div>
                <div style="text-align: right;">
                    <div class="status-online">● ONLINE</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Device activity by collection
    st.markdown("---")
    st.markdown("### 📊 Data Distribution by Device")
    
    device_data = []
    for device in all_devices:
        device_data.append({
            'Device': device,
            'Records': device_stats[device]['total_records'],
            'Collections': len(device_stats[device]['collections'])
        })
    
    device_df = pd.DataFrame(device_data).sort_values('Records', ascending=False)
    
    fig = go.Figure(data=[go.Bar(x=device_df['Records'].head(15), y=device_df['Device'].head(15), orientation='h', marker_color='#00ffff')])
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=500, title="Top Devices by Record Count")
    st.plotly_chart(fig, use_container_width=True)


def raw_data_page(all_data):
    """Raw data viewer page"""
    st.markdown("<h1 style='text-align: center;'>Raw Data Viewer</h1>", unsafe_allow_html=True)
    
    # Collection selector
    collections = list(all_data.keys())
    selected_collection = st.selectbox("Select Collection", collections)
    
    if selected_collection and selected_collection in all_data:
        df = all_data[selected_collection]
        
        if df.empty:
            st.warning(f"No data in {selected_collection}")
            return
        
        st.markdown(f"### {selected_collection.replace('_', ' ').title()}")
        st.metric("Total Records", len(df))
        
        # Preview data
        st.markdown("#### Data Preview")
        st.dataframe(df.head(100), use_container_width=True)
        
        # Column info
        st.markdown("#### Column Information")
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Type': df.dtypes.astype(str),
            'Non-Null': df.count().values,
            'Null %': (df.isnull().sum() / len(df) * 100).round(2).values
        })
        st.dataframe(col_info, use_container_width=True)
        
        # Download button
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"{selected_collection}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


# ============================================
# SIDEBAR NAVIGATION
# ============================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 48px;">🛡️</div>
            <h2 style="color: #00ffff;">NeuroFence2</h2>
            <p style="color: #888;">Security Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection status
        st.markdown("""
        <div style="background: rgba(0, 255, 255, 0.1); border-radius: 10px; padding: 10px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between;">
                <span>🔥 Firebase Status</span>
                <span class="status-online">● CONNECTED</span>
            </div>
            <div style="font-size: 10px; color: #888; margin-top: 5px;">neurofence2-default-rtdb</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu
        selected = st.selectbox(
            "Navigation",
            [
                "📊 Dashboard",
                "🚨 Alerts",
                "🌐 Network",
                "🖥️ Endpoint",
                "💾 USB",
                "🔧 Hardware",
                "📈 Performance",
                "📱 Devices",
                "📄 Raw Data"
            ]
        )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown(f"<p style='text-align: center; color: #888; font-size: 11px;'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
        
        return selected


# ============================================
# MAIN APP
# ============================================
def main():
    # Show loading spinner while fetching data
    with st.spinner("🔄 Fetching data from Firebase..."):
        all_data = fetch_all_collections()
    
    # Sidebar navigation
    selected_page = render_sidebar()
    
    # Display selected page
    if selected_page == "📊 Dashboard":
        dashboard_overview(all_data)
    elif selected_page == "🚨 Alerts":
        alerts_page(all_data)
    elif selected_page == "🌐 Network":
        network_page(all_data)
    elif selected_page == "🖥️ Endpoint":
        endpoint_page(all_data)
    elif selected_page == "💾 USB":
        usb_page(all_data)
    elif selected_page == "🔧 Hardware":
        hardware_page(all_data)
    elif selected_page == "📈 Performance":
        performance_page(all_data)
    elif selected_page == "📱 Devices":
        devices_page(all_data)
    elif selected_page == "📄 Raw Data":
        raw_data_page(all_data)

if __name__ == "__main__":
    main()
