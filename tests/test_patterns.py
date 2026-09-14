"""Behavioural tests for locales/patterns.json replacement rules.

Mirrors the engine's pattern pass: first matching rule wins, replacement is a
plain string (so `$1` expands to the capture group and `${...}` stays literal).
The two known-garbage rules are marked xfail on purpose - see FIX_PLAN.md
("范围外声明") for the decision to keep them unfixed for now.
"""

import json
import re
from pathlib import Path

import pytest

LOCALES_DIR = Path(__file__).resolve().parents[1] / "locales"


def load_patterns():
    return json.loads((LOCALES_DIR / "patterns.json").read_text(encoding="utf-8"))


def translate_pattern_pass(text, pats=None):
    """Engine-equivalent: iterate rules in order, first match wins."""
    pats = pats if pats is not None else load_patterns()
    trimmed = text.strip()
    for p in pats:
        flags = re.IGNORECASE
        if "m" in (p.get("flags") or ""):
            flags |= re.MULTILINE
        try:
            rx = re.compile(p["pattern"], flags)
        except re.error:
            continue  # JS-only regex constructs stay untestable from Python
        if rx.search(trimmed):
            # JS string replacement uses $1 style captures; convert to Python's.
            repl = p["replacement"].replace("\\", "\\\\")
            repl = re.sub(r"\$(\d+)", lambda m: "\\" + m.group(1), repl)
            return rx.sub(repl, trimmed)
    return None


def test_patterns_file_structure():
    pats = load_patterns()
    assert isinstance(pats, list) and len(pats) > 50
    for p in pats:
        assert set(p) <= {"pattern", "flags", "replacement"}, p
        assert isinstance(p["pattern"], str) and p["pattern"]
        assert isinstance(p["replacement"], str)


def test_zh_dictionary_loads():
    zh = json.loads((LOCALES_DIR / "zh-CN.json").read_text(encoding="utf-8"))
    assert isinstance(zh, dict) and len(zh) > 1200
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in zh.items())


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Refreshes in 5 days", "5 天后刷新"),
        ("Refreshes in 2 minutes, 30 seconds", "2 分钟 30 秒后刷新"),
        ("You have used some of your weekly limit, it will fully refresh in 3 days.",
         "您已使用部分每周额度，将在 3 天后完全刷新。"),
        ("Worked for 5 seconds", "工作了 5 秒"),
        ("Thought for 3 hours", "思考了 3 小时"),
        ("7 files changed", "7 个文件已更改"),
        ("Error: something bad happened", "错误：something bad happened"),
        ("Go to Request #12", "转到请求 #12"),
        ("Select model, current: Gemini", "选择模型，当前：Gemini"),
    ],
)
def test_pattern_expected_translations(source, expected):
    assert translate_pattern_pass(source) == expected


@pytest.mark.xfail(
    reason="已知垃圾输出：replacement 含未求值的 ${unit ...} 模板（修复决策见 FIX_PLAN.md 范围外声明）",
    strict=False,
)
@pytest.mark.parametrize("source", ["Worked for 5s", "Thought for 2m"])
def test_pattern_compact_unit_rules_are_broken(source):
    assert translate_pattern_pass(source) == f"工作了 5 秒"


@pytest.mark.xfail(
    reason='已知垃圾输出：replacement 带字面双引号，如 now -> "刚刚"（修复决策见 FIX_PLAN.md 范围外声明）',
    strict=False,
)
@pytest.mark.parametrize("source", ["now", "Account / Settings"])
def test_pattern_quoted_replacements_are_broken(source):
    assert translate_pattern_pass(source) is not None
    out = translate_pattern_pass(source)
    assert not out.startswith('"') and not out.endswith('"')
