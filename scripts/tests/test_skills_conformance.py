# what-it-is:   the CI wiring that runs scripts/skill-selftest.py against every real skill
# what-it-does: globs skills/critique-*/ (excluding the skills/_shared and
#               skills/_template-fixture support directories) and asserts the self-test CLI
#               exits 0 against each, as a parametrized test per skill
# why:          S-04 spec AC-3 requires the template-conformance script to validate all six
#               skills "uniformly in CI." Before this module, skill-selftest.py was only ever
#               run against the synthetic skills/_template-fixture/critique-toy fixture (in
#               scripts/tests/test_skill_selftest.py) or by hand (the one-time manual sweep
#               recorded in docs/internal/execution/P2-report.md's S05-AC1 row) -- never
#               automatically, against the real skills, in CI.
# used-by:      python -m pytest (the CI unit-python job; pytest.ini's testpaths already globs
#               scripts/tests, so this module is collected with no workflow edit)
"""Runs `scripts/skill-selftest.py` as a subprocess against every real
`skills/critique-<domain>/` directory.

This exercises the self-test's actual CLI contract (`python
scripts/skill-selftest.py <skill-dir>`, exit 0 on pass, per the script's
own module docstring) rather than the in-process `run_selftest()` /
`check_*()` helpers `scripts/tests/test_skill_selftest.py` already
exercises against its synthetic `critique-toy` fixture. That file proves
the checker is correct; this file proves the checker actually runs
against the skills it is meant to police.

Closes S-04 skill-template spec AC-3 ("a template-conformance script
validates all six skills uniformly in CI",
docs/internal/release-plans/plan_v0.1.0/S-04_skill-template/spec.md):
this module lands in the existing `unit-python` CI job's `python -m
pytest` collection automatically, so no new CI job or workflow edit is
needed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_DIR = _REPO_ROOT / "skills"
_SELFTEST = _REPO_ROOT / "scripts" / "skill-selftest.py"

# skills/_shared and skills/_template-fixture are support directories, not shipped skills. The
# "critique-*" glob below already excludes both by prefix (neither name starts with
# "critique-", and critique-toy itself sits one level deeper, under
# skills/_template-fixture/critique-toy/). Named here anyway so the exclusion is a documented
# decision rather than an accident of naming.
_EXCLUDED_NAMES = {"_shared", "_template-fixture"}

_SKILL_DIRS = sorted(
    path
    for path in _SKILLS_DIR.glob("critique-*")
    if path.is_dir() and path.name not in _EXCLUDED_NAMES
)


def test_at_least_one_skill_directory_found():
    """A guard against this module silently collecting zero parametrized
    cases (e.g. if the skills/ layout changes), which would make AC-3
    look satisfied by a suite that checks nothing.
    """
    assert _SKILL_DIRS, f"no skills/critique-*/ directories found under {_SKILLS_DIR}"


@pytest.mark.parametrize("skill_dir", _SKILL_DIRS, ids=[path.name for path in _SKILL_DIRS])
def test_skill_passes_selftest(skill_dir: Path):
    result = subprocess.run(
        [sys.executable, str(_SELFTEST), str(skill_dir)],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"scripts/skill-selftest.py {skill_dir} exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
