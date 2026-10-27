# what-it-is:   the lane-routing contract tests for E73 (merge runs the scripted lane itself)
# what-it-does: for every skill library.json registers, runs the skill's own checks.py through
#               merge.assemble (and, once per skill, through its scripts/merge.py shim) and checks
#               the merged envelope against D1-D3 and AC-1 through AC-7, with no model call
# why:          E73 (docs/internal/release-plans/_unassigned/E73_merge-runs-scripted-lane/spec.md)
#               moved the scripted lane's authority from the model's own copy to checks.py itself,
#               and a model finding's lane from the model's own claim to SKILL.md's declaration;
#               these are the tests that would have caught the defect the spec reproduces
# used-by:      python -m pytest (the CI unit-python job)
"""Tests for the lane-routing rules `skills/_shared/merge.py` implements under E73.

Parametrized over every skill `library.json` registers, the way `contract/tests/
test_gate_shipped_skills.py` parametrizes its own gate tests, so a skill registered later is covered
without an edit here. Each case runs the skill's own committed golden artifact through
`merge.assemble` (or, for the shim coverage below, through the skill's own `scripts/merge.py`) with a
hand-built findings file; no model is called anywhere in this file.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from skills._shared import merge
from skills._shared.artifact import Artifact
from skills._shared.findings import RawFinding, to_finding_dict

REPO_ROOT = Path(__file__).resolve().parents[3]


def _registered_skills() -> list[dict[str, Any]]:
    library = json.loads((REPO_ROOT / "library.json").read_text(encoding="utf-8"))
    return list(library["components"]["skills"])


def _goldens(skill: dict[str, Any]) -> list[dict[str, Any]]:
    examples = REPO_ROOT / skill["path"] / "examples"
    docs = (json.loads(p.read_text(encoding="utf-8")) for p in sorted(examples.glob("golden-*.json")))
    return [doc for doc in docs if doc.get("kind") == "golden"]


def _first_golden(skill: dict[str, Any]) -> dict[str, Any]:
    """The first committed golden file for `skill`, the same selection
    `contract/tests/test_gate_shipped_skills.py` makes."""
    goldens = _goldens(skill)
    if not goldens:
        raise AssertionError(f"{skill['name']} has no golden-*.json under examples/")
    return goldens[0]


def _artifact_path(skill: dict[str, Any], golden: dict[str, Any] | None = None) -> Path:
    return REPO_ROOT / (golden or _first_golden(skill))["artifact"]


def _lane_ids(skill: dict[str, Any]) -> tuple[frozenset[str], frozenset[str]]:
    skill_md = (REPO_ROOT / skill["path"] / "SKILL.md").read_text(encoding="utf-8")
    return merge.read_lane_manifest(skill_md)


def _load_artifact(path: Path) -> Artifact:
    """Build the same kind of Artifact object merge.assemble hands to checks.py's check(), for
    tests that need to compare against the scripted lane's own raw output directly."""
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    return Artifact(path=path.name, text=text, sha256=hashlib.sha256(raw).hexdigest(), disk_path=path.resolve())


def _script_raw(skill: dict[str, Any], artifact: Path | None = None) -> list[RawFinding]:
    return merge.run_script_checks(
        skill["name"], _load_artifact(artifact or _artifact_path(skill)), repo_root=REPO_ROOT
    )


def _script_finding_dicts(skill: dict[str, Any], artifact: Path) -> list[dict[str, Any]]:
    """checks.py's own live findings for `artifact`, as plain dicts: a model's faithful copy of
    the real scripted lane, which is what "old pass 4" actually handed merge.

    A committed golden-*.json's own `findings` is an illustrative example envelope and mixes judged
    criteria in with scripted ones (SKILL.md's protocol, pass 1-3 is judgment, not just checks.py's
    output), so it is not a stand-in for "the script's findings" the way this test needs.
    """
    return [
        to_finding_dict(raw, finding_id=f"F-{i:03d}") for i, raw in enumerate(_script_raw(skill, artifact), start=1)
    ]


