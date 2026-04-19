#!/usr/bin/env python3
"""
NEUROFENCE2 ENTERPRISE PLATFORM - Streamlit Cloud Edition
Fixed Firebase data fetching for agent's nested structure
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import json
import os
import hashlib
import requests
import re
import numpy as np
import base64
from streamlit_option_menu import option_menu
import threading
import queue
import asyncio
import warnings
from collections import defaultdict, Counter
warnings.filterwarnings('ignore')

# ============================================
# AI/ML IMPORTS
# ============================================
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib

# ============================================
# OPENROUTER API CONFIGURATION
# ============================================
OPENROUTER_API_KEY = "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"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-3.5-turbo"

# ============================================
# FIREBASE CONFIGURATION
# ============================================
FIREBASE_HOST = "neurofence2-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_AUTH = "AIzaSyCbT1wnRE9OO_yv2LjqSIyK1InddRgDFsY"
FIREBASE_BASE_URL = f"https://{FIREBASE_HOST}"

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
# CONFIGURATION
# ============================================
SCAN_THRESHOLD = 20
FLOOD_THRESHOLD = 50
HIGH_ENTROPY_THRESHOLD = 4.0
MODEL_FILE = 'network_anomaly_model.joblib'
SCALER_FILE = 'network_scaler.joblib'

# ============================================
# AUTHENTICATION CONFIG
# ============================================
USERS = {
    "admin": "admin123",
    "analyst": "analyst123",
    "viewer": "viewer123"
}

# ============================================
# Threat Intelligence Sources
# ============================================
THREAT_INTEL_SOURCES = {
    "AbuseIPDB": "https://www.abuseipdb.com/check/",
    "VirusTotal": "https://www.virustotal.com/gui/ip-address/",
    "GreyNoise": "https://viz.greynoise.io/ip/",
    "Shodan": "https://www.shodan.io/host/",
    "Talos": "https://talosintelligence.com/reputation_center/lookup?search="
}

HASH_INTEL_SOURCES = {
    "VirusTotal": "https://www.virustotal.com/gui/file/",
    "HybridAnalysis": "https://www.hybrid-analysis.com/search?query=",
    "JoeSandbox": "https://www.joesandbox.com/search?q=",
    "ANY.RUN": "https://app.any.run/submissions/#filehash:",
    "MalwareBazaar": "https://bazaar.abuse.ch/browse.php?search=sha256%3A"
}

# MITRE ATT&CK Database
MITRE_ATTACK_DB = {
    "T1046": {"name": "Network Service Scanning", "tactic": "Discovery", 
              "description": "Adversaries may attempt to get a listing of services running on remote hosts.",
              "detection": "Monitor for network traffic containing reconnaissance signatures.",
              "mitigation": "Use network intrusion detection/prevention systems."},
    "T1498": {"name": "Network Denial of Service", "tactic": "Impact",
              "description": "Adversaries may perform Network DoS attacks to degrade resource availability.",
              "detection": "Monitor for abnormal network traffic patterns.",
              "mitigation": "Implement rate limiting, use DoS protection services."},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "Exfiltration",
              "description": "Adversaries may steal data by exfiltrating it over a different protocol.",
              "detection": "Monitor for large data transfers over unusual ports.",
              "mitigation": "Monitor and restrict large outbound data transfers."},
    "T1568": {"name": "DNS Calculation", "tactic": "Command and Control",
              "description": "Adversaries may use DNS for command and control using DGAs.",
              "detection": "Monitor DNS queries for high-entropy domain names.",
              "mitigation": "Use DNS sinkholing, implement threat intelligence feeds."},
    "T1204": {"name": "User Execution", "tactic": "Execution",
              "description": "Adversary may rely upon a user to execute a malicious file.",
              "detection": "Monitor file system events for execution of suspicious files.",
              "mitigation": "Implement application whitelisting, user training."},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access",
              "description": "Adversaries may exploit weaknesses in public-facing applications.",
              "detection": "Monitor web server logs for suspicious patterns.",
              "mitigation": "Keep applications patched, use WAFs."},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution",
              "description": "Adversaries may abuse command and script interpreters.",
              "detection": "Monitor process creation for unusual command-line arguments.",
              "mitigation": "Restrict execution of scripts and command-line tools."},
    "T1547": {"name": "Registry Run Keys / Startup Folder", "tactic": "Persistence",
              "description": "Adversaries may achieve persistence by adding to startup folders.",
              "detection": "Monitor registry changes and file system events.",
              "mitigation": "Restrict write access to startup folders and registry keys."}
}

# CVE Database
SOFTWARE_CVES = {
    'chrome': [{'id': 'CVE-2024-1234', 'severity': 'HIGH', 'fixed_version': '120.0.6099.109'}],
    'firefox': [{'id': 'CVE-2024-5678', 'severity': 'MEDIUM', 'fixed_version': '121.0'}],
    'python': [{'id': 'CVE-2023-12345', 'severity': 'CRITICAL', 'fixed_version': '3.11.6'}],
    'java': [{'id': 'CVE-2024-123', 'severity': 'HIGH', 'fixed_version': '11.0.21'}],
    'nginx': [{'id': 'CVE-2023-1234', 'severity': 'MEDIUM', 'fixed_version': '1.24.0'}],
    'mysql': [{'id': 'CVE-2024-12345', 'severity': 'CRITICAL', 'fixed_version': '8.0.35'}],
}

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="NEUROFENCE2 ENTERPRISE PLATFORM",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CUSTOM CSS - Dark Professional Theme
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0a0f1e 0%, #1a1f2e 100%);
        background-attachment: fixed;
        color: #e0e0e0;
    }
    
    .stMarkdown, .stText, .stMetric {
        color: #e0e0e0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #fff !important;
        font-weight: 600 !important;
    }
    
    .glass-container-dark {
        background: rgba(26, 31, 46, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(102, 126, 234, 0.2);
        margin-bottom: 1.5rem;
    }
    
    .login-container-dark {
        max-width: 400px;
        margin: 50px auto;
        background: rgba(26, 31, 46, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .metric-card-dark {
        background: linear-gradient(135deg, #1e2436 0%, #2a2f42 100%);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    
    .metric-card-dark:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(102, 126, 234, 0.3);
    }
    
    .metric-critical { border-left-color: #ff4444; }
    .metric-high { border-left-color: #ff8e53; }
    .metric-medium { border-left-color: #ffd700; }
    .metric-low { border-left-color: #00c851; }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #fff;
        font-family: 'Fira Code', monospace;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #b0b0b0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .alert-card-dark {
        background: linear-gradient(135deg, #1e2436 0%, #2a2f42 100%);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-left: 5px solid;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .alert-card-dark:hover {
        transform: translateX(5px);
    }
    
    .alert-critical { border-left-color: #ff4444; }
    .alert-high { border-left-color: #ff8e53; }
    
    .alert-time {
        font-size: 0.8rem;
        color: #888;
        font-family: 'Fira Code', monospace;
    }
    
    .alert-title {
        font-size: 1rem;
        font-weight: 600;
        color: #fff;
    }
    
    .threat-card-dark {
        background: linear-gradient(135deg, #1e2436 0%, #2a2f42 100%);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .threat-card-dark:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }
    
    .threat-mitre {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-family: 'Fira Code', monospace;
    }
    
    .chat-container {
        background: rgba(26, 31, 46, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .chat-messages {
        background: rgba(20, 25, 40, 0.8);
        border-radius: 10px;
        padding: 1rem;
        height: 400px;
        overflow-y: auto;
        margin-bottom: 1rem;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 20px 20px 5px 20px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-left: auto;
        word-wrap: break-word;
    }
    
    .assistant-message {
        background: rgba(42, 47, 66, 0.95);
        color: #e0e0e0;
        padding: 0.8rem 1.2rem;
        border-radius: 20px 20px 20px 5px;
        margin: 0.5rem 0;
        max-width: 80%;
        margin-right: auto;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .system-message {
        background: rgba(255, 68, 68, 0.1);
        color: #ff4444;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 0.5rem auto;
        text-align: center;
        max-width: 90%;
    }
    
    .quick-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 1rem;
    }
    
    .quick-action-chip {
        background: rgba(42, 47, 66, 0.8);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .quick-action-chip:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        font-family: 'Fira Code', monospace;
    }
    
    .status-critical { background: linear-gradient(135deg, #ff4444, #cc0000); color: white; }
    .status-high { background: linear-gradient(135deg, #ff8e53, #ff6b6b); color: white; }
    .status-medium { background: linear-gradient(135deg, #ffd700, #ffaa00); color: #1a1f2e; }
    .status-low { background: linear-gradient(135deg, #00c851, #007e33); color: white; }
    
    .dataframe {
        font-family: 'Fira Code', monospace !important;
        background: #1a1f2e !important;
        color: #e0e0e0 !important;
        border-radius: 10px !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: rgba(26, 31, 46, 0.8);
        border-radius: 10px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #b0b0b0;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Device card */
    .device-card {
        background: linear-gradient(135deg, #1e2436 0%, #2a2f42 100%);
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(102, 126, 234, 0.2);
        transition: all 0.3s ease;
    }
    
    .device-card:hover {
        transform: translateX(5px);
        border-color: #667eea;
    }
    
    .device-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #667eea;
    }
    
    .device-stats {
        font-size: 0.8rem;
        color: #888;
        margin-top: 0.3rem;
    }
    
    .status-online {
        color: #00ff00;
        font-weight: 600;
    }
    
    .status-offline {
        color: #ff4444;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FIREBASE DATA FETCHING FUNCTIONS (FIXED)
# ============================================

@st.cache_data(ttl=30, show_spinner=False)
def fetch_firebase_collection(collection_name, limit=5000):
    """
    Fetch data from Firebase Realtime Database collection
    Handles the nested structure: device -> batch_id -> {records: [...]}
    """
    try:
        url = f"{FIREBASE_BASE_URL}/{collection_name}.json?auth={FIREBASE_AUTH}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if not data:
                return pd.DataFrame()
            
            records = []
            
            # Handle nested structure: device_name -> batch_id -> records
            if isinstance(data, dict):
                for device_name, device_data in data.items():
                    if isinstance(device_data, dict):
                        for batch_id, batch_content in device_data.items():
                            # Check if this batch has 'records' key (batch format)
                            if isinstance(batch_content, dict) and 'records' in batch_content:
                                batch_records = batch_content.get('records', [])
                                if isinstance(batch_records, list):
                                    for record in batch_records:
                                        if isinstance(record, dict):
                                            record['_device'] = device_name
                                            record['_batch_id'] = batch_id
                                            # Add batch metadata if available
                                            if 'uploaded_at' in batch_content:
                                                record['_batch_uploaded_at'] = batch_content['uploaded_at']
                                            records.append(record)
                            # Handle case where batch_content is directly a record (no 'records' key)
                            elif isinstance(batch_content, dict) and 'records' not in batch_content:
                                # Check if it has typical record fields
                                if any(key in batch_content for key in ['timestamp', 'alert_type', 'ip_src', 'process_name']):
                                    batch_content['_device'] = device_name
                                    batch_content['_batch_id'] = batch_id
                                    records.append(batch_content)
                            # Handle case where batch_content is a list
                            elif isinstance(batch_content, list):
                                for idx, record in enumerate(batch_content):
                                    if isinstance(record, dict):
                                        record['_device'] = device_name
                                        record['_batch_index'] = idx
                                        records.append(record)
            
            df = pd.DataFrame(records)
            
            if df.empty:
                return df
            
            # Convert timestamp columns to datetime
            timestamp_cols = ['timestamp', '_uploaded_at', '_stored_at', '_batch_uploaded_at', 
                            'first_seen', 'last_seen', 'created_time', 'created', 'modified', 'accessed']
            for col in timestamp_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Limit records
            if len(df) > limit:
                df = df.head(limit)
            
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_all_collections():
    """Fetch data from all collections"""
    data = {}
    status_messages = []
    
    for name, path in FIREBASE_COLLECTIONS.items():
        df = fetch_firebase_collection(path)
        if not df.empty:
            data[name] = df
            status_messages.append(f"✅ {name}: {len(df)} records")
        else:
            status_messages.append(f"⚠️ {name}: No data")
    
    # Show status in expander
    with st.expander("📊 Data Fetch Status", expanded=False):
        for msg in status_messages:
            st.text(msg)
    
    return data


class FirebaseDataManager:
    """Data manager for Firebase collections with caching"""
    
    def __init__(self):
        self.cache = {}
        self.last_fetch = {}
    
    def get_collection(self, name, minutes=1440, limit=5000):
        """Get collection data with time filtering"""
        df = fetch_firebase_collection(FIREBASE_COLLECTIONS.get(name, name), limit)
        
        if df.empty:
            return df
        
        if 'timestamp' in df.columns:
            time_limit = datetime.now() - timedelta(minutes=minutes)
            df = df[df['timestamp'] >= time_limit]
        
        return df
    
    def get_recent_alerts(self, limit=500):
        df = self.get_collection('alerts', minutes=1440, limit=limit)
        if not df.empty and 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)
        return df
    
    def get_network_packets(self, minutes=60, limit=10000):
        return self.get_collection('network_packets', minutes, limit)
    
    def get_dns_queries(self, minutes=60, limit=5000):
        return self.get_collection('dns_queries', minutes, limit)
    
    def get_http_transactions(self, minutes=60, limit=5000):
        return self.get_collection('http_transactions', minutes, limit)
    
    def get_file_operations(self, minutes=60, limit=5000):
        return self.get_collection('file_operations', minutes, limit)
    
    def get_processes(self, limit=1000):
        return self.get_collection('processes', minutes=1440, limit=limit)
    
    def get_process_events(self, limit=500):
        return self.get_collection('process_events', minutes=1440, limit=limit)
    
    def get_registry_keys(self, limit=500):
        return self.get_collection('registry_keys', minutes=1440, limit=limit)
    
    def get_software(self, limit=1000):
        return self.get_collection('software', minutes=1440, limit=limit)
    
    def get_performance_metrics(self, minutes=60):
        return self.get_collection('performance', minutes, limit=5000)
    
    def get_usb_devices(self, minutes=1440, limit=500):
        return self.get_collection('usb_devices', minutes, limit)
    
    def get_usb_file_activity(self, minutes=1440, limit=2000):
        return self.get_collection('usb_file_activity', minutes, limit)
    
    def get_network_threats(self, minutes=1440, limit=1000):
        return self.get_collection('network_threats', minutes, limit)
    
    def get_network_flows(self, minutes=60, limit=1000):
        return self.get_collection('network_flows', minutes, limit)
    
    def get_firewall_rules(self, limit=500):
        return self.get_collection('firewall_rules', minutes=1440, limit=limit)
    
    def get_all_ips(self, minutes=1440):
        df = self.get_network_packets(minutes=minutes, limit=10000)
        if df.empty:
            return []
        ips = set()
        if 'ip_src' in df.columns:
            ips.update(df['ip_src'].dropna().unique())
        if 'ip_dst' in df.columns:
            ips.update(df['ip_dst'].dropna().unique())
        return [ip for ip in ips if ip and ip != '']
    
    def get_all_file_hashes(self, limit=100):
        # Check multiple sources for file hashes
        hashes = set()
        
        # From file_operations
        df_files = self.get_file_operations(minutes=1440, limit=2000)
        if not df_files.empty and 'file_hash' in df_files.columns:
            hashes.update(df_files['file_hash'].dropna().unique())
        
        # From usb_file_activity
        df_usb = self.get_usb_file_activity(minutes=1440, limit=2000)
        if not df_usb.empty and 'file_hash' in df_usb.columns:
            hashes.update(df_usb['file_hash'].dropna().unique())
        
        # From file_system
        df_fs = self.get_collection('file_system', minutes=1440, limit=2000)
        if not df_fs.empty and 'hash_sha256' in df_fs.columns:
            hashes.update(df_fs['hash_sha256'].dropna().unique())
        
        return list(hashes)[:limit]
    
    def get_top_talkers(self, limit=10, minutes=60):
        df = self.get_network_packets(minutes=minutes, limit=10000)
        if df.empty or 'ip_src' not in df.columns:
            return pd.DataFrame()
        
        result = df.groupby('ip_src').size().reset_index(name='packet_count')
        result = result.nlargest(limit, 'packet_count')
        
        if 'frame_len' in df.columns:
            bytes_sum = df.groupby('ip_src')['frame_len'].sum().reset_index(name='total_bytes')
            result = result.merge(bytes_sum, on='ip_src', how='left')
        
        return result
    
    def get_devices(self):
        """Get list of all devices that have sent data"""
        devices = set()
        for name, path in FIREBASE_COLLECTIONS.items():
            try:
                url = f"{FIREBASE_BASE_URL}/{path}.json?auth={FIREBASE_AUTH}&shallow=true"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        devices.update(data.keys())
            except:
                pass
        return sorted(devices)

# ============================================
# THREAT DETECTION FUNCTIONS
# ============================================

def detect_port_scans(network_df):
    if network_df.empty or 'ip_src' not in network_df.columns:
        return pd.DataFrame()
    
    port_col = None
    for col in ['dst_port', 'tcp_dstport', 'udp_dstport']:
        if col in network_df.columns:
            port_col = col
            break
    
    if not port_col:
        return pd.DataFrame()
    
    scans = network_df.groupby('ip_src').agg({
        port_col: 'nunique',
        'timestamp': ['min', 'max']
    }).reset_index()
    
    scans.columns = ['src_ip', 'ports_scanned', 'first_seen', 'last_seen']
    scans['first_seen'] = pd.to_datetime(scans['first_seen'])
    scans['last_seen'] = pd.to_datetime(scans['last_seen'])
    scans['duration'] = (scans['last_seen'] - scans['first_seen']).dt.total_seconds()
    scans['is_scan'] = scans['ports_scanned'] >= SCAN_THRESHOLD
    
    return scans[scans['is_scan']]


def detect_dns_threats(dns_df):
    if dns_df.empty:
        return pd.DataFrame()
    
    threats = []
    
    if 'entropy' in dns_df.columns:
        high_entropy = dns_df[dns_df['entropy'] > HIGH_ENTROPY_THRESHOLD]
        for _, row in high_entropy.iterrows():
            threats.append({
                'timestamp': row.get('timestamp'),
                'indicator': row.get('query_name', 'Unknown'),
                'type': 'DNS DGA',
                'severity': 'MEDIUM',
                'src_ip': row.get('client_ip', 'Unknown'),
                'mitre_technique': 'T1568'
            })
    
    suspicious_tlds = ['.xyz', '.top', '.club', '.work', '.download', '.bid']
    for _, row in dns_df.iterrows():
        query = str(row.get('query_name', '')).lower()
        for tld in suspicious_tlds:
            if query.endswith(tld):
                threats.append({
                    'timestamp': row.get('timestamp'),
                    'indicator': query,
                    'type': 'Suspicious TLD',
                    'severity': 'LOW',
                    'src_ip': row.get('client_ip', 'Unknown'),
                    'mitre_technique': 'T1568'
                })
                break
    
    return pd.DataFrame(threats)


def detect_http_attacks(http_df):
    if http_df.empty:
        return pd.DataFrame()
    
    attacks = []
    patterns = [
        (r'(cmd|exec|system|passthru|shell|eval)', 'Command Injection', 'T1059'),
        (r'(union.*select|select.*from|insert.*into)', 'SQL Injection', 'T1190'),
        (r'(<script|javascript:|onerror=|onload=)', 'XSS', 'T1189'),
        (r'(\.\./|\.\.\\)', 'Path Traversal', 'T1005')
    ]
    
    uri_col = 'uri' if 'uri' in http_df.columns else 'request_uri' if 'request_uri' in http_df.columns else None
    
    if uri_col:
        for pattern, attack_type, technique in patterns:
            matches = http_df[http_df[uri_col].str.contains(pattern, case=False, na=False)]
            for _, row in matches.iterrows():
                attacks.append({
                    'timestamp': row.get('timestamp'),
                    'indicator': f"{row.get('host', '')}{row.get(uri_col, '')[:50]}",
                    'type': f'HTTP {attack_type}',
                    'severity': 'HIGH',
                    'src_ip': row.get('client_ip', 'Unknown'),
                    'mitre_technique': technique
                })
    
    return pd.DataFrame(attacks)


def detect_suspicious_files(files_df):
    if files_df.empty:
        return pd.DataFrame()
    
    suspicious = []
    patterns = [
        (r'.*\.(exe|dll|bat|ps1|vbs|js|jar)$', 'Executable', 'HIGH'),
        (r'.*\.(pem|key|ppk)$', 'SSH Key', 'HIGH'),
        (r'.*password.*\.txt$', 'Password File', 'CRITICAL')
    ]
    
    for _, row in files_df.iterrows():
        file_path = str(row.get('file_path', ''))
        for pattern, file_type, severity in patterns:
            if re.match(pattern, file_path, re.IGNORECASE):
                suspicious.append({
                    'timestamp': row.get('timestamp'),
                    'indicator': os.path.basename(file_path),
                    'type': f'File - {file_type}',
                    'severity': severity,
                    'file_path': file_path,
                    'process': row.get('process_name', 'Unknown'),
                    'mitre_technique': 'T1204'
                })
                break
    
    return pd.DataFrame(suspicious)


def detect_process_threats(processes_df):
    if processes_df.empty:
        return pd.DataFrame()
    
    threats = []
    suspicious_names = ['mimikatz', 'procdump', 'nc.exe', 'ncat', 'hashcat', 'john']
    
    for name in suspicious_names:
        matches = processes_df[processes_df['name'].str.contains(name, case=False, na=False)]
        for _, row in matches.iterrows():
            threats.append({
                'timestamp': row.get('timestamp'),
                'indicator': row.get('name'),
                'type': 'Suspicious Process',
                'severity': 'HIGH',
                'pid': row.get('pid'),
                'username': row.get('username', 'Unknown'),
                'mitre_technique': 'T1059'
            })
    
    if 'cpu_percent' in processes_df.columns:
        high_cpu = processes_df[processes_df['cpu_percent'] > 80]
        for _, row in high_cpu.iterrows():
            threats.append({
                'timestamp': row.get('timestamp'),
                'indicator': row.get('name'),
                'type': 'High CPU Usage',
                'severity': 'MEDIUM',
                'cpu_percent': row.get('cpu_percent'),
                'mitre_technique': 'T1499'
            })
    
    return pd.DataFrame(threats)


def detect_registry_threats(registry_df):
    if registry_df.empty:
        return pd.DataFrame()
    
    threats = []
    persistence_keys = [
        (r'Software\\Microsoft\\Windows\\CurrentVersion\\Run', 'Run Key', 'T1547.001'),
        (r'Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce', 'RunOnce Key', 'T1547.001')
    ]
    
    for _, row in registry_df.iterrows():
        key_path = str(row.get('key_path', ''))
        for persist_key, key_type, technique in persistence_keys:
            if persist_key in key_path:
                threats.append({
                    'timestamp': row.get('timestamp'),
                    'indicator': f"{row.get('hive', '')}\\{key_path}",
                    'type': f'Registry Persistence - {key_type}',
                    'severity': 'HIGH',
                    'operation': row.get('operation', 'MODIFIED'),
                    'mitre_technique': technique
                })
                break
    
    return pd.DataFrame(threats)


def check_software_vulnerabilities(software_df):
    if software_df.empty:
        return pd.DataFrame()
    
    vulnerabilities = []
    for _, row in software_df.iterrows():
        name = str(row.get('name', '')).lower()
        version = str(row.get('version', ''))
        
        for vuln_name, cves in SOFTWARE_CVES.items():
            if vuln_name in name:
                for cve in cves:
                    vulnerabilities.append({
                        'software': row.get('name'),
                        'version': version,
                        'cve_id': cve['id'],
                        'severity': cve['severity'],
                        'fixed_version': cve['fixed_version']
                    })
    
    return pd.DataFrame(vulnerabilities)


def get_ip_geolocation(ip):
    """Get IP geolocation data"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'isp': data.get('isp', 'Unknown'),
                    'lat': data.get('lat', 0),
                    'lon': data.get('lon', 0)
                }
    except:
        pass
    return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown', 'lat': 0, 'lon': 0}

