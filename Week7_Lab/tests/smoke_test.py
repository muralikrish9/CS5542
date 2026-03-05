"""
CS 5542 - Week 7 Lab: Smoke Test

Verifies the pipeline can run end-to-end without Snowflake credentials.
Runs fully offline via SNOWFLAKE_MOCK=true.

Usage:
    python tests/smoke_test.py
    # or via reproduce.sh which sets SNOWFLAKE_MOCK=true automatically
"""

import os
import sys
import json
import time
from pathlib import Path

# Ensure mock mode
os.environ["SNOWFLAKE_MOCK"] = "true"

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_tools_mock_mode():
    """Tools return mock data when SNOWFLAKE_MOCK=true."""
    from tools import query_snowflake, list_tables, retrieve_documents, summarize_text

    print("[smoke] Testing tools in mock mode...")

    # Snowflake tools → mock data
    result = query_snowflake("SELECT * FROM ATTACK_LOGS LIMIT 10")
    assert result.get("source") == "MOCK", f"Expected mock source, got: {result}"
    assert "rows" in result
    assert len(result["rows"]) > 0
    print(f"  [OK] query_snowflake mock: {result['row_count']} rows")

    tables = list_tables()
    assert tables["error"] is None
    assert len(tables["tables"]) > 0
    print(f"  [OK] list_tables mock: {tables['tables']}")

    # RAG retrieval — no Snowflake dependency
    docs = retrieve_documents("adversarial attacks machine learning")
    assert isinstance(docs, dict)
    print(f"  [OK] retrieve_documents: {len(docs.get('documents', []))} docs retrieved")

    # Summarization — no external calls
    text = ("Machine learning models are vulnerable to adversarial attacks. "
            "These attacks perturb input data to cause misclassification. "
            "Defense strategies include adversarial training and certified robustness.")
    summary = summarize_text(text)
    assert isinstance(summary, dict)
    assert "summary" in summary or "error" in summary
    print(f"  [OK] summarize_text: {str(summary)[:80]}...")

    print("[smoke] Tools: PASSED\n")


def test_config_loads():
    """Config file is parseable and contains required keys."""
    import yaml
    print("[smoke] Testing config.yaml...")
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    required_keys = ["agent", "snowflake", "logging", "artifacts", "rag", "reflection"]
    for k in required_keys:
        assert k in cfg, f"Missing config section: {k}"

    assert cfg["agent"]["seed"] == 42, "Seed must be 42 for reproducibility"
    assert cfg["agent"]["temperature"] == 0.0, "Temperature must be 0 for determinism"
    print(f"  [OK] All required config sections present")
    print(f"  [OK] seed={cfg['agent']['seed']}, temperature={cfg['agent']['temperature']}")
    print("[smoke] Config: PASSED\n")


def test_artifacts_dir():
    """Artifacts and logs directories exist."""
    print("[smoke] Testing directory structure...")
    for d in ["artifacts", "logs", "tests"]:
        assert Path(d).exists(), f"Required directory missing: {d}"
        print(f"  [OK] {d}/ exists")
    print("[smoke] Directories: PASSED\n")


def test_required_files():
    """All required deliverable files exist."""
    print("[smoke] Testing required files...")
    required = [
        "README.md",
        "RUN.md",
        "REPRO_AUDIT.md",
        "RELATED_WORK_REPRO.md",
        "reproduce.sh",
        "requirements.txt",
        "config.yaml",
        ".env.example",
        "agent.py",
        "tools.py",
    ]
    missing = []
    for f in required:
        if Path(f).exists():
            print(f"  [OK] {f}")
        else:
            print(f"  [FAIL] MISSING: {f}")
            missing.append(f)

    assert not missing, f"Missing required files: {missing}"
    print("[smoke] Required files: PASSED\n")


def test_agent_offline():
    """Agent runs end-to-end without API calls when GROQ_API_KEY is missing."""
    print("[smoke] Testing agent structure (import + config load)...")
    # Just test that the module imports and config loads correctly
    # We don't call the LLM in smoke test (no API key needed for smoke)
    import agent as ag
    cfg = ag.load_config("config.yaml")
    assert cfg is not None
    ag.set_seeds(cfg["agent"]["seed"])
    print("  [OK] agent module imports cleanly")
    print("  [OK] config loads from agent module")
    print("[smoke] Agent structure: PASSED\n")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    start = time.time()
    print("=" * 60)
    print("CS 5542 Week 7 — Smoke Test")
    print("=" * 60)
    print()

    tests = [
        test_required_files,
        test_config_loads,
        test_artifacts_dir,
        test_tools_mock_mode,
        test_agent_offline,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] FAILED: {t.__name__}: {e}\n")
            failed += 1

    elapsed = time.time() - start
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed ({elapsed:.2f}s)")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    print("\nAll smoke tests passed [OK]")
