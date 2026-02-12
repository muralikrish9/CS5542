#!/bin/bash
# Uses the specific python binary that matches the pip environment
PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "Warning: Python 3.10 binary not found at standard path. Falling back to 'python3'."
    PYTHON_BIN="python3"
fi

echo "Using Python: $PYTHON_BIN"
cd "$(dirname "$0")"
"$PYTHON_BIN" -m streamlit run app.py
