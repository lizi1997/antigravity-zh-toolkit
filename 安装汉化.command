#!/usr/bin/env bash
cd "$(dirname "$0")"

# Remove quarantine attribute and grant permissions
xattr -cr . 2>/dev/null || true
chmod +x ./antigravity-zh* 2>/dev/null || true
chmod +x ./*.sh 2>/dev/null || true

echo "========================================================"
echo "    Antigravity 现代化汉化一键安装器 (macOS)"
echo "========================================================"
echo ""

if [ -f "./antigravity-zh-macos-arm64" ]; then
    ./antigravity-zh-macos-arm64 patch
elif [ -f "./antigravity-zh" ]; then
    ./antigravity-zh patch
elif command -v python3 >/dev/null 2>&1; then
    python3 ./scripts/patcher.py patch
elif command -v python >/dev/null 2>&1; then
    python ./scripts/patcher.py patch
else
    echo "[!] 错误: 未检测到预编译程序或 Python 3 环境。"
    exit 1
fi

echo ""
echo "========================================================"
echo "  [+] 汉化安装完成！"
echo "  [+] 请在 Antigravity 中按 Cmd + Shift + N 新建窗口体验"
echo "========================================================"
echo ""
read -p "按回车键退出终端 (Press Enter to exit)..."
