# what-it-is:   the guard on the fresh-install failure path
# what-it-does: runs the contract CLI and a skill's scripted lane on a simulated machine where
#               jsonschema is absent, and asserts each reports the remedy instead of a traceback
# why:          /plugin install does not install Python packages, so this is the first thing a new
#               user hits; a raw ModuleNotFoundError there is a broken product, not a rough edge
# used-by:      python -m pytest (the CI unit-python job)
"""Tests the missing-dependency path for `jsonschema`.

Claude Code's ``/plugin install`` clones a repository; it does not run
``pip``. Before this guard, every skill's ``scripts/checks.py`` reached
``contract/validate.py``'s module-level ``import jsonschema`` through
``skills/_shared/runner.py`` and ``gate.py``, so on any machine without the
package a freshly installed plugin answered step 2 of every skill's protocol
with a bare ``ModuleNotFoundError`` traceback and no indication of the fix.

Absence is simulated by putting a directory containing a ``jsonschema``
package that raises ``ImportError`` at the front of ``PYTHONPATH``, which
shadows any real installation. Each case runs in a subprocess because the
import is cached process-wide once it succeeds, so an in-process test would
prove nothing after the first import.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "skills/critique-clarity/examples/clarity-golden-04-clean.md"

EXPECTED_REMEDY = 'pip install "jsonschema>=4.20,<5"'


@pytest.fixture(scope="module")
def without_jsonschema(tmp_path_factory: pytest.TempPathFactory) -> str:
    """A PYTHONPATH entry that shadows any installed jsonschema with a failing one."""
    shadow = tmp_path_factory.mktemp("no-jsonschema")
    package = shadow / "jsonschema"
    package.mkdir()
    (package / "__init__.py").write_text(
        'raise ImportError("No module named \'jsonschema\'")\n', encoding="utf-8"
    )
    return str(shadow)


def _run(args: list[str], pythonpath: str) -> subprocess.CompletedProcess[str]:
    env = {
        **{k: v for k, v in __import__("os").environ.items() if k != "PYTHONPATH"},
        "PYTHONPATH": pythonpath,
    }
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _assert_actionable(proc: subprocess.CompletedProcess[str]) -> None:
    combined = proc.stdout + proc.stderr
    assert EXPECTED_REMEDY in combined, f"the remedy must be named; got:\n{combined}"
    assert "Traceback (most recent call last)" not in combined, (
        f"a traceback is not an actionable error; got:\n{combined}"
    )
    assert "ModuleNotFoundError" not in combined and "ImportError" not in combined, (
        f"the raw import error must not reach the user; got:\n{combined}"
    )


@pytest.mark.parametrize("gate", [False, True], ids=["no-gate", "gate"])
def test_skill_scripted_lane_reports_the_remedy(without_jsonschema: str, gate: bool) -> None:
    """Step 2 of every skill's protocol is the first command a new user runs."""
    args = ["skills/critique-clarity/scripts/checks.py", str(ARTIFACT)]
    if gate:
        args.append("--gate")
    proc = _run(args, without_jsonschema)
    _assert_actionable(proc)
    # Same convention every other environment error here uses: 4 under --gate, 1 otherwise.
    assert proc.returncode == (4 if gate else 1)


@pytest.mark.parametrize("gate", [False, True], ids=["no-gate", "gate"])
def test_contract_cli_reports_the_remedy(without_jsonschema: str, gate: bool) -> None:
    """`python -m contract.validate` is the command agents/critique-critic.md documents."""
    envelope = next(REPO_ROOT.glob("bench/results/runs-cal1/**/haiku-r1.json"), None)
    assert envelope is not None, "expected a committed envelope to validate against"
    args = ["-m", "contract.validate", str(envelope)]
    if gate:
        args.append("--gate")
    proc = _run(args, without_jsonschema)
    _assert_actionable(proc)
    assert proc.returncode == (4 if gate else 1)


def test_importing_the_skill_chain_no_longer_fails_at_import_time(without_jsonschema: str) -> None:
    """The chain must load cleanly; the error belongs at the point of use, not at import.

    This is the property that lets the error be caught and reported at all. If the
    import were still eager, there would be no frame in which to catch it.
    """
    proc = _run(
        ["-c", "import sys; sys.path.insert(0, '.'); import skills._shared.runner; print('ok')"],
        without_jsonschema,
    )
    assert proc.returncode == 0, f"import chain must not fail without jsonschema:\n{proc.stderr}"
    assert "ok" in proc.stdout
