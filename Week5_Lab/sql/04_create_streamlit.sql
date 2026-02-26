-- Run this in a Snowflake Worksheet to create the Streamlit app
-- Make sure you're using: CS5542_WEEK5 database, PUBLIC schema, COMPUTE_WH warehouse

CREATE OR REPLACE STREAMLIT CS5542_WEEK5.PUBLIC.LAB5_DASHBOARD
  ROOT_LOCATION = '@CS5542_WEEK5.PUBLIC.LAB5_STAGE'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = 'COMPUTE_WH'
  TITLE = 'CS 5542 Week 5 — Snowflake Analytics Dashboard';
