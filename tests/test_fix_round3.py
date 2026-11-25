"""Regression tests for the round-3 audit fixes.

Covers: running-client guard, cross-build restore refusal, tampered-backup
refusal, malformed-dictionary fallback, non-UTF-8 member refusal, atomic
backup + lock, file-mode preservation, --dir validation, APPDATA fallback,
engine hardening markers, sentinel parity between build.py and patcher.py.
"""

import io
import json
import os
import struct
import sys
import zipfile
import zlib
from pathlib import Path

import pytest

import build as build_mod
import patcher
from test_asar import asar_path_for, build_asar, make_fake_app  # noqa: F401


@pytest.fixture
def install_dir(tmp_path):
    d = tmp_path / "Antigravity"
    d.mkdir()
    return str(d)


@pytest.fixture
def locales_dir(tmp_path, monkeypatch):
    ld = tmp_path / "locales"
    ld.mkdir()
    monkeypatch.setattr(patcher, "get_locales_dir", lambda: str(ld))
    return ld


# --- running-client guard --------------------------------------------------------

def test_patch_refuses_when_client_running(install_dir, locales_dir, monkeypatch, capsys):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    monkeypatch.setattr(patcher, "is_antigravity_running", lambda: True)
    assert patcher.apply_patch(install_dir) is False
    assert "running" in capsys.readouterr().out
    # The archive must be untouched: no backup was even created.
    assert not os.path.exists(asar + ".bak")


def test_patch_force_bypasses_running_guard(install_dir, locales_dir, monkeypatch):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    monkeypatch.setattr(patcher, "is_antigravity_running", lambda: True)
    assert patcher.apply_patch(install_dir, force=True) is True


def test_restore_refuses_when_client_running(install_dir, locales_dir, monkeypatch):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True
    monkeypatch.setattr(patcher, "is_antigravity_running", lambda: True)
    assert patcher.restore_backup(install_dir) is False


# --- cross-build restore refusal (B-01) ------------------------------------------

