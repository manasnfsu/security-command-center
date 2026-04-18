"""
System Monitor Dashboard - Streamlit Cloud
Minimal working version with hardcoded Firebase credentials
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import json
import os

# ============================================
# HARDCODED FIREBASE CREDENTIALS
# ============================================
FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": "systemmonitornative",
    "private_key_id": "461b220f696aad59dcb891d846fed04365323dbe",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDeFlQRjI5mkQnn\nitji2mkp9Kj/6bCiwK4mWhUyejYjKKqNsIsPjUkk5fqmq3OaM8YW/mjBiIKAcCCo\npp04MnP9F3/olFn3ROjxW24Y+S4yZCQLSlFdazrJRy+5s47MP7sy0mENsyI40Iyi\nJj2eRdTD3gTTZRhteBTUL010ahQDHmccw8/p8TKKg4LeOEUu88NBbdOEkemPzDbm\n22RSdAS/HZkpfGnKCDqgRxRx3YMc+Agh/2j5lyplz9UJc4lEkGlAzF2nSqG/3BBK\nAHlZWqtbJlMMgYYmw3qu1TcNfhbH+JX1jMSsfvibN+q8S5IzibM9OPXAYUGQ/+RJ\nmwd1MQUFAgMBAAECggEACRmRHZxMxBcdThzPq5FCIzNLLsaR3kQBiWts2EH5sJHH\nVexDRm0w72THqHH4rVDXGl9s8MEkgm7AZ9NWjdRDZxNswkg8h3fjXkBeJS0l9MVK\n/3YZb2J9aNHp5V9eHTBfU0MbhvGCwsveIfwUekUSOr8Azkijf5jJVwhj0WlR+JlV\nZRIrYbDMOrAPx97Adj+sJvxqeyzlqSMbidf8SKxYCU3LMO5Q3KM0xdp0a5YdjKXN\nosEDjD0P1aeAmIvw+afBDqDE7qitzYzCpZp2+zqRr/XhP2Cgs6ja59aCvfj6pzEb\nqVlf+Ujp3kS/lU3/YdIijR4+7FhQvHG5PXgnskCz4QKBgQD/NzjJOwnmPHWeIVji\n3saTeaGL42lP0KrfLf1eAQmBSBazKekdb6uY4jyfYTTIzE4+3bZlt59Ne6lPp0wV\nXIkT2jCuh3VC+x9Mc1kaG5wc1Z8H2+7gWgOeLxPRoVu1tUzYECXuB1jA3y8ddsHO\nglQ+EcoBzuQO8b0Mm/qZdrRuLwKBgQDexQtdQjUImqyLxGKHtx9765bA7oA6F8eq\nYVVuvWZg3Gnev14/3mxCTwUn+AMfOz5JmE6DZHvsatlnoow7stO49IsTFmac95dg\nNoQbVHn0/Epre6Swk6fY37c8Udlbt89Qme0x6TIepQg+dU7Yz1EBUPtn4AU6z9ZB\nw911ZCMHCwKBgQC6epEFiBvtnNOcHWWjL4ANFdySKDI03ZVcyW/OFhfp3NCpTMBG\nf+f0J6qAEjjNV2r8yGeT3x2JMgg+aVFQcnK+jLjxbYyiynbOF6JNT0s8TmKLDYp3\nZ44pMODcVXh7RuPFI9dzGu8gznLQpotp5xTC3aCqvY8p1Dx8UCRFqdSghQKBgDD/\nqEs/98hHtTIc5Qsy5TLtk8Al9YBRoLJCLHdqI22krYi4EPP9aVSAawLqk004S7AG\nVyahYHyU1/Lqluu+nsEs0LZHFBTshJg+BXq5bwXKxFe133iTUbTrKDOVUTjSSkBR\nSxHSWBrTc+fBB7G6j/e5J0MmzB+ufVMD0N80QlwXAoGBAM0YUZCjd/6e5eeBmytR\ndTMqK2BIwjOk/DuLHjyqflr17dJTCp9p4NIFqT8AL9enA4Ayd6GvHUDuqnYKRh+A\nO+ZX5UM6yygZRdm1YV/OgVCg8GiH+TdyaAn0By36Sb5WWEcUHtUEPbhHf+D1Rjj+\nYEg6TdvNat/+rdPwVdA/g5zK\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@systemmonitornative.iam.gserviceaccount.com",
    "client_id": "116040783114148590395",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40systemmonitornative.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Page config
st.set_page_config(
    page_title="System Monitor Dashboard",
    page_icon="🖥️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 10px;
        margin: 5px 0;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 10px;
        margin: 5px 0;
    }
    .alert-low {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Firebase
@st.cache_resource
def init_firebase():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CONFIG)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        return firestore.client()
    except Exception as e:
        st.warning(f"Firebase not available: {e}")
        return None

# Database connection
@st.cache_resource
def init_db():
    db_path = "system_monitor.db"
    if os.path.exists(db_path):
        return sqlite3.connect(db_path, check_same_thread=False)
    return None

def get_table_data(conn, table_name, limit=500):
    try:
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}"
        return pd.read_sql_query(query, conn)
    except:
        return pd.DataFrame()

def main():
    st.title("🖥️ System Monitor Dashboard")
    
    # Initialize
    db_conn = init_db()
    firestore_client = init_firebase()
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=80)
        st.title("Navigation")
        
        if db_conn:
            st.success("✅ SQLite Connected")
        else:
            st.error("❌ No database file")
            uploaded = st.file_uploader("Upload system_monitor.db", type=['db'])
            if uploaded:
                with open("system_monitor.db", "wb") as f:
                    f.write(uploaded.getbuffer())
                st.rerun()
        
        if firestore_client:
            st.success("✅ Firebase Connected")
        
        page = st.radio("Pages", ["Dashboard", "Alerts", "Network", "Processes", "USB/DLP"])
    
    if db_conn:
        if page == "Dashboard":
            show_dashboard(db_conn)
        elif page == "Alerts":
            show_alerts(db_conn)
        elif page == "Network":
            show_network(db_conn)
        elif page == "Processes":
            show_processes(db_conn)
        elif page == "USB/DLP":
            show_usb(db_conn)
    else:
        st.info("👈 Upload your system_monitor.db file to get started")

def show_dashboard(conn):
    st.header("📊 Overview")
    
    # Get counts
    cursor = conn.cursor()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT COUNT(*) FROM alerts")
        alert_count = cursor.fetchone()[0]
        st.metric("Total Alerts", alert_count)
    
    with col2:
        cursor.execute("SELECT COUNT(*) FROM network_packets")
        packet_count = cursor.fetchone()[0]
        st.metric("Network Packets", f"{packet_count:,}")
    
    with col3:
        cursor.execute("SELECT COUNT(DISTINCT pid) FROM processes")
        proc_count = cursor.fetchone()[0]
        st.metric("Processes", proc_count)
    
    with col4:
        cursor.execute("SELECT COUNT(*) FROM usb_devices")
        usb_count = cursor.fetchone()[0]
        st.metric("USB Events", usb_count)
    
    # Recent alerts
    st.subheader("🔔 Recent Alerts")
    alerts_df = get_table_data(conn, "alerts", limit=10)
    if not alerts_df.empty:
        for _, alert in alerts_df.iterrows():
            severity = alert.get('severity', 'LOW')
            timestamp = str(alert.get('timestamp', ''))[:19]
            alert_type = alert.get('alert_type', '')
            description = alert.get('description', '')
            
            if severity == 'HIGH':
                st.markdown(f'<div class="alert-high">⚠️ **{timestamp}** - {alert_type}<br>{description}</div>', unsafe_allow_html=True)
            elif severity == 'MEDIUM':
                st.markdown(f'<div class="alert-medium">⚡ **{timestamp}** - {alert_type}<br>{description}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-low">ℹ️ **{timestamp}** - {alert_type}<br>{description}</div>', unsafe_allow_html=True)
    else:
        st.info("No alerts")

def show_alerts(conn):
    st.header("🚨 All Alerts")
    
    severity_filter = st.selectbox("Severity", ["All", "HIGH", "MEDIUM", "LOW"])
    
    query = "SELECT * FROM alerts"
    if severity_filter != "All":
        query += f" WHERE severity = '{severity_filter}'"
    query += " ORDER BY timestamp DESC LIMIT 200"
    
    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True)

def show_network(conn):
    st.header("🌐 Network Activity")
    
    tab1, tab2 = st.tabs(["DNS Queries", "Network Threats"])
    
    with tab1:
        dns_df = get_table_data(conn, "dns_queries", limit=200)
        if not dns_df.empty:
            st.dataframe(dns_df[['timestamp', 'query_name', 'client_ip', 'entropy']], use_container_width=True)
        else:
            st.info("No DNS data")
    
    with tab2:
        threats_df = get_table_data(conn, "network_threats", limit=200)
        if not threats_df.empty:
            st.dataframe(threats_df[['timestamp', 'threat_type', 'severity', 'remote_ip', 'remote_port']], use_container_width=True)
        else:
            st.info("No threats detected")

def show_processes(conn):
    st.header("📊 Process Activity")
    
    events_df = get_table_data(conn, "process_events", limit=200)
    if not events_df.empty:
        st.dataframe(events_df[['timestamp', 'event_type', 'name', 'username']], use_container_width=True)
    else:
        st.info("No process events")

def show_usb(conn):
    st.header("💾 USB Activity")
    
    tab1, tab2 = st.tabs(["USB Devices", "File Activity"])
    
    with tab1:
        devices_df = get_table_data(conn, "usb_devices", limit=200)
        if not devices_df.empty:
            st.dataframe(devices_df[['timestamp', 'event_type', 'drive_letter', 'volume_label']], use_container_width=True)
        else:
            st.info("No USB devices")
    
    with tab2:
        files_df = get_table_data(conn, "usb_file_activity", limit=200)
        if not files_df.empty:
            st.dataframe(files_df[['timestamp', 'operation', 'file_path', 'risk_level']], use_container_width=True)
        else:
            st.info("No file activity")

if __name__ == "__main__":
    main()
