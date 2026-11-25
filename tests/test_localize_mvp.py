# -*- coding: utf-8 -*-
"""Tests for the offline localization MVP (``scripts/localization/``).

All fixtures build a throw-away repository under ``<repo>/.pytest_tmp/`` and
clean it up; no test writes to the real ``locales/``, ``engine/``, ``scripts/``
or to any installed client. The workspace-local scratch directory exists
because this development sandbox denies writes under ``%TEMP%`` (pytest's own
``tmp_path`` fixture fails there), not because the pipeline needs it.
"""

import difflib
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from localization import candidates as candidates_mod
from localization import merge, pipeline, providers, qa

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
CLI = SCRIPTS_DIR / "localize.py"
TMP_ROOT = REPO_ROOT / ".pytest_tmp" / "auto_localize"

BASE_DICTIONARY = {
    "Settings": "设置",
    "Save": "保存",
    "Cancel": "取消",
    "Workspace": "工作区",
    "Agent": "智能体",
    "Already translated": "已翻译",
}

CANDIDATES = [
    {
        "kind": "UI属性",
        "prop": "message",
        "path": "app.asar!dist/browserStream/x.js",
        "line": 10,
        "original": "Failed to stop agent browser",
        "translation": "停止智能体浏览器失败",
    },
    {
        "kind": "文本内容",
        "prop": "",
        "path": "app.asar!dist/y.js",
        "line": 20,
        "original": "Open the URL https://example.com in a new tab",
        "translation": "在新标签页中打开 https://example.com",
    },
    {
        "original": "You have {$count} credits",
        "translation": "您有 {$count} 积分",
    },
    {
        "original": "Press Ctrl+Alt+L to export",
        "translation": "按 Ctrl+Alt+L 导出",
    },
    {"original": "Already translated", "translation": "已翻译"},
]

EXPECTED_ADDITIONS = [
    "Failed to stop agent browser",
    "Open the URL https://example.com in a new tab",
    "Press Ctrl+Alt+L to export",
    "You have {$count} credits",
]


