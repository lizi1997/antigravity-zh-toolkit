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
import struct
import zlib
import argparse
from pathlib import Path

def get_user_locales_dir():
    """The user's editable dictionary directory (same location as the patcher)."""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support/Antigravity/locales")
    elif sys.platform.startswith("linux"):
        base = os.path.expanduser("~/.config/Antigravity/locales")
    else:
        base = os.path.join(os.environ.get("APPDATA", ""), "Antigravity", "locales")
    os.makedirs(base, exist_ok=True)
    return base

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
    data = Path(os.path.abspath(bin_path)).read_bytes()
    for m in pattern.finditer(data):
        s = m.group().decode("utf-8", errors="ignore")
        if is_valid_ui_string(s):
            strings.add(s.strip())

    # Also scan embedded zip entries (e.g. deflate-compressed main.js inside language_server)
    pos = 0
    quoted_re = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
    while True:
        idx = data.find(b'PK\x03\x04', pos)
        if idx == -1 or idx + 30 > len(data):
            break
        ver, flag, method, mtime, mdate, crc, csize, usize, fnlen, exlen = struct.unpack(
            '<HHHHHIIIHH', data[idx+4:idx+30]
        )
        if 0 < fnlen < 200 and exlen < 1000 and idx + 30 + fnlen + exlen + csize <= len(data):
            fname = data[idx+30:idx+30+fnlen].decode('utf-8', errors='ignore')
            if method == 8 and fname.endswith(('.js', '.html')) and not fname.startswith('prism/'):
                start = idx + 30 + fnlen + exlen
                try:
                    raw = zlib.decompress(data[start:start+csize], -15).decode('utf-8', errors='ignore')
                    for m in quoted_re.finditer(raw):
                        val = m.group(1)
                        try:
                            val = json.loads(f'"{val}"')
                        except Exception:
                            pass
                        if is_valid_ui_string(val):
                            strings.add(val.strip())
                except Exception:
                    pass
        pos = idx + 4

    print(f"[*] Found {len(strings)} raw candidate strings in {os.path.basename(bin_path)}")
    return strings

def get_default_install_dirs():
    """Platform-aware candidates for the Antigravity installation."""
    if sys.platform == "darwin":
        return [
            "/Applications/Antigravity.app/Contents/Resources",
            os.path.expanduser("~/Applications/Antigravity.app/Contents/Resources"),
        ]
    if sys.platform.startswith("linux"):
        return [
            "/opt/antigravity/resources",
            "/usr/lib/antigravity/resources",
            "/usr/local/lib/antigravity/resources",
            os.path.expanduser("~/.local/share/antigravity/resources"),
        ]
    return [os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity")]

def run_extraction(output_file=None, custom_dir=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    toolkit_dir = os.path.abspath(os.path.join(script_dir, ".."))
    locales_file = os.path.join(toolkit_dir, "locales", "zh-CN.json")

    existing_dict = {}
    if os.path.exists(locales_file):
        existing_dict = json.loads(Path(os.path.abspath(locales_file)).read_text(encoding="utf-8"))
    print(f"[*] Loaded existing dictionary: {len(existing_dict)} entries")
    lower_existing = {k.lower().strip(): v for k, v in existing_dict.items()}

    install_dirs = [custom_dir] if custom_dir else get_default_install_dirs()
    ls_name = "language_server.exe" if sys.platform == "win32" else "language_server"
    targets = []
    for d in install_dirs:
        for resources in (d, os.path.join(d, "resources")):
            targets.append(os.path.join(resources, "app.asar"))
            targets.append(os.path.join(resources, "bin", ls_name))

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

    # Keep the candidates OUT of the repository: locales/*.json is picked up
    # by the CI packaging step and would ship an untranslated file. The values
    # are empty by design - they are candidates, not translations.
    if output_file:
        out_path = output_file
    else:
        out_path = os.path.join(get_user_locales_dir(), "missing_strings.json")
    Path(os.path.abspath(out_path)).write_text(
        json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8"
    )

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
