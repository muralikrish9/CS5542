"""
CS 5542 — Week 7 Lab
Agent Tool Definitions (with Mock Mode for reproducibility)

Set SNOWFLAKE_MOCK=true in .env to run fully offline without Snowflake credentials.
All other tools (RAG, stats, summarization) work without Snowflake.
"""

from __future__ import annotations

import os
import json
import textwrap
from typing import Any

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

_MOCK_MODE = os.getenv("SNOWFLAKE_MOCK", "false").lower() in ("true", "1", "yes")

# ---------------------------------------------------------------------------
# Mock data for offline / smoke-test runs
# ---------------------------------------------------------------------------

_MOCK_TABLES = ["ATTACK_LOGS", "THREAT_INTEL", "NETWORK_EVENTS", "VULNERABILITY_DB"]

_MOCK_QUERY_RESULT = {
    "columns": ["attack_type", "count", "severity"],
    "rows": [
        ["SQL Injection", 142, "high"],
        ["XSS", 89, "medium"],
        ["Phishing", 203, "high"],
        ["DDoS", 31, "critical"],
    ],
    "row_count": 4,
    "source": "MOCK",
}

# ---------------------------------------------------------------------------
# Snowflake connection helper
# ---------------------------------------------------------------------------

def _get_sf_conn():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator=os.getenv("SNOWFLAKE_AUTHENTICATOR", "snowflake"),
        token=os.getenv("SNOWFLAKE_TOKEN"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "CS5542_WEEK5"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        role=os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )


# ---------------------------------------------------------------------------
# Tool 1 — Query Snowflake
# ---------------------------------------------------------------------------

def query_snowflake(sql: str) -> dict[str, Any]:
    """
    Execute a read-only SQL query against the Snowflake data warehouse.
    If SNOWFLAKE_MOCK=true, returns mock data for offline reproducibility.
    """
    if _MOCK_MODE:
        return _MOCK_QUERY_RESULT

    sql = sql.strip()
    first_word = sql.split()[0].upper() if sql else ""
    if first_word not in ("SELECT", "SHOW", "DESCRIBE", "DESC", "WITH"):
        return {"columns": [], "rows": [], "row_count": 0,
                "error": "Only SELECT queries are allowed."}
    try:
        conn = _get_sf_conn()
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(200)
        rows = [list(r) for r in rows]
        cur.close()
        conn.close()
        return {"columns": columns, "rows": rows, "row_count": len(rows), "error": None}
    except Exception as exc:
        return {"columns": [], "rows": [], "row_count": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# Tool 2 — RAG Document Retrieval
# ---------------------------------------------------------------------------

def retrieve_documents(query: str, top_k: int = 5) -> dict[str, Any]:
    """
    Retrieve the most relevant cybersecurity knowledge base chunks for a query
    using TF-IDF sparse retrieval over the project document corpus.

    Args:
        query: Natural-language question or search phrase.
        top_k: Number of top results to return (1–10, default 5).

    Returns:
        dict with keys:
            - results (list[dict]): each item has 'chunk_id', 'score', 'snippet'
            - error (str | None)
    """
    top_k = max(1, min(top_k, 10))
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Week4_Lab"))
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize
        import glob, re

        data_dir = os.path.join(os.path.dirname(__file__), "..", "Week2_Lab", "project_data")
        txt_files = sorted(glob.glob(os.path.join(data_dir, "*.txt")))
        if not txt_files:
            return {"results": [], "error": "No knowledge base documents found."}

        corpus = []
        ids = []
        for fp in txt_files:
            try:
                text = open(fp, encoding="utf-8", errors="ignore").read()
                # simple sentence-level chunking
                sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 40]
                for i, sent in enumerate(sentences):
                    corpus.append(sent)
                    ids.append(f"{os.path.basename(fp)}::s{i}")
            except Exception:
                pass

        if not corpus:
            return {"results": [], "error": "Empty corpus."}

        vec = TfidfVectorizer(lowercase=True, stop_words="english")
        X = normalize(vec.fit_transform(corpus))
        q = normalize(vec.transform([query]))
        scores = (X @ q.T).toarray().ravel()
        top_idx = np.argsort(-scores)[:top_k]

        results = [
            {
                "chunk_id": ids[i],
                "score": round(float(scores[i]), 4),
                "snippet": corpus[i][:300],
            }
            for i in top_idx
        ]
        return {"results": results, "error": None}
    except Exception as exc:
        return {"results": [], "error": str(exc)}


