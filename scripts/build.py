#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Toolkit - Build & Packaging Script (v1.0.0)
Cross-platform build utility for Windows, macOS, and Linux.
"""

import os
import sys
import json
import shutil
import argparse
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(REPO_ROOT, "locales")
ENGINE_DIR = os.path.join(REPO_ROOT, "engine")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

PATCHER_TEMPLATE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Patcher & Manager v1.0.0
Cross-Platform In-Place ASAR injection and management utility (Windows / macOS / Linux).
"""

import os
import sys
import struct
import json
import shutil
import hashlib
import subprocess
import argparse

SIGNATURE_PRELOAD = "// Antigravity Client Modern Chinese Localization Engine v1.0.0"

EMBEDDED_ENGINE_CODE = __EMBEDDED_ENGINE_PLACEHOLDER__

def get_default_install_dir():
    if sys.platform == "darwin":  # macOS
        candidates = [
            "/Applications/Antigravity.app/Contents/Resources",
            os.path.expanduser("~/Applications/Antigravity.app/Contents/Resources"),
        ]
    elif sys.platform.startswith("linux"):  # Linux
        candidates = [
            "/opt/antigravity/resources",
            "/usr/lib/antigravity/resources",
            "/usr/local/lib/antigravity/resources",
            os.path.expanduser("~/.local/share/antigravity/resources"),
        ]
    else:  # Windows
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\resources"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity"),
            os.path.expandvars(r"%PROGRAMFILES%\antigravity\resources"),
            os.path.expandvars(r"%PROGRAMFILES%\antigravity"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\antigravity\resources"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%\antigravity"),
        ]

    for c in candidates:
        if os.path.exists(os.path.join(c, "app.asar")):
            return c
        if os.path.exists(os.path.join(c, "resources", "app.asar")):
            return os.path.join(c, "resources")

    # Dynamic process detection
    if sys.platform == "win32":
        try:
            cmd = 'powershell -NoProfile -Command "(Get-Process -Name Antigravity -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path -First 1)"'
            out = subprocess.check_output(cmd, shell=True).decode("utf-8", errors="ignore").strip()
            if out and os.path.exists(out):
                candidate = os.path.join(os.path.dirname(out), "resources")
                if os.path.exists(os.path.join(candidate, "app.asar")):
                    return candidate
                if os.path.exists(os.path.join(os.path.dirname(out), "app.asar")):
                    return os.path.dirname(out)
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            cmd = "pgrep -f Antigravity.app"
            out = subprocess.check_output(cmd, shell=True).decode("utf-8", errors="ignore").strip()
            if out:
                p = "/Applications/Antigravity.app/Contents/Resources"
                if os.path.exists(os.path.join(p, "app.asar")):
                    return p
        except Exception:
            pass

    return None

def get_locales_dir():
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/Antigravity/locales")
    elif sys.platform.startswith("linux"):
        base = os.path.expanduser("~/.config/Antigravity/locales")
    else:
        base = os.path.join(os.environ.get("APPDATA", ""), "Antigravity", "locales")
    os.makedirs(base, exist_ok=True)
    return base

def is_antigravity_running():
    try:
        if sys.platform == "win32":
            res = subprocess.check_output('tasklist /FI "IMAGENAME eq Antigravity.exe"', shell=True).decode("gbk", errors="ignore")
            return "antigravity.exe" in res.lower()
        else:
            res = subprocess.check_output(["pgrep", "-i", "-f", "antigravity"]).decode("utf-8", errors="ignore")
            return len(res.strip()) > 0
    except Exception:
        return False

