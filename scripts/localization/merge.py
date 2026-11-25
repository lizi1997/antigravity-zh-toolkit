# -*- coding: utf-8 -*-
"""Deterministic, order-preserving and atomic dictionary merge.

Rules implemented here (design §4.5):

* an existing key is **never** overwritten: a human decision wins, a differing
  proposal is reported as a conflict;
* new keys are appended in stable source order (UTF-8 code point), so repeated
  runs and independent runs produce byte-identical files;
* the serialized file keeps the original line endings and trailing newline, so
  ``git diff`` only shows the added entries (``locales/zh-CN.json`` is CRLF);
* the write is atomic and preceded by a backup copy in the run directory;
* ``low``-confidence proposals are quarantined, never merged.
"""

import difflib
import json
from dataclasses import dataclass, field
from pathlib import Path

from . import textutils
from .providers import LOW


@dataclass
class MergePlan:
    additions: dict = field(default_factory=dict)
    already_present: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    quarantined: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)

    @property
    def changed(self):
        return bool(self.additions)

    def stats(self):
        return {
            "additions": len(self.additions),
            "already_present": len(self.already_present),
            "conflicts": len(self.conflicts),
            "quarantined": len(self.quarantined),
        }

    def as_dict(self, max_items=20):
        data = self.stats()
        data["additions_sample"] = [
            {"source": textutils.preview(source, 160), "target": textutils.preview(target, 160),
             "provider": self.evidence.get(source, {}).get("provider", "")}
            for source, target in list(self.additions.items())[:max_items]
        ]
        data["additions_truncated"] = len(self.additions) > max_items
        data["conflicts_sample"] = self.conflicts[:max_items]
        data["quarantined_sample"] = self.quarantined[:max_items]
        return data


def plan_merge(existing, proposals, rejections=None, max_items=None):
    """Build a merge plan.

    *existing*    - the current dictionary (order matters)
    *proposals*   - ``{source: Proposal}`` as produced by the provider chain
    *rejections*  - ``{source: [rule ids]}`` for entries the QA gate rejected
    """
    rejections = rejections or {}
    plan = MergePlan()
    for source in sorted(proposals):
        proposal = proposals[source]
        if source in existing:
            if existing[source] == proposal.target:
                plan.already_present.append(source)
            else:
                plan.conflicts.append({
                    "source": textutils.preview(source, 160),
                    "current": textutils.preview(existing[source], 160),
                    "proposed": textutils.preview(proposal.target, 160),
                    "provider": proposal.provider,
                })
            continue
        if source in rejections:
            plan.quarantined.append({
                "source": textutils.preview(source, 160),
                "reason": "qa:{}".format(",".join(rejections[source])),
            })
            continue
        if proposal.confidence == LOW:
            plan.quarantined.append({
                "source": textutils.preview(source, 160),
                "reason": "confidence:low ({})".format(proposal.provider),
            })
            continue
        plan.additions[source] = proposal.target
        plan.evidence[source] = {
            "provider": proposal.provider,
            "confidence": proposal.confidence,
            "origin": proposal.evidence.get("origin", ""),
        }
    return plan


def merged_dictionary(existing, plan):
    """Existing order first, then the additions in stable order."""
    merged = dict(existing)
    for source, target in plan.additions.items():
        merged[source] = target
    return merged


def serialize_dictionary(existing_text, merged):
    """Serialize *merged* with the formatting of the current file."""
    return textutils.dump_json_like(merged, existing_text)


def apply_dictionary(dictionary_path, merged, backup_dir=None):
    """Write *merged* atomically; returns a manifest with before/after hashes."""
    dictionary_path = Path(dictionary_path)
    original_text = textutils.read_text_raw(dictionary_path)
    new_text = serialize_dictionary(original_text, merged)

    manifest = {
        "path": str(dictionary_path),
        "sha256_before": textutils.sha256_text(original_text),
        "sha256_after": textutils.sha256_text(new_text),
        "changed": new_text != original_text,
        "entries_before": len(json.loads(original_text)),
        "entries_after": len(merged),
        "backup": None,
    }
    if not manifest["changed"]:
        return manifest

    if backup_dir:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / dictionary_path.name
        textutils.write_bytes_atomic(backup, original_text.encode("utf-8"))
        manifest["backup"] = str(backup)

    textutils.write_text_atomic(dictionary_path, new_text)
    return manifest


def restore_dictionary(dictionary_path, backup_path):
    """Put the pre-merge bytes back (used when the rebuild fails)."""
    dictionary_path = Path(dictionary_path)
    data = Path(backup_path).read_bytes()
    textutils.write_bytes_atomic(dictionary_path, data)
    return {
        "restored_from": str(backup_path),
        "sha256_after_restore": textutils.sha256_text(data.decode("utf-8")),
    }


def diff_preview(original_text, merged, max_lines=40):
    """A compact unified diff of the dictionary change (for dry-run output)."""
    new_text = serialize_dictionary(original_text, merged)
    if new_text == original_text:
        return {"lines": 0, "diff": ""}
    diff = list(
        difflib.unified_diff(
            original_text.splitlines(),
            new_text.splitlines(),
            fromfile="locales/zh-CN.json (current)",
            tofile="locales/zh-CN.json (planned)",
            lineterm="",
            n=1,
        )
    )
    body = diff[:max_lines]
    return {
        "lines": len(diff),
        "truncated": len(diff) > len(body),
        "diff": "\n".join(body),
        "files_compared": 1,
    }
