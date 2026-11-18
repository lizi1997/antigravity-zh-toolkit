"""Regression tests for the second audit round.

Each test pins one defect that was found and fixed:
  N-01/N-02  the user's dictionary is merged, never discarded
  N-07       a UTF-8 BOM in the user's dictionary is accepted
  N-14       an empty translation is rejected at build time
  N-22       a corrupt ASAR archive is rejected instead of being re-written
  N-21       restoring a same-build backup does not warn about a version mismatch
"""

import json
import os
import struct
import subprocess
import sys
from pathlib import Path

import pytest

import patcher  # via tests/conftest.py

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# N-01 / N-02: dictionary merging
# ---------------------------------------------------------------------------

def test_user_dictionary_is_merged_not_discarded(tmp_path, monkeypatch):
    """A user dictionary with fewer entries must never be thrown away.

    The old logic compared entry counts and replaced the user's whole file
    with the embedded one - silently deleting every translation the user had
    added or removed.
    """
    monkeypatch.setattr(patcher, "get_bundled_locales_dir", lambda: None)

    locales = tmp_path / "locales"
    locales.mkdir()
    user = {"MyOwnTerm": "我自己的词条"}
    (locales / "zh-CN.json").write_text(json.dumps(user, ensure_ascii=False), encoding="utf-8")
    (locales / "patterns.json").write_text("[]", encoding="utf-8")

    zh_text, _ = patcher.resolve_dictionary_texts(str(locales))
    merged = json.loads(zh_text)

    assert merged["MyOwnTerm"] == "我自己的词条", "the user's own entry was lost"
    assert len(merged) > len(user), "the shipped dictionary was not merged in"


def test_user_translation_wins_over_the_shipped_one(tmp_path, monkeypatch):
    monkeypatch.setattr(patcher, "get_bundled_locales_dir", lambda: None)
    locales = tmp_path / "locales"
    locales.mkdir()
    key = next(iter(patcher.EMBEDDED_ZH_JSON and json.loads(patcher.EMBEDDED_ZH_JSON)))
    (locales / "zh-CN.json").write_text(
        json.dumps({key: "我的译法"}, ensure_ascii=False), encoding="utf-8")
    (locales / "patterns.json").write_text("[]", encoding="utf-8")

    zh_text, _ = patcher.resolve_dictionary_texts(str(locales))
    merged = json.loads(zh_text)
    assert merged[key] == "我的译法"


