import os, sys, time, csv
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime

# Support both local .env and Streamlit Cloud secrets
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Pull from st.secrets if available (Streamlit Cloud), else env
def get_sf_env(key):
    try:
        return st.secrets["snowflake"].get(key) or os.getenv(key)
    except Exception:
        return os.getenv(key)

import snowflake.connector

LOG_PATH = "logs/pipeline_logs.csv"

def get_conn():
    account       = get_sf_env("SNOWFLAKE_ACCOUNT")
    user          = get_sf_env("SNOWFLAKE_USER")
    authenticator = get_sf_env("SNOWFLAKE_AUTHENTICATOR")
    token         = get_sf_env("SNOWFLAKE_TOKEN")
    password      = get_sf_env("SNOWFLAKE_PASSWORD")
    role          = get_sf_env("SNOWFLAKE_ROLE")
    warehouse     = get_sf_env("SNOWFLAKE_WAREHOUSE")
    database      = get_sf_env("SNOWFLAKE_DATABASE")
    schema        = get_sf_env("SNOWFLAKE_SCHEMA")

    kwargs = dict(account=account, user=user, warehouse=warehouse, database=database, schema=schema)
    if role:
        kwargs["role"] = role
    if authenticator and authenticator.lower() in {"programmatic_access_token", "oauth"}:
        kwargs["authenticator"] = authenticator
        kwargs["token"] = token
    else:
        kwargs["password"] = password
    return snowflake.connector.connect(**{k: v for k, v in kwargs.items() if v})

def log_event(team, user, query_name, latency_ms, rows, error=""):
    os.makedirs(os.path.dirname(LOG_PATH) if os.path.dirname(LOG_PATH) else ".", exist_ok=True)
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "team": team,
        "user": user,
        "query_name": query_name,
        "latency_ms": latency_ms,
        "rows_returned": rows,
        "error": error,
    }
    df = pd.DataFrame([row])
    header = not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0
    df.to_csv(LOG_PATH, mode="a", header=header, index=False)

def run_query(sql):
    t0 = time.time()
    conn = get_conn()
    df = pd.read_sql(sql, conn)
    conn.close()
    latency_ms = int((time.time() - t0) * 1000)
    return df, latency_ms

# ── UI ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CS 5542 — Week 5 Snowflake Dashboard", layout="wide")
st.title("CS 5542 — Week 5 · Snowflake Analytics Dashboard")
st.caption("Team Promptocalypse · AI Security Analytics Pipeline")

st.sidebar.header("Settings")
team = st.sidebar.text_input("Team name", value="Team Promptocalypse")
user = st.sidebar.text_input("Your name", value="Murali")
category = st.sidebar.text_input("Category filter (optional)", value="")
limit = st.sidebar.slider("Row limit", 10, 200, 50)

safe_cat = category.strip().replace("'", "''")
base_where = f"WHERE CATEGORY ILIKE '%{safe_cat}%'" if safe_cat else ""

QUERIES = {
    "Q1: Team × Category Stats": f"""
        SELECT TEAM, CATEGORY, COUNT(*) AS N, AVG(VALUE) AS AVG_VALUE
        FROM CS5542_WEEK5.PUBLIC.EVENTS
        {base_where}
        GROUP BY TEAM, CATEGORY
        ORDER BY N DESC
        LIMIT {limit}
    """,
    "Q2: Category Trends (last 24h)": f"""
        SELECT CATEGORY, COUNT(*) AS N_24H
        FROM CS5542_WEEK5.PUBLIC.EVENTS
        WHERE EVENT_TIME >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
        GROUP BY CATEGORY
        ORDER BY N_24H DESC
        LIMIT 20
    """,
    "Q3: User Role × Event Join": f"""
        SELECT U.TEAM, U.ROLE, E.CATEGORY, COUNT(*) AS N
        FROM CS5542_WEEK5.PUBLIC.USERS U
        JOIN CS5542_WEEK5.PUBLIC.EVENTS E ON U.TEAM = E.TEAM
        GROUP BY U.TEAM, U.ROLE, E.CATEGORY
        ORDER BY N DESC
        LIMIT {limit}
    """,
}

choice = st.selectbox("Select query", list(QUERIES.keys()))
sql = QUERIES[choice]

col1, col2 = st.columns([1, 4])
run = col1.button("▶ Run Query", type="primary")

if run:
    with st.spinner("Querying Snowflake..."):
        try:
            df, latency_ms = run_query(sql)
            log_event(team, user, choice, latency_ms, len(df))
            col2.metric("Rows returned", len(df))
            col2.metric("Latency", f"{latency_ms} ms")

            st.subheader("Results")
            st.dataframe(df, use_container_width=True)

            # Chart for Q1 and Q3
            if "N" in df.columns and "CATEGORY" in df.columns:
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X("CATEGORY:N", sort="-y"),
                    y=alt.Y("N:Q"),
                    color="TEAM:N" if "TEAM" in df.columns else alt.value("steelblue"),
                    tooltip=list(df.columns),
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.error(f"Query failed: {e}")
            log_event(team, user, choice, 0, 0, str(e))

st.divider()
st.subheader("Pipeline Logs")
if os.path.exists(LOG_PATH):
    logs = pd.read_csv(LOG_PATH)
    st.dataframe(logs.tail(20), use_container_width=True)
else:
    st.info("No logs yet — run a query above.")

st.divider()
st.markdown("""
**Pipeline:** `events.csv / users.csv` → Snowflake Internal Stage → `COPY INTO` → `CS5542_WEEK5.PUBLIC` → Streamlit Query UI → `pipeline_logs.csv`

**Extensions implemented:**
1. Enhanced monitoring fields (team, user, error) in pipeline logs
2. Interactive dashboard controls (parameterized filter + dynamic row limit)
3. Derived analytics via role × category join query
""")
