"""
System Monitor Dashboard - Streamlit Cloud
Hardcoded Firebase credentials - Python 3.11 compatible
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
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
st.set_page_config(page_title="System Monitor", page_icon="🖥️", layout="wide")

# Custom CSS
st.markdown("""
<style>
.alert-high { background-color: #ffebee; border-left: 4px solid #f44336; padding: 10px; margin: 5px 0; }
.alert-medium { background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 5px 0; }
.alert-low { background-color: #e8f5e9; border-left: 4px solid #4caf50; padding: 10px; margin: 5px 0; }
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
    except Exception as e:
        st.warning(f"Firebase not available: {e}")
    return None

# Database connection
@st.cache_resource
def init_db():
    if os.path.exists("system_monitor.db"):
        return sqlite3.connect("system_monitor.db", check_same_thread=False)
    return None

def main():
    st.title("🖥️ System Monitor Dashboard")
    
    db = init_db()
    firebase = init_firebase()
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=80)
        
        if db:
            st.success("✅ Database connected")
        else:
            st.error("❌ No database")
            uploaded = st.file_uploader("Upload system_monitor.db", type=['db'])
            if uploaded:
                with open("system_monitor.db", "wb") as f:
                    f.write(uploaded.getbuffer())
                st.rerun()
        
        if firebase:
            st.success("✅ Firebase connected")
        
        st.markdown("---")
        page = st.radio("Pages", ["Dashboard", "Alerts", "Network", "USB"])
    
    if db:
        if page == "Dashboard":
            show_dashboard(db)
        elif page == "Alerts":
            show_alerts(db)
        elif page == "Network":
            show_network(db)
        elif page == "USB":
            show_usb(db)

def show_dashboard(conn):
    st.header("📊 Overview")
    
    cursor = conn.cursor()
    col1, col2, col3, col4 = st.columns(4)
    
    cursor.execute("SELECT COUNT(*) FROM alerts")
    with col1: st.metric("Total Alerts", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM network_packets")
    with col2: st.metric("Network Packets", f"{cursor.fetchone()[0]:,}")
    
    cursor.execute("SELECT COUNT(DISTINCT pid) FROM processes")
    with col3: st.metric("Processes", cursor.fetchone()[0])
    
    cursor.execute("SELECT COUNT(*) FROM usb_devices")
    with col4: st.metric("USB Events", cursor.fetchone()[0])
    
    # Recent alerts
    st.subheader("🔔 Recent Alerts")
    alerts = pd.read_sql_query("SELECT timestamp, severity, alert_type, description FROM alerts ORDER BY timestamp DESC LIMIT 10", conn)
    for _, alert in alerts.iterrows():
        severity = alert['severity']
        cls = "alert-high" if severity == "HIGH" else "alert-medium" if severity == "MEDIUM" else "alert-low"
        st.markdown(f'<div class="{cls}"><strong>{alert["timestamp"][:19]}</strong> - {alert["alert_type"]}<br>{alert["description"][:100]}</div>', unsafe_allow_html=True)

def show_alerts(conn):
    st.header("🚨 All Alerts")
    severity = st.selectbox("Severity", ["All", "HIGH", "MEDIUM", "LOW"])
    query = "SELECT * FROM alerts"
    if severity != "All":
        query += f" WHERE severity = '{severity}'"
    query += " ORDER BY timestamp DESC LIMIT 200"
    df = pd.read_sql_query(query, conn)
    st.dataframe(df, use_container_width=True)

def show_network(conn):
    st.header("🌐 Network Activity")
    tab1, tab2 = st.tabs(["DNS Queries", "Threats"])
    with tab1:
        df = pd.read_sql_query("SELECT timestamp, query_name, entropy FROM dns_queries ORDER BY timestamp DESC LIMIT 200", conn)
        st.dataframe(df, use_container_width=True)
    with tab2:
        df = pd.read_sql_query("SELECT timestamp, threat_type, severity, remote_ip FROM network_threats ORDER BY timestamp DESC LIMIT 200", conn)
        st.dataframe(df, use_container_width=True)

def show_usb(conn):
    st.header("💾 USB Activity")
    tab1, tab2 = st.tabs(["Devices", "Files"])
    with tab1:
        df = pd.read_sql_query("SELECT timestamp, event_type, drive_letter FROM usb_devices ORDER BY timestamp DESC LIMIT 200", conn)
        st.dataframe(df, use_container_width=True)
    with tab2:
        df = pd.read_sql_query("SELECT timestamp, operation, file_path, risk_level FROM usb_file_activity ORDER BY timestamp DESC LIMIT 200", conn)
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
