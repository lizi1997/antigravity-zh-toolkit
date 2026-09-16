#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Toolkit - Build & Packaging Script (v1.0.1)
Cross-platform build utility for Windows, macOS, and Linux.

Regenerates two GENERATED artifacts - keep them in sync by always editing the
sources below and re-running this script (see CONTRIBUTING.md):

  scripts/patcher.py                  <- PATCHER_TEMPLATE + engine + dictionaries
  engine/ag_localization_engine.js    <- engine/engine_template.js + locales/*.json
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALES_DIR = os.path.join(REPO_ROOT, "locales")
ENGINE_DIR = os.path.join(REPO_ROOT, "engine")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

PATCHER_TEMPLATE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Patcher & Manager v1.0.1
Cross-Platform In-Place ASAR injection and management utility (Windows / macOS / Linux).

GENERATED FILE - DO NOT EDIT.
Produced by `python scripts/build.py` from PATCHER_TEMPLATE + locales/*.json +
engine/engine_template.js. Edit those sources and rebuild; direct edits here
are silently overwritten by the next build.
"""

import os
import sys
import struct
import json
import shutil
import hashlib
import argparse
import subprocess
from pathlib import Path

SIGNATURE_PRELOAD = "// Antigravity Client Modern Chinese Localization Engine"
ASAR_BLOCK_SIZE = 4194304
DICT_ZH_SENTINELS = ("/*AG_ZH_ZH_START*/", "/*AG_ZH_ZH_END*/")
DICT_PATTERNS_SENTINELS = ("/*AG_ZH_PATTERNS_START*/", "/*AG_ZH_PATTERNS_END*/")

EMBEDDED_ENGINE_CODE = __EMBEDDED_ENGINE_PLACEHOLDER__
EMBEDDED_ZH_JSON = __EMBEDDED_ZH_JSON_PLACEHOLDER__
EMBEDDED_PATTERNS_JSON = __EMBEDDED_PATTERNS_JSON_PLACEHOLDER__

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
        exe_path = _find_antigravity_process_path_windows()
        if exe_path and os.path.exists(exe_path):
            candidate = os.path.join(os.path.dirname(exe_path), "resources")
            if os.path.exists(os.path.join(candidate, "app.asar")):
                return candidate
            if os.path.exists(os.path.join(os.path.dirname(exe_path), "app.asar")):
                return os.path.dirname(exe_path)
    elif sys.platform == "darwin":
        try:
            out = subprocess.check_output(["pgrep", "-f", "Antigravity.app"]).decode("utf-8", errors="ignore").strip()
            if out:
                p = "/Applications/Antigravity.app/Contents/Resources"
                if os.path.exists(os.path.join(p, "app.asar")):
                    return p
        except Exception:
            pass

    return None

def _find_antigravity_process_path_windows():
    """Locate the running Antigravity.exe image path via the Win32 API.

    Pure ctypes (Toolhelp32 process snapshot + QueryFullProcessImageName):
    no shell, no subprocess, no console-window flash, no encoding surprises.
    """
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap in (0, -1, 0xFFFFFFFF):
            return None
        try:
            have = k32.Process32FirstW(snap, ctypes.byref(entry))
            while have:
                if entry.szExeFile and entry.szExeFile.lower() == "antigravity.exe":
                    hproc = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, entry.th32ProcessID)
                    if hproc:
                        try:
                            buf = ctypes.create_unicode_buffer(1024)
                            size = wintypes.DWORD(len(buf))
                            if k32.QueryFullProcessImageNameW(hproc, 0, buf, ctypes.byref(size)):
                                return buf.value
                        finally:
                            k32.CloseHandle(hproc)
                have = k32.Process32NextW(snap, ctypes.byref(entry))
        finally:
            k32.CloseHandle(snap)
    except Exception:
        return None
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
    if sys.platform == "win32":
        return _find_antigravity_process_path_windows() is not None
    try:
        my_pid = str(os.getpid())
        out = subprocess.check_output(["pgrep", "-i", "-f", "antigravity"]).decode("utf-8", errors="ignore")
        pids = [p.strip() for p in out.split() if p.strip() and p.strip() != my_pid]
        return len(pids) > 0
    except Exception:
        return False

