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


def test_dictionary_keys_have_no_surrounding_whitespace():
    """The engine looks entries up by the *trimmed* UI text.

    A key with leading/trailing whitespace therefore can never match, which
    silently leaves that UI string in English forever.
    """
    zh = json.loads((LOCALES_DIR / "zh-CN.json").read_text(encoding="utf-8"))
    padded = [k for k in zh if k != k.strip()]
    assert padded == [], f"keys can never match: {padded[:5]}"


def test_every_dictionary_entry_is_reachable():
    """Every entry must be findable through the engine's lookup order.

    Mirrors engine_template.js translateText(): exact match, then the
    lowercase index, then the pattern rules.
    """
    zh = json.loads((LOCALES_DIR / "zh-CN.json").read_text(encoding="utf-8"))
    pats = load_patterns()
    lower = {k.lower(): v for k, v in zh.items()}

    def lookup(text):
        t = text.strip()
        if not t or re.search(r"[\u4e00-\u9fff]", t):
            return None
        if t in zh:
            return zh[t]
        if t.lower() in lower:
            return lower[t.lower()]
        for p in pats:
            flags = re.IGNORECASE
            if "m" in (p.get("flags") or ""):
                flags |= re.MULTILINE
            try:
                rx = re.compile(p["pattern"], flags)
            except re.error:
                continue
            if rx.search(t):
                return True
        return None

    unreachable = []
    for key in zh:
        # The engine never looks up text that already contains CJK.
        if re.search(r"[\u4e00-\u9fff]", key):
            continue
        if lookup(key) is None:
            unreachable.append(key)
    assert unreachable == [], f"unreachable entries: {unreachable[:5]}"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        # Fragment-shaped strings: the variable part lives in the middle, so
        # only a pattern rule can match the full sentence.
        ("In addition to the custom skills folder, Antigravity will search the following paths in order to find skills for the agent.",
         "除了自定义技能文件夹，Antigravity 将按顺序搜索以下路径，以寻找智能体的技能。"),
        ("Changes the base URL for marketplace search results. You must restart Antigravity to use the new marketplace after changing this value.",
         "更改插件市场搜索结果的基准 URL。更改此值后，您必须重启 Antigravity 才能使用新的插件市场。"),
        ("Changes the base URL on each extension page. You must restart Antigravity.",
         "更改每个扩展页面的基准 URL。您必须重启 Antigravity。"),
        ("Receive product updates, tips, and promotions from Google Antigravity via email.",
         "通过电子邮件接收来自 Google Antigravity 的产品更新、提示和促销信息。"),
        ("When toggled on, Antigravity collects usage data to help Google enhance performance and features.",
         "开启后，Antigravity 将收集使用数据，以帮助 Google 提升性能并改进功能。"),
        ("This request will use your AI credits to fulfill model requests once you're out of model quota.",
         "This request 将在您的模型配额用尽时使用您的 AI 积分来满足模型请求。"),
        ("Requests will always use your model quota first before using AI credits.",
         "Requests 将始终在开始使用 AI 积分之前优先使用您的模型配额。"),
        ("Sign in to use Advanced", "登录以使用 Advanced"),
        ("5 tokens", "5 个 Token"),
        ("3 comments", "3 条评论"),
        ("Build with Gemini 3 Pro", "使用 Gemini 3 Pro"),
        ("There are currently no Build with Gemini 3 Pro plugins available.",
         "目前没有使用 Gemini 3 Pro 插件可供使用。"),
        ("No MCP servers found for My Server", "未找到匹配的 MCP 服务器：My Server"),
        ("No handlers configured for My Hook", "未配置处理程序：My Hook"),
        ("Add New Handler to My Hook", "添加新处理程序到 My Hook"),
    ],
)
def test_previously_unreachable_strings_are_translated(source, expected):
    """Regression guard for the 31 dictionary entries that used to carry
    surrounding whitespace and could never be matched."""
    assert translate_pattern_pass(source) == expected


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
