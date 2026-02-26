# CONTRIBUTIONS.md — Lab 5

## Team Name
Team Promptocalypse

## Project Title
AI Security Analytics Pipeline (Snowflake Integration)

---

## Member: Murali Ediga (Solo)
### Responsibilities
- Set up Snowflake environment (warehouse, database, schema, file format, internal stage).
- Designed and implemented ingestion pipeline (`PUT` to stage + `COPY INTO` with CSV format).
- Created schema DDL for EVENTS and USERS tables.
- Implemented 3 analytics/transformation queries (aggregation, time-filter, multi-table join).
- Built Streamlit dashboard with parameterized filters, query selection, chart output, and runtime logging.
- Pipeline monitoring via `logs/pipeline_logs.csv` with latency, row counts, and error capture.
- Created pipeline architecture diagram.
- Documentation (README, this file).

### Evidence (commits / PRs)
- Commit: `fc36d6d` — Finish CS5542 Week 5 lab package and submission docs
- Supporting commits:
  - `b9b7f54` — README cleanup and week summaries
  - `e7ca359` — root README and screenshot updates
- PRs: N/A (direct push workflow).

### Components implemented and tested
- `sql/01_create_schema.sql` — DB + table DDL
- `sql/02_stage_and_load.sql` — warehouse, file format, stage creation
- `sql/03_queries.sql` — 3 analytics queries
- `scripts/sf_connect.py` — Snowflake connector (supports password, OAuth, PAT, externalbrowser)
- `scripts/load_local_csv_to_stage.py` — CSV → stage → COPY INTO loader
- `app/streamlit_app.py` — interactive query dashboard
- `logs/pipeline_logs.csv` — pipeline execution log
- `pipeline_diagram.png` — architecture diagram

### Live execution results
- Database `CS5542_WEEK5` created, tables `EVENTS` (5 rows) and `USERS` (4 rows) loaded.
- All 3 queries executed successfully against live Snowflake warehouse.
- Ingestion latency: ~1.1s per CSV (XSMALL warehouse, cold start).
- Q2 returns 0 rows by design (event timestamps are historical, 24h filter is relative).
