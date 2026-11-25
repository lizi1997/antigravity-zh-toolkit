#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline localization pipeline - command line entry point.

    python scripts/localize.py release --translations untranslated_candidates.json   # dry-run
    python scripts/localize.py release --translations untranslated_candidates.json --apply
    python scripts/localize.py qa                                                   # dictionary check
    python scripts/localize.py merge --translations overlay.tsv --apply             # dictionary only

``release`` is a dry-run unless ``--apply`` is passed. See
``docs/auto-localization-mvp.md`` for scope and honest limitations.
"""

import os
import sys

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from localization.cli import main  # noqa: E402  (import after sys.path setup)

if __name__ == "__main__":
    raise SystemExit(main())
