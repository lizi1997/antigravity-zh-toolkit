# -*- coding: utf-8 -*-
"""Deterministic QA gate for proposed dictionary entries.

The gate is the only place where a machine proposal may become a dictionary
entry. It is pure, offline and unit-testable: every rule is a function of
``(source, target)`` plus, for two batch-level rules, the existing dictionary.

Coverage is stated, not implied: :data:`RULES` marks each design rule
as implemented or as an
explicit TODO, and every report carries that list. H1-H13, H21 and H23 are
implemented here; H14-H20 and H22 are not.
"""

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

from .textutils import (
    contains_sentinel,
    has_invisible_char,
    has_stray_surrogate,
    preview,
)

SEVERITY_RANK = {"blocker": 3, "major": 2, "minor": 1}


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: str
    implemented: bool
    note: str = ""


#: Design §4.4.3 rule table. ``implemented=False`` entries are honest TODOs: the
#: CLI prints them as ``not_implemented`` instead of pretending full coverage.
RULES = {
    "H1": Rule("H1", "placeholder fidelity", "blocker", True),
    "H2": Rule("H2", "URL / file-name fidelity", "blocker", True),
    "H3": Rule("H3", "code identifier fidelity", "blocker", True),
    "H4": Rule("H4", "HTML tag structure", "blocker", True),
    "H5": Rule("H5", "empty / whitespace-only translation", "blocker", True),
    "H6": Rule("H6", "key has leading/trailing whitespace", "blocker", True),
    "H7": Rule("H7", "engine splice-marker injection", "blocker", True),
    "H8": Rule("H8", "stray surrogate / BOM / zero-width / bidi control", "blocker", True),
    "H9": Rule("H9", "one source mapped to conflicting targets", "blocker", True),
    "H10": Rule("H10", "glossary term missing from translation", "blocker", True),
    "H11": Rule("H11", "forbidden glossary variant used", "major", True),
    "H12": Rule("H12", "length budget / overlong source", "major", True),
    "H13": Rule("H13", "fragment shape changed", "major", True),
    "H14": Rule("H14", "punctuation style", "minor", False, "not implemented in the MVP"),
    "H15": Rule("H15", "newline count changed", "major", False, "not implemented in the MVP"),
    "H16": Rule("H16", "English residue", "minor", False, "not implemented in the MVP"),
    "H17": Rule("H17", "pattern rule compiles / flags", "blocker", False,
                "pattern merging is out of scope in the MVP"),
    "H18": Rule("H18", "pattern anchoring / capture-group reference", "blocker", False,
                "pattern merging is out of scope in the MVP"),
    "H19": Rule("H19", "duplicate / shadowing pattern rule", "blocker", False,
                "pattern merging is out of scope in the MVP"),
    "H20": Rule("H20", "ReDoS heuristic", "major", False, "pattern merging is out of scope in the MVP"),
    "H21": Rule("H21", "case collision with an existing key", "major", True),
    "H22": Rule("H22", "duplicate target for opposite sources", "minor", False,
                "not implemented in the MVP"),
    "H23": Rule("H23", "NFC normalization", "minor", True),
}

#: The engine looks entries up through a lower-cased index
#: (``engine_template.js:34-36``), so two keys that differ only in case are not
#: independent entries.

#: CONTRIBUTING.md §词条翻译规范 + design §4.4.3 H10/H11.
GLOSSARY = {
    "agent": ("智能体", ("代理",)),
    "subagent": ("子智能体", ("子代理",)),
    "workspace": ("工作区", ("工作空间",)),
    "quota": ("配额", ("限额",)),
    "credits": ("积分", ("信用",)),
    "permissions": ("权限", ()),
    "customizations": ("自定义配置", ("定制",)),
    "trajectory": ("轨迹", ()),
}

