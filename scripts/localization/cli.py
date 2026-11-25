# -*- coding: utf-8 -*-
"""Command line interface for the offline localization MVP.

``python scripts/localize.py release`` is the one-command dry-run: it reads the
candidate file, resolves translations through the provider chain, runs the QA
gate, prints the merge plan and a diff preview, and writes **nothing**.

``--apply`` writes ``locales/zh-CN.json`` deterministically, rebuilds the
generated artifacts through ``scripts/build.py --no-exe`` and verifies the
result; a failed rebuild rolls the dictionary back.
"""

import argparse
import json
import sys
from pathlib import Path

from . import __version__, pipeline, providers

EXIT_CODES = {
    "0": "success",
    "2": "gate failure (blockers or majors; see the QA report)",
    "4": "precondition failed (input, provider, build or rollback)",
    "5": "internal error",
}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="localize",
        description="Offline localization pipeline (MVP vertical slice).",
        epilog="One-command dry-run:  python scripts/localize.py release --translations untranslated_candidates.json",
    )
    parser.add_argument("--version", action="version", version="localize " + __version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(sub):
        sub.add_argument("--repo-root", default=None,
                         help="repository root (default: the checkout that contains scripts/localize.py)")
        sub.add_argument("--candidates", default=None,
                         help="candidate file (default: <repo>/untranslated_candidates.json)")
        sub.add_argument("--translations", default=None,
                         help="explicit source->target overlay: JSON, JSONL or TSV")
        sub.add_argument("--provider", default="tm", choices=["tm", "file", "cmd", "online", "all"],
                         help="provider chain: tm (default), file, cmd, online (stub), all")
        sub.add_argument("--provider-cmd", default=None,
                         help="external command adapter (JSON on stdin, JSON on stdout)")
        sub.add_argument("--cmd-confidence", default=providers.LOW, choices=[providers.HIGH, providers.MEDIUM, providers.LOW],
                         help="confidence assigned to --provider-cmd proposals (default: low -> quarantined)")
        sub.add_argument("--allow-network", action="store_true",
                         help="first of the two switches required by the online provider (still unimplemented)")
        sub.add_argument("--limit", type=int, default=None, help="only process the first N candidates")
        sub.add_argument("--waive", action="append", default=[], metavar="RULE",
                         help="downgrade one QA rule (repeatable), recorded in the report")
        sub.add_argument("--run-dir", default=None, help="where run artifacts go (default: <repo>/.l10n/runs/<run-id>)")
        sub.add_argument("--run-id", default=None, help="override the generated run id")
        sub.add_argument("--json", action="store_true", help="print one JSON line on stdout (logs stay human)")
        sub.add_argument("--max-findings", type=int, default=50, help="how many QA findings to print")
        sub.add_argument("--max-items", type=int, default=20, help="how many plan items to print")

    release = subparsers.add_parser("release", help="propose -> QA -> plan -> (apply) -> rebuild -> verify")
    add_common(release)
    release.add_argument("--apply", action="store_true",
                         help="write locales/zh-CN.json and rebuild generated artifacts")
    release.add_argument("--no-build", action="store_true",
                         help="with --apply: write the dictionary but do not rebuild")

    merge = subparsers.add_parser("merge", help="propose -> QA -> plan -> (apply dictionary only)")
    add_common(merge)
    merge.add_argument("--apply", action="store_true", help="write locales/zh-CN.json (no rebuild)")

    qa = subparsers.add_parser("qa", help="QA the shipped dictionary, or a candidate/translation set")
    add_common(qa)
    qa.add_argument("--strict", action="store_true", help="dictionary mode: also fail on major findings")
    return parser


def _options(args):
    repo_root = Path(args.repo_root).resolve() if args.repo_root else pipeline.default_repo_root()
    return pipeline.Options(
        command=args.command,
        repo_root=repo_root,
        candidates_path=Path(args.candidates).resolve() if args.candidates else None,
        translations_path=Path(args.translations).resolve() if args.translations else None,
        provider=args.provider,
        provider_cmd=args.provider_cmd,
        cmd_confidence=args.cmd_confidence,
        allow_network=args.allow_network,
        apply=getattr(args, "apply", False),
        build=not getattr(args, "no_build", False),
        run_dir=Path(args.run_dir).resolve() if args.run_dir else None,
        run_id=args.run_id,
        limit=args.limit,
        waive=tuple(args.waive),
        max_findings=args.max_findings,
        max_items=args.max_items,
        strict=getattr(args, "strict", False),
    )


def _emit(report, args):
    if args.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(render_human(report, args) + "\n")
    sys.stdout.flush()


def render_human(report, args):
    lines = []
    title = report.get("command", "")
    if report.get("mode"):
        title += " ({})".format(report["mode"])
    lines.append("=" * 70)
    lines.append("  localize {}   v{}".format(title, __version__))
    lines.append("=" * 70)
    if report.get("repo_root"):
        lines.append("repo: {}".format(report["repo_root"]))

    if report.get("error"):
        lines.append("[!] {}".format(report["error"]))
        lines.append("exit: {} ({})".format(report.get("exit_code"), EXIT_CODES.get(str(report.get("exit_code")), "")))
        return "\n".join(lines)

    inputs = report.get("inputs") or {}
    if "candidates" in inputs:
        candidates = inputs["candidates"]
        suffix = " (limit {})".format(inputs["limit"]) if inputs.get("limit") else ""
        lines.append("candidates: {} ({} entries, {} with a translation){}".format(
            candidates["path"], candidates["count"], candidates["with_translation"], suffix))
    if inputs.get("translations"):
        lines.append("translations: {} ({} entries)".format(
            inputs["translations"]["path"], inputs["translations"]["count"]))
    if "dictionary" in inputs:
        lines.append("dictionary: {} ({} entries)".format(
            inputs["dictionary"]["path"], inputs["dictionary"]["entries"]))

    if report.get("providers"):
        lines.append("providers: " + ", ".join(
            "{}={}".format(item["name"], item["proposals"]) for item in report["providers"]))
    if report.get("proposals"):
        lines.append("proposals: {} total, {} new ({} already in the dictionary)".format(
            report["proposals"]["total"], report["proposals"]["new"],
            report["proposals"]["already_in_dictionary"]))
    if report.get("normalized_targets"):
        lines.append("NFC-normalized targets: {}".format(report["normalized_targets"]))

    qa = report.get("qa")
    if qa:
        lines.append("QA ({}): {} checked -> {}   blockers={} majors={} minors={}".format(
            qa["mode"], qa["checked"], qa["gate"], qa["blockers"], qa["majors"], qa["minors"]))
        for finding in qa.get("findings", [])[:args.max_findings]:
            lines.append("  [{}] {} {}".format(finding["severity"], finding["rule"], finding["message"]))
            if finding.get("source"):
                lines.append("         source: {}".format(finding["source"]))
        if qa.get("findings_truncated"):
            lines.append("  ... more findings: see --json output or the run directory")
        if qa.get("waived"):
            lines.append("  waived findings: {}".format(len(qa["waived"])))
        pending = [item["rule"] for item in qa.get("coverage", {}).get("not_implemented", [])]
        if pending:
            lines.append("  rules not implemented in this MVP: {}".format(", ".join(pending)))

    plan = report.get("plan")
    if plan:
        lines.append("plan: +{} additions, {} already present, {} conflicts, {} quarantined".format(
            plan["additions"], plan["already_present"], plan["conflicts"], plan["quarantined"]))
        for item in plan.get("additions_sample", [])[:args.max_items]:
            lines.append('  + {}  ->  {}'.format(item["source"], item["target"]))
        if plan.get("additions_truncated"):
            lines.append("  ... additions truncated")
        for item in plan.get("conflicts_sample", [])[:5]:
            lines.append('  ! conflict: {} (dictionary keeps "{}", proposal was "{}")'.format(
                item["source"], item["current"], item["proposed"]))
        for item in plan.get("quarantined_sample", [])[:5]:
            lines.append("  ? quarantined: {} ({})".format(item["source"], item["reason"]))

    diff = report.get("diff")
    if diff:
        lines.append("diff: {} changed diff lines{}".format(
            diff["lines"], " (truncated)" if diff.get("truncated") else ""))
        if diff.get("preview"):
            for line in diff["preview"].splitlines()[:args.max_items]:
                lines.append("  " + line)

    before = report.get("dictionary_sha256_before")
    if before:
        after = report.get("dictionary_sha256_after") or (report.get("merge") or {}).get("sha256_after") or before
        lines.append("dictionary sha256: {} -> {}".format(before[:16], after[:16]))

    build = report.get("build")
    if build:
        if build.get("ran"):
            lines.append("build: {} -> exit {} | engine entries {} | verified={}".format(
                build.get("command"), build.get("exit"), build.get("engine_entries"), build.get("verified")))
            if not build.get("verified") and build.get("reason"):
                lines.append("       reason: {}".format(build["reason"]))
        else:
            lines.append("build: not run ({})".format(build.get("reason")))

    rollback = report.get("rollback")
    if rollback:
        lines.append("ROLLBACK: performed={} ok={} reason={}".format(
            rollback.get("performed"), rollback.get("ok"), rollback.get("reason")))

    exit_code = report.get("exit_code")
    lines.append("exit: {} ({})".format(exit_code, EXIT_CODES.get(str(exit_code), "")))
    if report.get("mode") == "dry-run" and exit_code == 0:
        lines.append("hint: this was a dry-run and nothing was written; add --apply to write the dictionary and rebuild.")
    return "\n".join(lines)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    options = _options(args)
    try:
        exit_code, report = pipeline.run(options)
    except Exception as exc:  # noqa: BLE001 - the CLI must report, not crash
        report = {
            "schema": 1,
            "command": args.command,
            "error": "{}: {}".format(type(exc).__name__, exc),
            "exit_code": pipeline.EXIT_INTERNAL,
        }
        exit_code = pipeline.EXIT_INTERNAL
    _emit(report, args)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
