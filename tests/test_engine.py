"""Engine-level assertions (engine/engine_template.js).

The engine is injected into the Electron renderer, so most of its behaviour
cannot be exercised from Python. These tests guard the properties that are
cheap to assert statically and easy to break silently.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_TEMPLATE = REPO_ROOT / "engine" / "engine_template.js"
ENGINE_GENERATED = REPO_ROOT / "engine" / "ag_localization_engine.js"


def read_template():
    return ENGINE_TEMPLATE.read_text(encoding="utf-8")


def test_engine_warns_when_hot_reload_is_unavailable():
    """The client runs the renderer sandboxed, so the runtime hot-reload path
    is dead code there. It must at least say so instead of failing silently."""
    src = read_template()
    assert "Runtime dictionary hot loading is unavailable" in src
    assert "console.warn" in src


def test_engine_header_does_not_promise_hot_reloading():
    """The header comment must not claim a capability the client lacks."""
    header = "\n".join(read_template().splitlines()[:12])
    assert "hot-reload" not in header.lower()
    assert "hot reload" not in header.lower()


def test_engine_documents_the_sandbox_constraint():
    src = read_template()
    assert "sandbox" in src.lower()
    # The reason has to be stated, not just the limitation.
    assert re.search(r"require\('fs'\)|require\(\"fs\"\)", src)


def test_generated_engine_matches_template_structure():
    """The generated engine must still carry the template's logic."""
    gen = ENGINE_GENERATED.read_text(encoding="utf-8")
    assert "AG_ZH_ZH_START" in gen and "AG_ZH_PATTERNS_START" in gen
    assert "Runtime dictionary hot loading is unavailable" in gen


def test_generated_engine_embeds_the_current_dictionaries():
    """The generated engine must contain the current dictionary, not a stale
    copy - the dictionary is the only thing that reaches the client."""
    import json
    gen = ENGINE_GENERATED.read_text(encoding="utf-8")
    zh = json.loads((REPO_ROOT / "locales" / "zh-CN.json").read_text(encoding="utf-8"))
    pats = json.loads((REPO_ROOT / "locales" / "patterns.json").read_text(encoding="utf-8"))

    m = re.search(r"AG_ZH_ZH_START\*/(.*?)/\*AG_ZH_ZH_END\*/", gen, re.S)
    assert m, "embedded dictionary block not found"
    assert len(json.loads(m.group(1))) == len(zh)

    m = re.search(r"AG_ZH_PATTERNS_START\*/(.*?)/\*AG_ZH_PATTERNS_END\*/", gen, re.S)
    assert m, "embedded pattern block not found"
    assert len(json.loads(m.group(1))) == len(pats)


def _node_available():
    import shutil
    return shutil.which("node") is not None


def test_escape_dollar_is_not_a_noop():
    """`escapeDollar` must really double the '$'.

    With a *string* replacement "$$" collapses straight back to "$", which
    makes the escaping useless and lets "$&" / "$'" inside a translation be
    expanded by String.replace. The replacer therefore has to be a function.
    """
    import shutil, subprocess, tempfile
    if shutil.which("node") is None:
        import pytest
        pytest.skip("node is not available")

    src = read_template()
    fn = re.search(r"function escapeDollar\(s\) \{.*?\n    \}", src, re.S)
    assert fn, "escapeDollar not found in the engine template"

    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "check.js"
        script.write_text(
            fn.group(0) + """
const value = "Price is $10 and $& and $' here";
const escaped = escapeDollar(value);
console.log("unchanged=" + (escaped === value));
console.log("result=" + JSON.stringify("Replace ME now".replace("ME", escaped)));
""", encoding="utf-8")
        r = subprocess.run(["node", str(script)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
    out = r.stdout
    assert "unchanged=false" in out, out
    assert "Price is $10 and $& and $' here" in out, out


def test_dictionaries_cannot_spoof_the_splice_markers():
    """A dictionary value carrying a splice marker would make the next splice
    cut the engine in the wrong place - the build must reject it."""
    import json
    import shutil, subprocess
    if shutil.which("node") is None:
        import pytest
        pytest.skip("node is not available")

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import patcher
    for marker in ("/*AG_ZH_ZH_START*/", "/*AG_ZH_ZH_END*/",
                   "/*AG_ZH_PATTERNS_START*/", "/*AG_ZH_PATTERNS_END*/"):
        assert patcher.contains_sentinel_marker(json.dumps({"k": marker})), marker
        assert not patcher.contains_sentinel_marker(json.dumps({"k": "plain text"}))

    # the shipped dictionaries must be clean
    for name in ("zh-CN.json", "patterns.json"):
        text = (REPO_ROOT / "locales" / name).read_text(encoding="utf-8")
        assert not patcher.contains_sentinel_marker(text), name


def test_textarea_and_contenteditable_attributes_are_translated():
    """<textarea> and contentEditable elements must still have their own UI
    attributes (placeholder, aria-label, title) translated before their
    editable subtree is skipped."""
    src = read_template()
    assert "function hasTranslatableOwnAttrs(el)" in src
    assert "if (hasTranslatableOwnAttrs(root)) translateElementAttrs(root);" in src
    assert "if (hasTranslatableOwnAttrs(node)) translateElementAttrs(node);" in src
    assert "attributeFilter: TRANSLATABLE_ATTRS" in src

