#!/bin/sh
# Shell wrapper for agent Telegram notifier
# Runs notify.py in the background so hooks never experience latency.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Find suitable python3
PYTHON_BIN=""
if [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
elif [ -n "$HOME" ] && [ -x "$HOME/miniconda3/envs/mcp_servers/bin/python" ]; then
    PYTHON_BIN="$HOME/miniconda3/envs/mcp_servers/bin/python"
elif [ -n "$HOME" ] && [ -x "$HOME/miniconda3/bin/python3" ]; then
    PYTHON_BIN="$HOME/miniconda3/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
else
    PYTHON_BIN="python3"
fi

# Run asynchronously with stdin piped
exec "$PYTHON_BIN" "$SCRIPT_DIR/notify.py" "$@"
