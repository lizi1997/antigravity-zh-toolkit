#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "========================================================"
echo "    Antigravity 官方原版一键还原器 (macOS)"
echo "========================================================"
echo ""

if [ -f "./antigravity-zh-macos-arm64" ]; then
    ./antigravity-zh-macos-arm64 restore
elif [ -f "./antigravity-zh" ]; then
    ./antigravity-zh restore
elif command -v python3 >/dev/null 2>&1; then
    python3 ./scripts/patcher.py restore
elif command -v python >/dev/null 2>&1; then
    python ./scripts/patcher.py restore
else
    echo "[!] 错误: 未检测到预编译程序或 Python 3 环境。"
    exit 1
fi

echo ""
read -p "官方版本还原完成！按回车键退出终端 (Press Enter to exit)..."
