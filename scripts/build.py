#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Toolkit - Build & Packaging Script (v1.0.0)
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
    with open(patcher_py, "r", encoding="utf-8") as f:
        p_lines = f.readlines()
    
    out_lines = []
    engine_json_repr = json.dumps(full_engine_js, ensure_ascii=False)
    for line in p_lines:
        if line.startswith("EMBEDDED_ENGINE_CODE ="):
            out_lines.append(f"EMBEDDED_ENGINE_CODE = {engine_json_repr}\n")
        else:
            out_lines.append(line)

    with open(patcher_py, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    print(f"      Updated {patcher_py}")

    if compile_exe:
        print("[3/3] Compiling antigravity-zh.exe with PyInstaller...")
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
            output_exe = os.path.join(dist_dir, "antigravity-zh.exe")
            desktop_exe = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "antigravity-zh.exe")
            toolkit_exe = os.path.join(REPO_ROOT, "antigravity-zh.exe")
            if os.path.exists(output_exe):
                shutil.copy2(output_exe, desktop_exe)
                shutil.copy2(output_exe, toolkit_exe)
            print("\n" + "=" * 60)
            print(f"  [+] Build Succeeded!")
            print(f"  [+] Executable: {output_exe}")
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
