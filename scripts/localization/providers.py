# -*- coding: utf-8 -*-
"""Translation providers for the localization MVP.

Priority chain (first proposal for a source wins):

1. ``file``  - an explicit JSON/TSV overlay, i.e. a human decision;
2. ``tm``    - translation memory built from the shipped dictionary
               (exact -> case-insensitive -> standalone glossary term);
3. ``cmd``   - an external command adapter (stdin/stdout JSON);
4. ``online``- **interface stub only**: it refuses to run unless both switches
               are present, and even then it raises ``ProviderFailure``. There is
               no network code in this package.

``tm`` and ``file`` are deterministic and offline. ``cmd`` is offline by
construction (it only runs a local process) but its output is untrusted, so its
proposals default to confidence ``low`` and are quarantined unless the caller
raises the confidence explicitly.
"""

import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field

from .qa import GLOSSARY

HIGH, MEDIUM, LOW = "high", "medium", "low"

#: A standalone glossary term can be translated by the TM without context.
GLOSSARY_EXACT = {term: required for term, (required, _forbidden) in GLOSSARY.items()}


class ProviderFailure(RuntimeError):
    """A provider could not produce proposals."""


class NetworkNotAllowed(ProviderFailure):
    """A network-backed provider was requested without the double switch."""


@dataclass(frozen=True)
class Proposal:
    source: str
    target: str
    provider: str
    confidence: str = HIGH
    evidence: dict = field(default_factory=dict)


@dataclass
class ProviderInfo:
    name: str
    requires_network: bool
    deterministic: bool
    proposals: int = 0


class BaseProvider:
    name = "base"
    requires_network = False
    deterministic = True

    def propose(self, candidates):
        raise NotImplementedError

    def info(self, proposals=0):
        return ProviderInfo(
            name=self.name,
            requires_network=self.requires_network,
            deterministic=self.deterministic,
            proposals=proposals,
        )


class TranslationMemory:
    """Lookup table built from the shipped dictionary.

    Keys are matched after stripping (the engine trims the UI text before
    lookup). A case-insensitive hit is reported as ``medium`` confidence because
    the engine's own lower-cased index makes case variants ambiguous.
    """

    def __init__(self, dictionary):
        self.exact = {}
        self.folded = {}
        for source, target in dictionary.items():
            if not isinstance(target, str) or not target.strip():
                continue
            self.exact.setdefault(source.strip(), target)
            self.folded.setdefault(source.strip().casefold(), target)

    def lookup(self, source):
        key = source.strip()
        if key in self.exact:
            return self.exact[key], HIGH
        hit = self.folded.get(key.casefold())
        if hit is not None:
            return hit, MEDIUM
        return None, None

    def size(self):
        return len(self.exact)


class TranslationMemoryProvider(BaseProvider):
    name = "tm"

    def __init__(self, dictionary):
        self.memory = TranslationMemory(dictionary)

    def propose(self, candidates):
        proposals = []
        for candidate in candidates:
            source = candidate.source.strip()
            if not source:
                continue
            target, confidence = self.memory.lookup(source)
            if target is None:
                glossary = GLOSSARY_EXACT.get(source.casefold())
                if glossary:
                    target, confidence = glossary, HIGH
            if target is None:
                continue
            proposals.append(
                Proposal(source=source, target=target, provider=self.name,
                         confidence=confidence, evidence={"match": "tm"})
            )
        return proposals


class FileProvider(BaseProvider):
    """Explicit translations from a JSON/TSV overlay - treated as human input.

    The same provider also carries translations that are already embedded in the
    candidate file; *label* only records where they came from.
    """

    name = "file"

    def __init__(self, overlay, label="explicit"):
        self.overlay = dict(overlay)
        self.label = label

    def propose(self, candidates):
        proposals = []
        for candidate in candidates:
            source = candidate.source.strip()
            target = self.overlay.get(source)
            if target is None:
                target = self.overlay.get(candidate.source)
            if target is None or not target.strip():
                continue
            proposals.append(
                Proposal(source=source, target=target, provider=self.name,
                         confidence=HIGH, evidence={"match": self.label})
            )
        return proposals


