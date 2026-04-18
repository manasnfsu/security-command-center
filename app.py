"""
System Monitor Dashboard - Streamlit Cloud
Displays data from the System Monitor's SQLite database and Firebase
HARDCODED FIREBASE CREDENTIALS VERSION
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json
import os
from collections import defaultdict

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

# Page configuration
st.set_page_config(
    page_title="System Monitor Dashboard",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
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
    .stButton button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = None
if 'firestore_client' not in st.session_state:
    st.session_state.firestore_client = None

# Database connection functions
@st.cache_resource
def init_db_connection():
    """Initialize SQLite database connection"""
    try:
        db_path = "system_monitor.db"
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            return conn
        return None
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

@st.cache_resource
def init_firebase():
    """Initialize Firebase with hardcoded credentials"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CONFIG)
            firebase_admin.initialize_app(cred)
            st.success("✅ Firebase connected successfully!")
            return firestore.client()
        return firestore.client()
    except Exception as e:
        st.warning(f"⚠️ Firebase connection failed: {e}")
        return None

# Data fetching functions
def get_table_names(conn):
    """Get all table names from database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def get_table_data(conn, table_name, limit=1000):
    """Fetch data from a table"""
    try:
        query = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        return pd.DataFrame()

def get_alert_summary(conn):
    """Get alert statistics"""
    cursor = conn.cursor()
    
    # Total alerts by severity
    cursor.execute("""
        SELECT severity, COUNT(*) as count 
        FROM alerts 
        GROUP BY severity
    """)
    severity_counts = dict(cursor.fetchall())
    
    # Alerts over time (last 24 hours)
    cursor.execute("""
        SELECT 
            strftime('%H:00', timestamp) as hour,
            COUNT(*) as count,
            severity
        FROM alerts 
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour, severity
        ORDER BY hour
    """)
    hourly_data = cursor.fetchall()
    
    # Recent alerts
    cursor.execute("""
        SELECT * FROM alerts 
        ORDER BY timestamp DESC 
        LIMIT 50
    """)
    recent_alerts = cursor.fetchall()
    
    # Unresolved alerts
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
    unresolved = cursor.fetchone()[0]
    
    return {
        'severity_counts': severity_counts,
        'hourly_data': hourly_data,
        'recent_alerts': recent_alerts,
        'unresolved': unresolved,
        'total': sum(severity_counts.values()) if severity_counts else 0
    }

def get_network_stats(conn):
    """Get network statistics"""
    cursor = conn.cursor()
    
    # Top DNS queries
    cursor.execute("""
        SELECT query_name, COUNT(*) as count 
        FROM dns_queries 
        GROUP BY query_name 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_dns = cursor.fetchall()
    
    # Top HTTP hosts
    cursor.execute("""
        SELECT host, COUNT(*) as count 
        FROM http_transactions 
        WHERE host IS NOT NULL
        GROUP BY host 
        ORDER BY count DESC 
        LIMIT 10
    """)
    top_http = cursor.fetchall()
    
    # Network flows summary
    cursor.execute("""
        SELECT 
            protocol,
            COUNT(*) as flow_count,
            SUM(packets) as total_packets,
            SUM(bytes) as total_bytes
        FROM network_flows
        GROUP BY protocol
    """)
    flow_summary = cursor.fetchall()
    
    # Network threats
    cursor.execute("""
        SELECT threat_type, severity, COUNT(*) as count
        FROM network_threats
        GROUP BY threat_type, severity
        ORDER BY count DESC
    """)
    threats = cursor.fetchall()
    
    return {
        'top_dns': top_dns,
        'top_http': top_http,
        'flow_summary': flow_summary,
        'threats': threats
    }

def get_process_stats(conn):
    """Get process statistics"""
    cursor = conn.cursor()
    
    # Top processes by CPU
    cursor.execute("""
        SELECT name, MAX(cpu_percent) as max_cpu, AVG(cpu_percent) as avg_cpu
        FROM processes
        WHERE cpu_percent > 0
        GROUP BY name
        ORDER BY max_cpu DESC
        LIMIT 10
    """)
    top_cpu = cursor.fetchall()
    
    # Process events summary
    cursor.execute("""
        SELECT event_type, COUNT(*) as count
        FROM process_events
        GROUP BY event_type
    """)
    events = dict(cursor.fetchall())
    
    return {
        'top_cpu': top_cpu,
        'events': events,
        'total_processes': len([p for p in cursor.execute("SELECT DISTINCT pid FROM processes")])
    }

