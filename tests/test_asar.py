"""ASAR read/write round-trip and patcher behaviour tests.

Builds fake ASAR archives with an independent minimal builder (kept separate
from scripts/patcher.py on purpose) and validates the patcher against them.
All paths used here are derived from pytest's tmp_path fixture.
"""

import hashlib
import json
import os
import re
import struct
from pathlib import Path

import pytest

import patcher  # via tests/conftest.py

BLOCK = 4194304

MENU_BODY = (
    "addItemToSubmenu(menu, 'File', item1); addItemToSubmenu(menu, 'File', item2); "
    "addItemToSubmenu(menu, 'Help', item3); label: 'New Window' label: 'Docs'"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def chunk_hashes(data):
    return [sha(data[i:i + BLOCK]) for i in range(0, len(data), BLOCK)]


def build_asar(path, spec):
    """Independent minimal ASAR builder. spec: list of (archive_path, bytes)."""
    path = Path(path).resolve()
    header = {"files": {}}
    blob = b""
    for name, data in spec:
        node = header["files"]
        parts = name.split("/")
        for p in parts[:-1]:
            node = node.setdefault(p, {"files": {}})["files"]
        entry = {
            "size": len(data),
            "integrity": {
                "algorithm": "SHA256",
                "hash": sha(data),
                "blockSize": BLOCK,
                "blocks": chunk_hashes(data),
            },
        }
        if data:
            entry["offset"] = str(len(blob))
        node[parts[-1]] = entry
        blob += data

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    unpadded = len(header_bytes)
    pad = (4 - (unpadded % 4)) % 4
    header_bytes += b"\x00" * pad
    payload = struct.pack("<IIII", 4, 8 + len(header_bytes), 4 + len(header_bytes), unpadded)
    payload += header_bytes
    payload += blob
    path.write_bytes(payload)


def make_fake_app(path, preload_body, menu_body=MENU_BODY, extra=None):
    spec = [
        ("dist/preload.js", preload_body.encode("utf-8")),
        ("package.json", b'{"name":"antigravity","version":"9.9.9"}'),
    ]
    if menu_body is not None:
        spec.append(("dist/menu.js", menu_body.encode("utf-8")))
    if extra:
        spec.extend(extra)
    build_asar(path, spec)


@pytest.fixture
def locales_dir(tmp_path, monkeypatch):
    ld = tmp_path / "locales"
    ld.mkdir()
    monkeypatch.setattr(patcher, "get_locales_dir", lambda: str(ld))
    return ld


@pytest.fixture
def install_dir(tmp_path):
    d = tmp_path / "Antigravity"
    d.mkdir()
    return str(d)


def asar_path_for(install_dir):
    return os.path.abspath(os.path.join(install_dir, "app.asar"))


# ---------------------------------------------------------------------------
# Reader / writer round-trip
# ---------------------------------------------------------------------------

def test_read_roundtrip(tmp_path):
    p = tmp_path / "app.asar"
    spec = [
        ("dist/preload.js", b"console.log('preload');"),
        ("dist/menu.js", b"module.exports = {};"),
        ("assets/config.json", b'{"a":1}'),
        ("assets/empty.txt", b""),
    ]
    build_asar(p, spec)
    header, files = patcher.read_asar(str(p))
    assert files["dist/preload.js"] == b"console.log('preload');"
    assert files["assets/config.json"] == b'{"a":1}'
    assert "assets/empty.txt" not in files  # zero-size entries carry no offset
    assert header["files"]["dist"]["files"]["preload.js"]["size"] == len(b"console.log('preload');")


def test_write_offsets_shift_after_growth(tmp_path):
    p = tmp_path / "app.asar"
    build_asar(p, [
        ("a.js", b"AAA"),
        ("b.js", b"BBB"),
        ("c/c.js", b"CCC"),
    ])
    header, files = patcher.read_asar(str(p))
    old_offsets = {
        "a.js": int(header["files"]["a.js"]["offset"]),
        "b.js": int(header["files"]["b.js"]["offset"]),
        "c/c.js": int(header["files"]["c"]["files"]["c.js"]["offset"]),
    }
    files["a.js"] = b"A" * 100
    patcher.write_asar_inplace(str(p), header, files, modified={"a.js"})

    header2, files2 = patcher.read_asar(str(p))
    assert files2["a.js"] == b"A" * 100
    assert files2["b.js"] == b"BBB"
    assert files2["c/c.js"] == b"CCC"
    assert int(header2["files"]["b.js"]["offset"]) == old_offsets["b.js"] + 97
    assert int(header2["files"]["c"]["files"]["c.js"]["offset"]) == old_offsets["c/c.js"] + 97


def test_unmodified_integrity_preserved(tmp_path):
    p = tmp_path / "app.asar"
    big = bytes(range(256)) * 21000  # ~5.14 MB -> 2 blocks
    small = b"tiny"
    build_asar(p, [("small.txt", small), ("big.bin", big)])
    header, files = patcher.read_asar(str(p))
    original_integrity = json.loads(json.dumps(header["files"]["big.bin"]["integrity"]))

    files["small.txt"] = b"tiny-but-longer"
    patcher.write_asar_inplace(str(p), header, files, modified={"small.txt"})

    header2, files2 = patcher.read_asar(str(p))
    assert files2["big.bin"] == big
    # Untouched file keeps its original (multi-block) integrity metadata verbatim.
    assert header2["files"]["big.bin"]["integrity"] == original_integrity
    assert len(original_integrity["blocks"]) == 2


def test_modified_big_file_gets_chunked_integrity(tmp_path):
    p = tmp_path / "app.asar"
    big = bytes(range(256)) * 21000
    build_asar(p, [("big.bin", big)])
    header, files = patcher.read_asar(str(p))

    new_big = big + b"tail"
    files["big.bin"] = new_big
    patcher.write_asar_inplace(str(p), header, files, modified={"big.bin"})

    header2, files2 = patcher.read_asar(str(p))
    integrity = header2["files"]["big.bin"]["integrity"]
    assert integrity["hash"] == sha(new_big)
    assert integrity["blocks"] == chunk_hashes(new_big)
    assert len(integrity["blocks"]) == 2


def test_default_modified_recomputes_all(tmp_path):
    """modified=None (restore / scratch semantics) recomputes every integrity."""
    p = tmp_path / "app.asar"
    big = bytes(range(256)) * 21000
    build_asar(p, [("big.bin", big), ("x.txt", b"x")])
    header, files = patcher.read_asar(str(p))
    files["x.txt"] = b"yy"
    patcher.write_asar_inplace(str(p), header, files)  # no modified set

    header2, _ = patcher.read_asar(str(p))
    assert header2["files"]["big.bin"]["integrity"] == {
        "algorithm": "SHA256",
        "hash": sha(big),
        "blockSize": BLOCK,
        "blocks": chunk_hashes(big),
    }


def test_no_tmp_file_left_behind(tmp_path):
    p = tmp_path / "app.asar"
    build_asar(p, [("a.js", b"AAA")])
    header, files = patcher.read_asar(str(p))
    files["a.js"] = b"BBBB"
    patcher.write_asar_inplace(str(p), header, files, modified={"a.js"})
    assert list(tmp_path.glob("*.zh_tmp_*")) == []


def test_atomic_replace_failure_preserves_original(tmp_path, monkeypatch):
    """A locked target must fail without rewriting or corrupting app.asar."""
    p = (tmp_path / "app.asar").resolve()
    build_asar(p, [("a.js", b"AAA")])
    original = p.read_bytes()
    header, files = patcher.read_asar(str(p))
    files["a.js"] = b"BBBB"

    def denied(src, dst):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(os, "replace", denied)
    with pytest.raises(PermissionError, match="Close Antigravity"):
        patcher.write_asar_inplace(str(p), header, files, modified={"a.js"})

    assert p.read_bytes() == original
    assert list(tmp_path.glob("*.zh_tmp_*")) == []


# ---------------------------------------------------------------------------
# Dictionary splicing helpers
# ---------------------------------------------------------------------------

def test_splice_engine_dicts_swaps_content():
    engine = (
        "const EMBEDDED_TRANSLATIONS = /*AG_ZH_ZH_START*/{\"Old\": \"旧\"}/*AG_ZH_ZH_END*/;\n"
        "const EMBEDDED_PATTERNS = /*AG_ZH_PATTERNS_START*/[1]/*AG_ZH_PATTERNS_END*/;\n"
    )
    spliced = patcher.splice_engine_dicts(engine, '{"New": "新"}', "[2]")
    assert '"New": "新"' in spliced
    assert '"Old"' not in spliced
    assert "[2]" in spliced
    assert "[1]" not in spliced


def test_splice_engine_dicts_missing_sentinels_falls_back():
    engine = "const EMBEDDED_TRANSLATIONS = {}; "
    assert patcher.splice_engine_dicts(engine, '{"New": "新"}', "[2]") == engine


def test_load_valid_json_text_rejects_garbage(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    good = tmp_path / "good.json"
    good.write_text('{"ok": 1}', encoding="utf-8")
    assert patcher.load_valid_json_text(str(bad)) is None
    assert patcher.load_valid_json_text(str(good)) == '{"ok": 1}'
    missing = tmp_path / "missing.json"
    assert patcher.load_valid_json_text(str(missing)) is None


# ---------------------------------------------------------------------------
# C1: signature-aware patch source selection
# ---------------------------------------------------------------------------

def test_c1_stale_backup_refresh(install_dir, locales_dir):
    """App updated + stale backup: patch must use the CURRENT archive and
    refresh the backup instead of silently rolling the client back."""
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v2 official');")
    # Stale v1 backup: different (shorter) content, also unpatched.
    stale_bak = os.path.abspath(os.path.join(install_dir, "stale.asar"))
    make_fake_app(stale_bak, "console.log('v1');")
    os.replace(stale_bak, asar + ".bak")

    assert patcher.apply_patch(install_dir) is True

    header, files = patcher.read_asar(asar)
    preload = files["dist/preload.js"].decode("utf-8")
    assert "v2 official" in preload
    assert preload.count(patcher.SIGNATURE_PRELOAD) == 1
    assert "console.log('v1');" not in preload

    # Backup was refreshed to the CURRENT official build (unpatched v2).
    _, bak_files = patcher.read_asar(asar + ".bak")
    bak_preload = bak_files["dist/preload.js"].decode("utf-8")
    assert "v2 official" in bak_preload
    assert patcher.SIGNATURE_PRELOAD not in bak_preload


def test_c1_same_size_stale_backup_refresh(install_dir, locales_dir):
    """Equal file sizes must not make a stale backup look current."""
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v2');")
    stale_bak = os.path.abspath(os.path.join(install_dir, "stale.asar"))
    make_fake_app(stale_bak, "console.log('v1');")
    assert os.path.getsize(asar) == os.path.getsize(stale_bak)
    os.replace(stale_bak, asar + ".bak")

    assert patcher.apply_patch(install_dir) is True

    _, files = patcher.read_asar(asar)
    assert "console.log('v2');" in files["dist/preload.js"].decode("utf-8")
    _, backup_files = patcher.read_asar(asar + ".bak")
    assert backup_files["dist/preload.js"] == b"console.log('v2');"


@pytest.mark.parametrize("action", ["patch", "restore"])
def test_cli_failure_returns_nonzero(monkeypatch, action):
    monkeypatch.setattr(patcher.sys, "argv", ["patcher.py", action, "--dir", "missing-dir"])
    with pytest.raises(SystemExit) as exc:
        patcher.main()
    assert exc.value.code == 1


def test_c1_force_repatches_from_backup_exactly_once(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")

    assert patcher.apply_patch(install_dir) is True
    assert patcher.apply_patch(install_dir, force=True) is True

    _, files = patcher.read_asar(asar)
    preload = files["dist/preload.js"].decode("utf-8")
    assert "v1 official" in preload
    assert preload.count(patcher.SIGNATURE_PRELOAD) == 1


def test_c1_rerun_without_changes_is_noop(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")

    assert patcher.apply_patch(install_dir) is True
    before = Path(asar).read_bytes()
    assert patcher.apply_patch(install_dir) is True
    after = Path(asar).read_bytes()
    assert before == after


def test_c1_force_without_backup_keeps_existing_patch(install_dir, locales_dir):
    """--force without a clean baseline must REFUSE (and report failure).

    The exit code is what install.bat / install.sh propagate, so returning
    True here made a failed dictionary update look like a success.
    """
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True
    os.remove(asar + ".bak")

    assert patcher.apply_patch(install_dir, force=True) is False
    _, files = patcher.read_asar(asar)
    preload = files["dist/preload.js"].decode("utf-8")
    assert preload.count(patcher.SIGNATURE_PRELOAD) == 1  # no double injection


def test_c1_dictionary_update_triggers_repatch(install_dir, locales_dir):
    """Editing the external dictionary then re-running plain `patch` applies it."""
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    zh_path = locales_dir / "zh-CN.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    zh["BrandNewTestKey"] = "全新测试词条"
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")

    assert patcher.apply_patch(install_dir) is True
    _, files = patcher.read_asar(asar)
    preload = files["dist/preload.js"].decode("utf-8")
    assert "BrandNewTestKey" in preload
    assert preload.count(patcher.SIGNATURE_PRELOAD) == 1


def test_c1_invalid_external_dict_falls_back_to_embedded(install_dir, locales_dir, capsys):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    (locales_dir / "zh-CN.json").write_text("{ broken json !!", encoding="utf-8")
    pat = locales_dir / "patterns.json"
    if pat.exists():
        pat.unlink()

    assert patcher.apply_patch(install_dir) is True
    out = capsys.readouterr().out
    assert "invalid JSON" in out
    _, files = patcher.read_asar(asar)
    preload = files["dist/preload.js"].decode("utf-8")
    assert '"Configure the browser subagent. It requires"' in preload  # embedded dict


# ---------------------------------------------------------------------------
# Backup checksum sidecar (.bak.sha256)
# ---------------------------------------------------------------------------

def read_sidecar(install_dir):
    return Path(asar_path_for(install_dir) + ".bak.sha256").read_text(encoding="utf-8").strip()


def test_backup_sidecar_written_on_first_patch(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True
    assert read_sidecar(install_dir) == patcher.file_sha256(asar + ".bak")

    # A legitimate dictionary change still re-patches from the verified backup.
    zh_path = locales_dir / "zh-CN.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    zh["SidecarHappyPath"] = "正常路径"
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")
    assert patcher.apply_patch(install_dir) is True
    _, files = patcher.read_asar(asar)
    assert "SidecarHappyPath" in files["dist/preload.js"].decode("utf-8")


def test_repatch_refuses_tampered_backup(install_dir, locales_dir, capsys):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    # Swap the backup's preload for foreign content behind the tool's back.
    tampered = "console.log('tampered preload');"
    header, files = patcher.read_asar(asar + ".bak")
    files["dist/preload.js"] = tampered.encode("utf-8")
    patcher.write_asar_inplace(asar + ".bak", header, files)

    # Dictionary change triggers the re-patch-from-backup path; the sidecar
    # mismatch must keep the current patch instead of injecting bak content.
    zh_path = locales_dir / "zh-CN.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    zh["SidecarTampered"] = "备份被篡改"
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")

    assert patcher.apply_patch(install_dir) is False
    assert "checksum mismatch" in capsys.readouterr().out
    _, files = patcher.read_asar(asar)
    preload = files["dist/preload.js"].decode("utf-8")
    assert "tampered preload" not in preload
    assert preload.count(patcher.SIGNATURE_PRELOAD) == 1


def test_restore_warns_on_checksum_mismatch(install_dir, locales_dir, capsys):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    bak = asar + ".bak"
    header, files = patcher.read_asar(bak)
    files["dist/preload.js"] = b"console.log('replaced backup');"
    patcher.write_asar_inplace(bak, header, files)

    # A tampered backup is refused by default: warn loudly and leave the
    # installed archive untouched.
    assert patcher.restore_backup(install_dir) is False
    assert "checksum mismatch" in capsys.readouterr().out
    _, files = patcher.read_asar(asar)
    assert b"replaced backup" not in files["dist/preload.js"]

    # The user's explicit --force still restores it, with a warning.
    assert patcher.restore_backup(install_dir, force=True) is True
    assert "checksum mismatch" in capsys.readouterr().out
    _, files = patcher.read_asar(asar)
    assert files["dist/preload.js"] == b"console.log('replaced backup');"


def test_legacy_backup_without_sidecar_still_repatches(install_dir, locales_dir):
    """Backups created before the sidecar existed must keep working - and the
    missing sidecar must be back-filled, otherwise tamper detection stays
    disabled forever for every pre-sidecar installation."""
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True
    os.remove(asar + ".bak.sha256")

    zh_path = locales_dir / "zh-CN.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    zh["LegacyBackup"] = "旧版备份"
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")

    assert patcher.apply_patch(install_dir) is True
    _, files = patcher.read_asar(asar)
    assert "LegacyBackup" in files["dist/preload.js"].decode("utf-8")

    # F-05: the sidecar is repaired instead of staying missing forever.
    sidecar = Path(asar + ".bak.sha256")
    assert sidecar.exists()
    assert sidecar.read_text(encoding="utf-8").strip() == patcher.file_sha256(asar + ".bak")


def test_backup_from_another_build_is_refused(install_dir, locales_dir, capsys):
    """A backup that belongs to a different client build must not be used to
    rebuild the archive - that would silently roll the client back."""
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    # Replace the backup with an archive of a different build. The difference
    # lives in a file the patcher never touches, so it shows up in the build
    # fingerprint.
    other = os.path.abspath(os.path.join(install_dir, "other.asar"))
    make_fake_app(other, "console.log('v2 official');",
                  extra=[("assets/build-info.json", b'{"build": 2}')])
    os.replace(other, asar + ".bak")
    os.remove(asar + ".bak.sha256")

    # Force the re-patch-from-backup path with a dictionary change.
    zh_path = locales_dir / "zh-CN.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    zh["OtherBuildKey"] = "其他构建"
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")

    assert patcher.apply_patch(install_dir) is False
    assert "DIFFERENT client build" in capsys.readouterr().out
    _, files = patcher.read_asar(asar)
    assert "OtherBuildKey" not in files["dist/preload.js"].decode("utf-8")


def test_patch_seeds_locale_files(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    zh_path = locales_dir / "zh-CN.json"
    pat_path = locales_dir / "patterns.json"
    assert zh_path.exists() and pat_path.exists()
    seeded_zh = json.loads(zh_path.read_text(encoding="utf-8"))
    assert len(seeded_zh) > 1000


class _Submenu:
    """Minimal stand-in for Electron's MenuItem submenu."""

    def __init__(self):
        self.items = []

    def insert(self, position, item):
        self.items.insert(position, item)


def electron_default_menu():
    """Electron's default application menu.

    The 'fileMenu' role carries the label 'File'
    (electron/lib/browser/api/menu-item-roles.ts); the base menu is built by
    Electron, so the patcher can neither rename nor know about it.
    """
    return {"items": [{"label": "File", "submenu": _Submenu()}]}


def add_item_to_submenu(app_menu, submenu_label, position, item):
    """Verbatim port of the client's addItemToSubmenu() (dist/menu.js)."""
    for entry in app_menu["items"]:
        if entry["label"] == submenu_label:
            if entry.get("submenu") is None:
                return
            entry["submenu"].insert(position, item)
            return


def test_patch_menu_keeps_submenu_lookup_key():
    """The submenu lookup key must stay 'File'.

    addItemToSubmenu() resolves a submenu by `item.label === submenuLabel`,
    and the base menu label belongs to Electron - rewriting the lookup key
    makes the lookup fail and silently drops the menu item.
    """
    body = (
        "addItemToSubmenu(menu, 'File', 0, a); addItemToSubmenu(menu, 'File', 1, b); "
        "label: 'New Window'"
    )
    patched = patcher.patch_menu_js(body)
    assert "addItemToSubmenu(menu, 'File'" in patched
    assert "文件 (File)" not in patched
    assert "新建窗口 (New Window)" in patched


def test_patched_menu_item_really_lands_in_the_file_submenu():
    """Effect-level check: after patching, the New Window item must actually
    be inserted into Electron's File submenu."""
    body = "addItemToSubmenu(menu, 'File', 0, new MenuItem({ label: 'New Window' }));"
    patched = patcher.patch_menu_js(body)

    key = re.search(r"addItemToSubmenu\(menu, '([^']+)'", patched).group(1)
    label = re.search(r"label: '([^']+)'", patched).group(1)

    menu = electron_default_menu()
    add_item_to_submenu(menu, key, 0, {"label": label})

    assert key == "File"
    assert menu["items"][0]["submenu"].items == [{"label": "新建窗口 (New Window)"}]


def test_patch_updater_dialogs():
    body = "const options = { title: 'Check for Updates', message: 'No updates available' };"
    patched = patcher.patch_updater_js(body)
    assert "title: '检查更新'" in patched
    assert "message: '当前已是最新版本'" in patched


def test_patch_main_dialogs():
    body = "const options = { title: 'Confirm Quit', message: 'Are you sure you want to quit?', detail: 'There may be agents or background tasks running.', buttons: ['Cancel', 'Quit'] };"
    patched = patcher.patch_main_js(body)
    assert "title: '确认退出'" in patched
    assert "message: '确定要退出吗？'" in patched
    assert "detail: '可能有正在运行的智能体或后台任务。'" in patched
    assert "buttons: ['取消', '退出']" in patched


def test_updater_and_main_patches_report_misses(capsys):
    """A changed client UI must not fail silently.

    Only the menu patch used to report unmatched replacements, so a client
    update could break the updater/dialog localization with no hint at all.
    """
    patcher.patch_updater_js("const x = 1;")
    out = capsys.readouterr().out
    assert "MISS" in out
    assert "not found" in out

    patcher.patch_main_js("const y = 2;")
    out = capsys.readouterr().out
    assert "MISS" in out
    assert "not found" in out


def test_replacement_log_distinguishes_hits_from_replacements(capsys):
    """The log must show how many occurrences were really rewritten.

    Reporting only the hit count made a capped replacement look like a full
    one ("hit x3" while only the first occurrence was changed).
    """
    out, replaced, missed = patcher.apply_literal_replacements(
        "aaa bbb aaa", [[("aaa", "x", 1)], [("zzz", "y", -1)]], "Test")
    assert out == "x bbb aaa"
    assert replaced == 1
    assert missed == 1
    log = capsys.readouterr().out
    assert "hit x2, replaced x1" in log
    assert "MISS" in log


def test_alternative_spellings_do_not_report_a_false_miss(capsys):
    """Single- and double-quoted forms of the same string are alternatives.

    A client that only uses one of them must not be reported as a miss.
    """
    body = "const options = { title: 'Check for Updates', message: 'No updates available' };"
    patcher.patch_updater_js(body)
    out = capsys.readouterr().out
    assert "MISS" not in out
    assert "not found" not in out
    assert "hit x1, replaced x1" in out


def test_cli_refused_patch_returns_nonzero(install_dir, locales_dir, monkeypatch):
    """A refused patch must exit non-zero.

    install.bat / install.sh propagate this code, so a silent 0 would hide a
    dictionary update that never reached the client.
    """
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    # Change the dictionary so the tool wants to re-patch, then remove the
    # clean baseline it would have to rebuild from.
    zh_path = locales_dir / "zh-CN.json"
    zh = json.loads(zh_path.read_text(encoding="utf-8"))
    zh["CliRefusedKey"] = "命令行拒绝"
    zh_path.write_text(json.dumps(zh, ensure_ascii=False, indent=2), encoding="utf-8")
    os.remove(asar + ".bak")

    monkeypatch.setattr(patcher.sys, "argv", ["patcher.py", "patch", "--dir", install_dir])
    with pytest.raises(SystemExit) as exc:
        patcher.main()
    assert exc.value.code == 1

    _, files = patcher.read_asar(asar)
    assert "CliRefusedKey" not in files["dist/preload.js"].decode("utf-8")


def test_write_asar_directory_permission_denied_does_not_hang(tmp_path, monkeypatch):
    """Regression: on Windows, stdlib tempfile.mkstemp() retries 2^31 times
    when NTFS ACLs / sandboxes deny os.open() while os.access(dir, W_OK) is
    True. write_asar_inplace must fail on the first attempt instead."""
    p = (tmp_path / "app.asar").resolve()
    build_asar(p, [("a.js", b"AAA")])
    header, files = patcher.read_asar(str(p))
    files["a.js"] = b"BBBB"

    attempts = []
    real_open = patcher.os.open

    def deny_tmp_open(target, flags, *args):
        if ".zh_tmp_" in str(target):
            attempts.append(target)
            raise PermissionError(13, "Permission denied")
        return real_open(target, flags, *args)

    monkeypatch.setattr(patcher.os, "open", deny_tmp_open)

    with pytest.raises(PermissionError):
        patcher.write_asar_inplace(str(p), header, files, modified={"a.js"})

    assert len(attempts) == 1


