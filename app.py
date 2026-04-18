#!/usr/bin/env python3
"""
SECURITY COMMAND CENTER v5.0 - STREAMLIT CLOUD COMPATIBLE
=========================================================
Zero compilation dependencies - works on Python 3.14
"""

import streamlit as st
import sqlite3
import plotly.graph_objects as go
import requests
import json
import os
import hashlib
import re
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import warnings
from streamlit_option_menu import option_menu
import psutil

warnings.filterwarnings('ignore')

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Security Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #0f1235 100%);
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(20, 30, 70, 0.8), rgba(15, 20, 50, 0.8));
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(0, 255, 255, 0.3);
        text-align: center;
    }
    .metric-card h2 {
        color: #00ffff !important;
        font-size: 36px;
        margin: 0;
    }
    .metric-card p {
        color: #888;
        margin: 0;
        font-size: 14px;
    }
    .threat-critical {
        background: linear-gradient(135deg, #ff0000, #8b0000);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        color: white;
    }
    .threat-high {
        background: linear-gradient(135deg, #ff4500, #cc3300);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        color: white;
    }
    .threat-medium {
        background: linear-gradient(135deg, #ffaa00, #cc8800);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        color: white;
    }
    h1, h2, h3 {
        color: #00ffff !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #00ffff, #0088ff);
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .agent-card {
        background: rgba(20, 30, 70, 0.8);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(0, 255, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# OPENROUTER API
# ============================================
OPENROUTER_API_KEY = "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"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

# ============================================
# DATABASE SETUP
# ============================================
DB_PATH = "system_monitor.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  alert_type TEXT,
                  severity TEXT,
                  description TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS network_packets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  ip_src TEXT,
                  ip_dst TEXT,
                  frame_len INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS processes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  name TEXT,
                  pid INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usb_events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  device_name TEXT,
                  action TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS agent_info
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  agent_id TEXT UNIQUE,
                  hostname TEXT,
                  status TEXT,
                  last_seen TEXT)''')
    
    # Insert sample data if empty
    c.execute("SELECT COUNT(*) FROM alerts")
    if c.fetchone()[0] == 0:
        sample_alerts = [
            ("2024-01-15 10:30:00", "Port Scan", "HIGH", "Multiple port scans detected from 192.168.1.100"),
            ("2024-01-15 11:45:00", "Malware Detected", "CRITICAL", "Suspicious process mimikatz.exe found"),
            ("2024-01-15 14:20:00", "USB Insertion", "MEDIUM", "New USB device inserted"),
            ("2024-01-16 09:15:00", "Failed Login", "LOW", "Multiple failed login attempts"),
            ("2024-01-16 13:30:00", "Data Exfiltration", "CRITICAL", "Large outbound data transfer detected"),
        ]
        c.executemany("INSERT INTO alerts (timestamp, alert_type, severity, description) VALUES (?,?,?,?)", sample_alerts)
        
        sample_packets = [
            ("2024-01-15 10:30:00", "192.168.1.100", "8.8.8.8", 1500),
            ("2024-01-15 10:31:00", "192.168.1.101", "1.1.1.1", 1400),
            ("2024-01-15 10:32:00", "192.168.1.100", "8.8.4.4", 1450),
        ]
        c.executemany("INSERT INTO network_packets (timestamp, ip_src, ip_dst, frame_len) VALUES (?,?,?,?)", sample_packets)
        
        sample_agents = [
            ("agent-001", "WORKSTATION-01", "RUNNING", datetime.now().isoformat()),
            ("agent-002", "SERVER-01", "RUNNING", datetime.now().isoformat()),
            ("agent-003", "LAPTOP-01", "OFFLINE", (datetime.now() - timedelta(hours=2)).isoformat()),
        ]
        c.executemany("INSERT INTO agent_info (agent_id, hostname, status, last_seen) VALUES (?,?,?,?)", sample_agents)
    
    conn.commit()
    conn.close()

init_db()

# ============================================
# DATA FUNCTIONS
# ============================================
def get_alert_stats():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT severity, COUNT(*) as count FROM alerts GROUP BY severity", conn)
    conn.close()
    
    stats = {'total': 0, 'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for _, row in df.iterrows():
        severity = row['severity']
        count = row['count']
        stats['total'] += count
        if severity == 'CRITICAL':
            stats['critical'] = count
        elif severity == 'HIGH':
            stats['high'] = count
        elif severity == 'MEDIUM':
            stats['medium'] = count
        elif severity == 'LOW':
            stats['low'] = count
    return stats

def get_recent_alerts(limit=20):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM alerts ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_network_stats():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT COUNT(*) as count FROM network_packets", conn)
    total = df.iloc[0]['count']
    conn.close()
    return {'total_packets': total}

def get_agent_stats():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT COUNT(*) as count FROM agent_info WHERE status = 'RUNNING'", conn)
    active = df.iloc[0]['count']
    df = pd.read_sql_query("SELECT COUNT(*) as count FROM agent_info", conn)
    total = df.iloc[0]['count']
    conn.close()
    return {'active': active, 'total': total}

def get_process_stats():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT COUNT(*) as count FROM processes", conn)
    total = df.iloc[0]['count']
    conn.close()
    return {'total': total}

def get_usb_stats():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT COUNT(*) as count FROM usb_events", conn)
    total = df.iloc[0]['count']
    conn.close()
    return {'total_events': total}

# ============================================
# AI CHATBOT
# ============================================
class SecurityChatbot:
    def __init__(self):
        self.messages = []
    
    def get_system_stats(self):
        alert_stats = get_alert_stats()
        agent_stats = get_agent_stats()
        network_stats = get_network_stats()
        
        return f"""Current Security Statistics:
- Total Alerts: {alert_stats['total']}
- Critical Alerts: {alert_stats['critical']}
- High Alerts: {alert_stats['high']}
- Active Agents: {agent_stats['active']}
- Total Agents: {agent_stats['total']}
- Network Packets: {network_stats['total_packets']}"""
    
    def query(self, user_input):
        try:
            system_stats = self.get_system_stats()
            
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": f"You are a cybersecurity assistant. Here is current system data: {system_stats}"},
                    {"role": "user", "content": user_input}
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
                return self.fallback_response(user_input, system_stats)
        except Exception as e:
            return self.fallback_response(user_input, self.get_system_stats())
    
    def fallback_response(self, user_input, stats):
        return f"""Based on current security data:

{stats}

How can I assist you with your security monitoring needs?"""

# ============================================
# PAGES
# ============================================
def dashboard_page():
    st.markdown("<h1 style='text-align: center;'>Security Dashboard</h1>", unsafe_allow_html=True)
    
    alert_stats = get_alert_stats()
    agent_stats = get_agent_stats()
    network_stats = get_network_stats()
    process_stats = get_process_stats()
    usb_stats = get_usb_stats()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p>Total Alerts</p>
            <h2>{alert_stats['total']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p>Critical Alerts</p>
            <h2 style="color: #ff4444;">{alert_stats['critical']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p>Active Agents</p>
            <h2>{agent_stats['active']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <p>Network Packets</p>
            <h2>{network_stats['total_packets']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <p>USB Events</p>
            <h2>{usb_stats['total_events']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### Recent Alerts")
    
    alerts = get_recent_alerts(10)
    if len(alerts) > 0:
        for _, alert in alerts.iterrows():
            severity = alert['severity']
            severity_class = "threat-critical" if severity == "CRITICAL" else "threat-high" if severity == "HIGH" else "threat-medium"
            st.markdown(f"""
            <div class="{severity_class}">
                <strong>[{severity}]</strong> {alert['alert_type']}<br>
                <small>{alert['timestamp']}</small><br>
                {alert['description'][:100]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No alerts found")

def agents_page():
    st.markdown("<h1 style='text-align: center;'>Agent Management</h1>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM agent_info ORDER BY last_seen DESC", conn)
    conn.close()
    
    if len(df) > 0:
        for _, agent in df.iterrows():
            status_color = "#00ff00" if agent['status'] == 'RUNNING' else "#ff4444"
            st.markdown(f"""
            <div class="agent-card">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <strong>🖥️ {agent['hostname']}</strong><br>
                        <small>ID: {agent['agent_id']}</small>
                    </div>
                    <div>
                        <span style="color: {status_color};">● {agent['status']}</span><br>
                        <small>Last seen: {agent['last_seen'][:19]}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No agents registered")

def network_page():
    st.markdown("<h1 style='text-align: center;'>Network Monitor</h1>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM network_packets ORDER BY timestamp DESC LIMIT 50", conn)
    conn.close()
    
    if len(df) > 0:
        st.dataframe(df, use_container_width=True)
        
        # Simple chart
        fig = go.Figure(data=[go.Bar(x=df['timestamp'].head(10), y=df['frame_len'].head(10), marker_color='#00ffff')])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', title="Packet Sizes")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No network data available")

def threat_intel_page():
    st.markdown("<h1 style='text-align: center;'>Threat Intelligence</h1>", unsafe_allow_html=True)
    
    mitre_attacks = {
        "T1046": {"name": "Network Service Scanning", "tactic": "Discovery", "severity": "HIGH"},
        "T1003": {"name": "Credential Dumping", "tactic": "Credential Access", "severity": "CRITICAL"},
        "T1055": {"name": "Process Injection", "tactic": "Defense Evasion", "severity": "HIGH"},
        "T1486": {"name": "Ransomware", "tactic": "Impact", "severity": "CRITICAL"},
        "T1566": {"name": "Phishing", "tactic": "Initial Access", "severity": "HIGH"},
    }
    
    for tid, attack in mitre_attacks.items():
        severity_color = "#ff0000" if attack['severity'] == "CRITICAL" else "#ffaa00"
        st.markdown(f"""
        <div style="background: rgba(20,30,70,0.8); border-radius: 10px; padding: 15px; margin: 10px 0;">
            <strong style="color: #00ffff;">{tid}: {attack['name']}</strong><br>
            <span>Tactic: {attack['tactic']}</span> | <span style="color: {severity_color};">Severity: {attack['severity']}</span>
        </div>
        """, unsafe_allow_html=True)

def ai_assistant_page():
    st.markdown("<h1 style='text-align: center;'>🤖 AI Security Assistant</h1>", unsafe_allow_html=True)
    
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = SecurityChatbot()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            st.markdown(f"""
            <div style="background: rgba(0, 100, 200, 0.3); padding: 10px; border-radius: 10px; margin: 5px 0;">
                <strong>👤 You:</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: rgba(0, 200, 100, 0.2); padding: 10px; border-radius: 10px; margin: 5px 0;">
                <strong>🤖 AI:</strong> {msg['content']}
            </div>
            """, unsafe_allow_html=True)
    
    user_input = st.text_area("Ask about security:", placeholder="How many critical alerts?")
    
    if st.button("Send", use_container_width=True):
        if user_input:
            st.session_state.messages.append({'role': 'user', 'content': user_input})
            response = st.session_state.chatbot.query(user_input)
            st.session_state.messages.append({'role': 'assistant', 'content': response})
            st.rerun()

def reports_page():
    st.markdown("<h1 style='text-align: center;'>Reports</h1>", unsafe_allow_html=True)
    
    alert_stats = get_alert_stats()
    agent_stats = get_agent_stats()
    
    report = f"""Security Command Center Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

ALERT SUMMARY:
- Total Alerts: {alert_stats['total']}
- Critical: {alert_stats['critical']}
- High: {alert_stats['high']}
- Medium: {alert_stats['medium']}
- Low: {alert_stats['low']}

AGENT STATUS:
- Active Agents: {agent_stats['active']}
- Total Agents: {agent_stats['total']}

This report was generated automatically by Security Command Center.
"""
    
    st.download_button("Download Report", report, f"security_report_{datetime.now().strftime('%Y%m%d')}.txt")

# ============================================
# MAIN
# ============================================
def main():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = True  # Skip login for cloud
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <div style="font-size: 48px;">🛡️</div>
            <h2>Security Command</h2>
        </div>
        """, unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Agents", "Threat Intelligence", "Network Monitor", "AI Assistant", "Reports"],
            icons=["house", "people", "exclamation-triangle", "wifi", "robot", "file-text"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important"},
                "icon": {"color": "#00ffff"},
                "nav-link": {"color": "#fff"},
                "nav-link-selected": {"background-color": "rgba(0, 255, 255, 0.2)"},
            }
        )
    
    if selected == "Dashboard":
        dashboard_page()
    elif selected == "Agents":
        agents_page()
    elif selected == "Threat Intelligence":
        threat_intel_page()
    elif selected == "Network Monitor":
        network_page()
    elif selected == "AI Assistant":
        ai_assistant_page()
    elif selected == "Reports":
        reports_page()

if __name__ == "__main__":
    main()