class CommandProvider(BaseProvider):
    """External command adapter.

    The command receives a JSON payload on stdin::

        {"schema": 1, "items": [{"source": "...", "kind": "...", "prop": "...",
                                 "path": "...", "line": 1}, ...]}

    and must print a JSON object ``{"translations": {source: target}}`` or a list
    ``[{"source": "...", "target": "..."}]`` on stdout. Exit code != 0 is a
    provider failure. The command is executed without a shell; because its
    output is untrusted, proposals default to confidence ``low`` and therefore
    land in the quarantine bucket unless ``--cmd-confidence`` says otherwise.
    """

    name = "cmd"
    deterministic = False

    def __init__(self, command, confidence=LOW, timeout=180):
        if not command:
            raise ProviderFailure("--provider cmd requires --provider-cmd")
        self.command = shlex.split(command) if isinstance(command, str) else list(command)
        if not self.command:
            raise ProviderFailure("--provider-cmd is empty")
        self.confidence = confidence
        self.timeout = timeout

    def propose(self, candidates):
        payload = {
            "schema": 1,
            "items": [candidate.context() for candidate in candidates],
        }
        try:
            completed = subprocess.run(
                self.command,
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
            )
        except FileNotFoundError as exc:
            raise ProviderFailure("provider command not found: {} ({})".format(self.command[0], exc))
        except subprocess.TimeoutExpired:
            raise ProviderFailure("provider command timed out after {}s".format(self.timeout))
        if completed.returncode != 0:
            raise ProviderFailure(
                "provider command exited {}: {}".format(completed.returncode, (completed.stderr or "")[:400])
            )
        try:
            data = json.loads(completed.stdout or "{}")
        except ValueError as exc:
            raise ProviderFailure("provider command did not print valid JSON ({})".format(exc))

        mapping = {}
        if isinstance(data, dict) and isinstance(data.get("translations"), dict):
            mapping = data["translations"]
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and isinstance(item.get("source"), str) and isinstance(item.get("target"), str):
                    mapping[item["source"]] = item["target"]
        else:
            raise ProviderFailure("provider command output has no translations object")

        proposals = []
        for source, target in mapping.items():
            if not isinstance(source, str) or not isinstance(target, str) or not target.strip():
                continue
            proposals.append(
                Proposal(source=source, target=target, provider=self.name,
                         confidence=self.confidence, evidence={"match": "cmd"})
            )
        return proposals


class OnlineProvider(BaseProvider):
    """Interface stub for an online translation backend.

    Both switches are required (design §7.2): ``--allow-network`` **and**
    ``AG_L10N_ALLOW_NETWORK=1``. Even then this MVP has no implementation: it
    raises instead of silently pretending to translate.
    """

    name = "online"
    requires_network = True
    deterministic = False

    def __init__(self, allow_network, environ=None):
        environment = os.environ if environ is None else environ
        environment_ok = environment.get("AG_L10N_ALLOW_NETWORK") == "1"
        if not allow_network or not environment_ok:
            raise NetworkNotAllowed(
                "the 'online' provider needs BOTH --allow-network and AG_L10N_ALLOW_NETWORK=1"
            )

    def propose(self, candidates):
        raise ProviderFailure(
            "the 'online' provider is an interface stub in the MVP: no network backend exists "
            "(see docs/auto-localization-mvp.md)"
        )


def resolve_providers(provider, dictionary, overlay=None, provider_cmd=None,
                      cmd_confidence=LOW, allow_network=False, environ=None,
                      overlay_label="explicit"):
    """Build the provider chain for the requested ``--provider`` value."""
    chain = []
    overlay = overlay or {}
    provider = (provider or "tm").lower()

    if provider in ("all", "file") and overlay:
        chain.append(FileProvider(overlay, label=overlay_label))
    if provider in ("all", "tm"):
        chain.append(TranslationMemoryProvider(dictionary))
    if provider in ("all", "cmd") and provider_cmd:
        chain.append(CommandProvider(provider_cmd, confidence=cmd_confidence))
    if provider == "online":
        chain.append(OnlineProvider(allow_network, environ=environ))

    if not chain:
        if provider == "file":
            raise ProviderFailure("--provider file requires --translations")
        if provider == "cmd":
            raise ProviderFailure("--provider cmd requires --provider-cmd")
        if provider == "online":
            raise ProviderFailure("the 'online' provider is not available")
        raise ProviderFailure("no provider is available for --provider {}".format(provider))

    if overlay and provider in ("tm", "cmd", "online"):
        # The explicit overlay always participates: it is the highest-confidence
        # layer and skipping it would silently drop human decisions.
        chain.insert(0, FileProvider(overlay, label=overlay_label))

    return chain


def collect_proposals(candidates, providers):
    """Merge provider output: the first proposal for a source wins.

    Returns ``(proposals, counts)`` where ``proposals`` maps source -> Proposal
    and ``counts`` records how many proposals each provider produced (including
    those shadowed by an earlier provider, so the report does not hide them).
    """
    proposals = {}
    counts = {}
    for provider in providers:
        produced = provider.propose(candidates)
        counts[provider.name] = counts.get(provider.name, 0) + len(produced)
        for proposal in produced:
            source = proposal.source.strip()
            if not source:
                continue
            if source not in proposals:
                proposals[source] = proposal
    return proposals, counts
