"""
CS 5542 - Week 7 Lab: Pipeline Entry Point

Runs three benchmark queries through the agent and saves structured artifacts.
This is the single reproducible entry point invoked by reproduce.sh.
"""

import json
import os
import time
from pathlib import Path
from dataclasses import asdict

BENCHMARK_QUERIES = [
    "What are the most common types of adversarial attacks on machine learning systems?",
    "List the available tables and summarize what data is in the ATTACK_LOGS table.",
    "What defense strategies are most effective against phishing attacks based on the data?",
]


def main():
    from agent import run_agent

    results = []
    total_start = time.time()

    print(f"Running {len(BENCHMARK_QUERIES)} benchmark queries...\n")

    for i, query in enumerate(BENCHMARK_QUERIES, 1):
        print(f"[{i}/{len(BENCHMARK_QUERIES)}] {query[:70]}...")
        try:
            log = run_agent(query)
            results.append({
                "query": query,
                "answer": log.final_answer[:200],
                "iterations": log.iterations,
                "latency_ms": round(log.latency_ms),
                "total_tokens": log.total_tokens,
                "reflections": len(log.reflections),
                "status": "ok",
            })
            print(f"  ✓ {log.iterations} iters | {log.latency_ms:.0f}ms | {log.total_tokens} tokens")
        except Exception as e:
            results.append({"query": query, "status": "error", "error": str(e)})
            print(f"  ✗ ERROR: {e}")

    # Save summary artifact
    art_dir = Path("artifacts")
    art_dir.mkdir(exist_ok=True)
    summary_path = art_dir / "pipeline_results.json"
    with open(summary_path, "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_queries": len(BENCHMARK_QUERIES),
            "total_time_s": round(time.time() - total_start, 2),
            "mock_mode": os.getenv("SNOWFLAKE_MOCK", "false"),
            "results": results,
        }, f, indent=2)

    print(f"\nSummary saved → {summary_path}")
    passed = sum(1 for r in results if r["status"] == "ok")
    print(f"{passed}/{len(results)} queries completed successfully.")


if __name__ == "__main__":
    main()