def test_bundled_dictionary_is_merged_in(tmp_path, monkeypatch):
    """The dictionary shipped next to the tool is read-only input."""
    bundled = tmp_path / "bundled"
    bundled.mkdir()
    (bundled / "zh-CN.json").write_text(
        json.dumps({"BundledOnlyTerm": "随包词条"}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(patcher, "get_bundled_locales_dir", lambda: str(bundled))

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    (user_dir / "zh-CN.json").write_text(
        json.dumps({"UserOnlyTerm": "用户词条"}, ensure_ascii=False), encoding="utf-8")
    (user_dir / "patterns.json").write_text("[]", encoding="utf-8")

    zh_text, _ = patcher.resolve_dictionary_texts(str(user_dir))
    merged = json.loads(zh_text)
    assert "BundledOnlyTerm" in merged
    assert "UserOnlyTerm" in merged


def test_seed_never_overwrites_the_user_dictionary(tmp_path):
    """Seeding may create the file, but it must never replace it."""
    locales = tmp_path / "locales"
    locales.mkdir()
    (locales / "zh-CN.json").write_text(
        json.dumps({"KeepMe": "别覆盖我"}, ensure_ascii=False), encoding="utf-8")

    patcher.seed_locale_files(str(locales))

    assert json.loads((locales / "zh-CN.json").read_text(encoding="utf-8")) == {"KeepMe": "别覆盖我"}
    assert (locales / "patterns.json").exists()


# ---------------------------------------------------------------------------
# N-07: UTF-8 BOM
# ---------------------------------------------------------------------------

def test_bom_prefixed_dictionary_is_accepted(tmp_path):
    """Windows editors add a BOM; the whole file must not be discarded."""
    p = tmp_path / "zh-CN.json"
    p.write_bytes("﻿".encode("utf-8") + json.dumps({"A": "B"}).encode("utf-8"))
    text = patcher.load_valid_json_text(str(p))
    assert text is not None, "a BOM'd dictionary was rejected"
    assert json.loads(text) == {"A": "B"}


# ---------------------------------------------------------------------------
# N-14: empty translations
# ---------------------------------------------------------------------------

def test_build_rejects_an_empty_translation(tmp_path):
    """An empty translation would blank out the UI text it belongs to."""
    import shutil
    locales = tmp_path / "locales"
    engine_dir = tmp_path / "engine"
    scripts_dir = tmp_path / "scripts"
    locales.mkdir()
    engine_dir.mkdir()
    scripts_dir.mkdir()
    (locales / "zh-CN.json").write_text(
        json.dumps({"Save": ""}, ensure_ascii=False, indent=2), encoding="utf-8")
    (locales / "patterns.json").write_text("[]", encoding="utf-8")
    shutil.copy(REPO_ROOT / "engine" / "engine_template.js", engine_dir / "engine_template.js")

    src = (REPO_ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    assert "empty_values" in src, "the empty-translation guard is missing"

    # the guard is exercised by the real builder
    result = subprocess.run(
        [sys.executable, "-c",
         "import importlib.util,sys;"
         "spec=importlib.util.spec_from_file_location('b', r'%s');"
         "b=importlib.util.module_from_spec(spec);"
         "spec.loader.exec_module(b);"
         "b.LOCALES_DIR=r'%s';"
         "b.ENGINE_DIR=r'%s';"
         "b.SCRIPTS_DIR=r'%s';"
         "b.build(compile_exe=False)" % (
             REPO_ROOT / "scripts" / "build.py", locales, engine_dir, scripts_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    combined = (result.stdout + result.stderr).lower()
    assert result.returncode != 0, "the build accepted an empty translation"
    assert "attributeerror" not in combined, result.stdout + result.stderr
    assert "empty translation" in combined, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# N-22: corrupt ASAR archives
# ---------------------------------------------------------------------------

def _minimal_asar(tmp_path, name="app.asar", magic=4):
    """A tiny but valid ASAR archive."""
    header = {"files": {"a.txt": {"size": 3, "offset": "0"}}}
    hb = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload = struct.pack("<IIII", magic, 8 + len(hb), 4 + len(hb), len(hb))
    p = tmp_path / name
    p.write_bytes(payload + hb + b"abc")
    return p


def test_read_asar_rejects_a_bad_magic(tmp_path):
    p = _minimal_asar(tmp_path, magic=0xDEADBEEF)
    with pytest.raises(ValueError) as exc:
        patcher.read_asar(str(p))
    assert "magic" in str(exc.value).lower()


def test_read_asar_rejects_an_out_of_bounds_entry(tmp_path):
    p = _minimal_asar(tmp_path)
    data = bytearray(p.read_bytes())
    data[-3:] = b""                       # truncate the payload
    p.write_bytes(bytes(data))
    with pytest.raises(ValueError):
        patcher.read_asar(str(p))


def test_read_asar_rejects_a_truncated_header(tmp_path):
    p = tmp_path / "tiny.asar"
    p.write_bytes(b"\x04\x00\x00\x00")
    with pytest.raises(ValueError):
        patcher.read_asar(str(p))


# ---------------------------------------------------------------------------
# N-21: restoring a same-build backup must not warn about a version mismatch
# ---------------------------------------------------------------------------

def test_restore_of_a_same_build_does_not_warn(tmp_path, monkeypatch, capsys):
    """The patched archive is always larger than its own backup - comparing
    sizes reported a version mismatch on every single restore."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "test_asar_mod", REPO_ROOT / "tests" / "test_asar.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    install = tmp_path / "Antigravity"
    install.mkdir()
    asar = install / "app.asar"
    mod.make_fake_app(str(asar), "console.log('v1 official');")

    locales = tmp_path / "locales"
    locales.mkdir()
    monkeypatch.setattr(patcher, "get_locales_dir", lambda: str(locales))
    monkeypatch.setattr(patcher, "get_bundled_locales_dir", lambda: None)

    assert patcher.apply_patch(str(install)) is True
    capsys.readouterr()

    assert patcher.restore_backup(str(install)) is True
    out = capsys.readouterr().out
    assert "Size mismatch" not in out, out
    assert "DIFFERENT client build" not in out, out


# ---------------------------------------------------------------------------
# The launcher scripts must fall back to the bundled Python
# ---------------------------------------------------------------------------

def test_install_script_falls_back_to_python_when_the_binary_fails(tmp_path):
    """A binary built for another architecture must not abort the script."""
    import shutil
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available")
    probe = subprocess.run([bash, "-c", "true"], capture_output=True)
    if probe.returncode != 0:
        pytest.skip("bash is not runnable in this environment")

    work = tmp_path / "pkg"
    (work / "scripts").mkdir(parents=True)
    binary = work / "antigravity-zh-macos-arm64"
    binary.write_text("#!/bin/sh\nexit 126\n", encoding="utf-8", newline="\n")
    binary.chmod(0o755)
    (work / "scripts" / "patcher.py").write_text(
        "import sys\nprint('PYTHON_FALLBACK', sys.argv[1])\n",
        encoding="utf-8", newline="\n")
    install_src = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    (work / "install.sh").write_text(install_src, encoding="utf-8", newline="\n")

    r = subprocess.run([bash, "install.sh"], cwd=str(work), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PYTHON_FALLBACK patch" in r.stdout, r.stdout + r.stderr