def read_asar(asar_path):
    with open(asar_path, "rb") as f:
        u1, u2 = struct.unpack("<II", f.read(8))
        base_offset = 8 + u2
        u3, json_len = struct.unpack("<II", f.read(8))
        header_json = f.read(json_len).decode("utf-8")
        header = json.loads(header_json)
        
        files_data = {}
        def extract_files(tree, prefix=""):
            for name, entry in tree.get("files", {}).items():
                curr = f"{prefix}/{name}" if prefix else name
                if "files" in entry:
                    extract_files(entry, curr)
                elif "size" in entry and "offset" in entry:
                    f.seek(base_offset + int(entry["offset"]))
                    files_data[curr] = f.read(entry["size"])
        extract_files(header)
    return header, files_data

def write_asar_inplace(path, header, files_data):
    current_offset = 0
    def update_entries(tree, prefix=""):
        nonlocal current_offset
        for name, entry in tree.get("files", {}).items():
            curr = f"{prefix}/{name}" if prefix else name
            if "files" in entry:
                update_entries(entry, curr)
            elif curr in files_data:
                data = files_data[curr]
                entry["size"] = len(data)
                entry["offset"] = str(current_offset)
                h = hashlib.sha256(data).hexdigest()
                entry["integrity"] = {
                    "algorithm": "SHA256",
                    "hash": h,
                    "blockSize": 4194304,
                    "blocks": [h]
                }
                current_offset += len(data)
    update_entries(header)

    json_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    json_len = len(json_bytes)
    pad_len = (4 - (json_len % 4)) % 4
    json_bytes += b'\x00' * pad_len
    padded_json_len = len(json_bytes)

    u3 = 4 + padded_json_len
    u2 = 4 + u3
    u1 = 4

    with open(path, "r+b") as f:
        f.seek(0)
        f.write(struct.pack("<IIII", u1, u2, u3, json_len))
        f.write(json_bytes)
        def write_files(tree, prefix=""):
            for name, entry in tree.get("files", {}).items():
                curr = f"{prefix}/{name}" if prefix else name
                if "files" in entry:
                    write_files(entry, curr)
                elif curr in files_data:
                    f.write(files_data[curr])
        write_files(header)
        f.truncate()

def patch_menu_js(content_str):
    replacements = [
        ("label: 'New Window'", "label: '新建窗口 (New Window)'"),
        ("label: 'Docs'", "label: '官方文档 (Docs)'"),
        ("label: updater_1.MenuUpdateStep.CheckForUpdates", "label: '检查更新 (Check for Updates)'"),
        ("addItemToSubmenu(menu, 'File'", "addItemToSubmenu(menu, '文件 (File)'"),
        ("addItemToSubmenu(menu, 'Help'", "addItemToSubmenu(menu, '帮助 (Help)'"),
    ]
    for old, new in replacements:
        if old in content_str:
            content_str = content_str.replace(old, new)
    return content_str

def apply_patch(install_dir=None, force=False):
    if not install_dir:
        install_dir = get_default_install_dir()
    if not install_dir or not os.path.exists(install_dir):
        print("[!] Error: Antigravity installation not found. Specify with --dir")
        return False
        
    asar_path = os.path.join(install_dir, "app.asar") if os.path.exists(os.path.join(install_dir, "app.asar")) else os.path.join(install_dir, "resources", "app.asar")
    bak_path = asar_path + ".bak"
    
    if not os.path.exists(asar_path):
        print(f"[!] Error: {asar_path} does not exist.")
        return False
    
    if not os.path.exists(bak_path):
        print(f"[*] Creating backup of official app.asar -> {bak_path}...")
        shutil.copy2(asar_path, bak_path)
    else:
        print(f"[*] Official backup already exists at {bak_path}")

    locales_dir = get_locales_dir()
    engine_code = EMBEDDED_ENGINE_CODE

    print("[*] Reading app.asar (using clean backup if available)...")
    source_to_read = bak_path if (os.path.exists(bak_path) and force) else asar_path
    header, files = read_asar(source_to_read)
    
    if "dist/preload.js" not in files:
        print("[!] Error: dist/preload.js not found in app.asar!")
        return False
        
    preload_str = files["dist/preload.js"].decode("utf-8")
    if SIGNATURE_PRELOAD in preload_str and not force:
        print("[*] Antigravity is already patched with Modern Localization Engine v1.0.0!")
        return True
                
    print("[*] Injecting modern localization engine into dist/preload.js...")
    new_preload = preload_str.rstrip() + "\n\n" + engine_code + "\n"
    files["dist/preload.js"] = new_preload.encode("utf-8")

    if "dist/menu.js" in files:
        print("[*] Patching native menus in dist/menu.js...")
        menu_str = files["dist/menu.js"].decode("utf-8")
        files["dist/menu.js"] = patch_menu_js(menu_str).encode("utf-8")

    print("[*] Writing patched files in-place to app.asar...")
    try:
        write_asar_inplace(asar_path, header, files)
    except Exception as e:
        print(f"[!] In-place write error: {e}")
        return False
    
    print("\n========================================================")
    print("  [+] 汉化补丁安装成功！(Patch applied successfully!)")
    print(f"  [+] 词典目录: {locales_dir}")
    print("  [+] 请按 Ctrl+Shift+N (Mac: Cmd+Shift+N) 新建窗口，或重启客户端即可查看汉化效果！")
    print("  [+] 在任何页面随时按 Ctrl+Alt+L 可复制未汉化词条！")
    print("========================================================\n")
    return True

