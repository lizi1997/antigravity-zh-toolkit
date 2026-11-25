# -*- coding: utf-8 -*-
"""End-to-end MVP pipeline: candidates -> providers -> QA -> merge -> build.

``release`` is a dry-run unless ``--apply`` is passed:

* dry-run reads the inputs, runs the provider chain and the QA gate and prints
  the merge plan plus a diff preview - **nothing is written to disk**;
* ``--apply`` writes run artifacts, backs up the dictionary, writes the merged
  dictionary atomically, rebuilds the generated artifacts through
  ``scripts/build.py --no-exe``, verifies that the generated engine embeds the
  new entry count, and rolls the dictionary back when the rebuild or the
  verification fails.

Exit codes (design §6.2): ``0`` success, ``2`` gate failure, ``4`` precondition
failure (missing input, refused network provider, failed rebuild after rollback),
``5`` internal error.
"""

import json
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from . import candidates as candidates_mod
from . import merge as merge_mod
from . import providers as providers_mod
from . import qa as qa_mod
from . import textutils

EXIT_OK = 0
EXIT_GATE = 2
EXIT_PRECONDITION = 4
EXIT_INTERNAL = 5

ENGINE_SENTINEL = re.compile(r"AG_ZH_ZH_START\*/(.*?)/\*AG_ZH_ZH_END\*/", re.S)


class Precondition(RuntimeError):
    """An input or environment precondition is not met (exit code 4)."""


@dataclass
class Options:
    command: str
    repo_root: Path
    candidates_path: Path = None
    translations_path: Path = None
    provider: str = "tm"
    provider_cmd: str = None
    cmd_confidence: str = providers_mod.LOW
    allow_network: bool = False
    apply: bool = False
    build: bool = True
    run_dir: Path = None
    run_id: str = None
    limit: int = None
    waive: tuple = ()
    max_findings: int = 50
    max_items: int = 20
    strict: bool = False


def default_repo_root():
    """``scripts/localization/pipeline.py`` -> repository root."""
    return Path(__file__).resolve().parents[2]


def new_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]


# --------------------------------------------------------------------------
# input helpers
# --------------------------------------------------------------------------
def load_dictionary(path):
    path = Path(path)
    if not path.is_file():
        raise Precondition("dictionary not found: {}".format(path))
    text = textutils.read_text_raw(path)
    try:
        dictionary = json.loads(text)
    except ValueError as exc:
        raise Precondition("dictionary is not valid JSON: {} ({})".format(path, exc))
    if not isinstance(dictionary, dict):
        raise Precondition("dictionary is not a JSON object: {}".format(path))
    return text, dictionary


