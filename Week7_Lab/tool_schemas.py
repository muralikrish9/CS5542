"""
CS 5542 — Week 6 Lab
Tool Schemas (OpenAI function-calling format)

These schemas are consumed by the agent's LLM to decide which tool to call
and what arguments to pass.
"""

TOOL_SCHEMAS = [
    {
        "name": "query_snowflake",
        "description": (
            "Execute a read-only SQL SELECT query against the Snowflake data warehouse "
            "and return columns + rows. Use for any data retrieval from the database."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A valid Snowflake SQL SELECT statement.",
                }
            },
            "required": ["sql"],
        },
    },
    {
        "name": "retrieve_documents",
        "description": (
            "Search the cybersecurity knowledge base using TF-IDF retrieval. "
            "Returns the most relevant document snippets for a natural-language query. "
            "Use when the user asks about security concepts, attack techniques, or domain knowledge."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural-language question or search phrase.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of top results to return (1–10). Default 5.",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "compute_statistics",
        "description": (
            "Compute descriptive statistics (count, min, max, avg, stddev) for a numeric "
            "column in a Snowflake table. Optionally group by a category column. "
            "Use for analytical questions about distributions, averages, or group comparisons."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "table": {
                    "type": "string",
                    "description": "Table name (e.g. 'EVENTS' or 'CS5542_WEEK5.PUBLIC.EVENTS').",
                },
                "numeric_column": {
                    "type": "string",
                    "description": "Name of the numeric column to aggregate.",
                },
                "group_by": {
                    "type": "string",
                    "description": "Optional column name to group results by.",
                },
            },
            "required": ["table", "numeric_column"],
        },
    },
    {
        "name": "summarize_text",
        "description": (
            "Produce an extractive summary of a block of text. "
            "Use to condense long retrieved documents or query results into key points."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Input text to summarize.",
                },
                "max_sentences": {
                    "type": "integer",
                    "description": "Number of sentences to include (1–10). Default 3.",
                    "default": 3,
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "list_tables",
        "description": (
            "List all tables available in the current Snowflake database. "
            "Use when the user asks what data is available or before querying an unknown schema."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]
