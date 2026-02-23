import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import altair as alt
import time
from datetime import datetime

st.set_page_config(page_title="CS 5542 Week 5 Dashboard", layout="wide")
st.title("CS 5542 — Week 5 · Snowflake Analytics Dashboard")
st.caption("Team Promptocalypse · AI Security Analytics Pipeline")

# Get the active Snowflake session (built-in when running in Snowflake)
session = get_active_session()

st.sidebar.header("Settings")
team = st.sidebar.text_input("Team name", value="Team Promptocalypse")
user = st.sidebar.text_input("Your name", value="Murali")
category = st.sidebar.text_input("Category filter (optional)", value="")
limit = st.sidebar.slider("Row limit", 10, 200, 50)

safe_cat = category.strip().replace("'", "''")
base_where = f"WHERE CATEGORY ILIKE '%{safe_cat}%'" if safe_cat else ""

QUERIES = {
    "Q1: Team × Category Stats": f"""
        SELECT TEAM, CATEGORY, COUNT(*) AS N, ROUND(AVG(VALUE), 2) AS AVG_VALUE
        FROM CS5542_WEEK5.PUBLIC.EVENTS
        {base_where}
        GROUP BY TEAM, CATEGORY
        ORDER BY N DESC
        LIMIT {limit}
    """,
    "Q2: Category Trends (last 24h)": """
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

col1, col2, col3 = st.columns([1, 1, 4])
run = col1.button("▶ Run Query", type="primary")

if run:
    with st.spinner("Querying Snowflake..."):
        try:
            t0 = time.time()
            df = session.sql(sql).to_pandas()
            latency_ms = int((time.time() - t0) * 1000)

            # Log to pipeline_logs table
            session.sql(f"""
                INSERT INTO CS5542_WEEK5.PUBLIC.PIPELINE_LOGS
                    (TIMESTAMP, TEAM, USERNAME, QUERY_NAME, LATENCY_MS, ROWS_RETURNED, ERROR)
                VALUES (
                    CURRENT_TIMESTAMP(),
                    '{team.replace("'","''")}',
                    '{user.replace("'","''")}',
                    '{choice.replace("'","''")}',
                    {latency_ms},
                    {len(df)},
                    ''
                )
            """).collect()

            col2.metric("Rows", len(df))
            col3.metric("Latency", f"{latency_ms} ms")

            st.subheader("Results")
            st.dataframe(df, use_container_width=True)

            if "N" in df.columns and "CATEGORY" in df.columns:
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X("CATEGORY:N", sort="-y", title="Category"),
                    y=alt.Y("N:Q", title="Count"),
                    color="TEAM:N" if "TEAM" in df.columns else alt.value("steelblue"),
                    tooltip=list(df.columns),
                ).properties(height=300, title=choice)
                st.altair_chart(chart, use_container_width=True)

        except Exception as e:
            st.error(f"Query failed: {e}")

st.divider()
st.subheader("Pipeline Logs")
try:
    logs = session.sql("SELECT * FROM CS5542_WEEK5.PUBLIC.PIPELINE_LOGS ORDER BY TIMESTAMP DESC LIMIT 20").to_pandas()
    st.dataframe(logs, use_container_width=True)
except Exception:
    st.info("No logs yet — run a query above.")

st.divider()
st.markdown("""
**Pipeline:** `events.csv / users.csv` → Snowflake Stage → `COPY INTO` → `CS5542_WEEK5.PUBLIC` → Streamlit in Snowflake → `PIPELINE_LOGS`

**Extensions:** Enhanced monitoring · Parameterized filters · Role × Category join analytics
""")
