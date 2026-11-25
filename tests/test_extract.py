"""Tests for scripts/extract_untranslated.py (previously 0 coverage)."""

import json
import os
import struct
import zlib
from pathlib import Path

import pytest

import extract_untranslated as ext


def _deflate_raw(data: bytes) -> bytes:
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    return comp.compress(data) + comp.flush()


def _zip_entry(fname: bytes, raw: bytes) -> bytes:
    comp = _deflate_raw(raw)
    header = struct.pack(
        "<IHHHHHIIIHH",
        0x04034B50, 20, 0, 8, 0, 0, 0, len(comp), len(raw), len(fname), 0,
    )
    return header + fname + comp


def _binary_with_zip(tmp_path, inner_js: str) -> str:
    payload = b"Save File\x00preamble\x00" + _zip_entry(b"main.js", inner_js.encode("utf-8"))
    p = tmp_path / "language_server"
    p.write_bytes(payload)
    return str(p)


def test_is_valid_ui_string_basics():
    assert ext.is_valid_ui_string("Save File")
    assert ext.is_valid_ui_string("Are you sure?")
    assert not ext.is_valid_ui_string("ab")  # too short
    assert not ext.is_valid_ui_string("x" * 201)  # too long
    assert not ext.is_valid_ui_string("my_snake_case_name")  # identifier
    assert not ext.is_valid_ui_string("https://example.com/x")  # url
    assert not ext.is_valid_ui_string("12345")  # no letters
    assert "中文" and not ext.is_valid_ui_string("已经是中文了")


def test_extract_from_binary_plain_and_zip(tmp_path):
    inner = 't("Hello World"); t(\'Single Quoted Label\');'
    target = _binary_with_zip(tmp_path, inner)
    found = ext.extract_from_binary(target)
    assert "Save File" in found
    assert "Hello World" in found
    assert "Single Quoted Label" in found


def test_extract_skips_huge_files(tmp_path, monkeypatch):
    p = tmp_path / "big.bin"
    p.write_bytes(b"Hello World")
    monkeypatch.setattr(ext, "MAX_SCAN_BYTES", 4)
    assert ext.extract_from_binary(str(p)) == set()


def _make_install(tmp_path, *names):
    inst = tmp_path / "inst"
    (inst / "resources").mkdir(parents=True)
    asar = inst / "resources" / "app.asar"
    asar.write_bytes(b"\x00Welcome To Nowhere\x00")
    for n in names:
        (inst / n).write_bytes(b"")
    return str(inst)


def test_run_extraction_writes_nested_out_and_filters_known(tmp_path):
    inst = _make_install(tmp_path)
    out = tmp_path / "deep" / "nested" / "missing.json"  # parents do not exist
    missing = ext.run_extraction(str(out), inst)
    assert out.is_file()
    assert "Welcome To Nowhere" in missing
    # Entries already in the shipped dictionary are filtered out.
    assert "Google Chrome" not in missing


def test_run_extraction_no_install_raises(tmp_path):
    with pytest.raises(SystemExit) as exc:
        ext.run_extraction(str(tmp_path / "o.json"), str(tmp_path / "nope"))
    assert exc.value.code == 2


def test_default_install_dirs_cover_patcher_locations():
    dirs = ext.get_default_install_dirs()
    assert len(dirs) >= 2
    assert any("resources" in d for d in dirs)
