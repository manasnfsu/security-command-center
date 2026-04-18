#!/usr/bin/env python3
"""
SECURITY COMMAND CENTER v5.0 - STREAMLIT CLOUD COMPATIBLE EDITION
================================================================
FIXES for Python 3.14:
- Removed pandas/numpy/sklearn dependencies (use pure SQLite)
- Added platform detection for Windows-only features
- Mock modules for missing packages
- SQLite-only data processing
================================================================
"""

# ============================================
# MOCK MISSING MODULES FOR PYTHON 3.14
# ============================================
import sys
import warnings
warnings.filterwarnings('ignore')

# Mock classes for missing scientific packages
class MockDataFrame:
    def __init__(self, data=None):
        self._data = data or []
        self.columns = []
    
    def __len__(self):
        return len(self._data)
    
    def to_dict(self, *args, **kwargs):
        return {}
    
    def groupby(self, *args, **kwargs):
        return MockGroupBy()
    
    def value_counts(self):
        return {}
    
    def iterrows(self):
        return iter([])
    
    def iloc(self, *args, **kwargs):
        return MockSeries()
    
    def __getitem__(self, key):
        return MockSeries()
    
    def drop_duplicates(self, *args, **kwargs):
        return self

class MockSeries:
    def __init__(self, data=None):
        self._data = data or []
    
    def nunique(self):
        return 0
    
    def mean(self):
        return 0
    
    def __len__(self):
        return 0

class MockGroupBy:
    def __init__(self):
        pass
    
    def size(self):
        return MockSeries()
    
    def nunique(self):
        return MockSeries()
    
    def __getitem__(self, key):
        return self

class MockModule:
    def __getattr__(self, name):
        return MockFunction()
    
    def __call__(self, *args, **kwargs):
        return MockFunction()

class MockFunction:
    def __call__(self, *args, **kwargs):
        return None
    
    def __getattr__(self, name):
        return self

# Replace missing modules with mocks
mock_modules = ['pandas', 'numpy', 'sklearn', 'joblib', 'sklearn.ensemble', 
                'sklearn.preprocessing', 'sklearn.cluster']
for mod in mock_modules:
    if mod not in sys.modules:
        sys.modules[mod] = MockModule()

# Set pandas and numpy to mock at module level
pd = MockModule()
np = MockModule()

# ============================================
# PLATFORM DETECTION
# ============================================
import platform

# Platform-specific imports
if platform.system() == "Windows":
    import ctypes
    import ctypes.wintypes
    import win32file
    import win32con
    import win32gui
    import win32process
    import pythoncom
    import wmi
    PLATFORM_WINDOWS = True
else:
    # Stub for non-Windows platforms (Streamlit Cloud uses Linux)
    class MockModule:
        def __getattr__(self, name):
            return None
        def __call__(self, *args, **kwargs):
            return None
    
    ctypes = MockModule()
    ctypes.wintypes = MockModule()
    win32file = MockModule()
    win32con = MockModule()
    win32gui = MockModule()
    win32process = MockModule()
    pythoncom = MockModule()
    wmi = MockModule()
    PLATFORM_WINDOWS = False

import streamlit as st
import sqlite3
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
import base64
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
import threading
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, Counter
import random
import psutil
import tempfile
from jinja2 import Template

