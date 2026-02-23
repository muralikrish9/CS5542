# CONTRIBUTIONS.md — Lab 5

## Team Name
Team Promptocalypse (Solo submission)

## Project Title
AI Security Analytics Pipeline (Snowflake Integration)

---

## Member: Murali Ediga (Solo — all components)

### Responsibilities
- Designed and implemented the full end-to-end Snowflake pipeline (solo submission)
- Snowflake environment setup: database, schema, warehouse, role configuration
- Data ingestion: schema design, staging, and `COPY INTO` loading for `events.csv` and `users.csv`
- Query & transformation layer: 3 analytics queries (aggregation, time-filtered, multi-table join)
- Application integration: Streamlit in Snowflake native app with parameterized filters, query selector, and Altair charts
- Monitoring & logging: `PIPELINE_LOGS` table in Snowflake capturing timestamp, team, user, query, latency, row count, and errors
- Extensions: enhanced monitoring fields, interactive dashboard controls, derived role × category join analytics
- Pipeline diagram, README, and submission documentation

### Commit Evidence
- `eb14f73` — add pipeline_logs.csv with real Snowflake query execution results
- `03e2d7d` — upgrade streamlit app with PAT auth, charts, sidebar controls
- `34d2faa` — fix requirements.txt for deployment
- `84a46f7` — Streamlit in Snowflake native app with PIPELINE_LOGS table
- `fc36d6d` — Finish CS5542 Week 5 lab package and submission docs

### Components Implemented and Tested
- `sql/01_create_schema.sql` — database, schema, EVENTS + USERS tables
- `sql/02_stage_and_load.sql` — internal stage + COPY INTO loading
- `sql/03_queries.sql` — 3 analytics queries
- `sql/04_create_streamlit.sql` — Streamlit in Snowflake deployment
- `scripts/sf_connect.py` — Snowflake connector with PAT/OAuth support
- `scripts/load_local_csv_to_stage.py` — Python ingestion script
- `app/streamlit_app.py` — Snowflake-native Streamlit dashboard
- `logs/pipeline_logs.csv` — pipeline execution log (real Snowflake runs)
- `pipeline_diagram.png` — end-to-end pipeline diagram
- `PIPELINE_LOGS` table in Snowflake — live monitoring log

### Live Dashboard
Streamlit in Snowflake: https://app.snowflake.com/streamlit/sfedu02/dcb73175/#/apps/wjwddq3xfqomayzpws35
