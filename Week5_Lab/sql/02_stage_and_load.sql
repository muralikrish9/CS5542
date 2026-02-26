-- 02_stage_and_load.sql
-- Multi-Agent AI Attack Swarm Detection — Data Loading

USE WAREHOUSE COMPUTE_WH;
USE DATABASE CS5542_WEEK5;
USE SCHEMA PUBLIC;

-- File format for CSV
CREATE OR REPLACE FILE FORMAT CS5542_CSV_FMT
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL', 'null');

-- Internal stage
CREATE OR REPLACE STAGE CS5542_STAGE
  FILE_FORMAT = CS5542_CSV_FMT;

-- Upload CSVs to stage (run via SnowSQL or Python):
--   PUT file://data/sessions.csv @CS5542_STAGE;
--   PUT file://data/commands.csv @CS5542_STAGE;

-- Load sessions (1,619 honeypot sessions: AI swarm, human, scripted bot)
COPY INTO SESSIONS
FROM @CS5542_STAGE/sessions.csv
ON_ERROR = 'CONTINUE';

-- Load commands (8,315 individual commands across all sessions)
COPY INTO COMMANDS
FROM @CS5542_STAGE/commands.csv
ON_ERROR = 'CONTINUE';