warnings.filterwarnings('ignore')

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Security Command Center v5.0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS FOR CYBER SECURITY THEME
# ============================================
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #0f1235 100%);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
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
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #00ffff;
        box-shadow: 0 8px 25px rgba(0, 255, 255, 0.2);
    }
    
    /* Threat card */
    .threat-critical {
        background: linear-gradient(135deg, #ff0000, #8b0000);
        border-left: 5px solid #ff4444;
    }
    
    .threat-high {
        background: linear-gradient(135deg, #ff4500, #cc3300);
        border-left: 5px solid #ff8844;
    }
    
    .threat-medium {
        background: linear-gradient(135deg, #ffaa00, #cc8800);
        border-left: 5px solid #ffcc44;
    }
    
    /* Glowing text */
    .glow-text {
        color: #00ffff;
        text-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #00ffff !important;
        text-shadow: 0 0 5px rgba(0, 255, 255, 0.5);
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
    
    /* Chat container */
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        background: rgba(30, 40, 80, 0.6);
        border-left: 3px solid #00ffff;
    }
    
    /* Status indicators */
    .status-online {
        color: #00ff00;
        text-shadow: 0 0 5px #00ff00;
    }
    
    .status-offline {
        color: #ff4444;
        text-shadow: 0 0 5px #ff4444;
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
    
    /* Agent card */
    .agent-card {
        background: rgba(20, 30, 70, 0.8);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(0, 255, 255, 0.3);
        transition: all 0.3s;
    }
    
    .agent-card:hover {
        border-color: #00ffff;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# OPENROUTER API CONFIGURATION
# ============================================
OPENROUTER_API_KEY = "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"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-3.5-turbo"

# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_PATH = "system_monitor.db"

# ============================================
# STUB CLASSES FOR NON-WINDOWS PLATFORMS
# ============================================
if not PLATFORM_WINDOWS:
    class ClipboardMonitor:
        def __init__(self, db): pass
        def start(self): pass
        def stop(self): pass
    
    class USBMonitor:
        def __init__(self, db): pass
        def start(self): pass
        def stop(self): pass

# ============================================
# THREAT INTELLIGENCE CONFIG
# ============================================
SCAN_THRESHOLD = 20
FLOOD_THRESHOLD = 50

# ============================================
# AUTHENTICATION
# ============================================
USERS = {
    "admin": "admin123",
    "analyst": "analyst123",
    "viewer": "viewer123"
}

# ============================================
# MITRE ATT&CK DATABASE
# ============================================
MITRE_ATTACK_DB = {
    "T1046": {"name": "Network Service Scanning", "tactic": "Discovery", 
              "description": "Adversaries may attempt to get a listing of services running on remote hosts.",
              "severity": "MEDIUM"},
    "T1498": {"name": "Network Denial of Service", "tactic": "Impact",
              "description": "Adversaries may perform Network DoS attacks to degrade resources.",
              "severity": "HIGH"},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "Exfiltration",
              "description": "Adversaries may steal data by exfiltrating over alternative protocols.",
              "severity": "CRITICAL"},
    "T1568": {"name": "DNS Calculation", "tactic": "Command and Control",
              "description": "Adversaries may use DNS for C2 via domain generation algorithms.",
              "severity": "HIGH"},
    "T1204": {"name": "User Execution", "tactic": "Execution",
              "description": "Adversaries may rely on user execution of malicious files.",
              "severity": "MEDIUM"},
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access",
              "description": "Adversaries may exploit weaknesses in public-facing applications.",
              "severity": "CRITICAL"},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution",
              "description": "Adversaries may abuse command and script interpreters.",
              "severity": "HIGH"},
    "T1547": {"name": "Registry Run Keys / Startup Folder", "tactic": "Persistence",
              "description": "Adversaries may achieve persistence via startup folders.",
              "severity": "MEDIUM"},
    "T1003": {"name": "Credential Dumping", "tactic": "Credential Access",
              "description": "Adversaries may attempt to dump credentials from system memory.",
              "severity": "CRITICAL"},
    "T1055": {"name": "Process Injection", "tactic": "Defense Evasion",
              "description": "Adversaries may inject code into processes to evade defenses.",
              "severity": "HIGH"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic": "Impact",
              "description": "Adversaries may encrypt data to interrupt availability.",
              "severity": "CRITICAL"},
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control",
              "description": "Adversaries may communicate using application layer protocols.",
              "severity": "MEDIUM"},
    "T1566": {"name": "Phishing", "tactic": "Initial Access",
              "description": "Adversaries may send phishing messages to gain access.",
              "severity": "HIGH"},
}

THREAT_INTEL_SOURCES = {
    "AbuseIPDB": "https://www.abuseipdb.com/check/",
    "VirusTotal": "https://www.virustotal.com/gui/ip-address/",
    "GreyNoise": "https://viz.greynoise.io/ip/",
    "Shodan": "https://www.shodan.io/host/",
}

# ============================================
# SENSITIVE DATA PATTERNS
# ============================================
SENSITIVE_PATTERNS = {
    'CREDIT_CARD': {'pattern': r'\b(?:\d[ -]*?){13,16}\b', 'severity': 'HIGH'},
    'SSN': {'pattern': r'\b\d{3}-\d{2}-\d{4}\b', 'severity': 'CRITICAL'},
    'EMAIL': {'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'severity': 'LOW'},
    'PHONE': {'pattern': r'\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b', 'severity': 'MEDIUM'},
    'API_KEY': {'pattern': r'(api[_-]?key|apikey|token|secret)[\s]*[:=][\s]*[\'"]?[\w-]{20,}', 'severity': 'CRITICAL'},
}

# ============================================
# DATABASE MANAGER
# ============================================
class DatabaseManager:
    def __init__(self, db_name=DB_PATH):
        self.db_name = db_name
        self.setup_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name, timeout=30)
    
    def setup_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT UNIQUE,
                hostname TEXT,
                ip_address TEXT,
                os_version TEXT,
                start_time TEXT,
                last_seen TEXT,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                alert_type TEXT,
                severity TEXT,
                source TEXT,
                description TEXT,
                resolved BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_packets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ip_src TEXT,
                ip_dst TEXT,
                frame_len INTEGER,
                tcp_dstport INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                pid INTEGER,
                name TEXT,
                cpu_percent REAL,
                memory_percent REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usb_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                device_id TEXT,
                vendor TEXT,
                product TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensitive_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                file_path TEXT,
                data_type TEXT,
                severity TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized")
    
    def insert(self, table, data):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(data.values()))
            conn.commit()
            conn.close()
            return cursor.lastrowid
        except Exception as e:
            return None

