#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Untranslated String Extractor
Extracts candidate UI strings from language_server and app.asar,
compares with existing zh-CN.json, and outputs missing entries.
"""

import os
import sys
import re
import json
import argparse

def is_valid_ui_string(s):
    s = s.strip()
    if len(s) < 3 or len(s) > 200:
        return False
    # Must contain at least one English letter
    if not re.search(r'[a-zA-Z]', s):
        return False
    # Skip Chinese characters
    if re.search(r'[\u4e00-\u9fa5]', s):
        return False
    # Skip file paths, urls, code identifiers
    if s.startswith(('http://', 'https://', '/', '\\', './', '../', '@', '#')):
        return False
    if re.search(r'\.(js|ts|json|py|exe|dll|asar|css|html|png|jpg|svg|go)$', s, re.IGNORECASE):
        return False
    if re.match(r'^[a-z0-9_\-]+$', s): # snake_case or kebab-case identifier
        return False
    if re.match(r'^[0-9\s:._\-/\+$,#&\'"\[\]{}()\\<>=!*?|`@]+$', s):
        return False
    # Must have space or start with Capital letter or camelCase with multiple words
    if ' ' not in s and not (s[0].isupper() and any(c.islower() for c in s)):
        return False
    return True

def extract_from_binary(bin_path):
    print(f"[*] Scanning binary: {bin_path}...")
    strings = set()
    pattern = re.compile(rb'[\x20-\x7e]{3,200}')
    with open(bin_path, "rb") as f:
        # Read in 16MB chunks with 1KB overlap
        chunk_size = 16 * 1024 * 1024
        prev = b""
        while True:
            chunk = f.read(chunk_size)
            if not chunk: break
            data = prev + chunk
            prev = data[-1024:]
            for m in pattern.finditer(data):
                try:
                    s = m.group().decode('utf-8', errors='ignore')
                    if is_valid_ui_string(s):
                        strings.add(s.strip())
                except Exception:
                    pass
    print(f"[*] Found {len(strings)} raw candidate strings in {os.path.basename(bin_path)}")
    return strings

def run_extraction(output_file=None, custom_dir=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    toolkit_dir = os.path.abspath(os.path.join(script_dir, ".."))
    locales_file = os.path.join(toolkit_dir, "locales", "zh-CN.json")

    existing_dict = {}
    if os.path.exists(locales_file):
        with open(locales_file, "r", encoding="utf-8") as f:
            existing_dict = json.load(f)
    print(f"[*] Loaded existing dictionary: {len(existing_dict)} entries")
    lower_existing = {k.lower().strip(): v for k, v in existing_dict.items()}

    install_dir = custom_dir or os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity")
    targets = [
        os.path.join(install_dir, "resources", "bin", "language_server.exe"),
        os.path.join(install_dir, "resources", "app.asar"),
    ]

    all_candidates = set()
    for t in targets:
        if os.path.exists(t):
            all_candidates.update(extract_from_binary(t))

    missing = {}
    for s in sorted(all_candidates):
        lower_s = s.lower().strip()
        if lower_s not in lower_existing and s not in existing_dict:
            missing[s] = ""

    print(f"[+] Total missing untranslated candidate strings: {len(missing)}")

    out_path = output_file or os.path.join(toolkit_dir, "locales", "missing_strings.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)

    print(f"[+] Saved missing candidates to: {out_path}")
    return missing

def main():
    parser = argparse.ArgumentParser(description="Extract untranslated strings from Antigravity binaries")
    parser.add_argument("--out", help="Output JSON file for missing strings")
    parser.add_argument("--dir", help="Antigravity installation directory")
    args = parser.parse_args()

    run_extraction(args.out, args.dir)

if __name__ == "__main__":
    main()
