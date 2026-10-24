# what-it-is:   the --gate exit codes, exercised on every shipped skill's committed envelopes
# what-it-does: gates the expected_envelope inside each skill's golden files, gates a severity-4
#               variant of one envelope per skill, and runs the consumer recipe's command shape
# why:          test_gate.py proves the exit codes on synthetic envelopes only; a consumer gates
#               on real skill output, and E53 asks for the codes to hold on every shipped skill
# used-by:      python -m pytest (the CI unit-python job)
"""E53: `python -m contract.validate <file> --gate` exit codes on every shipped skill.

`test_gate.py` covers exit codes 0 to 4 on envelopes built by `fixtures.py`. This module runs the
same gate on what each skill actually committed: the `expected_envelope` of every golden file under
`<skill>/examples/`, for every skill `library.json` registers. No model is called. "Exercised" here
means the gate runs on each skill's committed envelopes, not on a live run.

A golden file is not itself an envelope. Its top-level keys are `kind`, `artifact`,
`expected_envelope` and `note`, so the gate rejects the file as a whole with exit 3. Each test below
therefore writes the `expected_envelope` object to its own file first, which is also what a consumer
copying a golden file as a sample would have to do.

No committed golden reaches exit 1, because none carries a severity-4 finding. For each skill, the
exit 1 path is reached with a variant built here from one of that skill's envelopes: one finding
raised to severity 4, and the histogram and gate verdict updated to match. The variant is never
written into the repository, because `examples/recipes/gate-in-ci.md` states that no severity-4
fixture exists in it.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from contract.validate import main, validate_document

REPO_ROOT = Path(__file__).resolve().parents[2]


def _registered_skills() -> list[dict[str, Any]]:
    library = json.loads((REPO_ROOT / "library.json").read_text(encoding="utf-8"))
    return list(library["components"]["skills"])


def _goldens(skill: dict[str, Any]) -> list[Path]:
    examples = REPO_ROOT / skill["path"] / "examples"
    paths = sorted(examples.glob("golden-*.json"))
    return [p for p in paths if json.loads(p.read_text(encoding="utf-8")).get("kind") == "golden"]


def _expected_envelope(golden: Path) -> dict[str, Any]:
    return json.loads(golden.read_text(encoding="utf-8"))["expected_envelope"]


def _implied_exit_code(summary: dict[str, Any]) -> int:
    """The exit code the gate must return for this summary, written out from the documented
    table in docs/how-to/gate-in-ci.md rather than by calling gate_exit_code(), so the
    assertion does not use the function under test as its own oracle."""
    by_severity = summary["by_severity"]
    if by_severity["4"] > 0:
        return 1
    if by_severity["3"] > summary["severity_3_threshold"]:
        return 2
    return 0


def _severity_4_variant(envelope: dict[str, Any]) -> dict[str, Any]:
    """Raise the first finding to severity 4 and update the histogram and the gate verdict to
    match. Every other field stays as the skill committed it, so the variant carries the same
    criteria, lanes and rubrics as a real run of that skill."""
    variant = copy.deepcopy(envelope)
    finding = variant["findings"][0]
    by_severity = variant["summary"]["by_severity"]
    by_severity[str(finding["severity"])] -= 1
    by_severity["4"] += 1
    finding["severity"] = 4
    variant["summary"]["gate"] = "fail"
    return variant


def _first_envelope_with_findings(skill: dict[str, Any]) -> dict[str, Any]:
    for golden in _goldens(skill):
        envelope = _expected_envelope(golden)
        if envelope["findings"]:
            return envelope
    raise AssertionError(f"{skill['name']} has no golden envelope with a finding to raise to severity 4")


def _first_clean_envelope(skill: dict[str, Any]) -> dict[str, Any]:
    for golden in _goldens(skill):
        envelope = _expected_envelope(golden)
        if _implied_exit_code(envelope["summary"]) == 0:
            return envelope
    raise AssertionError(f"{skill['name']} has no golden envelope that passes the gate")


def _write(tmp_path: Path, name: str, doc: dict[str, Any]) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return str(path)


SKILLS = _registered_skills()
GOLDENS = [(skill, golden) for skill in SKILLS for golden in _goldens(skill)]


def test_every_registered_skill_has_golden_envelopes() -> None:
    """A wrong path or a renamed examples directory must not make the tests below pass by
    collecting nothing."""
    assert SKILLS, "library.json registered no skills"
    missing = [skill["name"] for skill in SKILLS if not _goldens(skill)]
    assert not missing, f"registered skills with no golden-*.json under examples/: {missing}"


def test_every_registered_skill_reaches_exit_0_and_exit_2_from_its_goldens() -> None:
    """Each skill's committed envelopes cover both the passing gate and the severity-3 failure.
    Exit 1 is reached by the variant test below, because no golden carries severity 4."""
    gaps = []
    for skill in SKILLS:
        codes = {_implied_exit_code(_expected_envelope(g)["summary"]) for g in _goldens(skill)}
        if not {0, 2} <= codes:
            gaps.append(f"{skill['name']}: goldens reach exit codes {sorted(codes)}")
    assert not gaps, "skills whose goldens do not reach both exit 0 and exit 2:\n" + "\n".join(gaps)


@pytest.mark.parametrize(
    ("skill", "golden"),
    GOLDENS,
    ids=[f"{skill['name']}/{golden.stem}" for skill, golden in GOLDENS],
)
def test_gate_on_golden_expected_envelope(skill: dict[str, Any], golden: Path, tmp_path: Path) -> None:
    envelope = _expected_envelope(golden)
    expected = _implied_exit_code(envelope["summary"])
    assert (expected == 0) == (envelope["summary"]["gate"] == "pass"), (
        f"{golden.name}: summary.gate disagrees with the exit code its own counts imply"
    )

    assert main([_write(tmp_path, "envelope.json", envelope), "--gate"]) == expected
    # The wrapper is not an envelope: gating the golden file itself is a contract error.
    assert main([str(golden), "--gate"]) == 3


@pytest.mark.parametrize("skill", SKILLS, ids=[skill["name"] for skill in SKILLS])
def test_severity_4_variant_exits_1(skill: dict[str, Any], tmp_path: Path) -> None:
    variant = _severity_4_variant(_first_envelope_with_findings(skill))
    result = validate_document(variant)
    assert result.ok, f"the severity-4 variant is not contract-valid: {[str(e) for e in result.errors]}"

    path = _write(tmp_path, "severity-4.json", variant)
    assert main([path, "--gate"]) == 1
    # No threshold excuses a severity-4 finding.
    assert main([path, "--gate", "--threshold", "99"]) == 1


@pytest.mark.parametrize("skill", SKILLS, ids=[skill["name"] for skill in SKILLS])
def test_consumer_recipe_command_from_outside_the_checkout(skill: dict[str, Any], tmp_path: Path) -> None:
    """The command docs/how-to/gate-in-ci.md gives a consumer, run the way its workflow runs it:
    from a working directory outside this checkout, with PYTHONPATH pointing at the checkout."""
    clean = _write(tmp_path, "clean.json", _first_clean_envelope(skill))
    severity_4 = _write(
        tmp_path, "severity-4.json", _severity_4_variant(_first_envelope_with_findings(skill))
    )
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}

    def gate(path: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "contract.validate", path, "--gate", "--threshold", "0"],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    passed = gate(clean)
    failed = gate(severity_4)

    assert passed.returncode == 0, passed.stderr
    assert failed.returncode == 1, failed.stderr
    assert "valid" in failed.stdout