def get_usb_stats(conn):
    """Get USB/DLP statistics"""
    cursor = conn.cursor()
    
    # USB devices
    cursor.execute("""
        SELECT event_type, COUNT(*) as count
        FROM usb_devices
        GROUP BY event_type
    """)
    device_events = dict(cursor.fetchall())
    
    # File activity by category
    cursor.execute("""
        SELECT file_category, risk_level, COUNT(*) as count
        FROM usb_file_activity
        GROUP BY file_category, risk_level
        ORDER BY count DESC
    """)
    file_activity = cursor.fetchall()
    
    # Recent file operations
    cursor.execute("""
        SELECT operation, COUNT(*) as count
        FROM usb_file_activity
        GROUP BY operation
    """)
    operations = dict(cursor.fetchall())
    
    return {
        'device_events': device_events,
        'file_activity': file_activity,
        'operations': operations,
        'total_files': cursor.execute("SELECT COUNT(*) FROM usb_file_activity").fetchone()[0]
    }

def get_hardware_summary(conn):
    """Get hardware summary"""
    cursor = conn.cursor()
    
    # CPU info
    cpu = cursor.execute("SELECT * FROM cpu_info ORDER BY timestamp DESC LIMIT 1").fetchone()
    
    # Memory info
    memory = cursor.execute("SELECT * FROM memory_info ORDER BY timestamp DESC LIMIT 1").fetchone()
    
    # Disks
    disks = cursor.execute("SELECT * FROM disks").fetchall()
    
    return {
        'cpu': cpu,
        'memory': memory,
        'disks': disks
    }

