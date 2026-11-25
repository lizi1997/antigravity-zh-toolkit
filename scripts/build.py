#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Antigravity Localization Toolkit - Build & Packaging Script (v1.0.6)
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
Antigravity Localization Patcher & Manager v1.0.6
Cross-Platform In-Place ASAR injection and management utility (Windows / macOS / Linux).

GENERATED FILE - DO NOT EDIT.
Produced by `python scripts/build.py` from PATCHER_TEMPLATE + locales/*.json +
engine/engine_template.js. Edit those sources and rebuild; direct edits here
are silently overwritten by the next build.
"""

import os
import sys
import stat
import struct
import json
import shutil
import hashlib
import argparse
import subprocess
import tempfile
import time
from pathlib import Path

SIGNATURE_PRELOAD = "// Antigravity Client Modern Chinese Localization Engine"
ASAR_BLOCK_SIZE = 4194304
DICT_ZH_SENTINELS = ("/*AG_ZH_ZH_START*/", "/*AG_ZH_ZH_END*/")
DICT_PATTERNS_SENTINELS = ("/*AG_ZH_PATTERNS_START*/", "/*AG_ZH_PATTERNS_END*/")
# Archive members the patcher rewrites. They are excluded from the build
# fingerprint because a patched archive must still match its clean backup.
PATCH_TARGETS = ("dist/preload.js", "dist/menu.js", "dist/main.js", "dist/updater.js")

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
    """The user's editable dictionary directory (the one documented in README).

    This is the only place the tool writes to and the only place a user is
    expected to edit. The dictionary shipped next to the tool is read-only
    input and gets merged in by resolve_dictionary_texts().
    """
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

def _resolve_install_dir(install_dir):
    """Validate the install dir and locate app.asar. Returns (dir, asar, bak).

    Raises ValueError with a human-readable reason when the directory is
    unusable, so a typo in --dir can never silently read or write an
    unrelated app.asar. A symlinked app.asar is refused outright: os.replace
    would swap the link itself instead of the file it points to.
    """
    if not install_dir:
        install_dir = get_default_install_dir()
    if not install_dir:
        raise ValueError("Antigravity installation not found. Specify with --dir")
    resolved = os.path.realpath(os.path.abspath(install_dir))
    if not os.path.isdir(resolved):
        raise ValueError(f"Not a directory: {install_dir}")
    asar_path = os.path.join(resolved, "app.asar")
    if not os.path.isfile(asar_path):
        nested = os.path.join(resolved, "resources", "app.asar")
        if os.path.isfile(nested):
            asar_path = nested
    if os.path.islink(asar_path):
        raise ValueError(
            f"Refusing to touch a symlinked app.asar: {asar_path}. "
            "Point --dir at the real installation directory.")
    if not os.path.isfile(asar_path):
        raise ValueError(
            f"No Antigravity app.asar found under {resolved}. "
            "Pass the directory that directly contains app.asar "
            "(or its parent when app.asar lives in resources/).")
    return resolved, asar_path, asar_path + ".bak"

def _acquire_lock(directory):
    """Create an exclusive patch lock. Returns the lock path, or None if busy.

    A lock older than 15 minutes is treated as stale (previous run crashed)
    and is removed. Any other error while creating the lock is raised: the
    write path would fail there anyway, with a less clear message.
    """
    lock_path = os.path.join(directory, "app.asar.zhlock")
    try:
        fd = os.open(lock_path,
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                     0o600)
        try:
            os.write(fd, str(os.getpid()).encode("utf-8"))
        finally:
            os.close(fd)
        return lock_path
    except FileExistsError:
        try:
            age = time.time() - os.path.getmtime(lock_path)
        except OSError:
            return None
        if age > 900:
            try:
                os.remove(lock_path)
            except OSError:
                return None
            return _acquire_lock(directory)
        return None

def _release_lock(lock_path):
    if lock_path:
        try:
            os.remove(lock_path)
        except OSError:
            pass

def _atomic_copy2(src, dst):
    """Copy src to dst atomically: tmp + fsync + verify + os.replace.

    A plain shutil.copy2 can leave a truncated backup behind when two
    instances run concurrently or the machine loses power mid-copy - and a
    truncated .bak fails every later re-patch and restore. The checksum is
    verified before the rename, and the source file mode is preserved.
    """
    dst = os.path.abspath(dst)
    parent = os.path.dirname(dst)
    open_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    tmp_fd = None
    tmp_path = None
    for _ in range(16):
        candidate = os.path.join(parent, f".{os.path.basename(dst)}.tmp_{os.urandom(8).hex()}")
        try:
            tmp_fd = os.open(candidate, open_flags, 0o600)
            tmp_path = candidate
            break
        except FileExistsError:
            continue
    if tmp_fd is None or tmp_path is None:
        raise RuntimeError(f"Could not allocate temporary file in {parent}")
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            with open(src, "rb") as s:
                shutil.copyfileobj(s, f, 1024 * 1024)
            f.flush()
            os.fsync(f.fileno())
        if file_sha256(tmp_path) != file_sha256(src):
            raise IOError("Backup verification failed: checksum mismatch after copy")
        try:
            os.chmod(tmp_path, stat.S_IMODE(os.stat(src).st_mode))
        except OSError:
            pass
        os.replace(tmp_path, dst)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

