#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$DIR/antigravity-zh" ]; then
    chmod +x "$DIR/antigravity-zh"
    "$DIR/antigravity-zh" status
    exit 0
fi

if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/scripts/patcher.py" status
elif command -v python >/dev/null 2>&1; then
    python "$DIR/scripts/patcher.py" status
fi