def _golden_with_script_findings(skill: dict[str, Any]) -> tuple[dict[str, Any], Path] | tuple[None, None]:
    """The first golden artifact for `skill` whose live scripted lane is non-empty, for the two
    tests below that need a real script finding to drop. Not every skill's first golden artifact
    triggers one (critique-argument's golden-01 is a pure judged-criteria case)."""
    for golden in _goldens(skill):
        artifact = REPO_ROOT / golden["artifact"]
        if _script_raw(skill, artifact):
            return golden, artifact
    return None, None


def _finding(criterion: str, severity: int, *, location: str = "test location", **over: object) -> dict:
    finding = {
        "criterion": criterion,
        "severity": severity,
        "location": location,
        "evidence": f"quoted text for {criterion}",
        "violation": f"{criterion} was breached.",
        "fix": "Rewrite it.",
    }
    finding.update(over)
    return finding


SKILLS = _registered_skills()
IDS = [skill["name"] for skill in SKILLS]


# ----------------------------------------------------------------------------------------------
# AC-1: every finding check() returns is listed or counted as suppressed, whatever findings holds.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_every_script_finding_is_listed_or_suppressed(skill: dict[str, Any]) -> None:
    """The shared test from the spec's Tests table: the scripted lane in the merged envelope
    cannot be compared byte for byte with checks.py's own envelope, because bounding runs over the
    combined pool. So every severity 3 or 4 script finding must survive (nothing outranks it), and
    every suppressed below-3 script finding must be covered by summary.suppressed_count. The
    findings file here is empty: this is AC-1 at its strongest, since nothing the model wrote can
    be relied on to carry a script finding forward any more.
    """
    script_raw = _script_raw(skill)
    envelope = merge.assemble(
        skill=skill["name"], artifact=_artifact_path(skill), findings=[], repo_root=REPO_ROOT
    )
    kept_pairs = {(f["criterion"], f["location"]) for f in envelope["findings"]}

    high = [raw for raw in script_raw if raw.severity >= 3]
    missing_high = [raw for raw in high if (raw.criterion, raw.location) not in kept_pairs]
    assert not missing_high, f"{skill['name']}: severity>=3 script finding(s) dropped: {missing_high}"

    below = [raw for raw in script_raw if raw.severity < 3]
    missing_below = [raw for raw in below if (raw.criterion, raw.location) not in kept_pairs]
    assert len(missing_below) <= envelope["summary"]["suppressed_count"], (
        f"{skill['name']}: {len(missing_below)} below-severity-3 script finding(s) missing from "
        f"findings[], but summary.suppressed_count is only {envelope['summary']['suppressed_count']}"
    )


# ----------------------------------------------------------------------------------------------
# D1 / AC-3: a model finding on a scripted criterion the script did not emit is dropped, counted.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_a_model_copy_of_a_scripted_criterion_is_dropped(skill: dict[str, Any]) -> None:
    scripted_ids, _judged_ids = _lane_ids(skill)
    script_raw = _script_raw(skill)
    cited = {raw.criterion for raw in script_raw}
    candidates = sorted(c for c in scripted_ids if c not in cited)
    if not candidates:
        pytest.skip(f"{skill['name']}: this artifact's real scripted lane cites every scripted criterion")
    target = candidates[0]

    findings = [_finding(target, 2, lane="scripted", confidence="medium")]
    diagnostics: dict[str, Any] = {}
    envelope = merge.assemble(
        skill=skill["name"],
        artifact=_artifact_path(skill),
        findings=findings,
        repo_root=REPO_ROOT,
        diagnostics=diagnostics,
    )

    assert diagnostics["dropped_scripted_criteria"] == {target: 1}
    assert all(f["criterion"] != target for f in envelope["findings"])


