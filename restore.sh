#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================"
echo "        Antigravity 官方原版一键还原器 (macOS/Linux)"
echo "========================================================"
echo ""

if [ -f "$DIR/antigravity-zh" ]; then
    chmod +x "$DIR/antigravity-zh"
    "$DIR/antigravity-zh" restore
    exit 0
fi

if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/scripts/patcher.py" restore
elif command -v python >/dev/null 2>&1; then
    python "$DIR/scripts/patcher.py" restore
else
    echo "[!] 错误: 未检测到 Python 3 环境。"
    exit 1
fi
