"""
CS 5542 — Week 8 Lab: Integrated Agent with Dual-Model Support
Extends the Week 7 ReAct agent to support both Groq (cloud) and local LoRA model.
"""

import json
import os
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

load_dotenv()

# Import Week7 tools
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Week7_Lab"))
from tools import query_snowflake, retrieve_documents, compute_statistics, summarize_text, list_tables
from tool_schemas import TOOL_SCHEMAS


def load_config(path: str = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


@dataclass
class AgentResult:
    query: str
    answer: str
    model_backend: str
    iterations: int
    latency_ms: float
    total_tokens: int
    steps: list = field(default_factory=list)


SYSTEM_PROMPT = """You are a cybersecurity AI assistant specialized in honeypot analysis, 
threat detection, and attack classification. You have access to tools:

- query_snowflake(sql): Execute SELECT queries on Snowflake
- retrieve_documents(query): TF-IDF RAG retrieval
- compute_statistics(sql): Descriptive stats on Snowflake data
- summarize_text(text): Extractive summarization
- list_tables(): List available tables

Ground answers in data. Use tools before concluding.
When done, respond with: FINAL ANSWER: <answer>"""


class GroqBackend:
    """Cloud inference via Groq API (LLaMA 3.3 70B)."""

    def __init__(self, cfg: dict):
        from groq import Groq
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = cfg["agent"]["model"]
        self.temperature = cfg["agent"]["temperature"]
        self.seed = cfg["agent"]["seed"]

    def chat(self, messages: list, tools=None) -> dict:
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            seed=self.seed,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        return {
            "content": msg.content or "",
            "tool_calls": getattr(msg, "tool_calls", None),
            "tokens": resp.usage.total_tokens if resp.usage else 0,
        }


class LocalLoRABackend:
    """Local inference via fine-tuned LoRA model."""

    def __init__(self, cfg: dict):
        from inference import load_model, generate
        self._generate = generate
        adapter_dir = cfg.get("local_model", {}).get("adapter_dir", "adapters")
        if not os.path.isabs(adapter_dir):
            adapter_dir = os.path.join(os.path.dirname(__file__), adapter_dir)
        self.model, self.tokenizer = load_model(adapter_dir=adapter_dir)
        self.temperature = cfg.get("local_model", {}).get("temperature", 0.1)

    def chat(self, messages: list, tools=None) -> dict:
        # Flatten messages to single instruction for local model
        instruction = messages[-1]["content"] if messages else ""
        result = self._generate(
            self.model, self.tokenizer, instruction,
            temperature=self.temperature,
        )
        return {
            "content": f"FINAL ANSWER: {result['response']}",
            "tool_calls": None,
            "tokens": result["tokens_generated"],
        }


def get_backend(cfg: dict, force_backend: str = None):
    backend_name = force_backend or cfg.get("agent", {}).get("backend", "groq")
    if backend_name == "local":
        return LocalLoRABackend(cfg), "local_lora"
    else:
        return GroqBackend(cfg), "groq"


def dispatch_tool(fn: str, args: dict) -> Any:
    dispatch = {
        "query_snowflake": lambda a: query_snowflake(a["sql"]),
        "retrieve_documents": lambda a: retrieve_documents(a["query"]),
        "compute_statistics": lambda a: compute_statistics(a.get("table", ""), a.get("numeric_column", "")),
        "summarize_text": lambda a: summarize_text(a["text"]),
        "list_tables": lambda a: list_tables(),
    }
    handler = dispatch.get(fn)
    if not handler:
        return {"error": f"Unknown tool: {fn}"}
    try:
        return handler(args)
    except Exception as e:
        return {"error": str(e)}


def run_agent(query: str, config_path: str = None, force_backend: str = None) -> AgentResult:
    cfg = load_config(config_path)
    backend, backend_name = get_backend(cfg, force_backend)
    max_iter = cfg["agent"].get("max_iterations", 6)

    logging.info(f"Agent query: {query!r} | backend={backend_name}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    steps = []
    total_tokens = 0
    iterations = 0
    final_answer = ""
    start = time.perf_counter()

    for _ in range(max_iter):
        iterations += 1
        resp = backend.chat(messages, tools=TOOL_SCHEMAS if backend_name == "groq" else None)
        total_tokens += resp["tokens"]

        if resp["tool_calls"]:
            messages.append({"role": "assistant", "content": resp["content"], "tool_calls": resp["tool_calls"]})
            for tc in resp["tool_calls"]:
                fn = tc.function.name
                args = json.loads(tc.function.arguments)
                steps.append({"tool": fn, "args": args})
                result = dispatch_tool(fn, args)
                steps.append({"tool_result": fn, "result": str(result)[:500]})
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
        else:
            content = resp["content"]
            if "FINAL ANSWER:" in content:
                final_answer = content.split("FINAL ANSWER:")[-1].strip()
            else:
                final_answer = content
            break

    latency_ms = (time.perf_counter() - start) * 1000

    return AgentResult(
        query=query,
        answer=final_answer,
        model_backend=backend_name,
        iterations=iterations,
        latency_ms=round(latency_ms, 1),
        total_tokens=total_tokens,
        steps=steps,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Question for the agent")
    parser.add_argument("--backend", choices=["groq", "local"], default="groq")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    result = run_agent(args.query, config_path=args.config, force_backend=args.backend)
    print(f"\nBackend: {result.model_backend}")
    print(f"Answer: {result.answer}")
    print(f"Iterations: {result.iterations} | Latency: {result.latency_ms}ms | Tokens: {result.total_tokens}")