# ----------------------------------------------------------------------------------------------
# D2 / AC-4: an undeclared criterion fails the merge, naming it; a BYOR one is filed as judged.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_an_undeclared_criterion_fails_the_merge_by_name(skill: dict[str, Any]) -> None:
    bad_id = "ZZZUNDECLARED-TESTID"
    findings = [_finding(bad_id, 2)]

    with pytest.raises(merge.MergeError, match=bad_id):
        merge.assemble(skill=skill["name"], artifact=_artifact_path(skill), findings=findings, repo_root=REPO_ROOT)


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_a_byor_marked_finding_is_filed_as_judged_whatever_its_namespace(skill: dict[str, Any]) -> None:
    findings = [_finding("BYOR-TEST-CRITERION", 3, rubric_source="byor")]

    envelope = merge.assemble(
        skill=skill["name"], artifact=_artifact_path(skill), findings=findings, repo_root=REPO_ROOT
    )

    matches = [f for f in envelope["findings"] if f["criterion"] == "BYOR-TEST-CRITERION"]
    assert len(matches) == 1
    assert matches[0]["lane"] == "judged"


# ----------------------------------------------------------------------------------------------
# AC-2 / "Mislabeled judgment" and "No lane" rows of the spec's Tests table.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_a_judged_criterion_mislabeled_scripted_is_refiled_as_judged(skill: dict[str, Any]) -> None:
    """The exact reproduction in the spec: FORMS-ACTION-HIERARCHY labeled "scripted" at confidence
    "medium" comes back as judged, confidence medium - not forced to high."""
    _scripted_ids, judged_ids = _lane_ids(skill)
    target = sorted(judged_ids)[0]
    findings = [_finding(target, 3, location="mislabeled-judgment case", lane="scripted", confidence="medium")]

    envelope = merge.assemble(
        skill=skill["name"], artifact=_artifact_path(skill), findings=findings, repo_root=REPO_ROOT
    )

    matches = [f for f in envelope["findings"] if f["criterion"] == target and f["location"] == findings[0]["location"]]
    assert len(matches) == 1, f"{skill['name']}: expected exactly one finding at the test location"
    assert matches[0]["lane"] == "judged"
    assert matches[0]["confidence"] == "medium"


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_a_judged_criterion_with_no_lane_is_filed_as_judged(skill: dict[str, Any]) -> None:
    _scripted_ids, judged_ids = _lane_ids(skill)
    target = sorted(judged_ids)[0]
    findings = [_finding(target, 3, location="no-lane case", confidence="low")]
    assert "lane" not in findings[0]

    envelope = merge.assemble(
        skill=skill["name"], artifact=_artifact_path(skill), findings=findings, repo_root=REPO_ROOT
    )

    matches = [f for f in envelope["findings"] if f["criterion"] == target and f["location"] == findings[0]["location"]]
    assert len(matches) == 1
    assert matches[0]["lane"] == "judged"
    assert matches[0]["confidence"] == "low"


# ----------------------------------------------------------------------------------------------
# D3 / AC-5: a judged finding with no confidence defaults to medium, not high.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_a_judged_finding_with_no_confidence_defaults_to_medium(skill: dict[str, Any]) -> None:
    _scripted_ids, judged_ids = _lane_ids(skill)
    target = sorted(judged_ids)[0]
    findings = [_finding(target, 3, location="no-confidence case")]
    assert "confidence" not in findings[0]

    envelope = merge.assemble(
        skill=skill["name"], artifact=_artifact_path(skill), findings=findings, repo_root=REPO_ROOT
    )

    matches = [f for f in envelope["findings"] if f["criterion"] == target and f["location"] == findings[0]["location"]]
    assert len(matches) == 1
    assert matches[0]["confidence"] == "medium"