def get_bundled_locales_dir():
    """The read-only dictionary shipped next to the tool.

    Covers both layouts:
      * a release package or a source checkout - `locales/` next to
        scripts/patcher.py (the macOS bundle keeps it at macos_dist/locales)
      * a PyInstaller one-file binary - `locales/` next to the executable

    It is never written to; the user's editable copy lives in
    get_locales_dir().
    """
    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "locales"))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "locales"))
    for c in candidates:
        c = os.path.abspath(c)
        if os.path.isfile(os.path.join(c, "zh-CN.json")):
            return c
    return None

def is_antigravity_running():
    if sys.platform == "win32":
        return _find_antigravity_process_path_windows() is not None
    try:
        my_pid = str(os.getpid())
        # Exact process-name match only: "-f" would substring-match full command
        # lines (installer shells and tool paths contain "antigravity"), making
        # the check report the IDE as running when it is not.
        out = subprocess.check_output(["pgrep", "-i", "-x", "Antigravity"]).decode("utf-8", errors="ignore")
        pids = [p.strip() for p in out.split() if p.strip() and p.strip() != my_pid]
        return len(pids) > 0
    except Exception:
        return False

def read_asar(asar_path):
    data = Path(os.path.abspath(asar_path)).read_bytes()
    if len(data) < 16:
        raise ValueError("Not an ASAR archive: file is too small to hold a header")
    u1, u2 = struct.unpack_from("<II", data, 0)
    if u1 != 4:
        # Chromium's pickle format always starts with a uint32 payload size of
        # 4. Without this check a truncated or foreign file was accepted and
        # its members were silently sliced out of the wrong offsets.
        raise ValueError(f"Not an ASAR archive: unexpected header magic {u1} (expected 4)")
    base_offset = 8 + u2
    u3, json_len = struct.unpack_from("<II", data, 8)
    if base_offset > len(data) or 16 + json_len > len(data):
        raise ValueError("Not an ASAR archive: the header length exceeds the file size")
    header = json.loads(data[16:16 + json_len].decode("utf-8"))

    files_data = {}
    def extract_files(tree, prefix=""):
        for name, entry in tree.get("files", {}).items():
            curr = f"{prefix}/{name}" if prefix else name
            if "files" in entry:
                extract_files(entry, curr)
            elif "size" in entry and "offset" in entry:
                start = base_offset + int(entry["offset"])
                size = int(entry["size"])
                # A truncated archive used to yield short slices without any
                # error, and re-writing it would have frozen the corruption.
                if start < 0 or size < 0 or start + size > len(data):
                    raise ValueError(
                        f"Corrupt ASAR archive: entry {curr} spans {start}..{start + size} "
                        f"but the file is only {len(data)} bytes")
                files_data[curr] = data[start:start + size]
    extract_files(header)
    return header, files_data