# ============================================
# AI/ML FUNCTIONS
# ============================================

def prepare_ai_features(network_df):
    if network_df.empty or 'ip_src' not in network_df.columns:
        return pd.DataFrame()
    
    agg_dict = {'ip_src': 'first'}
    
    if 'frame_len' in network_df.columns:
        agg_dict['frame_len'] = ['sum', 'mean', 'std']
    
    port_col = None
    for col in ['dst_port', 'tcp_dstport', 'udp_dstport']:
        if col in network_df.columns:
            port_col = col
            break
    
    if port_col:
        agg_dict[port_col] = 'nunique'
    
    grouped = network_df.groupby('ip_src').agg(agg_dict).reset_index(drop=True)
    
    rename_map = {}
    if 'frame_len_sum' in grouped.columns:
        rename_map['frame_len_sum'] = 'total_bytes'
    if 'frame_len_mean' in grouped.columns:
        rename_map['frame_len_mean'] = 'avg_bytes'
    if port_col and f'{port_col}_nunique' in grouped.columns:
        rename_map[f'{port_col}_nunique'] = 'unique_ports'
    
    grouped = grouped.rename(columns=rename_map)
    
    return grouped


def train_ai_model(network_df):
    """Train Isolation Forest model for anomaly detection"""
    features = prepare_ai_features(network_df)
    
    if features.empty or len(features) < 10:
        return None, None, []
    
    feature_cols = [col for col in ['total_bytes', 'avg_bytes', 'unique_ports'] if col in features.columns]
    
    if len(feature_cols) < 2:
        return None, None, []
    
    X = features[feature_cols].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    model.fit(X_scaled)
    
    model_data = {
        'model': model,
        'feature_names': feature_cols,
        'training_date': datetime.now().isoformat()
    }
    joblib.dump(model_data, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    
    return model, scaler, feature_cols


def load_ai_model():
    if os.path.exists(MODEL_FILE) and os.path.exists(SCALER_FILE):
        model_data = joblib.load(MODEL_FILE)
        if isinstance(model_data, dict):
            model = model_data['model']
            feature_names = model_data.get('feature_names', [])
        else:
            model = model_data
            feature_names = []
        scaler = joblib.load(SCALER_FILE)
        return model, scaler, feature_names
    return None, None, []


def detect_ai_anomalies(network_df, model, scaler, feature_names):
    if network_df.empty or model is None:
        return pd.DataFrame()
    
    features = prepare_ai_features(network_df)
    if features.empty:
        return pd.DataFrame()
    
    available_features = [f for f in feature_names if f in features.columns]
    if not available_features:
        return pd.DataFrame()
    
    X = features[available_features].fillna(0)
    X_scaled = scaler.transform(X)
    
    predictions = model.predict(X_scaled)
    scores = model.decision_function(X_scaled)
    
    features['anomaly_score'] = scores
    features['is_anomaly'] = predictions == -1
    
    return features[features['is_anomaly']].copy()

# ============================================
# OPENROUTER CHATBOT CLASS
# ============================================

class SecurityChatbot:
    """AI-powered security assistant using OpenRouter API"""
    
    def __init__(self, api_key, data_manager, model=DEFAULT_MODEL):
        self.api_key = api_key
        self.data_manager = data_manager
        self.model = model
        self.api_base = OPENROUTER_API_BASE
        self.conversation_history = []
        self.system_prompt = self._create_system_prompt()
        
    def _create_system_prompt(self):
        return """You are an expert Security Operations Center (NEUROFENCE2 ENTERPRISE PLATFORM) analyst.
Your role is to help security analysts understand threats, analyze data, and respond to incidents.

CAPABILITIES:
- Analyze security alerts and provide context
- Explain MITRE ATT&CK techniques
- Provide remediation steps
- Analyze network traffic patterns
- Identify IOCs
- Recommend security best practices

RESPONSE GUIDELINES:
- Be concise but thorough
- Use bullet points for clarity
- Include MITRE ATT&CK references
- Provide actionable recommendations
- Maintain professional tone
"""
    
    def add_to_history(self, role, content):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_mitre_info(self, technique_id):
        technique_id = technique_id.upper()
        if technique_id in MITRE_ATTACK_DB:
            return MITRE_ATTACK_DB[technique_id]
        return None
    
    def get_alert_summary(self):
        """Get summary of recent alerts"""
        alerts_df = self.data_manager.get_recent_alerts(limit=200)
        if alerts_df.empty:
            return "No alerts found."
        
        critical = len(alerts_df[alerts_df['severity'] == 'CRITICAL']) if 'severity' in alerts_df.columns else 0
        high = len(alerts_df[alerts_df['severity'] == 'HIGH']) if 'severity' in alerts_df.columns else 0
        
        summary = f"Alert Summary:\n- Total: {len(alerts_df)}\n- Critical: {critical}\n- High: {high}\n\n"
        summary += "Recent Alerts:\n"
        
        for _, row in alerts_df.head(5).iterrows():
            summary += f"- {row.get('timestamp', '')} | {row.get('alert_type', '')} | {row.get('severity', '')}\n"
        
        return summary
    
    def generate_response(self, user_query, page_context):
        """Generate response using OpenRouter API"""
        if not self.api_key or self.api_key == "your-openrouter-api-key-here":
            return "⚠️ Chatbot not configured. Please set your OpenRouter API key."
        
        lowered_query = user_query.lower()
        
        # Check for MITRE query
        mitre_match = re.search(r'T\d{4}', user_query.upper())
        if mitre_match:
            mitre_info = self.get_mitre_info(mitre_match.group())
            if mitre_info:
                return f"""**MITRE ATT&CK {mitre_match.group()}: {mitre_info['name']}**

**Tactic:** {mitre_info['tactic']}

**Description:** {mitre_info['description']}

**Detection:** {mitre_info['detection']}

**Mitigation:** {mitre_info['mitigation']}"""
        
        # Check for alert summary
        if 'summary' in lowered_query or 'overview' in lowered_query:
            return self.get_alert_summary()
        
        # Prepare API request
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": f"Current page: {page_context}"}
            ]
            
            for msg in self.conversation_history[-10:]:
                messages.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            
            messages.append({"role": "user", "content": user_query})
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://localhost:8501"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result['choices'][0]['message']['content']
                self.add_to_history("user", user_query)
                self.add_to_history("assistant", assistant_response)
                return assistant_response
            else:
                return f"❌ API Error: {response.status_code}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def clear_history(self):
        self.conversation_history = []

