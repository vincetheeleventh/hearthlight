"""Root pytest configuration.

Why this file exists: `pytest` run from the repository root aborted during
COLLECTION, so the entire suite returned zero results -- not failures, no results
at all. The cause is `staging/overview-ui/test_productions.py`, which imports
`film_study_tool.*`. That package is the Film Study Tool, a sibling repository
that is not vendored here, so the import raises `ModuleNotFoundError` and pytest
stops before running anything else.

Skipping that one module makes the other 39 tests collectable and runnable. This
is a collection guard, not a verdict on the test: it is a real test of Hearthlight
Studio and it passes where `film_study_tool` is importable. If the Studio's final
home ever puts that package on the path, delete this file.

Added 2026-08-10 by the weekly workshop (GREEN -- test infrastructure for code
that already exists).
"""

from __future__ import annotations

import importlib.util

collect_ignore: list[str] = []

if importlib.util.find_spec("film_study_tool") is None:
    collect_ignore.append("staging/overview-ui/test_productions.py")