def read_asar(asar_path):
    data = Path(os.path.abspath(asar_path)).read_bytes()
    u1, u2 = struct.unpack_from("<II", data, 0)
    base_offset = 8 + u2
    u3, json_len = struct.unpack_from("<II", data, 8)
    header = json.loads(data[16:16 + json_len].decode("utf-8"))

    files_data = {}
    def extract_files(tree, prefix=""):
        for name, entry in tree.get("files", {}).items():
            curr = f"{prefix}/{name}" if prefix else name
            if "files" in entry:
                extract_files(entry, curr)
            elif "size" in entry and "offset" in entry:
                start = base_offset + int(entry["offset"])
                files_data[curr] = data[start:start + entry["size"]]
    extract_files(header)
    return header, files_data

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(ASAR_BLOCK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()

def compute_integrity(data):
    blocks = [hashlib.sha256(data[i:i + ASAR_BLOCK_SIZE]).hexdigest()
              for i in range(0, len(data), ASAR_BLOCK_SIZE)]
    return {
        "algorithm": "SHA256",
        "hash": hashlib.sha256(data).hexdigest(),
        "blockSize": ASAR_BLOCK_SIZE,
        "blocks": blocks,
    }

def _write_all(fd, data):
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]

# Windows CRT defaults os.open to text mode unless O_BINARY is passed, which
# would silently corrupt every \n into \r\n inside the binary archive.
_O_BINARY = getattr(os, "O_BINARY", 0)