def restore_backup(install_dir=None):
    if not install_dir:
        install_dir = get_default_install_dir()
    if not install_dir or not os.path.exists(install_dir):
        print("[!] Error: Antigravity installation not found.")
        return False
        
    asar_path = os.path.join(install_dir, "app.asar") if os.path.exists(os.path.join(install_dir, "app.asar")) else os.path.join(install_dir, "resources", "app.asar")
    bak_path = asar_path + ".bak"
    
    if not os.path.exists(bak_path):
        print(f"[!] No backup file found at {bak_path}")
        return False
        
    print("[*] Restoring original app.asar from backup...")
    try:
        header, files = read_asar(bak_path)
        write_asar_inplace(asar_path, header, files)
        print("[+] Restored official Antigravity app.asar successfully!")
        return True
    except Exception as e:
        print(f"[!] Restore failed: {e}")
        return False

def show_status(install_dir=None):
    if not install_dir:
        install_dir = get_default_install_dir()
    print("=== Antigravity Localization Status ===")
    print(f"Platform:    {sys.platform}")
    print(f"Install Dir: {install_dir}")
    if not install_dir:
        print("Status: Not installed or not found.")
        return

    asar_path = os.path.join(install_dir, "app.asar") if os.path.exists(os.path.join(install_dir, "app.asar")) else os.path.join(install_dir, "resources", "app.asar")
    bak_path = asar_path + ".bak"
    print(f"app.asar exists: {os.path.exists(asar_path)}")
    print(f"Backup exists:   {os.path.exists(bak_path)}")
    print(f"Client running:  {is_antigravity_running()}")
    
    if os.path.exists(asar_path):
        try:
            header, files = read_asar(asar_path)
            preload_str = files.get("dist/preload.js", b"").decode("utf-8", errors="ignore")
            is_patched = SIGNATURE_PRELOAD in preload_str
            print(f"Patched:         {is_patched}")
        except Exception as e:
            print(f"Error reading app.asar: {e}")

def main():
    parser = argparse.ArgumentParser(description="Antigravity Modern Chinese Localization Patcher v1.0.0")
    parser.add_argument("action", nargs="?", default="patch", choices=["patch", "restore", "status"], help="Action to perform (default: patch)")
    parser.add_argument("--dir", help="Custom Antigravity installation directory")
    parser.add_argument("--force", action="store_true", help="Force re-patching even if already patched")
    
    args = parser.parse_args()
    
    if args.action == "patch":
        apply_patch(args.dir, force=args.force)
    elif args.action == "restore":
        restore_backup(args.dir)
    elif args.action == "status":
        show_status(args.dir)

    # If running in interactive terminal on Windows without arguments, pause before exit
    if sys.platform == "win32" and len(sys.argv) <= 1:
        try:
            input("\n按回车键退出 (Press Enter to exit)...")
        except Exception:
            pass