# Main dashboard
def main():
    st.title("🖥️ System Monitor Dashboard")
    st.markdown("---")
    
    # Initialize connections
    conn = init_db_connection()
    firestore_client = init_firebase()
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/security-checked--v1.png", width=80)
        st.title("System Monitor")
        
        # Database status
        if conn:
            st.success("✅ SQLite Connected")
            tables = get_table_names(conn)
            st.caption(f"Tables: {len(tables)}")
        else:
            st.error("❌ SQLite Database not found")
            st.info("Upload your `system_monitor.db` file below")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Upload system_monitor.db",
                type=['db', 'sqlite', 'sqlite3'],
                key="db_uploader"
            )
            if uploaded_file is not None:
                with open("system_monitor.db", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Database uploaded! Please refresh.")
                st.rerun()
        
        if firestore_client:
            st.success("✅ Firebase Connected")
            st.caption("Real-time sync enabled")
        else:
            st.warning("⚠️ Firebase not available")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            ["🏠 Dashboard", "🌐 Network", "📊 Processes", "🚨 Alerts", 
             "💾 USB/DLP", "🖥️ Hardware", "📦 Software", "📈 Performance"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Page routing
    if page == "🏠 Dashboard":
        show_dashboard(conn)
    elif page == "🌐 Network":
        show_network_page(conn)
    elif page == "📊 Processes":
        show_processes_page(conn)
    elif page == "🚨 Alerts":
        show_alerts_page(conn)
    elif page == "💾 USB/DLP":
        show_usb_page(conn)
    elif page == "🖥️ Hardware":
        show_hardware_page(conn)
    elif page == "📦 Software":
        show_software_page(conn)
    elif page == "📈 Performance":
        show_performance_page(conn)

def show_dashboard(conn):
    """Main dashboard view"""
    st.header("📊 System Overview")
    
    if not conn:
        st.warning("No database connection. Please upload your system_monitor.db file using the sidebar.")
        return
    
    # Get all stats
    alert_stats = get_alert_summary(conn)
    network_stats = get_network_stats(conn)
    process_stats = get_process_stats(conn)
    usb_stats = get_usb_stats(conn)
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Alerts", alert_stats['total'], 
                  delta=f"{alert_stats['unresolved']} unresolved")
    
    with col2:
        st.metric("Active Processes", process_stats.get('total_processes', 0))
    
    with col3:
        st.metric("USB File Ops", usb_stats.get('total_files', 0))
    
    with col4:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM network_packets")
        packet_count = cursor.fetchone()[0]
        st.metric("Network Packets", f"{packet_count:,}")
    
    st.markdown("---")
    
    # Alerts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 Alert Severity Distribution")
        if alert_stats['severity_counts']:
            fig = px.pie(
                values=list(alert_stats['severity_counts'].values()),
                names=list(alert_stats['severity_counts'].keys()),
                color=list(alert_stats['severity_counts'].keys()),
                color_discrete_map={'HIGH': '#f44336', 'MEDIUM': '#ff9800', 'LOW': '#4caf50'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No alerts recorded")
    
    with col2:
        st.subheader("📡 Top DNS Queries")
        if network_stats['top_dns']:
            top_dns_df = pd.DataFrame(network_stats['top_dns'], columns=['Domain', 'Queries'])
            fig = px.bar(top_dns_df, x='Domain', y='Queries', title="Most Frequent DNS Queries")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No DNS data available")
    
    # Recent alerts
    st.subheader("🔔 Recent Alerts")
    if alert_stats['recent_alerts']:
        for alert in alert_stats['recent_alerts'][:5]:
            alert_id = alert[0]
            timestamp = alert[1][:19] if alert[1] else ''
            severity = alert[2]
            alert_type = alert[3]
            description = alert[4]
            
            if severity == 'HIGH':
                st.markdown(f'<div class="alert-high">⚠️ **{timestamp}** - [{severity}] {alert_type}<br>{description}</div>', unsafe_allow_html=True)
            elif severity == 'MEDIUM':
                st.markdown(f'<div class="alert-medium">⚡ **{timestamp}** - [{severity}] {alert_type}<br>{description}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="alert-low">ℹ️ **{timestamp}** - [{severity}] {alert_type}<br>{description}</div>', unsafe_allow_html=True)
    else:
        st.info("No recent alerts")
    
    # Network threats
    if network_stats['threats']:
        st.subheader("🛡️ Network Threats Detected")
        threats_df = pd.DataFrame(network_stats['threats'], columns=['Threat Type', 'Severity', 'Count'])
        st.dataframe(threats_df, use_container_width=True)

def show_network_page(conn):
    """Network monitoring page"""
    st.header("🌐 Network Monitoring")
    
    if not conn:
        st.error("No database connection")
        return
    
    tabs = st.tabs(["DNS Queries", "HTTP Traffic", "Network Flows", "Threats"])
    
    with tabs[0]:
        st.subheader("DNS Query Log")
        dns_df = get_table_data(conn, "dns_queries", limit=500)
        if not dns_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                search = st.text_input("Search domain", key="dns_search")
            with col2:
                show_entropy = st.checkbox("Show high entropy (>4.0)", key="dns_entropy")
            
            if search:
                dns_df = dns_df[dns_df['query_name'].str.contains(search, case=False, na=False)]
            if show_entropy:
                dns_df = dns_df[dns_df['entropy'] > 4.0]
            
            st.dataframe(
                dns_df[['timestamp', 'query_name', 'client_ip', 'entropy', 'process_name']].head(100),
                use_container_width=True
            )
            
            if 'entropy' in dns_df.columns:
                fig = px.histogram(dns_df, x='entropy', nbins=50, title="DNS Query Entropy Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No DNS data")
    
    with tabs[1]:
        st.subheader("HTTP Transactions")
        http_df = get_table_data(conn, "http_transactions", limit=500)
        if not http_df.empty:
            st.dataframe(
                http_df[['timestamp', 'method', 'host', 'uri', 'status', 'process_name']].head(100),
                use_container_width=True
            )
        else:
            st.info("No HTTP data")
    
    with tabs[2]:
        st.subheader("Network Flows")
        flows_df = get_table_data(conn, "network_flows", limit=500)
        if not flows_df.empty:
            st.dataframe(
                flows_df[['first_seen', 'src_ip', 'dst_ip', 'protocol', 'packets', 'bytes', 'application']].head(100),
                use_container_width=True
            )
        else:
            st.info("No flow data")
    
    with tabs[3]:
        st.subheader("Network Threats")
        threats_df = get_table_data(conn, "network_threats", limit=500)
        if not threats_df.empty:
            st.dataframe(
                threats_df[['timestamp', 'threat_type', 'severity', 'process_name', 'remote_ip', 'remote_port', 'evidence']].head(100),
                use_container_width=True
            )
        else:
            st.info("No threats detected")

def show_processes_page(conn):
    """Process monitoring page"""
    st.header("📊 Process Monitoring")
    
    if not conn:
        st.error("No database connection")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Process Events Timeline")
        events_df = get_table_data(conn, "process_events", limit=1000)
        if not events_df.empty:
            events_df['hour'] = pd.to_datetime(events_df['timestamp']).dt.hour
            event_counts = events_df.groupby(['hour', 'event_type']).size().reset_index(name='count')
            fig = px.bar(event_counts, x='hour', y='count', color='event_type', title="Process Events by Hour")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No process events")
    
    with col2:
        st.subheader("Top Processes by CPU")
        processes_df = get_table_data(conn, "processes", limit=1000)
        if not processes_df.empty and 'cpu_percent' in processes_df.columns:
            top_cpu = processes_df.nlargest(10, 'cpu_percent')[['name', 'cpu_percent', 'memory_percent', 'username']]
            fig = px.bar(top_cpu, x='name', y='cpu_percent', title="CPU Usage by Process")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No process data")
    
    st.subheader("Recent Process Activity")
    recent_procs = get_table_data(conn, "process_events", limit=200)
    if not recent_procs.empty:
        st.dataframe(
            recent_procs[['timestamp', 'event_type', 'name', 'exe_path', 'username']].head(100),
            use_container_width=True
        )

def show_alerts_page(conn):
    """Alerts management page"""
    st.header("🚨 Security Alerts")
    
    if not conn:
        st.error("No database connection")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severity_filter = st.selectbox("Severity", ["All", "HIGH", "MEDIUM", "LOW"])
    with col2:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT source FROM alerts")
        sources = ["All"] + [row[0] for row in cursor.fetchall() if row[0]]
        source_filter = st.selectbox("Source", sources)
    with col3:
        resolved_filter = st.selectbox("Status", ["All", "Open", "Resolved"])
    
    # Get alerts
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    
    if severity_filter != "All":
        query += " AND severity = ?"
        params.append(severity_filter)
    if source_filter != "All":
        query += " AND source = ?"
        params.append(source_filter)
    if resolved_filter == "Open":
        query += " AND resolved = 0"
    elif resolved_filter == "Resolved":
        query += " AND resolved = 1"
    
    query += " ORDER BY timestamp DESC LIMIT 500"
    
    alerts_df = pd.read_sql_query(query, conn, params=params)
    
    st.write(f"Found {len(alerts_df)} alerts")
    
    # Display alerts
    for _, alert in alerts_df.iterrows():
        severity = alert['severity']
        timestamp = alert['timestamp'][:19] if alert['timestamp'] else ''
        alert_type = alert['alert_type']
        description = alert['description']
        source = alert['source']
        
        if severity == 'HIGH':
            st.markdown(f"""
            <div class="alert-high">
                <strong>[{severity}]</strong> {alert_type}<br>
                <small>{timestamp} | {source}</small><br>
                {description}
            </div>
            """, unsafe_allow_html=True)
        elif severity == 'MEDIUM':
            st.markdown(f"""
            <div class="alert-medium">
                <strong>[{severity}]</strong> {alert_type}<br>
                <small>{timestamp} | {source}</small><br>
                {description}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert-low">
                <strong>[{severity}]</strong> {alert_type}<br>
                <small>{timestamp} | {source}</small><br>
                {description}
            </div>
            """, unsafe_allow_html=True)

def show_usb_page(conn):
    """USB/DLP monitoring page"""
    st.header("💾 USB Device & DLP Monitoring")
    
    if not conn:
        st.error("No database connection")
        return
    
    tabs = st.tabs(["USB Devices", "File Activity", "Risk Analysis"])
    
    with tabs[0]:
        st.subheader("USB Device Events")
        devices_df = get_table_data(conn, "usb_devices", limit=200)
        if not devices_df.empty:
            st.dataframe(
                devices_df[['timestamp', 'event_type', 'drive_letter', 'volume_label', 'capacity_gb']],
                use_container_width=True
            )
            
            if 'timestamp' in devices_df.columns:
                devices_df['date'] = pd.to_datetime(devices_df['timestamp']).dt.date
                conn_counts = devices_df[devices_df['event_type'] == 'CONNECTED'].groupby('date').size()
                if not conn_counts.empty:
                    fig = px.line(x=conn_counts.index, y=conn_counts.values, title="USB Connections Over Time")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No USB device data")
    
    with tabs[1]:
        st.subheader("USB File Activity")
        file_activity_df = get_table_data(conn, "usb_file_activity", limit=500)
        if not file_activity_df.empty:
            st.dataframe(
                file_activity_df[['timestamp', 'operation', 'file_path', 'file_size', 'risk_level', 'file_category']].head(100),
                use_container_width=True
            )
            
            if 'operation' in file_activity_df.columns:
                op_counts = file_activity_df['operation'].value_counts()
                fig = px.pie(values=op_counts.values, names=op_counts.index, title="File Operations Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No USB file activity")
    
    with tabs[2]:
        st.subheader("Risk Level Analysis")
        file_activity_df = get_table_data(conn, "usb_file_activity", limit=1000)
        if not file_activity_df.empty and 'file_category' in file_activity_df.columns:
            risk_by_category = file_activity_df.groupby(['file_category', 'risk_level']).size().reset_index(name='count')
            fig = px.bar(risk_by_category, x='file_category', y='count', color='risk_level', 
                        title="Risk Level by File Category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for risk analysis")

def show_hardware_page(conn):
    """Hardware inventory page"""
    st.header("🖥️ Hardware Inventory")
    
    if not conn:
        st.error("No database connection")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("CPU Information")
        cpu_df = get_table_data(conn, "cpu_info", limit=1)
        if not cpu_df.empty:
            cpu = cpu_df.iloc[0]
            st.write(f"**Name:** {cpu.get('name', 'Unknown')}")
            st.write(f"**Cores:** {cpu.get('cores', 0)} physical, {cpu.get('logical_cores', 0)} logical")
            st.write(f"**Max Frequency:** {cpu.get('max_freq', 0)} MHz")
            st.write(f"**Current Usage:** {cpu.get('usage_percent', 0)}%")
        else:
            st.info("No CPU data")
    
    with col2:
        st.subheader("Memory Information")
        mem_df = get_table_data(conn, "memory_info", limit=1)
        if not mem_df.empty:
            mem = mem_df.iloc[0]
            st.write(f"**Total:** {mem.get('total', 0):.2f} GB")
            st.write(f"**Used:** {mem.get('used', 0):.2f} GB")
            st.write(f"**Available:** {mem.get('available', 0):.2f} GB")
            st.write(f"**Usage:** {mem.get('percent', 0)}%")
            
            mem_percent = mem.get('percent', 0)
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=mem_percent,
                title={'text': "Memory Usage"},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "red" if mem_percent > 90 else "orange" if mem_percent > 70 else "green"},
                       'steps': [
                           {'range': [0, 70], 'color': "lightgreen"},
                           {'range': [70, 90], 'color': "orange"},
                           {'range': [90, 100], 'color': "red"}],
                       'threshold': {'value': 90, 'color': "red"}}))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No memory data")
    
    st.subheader("Disk Drives")
    disks_df = get_table_data(conn, "disks")
    if not disks_df.empty:
        for _, disk in disks_df.iterrows():
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write(f"**{disk.get('device', 'Unknown')}**")
                st.caption(disk.get('mountpoint', ''))
            with col2:
                used_percent = disk.get('percent', 0)
                st.progress(used_percent / 100)
                st.write(f"{disk.get('used', 0):.1f} GB / {disk.get('total', 0):.1f} GB ({used_percent:.0f}% used)")
            st.markdown("---")
    else:
        st.info("No disk data")