def _write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    textutils.write_text_atomic(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


# --------------------------------------------------------------------------
# proposal + QA stage
# --------------------------------------------------------------------------
def prepare(options, dictionary):
    """Run providers and QA; returns the intermediate state shared by commands."""
    repo_root = Path(options.repo_root)
    candidates_path = options.candidates_path or (repo_root / "untranslated_candidates.json")
    candidates_path = Path(candidates_path)
    candidates = candidates_mod.load_candidates(candidates_path, limit=options.limit)

    # Conflicting duplicate rows in the candidate file are invisible to the
    # provider chain (it keys proposals by source), so surface them as H9 here.
    seen_targets = {}
    for candidate in candidates:
        if candidate.target.strip():
            seen_targets.setdefault(candidate.source.strip(), set()).add(candidate.target.strip())
    conflict_findings = [
        qa_mod.Finding(
            rule="H9",
            severity="blocker",
            message="candidate file maps one source to conflicting translations: {}".format(
                sorted(textutils.preview(item, 60) for item in targets)
            ),
            source=source,
            target="",
            origin="candidates",
        )
        for source, targets in seen_targets.items()
        if len(targets) > 1 and source not in dictionary
    ]
    # A conflicting candidate translation for a source that is already in the
    # dictionary used to be skipped silently ("already present"). Surface it as
    # minor so reviewers can see the drift; the dictionary entry still wins.
    conflict_findings += [
        qa_mod.Finding(
            rule="H9",
            severity="minor",
            message="candidate translation conflicts with the existing dictionary entry (dictionary kept): {}".format(
                sorted(textutils.preview(item, 60) for item in targets)
            ),
            source=source,
            target="",
            origin="candidates",
        )
        for source, targets in seen_targets.items()
        if len(targets) > 1 and source in dictionary
    ]

    overlay = {}
    if options.translations_path:
        overlay = candidates_mod.load_translations(Path(options.translations_path))
        candidates_mod.apply_overlay(candidates, overlay)

    # The candidate file itself may carry translations (the tracked
    # `untranslated_candidates.json` does). They are the highest-confidence
    # layer too, but an explicit --translations overlay always wins.
    implicit_overlay = {}
    for candidate in candidates:
        if candidate.target.strip():
            implicit_overlay[candidate.source.strip()] = candidate.target
    merged_overlay = dict(implicit_overlay)
    merged_overlay.update(overlay)

    chain = providers_mod.resolve_providers(
        options.provider,
        dictionary,
        overlay=merged_overlay,
        provider_cmd=options.provider_cmd,
        cmd_confidence=options.cmd_confidence,
        allow_network=options.allow_network,
        overlay_label="explicit" if overlay else "candidates",
    )
    proposals, provider_counts = providers_mod.collect_proposals(candidates, chain)

    candidates_by_source = {}
    normalized = 0
    for candidate in candidates:
        candidates_by_source.setdefault(candidate.source.strip(), candidate)
    for source, proposal in proposals.items():
        clean = qa_mod.normalize(proposal.target)
        if clean != proposal.target:
            normalized += 1
            proposal.target = clean

    entries = [
        qa_mod.QaEntry(
            source=source,
            target=proposal.target,
            origin=(candidates_by_source.get(source).origin()
                    if source in candidates_by_source else proposal.evidence.get("match", "")),
            confidence=proposal.confidence,
            stray_surrogate=(
                candidates_by_source[source].stray_surrogate
                if source in candidates_by_source else False
            ),
        )
        for source, proposal in sorted(proposals.items())
        if source not in dictionary
    ]
    skipped_existing = len(proposals) - len(entries)

    qa_report = qa_mod.run_qa(entries, dictionary, waive=options.waive,
                              extra_findings=conflict_findings)

    rejections = {}
    for finding in qa_report.findings:
        if finding.severity in ("blocker", "major") and finding.source:
            rejections.setdefault(finding.source, [])
            if finding.rule not in rejections[finding.source]:
                rejections[finding.source].append(finding.rule)

    plan = merge_mod.plan_merge(dictionary, proposals, rejections=rejections)

    return {
        "candidates_path": candidates_path,
        "candidates": candidates,
        "overlay_count": len(overlay),
        "implicit_overlay_count": len(implicit_overlay),
        "chain": chain,
        "provider_counts": provider_counts,
        "proposals": proposals,
        "entries": entries,
        "qa": qa_report,
        "plan": plan,
        "rejections": rejections,
        "normalized_targets": normalized,
        "skipped_existing": skipped_existing,
    }


def _inputs_report(options, state, dictionary_path, dictionary):
    report = {
        "candidates": {
            "path": str(state["candidates_path"]),
            "count": len(state["candidates"]),
            "with_translation": sum(1 for item in state["candidates"] if item.target.strip()),
        },
        "translations": None,
        "dictionary": {"path": str(dictionary_path), "entries": len(dictionary)},
        "limit": options.limit,
    }
    report["candidates"]["without_translation"] = (
        report["candidates"]["count"] - report["candidates"]["with_translation"]
    )
    if options.translations_path:
        report["translations"] = {
            "path": str(options.translations_path),
            "count": state["overlay_count"],
        }
    return report


# --------------------------------------------------------------------------
# build + verification + rollback
# --------------------------------------------------------------------------
def generated_engine_entries(repo_root):
    engine_path = Path(repo_root) / "engine" / "ag_localization_engine.js"
    if not engine_path.is_file():
        return None
    text = textutils.read_text_raw(engine_path)
    match = ENGINE_SENTINEL.search(text)
    if not match:
        return None
    try:
        return len(json.loads(match.group(1)))
    except ValueError:
        return None


def rebuild(repo_root, expected_entries):
    """Run ``scripts/build.py --no-exe`` and verify the embedded entry count."""
    build_script = Path(repo_root) / "scripts" / "build.py"
    if not build_script.is_file():
        raise Precondition("build script not found: {}".format(build_script))
    command = [sys.executable, str(build_script), "--no-exe"]
    result = {
        "ran": True,
        "command": " ".join(command),
        "exit": None,
        "engine_entries": None,
        "expected_entries": expected_entries,
        "verified": False,
    }
    try:
        completed = subprocess.run(
            command,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        result["reason"] = "could not start the build: {}".format(exc)
        result["exit"] = -1
        return result
    result["exit"] = completed.returncode
    result["stdout_tail"] = (completed.stdout or "")[-800:]
    if completed.stderr:
        result["stderr_tail"] = completed.stderr[-800:]
    if completed.returncode != 0:
        result["reason"] = "build failed with exit code {}".format(completed.returncode)
        return result
    entries = generated_engine_entries(repo_root)
    result["engine_entries"] = entries
    if entries is None:
        result["reason"] = "could not read the embedded dictionary from engine/ag_localization_engine.js"
        return result
    if entries != expected_entries:
        result["reason"] = "generated engine embeds {} entries, expected {}".format(entries, expected_entries)
        return result
    result["verified"] = True
    return result


def rollback(repo_root, dictionary_path, original_text, manifest, build_result):
    """Restore the dictionary and rebuild so the tree is consistent again."""
    if not manifest.get("backup"):
        return {"performed": False, "ok": False, "reason": "no backup was written"}
    restored = merge_mod.restore_dictionary(dictionary_path, manifest["backup"])
    original_entries = len(json.loads(original_text))
    rebuild_result = rebuild(repo_root, expected_entries=original_entries)
    return {
        "performed": True,
        "reason": build_result.get("reason"),
        "restored": restored,
        "rebuild": rebuild_result,
        "ok": bool(rebuild_result.get("verified")),
    }


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def run_release(options):
    repo_root = Path(options.repo_root).resolve()
    run_id = options.run_id or new_run_id()
    report = {
        "schema": 1,
        "command": "release",
        "mode": "apply" if options.apply else "dry-run",
        "run_id": run_id,
        "repo_root": str(repo_root),
        "offline": True,
        "network": (
            "no provider in this MVP opens a socket"
            if options.provider != "cmd"
            else "the pipeline opens no socket; --provider cmd runs a local command you supply"
        ),
    }
    dictionary_path = repo_root / "locales" / "zh-CN.json"
    try:
        dictionary_text, dictionary = load_dictionary(dictionary_path)
        state = prepare(options, dictionary)
        report["inputs"] = _inputs_report(options, state, dictionary_path, dictionary)
        report["providers"] = [
            {
                "name": provider.name,
                "requires_network": provider.requires_network,
                "deterministic": provider.deterministic,
                "proposals": state["provider_counts"].get(provider.name, 0),
            }
            for provider in state["chain"]
        ]
        report["normalized_targets"] = state["normalized_targets"]
        report["proposals"] = {
            "total": len(state["proposals"]),
            "new": len(state["entries"]),
            "already_in_dictionary": state["skipped_existing"],
        }
        report["qa"] = state["qa"].as_dict(max_findings=options.max_findings)
        plan = state["plan"]
        report["plan"] = plan.as_dict(max_items=options.max_items)
        merged = merge_mod.merged_dictionary(dictionary, plan)
        diff = merge_mod.diff_preview(dictionary_text, merged)
        report["diff"] = {
            "lines": diff["lines"],
            "truncated": diff.get("truncated", False),
            "preview": "" if options.apply else diff["diff"],
        }
        report["dictionary_sha256_before"] = textutils.sha256_text(dictionary_text)
    except Precondition as exc:
        report["error"] = str(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report
    except (providers_mod.ProviderFailure, candidates_mod.CandidateError) as exc:
        report["error"] = str(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report

    if state["qa"].gate != "pass":
        report["exit_code"] = EXIT_GATE
        return EXIT_GATE, report

    if not options.apply:
        report["build"] = {"ran": False, "reason": "dry-run: nothing was written"}
        report["dictionary_sha256_after"] = report["dictionary_sha256_before"]
        report["exit_code"] = EXIT_OK
        return EXIT_OK, report

    if not plan.changed:
        report["dictionary_sha256_after"] = report["dictionary_sha256_before"]
        report["build"] = {"ran": False, "reason": "dictionary already up to date"}
        # A previous `--no-build` run (or a hand-edited dictionary) can leave the
        # generated artifacts stale; repair that instead of reporting success.
        if options.build and generated_engine_entries(repo_root) != len(dictionary):
            try:
                build_result = rebuild(repo_root, expected_entries=len(dictionary))
            except Precondition as exc:
                build_result = {"ran": False, "exit": None, "verified": False,
                                "engine_entries": None, "reason": str(exc)}
            report["build"] = build_result
            report["rebuilt_stale_artifacts"] = True
            if not build_result.get("verified"):
                report["exit_code"] = EXIT_PRECONDITION
                return EXIT_PRECONDITION, report
        report["exit_code"] = EXIT_OK
        return EXIT_OK, report

    run_dir = Path(options.run_dir) if options.run_dir else (repo_root / ".l10n" / "runs" / run_id)
    try:
        _write_json(run_dir / "qa.json", state["qa"].as_dict(max_findings=1000000))
        _write_json(run_dir / "plan.json", {
            "run_id": run_id,
            "stats": plan.stats(),
            "additions": [
                {"source": source, "target": target, "evidence": plan.evidence.get(source, {})}
                for source, target in plan.additions.items()
            ],
            "conflicts": plan.conflicts,
            "quarantined": plan.quarantined,
            "already_present": plan.already_present,
        })
        manifest = merge_mod.apply_dictionary(
            dictionary_path, merged, backup_dir=run_dir / "pre-merge"
        )
        report["merge"] = manifest
        report["dictionary_sha256_after"] = manifest["sha256_after"]
    except OSError as exc:
        report["error"] = "could not write the merge: {}".format(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report

    if not options.build:
        report["build"] = {"ran": False, "reason": "--no-build: generated artifacts were not refreshed"}
        report["exit_code"] = EXIT_OK
        _write_json(run_dir / "manifest.json", {
            "run_id": run_id,
            "plan": plan.stats(),
            "merge": manifest,
            "build": report["build"],
        })
        return EXIT_OK, report

    try:
        build_result = rebuild(repo_root, expected_entries=len(merged))
    except Precondition as exc:
        build_result = {"ran": False, "exit": None, "verified": False,
                        "engine_entries": None, "reason": str(exc)}
    report["build"] = build_result
    if build_result.get("verified"):
        report["exit_code"] = EXIT_OK
        _write_json(run_dir / "manifest.json", {
            "run_id": run_id,
            "inputs": report["inputs"],
            "providers": report["providers"],
            "qa": {key: report["qa"][key] for key in ("checked", "gate", "blockers", "majors", "minors")},
            "plan": plan.stats(),
            "merge": manifest,
            "build": build_result,
        })
        return EXIT_OK, report

    report["rollback"] = rollback(repo_root, dictionary_path, dictionary_text, manifest, build_result)
    report["exit_code"] = EXIT_PRECONDITION
    _write_json(run_dir / "manifest.json", {
        "run_id": run_id,
        "plan": plan.stats(),
        "merge": manifest,
        "build": build_result,
        "rollback": report["rollback"],
    })
    return EXIT_PRECONDITION, report


def run_merge(options):
    repo_root = Path(options.repo_root).resolve()
    run_id = options.run_id or new_run_id()
    dictionary_path = repo_root / "locales" / "zh-CN.json"
    report = {
        "schema": 1,
        "command": "merge",
        "mode": "apply" if options.apply else "dry-run",
        "run_id": run_id,
        "repo_root": str(repo_root),
    }
    try:
        dictionary_text, dictionary = load_dictionary(dictionary_path)
        state = prepare(options, dictionary)
    except Precondition as exc:
        report["error"] = str(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report
    except (providers_mod.ProviderFailure, candidates_mod.CandidateError) as exc:
        report["error"] = str(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report

    report["inputs"] = _inputs_report(options, state, dictionary_path, dictionary)
    report["providers"] = [
        {
            "name": provider.name,
            "requires_network": provider.requires_network,
            "deterministic": provider.deterministic,
            "proposals": state["provider_counts"].get(provider.name, 0),
        }
        for provider in state["chain"]
    ]
    report["proposals"] = {
        "total": len(state["proposals"]),
        "new": len(state["entries"]),
        "already_in_dictionary": state["skipped_existing"],
    }
    report["qa"] = state["qa"].as_dict(max_findings=options.max_findings)
    plan = state["plan"]
    report["plan"] = plan.as_dict(max_items=options.max_items)
    merged = merge_mod.merged_dictionary(dictionary, plan)
    report["dictionary_sha256_before"] = textutils.sha256_text(dictionary_text)
    diff = merge_mod.diff_preview(dictionary_text, merged)
    report["diff"] = {"lines": diff["lines"], "truncated": diff.get("truncated", False)}

    if state["qa"].gate != "pass":
        report["exit_code"] = EXIT_GATE
        return EXIT_GATE, report
    if not options.apply:
        report["dictionary_sha256_after"] = report["dictionary_sha256_before"]
        report["exit_code"] = EXIT_OK
        return EXIT_OK, report
    if not plan.changed:
        report["dictionary_sha256_after"] = report["dictionary_sha256_before"]
        report["exit_code"] = EXIT_OK
        return EXIT_OK, report

    run_dir = Path(options.run_dir) if options.run_dir else (repo_root / ".l10n" / "runs" / run_id)
    try:
        _write_json(run_dir / "qa.json", state["qa"].as_dict(max_findings=1000000))
        _write_json(run_dir / "plan.json", {
            "run_id": run_id,
            "stats": plan.stats(),
            "additions": [
                {"source": source, "target": target, "evidence": plan.evidence.get(source, {})}
                for source, target in plan.additions.items()
            ],
        })
        report["merge"] = merge_mod.apply_dictionary(
            dictionary_path, merged, backup_dir=run_dir / "pre-merge"
        )
        report["dictionary_sha256_after"] = report["merge"]["sha256_after"]
    except OSError as exc:
        report["error"] = "could not write the merge: {}".format(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report

    report["build"] = {"ran": False, "reason": "merge does not rebuild; use 'release --apply'"}
    report["exit_code"] = EXIT_OK
    return EXIT_OK, report


def run_qa_command(options):
    repo_root = Path(options.repo_root).resolve()
    dictionary_path = repo_root / "locales" / "zh-CN.json"
    report = {"schema": 1, "command": "qa", "repo_root": str(repo_root)}
    try:
        dictionary_text, dictionary = load_dictionary(dictionary_path)
    except Precondition as exc:
        report["error"] = str(exc)
        report["exit_code"] = EXIT_PRECONDITION
        return EXIT_PRECONDITION, report

    if options.candidates_path or options.translations_path:
        try:
            state = prepare(options, dictionary)
        except (Precondition, providers_mod.ProviderFailure, candidates_mod.CandidateError) as exc:
            report["error"] = str(exc)
            report["exit_code"] = EXIT_PRECONDITION
            return EXIT_PRECONDITION, report
        report["mode"] = "proposals"
        report["inputs"] = _inputs_report(options, state, dictionary_path, dictionary)
        report["qa"] = state["qa"].as_dict(max_findings=options.max_findings)
    else:
        qa_report = qa_mod.run_dictionary_qa(dictionary, strict=options.strict)
        report["mode"] = "dictionary"
        report["inputs"] = {"dictionary": {"path": str(dictionary_path), "entries": len(dictionary)}}
        report["qa"] = qa_report.as_dict(max_findings=options.max_findings)

    report["dictionary_sha256"] = textutils.sha256_text(dictionary_text)
    report["exit_code"] = EXIT_OK if report["qa"]["gate"] == "pass" else EXIT_GATE
    return report["exit_code"], report


COMMANDS = {
    "release": run_release,
    "merge": run_merge,
    "qa": run_qa_command,
}


def run(options):
    handler = COMMANDS.get(options.command)
    if handler is None:
        raise Precondition("unknown command: {}".format(options.command))
    try:
        return handler(options)
    except Precondition as exc:
        return EXIT_PRECONDITION, {"schema": 1, "command": options.command, "error": str(exc),
                                   "exit_code": EXIT_PRECONDITION}