# ----------------------------------------------------------------------------------------------
# Requirement 8 / "Old pass 4" row: a findings file still carrying the script's own findings
# gives the same envelope as one carrying the judged findings alone.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_old_pass_4_findings_give_the_same_envelope_as_judged_only(skill: dict[str, Any]) -> None:
    _scripted_ids, judged_ids = _lane_ids(skill)
    golden, artifact = _golden_with_script_findings(skill)
    if golden is None:
        pytest.skip(f"{skill['name']}: no committed golden artifact's live scripted lane is non-empty")
    script_copies = _script_finding_dicts(skill, artifact)
    assert script_copies

    judged_finding = _finding(sorted(judged_ids)[0], 3, location="old-pass-4 comparison case")
    timestamp = "2026-10-26T00:00:00Z"

    old_pass_4 = merge.assemble(
        skill=skill["name"],
        artifact=artifact,
        findings=[*script_copies, judged_finding],
        repo_root=REPO_ROOT,
        timestamp=timestamp,
    )
    judged_only = merge.assemble(
        skill=skill["name"],
        artifact=artifact,
        findings=[judged_finding],
        repo_root=REPO_ROOT,
        timestamp=timestamp,
    )

    assert old_pass_4 == judged_only


# ----------------------------------------------------------------------------------------------
# AC-7: the skill's own scripts/merge.py shim, not just the shared module, shows the behavior.
# ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_the_skill_shim_drops_a_scripted_copy_and_refiles_a_mislabeled_judgment(
    skill: dict[str, Any], tmp_path: Path
) -> None:
    """AC-7, run through the actual entry point every SKILL.md documents
    (`skills/<skill>/scripts/merge.py`), not only the shared module.

    A model's findings file that OMITS a script finding no longer matters either way: this module
    runs checks.py itself (requirement 1), so every real scripted finding reaches the envelope (or
    is counted suppressed) regardless of what the findings file says. What this test shows is the
    other half of AC-7: a judged-criterion finding mislabeled "scripted" is refiled as judged, at
    its stated confidence, by the actual per-skill entry point every SKILL.md documents.
    """
    _scripted_ids, judged_ids = _lane_ids(skill)

    mislabeled = _finding(
        sorted(judged_ids)[0], 3, location="shim mislabeled-judgment case", lane="scripted", confidence="medium"
    )
    findings_file = tmp_path / "findings.json"
    findings_file.write_text(json.dumps({"findings": [mislabeled]}), encoding="utf-8")

    shim = REPO_ROOT / skill["path"] / "scripts" / "merge.py"
    proc = subprocess.run(
        [sys.executable, str(shim), "--artifact", str(_artifact_path(skill)), "--findings", str(findings_file)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    envelope = json.loads(proc.stdout)

    matches = [
        f
        for f in envelope["findings"]
        if f["criterion"] == mislabeled["criterion"] and f["location"] == mislabeled["location"]
    ]
    assert len(matches) == 1
    assert matches[0]["lane"] == "judged"
    assert matches[0]["confidence"] == "medium"


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_the_skill_shim_restores_a_script_finding_the_findings_file_omits(
    skill: dict[str, Any], tmp_path: Path
) -> None:
    """AC-7's other half, through the same real entry point: a findings file missing one of
    checks.py's own findings still produces an envelope carrying it, or counting it suppressed,
    because the scripted lane no longer comes from that file at all."""
    golden, artifact = _golden_with_script_findings(skill)
    if golden is None:
        pytest.skip(f"{skill['name']}: no committed golden artifact's live scripted lane is non-empty")
    script_copies = _script_finding_dicts(skill, artifact)
    removed = script_copies.pop(0)

    findings_file = tmp_path / "findings.json"
    findings_file.write_text(json.dumps({"findings": script_copies}), encoding="utf-8")

    shim = REPO_ROOT / skill["path"] / "scripts" / "merge.py"
    proc = subprocess.run(
        [sys.executable, str(shim), "--artifact", str(artifact), "--findings", str(findings_file)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    envelope = json.loads(proc.stdout)

    pairs = {(f["criterion"], f["location"]) for f in envelope["findings"]}
    removed_pair = (removed["criterion"], removed["location"])
    was_kept = removed_pair in pairs
    was_suppressed = envelope["summary"]["suppressed_count"] > 0
    assert was_kept or was_suppressed, f"{skill['name']}: omitted script finding {removed_pair} vanished uncounted"