def write_asar_inplace(path, header, files_data, modified=None):
    """Serialize `header` + `files_data` into an ASAR archive at `path`.

    Offsets and sizes are recomputed for every packed file (preceding content
    growing shifts everything after it). Integrity hashes are recomputed only
    for paths in `modified`, or for all files when `modified` is None (restore
    and scratch builds); untouched files keep their original integrity
    metadata, which stays valid because their content is unchanged.

    Writing is atomic when possible (temp file + os.replace). If the target is
    held open by the running client, we fall back to an in-place rewrite.
    """
    path = os.path.abspath(path)
    offsets = {}
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
                offsets[curr] = current_offset
                if modified is None or curr in modified:
                    entry["integrity"] = compute_integrity(data)
                current_offset += len(data)
    update_entries(header)

    json_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    json_len = len(json_bytes)
    pad_len = (4 - (json_len % 4)) % 4
    json_bytes += b'\x00' * pad_len
    padded_json_len = len(json_bytes)

    u3 = 4 + padded_json_len
    u2 = 4 + u3

    payload = bytearray()
    payload += struct.pack("<IIII", 4, u2, u3, json_len)
    payload += json_bytes
    for curr, off in sorted(offsets.items(), key=lambda kv: kv[1]):
        payload += files_data[curr]

    tmp_path = path + ".zh_tmp"
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | _O_BINARY)
        try:
            _write_all(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        try:
            os.replace(tmp_path, path)
        except PermissionError as exc:
            raise PermissionError(
                "Cannot replace app.asar atomically. Close Antigravity and try again."
            ) from exc
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def patch_menu_js(content_str):
    replacements = [
        ("label: 'New Window'", "label: '新建窗口 (New Window)'", -1),
        ("label: 'Docs'", "label: '官方文档 (Docs)'", -1),
        ("label: updater_1.MenuUpdateStep.CheckForUpdates", "label: '检查更新 (Check for Updates)'", -1),
        # Only the first occurrence of the submenu lookup keys is rewritten so
        # later addItemToSubmenu calls still find the original 'File'/'Help' keys.
        ("addItemToSubmenu(menu, 'File'", "addItemToSubmenu(menu, '文件 (File)'", 1),
        ("addItemToSubmenu(menu, 'Help'", "addItemToSubmenu(menu, '帮助 (Help)'", 1),
    ]
    applied = []
    missed = 0
    for old, new, count in replacements:
        hits = content_str.count(old)
        if hits:
            content_str = content_str.replace(old, new, count)
            applied.append(f"hit x{hits}: {old[:44]}")
        else:
            applied.append(f"MISS     : {old[:44]}")
            missed += 1
    print("[*] Native menu patch results:")
    for line in applied:
        print(f"      {line}")
    if missed:
        print(f"[!] {missed} menu replacement(s) not found - the client UI may have changed in an update")
    return content_str

def load_valid_json_text(path):
    """Return the file text when it parses as JSON, else None."""
    try:
        text = Path(os.path.abspath(path)).read_text(encoding="utf-8")
        json.loads(text)
        return text
    except Exception:
        return None

def resolve_dictionary_texts(locales_dir):
    """Prefer user-edited external dictionaries; validate before use."""
    zh_path = os.path.join(locales_dir, "zh-CN.json")
    pat_path = os.path.join(locales_dir, "patterns.json")
    zh_text = load_valid_json_text(zh_path)
    pat_text = load_valid_json_text(pat_path)
    if zh_text is None and os.path.exists(zh_path):
        print("[!] External zh-CN.json is invalid JSON; using embedded dictionary")
    if pat_text is None and os.path.exists(pat_path):
        print("[!] External patterns.json is invalid JSON; using embedded patterns")
    return (zh_text if zh_text is not None else EMBEDDED_ZH_JSON,
            pat_text if pat_text is not None else EMBEDDED_PATTERNS_JSON)

def splice_engine_dicts(engine_code, zh_text, pat_text):
    """Swap the sentinel-wrapped dictionary blocks inside the engine code."""
    def _splice(code, start_mark, end_mark, text):
        anchor = code.find(start_mark)
        if anchor == -1:
            return None
        end = code.find(end_mark, anchor)
        if end == -1:
            return None
        return code[:anchor + len(start_mark)] + "\n" + text + "\n" + code[end:]
    spliced = _splice(engine_code, DICT_ZH_SENTINELS[0], DICT_ZH_SENTINELS[1], zh_text)
    if spliced is None:
        print("[!] zh dictionary sentinel not found in engine; injecting embedded dictionaries as-is")
        return engine_code
    spliced = _splice(spliced, DICT_PATTERNS_SENTINELS[0], DICT_PATTERNS_SENTINELS[1], pat_text)
    if spliced is None:
        print("[!] patterns sentinel not found in engine; injecting embedded dictionaries as-is")
        return engine_code
    return spliced

def seed_locale_files(locales_dir):
    """Drop editable copies of the embedded dictionaries (never overwrite)."""
    for fname, text in (("zh-CN.json", EMBEDDED_ZH_JSON), ("patterns.json", EMBEDDED_PATTERNS_JSON)):
        target = Path(os.path.abspath(os.path.join(locales_dir, fname)))
        if target.exists():
            continue
        try:
            target.write_text(text, encoding="utf-8")
            print(f"[+] Seeded editable dictionary: {target}")
        except Exception as e:
            print(f"[!] Could not seed {target}: {e}")

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

    print("[*] Reading current app.asar...")
    try:
        header, files = read_asar(asar_path)
    except Exception as e:
        print(f"[!] Error reading {asar_path}: {e}")
        return False

    if "dist/preload.js" not in files:
        print("[!] Error: dist/preload.js not found in app.asar!")
        return False

    current_patched = SIGNATURE_PRELOAD in files["dist/preload.js"].decode("utf-8", errors="ignore")

    locales_dir = get_locales_dir()
    zh_text, pat_text = resolve_dictionary_texts(locales_dir)
    engine_code = splice_engine_dicts(EMBEDDED_ENGINE_CODE, zh_text, pat_text)

    if current_patched and not force:
        if engine_code in files["dist/preload.js"].decode("utf-8", errors="ignore"):
            print("[*] Antigravity is already patched with the current engine and dictionaries!")
            seed_locale_files(locales_dir)
            return True
        if not os.path.exists(bak_path):
            print("[!] Dictionaries changed but no official backup exists to re-patch from; keeping current patch.")
            return True
        print("[*] Dictionaries/engine changed since last patch; re-patching from official backup...")
        header, files = read_asar(bak_path)
        if "dist/preload.js" not in files:
            print("[!] Error: dist/preload.js missing from backup?!")
            return False
    elif current_patched and force:
        if not os.path.exists(bak_path):
            # No clean origin to re-patch from; injecting twice would duplicate
            # the engine, so keep the existing patch instead.
            print("[!] --force requested but no official backup exists; keeping current patch as-is.")
            return True
        print("[*] Current build already patched; re-patching from clean official backup...")
        header, files = read_asar(bak_path)
        if "dist/preload.js" not in files:
            print("[!] Error: dist/preload.js missing from backup?!")
            return False
    elif not os.path.exists(bak_path):
        print(f"[*] Creating backup of official app.asar -> {bak_path}...")
        shutil.copy2(asar_path, bak_path)
    else:
        # The current build is an unpatched official archive, which is by
        # definition authoritative: replace a stale (older-version) backup with
        # it. Same size is treated as "same build" to avoid needless copies of
        # multi-hundred-MB archives.
        if file_sha256(asar_path) == file_sha256(bak_path):
            print(f"[*] Official backup already exists at {bak_path}")
        else:
            print("[*] Detected app update: refreshing official backup (existing one was stale)")
            shutil.copy2(asar_path, bak_path)

    print("[*] Injecting modern localization engine into dist/preload.js...")
    preload_str = files["dist/preload.js"].decode("utf-8")
    new_preload = preload_str.rstrip() + "\n\n" + engine_code + "\n"
    files["dist/preload.js"] = new_preload.encode("utf-8")
    modified = {"dist/preload.js"}

    if "dist/menu.js" in files:
        print("[*] Patching native menus in dist/menu.js...")
        menu_str = files["dist/menu.js"].decode("utf-8")
        files["dist/menu.js"] = patch_menu_js(menu_str).encode("utf-8")
        modified.add("dist/menu.js")

    print("[*] Writing patched files to app.asar...")
    try:
        write_asar_inplace(asar_path, header, files, modified=modified)
    except Exception as e:
        print(f"[!] Write error: {e}")
        return False

    seed_locale_files(locales_dir)

    print("\n========================================================")
    print("  [+] 汉化补丁安装成功！(Patch applied successfully!)")
    print(f"  [+] 词典目录(可直接编辑, 改完重新运行本程序生效): {locales_dir}")
    print("  [+] 请按 Ctrl+Shift+N (Mac: Cmd+Shift+N) 新建窗口，或重启客户端即可查看汉化效果！")
    print("  [+] 在任何页面随时按 Ctrl+Alt+L 可复制未汉化词条！")
    print("========================================================\n")
    return True

def restore_backup(install_dir=None):
    if not install_dir:
        install_dir = get_default_install_dir()
    if not install_dir or not os.path.exists(install_dir):
        print("[!] Error: Antigravity installation not found. Specify with --dir")
        return False

    asar_path = os.path.join(install_dir, "app.asar") if os.path.exists(os.path.join(install_dir, "app.asar")) else os.path.join(install_dir, "resources", "app.asar")
    bak_path = asar_path + ".bak"

    if not os.path.exists(bak_path):
        print(f"[!] No backup file found at {bak_path}")
        return False

    if os.path.exists(asar_path):
        cur_size, bak_size = os.path.getsize(asar_path), os.path.getsize(bak_path)
        if cur_size != bak_size:
            print(f"[!] Size mismatch: current app.asar is {cur_size} bytes, backup is {bak_size} bytes.")
            print("[!] The backup may come from a different (older) client version; restoring rolls the app back to it.")

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
            return True
        except Exception as e:
            print(f"Error reading app.asar: {e}")
            return False
    return False

def main():
    parser = argparse.ArgumentParser(description="Antigravity Modern Chinese Localization Patcher v1.0.2")
    parser.add_argument("action", nargs="?", default="patch", choices=["patch", "restore", "status"], help="Action to perform (default: patch)")
    parser.add_argument("--dir", help="Custom Antigravity installation directory")
    parser.add_argument("--force", action="store_true", help="Force re-patching even if already patched")

    args = parser.parse_args()

    if args.action == "patch":
        ok = apply_patch(args.dir, force=args.force)
    elif args.action == "restore":
        ok = restore_backup(args.dir)
    elif args.action == "status":
        ok = show_status(args.dir)

    # If running in interactive terminal on Windows without arguments, pause before exit
    if sys.platform == "win32" and len(sys.argv) <= 1:
        try:
            input("\n按回车键退出 (Press Enter to exit)...")
        except Exception:
            pass

    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
'''

def build(compile_exe=True):
    print("=" * 60)
    print("  Antigravity-ZH Toolkit Builder (v1.0.2)")
    print("=" * 60)

    template_path = os.path.join(ENGINE_DIR, "engine_template.js")
    zh_path = os.path.join(LOCALES_DIR, "zh-CN.json")
    pat_path = os.path.join(LOCALES_DIR, "patterns.json")

    print("[1/3] Loading locales and building ag_localization_engine.js...")
    zh_json_str = Path(zh_path).read_text(encoding="utf-8")
    pat_json_str = Path(pat_path).read_text(encoding="utf-8")
    template = Path(template_path).read_text(encoding="utf-8")
    # Fail fast on broken dictionary sources before generating anything.
    json.loads(zh_json_str)
    json.loads(pat_json_str)

    full_engine_js = (
        "// GENERATED by scripts/build.py - DO NOT EDIT.\n"
        "// Edit engine/engine_template.js and locales/*.json, then rebuild.\n"
        + template.replace("__TRANSLATIONS_JSON__", zh_json_str).replace("__PATTERNS_JSON__", pat_json_str)
    )
    engine_out = os.path.join(ENGINE_DIR, "ag_localization_engine.js")
    Path(engine_out).write_text(full_engine_js, encoding="utf-8", newline="\n")
    print(f"      Saved {engine_out} ({len(full_engine_js)} bytes)")

    print("[2/3] Embedding latest engine into scripts/patcher.py...")
    patcher_py = os.path.join(SCRIPTS_DIR, "patcher.py")
    clean_patcher_code = (
        PATCHER_TEMPLATE
        .replace("__EMBEDDED_ENGINE_PLACEHOLDER__", json.dumps(full_engine_js, ensure_ascii=False))
        .replace("__EMBEDDED_ZH_JSON_PLACEHOLDER__", json.dumps(zh_json_str, ensure_ascii=False))
        .replace("__EMBEDDED_PATTERNS_JSON_PLACEHOLDER__", json.dumps(pat_json_str, ensure_ascii=False))
    )
    Path(patcher_py).write_text(clean_patcher_code, encoding="utf-8", newline="\n")
    print(f"      Updated {patcher_py}")

    if compile_exe:
        is_win = sys.platform == "win32"
        binary_name = "antigravity-zh.exe" if is_win else "antigravity-zh"
        print(f"[3/3] Compiling {binary_name} with PyInstaller...")
        dist_dir = os.path.join(REPO_ROOT, "dist")
        build_dir = os.path.join(REPO_ROOT, "build")
        os.makedirs(dist_dir, exist_ok=True)

        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m", "PyInstaller",
                    "--onefile",
                    "--clean",
                    "--name", "antigravity-zh",
                    "--distpath", dist_dir,
                    "--workpath", build_dir,
                    "--specpath", build_dir,
                    patcher_py,
                ],
                check=True,
            )
            output_bin = os.path.join(dist_dir, binary_name)

            # Keep a copy at the repo root for double-click installs.
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
            print(f"  [+] Copied to repo root.")
            print("=" * 60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] Compilation failed: {e}")
            return False
    else:
        print("[+] Engine and patcher updated (skipping executable compilation).")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity-ZH Builder v1.0.2")
    parser.add_argument("--no-exe", action="store_true", help="Skip PyInstaller compilation")
    args = parser.parse_args()
    build(compile_exe=not args.no_exe)
