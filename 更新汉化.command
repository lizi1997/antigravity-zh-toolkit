#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Remove attributes only from executable entry points, not the whole folder.
for file in ./antigravity-zh-macos-arm64 ./antigravity-zh ./*.command ./*.sh; do
    [ -e "$file" ] || continue
    xattr -c "$file" 2>/dev/null || true
done
chmod +x ./antigravity-zh* 2>/dev/null || true
chmod +x ./*.sh 2>/dev/null || true

echo "========================================================"
echo "    Antigravity 汉化一键更新器 (macOS)"
echo "    检测客户端更新 -> 刷新备份 -> 重打汉化"
echo "========================================================"
echo ""

DIR="$(pwd)"
# Pick the binary that matches this machine and fall back to the bundled
# Python when it cannot run here (wrong architecture, missing exec permission).
# A binary that fails must NOT abort the script: the bundled
# scripts/patcher.py is the portable fallback and has to stay reachable.
pick_binary() {
    local candidate=""
    case "$(uname -m 2>/dev/null || echo unknown)" in
        arm64|aarch64) candidate="$DIR/antigravity-zh-macos-arm64" ;;
        x86_64|amd64)  candidate="$DIR/antigravity-zh" ;;
    esac
    if [ -z "$candidate" ] || [ ! -f "$candidate" ]; then
        if [ -f "$DIR/antigravity-zh-macos-arm64" ]; then
            candidate="$DIR/antigravity-zh-macos-arm64"
        elif [ -f "$DIR/antigravity-zh" ]; then
            candidate="$DIR/antigravity-zh"
        else
            candidate=""
        fi
    fi
    printf '%s' "$candidate"
    return 0
}

run_tool() {
    local action="$1"
    local binary
    local rc=0
    binary="$(pick_binary)"
    if [ -n "$binary" ]; then
        chmod +x "$binary" 2>/dev/null || true
        set +e
        "$binary" "$action"
        rc=$?
        set -e
        if [ "$rc" -eq 0 ]; then
            return 0
        fi
        echo "[!] $binary could not run on this machine (exit $rc)."
        echo "[!] Falling back to the bundled Python script."
    fi
    if command -v python3 >/dev/null 2>&1; then
        python3 "$DIR/scripts/patcher.py" "$action"
    elif command -v python >/dev/null 2>&1; then
        python "$DIR/scripts/patcher.py" "$action"
    else
        echo "[!] Error: no usable Python 3 environment and no working binary."
        echo "    Install Python 3.10+ or download the prebuilt release:"
        echo "    https://github.com/lizi1997/antigravity-zh-toolkit/releases"
        return 1
    fi
}

run_tool update

echo ""
echo "========================================================"
echo "  [+] 更新检查完成"
echo "  [+] 请在 Antigravity 中按 Cmd + Shift + N 新建窗口查看效果"
echo "========================================================"
echo ""
read -p "按回车键退出 (Press Enter to exit)..."