# ---------------------------------------------------------------------------
# Tool 3 — Statistical Analytics
# ---------------------------------------------------------------------------

def compute_statistics(table: str, numeric_column: str,
                        group_by: str | None = None) -> dict[str, Any]:
    """
    Compute descriptive statistics (count, min, max, avg, stddev) for a
    numeric column in a Snowflake table, optionally grouped by a category column.

    Args:
        table: Fully-qualified or short table name (e.g. 'EVENTS' or
               'CS5542_WEEK5.PUBLIC.EVENTS').
        numeric_column: Name of the numeric column to aggregate.
        group_by: Optional column name to group results by.

    Returns:
        dict with keys:
            - columns (list[str])
            - rows (list[list])
            - row_count (int)
            - error (str | None)
    """
    if group_by:
        sql = (
            f"SELECT {group_by}, COUNT(*) AS cnt, "
            f"MIN({numeric_column}) AS min_val, MAX({numeric_column}) AS max_val, "
            f"ROUND(AVG({numeric_column}), 4) AS avg_val, "
            f"ROUND(STDDEV({numeric_column}), 4) AS stddev_val "
            f"FROM {table} GROUP BY {group_by} ORDER BY cnt DESC LIMIT 50"
        )
    else:
        sql = (
            f"SELECT COUNT(*) AS cnt, "
            f"MIN({numeric_column}) AS min_val, MAX({numeric_column}) AS max_val, "
            f"ROUND(AVG({numeric_column}), 4) AS avg_val, "
            f"ROUND(STDDEV({numeric_column}), 4) AS stddev_val "
            f"FROM {table}"
        )
    return query_snowflake(sql)


# ---------------------------------------------------------------------------
# Tool 4 — Text Summarization
# ---------------------------------------------------------------------------

def summarize_text(text: str, max_sentences: int = 3) -> dict[str, Any]:
    """
    Produce an extractive summary of a block of text by selecting the
    highest-scoring sentences using TF-IDF centroid similarity.

    Args:
        text: Input text to summarize.
        max_sentences: Number of sentences to include (1–10, default 3).

    Returns:
        dict with keys:
            - summary (str): the extracted summary
            - sentence_count (int): number of sentences in the summary
            - error (str | None)
    """
    max_sentences = max(1, min(max_sentences, 10))
    try:
        import re
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
        if not sentences:
            return {"summary": text[:500], "sentence_count": 1, "error": None}
        if len(sentences) <= max_sentences:
            return {"summary": " ".join(sentences), "sentence_count": len(sentences), "error": None}

        vec = TfidfVectorizer(stop_words="english")
        X = normalize(vec.fit_transform(sentences))
        centroid = X.mean(axis=0)
        # centroid is a matrix row; convert to array
        centroid = np.asarray(centroid).ravel()
        scores = X.dot(centroid)
        top_idx = sorted(np.argsort(-scores)[:max_sentences])
        summary = " ".join(sentences[i] for i in top_idx)
        return {"summary": summary, "sentence_count": len(top_idx), "error": None}
    except Exception as exc:
        return {"summary": "", "sentence_count": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# Tool 5 — List Available Tables
# ---------------------------------------------------------------------------

def list_tables() -> dict[str, Any]:
    """List tables. Returns mock data when SNOWFLAKE_MOCK=true."""
    if _MOCK_MODE:
        return {"tables": _MOCK_TABLES, "error": None}
    result = query_snowflake("SHOW TABLES")
    if result["error"]:
        return {"tables": [], "error": result["error"]}
    # SHOW TABLES returns 'name' as column 2 (index 1)
    try:
        name_col = next(
            (i for i, c in enumerate(result["columns"]) if c.lower() == "name"),
            1
        )
        tables = [row[name_col] for row in result["rows"]]
        return {"tables": tables, "error": None}
    except Exception as exc:
        return {"tables": [], "error": str(exc)}
