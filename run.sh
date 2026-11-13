#!/usr/bin/env bash
# Universal launcher for Local Claude Code
# Works automatically on Bazzite, Kali Linux, Ubuntu, Debian, Arch
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "[!] python3 not found. Please install python3."
    exit 1
fi

# If on Kali/Debian and virtualenv exists, use it
if [ -f "$DIR/venv/bin/activate" ]; then
    source "$DIR/venv/bin/activate"
fi

exec python3 "$DIR/agent.py" "$@"
