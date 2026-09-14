#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================"
echo "   Antigravity-ZH Local Build Utility (macOS / Linux)"
echo "========================================================"
echo ""

if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/scripts/build.py"
elif command -v python >/dev/null 2>&1; then
    python "$DIR/scripts/build.py"
else
    echo "[!] 错误: 未找到 Python 环境。"
    exit 1
fi
