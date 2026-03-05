# REPRO_AUDIT.md — Reproducibility Audit

## Checklist

### Environment & Dependencies
- [x] `requirements.txt` pins exact versions (no `>=` ranges)
- [x] Python version documented (3.10.0)
- [x] Virtual environment instructions in RUN.md
- [x] `.env.example` provided; `.env` never committed (in `.gitignore`)

### Determinism
- [x] LLM temperature fixed at `0.0` in `config.yaml`
- [x] LLM seed fixed at `42` in `config.yaml` and passed to Groq API
- [x] `PYTHONHASHSEED=42` set in `reproduce.sh`
- [x] `numpy.random.seed(42)` and `random.seed(42)` called in `set_seeds()`
- [ ] LLM output is stochastic by nature — identical tokens not guaranteed across API versions

### Single-Command Execution
- [x] `bash reproduce.sh` runs the full pipeline end-to-end
- [x] Mock mode enabled by default (no credentials required)
- [x] `--live` flag for real Snowflake execution
- [x] Windows fallback documented in RUN.md

### Config-Driven Execution
- [x] All runtime parameters in `config.yaml` (model, seed, temperature, max_iterations, paths)
- [x] No hardcoded magic numbers in `agent.py` or `tools.py`
- [x] Config snapshot saved in every artifact JSON

### Artifact Generation
- [x] `artifacts/` directory created automatically
- [x] Every run saves a timestamped JSON trace (`agent_trace_<timestamp>.json`)
- [x] Pipeline summary saved to `artifacts/pipeline_results.json`
- [x] Artifacts include: query, answer, iterations, latency, tokens, reflection count, config snapshot

### Logging
- [x] `logs/` directory created automatically
- [x] Structured log written to `logs/pipeline.log`
- [x] Log includes timestamps, log level, tool calls, reflection status

### Smoke Test
- [x] `tests/smoke_test.py` runs fully offline (no API keys needed)
- [x] Tests: required files, config keys, directory structure, tool mock mode, agent import
- [x] Exits with code 1 on failure (CI-compatible)
- [x] Runs in < 5 seconds

### Offline Mode
- [x] `SNOWFLAKE_MOCK=true` bypasses all Snowflake connections
- [x] Mock data is deterministic and representative
- [x] `retrieve_documents`, `summarize_text` work without any credentials

---

## Known Limitations

| Issue | Impact | Mitigation |
|-------|--------|------------|
| LLM output non-determinism | Minor answer variation across API versions | temperature=0, seed=42 minimize variance |
| Snowflake PAT expiry | Live mode requires fresh PAT | Mock mode covers offline reproducibility |
| Groq model deprecation | `llama-3.3-70b-versatile` may be renamed | Config-driven model name; change one line |
| No Docker container | Harder cross-machine reproduction | Bonus task for future work |

---

## Reproduction Evidence

Smoke test output (offline mode):
```
============================================================
CS 5542 Week 7 — Smoke Test
============================================================

[smoke] Testing required files...
  ✓ README.md  ✓ RUN.md  ✓ REPRO_AUDIT.md  ✓ RELATED_WORK_REPRO.md
  ✓ reproduce.sh  ✓ requirements.txt  ✓ config.yaml  ✓ .env.example
  ✓ agent.py  ✓ tools.py
[smoke] Required files: PASSED

[smoke] Testing config.yaml...
  ✓ All required config sections present
  ✓ seed=42, temperature=0.0
[smoke] Config: PASSED

[smoke] Testing directory structure...
  ✓ artifacts/  ✓ logs/  ✓ tests/
[smoke] Directories: PASSED

[smoke] Testing tools in mock mode...
  ✓ query_snowflake mock: 4 rows
  ✓ list_tables mock: ['ATTACK_LOGS', 'THREAT_INTEL', 'NETWORK_EVENTS', 'VULNERABILITY_DB']
  ✓ retrieve_documents: docs retrieved
  ✓ summarize_text: ...
[smoke] Tools: PASSED

Results: 5 passed, 0 failed
All smoke tests passed ✓
```
