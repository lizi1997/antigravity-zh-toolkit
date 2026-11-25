# -*- coding: utf-8 -*-
"""Candidate strings and translation overlays.

A *candidate* is a UI string the extractor believes is missing from the
dictionary. The extractor itself is **not** rewritten in the MVP, so this module
only normalizes what already exists:

* ``untranslated_candidates.json`` - a JSON **list** of objects with at least
  ``original`` (optionally ``translation``, ``kind``, ``prop``, ``path``,
  ``line``, ``note``), which is the format of the tracked sample file;
* a JSON **object** mapping source -> target (the legacy extractor output);
* JSONL, one object per line;
* TSV, ``source<TAB>target``.

Everything is sanitized at the boundary: a lone surrogate (the character that
crashed the legacy extractor) becomes U+FFFD and is flagged so QA rule H8
rejects the entry instead of aborting the run.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .textutils import has_stray_surrogate, read_text_raw, sanitize_surrogates


class CandidateError(ValueError):
    """Raised when an input file cannot be interpreted as candidates/overlay."""


@dataclass
class Candidate:
    source: str
    target: str = ""
    kind: str = ""
    prop: str = ""
    path: str = ""
    line: int = None
    note: str = ""
    stray_surrogate: bool = False

    def origin(self):
        bits = [bit for bit in (self.kind, self.prop) if bit]
        if self.path:
            location = self.path
            if self.line:
                location += ":{}".format(self.line)
            bits.append(location)
        return " | ".join(bits)

    def context(self):
        """Context handed to providers (never includes the target)."""
        return {
            "source": self.source,
            "kind": self.kind,
            "prop": self.prop,
            "path": self.path,
            "line": self.line,
        }


def _prepare(text):
    """Strip a UTF-8 BOM (surrogates are handled per record, with provenance)."""
    if text.startswith("\ufeff"):
        text = text[1:]
    return text


def _records_from_json(data, path):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if all(isinstance(value, str) for value in data.values()):
            return [{"original": key, "translation": value} for key, value in data.items()]
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
    raise CandidateError(
        "{}: expected a JSON list of candidate objects or an object mapping source -> target".format(path)
    )


def _coerce_record(record, path, position):
    if not isinstance(record, dict):
        raise CandidateError("{}: record #{} is not an object".format(path, position))
    source = None
    for key in ("original", "source", "text", "key"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            source = value
            break
    if source is None:
        raise CandidateError("{}: record #{} has no 'original'/'source' string".format(path, position))
    target = ""
    for key in ("translation", "target", "value"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            target = value
            break
    line = record.get("line")
    if isinstance(line, str) and line.isdigit():
        line = int(line)
    if not isinstance(line, int):
        line = None
    return Candidate(
        source=sanitize_surrogates(source),
        target=sanitize_surrogates(target),
        kind=str(record.get("kind") or ""),
        prop=str(record.get("prop") or ""),
        path=str(record.get("path") or ""),
        line=line,
        note=str(record.get("note") or ""),
        stray_surrogate=has_stray_surrogate(source) or has_stray_surrogate(target),
    )


def load_candidates(path, limit=None):
    """Load candidate strings from *path* (JSON list/map, JSONL or TSV)."""
    path = Path(path)
    if not path.is_file():
        raise CandidateError("candidate file not found: {}".format(path))
    text = _prepare(read_text_raw(path))
    suffix = path.suffix.lower()

    if suffix in (".jsonl", ".ndjson"):
        records = []
        for number, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError as exc:
                raise CandidateError("{}:{}: invalid JSONL record ({})".format(path, number, exc))
    elif suffix in (".tsv", ".tab", ".txt"):
        return [
            Candidate(source=source, target=target)
            for source, target in load_translations(path, limit=limit).items()
        ]
    else:
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise CandidateError("{}: invalid JSON ({})".format(path, exc))
        records = _records_from_json(data, path)

    candidates = [_coerce_record(record, path, position) for position, record in enumerate(records)]
    if limit is not None:
        candidates = candidates[:limit]
    return candidates


def _parse_tsv(text, path):
    mapping = {}
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" not in line:
            raise CandidateError("{}:{}: expected 'source<TAB>target'".format(path, number))
        source, target = line.split("\t", 1)
        source = source.strip()
        if number == 1 and source.lower() in ("source", "original", "原文"):
            continue  # header row
        if not source:
            continue
        mapping[source] = target.replace("\\n", "\n").replace("\\t", "\t")
    return mapping


def load_translations(path, limit=None):
    """Load a source -> target overlay.

    ``.tsv``/``.txt`` are parsed as TSV; everything else as JSON/JSONL and then
    flattened (a candidate list only contributes entries that carry a target).
    """
    path = Path(path)
    if not path.is_file():
        raise CandidateError("translation file not found: {}".format(path))
    text = _prepare(read_text_raw(path))
    suffix = path.suffix.lower()

    if suffix in (".tsv", ".tab", ".txt"):
        mapping = _parse_tsv(text, path)
    elif suffix in (".jsonl", ".ndjson"):
        mapping = {}
        for number, line in enumerate(text.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError as exc:
                raise CandidateError("{}:{}: invalid JSONL record ({})".format(path, number, exc))
            if not isinstance(record, dict):
                raise CandidateError("{}:{}: record is not an object".format(path, number))
            candidate = _coerce_record(record, path, number)
            if candidate.target.strip():
                mapping[candidate.source] = candidate.target
    else:
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise CandidateError("{}: invalid JSON ({})".format(path, exc))
        mapping = {}
        for record in _records_from_json(data, path):
            candidate = _coerce_record(record, path, len(mapping))
            if candidate.target.strip():
                mapping[candidate.source] = candidate.target

    cleaned = {}
    for source, target in mapping.items():
        source = sanitize_surrogates(source).strip()
        if source:
            cleaned[source] = sanitize_surrogates(target)
    if limit is not None:
        cleaned = dict(list(cleaned.items())[:limit])
    return cleaned


def apply_overlay(candidates, overlay):
    """Fill/replace candidate targets from *overlay*; returns the number changed."""
    changed = 0
    for candidate in candidates:
        source = candidate.source.strip()
        target = overlay.get(source)
        if target is None:
            target = overlay.get(candidate.source)
        if target is None:
            continue
        if candidate.target != target:
            candidate.target = target
            changed += 1
    return changed
