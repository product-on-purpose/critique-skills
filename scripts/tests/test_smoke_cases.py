# what-it-is:   a coverage guard for scripts/smoke.py's CASES table
# what-it-does: asserts the table names exactly the skills on disk, each with an artifact that exists
# why:          `/plugin install` delivers every skills/critique-*/ directory, whatever library.json
#               says about its status, so a skill missing from CASES ships untested for the
#               fresh-install defect the CI `smoke` job exists for. critique-forms was missing from
#               the hand-kept table until 2026-09-30, and the job still passed.
# used-by:      python -m pytest (the CI unit-python job)
"""Tests that the install smoke check exercises every skill a user installs."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _smoke():
    spec = importlib.util.spec_from_file_location("smoke_under_test", REPO_ROOT / "scripts" / "smoke.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_smoke_cases_cover_every_installed_skill() -> None:
    on_disk = {p.parent.name for p in REPO_ROOT.glob("skills/critique-*/SKILL.md")}
    assert {skill for skill, _artifact in _smoke().CASES} == on_disk


def test_every_smoke_artifact_exists() -> None:
    for skill, artifact in _smoke().CASES:
        assert (REPO_ROOT / artifact).is_file(), f"{skill}: no such artifact {artifact}"