#: Acronyms the project always keeps verbatim. Deliberately a short allow-list:
#: a blanket ``[A-Z]{2,}`` rule would reject legitimate translations ("URL bar"
#: -> "地址栏", "UI" -> "界面") and legitimate button labels ("OK").
ACRONYMS = (
    "MCP", "API", "JSON", "JSONL", "HTTP", "HTTPS", "SSH", "TLS", "OAuth",
    "OIDC", "ASAR", "SHA", "CSV", "TSV", "WSL", "NFC", "PDF", "GPT",
)

_FILE_EXTENSIONS = (
    "js|ts|tsx|jsx|json|jsonl|py|exe|dll|asar|css|html?|png|jpe?g|gif|svg|go|"
    "md|zip|sh|bat|cmd|toml|ya?ml|csv|tsv|pdf|lock"
)

_RE_PLACEHOLDER_PATTERNS = (
    ("brace", re.compile(r"\{\{?\s*\$?[A-Za-z0-9_.:-]+\s*\}?\}")),
    ("dollar", re.compile(r"\$\{[^}\n]+\}")),
    ("percent", re.compile(r"%(?:\d+\$)?[sdifxX]")),
    ("positional", re.compile(r"\$[1-9](?!\d)")),
)
_RE_URL = re.compile(r"https?://[^\s<>\"'`）)\]]+")
_RE_FILENAME = re.compile(r"(?<![\w.-])(?:[\w.-]+)\.(?:" + _FILE_EXTENSIONS + r")\b", re.IGNORECASE)
_RE_HTML_TAG = re.compile(r"<\s*(/?)\s*([a-zA-Z][a-zA-Z0-9-]*)")
_RE_GLOSSARY = re.compile(r"\b(" + "|".join(GLOSSARY) + r")\b", re.IGNORECASE)
_RE_ACRONYM = re.compile(r"\b(?:" + "|".join(sorted(ACRONYMS, key=len, reverse=True)) + r")\b")


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    source: str = ""
    target: str = ""
    origin: str = ""

    def as_dict(self):
        return {
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "source": preview(self.source, 160),
            "target": preview(self.target, 160),
            "origin": self.origin,
        }


@dataclass
class QaEntry:
    """One proposed dictionary entry plus where it came from."""

    source: str
    target: str
    origin: str = ""
    confidence: str = "high"
    stray_surrogate: bool = False


@dataclass
class QaReport:
    mode: str
    checked: int
    findings: list = field(default_factory=list)
    waived: list = field(default_factory=list)
    gate: str = "pass"

    def count(self, severity):
        return sum(1 for finding in self.findings if finding.severity == severity)

    def rules_with_findings(self):
        seen = []
        for finding in self.findings:
            if finding.rule not in seen:
                seen.append(finding.rule)
        return seen

    def as_dict(self, max_findings=50):
        findings = [finding.as_dict() for finding in self.findings[:max_findings]]
        return {
            "mode": self.mode,
            "checked": self.checked,
            "gate": self.gate,
            "blockers": self.count("blocker"),
            "majors": self.count("major"),
            "minors": self.count("minor"),
            "rules_with_findings": self.rules_with_findings(),
            "findings_truncated": len(self.findings) > len(findings),
            "findings": findings,
            "waived": list(self.waived),
            "coverage": coverage(),
        }


def coverage():
    """Which design rules this module actually implements."""
    implemented = [rule.id for rule in RULES.values() if rule.implemented]
    pending = [
        {"rule": rule.id, "title": rule.title, "note": rule.note}
        for rule in RULES.values()
        if not rule.implemented
    ]
    return {"implemented": implemented, "not_implemented": pending}


# --------------------------------------------------------------------------
# tokenizers
# --------------------------------------------------------------------------
def placeholders(text):
    """Multiset of placeholder tokens, grouped by kind.

    ``$1`` is matched after ``${...}`` so a JS template placeholder is never
    mistaken for a positional argument.
    """
    masked = text
    found = Counter()
    for kind, regex in _RE_PLACEHOLDER_PATTERNS:
        for match in regex.finditer(masked):
            found[(kind, re.sub(r"\s+", "", match.group(0)))] += 1
        masked = regex.sub(lambda m: " " * len(m.group(0)), masked)
    return found


