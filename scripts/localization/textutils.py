# -*- coding: utf-8 -*-
"""Text hygiene helpers shared by the localization MVP modules.

The helpers here exist because three failure modes already bit the project:

1. the legacy extractor crashed on a *lone surrogate* while writing JSON, so
   every text that enters the pipeline is checked and sanitized at the boundary;
2. ``locales/zh-CN.json`` uses CRLF line endings and a trailing newline, so a
   naive rewrite would produce a 2,800-line diff - :func:`dump_json_like`
   reproduces the file style byte for byte;
3. the engine splices its dictionaries between comment markers, so any text
   carrying one of those markers must be rejected before it reaches a file.
"""

import hashlib
import json
import os
from pathlib import Path

SENTINEL_MARKERS = (
    "/*AG_ZH_ZH_START*/",
    "/*AG_ZH_ZH_END*/",
    "/*AG_ZH_PATTERNS_START*/",
    "/*AG_ZH_PATTERNS_END*/",
)

#: Characters that never belong in a translatable UI string.
INVISIBLE_CHARS = (
    "\ufeff",  # BOM / zero-width no-break space
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
) + tuple(chr(cp) for cp in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A)))


def has_stray_surrogate(text):
    """True when *text* contains an unpaired UTF-16 surrogate code point."""
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in text)


def sanitize_surrogates(text):
    """Replace unpaired surrogates with U+FFFD so the text can be JSON encoded.

    The legacy extractor emitted exactly one such character and then died with
    ``UnicodeEncodeError`` at write time. The MVP replaces it at the boundary and
    lets QA (H8) report the entry, so one bad string cannot abort a whole run.
    """
    if not has_stray_surrogate(text):
        return text
    return "".join("\ufffd" if 0xD800 <= ord(ch) <= 0xDFFF else ch for ch in text)


def has_invisible_char(text):
    """True when *text* carries a BOM, zero-width or bidi control character."""
    return any(ch in text for ch in INVISIBLE_CHARS)


def contains_sentinel(text):
    """True when *text* embeds one of the engine's dictionary splice markers."""
    return any(marker in text for marker in SENTINEL_MARKERS)


def preview(text, limit=120):
    """A short, printable rendering safe for reports and console output."""
    text = sanitize_surrogates(text)
    flat = text.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")
    if len(flat) > limit:
        flat = flat[:limit] + "..."
    return flat


def read_text_raw(path):
    """Read UTF-8 text *without* newline translation.

    ``Path.read_text`` (Python < 3.13) normalizes CRLF to LF, which would make
    the style-preserving writer produce a whole-file diff.
    """
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def detect_newline(text):
    """The dominant line ending of *text*: CRLF when present, else LF."""
    return "\r\n" if "\r\n" in text else "\n"


def dump_json_like(obj, original_text):
    """Serialize *obj* with the indentation and line endings of *original_text*.

    Reproducing the original style is what keeps ``git diff`` limited to the
    entries that actually changed.
    """
    newline = detect_newline(original_text)
    dumped = json.dumps(obj, ensure_ascii=False, indent=2)
    if newline != "\n":
        dumped = dumped.replace("\n", newline)
    return dumped + (newline if original_text.endswith(newline) else "")


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_text_atomic(path, text):
    """Write *text* to *path* atomically (same-directory temp file + replace).

    ``newline=""`` disables the platform newline translation so the CRLF/LF
    style computed by :func:`dump_json_like` reaches the disk unchanged.
    """
    path = Path(path)
    tmp = path.with_name(path.name + ".l10n-tmp")
    try:
        with open(tmp, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def write_bytes_atomic(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + ".l10n-tmp")
    try:
        with open(tmp, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
