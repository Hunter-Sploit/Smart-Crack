#!/usr/bin/env bash
# SmartCrack Wrapper Script - runs directly using .venv
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

if [ -f "$DIR/.venv/bin/smartcrack" ]; then
    "$DIR/.venv/bin/smartcrack" "$@"
elif [ -f "$DIR/.venv/bin/python" ]; then
    "$DIR/.venv/bin/python" -m smartcrack "$@"
else
    echo "[!] .venv not found. Running installer first..."
    bash "$DIR/install.sh"
    "$DIR/.venv/bin/smartcrack" "$@"
fi