def urls(text):
    return Counter(match.group(0).rstrip(".,;:!?") for match in _RE_URL.finditer(text))


def filenames(text):
    return Counter(match.group(0) for match in _RE_FILENAME.finditer(text))


def identifiers(text):
    """Code-ish tokens that must survive translation verbatim."""
    found = Counter()
    for match in re.finditer(r"`([^`\n]+)`", text):
        found[("backtick", match.group(1).strip())] += 1
    for match in re.finditer(r"(?<![\w-])--[a-z][a-z0-9-]+", text):
        found[("flag", match.group(0))] += 1
    for match in re.finditer(r"\b(?:Ctrl|Alt|Shift|Meta|Cmd|Win)(?:\+[A-Za-z0-9]+){1,3}\b", text):
        found[("chord", match.group(0))] += 1
    for match in re.finditer(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", text):
        found[("allcaps", match.group(0))] += 1
    for match in re.finditer(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b", text):
        found[("snake", match.group(0))] += 1
    for match in re.finditer(r"\b[a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)+\b", text):
        found[("camel", match.group(0))] += 1
    for match in _RE_ACRONYM.finditer(text):
        found[("acronym", match.group(0))] += 1
    return found


def html_tags(text):
    """Ordered tag sequence: ``[(name, is_closing), ...]``."""
    return [(name.lower(), bool(closing)) for closing, name in _RE_HTML_TAG.findall(text)]


def normalize(text):
    """NFC normalization (rule H23)."""
    return unicodedata.normalize("NFC", text)


def _missing_tokens(source_tokens, target_text, key_kind):
    """Tokens whose occurrence count in *target_text* is lower than in the source.

    Placeholder and identifier counters are keyed by ``(kind, token)``; URL and
    file-name counters are keyed by the token itself.
    """
    missing = []
    for token, count in source_tokens.items():
        token_text = token[1] if key_kind in ("placeholder", "identifier") else token
        if target_text.count(token_text) < count:
            missing.append(token_text)
    return missing


# --------------------------------------------------------------------------
# entry-level rules
# --------------------------------------------------------------------------
def check_entry(entry):
    """Run H1-H8, H10-H13 and H23 against a single proposed entry."""
    findings = []
    source = entry.source
    target = entry.target

    def add(rule, message, severity=None):
        findings.append(
            Finding(
                rule=rule,
                severity=severity or RULES[rule].severity,
                message=message,
                source=source,
                target=target,
                origin=entry.origin,
            )
        )

    # H5 empty / whitespace-only translation.
    if not target.strip():
        add("H5", "translation is empty - the engine would render an empty label")

    # H6 padded key: the engine trims the UI text before lookup (engine_template.js:209).
    if source != source.strip():
        add("H6", "source key has leading/trailing whitespace and can never match")

    # H7 splice markers would break the engine dictionary splice.
    if contains_sentinel(source) or contains_sentinel(target):
        add("H7", "entry contains an engine splice marker")

    # H8 surrogate / invisible control characters.
    if entry.stray_surrogate or has_stray_surrogate(source) or has_stray_surrogate(target):
        add("H8", "entry contains an unpaired surrogate (legacy extractor crash class)")
    if has_invisible_char(source) or has_invisible_char(target):
        add("H8", "entry contains a BOM / zero-width / bidi control character")
    if "\ufffd" in source or "\ufffd" in target:
        add("H8", "entry contains U+FFFD (a surrogate was sanitized at the boundary)")

    # H1 placeholders: multiset equality, not just "present".
    source_placeholders = placeholders(source)
    target_placeholders = placeholders(target)
    if source_placeholders != target_placeholders:
        missing = _missing_tokens(source_placeholders, target, "placeholder")
        extra = _missing_tokens(target_placeholders, source, "placeholder")
        add("H1", "placeholder mismatch: missing={} extra={}".format(missing, extra))

    # H2 URLs and file names must be copied verbatim.
    missing_urls = _missing_tokens(urls(source), target, "url")
    if missing_urls:
        add("H2", "URL not preserved: {}".format(missing_urls))
    missing_files = _missing_tokens(filenames(source), target, "filename")
    if missing_files:
        add("H2", "file name not preserved: {}".format(missing_files))

    # H3 identifiers must be copied verbatim (case sensitive).
    missing_identifiers = _missing_tokens(identifiers(source), target, "identifier")
    if missing_identifiers:
        add("H3", "code identifier not preserved: {}".format(missing_identifiers))

    # H4 HTML tag sequence must not change.
    source_tags = html_tags(source)
    if source_tags and source_tags != html_tags(target):
        add("H4", "HTML tag sequence changed: {} -> {}".format(source_tags, html_tags(target)))

    # H10 / H11 glossary.
    missing_terms = []
    for match in _RE_GLOSSARY.finditer(source):
        term = match.group(1).lower()
        required, _forbidden = GLOSSARY[term]
        if required not in target:
            missing_terms.append("{}->{}".format(term, required))
    if missing_terms:
        add("H10", "glossary term missing: {}".format(missing_terms))

    stripped = source.strip().lower()
    if stripped in GLOSSARY:
        _required, forbidden = GLOSSARY[stripped]
        used = [variant for variant in forbidden if variant in target]
        if used:
            add("H11", "forbidden glossary variant: {}".format(used))

    # H12 length budget. The engine skips sources longer than 500 characters
    # outright (design baseline B13), so that is a blocker, not a warning.
    if len(source) > 500:
        add("H12", "source is longer than 500 characters; the engine skips it", severity="blocker")
    else:
        limit = max(int(1.4 * len(source)), 8)
        if len(target) > limit:
            add("H12", "translation is {} chars, budget is {} (1.4x source)".format(len(target), limit))

    # H13 fragment shape: these strings are glued to other text by the client.
    shape = _fragment_shape_problem(source, target)
    if shape:
        add("H13", shape)

    # H23 NFC.
    if normalize(target) != target:
        add("H23", "translation is not NFC-normalized (auto-normalized before merge)")

    return findings


def _fragment_shape_problem(source, target):
    source_tail = source.rstrip()
    target_tail = target.rstrip()
    checks = (
        (":", (":", "："), "source ends with ':' but the translation does not"),
        (",", (",", "，"), "source ends with ',' but the translation does not"),
        ("…", ("…", "..."), "source ends with an ellipsis but the translation does not"),
        ("...", ("…", "..."), "source ends with an ellipsis but the translation does not"),
    )
    for ending, allowed, message in checks:
        if source_tail.endswith(ending) and not target_tail.endswith(allowed):
            return message
    if source_tail.startswith("(") and not target_tail.startswith(("(", "（")):
        return "source starts with '(' but the translation does not"
    return None


# --------------------------------------------------------------------------
# batch-level rules
# --------------------------------------------------------------------------
def check_batch(entries, dictionary):
    """Run the entry rules plus H9 (conflicting targets) and H21 (case collision)."""
    findings = []
    for entry in entries:
        findings.extend(check_entry(entry))

    # H9: the engine map is injective (one source -> one target).
    by_source = {}
    for entry in entries:
        key = normalize(entry.source).strip()
        by_source.setdefault(key, []).append(entry)
    for key, group in by_source.items():
        targets = {normalize(item.target) for item in group}
        if len(targets) > 1:
            findings.append(
                Finding(
                    rule="H9",
                    severity=RULES["H9"].severity,
                    message="conflicting translations for one source: {}".format(
                        [preview(item.target, 60) for item in group]
                    ),
                    source=key,
                    target="",
                    origin="batch",
                )
            )

    # H21: the engine's lower-cased index makes case-differing keys collide.
    folded = {}
    for source in dictionary:
        folded.setdefault(source.casefold(), []).append(source)
    reported = set()
    for entry in entries:
        key = normalize(entry.source).strip()
        if key in dictionary:
            continue  # exact entries are protected by the merge (human wins)
        collisions = [
            existing for existing in folded.get(key.casefold(), [])
            if existing != key and dictionary[existing] != entry.target
        ]
        if collisions and key.casefold() not in reported:
            reported.add(key.casefold())
            findings.append(
                Finding(
                    rule="H21",
                    severity=RULES["H21"].severity,
                    message="case collision with {}: the engine's lower-cased index keeps one of them".format(
                        collisions[:3]
                    ),
                    source=key,
                    target=entry.target,
                    origin=entry.origin,
                )
            )
    return findings


def run_qa(entries, dictionary, waive=(), extra_findings=()):
    """Full gate for proposed entries. ``waive`` names rules recorded as waived.

    ``extra_findings`` lets the caller inject findings that need input the entry
    list cannot express (for example conflicting duplicate rows in the candidate
    file, which the provider chain has already collapsed by source).
    """
    waived_rules = set(waive)
    findings = list(check_batch(entries, dictionary)) + list(extra_findings)
    waived = []
    kept = []
    for finding in findings:
        if finding.rule in waived_rules:
            waived.append({"rule": finding.rule, "source": preview(finding.source, 120),
                           "reason": "waived via --waive"})
        else:
            kept.append(finding)
    report = QaReport(mode="proposals", checked=len(entries), findings=kept, waived=waived)
    report.gate = "fail" if any(item.severity in ("blocker", "major") for item in kept) else "pass"
    return report


# --------------------------------------------------------------------------
# dictionary-level checks (``localize qa --dict``)
# --------------------------------------------------------------------------
def run_dictionary_qa(dictionary, strict=False):
    """Structural checks on the shipped dictionary.

    Only the rules that cannot be satisfied by *existing* content are applied
    here: H5-H8, H12 (overlong keys), H21 (case collisions) and H23. H1-H4 and
    H10-H13 describe *new* proposals, and applying them retroactively would
    drown real regressions in legacy noise (documented in the MVP doc).
    """
    findings = []
    for source, target in dictionary.items():
        if not isinstance(target, str):
            findings.append(Finding("H5", "blocker", "translation is not a string", source, str(target), "dictionary"))
            continue
        if not target.strip():
            findings.append(Finding("H5", "blocker", "empty translation", source, target, "dictionary"))
        if source != source.strip():
            findings.append(Finding("H6", "blocker", "key has leading/trailing whitespace", source, target, "dictionary"))
        if contains_sentinel(source) or contains_sentinel(target):
            findings.append(Finding("H7", "blocker", "engine splice marker present", source, target, "dictionary"))
        if has_stray_surrogate(source) or has_stray_surrogate(target) or has_invisible_char(target):
            findings.append(Finding("H8", "blocker", "stray surrogate / invisible control character", source, target, "dictionary"))
        if len(source) > 500:
            findings.append(Finding("H12", "major", "key is longer than 500 chars; the engine skips it", source, target, "dictionary"))
        if normalize(target) != target:
            findings.append(Finding("H23", "minor", "translation is not NFC-normalized", source, target, "dictionary"))

    folded = {}
    for source in dictionary:
        folded.setdefault(source.casefold(), []).append(source)
    for group in folded.values():
        if len(group) > 1:
            targets = {dictionary[source] for source in group}
            if len(targets) > 1:
                findings.append(
                    Finding("H21", "major", "case collision with different translations: {}".format(group[:4]),
                            group[0], "", "dictionary")
                )

    report = QaReport(mode="dictionary", checked=len(dictionary), findings=findings)
    has_problem = any(item.severity == "blocker" or (strict and item.severity == "major") for item in findings)
    report.gate = "fail" if has_problem else "pass"
    return report
