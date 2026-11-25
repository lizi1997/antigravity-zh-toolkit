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
        appdata = os.environ.get("APPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Roaming")
        if not appdata:
            raise RuntimeError(
                "Cannot locate the Antigravity locales directory: "
                "neither %APPDATA% nor the home directory is available.")
        base = os.path.join(appdata, "Antigravity", "locales")
    os.makedirs(base, exist_ok=True)
    return base

# NOTE on recall vs precision: the length and shape filters here are a
# deliberate "recall over precision" pre-filter for the offline pipeline
# (scripts/localize.py QA H5/H12 apply the strict gates afterwards), so the
# thresholds intentionally differ from the engine's runtime skip rules.
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

# Files larger than this are skipped: reading a multi-hundred-MB binary
# fully into memory can OOM the extractor on small machines.
MAX_SCAN_BYTES = 300 * 1024 * 1024

def extract_from_binary(bin_path):
    print(f"[*] Scanning binary: {bin_path}...")
    try:
        if os.path.getsize(bin_path) > MAX_SCAN_BYTES:
            print(f"[!] Skipping {bin_path}: larger than {MAX_SCAN_BYTES // (1024 * 1024)} MB.")
            return set()
    except OSError as e:
        print(f"[!] Cannot stat {bin_path}: {e}")
        return set()
    strings = set()
    zip_errors = 0
    pattern = re.compile(rb'[\x20-\x7e]{3,200}')
    data = Path(os.path.abspath(bin_path)).read_bytes()
    for m in pattern.finditer(data):
        s = m.group().decode("utf-8", errors="ignore")
        if is_valid_ui_string(s):
            strings.add(s.strip())

    # Also scan embedded zip entries (e.g. deflate-compressed main.js inside language_server).
    # Both double- and single-quoted JS string literals are collected.
    pos = 0
    quoted_res = (
        re.compile(r'"((?:[^"\\\n]|\\.)*)"'),
        re.compile(r"'((?:[^'\\\n]|\\.)*)'"),
    )
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
                    for quoted_re in quoted_res:
                        for m in quoted_re.finditer(raw):
                            val = m.group(1)
                            try:
                                val = json.loads(f'"{val}"')
                            except Exception:
                                pass
                            if is_valid_ui_string(val):
                                strings.add(val.strip())
                except Exception:
                    zip_errors += 1
        pos = idx + 4

    print(f"[*] Found {len(strings)} raw candidate strings in {os.path.basename(bin_path)}"
          + (f" ({zip_errors} unreadable zip entr{'y' if zip_errors == 1 else 'ies'} skipped)" if zip_errors else ""))
    return strings

def get_default_install_dirs():
    """Platform-aware candidates for the Antigravity installation.

    Mirrors the patcher candidate table (scripts/patcher.py): the extractor
    must look everywhere the patcher installs to, or standard installs are
    silently reported as "no candidates".
    """
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
    return [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\resources"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity"),
        os.path.expandvars(r"%PROGRAMFILES%\antigravity\resources"),
        os.path.expandvars(r"%PROGRAMFILES%\antigravity"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\antigravity\resources"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\antigravity"),
    ]

def run_extraction(output_file=None, custom_dir=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    toolkit_dir = os.path.abspath(os.path.join(script_dir, ".."))
    locales_file = os.path.join(toolkit_dir, "locales", "zh-CN.json")

    existing_dict = {}
    if os.path.exists(locales_file):
        # utf-8-sig, same as the patcher: a BOM saved by Windows Notepad
        # must not break extraction while patching accepts it.
        existing_dict = json.loads(Path(os.path.abspath(locales_file)).read_text(encoding="utf-8-sig"))
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
    scanned = 0
    for t in targets:
        if os.path.exists(t):
            scanned += 1
            all_candidates.update(extract_from_binary(t))
    if not scanned:
        searched = ", ".join(install_dirs)
        print(f"[!] Error: no Antigravity installation found (searched: {searched}).")
        print("[!] Pass --dir with the directory containing app.asar.")
        raise SystemExit(2)

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
    out_abs = os.path.abspath(out_path)
    parent = os.path.dirname(out_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)
    Path(out_abs).write_text(
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