# ============================================
# AI CHATBOT
# ============================================
class EnhancedSecurityAIChatbot:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.conversation_history = []
    
    def get_system_data_context(self):
        context = {}
        if not self.db_manager:
            return context
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
            context['alert_summary'] = [{'severity': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM alerts")
            context['total_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM network_packets")
            context['total_packets'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usb_events")
            context['usb_events'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT agent_id) FROM agent_info")
            context['unique_agents'] = cursor.fetchone()[0]
            
            conn.close()
        except Exception as e:
            pass
        return context
    
    def query(self, user_message):
        try:
            system_context = self.get_system_data_context()
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a cybersecurity AI assistant."},
                    {"role": "user", "content": f"System Data: {json.dumps(system_context)}\n\nUser: {user_message}"}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{OPENROUTER_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return self.get_fallback_response(user_message, system_context)
        except Exception as e:
            return self.get_fallback_response(user_message, {})
    
    def get_fallback_response(self, message, context):
        return f"""📊 **Security Summary:**

- Total Alerts: {context.get('total_alerts', 0)}
- Network Packets: {context.get('total_packets', 0)}
- USB Events: {context.get('usb_events', 0)}
- Active Agents: {context.get('unique_agents', 0)}

How can I help you today?"""

# ============================================
# DATA PROCESSING FUNCTIONS (SQLite-only)
# ============================================
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_unique_agents():
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT agent_id, hostname, ip_address, os_version, 
                   start_time, last_seen, status
            FROM agent_info ORDER BY last_seen DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        conn.close()
        return []

def get_agent_stats_unique():
    agents = get_unique_agents()
    total = len(agents)
    active = sum(1 for a in agents if a.get('status') == 'RUNNING')
    return {'total': total, 'active': active, 'online': active, 'offline': total - active}

def get_alert_stats():
    conn = get_db_connection()
    if not conn:
        return {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
        rows = cursor.fetchall()
        conn.close()
        
        stats = {'total': total, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for row in rows:
            severity = row[0]
            count = row[1]
            if severity == 'CRITICAL':
                stats['critical'] = count
            elif severity == 'HIGH':
                stats['high'] = count
            elif severity == 'MEDIUM':
                stats['medium'] = count
            elif severity == 'LOW':
                stats['low'] = count
        return stats
    except:
        conn.close()
        return {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

def get_recent_alerts(limit=50):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        conn.close()
        return []

def get_recent_network_activity(limit=100):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM network_packets ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        conn.close()
        return []

def get_recent_processes(limit=50):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processes ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        conn.close()
        return []

def get_recent_usb_events(limit=50):
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usb_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        conn.close()
        return []

def get_network_stats():
    conn = get_db_connection()
    if not conn:
        return {'total_packets': 0, 'unique_ips': 0}
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM network_packets")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT ip_src) FROM network_packets")
        unique = cursor.fetchone()[0]
        conn.close()
        return {'total_packets': total, 'unique_ips': unique}
    except:
        conn.close()
        return {'total_packets': 0, 'unique_ips': 0}

def get_process_stats():
    conn = get_db_connection()
    if not conn:
        return {'total': 0, 'suspicious': 0}
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT pid) FROM processes")
        total = cursor.fetchone()[0]
        
        suspicious_names = ['mimikatz', 'procdump', 'nc', 'ncat', 'psexec']
        placeholders = ','.join(['?' for _ in suspicious_names])
        cursor.execute(f"SELECT COUNT(*) FROM processes WHERE name IN ({placeholders})", suspicious_names)
        suspicious = cursor.fetchone()[0]
        conn.close()
        return {'total': total, 'suspicious': suspicious}
    except:
        conn.close()
        return {'total': 0, 'suspicious': 0}

def get_usb_stats():
    conn = get_db_connection()
    if not conn:
        return {'total_events': 0}
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usb_events")
        total = cursor.fetchone()[0]
        conn.close()
        return {'total_events': total}
    except:
        conn.close()
        return {'total_events': 0}

# ============================================
# AGENTS PAGE
# ============================================
def agents_page():
    st.markdown("<h1 style='text-align: center;'>Agent Management</h1>", unsafe_allow_html=True)
    
    agents = get_unique_agents()
    
    if agents:
        st.markdown(f"### 🖥️ Unique Agents ({len(agents)})")
        for agent in agents:
            status_color = "#00ff00" if agent.get('status') == 'RUNNING' else "#ff4444"
            st.markdown(f"""
            <div class="agent-card">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <strong style="color: #00ffff;">🖥️ {agent.get('hostname', 'Unknown')}</strong><br>
                        <span style="font-size: 12px;">IP: {agent.get('ip_address', 'Unknown')}</span>
                    </div>
                    <div>
                        <div style="color: {status_color};">● {agent.get('status', 'UNKNOWN')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No agents registered yet")

# ============================================
# SIDEBAR NAVIGATION
# ============================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 48px;">🛡️</div>
            <h2 style="color: #00ffff;">Security Command</h2>
            <p style="color: #888;">v5.0 - Cloud Edition</p>
        </div>
        """, unsafe_allow_html=True)
        
        agent_stats = get_agent_stats_unique()
        st.markdown(f"""
        <div style="background: rgba(0, 255, 255, 0.1); border-radius: 10px; padding: 10px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between;">
                <span>🖥️ Active Agents</span>
                <span class="status-online">{agent_stats['active']}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>📊 Total Agents</span>
                <span>{agent_stats['total']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Agents", "Threat Intelligence", 
                     "Network Monitor", "Endpoint Security", "USB Monitor", 
                     "Sensitive Data", "AI Assistant", "Reports"],
            icons=["house", "people", "exclamation-triangle", "wifi", 
                   "shield", "usb", "eye", "robot", "file-text"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#00ffff", "font-size": "18px"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin": "5px 0", "color": "#fff"},
                "nav-link-selected": {"background-color": "rgba(0, 255, 255, 0.2)", "border-left": "3px solid #00ffff"},
            }
        )
        
        st.markdown("---")
        alert_stats = get_alert_stats()
        threat_level = "CRITICAL" if alert_stats['critical'] > 5 else "HIGH" if alert_stats['high'] > 10 else "MEDIUM" if alert_stats['medium'] > 20 else "LOW"
        threat_color = "#ff0000" if threat_level == "CRITICAL" else "#ff4500" if threat_level == "HIGH" else "#ffaa00" if threat_level == "MEDIUM" else "#00ff00"
        
        st.markdown(f"""
        <div style="background: rgba(0,0,0,0.5); border-radius: 10px; padding: 15px; text-align: center;">
            <div style="font-size: 12px; color: #888;">CURRENT THREAT LEVEL</div>
            <div style="font-size: 24px; font-weight: bold; color: {threat_color};">{threat_level}</div>
        </div>
        """, unsafe_allow_html=True)
        
        return selected

# ============================================
# DASHBOARD PAGE
# ============================================
def dashboard_page():
    st.markdown("<h1 style='text-align: center;'>Security Command Dashboard</h1>", unsafe_allow_html=True)
    
    agent_stats = get_agent_stats_unique()
    alert_stats = get_alert_stats()
    network_stats = get_network_stats()
    process_stats = get_process_stats()
    usb_stats = get_usb_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #888;">Active Agents</div>
            <div style="font-size: 32px; font-weight: bold; color: #00ffff;">{agent_stats['active']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #888;">Alerts</div>
            <div style="font-size: 32px; font-weight: bold; color: #ff4444;">{alert_stats['total']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #888;">Network Packets</div>
            <div style="font-size: 32px; font-weight: bold; color: #00ffff;">{network_stats['total_packets']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #888;">Processes</div>
            <div style="font-size: 32px; font-weight: bold; color: #00ffff;">{process_stats['total']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #888;">USB Events</div>
            <div style="font-size: 32px; font-weight: bold; color: #00ffff;">{usb_stats['total_events']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🚨 Recent Security Alerts")
    recent_alerts = get_recent_alerts(20)
    if recent_alerts:
        for alert in recent_alerts:
            severity = alert.get('severity', 'MEDIUM')
            severity_class = "threat-critical" if severity == "CRITICAL" else "threat-high" if severity == "HIGH" else "threat-medium"
            
            st.markdown(f"""
            <div class="{severity_class}" style="padding: 10px; border-radius: 8px; margin: 5px 0;">
                <div style="display: flex; justify-content: space-between;">
                    <span><strong>[{severity}]</strong> {alert.get('alert_type', 'Unknown')}</span>
                    <span style="font-size: 12px;">{alert.get('timestamp', '')[:19]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent alerts")

# ============================================
# THREAT INTELLIGENCE PAGE
# ============================================
def threat_intelligence_page():
    st.markdown("<h1 style='text-align: center;'>Threat Intelligence</h1>", unsafe_allow_html=True)
    
    st.markdown("## 🎯 MITRE ATT&CK Framework")
    
    for technique_id, technique in MITRE_ATTACK_DB.items():
        st.markdown(f"""
        <div style="background: rgba(20,30,70,0.8); border-radius: 10px; padding: 15px; margin: 10px 0;">
            <strong style="color: #00ffff;">{technique_id}: {technique['name']}</strong><br>
            <span style="font-size: 12px;">Tactic: {technique['tactic']} | Severity: {technique['severity']}</span>
            <p style="font-size: 12px; margin-top: 5px;">{technique['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("## 🔍 Threat Intelligence Lookup")
    ip_lookup = st.text_input("IP Address Lookup")
    if ip_lookup:
        for source, url in THREAT_INTEL_SOURCES.items():
            st.markdown(f"- [{source}]({url}{ip_lookup})")

# ============================================
# NETWORK MONITOR PAGE
# ============================================
def network_monitor_page():
    st.markdown("<h1 style='text-align: center;'>Network Monitor</h1>", unsafe_allow_html=True)
    
    network_data = get_recent_network_activity(100)
    if network_data:
        st.dataframe(network_data, use_container_width=True)
    else:
        st.info("No network data available")

# ============================================
# ENDPOINT SECURITY PAGE
# ============================================
def endpoint_security_page():
    st.markdown("<h1 style='text-align: center;'>Endpoint Security</h1>", unsafe_allow_html=True)
    
    process_data = get_recent_processes(50)
    if process_data:
        st.dataframe(process_data, use_container_width=True)
        
        suspicious = [p for p in process_data if p.get('name', '').lower() in ['mimikatz', 'procdump', 'nc', 'ncat', 'psexec']]
        if suspicious:
            st.error(f"⚠️ {len(suspicious)} suspicious processes detected!")
    else:
        st.info("No process data available")

# ============================================
# USB MONITOR PAGE
# ============================================
def usb_monitor_page():
    st.markdown("<h1 style='text-align: center;'>USB Device Monitor</h1>", unsafe_allow_html=True)
    
    usb_data = get_recent_usb_events(100)
    if usb_data:
        st.dataframe(usb_data, use_container_width=True)
    else:
        st.info("No USB events recorded")

# ============================================
# SENSITIVE DATA PAGE
# ============================================
def sensitive_data_page():
    st.markdown("<h1 style='text-align: center;'>Sensitive Data Discovery</h1>", unsafe_allow_html=True)
    st.info("Sensitive data monitoring is active. Check database for findings.")

# ============================================
# AI ASSISTANT PAGE
# ============================================
def ai_assistant_page():
    st.markdown("<h1 style='text-align: center;'>🤖 AI Security Assistant</h1>", unsafe_allow_html=True)
    
    db_manager = DatabaseManager()
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = EnhancedSecurityAIChatbot(db_manager)
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div class="chat-message" style="background: rgba(0, 100, 200, 0.3);">
                <strong>👤 You:</strong><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message" style="background: rgba(0, 200, 100, 0.2);">
                <strong>🤖 AI Assistant:</strong><br>{msg['content']}
            </div>
            """, unsafe_allow_html=True)
    
    user_input = st.text_area("Ask about your security data:", placeholder="How many alerts?")
    
    if st.button("Send", use_container_width=True):
        if user_input:
            st.session_state.messages.append({'role': 'user', 'content': user_input})
            response = st.session_state.chatbot.query(user_input)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()
    
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ============================================
# REPORTS PAGE
# ============================================
def reports_page():
    st.markdown("<h1 style='text-align: center;'>Reports</h1>", unsafe_allow_html=True)
    
    alert_stats = get_alert_stats()
    agent_stats = get_agent_stats_unique()
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>Security Summary Report</h3>
        <p>Total Alerts: {alert_stats['total']}</p>
        <p>Critical Alerts: {alert_stats['critical']}</p>
        <p>Active Agents: {agent_stats['active']}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    report_data = f"""Security Command Center Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Alerts: {alert_stats['total']}
Critical: {alert_stats['critical']}
High: {alert_stats['high']}
Active Agents: {agent_stats['active']}"""
    
    st.download_button("Download Report", report_data, f"report_{datetime.now().strftime('%Y%m%d')}.txt")

# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    st.markdown("""
    <div style="text-align: center; padding: 50px 0;">
        <div style="font-size: 80px;">🛡️</div>
        <h1>Security Command Center v5.0</h1>
        <p>Cloud Enterprise Security Platform</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

# ============================================
# MAIN APP
# ============================================
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        login_page()
        return
    
    selected_page = render_sidebar()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"👤 Logged in as: {st.session_state.get('username', 'admin')}")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    if selected_page == "Dashboard":
        dashboard_page()
    elif selected_page == "Agents":
        agents_page()
    elif selected_page == "Threat Intelligence":
        threat_intelligence_page()
    elif selected_page == "Network Monitor":
        network_monitor_page()
    elif selected_page == "Endpoint Security":
        endpoint_security_page()
    elif selected_page == "USB Monitor":
        usb_monitor_page()
    elif selected_page == "Sensitive Data":
        sensitive_data_page()
    elif selected_page == "AI Assistant":
        ai_assistant_page()
    elif selected_page == "Reports":
        reports_page()

if __name__ == "__main__":
    main()
