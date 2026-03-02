"""
CS 5542 — Week 6 Lab
AI Agent Implementation

Implements a ReAct-style agent loop using the Groq API (LLaMA 3.3 70B).
The agent reasons over user questions, selects tools, and iterates until
it produces a final grounded response.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from tools import (
    query_snowflake,
    retrieve_documents,
    compute_statistics,
    summarize_text,
    list_tables,
)
from tool_schemas import TOOL_SCHEMAS

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 6          # safety cap on tool-call loops
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a data analytics and cybersecurity assistant for the CS 5542 Big Data course.
You have access to a set of tools to help answer user questions:

- query_snowflake: run SQL SELECT queries on the Snowflake database (tables: EVENTS, USERS, COMMANDS, SESSIONS, PIPELINE_LOGS)
- retrieve_documents: semantic search over a cybersecurity knowledge base
- compute_statistics: descriptive stats on any numeric Snowflake column
- summarize_text: extractive summarization of long text
- list_tables: list available Snowflake tables

## Reasoning Strategy
1. Understand what the user is asking.
2. Decide which tool(s) to call and in what order.
3. Use tool results to ground your answer — do not fabricate numbers.
4. If a tool returns an error, try a simpler variant or explain the limitation.
5. Produce a clear, concise final answer that cites the data you retrieved.

Always prefer real data from tools over general knowledge when answering analytics questions.

IMPORTANT: When calling summarize_text, the `text` argument MUST be the actual text content
returned from retrieve_documents or query_snowflake — never a placeholder string like "TODO".
Extract the snippets from the tool results and pass them directly.
"""

# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

TOOL_FN_MAP = {
    "query_snowflake": query_snowflake,
    "retrieve_documents": retrieve_documents,
    "compute_statistics": compute_statistics,
    "summarize_text": summarize_text,
    "list_tables": list_tables,
}


def _dispatch_tool(name: str, args: dict) -> str:
    """Call the named tool and return its result as a JSON string."""
    fn = TOOL_FN_MAP.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        result = fn(**args)
    except TypeError as exc:
        result = {"error": f"Bad arguments for {name}: {exc}"}
    return json.dumps(result, default=str)


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

class AgentLog:
    """Lightweight container for tracking one agent run."""

    def __init__(self, query: str):
        self.query = query
        self.steps: list[dict] = []
        self.final_answer: str = ""
        self.total_tokens: int = 0
        self.latency_ms: int = 0
        self.iterations: int = 0

    def add_step(self, kind: str, data: Any):
        self.steps.append({"kind": kind, "data": data, "ts": time.time()})


def run_agent(user_query: str, groq_api_key: str | None = None) -> AgentLog:
    """
    Run the ReAct agent loop for a given user query.

    Args:
        user_query: The user's natural-language question.
        groq_api_key: Groq API key (falls back to GROQ_API_KEY env var).

    Returns:
        AgentLog with all steps, final answer, and metadata.
    """
    log = AgentLog(user_query)
    t0 = time.time()

    api_key = groq_api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        log.final_answer = "Error: GROQ_API_KEY not configured."
        return log

    client = Groq(api_key=api_key)

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    for iteration in range(MAX_ITERATIONS):
        log.iterations = iteration + 1

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[{"type": "function", "function": s} for s in TOOL_SCHEMAS],
                tool_choice="auto",
                max_tokens=2048,
                temperature=0.2,
            )
        except Exception as exc:
            log.final_answer = f"LLM error: {exc}"
            break

        msg = response.choices[0].message
        log.total_tokens += response.usage.total_tokens if response.usage else 0

        # No tool calls → agent is done
        if not msg.tool_calls:
            log.final_answer = msg.content or ""
            log.add_step("final_answer", log.final_answer)
            break

        # Append assistant message (with tool_calls)
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        })

        # Execute each tool call
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            log.add_step("tool_call", {"tool": name, "args": args})
            result_str = _dispatch_tool(name, args)
            log.add_step("tool_result", {"tool": name, "result": result_str[:1000]})

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": name,
                "content": result_str,
            })
    else:
        # Hit max iterations without a final answer
        log.final_answer = (
            "I reached the maximum reasoning steps. "
            "Here is what I found so far — please ask a more specific question."
        )

    log.latency_ms = int((time.time() - t0) * 1000)
    return log
