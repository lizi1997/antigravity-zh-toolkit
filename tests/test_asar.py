"""ASAR read/write round-trip and patcher behaviour tests.

Builds fake ASAR archives with an independent minimal builder (kept separate
from scripts/patcher.py on purpose) and validates the patcher against them.
All paths used here are derived from pytest's tmp_path fixture.
"""

import hashlib
import json
import os
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
    assert not os.path.exists(str(p) + ".zh_tmp")


def test_inplace_fallback_when_replace_denied(tmp_path, monkeypatch):
    """When the target is locked (Windows), the writer falls back to r+b rewrite."""
    p = (tmp_path / "app.asar").resolve()
    build_asar(p, [("a.js", b"AAA")])
    header, files = patcher.read_asar(str(p))
    files["a.js"] = b"BBBB"

    def denied(src, dst):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(os, "replace", denied)
    patcher.write_asar_inplace(str(p), header, files, modified={"a.js"})

    _, files2 = patcher.read_asar(str(p))
    assert files2["a.js"] == b"BBBB"
    assert not os.path.exists(str(p) + ".zh_tmp")


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
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True
    os.remove(asar + ".bak")

    assert patcher.apply_patch(install_dir, force=True) is True
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


def test_patch_seeds_locale_files(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    zh_path = locales_dir / "zh-CN.json"
    pat_path = locales_dir / "patterns.json"
    assert zh_path.exists() and pat_path.exists()
    seeded_zh = json.loads(zh_path.read_text(encoding="utf-8"))
    assert len(seeded_zh) > 1000


def test_patch_menu_uses_conservative_first_occurrence():
    body = (
        "addItemToSubmenu(menu, 'File', a); addItemToSubmenu(menu, 'File', b); "
        "label: 'New Window'"
    )
    patched = patcher.patch_menu_js(body)
    assert patched.count("addItemToSubmenu(menu, '文件 (File)'") == 1
    assert patched.count("addItemToSubmenu(menu, 'File'") == 1  # second call untouched
    assert "新建窗口 (New Window)" in patched