def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(ASAR_BLOCK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()

def write_backup_sidecar(asar_path, bak_path):
    """Record the official backup's SHA-256 next to it, so later re-patches
    and restores can detect a tampered or replaced backup."""
    sidecar = bak_path + ".sha256"
    try:
        Path(sidecar).write_text(file_sha256(asar_path) + "\n", encoding="utf-8")
        print(f"[+] Recorded backup checksum: {sidecar}")
    except Exception as e:
        print(f"[!] Could not write backup checksum {sidecar}: {e}")

def backup_matches_sidecar(bak_path):
    """True when the backup has no sidecar (legacy) or its hash matches."""
    sidecar = bak_path + ".sha256"
    if not os.path.exists(sidecar):
        return True
    try:
        expected = Path(sidecar).read_text(encoding="utf-8").strip()
    except Exception:
        return True
    return file_sha256(bak_path) == expected

def ensure_backup_sidecar(bak_path):
    """Write the missing `.sha256` sidecar for a backup created before it existed.

    The sidecar was only ever written when a backup was created or refreshed,
    so every installation that already had a backup kept it sidecar-less
    forever - and `backup_matches_sidecar()` trusts a sidecar-less backup
    unconditionally, leaving tamper detection permanently disabled for those
    installations. Back-filling the sidecar restores it.
    """
    sidecar = bak_path + ".sha256"
    if os.path.exists(sidecar) or not os.path.exists(bak_path):
        return False
    try:
        Path(sidecar).write_text(file_sha256(bak_path) + "\n", encoding="utf-8")
        print(f"[+] Recorded backup checksum: {sidecar}")
        return True
    except Exception as e:
        print(f"[!] Could not write backup checksum {sidecar}: {e}")
        return False

def compute_build_fingerprint(header, files):
    """Stable identity of a client build, ignoring the files the patcher edits.

    Two archives with the same fingerprint come from the same client build.
    The patched targets are excluded because the patcher changes them itself;
    the unpacked entry paths are included because their payload lives outside
    the archive and must therefore match too.
    """
    h = hashlib.sha256()
    unpacked = []

    def _walk(node, prefix=""):
        for name, entry in node.get("files", {}).items():
            path = f"{prefix}/{name}" if prefix else name
            if "files" in entry:
                _walk(entry, path)
            elif "offset" not in entry:
                unpacked.append(path)

    _walk(header)
    for path in sorted(unpacked):
        h.update(b"U\0" + path.encode("utf-8") + b"\0")
    for path in sorted(files):
        if path in PATCH_TARGETS:
            continue
        h.update(path.encode("utf-8") + b"\0" + hashlib.sha256(files[path]).digest())
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

def write_asar_inplace(path, header, files_data, modified=None):
    """Serialize `header` + `files_data` into an ASAR archive at `path`.

    Offsets and sizes are recomputed for every packed file (preceding content
    growing shifts everything after it). Integrity hashes are recomputed only
    for paths in `modified`, or for all files when `modified` is None (restore
    and scratch builds); untouched files keep their original integrity
    metadata, which stays valid because their content is unchanged.

    Writing is atomic (temp file in the same directory + os.replace) so a
    locked or read-only target fails cleanly without corrupting app.asar.
    """
    path = os.path.abspath(path)
    # Preserve the original file mode across the atomic replace: the temp
    # file is created 0600, and without this the installed app.asar would
    # silently change from 0644 to 0600 on every patch/restore.
    try:
        src_mode = stat.S_IMODE(os.stat(path).st_mode)
    except OSError:
        src_mode = None
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

    # Avoid tempfile.mkstemp() on Windows: when NTFS ACLs or a sandbox deny
    # write access to `dir` while `os.access(dir, os.W_OK)` still returns True
    # (because W_OK only inspects the DOS read-only bit), Python's stdlib
    # `_mkstemp_inner` retries `TMP_MAX` (2,147,483,647) times and hangs.
    parent_dir = os.path.dirname(path)
    base_name = os.path.basename(path)
    open_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    tmp_fd = None
    tmp_path = None
    for _ in range(16):
        candidate = os.path.join(parent_dir, f"{base_name}.zh_tmp_{os.urandom(8).hex()}")
        try:
            tmp_fd = os.open(candidate, open_flags, 0o600)
            tmp_path = candidate
            break
        except FileExistsError:
            continue
        except PermissionError as exc:
            if os.path.exists(candidate):
                continue
            raise PermissionError(
                f"Permission denied writing to {parent_dir}. Run with sufficient permissions and try again."
            ) from exc
    if tmp_fd is None or tmp_path is None:
        raise RuntimeError(f"Could not allocate temporary file in {parent_dir}")
    try:
        try:
            _write_all(tmp_fd, payload)
            os.fsync(tmp_fd)
        finally:
            os.close(tmp_fd)
        if src_mode is not None:
            try:
                os.chmod(tmp_path, src_mode)
            except OSError:
                pass
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

def apply_literal_replacements(content_str, groups, label):
    """Apply literal replacements and report hits *and* actual replacements.

    `groups` is a list of groups; every group holds the alternative spellings
    of one logical string (for example the single- and double-quoted form of a
    dialog title). A group counts as a hit when *any* of its alternatives
    matched - otherwise a client that only uses one quoting style would report
    a spurious miss.

    `hits` is how often the literal occurs in the source; `replaced` is how
    many occurrences were really rewritten (a replacement may cap the count).
    Reporting only `hits` made the log claim success for replacements that
    never happened - the menu lookup-key rewrite used to print "hit x3" while
    only the first occurrence was touched.
    """
    applied = []
    missed = 0
    replaced_total = 0
    for group in groups:
        group_hits = 0
        group_replaced = 0
        matched_literal = None
        for old, new, count in group:
            hits = content_str.count(old)
            if hits:
                content_str = content_str.replace(old, new, count)
                after = content_str.count(old)
                replaced = hits - after if count >= 0 else hits
                group_hits += hits
                group_replaced += replaced
                if matched_literal is None:
                    matched_literal = old
        if group_hits:
            applied.append(f"hit x{group_hits}, replaced x{group_replaced}: {matched_literal[:44]}")
            replaced_total += group_replaced
        else:
            applied.append(f"MISS     : {group[0][0][:44]}")
            missed += 1
    print(f"[*] {label} patch results:")
    for line in applied:
        print(f"      {line}")
    if missed:
        print(f"[!] {missed} {label} replacement(s) not found - the client UI may have changed in an update")
    return content_str, replaced_total, missed

def patch_menu_js(content_str):
    # The submenu *lookup keys* ('File' / 'Help') must stay untouched.
    # addItemToSubmenu() resolves a submenu with `item.label === submenuLabel`,
    # and the base application menu is built by Electron - the patch cannot
    # rename those labels. Rewriting the lookup key therefore made the lookup
    # fail and silently dropped the "New Window" item together with its
    # CmdOrCtrl+Shift+N accelerator. Only the visible labels are localized.
    groups = [
        [("label: 'New Window'", "label: '新建窗口 (New Window)'", -1)],
        [("label: 'Docs'", "label: '官方文档 (Docs)'", -1)],
        # NOTE: the "Check for Updates" label is deliberately NOT rewritten.
        # updateMenuState() overwrites item.label with the raw updater state on
        # every updater event, so a translated label would be erased again -
        # and the click handler resolves its action by that label.
    ]
    content_str, _, _ = apply_literal_replacements(content_str, groups, "Native menu")
    return content_str

def patch_updater_js(content_str):
    groups = [
        [("title: 'Check for Updates'", "title: '检查更新'", -1),
         ('title: "Check for Updates"', 'title: "检查更新"', -1)],
        [("message: 'No updates available'", "message: '当前已是最新版本'", -1),
         ('message: "No updates available"', 'message: "当前已是最新版本"', -1)],
    ]
    content_str, _, _ = apply_literal_replacements(content_str, groups, "Native updater")
    return content_str

def patch_main_js(content_str):
    groups = [
        [("title: 'Confirm Quit'", "title: '确认退出'", -1)],
        [("message: 'Are you sure you want to quit?'", "message: '确定要退出吗？'", -1)],
        [("detail: 'There may be agents or background tasks running.'", "detail: '可能有正在运行的智能体或后台任务。'", -1)],
        [("buttons: ['Cancel', 'Quit']", "buttons: ['取消', '退出']", -1)],
    ]
    content_str, _, _ = apply_literal_replacements(content_str, groups, "Native main dialog")
    return content_str

def load_valid_json_text(path):
    """Return the file text when it parses as JSON, else None."""
    try:
        # utf-8-sig transparently strips a BOM. Windows editors add one, and a
        # plain utf-8 read would make json.loads() fail on the whole file.
        text = Path(os.path.abspath(path)).read_text(encoding="utf-8-sig")
        json.loads(text)
        return text
    except Exception:
        return None

def merge_dict_texts(base_text, override_text):
    """Merge two JSON objects; the override wins per key.

    Defensive: an override that is valid JSON but not an object (a user
    hand-editing the dictionary can easily produce `[]`), or that carries
    non-string keys/values, is ignored with a warning instead of crashing
    the patch or silently emptying the dictionary.
    """
    try:
        merged = dict(json.loads(base_text))
        override = json.loads(override_text)
    except Exception:
        print("[!] Dictionary merge failed (invalid JSON); keeping base dictionary.")
        return base_text
    if not isinstance(override, dict):
        print("[!] Dictionary override is valid JSON but not an object; ignoring it.")
        return base_text
    if any(not isinstance(k, str) for k in override):
        print("[!] Dictionary override has non-string key(s); ignoring it.")
        return base_text
    if any(not isinstance(v, str) for v in override.values()):
        print("[!] Dictionary override has non-string value(s); ignoring it.")
        return base_text
    merged.update(override)
    return json.dumps(merged, ensure_ascii=False, indent=2)

def merge_pattern_texts(base_text, override_text):
    """Merge two JSON rule lists.

    The override is the user's copy:
      * a rule the user changed keeps the base rule's position but the user's
        content, so an upstream revision does not silently win;
      * a rule the user added is placed first, so it takes priority.

    Defensive: an override that is valid JSON but not a list is ignored, and
    individual malformed rules are skipped with a count instead of raising
    AttributeError on `rule.get`.
    """
    base = json.loads(base_text)
    try:
        override = json.loads(override_text)
    except Exception:
        print("[!] Pattern merge failed (invalid JSON); keeping base rules.")
        return base_text
    if not isinstance(base, list) or not isinstance(override, list):
        print("[!] Pattern file is valid JSON but not a rule list; keeping base rules.")
        return base_text
    skipped = 0
    index_of = {}
    merged = []
    for rule in base:
        index_of[(rule.get("pattern"), rule.get("flags"))] = len(merged)
        merged.append(rule)
    fresh = []
    for rule in override:
        if not isinstance(rule, dict) or "pattern" not in rule or "replacement" not in rule:
            skipped += 1
            continue
        key = (rule.get("pattern"), rule.get("flags"))
        if key in index_of:
            merged[index_of[key]] = rule
        else:
            fresh.append(rule)
    if skipped:
        print(f"[!] Skipped {skipped} malformed pattern rule(s) (not rule objects); keeping the rest.")
    return json.dumps(fresh + merged, ensure_ascii=False, indent=2)

def base_dictionary_texts():
    """The dictionary the tool ships: the embedded copy plus the bundle that
    sits next to the tool (a release package or a source checkout).

    Returns (zh_text, patterns_text) as JSON strings.
    """
    zh_base = EMBEDDED_ZH_JSON
    pat_base = EMBEDDED_PATTERNS_JSON

    bundled_dir = get_bundled_locales_dir()
    if bundled_dir:
        bundled_zh = load_valid_json_text(os.path.join(bundled_dir, "zh-CN.json"))
        bundled_pat = load_valid_json_text(os.path.join(bundled_dir, "patterns.json"))
        if bundled_zh and not contains_sentinel_marker(bundled_zh):
            zh_base = merge_dict_texts(zh_base, bundled_zh)
        if bundled_pat and not contains_sentinel_marker(bundled_pat):
            pat_base = merge_pattern_texts(pat_base, bundled_pat)
    return zh_base, pat_base

def resolve_dictionary_texts(locales_dir):
    """Merge the embedded dictionary with the bundled and the user's copy.

    Precedence, later wins per key: embedded < bundled < user.

    The user's dictionary is never discarded. An earlier version compared the
    entry counts and threw the whole file away when the user's copy had fewer
    entries - that silently deleted the user's own translations.
    """
    zh_base, pat_base = base_dictionary_texts()

    zh_path = os.path.join(locales_dir, "zh-CN.json")
    pat_path = os.path.join(locales_dir, "patterns.json")
    zh_text = load_valid_json_text(zh_path)
    pat_text = load_valid_json_text(pat_path)
    if zh_text is None and os.path.exists(zh_path):
        print("[!] External zh-CN.json could not be parsed (invalid JSON or an encoding problem);")
        print("[!] falling back to the bundled dictionary - your edits were NOT applied.")
    if pat_text is None and os.path.exists(pat_path):
        print("[!] External patterns.json could not be parsed; falling back to the bundled rules.")
    if zh_text is not None:
        try:
            raw_user = json.loads(zh_text)
            if not isinstance(raw_user, dict):
                print("[!] External zh-CN.json is valid JSON but not an object; ignoring it.")
                zh_text = None
                raw_user = {}
            padded = [k for k in raw_user if isinstance(k, str) and k != k.strip()]
            if padded:
                cleaned = {}
                for k, v in raw_user.items():
                    sk = k.strip()
                    if not sk:
                        continue
                    if k == sk or sk not in raw_user:
                        cleaned[sk] = v
                zh_text = json.dumps(cleaned, ensure_ascii=False, indent=2)
                print(f"[*] Normalized {len(padded)} key(s) with leading/trailing whitespace from external zh-CN.json.")
        except Exception:
            pass
    for label, user_text in (("zh-CN.json", zh_text), ("patterns.json", pat_text)):
        if user_text is not None and contains_sentinel_marker(user_text):
            print(f"[!] External {label} contains an engine splice marker; ignoring that file.")
            if label == "zh-CN.json":
                zh_text = None
            else:
                pat_text = None

    if zh_text is not None:
        zh_base = merge_dict_texts(zh_base, zh_text)
    if pat_text is not None:
        pat_base = merge_pattern_texts(pat_base, pat_text)
    return zh_base, pat_base

def contains_sentinel_marker(text):
    """True when the text embeds one of the engine's splice markers.

    The markers are plain comments in the engine source, so a dictionary value
    containing one of them cannot escape a string literal on its own - but the
    *next* splice searches for the markers textually and would then cut the
    engine in the wrong place. Reject such content outright.
    """
    return any(marker in text for marker in (DICT_ZH_SENTINELS + DICT_PATTERNS_SENTINELS))

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
    """Drop editable copies of the shipped dictionaries (never overwrite).

    An existing user file is left exactly as the user left it: the read path
    merges the shipped dictionary with the user's copy, so upstream additions
    reach the client without touching the user's translations.
    """
    zh_base, pat_base = base_dictionary_texts()
    for fname, text in (("zh-CN.json", zh_base), ("patterns.json", pat_base)):
        target = Path(os.path.abspath(os.path.join(locales_dir, fname)))
        if target.exists():
            continue
        try:
            target.write_text(text, encoding="utf-8")
            print(f"[+] Seeded editable dictionary: {target}")
        except Exception as e:
            print(f"[!] Could not seed {target}: {e}")

def apply_patch(install_dir=None, force=False):
    try:
        install_dir, asar_path, bak_path = _resolve_install_dir(install_dir)
    except ValueError as e:
        print(f"[!] Error: {e}")
        return False

    if is_antigravity_running() and not force:
        print("[!] Antigravity appears to be running. Close it first, then run again")
        print("[!] (or pass --force to patch anyway, then restart the client).")
        return False

    lock_path = _acquire_lock(install_dir)
    if lock_path is None:
        print("[!] Another patch/restore operation appears to be in progress")
        print(f"[!] (lock file present in {install_dir}). If no other instance is")
        print("[!] running, remove app.asar.zhlock and try again.")
        return False
    try:
        return _apply_patch_locked(install_dir, asar_path, bak_path, force=force)
    finally:
        _release_lock(lock_path)

def _apply_patch_locked(install_dir, asar_path, bak_path, force=False):

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

    try:
        locales_dir = get_locales_dir()
    except Exception as e:
        print(f"[!] Error: {e}")
        return False
    zh_text, pat_text = resolve_dictionary_texts(locales_dir)
    engine_code = splice_engine_dicts(EMBEDDED_ENGINE_CODE, zh_text, pat_text)

    if current_patched and not force:
        if engine_code in files["dist/preload.js"].decode("utf-8", errors="ignore"):
            print("[*] Antigravity is already patched with the current engine and dictionaries!")
            ensure_backup_sidecar(bak_path)
            seed_locale_files(locales_dir)
            return True
        if not os.path.exists(bak_path):
            print("[!] Dictionaries changed but no official backup exists to re-patch from; keeping current patch.")
            print("[!] The new dictionaries were NOT applied. Restore the official app.asar first, then patch again.")
            return False
        print("[*] Dictionaries/engine changed since last patch; re-patching from official backup...")
        if not backup_matches_sidecar(bak_path):
            print("[!] Backup checksum mismatch - app.asar.bak may have been replaced or modified.")
            print("[!] Refusing to patch from it; keeping the current patch. Run `restore` to re-baseline.")
            return False
        bak_header, bak_files = read_asar(bak_path)
        if "dist/preload.js" not in bak_files:
            print("[!] Error: dist/preload.js missing from backup?!")
            return False
        if compute_build_fingerprint(bak_header, bak_files) != compute_build_fingerprint(header, files):
            print("[!] The official backup belongs to a DIFFERENT client build than the installed app.asar.")
            print("[!] Refusing to rebuild from it - that would roll the client back to an older version.")
            print("[!] Run `restore` to re-baseline the backup, then patch again.")
            return False
        header, files = bak_header, bak_files
    elif current_patched and force:
        if not os.path.exists(bak_path):
            # No clean origin to re-patch from; injecting twice would duplicate
            # the engine, so keep the existing patch instead.
            print("[!] --force requested but no official backup exists; keeping current patch as-is.")
            return False
        print("[*] Current build already patched; re-patching from clean official backup...")
        if not backup_matches_sidecar(bak_path):
            print("[!] Backup checksum mismatch - app.asar.bak may have been replaced or modified.")
            print("[!] Refusing to patch from it; keeping the current patch. Run `restore` to re-baseline.")
            return False
        bak_header, bak_files = read_asar(bak_path)
        if "dist/preload.js" not in bak_files:
            print("[!] Error: dist/preload.js missing from backup?!")
            return False
        if compute_build_fingerprint(bak_header, bak_files) != compute_build_fingerprint(header, files):
            print("[!] The official backup belongs to a DIFFERENT client build than the installed app.asar.")
            print("[!] Refusing to rebuild from it - that would roll the client back to an older version.")
            print("[!] Run `restore` to re-baseline the backup, then patch again.")
            return False
        header, files = bak_header, bak_files
    elif not os.path.exists(bak_path):
        print(f"[*] Creating backup of official app.asar -> {bak_path}...")
        try:
            _atomic_copy2(asar_path, bak_path)
        except Exception as e:
            print(f"[!] Could not create backup: {e}")
            return False
        write_backup_sidecar(asar_path, bak_path)
    else:
        # The current build is an unpatched official archive, which is by
        # definition authoritative: replace a stale (older-version) backup with
        # it. Same size is treated as "same build" to avoid needless copies of
        # multi-hundred-MB archives.
        if file_sha256(asar_path) == file_sha256(bak_path):
            print(f"[*] Official backup already exists at {bak_path}")
        else:
            print("[*] Detected app update: refreshing official backup (existing one was stale)")
            try:
                _atomic_copy2(asar_path, bak_path)
            except Exception as e:
                print(f"[!] Could not refresh backup: {e}")
                return False
            write_backup_sidecar(asar_path, bak_path)

    # A backup created before the sidecar existed never gets one on its own;
    # back-fill it so tamper detection is not permanently disabled.
    ensure_backup_sidecar(bak_path)

    def _decode_target(arc_path):
        # A non-UTF-8 member used to raise an uncaught UnicodeDecodeError and
        # abort with a stack trace. Refuse that file instead; untouched
        # members are simply left as-is because nothing is written yet.
        try:
            return files[arc_path].decode("utf-8")
        except UnicodeDecodeError:
            print(f"[!] {arc_path} is not valid UTF-8; refusing to patch it.")
            return None

    print("[*] Injecting modern localization engine into dist/preload.js...")
    preload_str = _decode_target("dist/preload.js")
    if preload_str is None:
        return False
    new_preload = preload_str.rstrip() + "\n\n" + engine_code + "\n"
    files["dist/preload.js"] = new_preload.encode("utf-8")
    modified = {"dist/preload.js"}

    if "dist/menu.js" in files:
        print("[*] Patching native menus in dist/menu.js...")
        menu_str = _decode_target("dist/menu.js")
        if menu_str is None:
            return False
        files["dist/menu.js"] = patch_menu_js(menu_str).encode("utf-8")
        modified.add("dist/menu.js")

    if "dist/updater.js" in files:
        print("[*] Patching native updater in dist/updater.js...")
        updater_str = _decode_target("dist/updater.js")
        if updater_str is None:
            return False
        files["dist/updater.js"] = patch_updater_js(updater_str).encode("utf-8")
        modified.add("dist/updater.js")

    if "dist/main.js" in files:
        print("[*] Patching native dialogs in dist/main.js...")
        main_str = _decode_target("dist/main.js")
        if main_str is None:
            return False
        files["dist/main.js"] = patch_main_js(main_str).encode("utf-8")
        modified.add("dist/main.js")

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

def restore_backup(install_dir=None, force=False):
    try:
        install_dir, asar_path, bak_path = _resolve_install_dir(install_dir)
    except ValueError as e:
        print(f"[!] Error: {e}")
        return False

    if is_antigravity_running() and not force:
        print("[!] Antigravity appears to be running. Close it first, then run again")
        print("[!] (or pass --force to restore anyway, then restart the client).")
        return False

    if not os.path.exists(bak_path):
        print(f"[!] No backup file found at {bak_path}")
        return False

    lock_path = _acquire_lock(install_dir)
    if lock_path is None:
        print("[!] Another patch/restore operation appears to be in progress")
        print(f"[!] (lock file present in {install_dir}). If no other instance is")
        print("[!] running, remove app.asar.zhlock and try again.")
        return False
    try:
        return _restore_backup_locked(install_dir, asar_path, bak_path, force=force)
    finally:
        _release_lock(lock_path)

def _restore_backup_locked(install_dir, asar_path, bak_path, force=False):
    if os.path.exists(asar_path):
        # Compare the client build, not the file size: the patcher injects the
        # engine, so a patched archive is always larger than its own backup and
        # a size comparison reported a version mismatch on every restore.
        # A mismatched backup used to be restored anyway with only a printed
        # warning, silently rolling the client back to an older version.
        try:
            cur_header, cur_files = read_asar(asar_path)
            bak_header, bak_files = read_asar(bak_path)
            if compute_build_fingerprint(cur_header, cur_files) != compute_build_fingerprint(bak_header, bak_files):
                print("[!] The backup belongs to a DIFFERENT client build than the installed app.asar.")
                print("[!] Refusing to roll the client back to another version.")
                print("[!] If you really want this backup, delete the current app.asar first")
                print("[!] (or pass --force), keeping in mind the client will be downgraded.")
                if not force:
                    return False
        except Exception as e:
            print(f"[!] Could not compare the backup against the installed archive: {e}")
            if not force:
                return False

    if not backup_matches_sidecar(bak_path):
        print("[!] WARNING: backup checksum mismatch - app.asar.bak may have been modified or replaced.")
        if not force:
            print("[!] Refusing to restore a tampered backup; pass --force to proceed anyway.")
            return False
        print("[!] Restoring it anyway as requested (--force).")

    # Keep a timestamped copy of the archive being replaced, so a bad backup
    # never leaves the user with no way back.
    if os.path.exists(asar_path):
        try:
            import datetime
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            pre_path = asar_path + f".pre-restore-{stamp}"
            _atomic_copy2(asar_path, pre_path)
            print(f"[*] Saved pre-restore copy: {pre_path}")
        except Exception as e:
            print(f"[!] Could not save a pre-restore copy: {e}")
            if not force:
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

def update_patch(install_dir=None, force=False):
    """One-command refresh, meant to be re-run after every client update.

    Detects whether the installed client changed since the last patch
    (backup missing or refreshed), re-applies the patch idempotently, and
    prints a short summary of what happened. Safe to run on a schedule:
    when everything is already current it is a read-only no-op.
    """
    try:
        install_dir, asar_path, bak_path = _resolve_install_dir(install_dir)
    except ValueError as e:
        print(f"[!] Error: {e}")
        return False

    had_backup = os.path.exists(bak_path)
    bak_sha_before = file_sha256(bak_path) if had_backup else None
    patched_before = False
    if os.path.exists(asar_path):
        try:
            _, before_files = read_asar(asar_path)
            patched_before = SIGNATURE_PRELOAD in before_files.get(
                "dist/preload.js", b"").decode("utf-8", errors="ignore")
        except Exception:
            pass

    print("[*] update: checking installed client against backup...")
    if not apply_patch(install_dir, force=force):
        return False

    bak_sha_after = file_sha256(bak_path) if os.path.exists(bak_path) else None
    if not had_backup and bak_sha_after:
        print("[*] update: no backup existed; created one from the installed client.")
    elif bak_sha_before != bak_sha_after:
        print("[*] update: client update detected; official backup refreshed and patch re-applied.")
        print("[*] update: if the new client added English UI, run the extractor + localize pipeline")
        print("           (or press Ctrl+Alt+L in the client) to collect the new strings.")
    elif not patched_before:
        print("[*] update: patch applied to the installed client.")
    else:
        print("[*] update: already current; nothing to do.")
    return True

def run_watch(install_dir=None, interval_s=1800, iterations=None):
    """Resident watcher: re-patch whenever the installed app.asar changes.

    Each round is just apply_patch(), which is idempotent: an unchanged
    client is a read-only no-op, and a round is skipped while the client is
    running (patching a live client is refused without --force). `iterations`
    bounds the loop for tests; the CLI runs forever until Ctrl+C.
    """
    if interval_s < 60:
        print(f"[!] Interval {interval_s}s is too short; using 60s minimum.")
        interval_s = 60
    print(f"[*] watch: checking every {interval_s}s (Ctrl+C to stop)...")
    count = 0
    try:
        while True:
            count += 1
            print(f"[*] watch: round {count} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            try:
                if is_antigravity_running():
                    print("[*] watch: client is running; skipping this round.")
                elif not apply_patch(install_dir):
                    print("[!] watch: round failed (see above); will retry next round.")
            except Exception as e:
                print(f"[!] watch: round failed with {e!r}; will retry next round.")
            if iterations is not None and count >= iterations:
                break
            time.sleep(interval_s)
    except KeyboardInterrupt:
        print("[*] watch: stopped.")
    return True

def show_status(install_dir=None):
    print("=== Antigravity Localization Status ===")
    print(f"Platform:    {sys.platform}")
    try:
        install_dir, asar_path, bak_path = _resolve_install_dir(install_dir)
    except ValueError as e:
        print(f"Install Dir: {install_dir}")
        print(f"Status: Not installed or not found ({e}).")
        return False
    print(f"Install Dir: {install_dir}")
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
    parser = argparse.ArgumentParser(description="Antigravity Modern Chinese Localization Patcher v1.0.6")
    parser.add_argument("action", nargs="?", default="patch", choices=["patch", "restore", "status", "update", "watch"], help="Action to perform (default: patch)")
    parser.add_argument("--dir", help="Custom Antigravity installation directory (must contain app.asar or a resources/app.asar; symlinked app.asar is refused)")
    parser.add_argument("--force", action="store_true", help="Force re-patching even if already patched; also bypasses the running-client, version-mismatch and tampered-backup guards (the client must be restarted afterwards)")
    parser.add_argument("--interval", type=int, default=1800, help="Watch interval in seconds (watch only, minimum 60)")

    args = parser.parse_args()

    if args.action == "patch":
        ok = apply_patch(args.dir, force=args.force)
    elif args.action == "restore":
        ok = restore_backup(args.dir, force=args.force)
    elif args.action == "update":
        ok = update_patch(args.dir, force=args.force)
    elif args.action == "watch":
        ok = run_watch(args.dir, interval_s=args.interval)
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

# Module-level twin of the helper inside PATCHER_TEMPLATE (that copy is what
# ships inside scripts/patcher.py). Keep both in sync.
def contains_sentinel_marker(text):
    """True when the text embeds one of the engine's splice markers."""
    markers = ("/*AG_ZH_ZH_START*/", "/*AG_ZH_ZH_END*/",
               "/*AG_ZH_PATTERNS_START*/", "/*AG_ZH_PATTERNS_END*/")
    return any(marker in text for marker in markers)

def build(compile_exe=True):
    print("=" * 60)
    print("  Antigravity-ZH Toolkit Builder (v1.0.6)")
    print("=" * 60)

    template_path = os.path.join(ENGINE_DIR, "engine_template.js")
    zh_path = os.path.join(LOCALES_DIR, "zh-CN.json")
    pat_path = os.path.join(LOCALES_DIR, "patterns.json")

    print("[1/3] Loading locales and building ag_localization_engine.js...")
    zh_json_str = Path(zh_path).read_text(encoding="utf-8-sig")
    pat_json_str = Path(pat_path).read_text(encoding="utf-8-sig")
    template = Path(template_path).read_text(encoding="utf-8")
    # Fail fast on broken dictionary sources before generating anything.
    # utf-8-sig matches the patcher/LSP tooling: a BOM saved by Windows
    # Notepad must not break the release build while patching accepts it.
    zh_obj = json.loads(zh_json_str)
    pat_obj = json.loads(pat_json_str)
    if not isinstance(zh_obj, dict):
        raise SystemExit(
            "[!] locales/zh-CN.json must be a JSON object (string keys to string values), "
            f"got {type(zh_obj).__name__}."
        )
    if not isinstance(pat_obj, list):
        raise SystemExit(
            "[!] locales/patterns.json must be a JSON list of rule objects, "
            f"got {type(pat_obj).__name__}."
        )

    # The engine looks entries up by the *trimmed* UI text, so a key with
    # leading/trailing whitespace can never match anything. Reject it here
    # instead of shipping a silently dead entry.
    padded_keys = [k for k in zh_obj if k != k.strip()]
    if padded_keys:
        preview = ", ".join(repr(k) for k in padded_keys[:5])
        raise SystemExit(
            f"[!] locales/zh-CN.json has {len(padded_keys)} key(s) with leading/trailing "
            f"whitespace - they can never match because the engine trims the UI text "
            f"before looking it up.\n    {preview}\n"
            f"[!] Fix the keys (or move the variable part into locales/patterns.json) and rebuild."
        )

    # A dictionary value carrying a splice marker would make the next splice cut
    # the engine in the wrong place.
    for label, text in (("zh-CN.json", zh_json_str), ("patterns.json", pat_json_str)):
        if contains_sentinel_marker(text):
            raise SystemExit(
                f"[!] locales/{label} contains an engine splice marker "
                f"(AG_ZH_ZH_START/END, AG_ZH_PATTERNS_START/END).\n"
                f"[!] That marker would break the engine splice - remove it and rebuild."
            )

    # A non-string dictionary value would crash the empty-value check below
    # with AttributeError; report it by name instead.
    non_string_values = {k: type(v).__name__ for k, v in zh_obj.items()
                         if not isinstance(v, str)}
    if non_string_values:
        preview = ", ".join(f"{k!r} ({t})" for k, t in list(non_string_values.items())[:5])
        raise SystemExit(
            f"[!] locales/zh-CN.json has {len(non_string_values)} entry/entries with a non-string "
            f"translation - every value must be a string.\n    {preview}\n"
            f"[!] Fix them or remove them and rebuild."
        )

    # An empty translation would blank out the UI text it belongs to.
    empty_values = [k for k, v in zh_obj.items() if not v.strip()]
    if empty_values:
        preview = ", ".join(repr(k) for k in empty_values[:5])
        raise SystemExit(
            f"[!] locales/zh-CN.json has {len(empty_values)} entry/entries with an empty "
            f"translation - the engine would render an empty label.\n    {preview}\n"
            f"[!] Fill them in or remove them and rebuild."
        )

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
                print("[+] Copied to repo root.")
            except Exception as e:
                print(f"[!] Could not copy the binary to the repo root: {e}")

            if not is_win:
                try:
                    os.chmod(output_bin, 0o755)
                    os.chmod(os.path.join(REPO_ROOT, binary_name), 0o755)
                except Exception:
                    pass

            print("\n" + "=" * 60)
            print(f"  [+] Build Succeeded!")
            print(f"  [+] Binary: {output_bin}")
            print("=" * 60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[!] Compilation failed: {e}")
            return False
    else:
        print("[+] Engine and patcher updated (skipping executable compilation).")
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity-ZH Builder v1.0.6")
    parser.add_argument("--no-exe", action="store_true", help="Skip PyInstaller compilation")
    args = parser.parse_args()
    # The exit code has to reflect the build result: CI uses it to decide
    # whether a release may be published.
    raise SystemExit(0 if build(compile_exe=not args.no_exe) else 1)
