"""Tests for skills/_shared/stdio.py: JSON on stdout survives a non-UTF-8 console (E84).

``PYTHONIOENCODING=cp1252`` makes a child Python encode stdout as cp1252 on any platform, so these
tests reproduce the Windows failure on the Linux CI runners that never saw it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED = REPO_ROOT / "skills" / "_shared"


def _cp1252_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("PYTHONUTF8", None)
    env["PYTHONIOENCODING"] = "cp1252"
    return env


def test_write_json_survives_a_cp1252_stdout() -> None:
    code = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "from skills._shared.stdio import write_json;"
        "write_json({'evidence': 'a \\u2192 b, \\u2019quoted\\u2019, \\u00e9'})"
    )
    proc = subprocess.run([sys.executable, "-c", code, str(REPO_ROOT)], capture_output=True,
                          env=_cp1252_env())
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert json.loads(proc.stdout.decode("utf-8")) == {"evidence": "a → b, ’quoted’, é"}


def test_a_scripted_lane_quoting_an_arrow_prints_an_envelope_on_a_cp1252_stdout(tmp_path: Path) -> None:
    """End to end: the shape of the 2026-11-16 crash, critique-clarity on a sentence with an arrow."""
    words = " ".join(f"word{i}" for i in range(70))
    artifact = tmp_path / "note.md"
    artifact.write_text(f"# Note\n\nThe flow goes upload → review → publish and then {words}.\n",
                        encoding="utf-8", newline="\n")
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "skills/critique-clarity/scripts/checks.py"),
         "--repo-root", str(tmp_path), str(artifact)],
        cwd=REPO_ROOT, capture_output=True, env=_cp1252_env(),
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    envelope = json.loads(proc.stdout.decode("utf-8"))
    assert any("→" in f["evidence"] for f in envelope["findings"]), "the test needs a finding that quotes the arrow"


def test_no_shared_cli_prints_json_except_through_write_json() -> None:
    """A new print of non-ASCII JSON would bring the crash back; route it through write_json."""
    offenders = []
    for path in sorted(SHARED.glob("*.py")):
        if path.name == "stdio.py":
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"print\(json\.dumps|json\.dump\([^)]*sys\.stdout", text):
            offenders.append(path.name)
    assert not offenders, offenders