# --------------------------------------------------------------------------
# scratch repository fixtures
# --------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _cleanup_tmp_root():
    yield
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(root):
    root = Path(root)
    return {
        str(path.relative_to(root)).replace(os.sep, "/"): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_dictionary(root, mapping):
    """Write the dictionary with CRLF endings, like the real repository file."""
    text = json.dumps(mapping, ensure_ascii=False, indent=2).replace("\n", "\r\n") + "\r\n"
    (Path(root) / "locales" / "zh-CN.json").write_bytes(text.encode("utf-8"))


def make_scratch(prefix="repo"):
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    root = TMP_ROOT / (prefix + "-" + uuid.uuid4().hex[:10])
    (root / "scripts").mkdir(parents=True)
    (root / "engine").mkdir()
    (root / "locales").mkdir()
    shutil.copy2(SCRIPTS_DIR / "build.py", root / "scripts" / "build.py")
    shutil.copy2(REPO_ROOT / "engine" / "engine_template.js", root / "engine" / "engine_template.js")
    write_dictionary(root, BASE_DICTIONARY)
    (root / "locales" / "patterns.json").write_text("[]\n", encoding="utf-8")
    return root


@pytest.fixture()
def scratch_repo():
    root = make_scratch()
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


def write_candidates(root, records=None, name="candidates.json"):
    path = Path(root) / name
    path.write_text(json.dumps(records if records is not None else CANDIDATES,
                               ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def run_cli(*args, env_extra=None, expect=None):
    environment = os.environ.copy()
    environment.pop("AG_L10N_ALLOW_NETWORK", None)
    environment["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        environment.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(CLI)] + [str(item) for item in args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        timeout=300,
    )
    if expect is not None:
        assert proc.returncode == expect, "exit {}\nstdout:\n{}\nstderr:\n{}".format(
            proc.returncode, proc.stdout, proc.stderr)
    return proc


def report_of(proc):
    return json.loads(proc.stdout.strip().splitlines()[-1])


def apply_release(root, candidates, *extra, expect=0):
    return run_cli(
        "release", "--repo-root", root, "--candidates", candidates, "--apply", "--json",
        *extra, expect=expect,
    )


# --------------------------------------------------------------------------
# dry-run / apply behaviour
# --------------------------------------------------------------------------
def test_dry_run_is_the_default_and_writes_nothing(scratch_repo):
    candidates = write_candidates(scratch_repo)
    before = snapshot(scratch_repo)

    proc = run_cli("release", "--repo-root", scratch_repo, "--candidates", candidates,
                   "--translations", candidates, "--json", expect=0)
    report = report_of(proc)

    assert report["mode"] == "dry-run"
    assert report["exit_code"] == 0
    assert report["qa"]["gate"] == "pass"
    # Only entries that would actually be written go through the gate.
    assert report["qa"]["checked"] == len(EXPECTED_ADDITIONS)
    assert report["proposals"] == {
        "total": len(CANDIDATES),
        "new": len(EXPECTED_ADDITIONS),
        "already_in_dictionary": 1,
    }
    assert report["plan"]["additions"] == len(EXPECTED_ADDITIONS)
    assert report["plan"]["already_present"] == 1
    assert report["build"]["ran"] is False
    assert report["dictionary_sha256_before"] == report["dictionary_sha256_after"]
    assert snapshot(scratch_repo) == before, "dry-run must not write a single file"


def test_apply_is_idempotent(scratch_repo):
    candidates = write_candidates(scratch_repo)
    dictionary_path = scratch_repo / "locales" / "zh-CN.json"
    engine_path = scratch_repo / "engine" / "ag_localization_engine.js"
    patcher_path = scratch_repo / "scripts" / "patcher.py"

    first = apply_release(scratch_repo, candidates, "--translations", candidates)
    report_first = report_of(first)
    assert report_first["mode"] == "apply"
    assert report_first["plan"]["additions"] == len(EXPECTED_ADDITIONS)
    assert report_first["build"]["verified"] is True
    assert report_first["build"]["engine_entries"] == len(BASE_DICTIONARY) + len(EXPECTED_ADDITIONS)

    hashes = {path: _sha256(path) for path in (dictionary_path, engine_path, patcher_path)}

    second = apply_release(scratch_repo, candidates, "--translations", candidates)
    report_second = report_of(second)
    assert report_second["plan"]["additions"] == 0
    assert report_second["plan"]["already_present"] == len(EXPECTED_ADDITIONS) + 1
    assert report_second["build"]["ran"] is False
    assert report_second["dictionary_sha256_before"] == report_second["dictionary_sha256_after"]
    for path, digest in hashes.items():
        assert _sha256(path) == digest, "{} changed on a repeated apply".format(path.name)

    dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))
    assert list(dictionary)[:len(BASE_DICTIONARY)] == list(BASE_DICTIONARY)
    assert len(dictionary) == len(BASE_DICTIONARY) + len(EXPECTED_ADDITIONS)


def test_apply_is_deterministic_across_independent_repositories():
    first = make_scratch("det-a")
    second = make_scratch("det-b")
    try:
        for root in (first, second):
            candidates = write_candidates(root)
            apply_release(root, candidates, "--translations", candidates)
        for relative in ("locales/zh-CN.json", "engine/ag_localization_engine.js", "scripts/patcher.py"):
            assert _sha256(first / relative) == _sha256(second / relative), relative
    finally:
        shutil.rmtree(first, ignore_errors=True)
        shutil.rmtree(second, ignore_errors=True)


def test_apply_preserves_file_format_and_key_order(scratch_repo):
    candidates = write_candidates(scratch_repo)
    dictionary_path = scratch_repo / "locales" / "zh-CN.json"
    original_bytes = dictionary_path.read_bytes()
    apply_release(scratch_repo, candidates, "--translations", candidates)

    after_bytes = dictionary_path.read_bytes()
    # CRLF preserved, trailing newline preserved, no lone LF introduced.
    assert after_bytes.endswith(b"\r\n")
    assert after_bytes.count(b"\n") == after_bytes.count(b"\r\n")

    old_object = json.loads(original_bytes.decode("utf-8"))
    new_object = json.loads(after_bytes.decode("utf-8"))
    new_keys = [key for key in new_object if key not in old_object]

    assert list(new_object)[:len(old_object)] == list(old_object)
    assert new_keys == sorted(new_keys), "new keys must be appended in codepoint order"

    old_lines = original_bytes.decode("utf-8").split("\r\n")
    new_lines = after_bytes.decode("utf-8").split("\r\n")
    changed = [
        line for line in difflib.unified_diff(old_lines, new_lines, lineterm="", n=0)
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    ]
    removed = [line for line in changed if line.startswith("-")]
    added = [line for line in changed if line.startswith("+")]
    # The only existing line that changes is the last entry, which gains a comma.
    assert len(removed) == 1, removed
    assert len(added) == len(new_keys) + 1, added

    engine = (scratch_repo / "engine" / "ag_localization_engine.js").read_text(encoding="utf-8")
    for key in EXPECTED_ADDITIONS:
        assert key in engine


def test_apply_with_no_build_is_repaired_by_the_next_apply(scratch_repo):
    candidates = write_candidates(scratch_repo)
    dictionary_path = scratch_repo / "locales" / "zh-CN.json"

    report = report_of(apply_release(scratch_repo, candidates,
                                     "--translations", candidates, "--no-build"))
    assert report["build"]["ran"] is False
    assert len(json.loads(dictionary_path.read_text(encoding="utf-8"))) == len(BASE_DICTIONARY) + len(EXPECTED_ADDITIONS)
    assert not (scratch_repo / "engine" / "ag_localization_engine.js").exists()

    repaired = report_of(apply_release(scratch_repo, candidates, "--translations", candidates))
    assert repaired["plan"]["additions"] == 0
    assert repaired["rebuilt_stale_artifacts"] is True
    assert repaired["build"]["verified"] is True
    assert repaired["build"]["engine_entries"] == len(BASE_DICTIONARY) + len(EXPECTED_ADDITIONS)


def test_apply_rolls_back_when_the_rebuild_fails(scratch_repo):
    candidates = write_candidates(scratch_repo)
    dictionary_path = scratch_repo / "locales" / "zh-CN.json"
    original_sha = _sha256(dictionary_path)
    (scratch_repo / "engine" / "engine_template.js").unlink()  # build.py can no longer run

    report = report_of(apply_release(scratch_repo, candidates,
                                     "--translations", candidates, expect=4))

    assert report["qa"]["gate"] == "pass"
    assert report["build"]["verified"] is False
    assert report["rollback"]["performed"] is True
    assert report["rollback"]["ok"] is False, "the rebuild cannot recover without the template"
    assert _sha256(dictionary_path) == original_sha, "the dictionary must be restored"

    backups = list((scratch_repo / ".l10n" / "runs").glob("*/pre-merge/zh-CN.json"))
    assert backups, "a pre-merge backup must exist"
    assert _sha256(backups[0]) == original_sha

    manifest = json.loads(next((scratch_repo / ".l10n" / "runs").glob("*/manifest.json")).read_text(encoding="utf-8"))
    assert manifest["rollback"]["performed"] is True


# --------------------------------------------------------------------------
# QA gate
# --------------------------------------------------------------------------
def test_qa_rejects_a_broken_placeholder_and_leaves_the_dictionary_alone(scratch_repo):
    candidates = write_candidates(scratch_repo, [
        {"original": "You have {count} credits", "translation": "您有 额度"},
    ])
    dictionary_path = scratch_repo / "locales" / "zh-CN.json"
    before = _sha256(dictionary_path)
    snapshot_before = snapshot(scratch_repo)

    report = report_of(apply_release(scratch_repo, candidates, expect=2))

    assert report["qa"]["gate"] == "fail"
    rules = {finding["rule"] for finding in report["qa"]["findings"]}
    assert "H1" in rules, rules
    assert report["plan"]["quarantined"] >= 1
    assert _sha256(dictionary_path) == before
    assert snapshot(scratch_repo) == snapshot_before, "a failed gate must not write anything"


def test_waivers_are_recorded_and_unblock_the_gate(scratch_repo):
    candidates = write_candidates(scratch_repo, [
        {"original": "You have {count} credits", "translation": "您有 额度"},
    ])
    report = report_of(run_cli(
        "release", "--repo-root", scratch_repo, "--candidates", candidates,
        "--waive", "H1", "--waive", "H10", "--json", expect=0,
    ))
    assert report["qa"]["gate"] == "pass"
    assert len(report["qa"]["waived"]) == 2
    assert report["plan"]["additions"] == 1


def test_h9_rejects_one_source_with_two_translations():
    entries = [
        qa.QaEntry(source="Open recent", target="打开最近", origin="a"),
        qa.QaEntry(source="Open recent", target="打开最近的", origin="b"),
    ]
    report = qa.run_qa(entries, {})
    assert report.gate == "fail"
    assert "H9" in {finding.rule for finding in report.findings}


def test_h21_rejects_a_case_collision_with_a_different_translation():
    entries = [qa.QaEntry(source="Save all", target="全部保存")]
    report = qa.run_qa(entries, {"save all": "全部存储"})
    assert report.gate == "fail"
    assert "H21" in {finding.rule for finding in report.findings}


def test_conflicting_duplicate_rows_in_the_candidate_file_fail_h9(scratch_repo):
    candidates = write_candidates(scratch_repo, [
        {"original": "Open recent", "translation": "打开最近"},
        {"original": "Open recent", "translation": "打开最近的"},
    ])
    report = report_of(run_cli(
        "release", "--repo-root", scratch_repo, "--candidates", candidates, "--json", expect=2))
    assert "H9" in report["qa"]["rules_with_findings"]
    assert report["qa"]["gate"] == "fail"


@pytest.mark.parametrize("source,target,rule", [
    ("You have {$n} credits", "您有 积分", "H1"),
    ("See https://example.com/docs for details", "请参阅文档了解详情", "H2"),
    ("Open app.asar with care", "请小心打开应用包", "H2"),
    ("Press Ctrl+Alt+L", "按快捷键", "H3"),
    ("Use --no-exe to skip the binary", "使用该选项跳过二进制", "H3"),
    ("Run `build.py` first", "先运行构建脚本", "H3"),
    ("Model Context Protocol (MCP) support", "模型上下文协议支持", "H3"),
    ("Set MAX_RETRIES here", "在此设置重试次数", "H3"),
    ("<b>Bold</b> text", "粗体文本", "H4"),
    ("Workspace settings", "设置", "H10"),
])
def test_entry_rules_reject_token_loss(source, target, rule):
    findings = qa.check_entry(qa.QaEntry(source=source, target=target))
    assert rule in {finding.rule for finding in findings}, [finding.rule for finding in findings]


@pytest.mark.parametrize("source,target", [
    ("You have {$n} credits", "您有 {$n} 积分"),
    ("See https://example.com/docs", "请参阅 https://example.com/docs"),
    ("Open app.asar with care", "请小心打开 app.asar"),
    ("Press Ctrl+Alt+L", "按 Ctrl+Alt+L 导出"),
    ("Use --no-exe to skip", "使用 --no-exe 跳过"),
    ("Run `build.py` first", "先运行 `build.py`"),
    ("Model Context Protocol (MCP) support", "模型上下文协议 (MCP) 支持"),
    ("Set MAX_RETRIES here", "在此设置 MAX_RETRIES"),
    ("<b>Bold</b> text", "<b>粗体</b>文本"),
    ("Workspace settings", "工作区设置"),
])
def test_entry_rules_accept_faithful_translations(source, target):
    assert qa.check_entry(qa.QaEntry(source=source, target=target)) == []


@pytest.mark.parametrize("source,target,rule", [
    ("Save changes", "   ", "H5"),
    (" Save changes", "保存更改", "H6"),
    ("Text /*AG_ZH_ZH_START*/ here", "文本", "H7"),
    ("A" * 501, "很长的文本", "H12"),
])
def test_entry_rules_reject_structural_problems(source, target, rule):
    findings = qa.check_entry(qa.QaEntry(source=source, target=target))
    assert rule in {finding.rule for finding in findings}, [finding.rule for finding in findings]


def test_stray_surrogate_is_rejected_by_h8():
    findings = qa.check_entry(qa.QaEntry(source="Broken \ud800 text", target="损坏的文本",
                                        stray_surrogate=True))
    assert "H8" in {finding.rule for finding in findings}


def test_dictionary_qa_fails_on_an_empty_value_and_passes_on_the_fixture():
    assert qa.run_dictionary_qa(dict(BASE_DICTIONARY)).gate == "pass"
    broken = dict(BASE_DICTIONARY, Breakage="   ")
    report = qa.run_dictionary_qa(broken)
    assert report.gate == "fail"
    assert {finding.rule for finding in report.findings} == {"H5"}


def test_rule_coverage_is_stated_not_implied():
    coverage = qa.coverage()
    assert set(coverage["implemented"]) >= {"H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8",
                                            "H9", "H10", "H11", "H12", "H13", "H21", "H23"}
    pending = {item["rule"] for item in coverage["not_implemented"]}
    assert pending, "unimplemented rules must stay visible in every report"
    assert pending | set(coverage["implemented"]) == set(qa.RULES)


# --------------------------------------------------------------------------
# providers and offline guarantees
# --------------------------------------------------------------------------
def test_translation_memory_prefers_exact_and_flags_case_matches():
    provider = providers.TranslationMemoryProvider({"Settings": "设置"})
    proposals = provider.propose([
        candidates_mod.Candidate(source="Settings", target=""),
        candidates_mod.Candidate(source="settings", target=""),
        candidates_mod.Candidate(source="Unrelated text", target=""),
    ])
    by_source = {proposal.source: proposal for proposal in proposals}
    assert by_source["Settings"].confidence == providers.HIGH
    assert by_source["settings"].confidence == providers.MEDIUM
    assert "Unrelated text" not in by_source


def test_file_provider_wins_over_translation_memory():
    memory = providers.TranslationMemoryProvider({"Settings": "设置"})
    overlay = providers.FileProvider({"Settings": "设定"})
    candidates = [candidates_mod.Candidate(source="Settings", target="")]
    proposals, counts = providers.collect_proposals(candidates, [overlay, memory])
    assert counts == {"file": 1, "tm": 1}
    assert proposals["Settings"].target == "设定"
    assert proposals["Settings"].provider == "file"


def test_command_provider_output_is_quarantined_at_low_confidence():
    script = (
        "import json,sys;"
        "payload=json.load(sys.stdin);"
        "print(json.dumps({'translations': {item['source']: '新文本' for item in payload['items']}}))"
    )
    provider = providers.CommandProvider([sys.executable, "-c", script])
    candidates = [candidates_mod.Candidate(source="Some new string", target="")]
    proposals, counts = providers.collect_proposals(candidates, [provider])
    assert counts["cmd"] == 1
    assert proposals["Some new string"].confidence == providers.LOW

    plan = merge.plan_merge({}, proposals)
    assert plan.additions == {}
    assert plan.quarantined[0]["reason"].startswith("confidence:low")


def test_online_provider_requires_both_switches_and_has_no_implementation(scratch_repo):
    candidates = write_candidates(scratch_repo)

    without_switches = report_of(run_cli(
        "release", "--repo-root", scratch_repo, "--candidates", candidates,
        "--provider", "online", "--json", expect=4))
    assert "AG_L10N_ALLOW_NETWORK" in without_switches["error"]

    with_env_only = report_of(run_cli(
        "release", "--repo-root", scratch_repo, "--candidates", candidates,
        "--provider", "online", "--json", expect=4,
        env_extra={"AG_L10N_ALLOW_NETWORK": "1"}))
    assert "AG_L10N_ALLOW_NETWORK" in with_env_only["error"]

    with_both = report_of(run_cli(
        "release", "--repo-root", scratch_repo, "--candidates", candidates,
        "--provider", "online", "--allow-network", "--json", expect=4,
        env_extra={"AG_L10N_ALLOW_NETWORK": "1"}))
    assert "stub" in with_both["error"]


def test_localization_package_contains_no_network_code():
    forbidden = ("socket", "ssl", "urllib", "http", "requests", "aiohttp", "httpx", "ftplib", "smtplib")
    for path in sorted((SCRIPTS_DIR / "localization").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for module in forbidden:
            pattern = r"(?m)^\s*(?:import|from)\s+" + re.escape(module) + r"\b"
            assert not re.search(pattern, text), "{} imports {}".format(path.name, module)


def test_a_full_dry_run_never_creates_a_socket(scratch_repo, monkeypatch):
    candidates = write_candidates(scratch_repo)

    def refuse(*_args, **_kwargs):
        raise AssertionError("the pipeline tried to open a socket")

    monkeypatch.setattr(socket, "socket", refuse)
    options = pipeline.Options(
        command="release",
        repo_root=scratch_repo,
        candidates_path=candidates,
        translations_path=candidates,
    )
    exit_code, report = pipeline.run(options)
    assert exit_code == 0, report.get("error")
    assert report["mode"] == "dry-run"
    assert report["plan"]["additions"] == len(EXPECTED_ADDITIONS)


def test_tsv_overlay_and_candidate_map_format(scratch_repo):
    overlay = scratch_repo / "overlay.tsv"
    overlay.write_text(
        "original\ttarget\n"
        "New menu entry\t新菜单项\n"
        "Another entry\t另一个条目\n",
        encoding="utf-8",
    )
    candidates = write_candidates(scratch_repo, [
        {"original": "New menu entry", "translation": ""},
        {"original": "Another entry", "translation": ""},
    ])
    report = report_of(run_cli(
        "release", "--repo-root", scratch_repo, "--candidates", candidates,
        "--translations", overlay, "--provider", "file", "--json", expect=0))
    assert report["plan"]["additions"] == 2
    assert {item["target"] for item in report["plan"]["additions_sample"]} == {"新菜单项", "另一个条目"}

    mapping_path = scratch_repo / "map.json"
    mapping_path.write_text(json.dumps({"Settings": "设置", "New menu entry": "新菜单项"},
                                       ensure_ascii=False), encoding="utf-8")
    loaded = candidates_mod.load_candidates(mapping_path)
    assert {candidate.source for candidate in loaded} == {"Settings", "New menu entry"}
    assert {candidate.target for candidate in loaded} == {"设置", "新菜单项"}


def test_human_output_is_printed_without_json(scratch_repo):
    candidates = write_candidates(scratch_repo)
    proc = run_cli("release", "--repo-root", scratch_repo, "--candidates", candidates,
                   "--translations", candidates, expect=0)
    assert "localize release (dry-run)" in proc.stdout
    assert "QA (proposals)" in proc.stdout
    assert "hint:" in proc.stdout
    assert "not implemented in this MVP" in proc.stdout