# ============================================
# AUTHENTICATION
# ============================================

def check_password():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if st.session_state['authenticated']:
        return True
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div class="login-container-dark">
                    <div style="text-align: center; margin-bottom: 2rem;">
                        <div style="font-size: 48px;">🛡️</div>
                        <h1>NeuroFence2</h1>
                        <p style="color: #888;">Security Operations Center</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            
            if st.button("Login", use_container_width=True):
                if username in USERS and USERS[username] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.success("Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    return False

# ============================================
# PAGE RENDER FUNCTIONS
# ============================================

def render_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.markdown(f"""
            <div style="background: rgba(12,18,32,0.92); padding: 0.7rem 1rem; border-radius: 16px;">
                <span style="color: #4ade80;">👤 {st.session_state['username']}</span>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <h1 style="text-align: center; background: linear-gradient(135deg, #38bdf8, #22c55e); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                NEUROFENCE2 SECURITY CENTER
            </h1>
        """, unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Logout"):
            st.session_state['authenticated'] = False
            st.rerun()


def render_navigation():
    with st.container():
        st.markdown('<div class="glass-container-dark" style="padding: 0.5rem;">', unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Main Dashboard", "Network Threats", "System DLP", "Threat Intelligence", "AI Detection"],
            icons=["house", "wifi", "folder", "shield", "robot"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#0f766e", "font-size": "1.2rem"},
                "nav-link": {
                    "font-size": "1rem",
                    "text-align": "center",
                    "margin": "0px",
                    "padding": "0.75rem 1rem",
                    "color": "#5f6b7a",
                    "font-weight": "600",
                    "border-radius": "999px",
                },
                "nav-link-selected": {
                    "background": "linear-gradient(135deg, #0f766e 0%, #115e59 100%)",
                    "color": "white",
                },
            }
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        return selected


def render_main_dashboard(data_manager, minutes):
    """Main Dashboard with key metrics and alerts"""
    
    with st.spinner("Loading security telemetry from Firebase..."):
        network_df = data_manager.get_network_packets(minutes=minutes, limit=10000)
        alerts_df = data_manager.get_recent_alerts(limit=500)
        network_threats_df = data_manager.get_network_threats(minutes=minutes, limit=500)
        usb_activity_df = data_manager.get_usb_file_activity(minutes=minutes, limit=1000)
        processes_df = data_manager.get_processes(limit=500)
        perf_df = data_manager.get_performance_metrics(minutes=minutes)
        
        port_scans = detect_port_scans(network_df)
        dns_threats = detect_dns_threats(data_manager.get_dns_queries(minutes=minutes, limit=1000))
        http_attacks = detect_http_attacks(data_manager.get_http_transactions(minutes=minutes, limit=1000))
        file_threats = detect_suspicious_files(data_manager.get_file_operations(minutes=minutes, limit=1000))
        process_threats = detect_process_threats(processes_df)
        
        top_talkers = data_manager.get_top_talkers(limit=10, minutes=minutes)
        
        # Get devices
        devices = data_manager.get_devices()
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    critical_count = len(alerts_df[alerts_df['severity'] == 'CRITICAL']) if not alerts_df.empty else 0
    total_threats = len(port_scans) + len(dns_threats) + len(http_attacks) + len(file_threats) + len(process_threats) + len(network_threats_df)
    
    with col1:
        st.markdown(f"""
            <div class="metric-card-dark metric-critical">
                <div class="metric-label">CRITICAL ALERTS</div>
                <div class="metric-value">{critical_count}</div>
                <div class="metric-trend">Total: {len(alerts_df)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card-dark metric-high">
                <div class="metric-label">TOTAL THREATS</div>
                <div class="metric-value">{total_threats}</div>
                <div class="metric-trend">Network: {len(network_threats_df)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card-dark metric-medium">
                <div class="metric-label">USB FILE EVENTS</div>
                <div class="metric-value">{len(usb_activity_df):,}</div>
                <div class="metric-trend">DLP Monitoring</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="metric-card-dark metric-low">
                <div class="metric-label">ACTIVE DEVICES</div>
                <div class="metric-value">{len(devices)}</div>
                <div class="metric-trend">Telemetry Sources</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Two column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        if not top_talkers.empty:
            fig = px.bar(
                top_talkers.head(10),
                x='packet_count',
                y='ip_src',
                orientation='h',
                title="Top Source IPs",
                color='packet_count',
                color_continuous_scale='Reds'
            )
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No network packet data available")
    
    with col2:
        if not perf_df.empty and 'cpu_percent' in perf_df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['cpu_percent'], 
                                    name="CPU %", line=dict(color='#00ffff', width=2)))
            if 'memory_percent' in perf_df.columns:
                fig.add_trace(go.Scatter(x=perf_df['timestamp'], y=perf_df['memory_percent'],
                                        name="Memory %", line=dict(color='#ffaa00', width=2)))
            fig.update_layout(title="System Performance", plot_bgcolor='rgba(0,0,0,0)', 
                            paper_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No performance data available")
    
    st.markdown("---")
    
    # Recent Critical Alerts
    if not alerts_df.empty:
        st.markdown("### 🚨 Recent Security Alerts")
        critical = alerts_df.head(5)
        
        for _, alert in critical.iterrows():
            severity = alert.get('severity', 'MEDIUM')
            severity_class = "alert-critical" if severity == 'CRITICAL' else "alert-high" if severity == 'HIGH' else "alert-card-dark"
            st.markdown(f"""
                <div class="alert-card-dark {severity_class}">
                    <div class="alert-time">{alert.get('timestamp', '')}</div>
                    <div class="alert-title">🚨 {alert.get('alert_type', 'Unknown Alert')}</div>
                    <div class="alert-description">{alert.get('description', 'No description')[:200]}</div>
                    <div class="alert-source">
                        <span class="status-badge status-{severity.lower()}">{severity}</span>
                        Source: {alert.get('source', 'Unknown')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No alerts found. Check if the agent is running and sending data to Firebase.")
    
    # Device Status Section
    if devices:
        st.markdown("---")
        st.markdown("### 🖥️ Connected Devices")
        
        cols = st.columns(4)
        for idx, device in enumerate(devices[:8]):
            with cols[idx % 4]:
                st.markdown(f"""
                    <div class="device-card">
                        <div class="device-name">🖥️ {device}</div>
                        <div class="device-stats">
                            <span class="status-online">● ONLINE</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)


def render_network_threats(data_manager, minutes):
    """Network threats analysis page"""
    st.markdown("<h1 style='text-align: center;'>Network Threat Observatory</h1>", unsafe_allow_html=True)
    
    with st.spinner("Analyzing network threats from Firebase..."):
        network_df = data_manager.get_network_packets(minutes=minutes, limit=20000)
        dns_df = data_manager.get_dns_queries(minutes=minutes, limit=2000)
        http_df = data_manager.get_http_transactions(minutes=minutes, limit=2000)
        network_threats_df = data_manager.get_network_threats(minutes=minutes, limit=1000)
        
        port_scans = detect_port_scans(network_df)
        dns_threats = detect_dns_threats(dns_df)
        http_attacks = detect_http_attacks(http_df)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Port Scans", len(port_scans))
    with col2:
        st.metric("DNS Threats", len(dns_threats))
    with col3:
        st.metric("HTTP Attacks", len(http_attacks))
    with col4:
        st.metric("Engine Threats", len(network_threats_df))
    
    st.markdown("---")
    
    # MITRE ATT&CK Summary
    st.markdown("### MITRE ATT&CK Techniques Detected")
    
    col1, col2 = st.columns(2)
    
    if not port_scans.empty:
        with col1:
            with st.expander(f"🚨 T1046 - Network Service Scanning ({len(port_scans)} detected)"):
                st.dataframe(port_scans[['src_ip', 'ports_scanned']].head(10), use_container_width=True)
    
    if not dns_threats.empty:
        with col2:
            with st.expander(f"🚨 T1568 - DNS Calculation ({len(dns_threats)} detected)"):
                st.dataframe(dns_threats[['indicator', 'type', 'severity']].head(10), use_container_width=True)
    
    if not http_attacks.empty:
        with col1:
            with st.expander(f"🚨 T1190 - Exploit Public-Facing Application ({len(http_attacks)} detected)"):
                st.dataframe(http_attacks[['indicator', 'type', 'src_ip']].head(10), use_container_width=True)
    
    st.markdown("---")
    
    # Detailed Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Network Threats", "DNS Queries", "HTTP Transactions", "Raw Packets"])
    
    with tab1:
        if not network_threats_df.empty:
            st.dataframe(network_threats_df.head(200), use_container_width=True)
        else:
            st.info("No network threats detected")
    
    with tab2:
        if not dns_df.empty:
            display_cols = ['timestamp', 'query_name', 'query_type', 'client_ip', 'entropy']
            available = [c for c in display_cols if c in dns_df.columns]
            st.dataframe(dns_df[available].head(200), use_container_width=True)
        else:
            st.info("No DNS data available")
    
    with tab3:
        if not http_df.empty:
            display_cols = ['timestamp', 'method', 'host', 'uri', 'status', 'client_ip']
            available = [c for c in display_cols if c in http_df.columns]
            st.dataframe(http_df[available].head(200), use_container_width=True)
        else:
            st.info("No HTTP data available")
    
    with tab4:
        if not network_df.empty:
            display_cols = ['timestamp', 'ip_src', 'ip_dst', 'frame_len', '_device']
            available = [c for c in display_cols if c in network_df.columns]
            st.dataframe(network_df[available].head(200), use_container_width=True)
        else:
            st.info("No packet data available")


def render_system_dlp(data_manager, minutes):
    """Data Loss Prevention page"""
    st.markdown("<h1 style='text-align: center;'>Data Loss Prevention Studio</h1>", unsafe_allow_html=True)
    
    with st.spinner("Analyzing DLP threats from Firebase..."):
        files_df = data_manager.get_file_operations(minutes=minutes, limit=2000)
        processes_df = data_manager.get_processes(limit=500)
        registry_df = data_manager.get_registry_keys(limit=500)
        software_df = data_manager.get_software(limit=500)
        usb_activity_df = data_manager.get_usb_file_activity(minutes=minutes, limit=2000)
        usb_devices_df = data_manager.get_usb_devices(minutes=minutes, limit=200)
        
        file_threats = detect_suspicious_files(files_df)
        process_threats = detect_process_threats(processes_df)
        registry_threats = detect_registry_threats(registry_df)
        vulnerabilities = check_software_vulnerabilities(software_df)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Suspicious Files", len(file_threats))
    with col2:
        st.metric("Process Threats", len(process_threats))
    with col3:
        st.metric("Registry Threats", len(registry_threats))
    with col4:
        st.metric("USB Events", len(usb_activity_df))
    
    st.markdown("---")
    
    # MITRE ATT&CK Summary
    st.markdown("### MITRE ATT&CK Techniques Detected")
    
    col1, col2 = st.columns(2)
    
    if not file_threats.empty:
        with col1:
            with st.expander(f"🚨 T1204 - User Execution ({len(file_threats)} detected)"):
                st.dataframe(file_threats[['indicator', 'type', 'severity']].head(10), use_container_width=True)
    
    if not process_threats.empty:
        with col2:
            with st.expander(f"🚨 T1059 - Command and Scripting ({len(process_threats)} detected)"):
                st.dataframe(process_threats[['indicator', 'type', 'pid']].head(10), use_container_width=True)
    
    if not registry_threats.empty:
        with col1:
            with st.expander(f"🚨 T1547 - Registry Run Keys ({len(registry_threats)} detected)"):
                st.dataframe(registry_threats[['indicator', 'operation']].head(10), use_container_width=True)
    
    st.markdown("---")
    
    # Detailed Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["USB Activity", "File Operations", "Processes", "Registry", "Software"])
    
    with tab1:
        if not usb_activity_df.empty:
            st.dataframe(usb_activity_df.head(200), use_container_width=True)
        if not usb_devices_df.empty:
            st.markdown("### USB Devices")
            st.dataframe(usb_devices_df.head(100), use_container_width=True)
        else:
            st.info("No USB activity data available")
    
    with tab2:
        if not files_df.empty:
            st.dataframe(files_df.head(200), use_container_width=True)
        else:
            st.info("No file operation data available")
    
    with tab3:
        if not processes_df.empty:
            display_cols = ['name', 'pid', 'cpu_percent', 'memory_percent', 'username']
            available = [c for c in display_cols if c in processes_df.columns]
            st.dataframe(processes_df[available].head(200), use_container_width=True)
        else:
            st.info("No process data available")
    
    with tab4:
        if not registry_df.empty:
            st.dataframe(registry_df.head(200), use_container_width=True)
        else:
            st.info("No registry data available")
    
    with tab5:
        if not software_df.empty:
            st.dataframe(software_df.head(200), use_container_width=True)
        if not vulnerabilities.empty:
            st.markdown("### Vulnerabilities Detected")
            st.dataframe(vulnerabilities, use_container_width=True)
        if software_df.empty and vulnerabilities.empty:
            st.info("No software data available")


def render_threat_intelligence(data_manager, minutes):
    """Threat Intelligence page"""
    st.markdown("<h1 style='text-align: center;'>Threat Intelligence Workbench</h1>", unsafe_allow_html=True)
    
    with st.spinner("Loading threat intelligence from Firebase..."):
        all_ips = data_manager.get_all_ips(minutes=minutes)
        all_hashes = data_manager.get_all_file_hashes(limit=50)
        network_df = data_manager.get_network_packets(minutes=minutes, limit=5000)
        
        external_ips = [ip for ip in all_ips if ip and not ip.startswith(('10.', '192.168.', '127.', '172.'))]
    
    tab1, tab2 = st.tabs(["IP Intelligence", "Hash Intelligence"])
    
    with tab1:
        if external_ips:
            st.markdown(f"### Found {len(external_ips)} External IPs")
            selected_ip = st.selectbox("Select IP for analysis:", external_ips[:100])
            
            if selected_ip:
                col1, col2 = st.columns(2)
                
                with col1:
                    geo = get_ip_geolocation(selected_ip)
                    st.markdown("#### IP Geolocation")
                    st.json(geo)
                    
                    if geo['lat'] != 0 and geo['lon'] != 0:
                        fig = go.Figure(go.Scattergeo(
                            lon=[geo['lon']],
                            lat=[geo['lat']],
                            text=[selected_ip],
                            mode='markers',
                            marker=dict(size=15, color='red')
                        ))
                        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### Threat Intelligence Sources")
                    for name, url in THREAT_INTEL_SOURCES.items():
                        st.markdown(f"""
                            <div style="background: #1a1f2e; padding: 0.5rem; border-radius: 8px; margin: 0.3rem 0; text-align: center;">
                                <a href="{url}{selected_ip}" target="_blank" style="color: #667eea; text-decoration: none;">{name}</a>
                            </div>
                        """, unsafe_allow_html=True)
                
                ip_activity = network_df[network_df['ip_src'] == selected_ip]
                if not ip_activity.empty:
                    st.markdown("#### Recent Activity")
                    st.dataframe(ip_activity[['timestamp', 'ip_dst', 'frame_len']].head(20), use_container_width=True)
        else:
            st.info("No external IPs found in the current data")
    
    with tab2:
        if all_hashes:
            selected_hash = st.selectbox("Select hash for analysis:", all_hashes)
            
            if selected_hash:
                st.markdown("#### Hash Details")
                st.code(selected_hash)
                
                st.markdown("#### Threat Intelligence Sources")
                cols = st.columns(3)
                for i, (name, url) in enumerate(HASH_INTEL_SOURCES.items()):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div style="background: #1a1f2e; padding: 0.5rem; border-radius: 8px; margin: 0.2rem; text-align: center;">
                                <a href="{url}{selected_hash}" target="_blank" style="color: #667eea;">{name}</a>
                            </div>
                        """, unsafe_allow_html=True)
                
                hash_files = data_manager.get_file_operations(minutes=minutes, limit=500)
                hash_files = hash_files[hash_files['file_hash'] == selected_hash] if 'file_hash' in hash_files.columns else pd.DataFrame()
                if not hash_files.empty:
                    st.markdown("#### File Operations")
                    st.dataframe(hash_files[['timestamp', 'operation', 'file_path']], use_container_width=True)
        else:
            st.info("No file hashes available for analysis")


def render_ai_detection(data_manager, minutes):
    """AI Detection page with chatbot"""
    st.markdown("<h1 style='text-align: center;'>AI Detection Command Deck</h1>", unsafe_allow_html=True)
    
    # Load AI model
    model, scaler, feature_names = load_ai_model()
    
    with st.spinner("Running AI analysis on Firebase data..."):
        network_df = data_manager.get_network_packets(minutes=minutes, limit=100000)
        alerts_df = data_manager.get_recent_alerts(limit=200)
        
        if model is None:
            st.warning("⚠️ AI model not trained. Use the training option below to train the model.")
        else:
            anomalies = detect_ai_anomalies(network_df, model, scaler, feature_names)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-card-dark metric-medium">
                        <div class="metric-label">TOTAL PACKETS</div>
                        <div class="metric-value">{len(network_df):,}</div>
                    </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                    <div class="metric-card-dark metric-high">
                        <div class="metric-label">ANOMALIES DETECTED</div>
                        <div class="metric-value">{len(anomalies)}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            if not anomalies.empty:
                st.markdown("### 🚨 Anomalous IPs Detected")
                display_cols = ['ip_src', 'total_bytes', 'unique_ports', 'anomaly_score']
                available = [c for c in display_cols if c in anomalies.columns]
                st.dataframe(anomalies[available].head(50), use_container_width=True)
                
                if len(anomalies) > 1:
                    fig = px.scatter(
                        anomalies.head(100),
                        x='total_bytes' if 'total_bytes' in anomalies.columns else anomalies.index,
                        y='anomaly_score',
                        title="Anomaly Scores by IP",
                        color='anomaly_score',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No anomalies detected by AI model")
    
    # AI Training Section
    st.markdown("---")
    st.markdown("### 🤖 AI Model Training")
    
    col1, col2 = st.columns(2)
    with col1:
        training_hours = st.number_input("Training Data (hours)", min_value=1, max_value=168, value=24)
    
    with col2:
        if st.button("🚀 Train AI Model", use_container_width=True):
            with st.spinner("Training AI model on network data..."):
                network_data = data_manager.get_network_packets(minutes=training_hours, limit=50000)
                if len(network_data) > 100:
                    model, scaler, features = train_ai_model(network_data)
                    if model:
                        st.success(f"✅ Model trained successfully on {len(network_data):,} packets!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Training failed - insufficient data")
                else:
                    st.error(f"Need more data. Only {len(network_data)} packets available.")
    
    # Chatbot Section
    st.markdown("---")
    st.markdown("### 🤖 AI Security Assistant Chatbot")
    
    if 'chatbot' not in st.session_state:
        st.session_state['chatbot'] = SecurityChatbot(OPENROUTER_API_KEY, data_manager, DEFAULT_MODEL)
    
    chatbot = st.session_state['chatbot']
    
    # Model selector
    available_models = ["openai/gpt-3.5-turbo", "openai/gpt-4", "anthropic/claude-3-haiku", "google/gemini-pro"]
    selected_model = st.selectbox("AI Model", available_models, index=0)
    if selected_model != chatbot.model:
        chatbot.model = selected_model
    
    # Chat interface
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    
    for msg in chatbot.conversation_history[-15:]:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-message">{msg["content"]}<div class="chat-timestamp">{msg["timestamp"][11:16]}</div></div>', unsafe_allow_html=True)
        elif msg["role"] == "assistant":
            st.markdown(f'<div class="assistant-message">{msg["content"]}<div class="chat-timestamp">{msg["timestamp"][11:16]}</div></div>', unsafe_allow_html=True)
        elif msg["role"] == "system":
            st.markdown(f'<div class="system-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input("Ask a question:", placeholder="e.g., 'Summarize alerts', 'What is T1046?', 'Show anomalies'", label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Send 📤")
        
        if submitted and user_input:
            with st.spinner("Thinking..."):
                response = chatbot.generate_response(user_input, "AI Detection")
                st.rerun()
    
    # Quick actions
    st.markdown('<div class="quick-actions">', unsafe_allow_html=True)
    quick_queries = [
        ("📊 Summary", "Summarize all alerts"),
        ("🚨 Critical", "What are the top critical alerts?"),
        ("🔍 MITRE T1046", "Explain MITRE T1046"),
        ("💾 USB DLP", "Any USB exfiltration risks?"),
        ("🌐 Threats", "Show me network threats")
    ]
    
    for label, query in quick_queries:
        if st.button(label, key=f"quick_{label}"):
            with st.spinner("Thinking..."):
                response = chatbot.generate_response(query, "AI Detection")
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# MAIN APPLICATION
# ============================================

def main():
    # Initialize session state
    if 'hours_filter' not in st.session_state:
        st.session_state['hours_filter'] = 24
        st.session_state['minutes_filter'] = 1440
    
    # Check authentication
    if not check_password():
        return
    
    # Initialize data manager
    data_manager = FirebaseDataManager()
    
    # Render header
    render_header()
    
    # Time filter
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            hours = st.slider("⏱️ Time Range (hours)", 1, 168, st.session_state['hours_filter'], key="time_slider")
            st.session_state['hours_filter'] = hours
            st.session_state['minutes_filter'] = hours * 60
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Refresh Data from Firebase", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Render navigation
    selected_page = render_navigation()
    
    # Render selected page
    minutes = st.session_state['minutes_filter']
    
    if selected_page == "Main Dashboard":
        render_main_dashboard(data_manager, minutes)
    elif selected_page == "Network Threats":
        render_network_threats(data_manager, minutes)
    elif selected_page == "System DLP":
        render_system_dlp(data_manager, minutes)
    elif selected_page == "Threat Intelligence":
        render_threat_intelligence(data_manager, minutes)
    elif selected_page == "AI Detection":
        render_ai_detection(data_manager, minutes)
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 1rem;">
            NeuroFence2 Enterprise Platform<br>
            <small>Real-time Security Monitoring • DLP • Threat Intelligence • AI Detection</small>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
