"""
CS 5542 — Week 6 Lab
Streamlit Agent Interface

Extends the Week 5 Snowflake dashboard with an interactive AI agent chat
powered by LLaMA 3.3 70B (Groq) with tool-calling support.
"""

from __future__ import annotations

import json
import os
import time

import streamlit as st
from dotenv import load_dotenv

from agent import run_agent, AgentLog
from tools import list_tables, query_snowflake

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="CS 5542 Week 6 — AI Agent",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 CS 5542 — Week 6 · AI Agent Analytics")
st.caption("Team Promptocalypse · Snowflake + RAG + LLaMA 3.3 70B (Groq)")

# ---------------------------------------------------------------------------
# Sidebar — configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Configuration")

    groq_key = st.text_input(
        "Groq API Key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Get a free key at console.groq.com",
    )

    st.divider()
    st.subheader("📊 Quick DB Info")
    if st.button("List Tables"):
        with st.spinner("Querying..."):
            res = list_tables()
        if res["error"]:
            st.error(res["error"])
        else:
            for t in res["tables"]:
                st.code(t)

    st.divider()
    st.subheader("💡 Example Questions")
    examples = [
        "How many events are in the database?",
        "What are the top 5 categories by event count?",
        "What is the average value per team?",
        "Explain what adversarial attacks on AI systems are.",
        "Summarize the key findings about web application security from the knowledge base.",
        "Show me statistics on the VALUE column in EVENTS grouped by CATEGORY.",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["pending_query"] = ex

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Render existing messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_steps"):
            with st.expander("🔧 Tool calls", expanded=False):
                for step in msg["tool_steps"]:
                    if step["kind"] == "tool_call":
                        st.markdown(f"**→ `{step['data']['tool']}`**")
                        st.json(step["data"]["args"])
                    elif step["kind"] == "tool_result":
                        try:
                            parsed = json.loads(step["data"]["result"])
                            st.json(parsed)
                        except Exception:
                            st.text(step["data"]["result"])

# ---------------------------------------------------------------------------
# Handle pending query from sidebar buttons
# ---------------------------------------------------------------------------

pending = st.session_state.pop("pending_query", None)

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

user_input = st.chat_input("Ask me anything about the data or cybersecurity…")
query = pending or user_input

if query:
    # Show user message
    st.session_state["messages"].append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking…"):
            if not groq_key:
                st.error("Please enter your Groq API key in the sidebar.")
                st.stop()

            t0 = time.time()
            log: AgentLog = run_agent(query, groq_api_key=groq_key)
            elapsed = time.time() - t0

        # Show final answer
        st.markdown(log.final_answer)

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("⏱ Latency", f"{log.latency_ms} ms")
        col2.metric("🔄 Iterations", log.iterations)
        col3.metric("🪙 Tokens", log.total_tokens)

        # Tool call log
        tool_steps = [s for s in log.steps if s["kind"] in ("tool_call", "tool_result")]
        if tool_steps:
            with st.expander("🔧 Tool calls", expanded=True):
                for step in tool_steps:
                    if step["kind"] == "tool_call":
                        st.markdown(f"**→ `{step['data']['tool']}`**")
                        st.json(step["data"]["args"])
                    elif step["kind"] == "tool_result":
                        try:
                            parsed = json.loads(step["data"]["result"])
                            # Pretty-print table results
                            if "rows" in parsed and parsed["rows"]:
                                import pandas as pd
                                df = pd.DataFrame(parsed["rows"], columns=parsed.get("columns", []))
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.json(parsed)
                        except Exception:
                            st.text(step["data"]["result"])

    # Store assistant message with tool steps
    st.session_state["messages"].append({
        "role": "assistant",
        "content": log.final_answer,
        "tool_steps": tool_steps,
    })

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    "**Pipeline:** `Week2 docs + Week4 RAG + Week5 Snowflake → Agent (LLaMA 3.3 70B) → Grounded Response`  \n"
    "**Tools:** `query_snowflake` · `retrieve_documents` · `compute_statistics` · "
    "`summarize_text` · `list_tables`"
)
