"""Behavioural tests for locales/patterns.json replacement rules.

Mirrors the engine's pattern pass: first matching rule wins and replacements
use JavaScript-style `$1` capture groups.
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
        ("Worked for 5s", "工作了 5 秒"),
        ("Worked for 2.5m", "工作了 2.5 分钟"),
        ("Worked for 1h", "工作了 1 小时"),
        ("Thought for 5s", "思考了 5 秒"),
        ("Thought for 2m", "思考了 2 分钟"),
        ("Thought for 1.5h", "思考了 1.5 小时"),
        ("now", "刚刚"),
        ("Account / Settings", "账户设置"),
        ("7 files changed", "7 个文件已更改"),
        ("Error: something bad happened", "错误：something bad happened"),
        ("Go to Request #12", "转到请求 #12"),
        ("Select model, current: Gemini", "选择模型，当前：Gemini"),
        ("Models within this group: Gemini Flash, Gemini Pro", "该组包含的模型: Gemini Flash, Gemini Pro"),
        ("Alt+Enter Sends immediately", "Alt+Enter：立即发送"),
        ("Enter Queues after the turn", "Enter：在当前轮次后排队"),
    ],
)
def test_pattern_expected_translations(source, expected):
    assert translate_pattern_pass(source) == expected
