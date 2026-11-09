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
        ("This folder belongs to the WSL distro \"Ubuntu\", but this window is connected to \"Debian\".", "此文件夹属于 WSL 发行版“Ubuntu”，但当前窗口连接的是“Debian”。"),
        ("Installing into Ubuntu…", "正在安装到 Ubuntu…"),
        ("This location cannot be opened in WSL: C:\\foo", "无法在 WSL 中打开此位置: C:\\foo"),
        ("Preview unavailable — notebook parse failed", "无法预览：notebook parse failed"),
        ("Comment (Ctrl+Alt+M)", "评论（Ctrl+Alt+M）"),
        ("Comments (3)", "评论（3）"),
        ("Comment on page 4", "第 4 页的评论"),
        ("Read URL: https://example.com", "读取 URL：https://example.com"),
        ("Show 8 breakdowns", "显示 8 项明细"),
        ("Show 1 breakdown", "显示 1 项明细"),
        ("3 demoted", "3 项已降级"),
        ("2 excluded", "2 项已排除"),
        ("4 tools excluded", "4 个工具已排除"),
        ("1 tool excluded", "1 个工具已排除"),
        ("8 tools", "8 个工具"),
        ("2 rules exceeded the rules budget and were demoted from full inline content to a file-path pointer.", "2 条规则超出规则预算，已从完整内容降级为文件路径指针。"),
        ("1 item in Skills exceeded the customization budget and was excluded from context.", "Skills 中有 1 项超出自定义配置预算，已从上下文中排除。"),
        ("Exceeded the rules token budget. Full rule content (1,426 tokens) was replaced with a lightweight file-path pointer in context.", "已超出规则 token 预算。完整规则内容（1,426 个 token）已替换为轻量的文件路径指针。"),
        ("All tools in this MCP server (800 tokens) exceeded the customization budget and were excluded from context.", "此 MCP 服务器中的全部工具（800 个 token）已超出自定义配置预算，并从上下文中排除。"),
        ("3 tools in this MCP server (800 tokens) exceeded the customization budget and were excluded from context.", "此 MCP 服务器中有 3 个工具（800 个 token）已超出自定义配置预算，并从上下文中排除。"),
        ("Exceeded the customization token budget (120 tokens) and was excluded from context.", "已超出自定义配置 token 预算（120 个 token），并从上下文中排除。"),
        ("Failed to update agent: boom", "更新智能体失败：boom"),
        ("Failed to toggle plugin: boom", "切换插件失败：boom"),
        ('The WSL distro "Ubuntu" is no longer installed.', "WSL 发行版“Ubuntu”已不再安装。"),
    ],
)
def test_pattern_expected_translations(source, expected):
    assert translate_pattern_pass(source) == expected
