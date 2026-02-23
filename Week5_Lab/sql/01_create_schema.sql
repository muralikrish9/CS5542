-- 01_create_schema.sql
-- Multi-Agent AI Attack Swarm Detection — Snowflake Schema
CREATE OR REPLACE DATABASE CS5542_WEEK5;
CREATE OR REPLACE SCHEMA CS5542_WEEK5.PUBLIC;

-- Honeypot sessions: AI swarm, human, and scripted bot attackers
CREATE OR REPLACE TABLE CS5542_WEEK5.PUBLIC.SESSIONS (
  SESSION_ID STRING,
  LABEL STRING,          -- ai_swarm | human | scripted_bot
  SOURCE STRING,         -- data collection source directory
  HOST STRING,
  PORT INT,
  START_TIME FLOAT,      -- unix timestamp
  END_TIME FLOAT,        -- unix timestamp
  COMMAND_COUNT INT
);

-- Individual commands executed within each session
CREATE OR REPLACE TABLE CS5542_WEEK5.PUBLIC.COMMANDS (
  SESSION_ID STRING,
  TIMESTAMP FLOAT,       -- unix timestamp
  COMMAND STRING,
  LATENCY FLOAT          -- seconds
);