def show_software_page(conn):
    """Software inventory page"""
    st.header("📦 Software Inventory")
    
    if not conn:
        st.error("No database connection")
        return
    
    tabs = st.tabs(["Installed Software", "Software Events"])
    
    with tabs[0]:
        st.subheader("Installed Applications")
        software_df = get_table_data(conn, "software", limit=500)
        if not software_df.empty:
            search = st.text_input("Search software", key="sw_search")
            if search:
                software_df = software_df[software_df['name'].str.contains(search, case=False, na=False)]
            
            st.dataframe(
                software_df[['name', 'version', 'publisher', 'install_date']].head(200),
                use_container_width=True
            )
            st.caption(f"Total: {len(software_df)} installed applications")
        else:
            st.info("No software data")
    
    with tabs[1]:
        st.subheader("Software Installation/Uninstallation Events")
        events_df = get_table_data(conn, "software_events", limit=500)
        if not events_df.empty:
            event_type = st.selectbox("Event Type", ["All", "INSTALLED", "UNINSTALLED", "UPDATED"], key="sw_event_type")
            if event_type != "All":
                events_df = events_df[events_df['event_type'] == event_type]
            
            st.dataframe(
                events_df[['timestamp', 'event_type', 'name', 'version', 'publisher']].head(100),
                use_container_width=True
            )
            
            if 'timestamp' in events_df.columns:
                events_df['date'] = pd.to_datetime(events_df['timestamp']).dt.date
                timeline = events_df.groupby(['date', 'event_type']).size().reset_index(name='count')
                if not timeline.empty:
                    fig = px.line(timeline, x='date', y='count', color='event_type', title="Software Events Timeline")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No software events")

