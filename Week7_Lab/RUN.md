# RUN.md — Step-by-Step Execution Guide

## Prerequisites

- Python 3.10+
- Git
- (Optional) Snowflake account with CS5542_WEEK5 database
- (Optional) Groq API key

## Step 1: Clone and enter the lab directory

```bash
git clone https://github.com/muralikrish9/CS5542.git
cd CS5542/Week7_Lab
```

## Step 2: Set up environment

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
# or: .venv\Scripts\activate    # Windows

# Install pinned dependencies
pip install -r requirements.txt
```

## Step 3a: Run offline (no credentials needed — recommended for graders)

```bash
bash reproduce.sh
```

This sets `SNOWFLAKE_MOCK=true` automatically. All Snowflake calls return
pre-defined mock data. The agent still queries Groq unless `GROQ_API_KEY` is missing,
in which case only the smoke test runs.

**To run ONLY the smoke test (zero API calls):**
```bash
cd Week7_Lab
SNOWFLAKE_MOCK=true python tests/smoke_test.py
```

## Step 3b: Run live (real Snowflake + Groq)

```bash
cp .env.example .env
# Edit .env with your credentials
bash reproduce.sh --live
```

## Step 4: View outputs

**Artifacts** (timestamped JSON agent traces):
```bash
ls artifacts/
cat artifacts/pipeline_results.json
```

**Logs:**
```bash
cat logs/pipeline.log
```

## Expected output

```
============================================================
CS 5542 Week 7 — Reproducibility Pipeline
Mode: MOCK (offline)
============================================================

[1/5] Installing pinned dependencies...
[2/5] Running smoke test...
  All smoke tests passed ✓

[3/5] Running agent pipeline (3 benchmark queries)...
[1/3] What are the most common types of adversarial attacks...
  ✓ 3 iters | 1243ms | 892 tokens
[2/3] List the available tables...
  ✓ 2 iters | 876ms | 644 tokens
[3/3] What defense strategies are most effective...
  ✓ 4 iters | 1891ms | 1203 tokens

Summary saved → artifacts/pipeline_results.json
3/3 queries completed successfully.
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: groq` | `pip install -r requirements.txt` |
| `GROQ_API_KEY not set` | Copy `.env.example` to `.env` and fill in key |
| `Snowflake auth failed` | Use `bash reproduce.sh` (mock mode) or fix `.env` |
| Smoke test fails on `retrieve_documents` | Ensure scikit-learn is installed |

## Windows note

On Windows PowerShell, replace `bash reproduce.sh` with:
```powershell
$env:SNOWFLAKE_MOCK="true"; $env:PYTHONHASHSEED="42"; python run_pipeline.py
```
