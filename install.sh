#!/bin/sh
# Convenience wrapper for install.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/install.py" "$@"