if __name__ == "__main__":
    main()
'''

def build(compile_exe=True):
    print("=" * 60)
    print("  Antigravity-ZH Toolkit Builder (v1.0.0)")
    print("=" * 60)

    template_path = os.path.join(ENGINE_DIR, "engine_template.js")
    zh_path = os.path.join(LOCALES_DIR, "zh-CN.json")
    pat_path = os.path.join(LOCALES_DIR, "patterns.json")

    print("[1/3] Loading locales and building ag_localization_engine.js...")
    with open(zh_path, "r", encoding="utf-8") as f:
        zh_json_str = f.read()
    with open(pat_path, "r", encoding="utf-8") as f:
        pat_json_str = f.read()
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    full_engine_js = template.replace("__TRANSLATIONS_JSON__", zh_json_str).replace("__PATTERNS_JSON__", pat_json_str)
    engine_out = os.path.join(ENGINE_DIR, "ag_localization_engine.js")
    with open(engine_out, "w", encoding="utf-8") as f:
        f.write(full_engine_js)
    print(f"      Saved {engine_out} ({len(full_engine_js)} bytes)")

    print("[2/3] Embedding latest engine into scripts/patcher.py...")
    patcher_py = os.path.join(SCRIPTS_DIR, "patcher.py")
    clean_patcher_code = PATCHER_TEMPLATE.replace("__EMBEDDED_ENGINE_PLACEHOLDER__", json.dumps(full_engine_js, ensure_ascii=False))
    with open(patcher_py, "w", encoding="utf-8") as f:
        f.write(clean_patcher_code)
    print(f"      Updated {patcher_py}")

    if compile_exe:
        is_win = sys.platform == "win32"
        binary_name = "antigravity-zh.exe" if is_win else "antigravity-zh"
        print(f"[3/3] Compiling {binary_name} with PyInstaller...")
        dist_dir = os.path.join(REPO_ROOT, "dist")
        build_dir = os.path.join(REPO_ROOT, "build")
        os.makedirs(dist_dir, exist_ok=True)
        
        cmd = [
            sys.executable,
            "-m", "PyInstaller",
            "--onefile",
            "--clean",
            "--name", "antigravity-zh",
            "--distpath", dist_dir,
            "--workpath", build_dir,
            "--specpath", build_dir,
            patcher_py
        ]
        
        try:
            subprocess.run(cmd, check=True)
            output_bin = os.path.join(dist_dir, binary_name)
            
            # Sync to desktop if local environment
            desktop_candidates = [
                os.path.join(os.path.expanduser("~"), "Desktop"),
                os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop"),
            ]
            for candidate in desktop_candidates:
                if os.path.isdir(candidate):
                    try:
                        shutil.copy2(output_bin, os.path.join(candidate, binary_name))
                        break
                    except Exception:
                        pass

            try:
                shutil.copy2(output_bin, os.path.join(REPO_ROOT, binary_name))
            except Exception:
                pass

            if not is_win:
                try:
                    os.chmod(output_bin, 0o755)
                    os.chmod(os.path.join(REPO_ROOT, binary_name), 0o755)
                except Exception:
                    pass

            print("\n" + "=" * 60)
            print(f"  [+] Build Succeeded!")
            print(f"  [+] Binary: {output_bin}")
            print(f"  [+] Synced to Desktop and root.")
            print("=" * 60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] Compilation failed: {e}")
            return False
    else:
        print("[+] Engine and patcher updated (skipping executable compilation).")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity-ZH Builder v1.0.0")
    parser.add_argument("--no-exe", action="store_true", help="Skip PyInstaller compilation")
    args = parser.parse_args()
    build(compile_exe=not args.no_exe)
