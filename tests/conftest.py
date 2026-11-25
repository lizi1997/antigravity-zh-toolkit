"""Shared pytest fixtures: expose scripts/patcher.py on sys.path."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import patcher  # noqa: E402  (needs the sys.path hook above)


@pytest.fixture(autouse=True)
def _no_running_client(monkeypatch):
    """Stub the running-client guard: unit tests control that precondition.

    The real guard is covered by dedicated tests that re-enable it. Without
    this stub the suite would depend on whether Antigravity happens to be
    running on the machine executing the tests.
    """
    monkeypatch.setattr(patcher, "is_antigravity_running", lambda: False)