def test_restore_refuses_other_build_without_force(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True

    # Rewrite the installed archive as a *different* build (extra member).
    make_fake_app(
        asar, "console.log('v2 official');",
        extra=[("dist/extra.js", b"console.log('new in v2');")],
    )
    before = Path(asar).read_bytes()
    assert patcher.restore_backup(install_dir) is False
    assert Path(asar).read_bytes() == before  # untouched

    assert patcher.restore_backup(install_dir, force=True) is True
    # A pre-restore copy must exist so a bad backup never strands the user.
    copies = [p for p in Path(install_dir).iterdir() if p.name.startswith("app.asar.pre-restore-")]
    assert len(copies) == 1


# --- malformed dictionaries fall back instead of crashing (R-03) -----------------

def test_merge_ignores_wrong_shapes():
    base_zh = '{"Keep": "保留"}'
    assert json.loads(patcher.merge_dict_texts(base_zh, '["not", "an", "object"]')) == {"Keep": "保留"}
    assert json.loads(patcher.merge_dict_texts(base_zh, '{"n": 42}')) == {"Keep": "保留"}

    base_pat = '[{"pattern": "^a$", "flags": "i", "replacement": "b"}]'
    assert json.loads(patcher.merge_pattern_texts(base_pat, '{"not": "a list"}')) == json.loads(base_pat)
    merged = json.loads(patcher.merge_pattern_texts(
        base_pat, '[{"pattern": "^a$", "flags": "i", "replacement": "B"}, "junk", 42]'))
    assert merged == [{"pattern": "^a$", "flags": "i", "replacement": "B"}]


def test_resolve_ignores_invalid_user_dicts(tmp_path, monkeypatch):
    user = tmp_path / "userlocales"
    user.mkdir()
    (user / "zh-CN.json").write_text('["not", "an", "object"]', encoding="utf-8")
    (user / "patterns.json").write_text('{"not": "a list"}', encoding="utf-8")
    zh_text, pat_text = patcher.resolve_dictionary_texts(str(user))
    base_zh, base_pat = patcher.base_dictionary_texts()
    assert json.loads(zh_text) == json.loads(base_zh)
    assert json.loads(pat_text) == json.loads(base_pat)


def test_load_valid_json_text_accepts_bom(tmp_path):
    p = tmp_path / "bom.json"
    p.write_bytes(b'\xef\xbb\xbf{"a": "b"}')
    assert patcher.load_valid_json_text(str(p)) is not None


# --- non-UTF-8 members are refused, not crashed (R-02) ----------------------------

def test_patch_refuses_non_utf8_preload(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    build_asar(asar, [("dist/preload.js", b"\xff\xfe\x00invalid\x01\x02")])
    assert patcher.apply_patch(install_dir) is False
    # Nothing was written: the archive still holds the undecodable bytes.
    _, files = patcher.read_asar(asar)
    assert files["dist/preload.js"] == b"\xff\xfe\x00invalid\x01\x02"


# --- atomic backup + lock (B-02) ---------------------------------------------------

def test_backup_is_valid_asar_with_matching_sidecar(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.apply_patch(install_dir) is True
    bak = asar + ".bak"
    patcher.read_asar(bak)  # must parse: no truncation
    expected = Path(bak + ".sha256").read_text(encoding="utf-8").strip()
    assert patcher.file_sha256(bak) == expected


def test_lock_blocks_concurrent_patch(install_dir, locales_dir, capsys):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    Path(install_dir, "app.asar.zhlock").write_text("12345", encoding="utf-8")
    assert patcher.apply_patch(install_dir) is False
    assert "lock" in capsys.readouterr().out.lower()
    assert not os.path.exists(asar + ".bak")


def test_stale_lock_is_broken(install_dir, locales_dir):
    import time

    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    lock = Path(install_dir, "app.asar.zhlock")
    lock.write_text("99999", encoding="utf-8")
    old = time.time() - 3600
    os.utime(lock, (old, old))
    assert patcher.apply_patch(install_dir) is True


# --- mode preservation (R-06) + --dir validation (R-07) ----------------------------

def test_write_preserves_file_mode(tmp_path):
    target = tmp_path / "m.asar"
    build_asar(str(target), [("a.js", b"data")])
    before = patcher.stat.S_IMODE(os.stat(target).st_mode)
    header, files = patcher.read_asar(str(target))
    patcher.write_asar_inplace(str(target), header, files)
    after = patcher.stat.S_IMODE(os.stat(target).st_mode)
    assert after == before


def test_resolve_rejects_bad_dirs(tmp_path):
    with pytest.raises(ValueError):
        patcher._resolve_install_dir(str(tmp_path / "nope"))
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        patcher._resolve_install_dir(str(f))
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError):
        patcher._resolve_install_dir(str(empty))


def test_resolve_finds_nested_resources(tmp_path):
    res = tmp_path / "inst" / "resources"
    res.mkdir(parents=True)
    build_asar(str(res / "app.asar"), [("dist/preload.js", b"x")])
    _, asar_path, bak_path = patcher._resolve_install_dir(str(tmp_path / "inst"))
    assert asar_path == str(res / "app.asar")
    assert bak_path == asar_path + ".bak"


@pytest.mark.skipif(sys.platform != "win32", reason="APPDATA fallback is Windows-only")
def test_locales_dir_falls_back_without_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOMEDRIVE", "")
    monkeypatch.setenv("HOMEPATH", "")
    # expanduser("~") must resolve into tmp_path for isolation
    monkeypatch.setenv("HOME", str(tmp_path))
    got = patcher.get_locales_dir()
    assert "AppData" in got
    assert os.path.isabs(got)


# --- engine hardening markers ------------------------------------------------------

ENGINE_SRC = Path(__file__).resolve().parents[1] / "engine" / "engine_template.js"


def test_engine_uses_null_prototype_dicts():
    src = ENGINE_SRC.read_text(encoding="utf-8")
    assert src.count("Object.create(null)") >= 3  # lowerTranslations x2 + merged


def test_engine_polling_is_throttled():
    src = ENGINE_SRC.read_text(encoding="utf-8")
    assert "document.hidden" in src
    assert "}, 5000);" in src
    assert "}, 2000);" not in src


def test_engine_shortcut_ignores_editable_focus():
    src = ENGINE_SRC.read_text(encoding="utf-8")
    assert "isContentEditable" in src
    assert "INPUT|TEXTAREA|SELECT" in src


def test_engine_untranslated_cache_evicts():
    src = ENGINE_SRC.read_text(encoding="utf-8")
    assert "oldest" in src  # FIFO eviction instead of a permanent lock-up


# --- sentinel parity between build.py and patcher.py --------------------------------

SENTINEL_CASES = [
    "plain text",
    "/*AG_ZH_ZH_START*/",
    "/*AG_ZH_ZH_END*/",
    "/*AG_ZH_PATTERNS_START*/",
    "/*AG_ZH_PATTERNS_END*/",
    '{"a": "/*AG_ZH_ZH_START*/ value"}',
    "",
]


def test_sentinel_helpers_stay_in_sync():
    for case in SENTINEL_CASES:
        assert build_mod.contains_sentinel_marker(case) == patcher.contains_sentinel_marker(case)


# --- update / watch (post-update automation) -----------------------------------------

def test_update_patches_fresh_install(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.update_patch(install_dir) is True
    _, files = patcher.read_asar(asar)
    assert patcher.SIGNATURE_PRELOAD in files["dist/preload.js"].decode("utf-8")
    assert os.path.exists(asar + ".bak")


def test_update_is_noop_when_current(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.update_patch(install_dir) is True
    bak_sha = patcher.file_sha256(asar + ".bak")
    assert patcher.update_patch(install_dir) is True
    assert patcher.file_sha256(asar + ".bak") == bak_sha  # backup untouched


def test_update_redetects_client_update(install_dir, locales_dir):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    assert patcher.update_patch(install_dir) is True

    # Simulate a client update: the official archive is replaced wholesale.
    make_fake_app(asar, "console.log('v2 official');",
                  extra=[("dist/extra.js", b"console.log('new in v2');")])
    assert patcher.update_patch(install_dir) is True
    _, files = patcher.read_asar(asar)
    assert patcher.SIGNATURE_PRELOAD in files["dist/preload.js"].decode("utf-8")
    # The backup now belongs to v2, not v1.
    _, bak_files = patcher.read_asar(asar + ".bak")
    assert b"v2 official" in bak_files["dist/preload.js"]
    assert patcher.SIGNATURE_PRELOAD not in bak_files["dist/preload.js"].decode("utf-8")


def test_update_refuses_when_client_running(install_dir, locales_dir, monkeypatch):
    asar = asar_path_for(install_dir)
    make_fake_app(asar, "console.log('v1 official');")
    monkeypatch.setattr(patcher, "is_antigravity_running", lambda: True)
    assert patcher.update_patch(install_dir) is False
    assert not os.path.exists(asar + ".bak")


def test_watch_rounds_call_apply_patch(install_dir, monkeypatch):
    calls = []
    monkeypatch.setattr(patcher, "apply_patch", lambda d=None, force=False: calls.append(d) or True)
    monkeypatch.setattr(patcher.time, "sleep", lambda s: None)
    assert patcher.run_watch(install_dir, interval_s=60, iterations=2) is True
    assert calls == [install_dir, install_dir]


def test_watch_skips_while_client_running(install_dir, monkeypatch):
    calls = []
    monkeypatch.setattr(patcher, "is_antigravity_running", lambda: True)
    monkeypatch.setattr(patcher, "apply_patch", lambda d=None, force=False: calls.append(d) or True)
    monkeypatch.setattr(patcher.time, "sleep", lambda s: None)
    assert patcher.run_watch(install_dir, interval_s=60, iterations=2) is True
    assert calls == []


def test_watch_minimum_interval(install_dir, monkeypatch, capsys):
    monkeypatch.setattr(patcher, "apply_patch", lambda d=None, force=False: True)
    assert patcher.run_watch(install_dir, interval_s=1, iterations=1) is True
    assert "minimum" in capsys.readouterr().out
