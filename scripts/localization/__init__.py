# -*- coding: utf-8 -*-
"""Offline localization pipeline - MVP vertical slice.

This package implements the Phase 0-2 slice of ``docs/auto-localization-design.md``:

* :mod:`localization.candidates` - load candidate strings and translation
  overlays (JSON list/map, JSONL, TSV).
* :mod:`localization.providers` - translation memory (``tm``), explicit
  translation file (``file``) and an external command adapter (``cmd``). The
  ``online`` provider is an interface stub: this package contains **no network
  code path at all**.
* :mod:`localization.qa` - deterministic QA gate. Rules H1-H13, H21 and H23 are
  implemented; H14-H20 and H22 are registered as explicit TODOs so a report can
  never claim more coverage than the code has.
* :mod:`localization.merge` - order-preserving, byte-minimal, atomic dictionary
  merge with a pre-merge backup.
* :mod:`localization.pipeline` - ``release`` orchestration: dry-run by default,
  ``--apply`` writes the dictionary and rebuilds generated artifacts through
  ``scripts/build.py``, with rollback when the rebuild or its verification fails.

Deliberately **not** implemented (see ``docs/auto-localization-mvp.md``): the
extractor/probe rewrite, pattern-rule synthesis, engine hit counters,
``patcher patch --dry-run``, client snapshots, runtime verification and any
network translation backend.
"""

__version__ = "0.1.0"
