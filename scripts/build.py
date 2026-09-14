#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Toolkit - Build & Packaging Script
Reads dictionary files, builds ag_localization_engine.js, generates standalone patcher.py,
and compiles antigravity-zh.exe using PyInstaller.
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
    print("  Antigravity-ZH Toolkit Builder")
    print("=" * 60)

    # 1. Check template and locales
    template_path = os.path.join(ENGINE_DIR, "engine_template.js")
    zh_path = os.path.join(LOCALES_DIR, "zh-CN.json")
    pat_path = os.path.join(LOCALES_DIR, "patterns.json")

    if not os.path.exists(template_path):
        print(f"[!] Error: Template file missing: {template_path}")
        return False

    print("[1/4] Loading locales...")
    with open(zh_path, "r", encoding="utf-8") as f:
        zh_json_str = f.read()
    with open(pat_path, "r", encoding="utf-8") as f:
        pat_json_str = f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 2. Build complete engine JS
    print("[2/4] Generating ag_localization_engine.js...")
    full_engine_js = template.replace("__TRANSLATIONS_JSON__", zh_json_str).replace("__PATTERNS_JSON__", pat_json_str)
    engine_out = os.path.join(ENGINE_DIR, "ag_localization_engine.js")
    with open(engine_out, "w", encoding="utf-8") as f:
        f.write(full_engine_js)
    print(f"      Saved {engine_out} ({len(full_engine_js)} bytes)")

    # 3. Build standalone patcher.py
    print("[3/4] Updating scripts/patcher.py with embedded engine...")
    patcher_py_path = os.path.join(SCRIPTS_DIR, "patcher.py")
    
    # Read existing patcher or template
    with open(patcher_py_path, "r", encoding="utf-8") as f:
        patcher_code = f.read()

    # Replace EMBEDDED_ENGINE_CODE assignment
    # Locate signature: EMBEDDED_ENGINE_CODE = ...
    import re
    new_embedded = json.dumps(full_engine_js, ensure_ascii=False)
    if "EMBEDDED_ENGINE_CODE =" in patcher_code:
        patcher_code = re.sub(
            r'EMBEDDED_ENGINE_CODE\s*=\s*(?:".*?"|\'.*?\'|""".*?"""|\'\'\'.*?\'\'\'|__EMBEDDED_ENGINE_PLACEHOLDER__)',
            f'EMBEDDED_ENGINE_CODE = {new_embedded}',
            patcher_code,
            flags=re.DOTALL
        )
    else:
        print("[!] Warning: EMBEDDED_ENGINE_CODE anchor not found, rewriting patcher...")

    with open(patcher_py_path, "w", encoding="utf-8") as f:
        f.write(patcher_code)
    print(f"      Saved {patcher_py_path} ({len(patcher_code)} bytes)")

    # 4. Compile with PyInstaller
    if compile_exe:
        print("[4/4] Compiling antigravity-zh.exe with PyInstaller...")
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
            patcher_py_path
        ]
        
        try:
            res = subprocess.run(cmd, check=True)
            output_exe = os.path.join(dist_dir, "antigravity-zh.exe")
            print("\n" + "=" * 60)
            print(f"  [+] Build Succeeded!")
            print(f"  [+] Executable: {output_exe}")
            print(f"  [+] Size: {os.path.getsize(output_exe)} bytes")
            print("=" * 60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] Compilation failed: {e}")
            return False
        except Exception as e:
            print(f"[!] Could not run PyInstaller: {e}")
            print("    Run 'pip install -r requirements.txt' first.")
            return False
    else:
        print("[+] Engine and patcher updated (skipping executable compilation).")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity-ZH Builder")
    parser.add_argument("--no-exe", action="store_true", help="Skip PyInstaller compilation")
    args = parser.parse_args()
    build(compile_exe=not args.no_exe)
