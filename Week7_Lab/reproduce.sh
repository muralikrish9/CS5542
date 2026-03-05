#!/usr/bin/env bash
# CS 5542 - Week 7 Lab: Single-command reproducibility entry point
# Usage: bash reproduce.sh [--live]
#
# Default: runs in mock mode (no Snowflake required)
# With --live: uses real Snowflake credentials from .env

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LIVE_MODE=false
for arg in "$@"; do
  [[ "$arg" == "--live" ]] && LIVE_MODE=true
done

echo "============================================================"
echo "CS 5542 Week 7 — Reproducibility Pipeline"
echo "Mode: $([ "$LIVE_MODE" = true ] && echo 'LIVE (Snowflake)' || echo 'MOCK (offline)')"
echo "============================================================"
echo ""

# 1. Check Python
python --version || { echo "ERROR: Python not found."; exit 1; }

# 2. Install pinned dependencies
echo "[1/5] Installing pinned dependencies..."
pip install -r requirements.txt -q

# 3. Set environment
if [ "$LIVE_MODE" = true ]; then
  [ -f .env ] || { echo "ERROR: .env not found. Copy .env.example and fill in credentials."; exit 1; }
  export $(grep -v '^#' .env | xargs)
  export SNOWFLAKE_MOCK=false
else
  export SNOWFLAKE_MOCK=true
fi

export PYTHONHASHSEED=42
export RANDOM_SEED=42

# 4. Run smoke test
echo ""
echo "[2/5] Running smoke test..."
python tests/smoke_test.py

# 5. Run agent pipeline
echo ""
echo "[3/5] Running agent pipeline (3 benchmark queries)..."
python run_pipeline.py

# 6. Show artifacts
echo ""
echo "[4/5] Artifacts generated:"
ls -lh artifacts/ 2>/dev/null || echo "  (none)"

# 7. Show logs
echo ""
echo "[5/5] Log tail:"
tail -20 logs/pipeline.log 2>/dev/null || echo "  (no log yet)"

echo ""
echo "============================================================"
echo "Reproduction complete."
echo "============================================================"
