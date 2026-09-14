#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================"
echo "       Antigravity 现代化汉化一键安装器 v1.0.0 (macOS/Linux)"
echo "========================================================"
echo ""

if [ -f "$DIR/antigravity-zh-macos-arm64" ]; then
    chmod +x "$DIR/antigravity-zh-macos-arm64"
    "$DIR/antigravity-zh-macos-arm64" patch --force
    exit 0
elif [ -f "$DIR/antigravity-zh" ]; then
    chmod +x "$DIR/antigravity-zh"
    "$DIR/antigravity-zh" patch --force
    exit 0
fi

if command -v python3 >/dev/null 2>&1; then
    python3 "$DIR/scripts/patcher.py" patch --force
elif command -v python >/dev/null 2>&1; then
    python "$DIR/scripts/patcher.py" patch --force
else
    echo "[!] 错误: 未检测到 Python 3 环境或预编译二进制程序。"
    echo "    请安装 Python 3 或直接从 GitHub Releases 下载预编译程序："
    echo "    https://github.com/lizi1997/antigravity-zh-toolkit/releases"
    exit 1
fi