def show_performance_page(conn):
    """Performance monitoring page"""
    st.header("📈 System Performance")
    
    if not conn:
        st.error("No database connection")
        return
    
    perf_df = get_table_data(conn, "performance", limit=1000)
    
    if not perf_df.empty and 'timestamp' in perf_df.columns:
        perf_df['timestamp'] = pd.to_datetime(perf_df['timestamp'])
        perf_df = perf_df.sort_values('timestamp')
        
        # CPU Usage
        st.subheader("CPU Usage Over Time")
        if 'cpu_percent' in perf_df.columns:
            fig = px.line(perf_df, x='timestamp', y='cpu_percent', title="CPU Usage %")
            fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Critical")
            fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Warning")
            st.plotly_chart(fig, use_container_width=True)
        
        # Memory Usage
        st.subheader("Memory Usage Over Time")
        if 'memory_percent' in perf_df.columns:
            fig = px.line(perf_df, x='timestamp', y='memory_percent', title="Memory Usage %")
            fig.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Critical")
            fig.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="Warning")
            st.plotly_chart(fig, use_container_width=True)
        
        # Network I/O
        if 'net_io_sent' in perf_df.columns and 'net_io_recv' in perf_df.columns:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Network Sent")
                fig = px.area(perf_df, x='timestamp', y='net_io_sent', title="Bytes Sent")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Network Received")
                fig = px.area(perf_df, x='timestamp', y='net_io_recv', title="Bytes Received")
                st.plotly_chart(fig, use_container_width=True)
        
        # Process count
        if 'processes_count' in perf_df.columns:
            st.subheader("Process Count")
            fig = px.line(perf_df, x='timestamp', y='processes_count', title="Running Processes")
            st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        st.subheader("Performance Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Avg CPU", f"{perf_df['cpu_percent'].mean():.1f}%" if 'cpu_percent' in perf_df else "N/A")
        with col2:
            st.metric("Max CPU", f"{perf_df['cpu_percent'].max():.1f}%" if 'cpu_percent' in perf_df else "N/A")
        with col3:
            st.metric("Avg Memory", f"{perf_df['memory_percent'].mean():.1f}%" if 'memory_percent' in perf_df else "N/A")
        with col4:
            st.metric("Max Memory", f"{perf_df['memory_percent'].max():.1f}%" if 'memory_percent' in perf_df else "N/A")
    else:
        st.info("No performance data available")

if __name__ == "__main__":
    main()
