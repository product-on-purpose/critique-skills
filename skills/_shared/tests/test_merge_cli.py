"""Tests for skills/_shared/merge.py, the envelope-assembly CLI the critic calls.

Why this exists at all. skills/_shared/envelope.py has carried the deterministic assembly logic
since the beginning, and assemble_envelope's own docstring names its intended callers as
"skills/_shared/runner.py, or a judged-lane critic merging both lanes". The scripted lane could
reach it, because runner.py is a CLI. The critic could not: it is prose plus Bash, and the function
is Python. So the critic did the ranking, bounding, histogram and gate arithmetic in its head.

Measured 2026-08-09 on the pinned haiku tier: 2 of 7 cells produced a contract-valid envelope. Both
recurring failures were the critic mis-stating its own measurement, a histogram that did not total
len(findings) plus suppressed_count, and a scripted finding claiming less than high confidence. This
module turns both from arithmetic the model must get right into a subprocess it already has the
tools to run.

E73 (2026-10-26) changed what `findings` means in these tests. `merge.assemble` now runs
critique-clarity's own `scripts/checks.py` on `artifact` itself, so the scripted lane in every
envelope below comes from that run, not from anything in `findings`. `findings` is now the judged
lane only, and a finding's criterion, not its own `lane` field, decides where it lands: a criterion
in critique-clarity's `checks.scripted` (SKILL.md) is dropped (D1), one in `checks.judged` is kept as
judged regardless of what `lane` it claims (D2/D3). `skills/_shared/tests/test_merge_lanes.py` covers
that routing across every registered skill; the tests here are the CLI plumbing (stdin, a findings
file, a bare list, an empty input, an invalid envelope) plus the handful of assemble() behaviours
(histogram, sha256, prose, rubrics) that do not depend on the routing itself.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from contract.validate import validate_document
from skills._shared import merge

REPO_ROOT = Path(__file__).resolve().parents[3]


def _finding(criterion: str, severity: int, *, lane: str = "judged", **over: object) -> dict:
    finding = {
        "criterion": criterion,
        "severity": severity,
        "location": f"section {severity}",
        "evidence": f"quoted text for {criterion}",
        "violation": f"{criterion} was breached.",
        "fix": "Rewrite it.",
        "lane": lane,
        "confidence": "high",
    }
    finding.update(over)
    return finding


@pytest.fixture()
def artifact(tmp_path: Path) -> Path:
    p = tmp_path / "sample.md"
    p.write_bytes(b"# Heading\n\nSome body text.\n")
    return p


def test_histogram_counts_every_finding_including_the_suppressed_ones(artifact: Path) -> None:
    """The exact failure measured twice on haiku: "histogram total 9 does not equal len(findings)
    (9) plus suppressed_count (2)". The histogram is over everything found; `findings` is the
    bounded subset. Getting that wrong is the single most common way a cell was lost.

    PLAIN-AUDIENCE is a declared judged criterion (skills/critique-clarity/SKILL.md), so each of
    these 8 findings is kept, at a distinct location so the contract's uniqueItems rule on
    findings[] is satisfied once bounding narrows the set to 5.
    """
    # 8 low-severity findings, so bounding keeps 5 and suppresses 3.
    findings = [_finding("PLAIN-AUDIENCE", 1, location=f"paragraph {i}") for i in range(8)]

    envelope = merge.assemble(
        skill="critique-clarity", artifact=artifact, findings=findings, repo_root=REPO_ROOT
    )

    total = sum(envelope["summary"]["by_severity"].values())
    assert total == len(envelope["findings"]) + envelope["summary"]["suppressed_count"]
    assert total == 8
    assert envelope["summary"]["suppressed_count"] == 3


def test_a_model_finding_on_a_scripted_criterion_is_dropped(artifact: Path) -> None:
    """D1 option A. PLAIN-ACTIVE is a declared scripted criterion, so the model's copy of it -
    whatever confidence or lane it claims - is dropped rather than merged in: the scripted lane is
    critique-clarity's own checks.py, run on `artifact`, and only that. The trivial fixture artifact
    trips no real PLAIN-ACTIVE check, so a clean envelope here is itself the assertion that the copy
    was dropped, not kept at a corrected confidence.
    """
    findings = [_finding("PLAIN-ACTIVE", 2, lane="scripted", confidence="medium")]
    diagnostics: dict = {}

    envelope = merge.assemble(
        skill="critique-clarity",
        artifact=artifact,
        findings=findings,
        repo_root=REPO_ROOT,
        diagnostics=diagnostics,
    )

    assert envelope["findings"] == []
    assert diagnostics["dropped_scripted_criteria"] == {"PLAIN-ACTIVE": 1}
    assert diagnostics["dropped_count"] == 1


def test_a_judged_findings_confidence_is_left_alone(artifact: Path) -> None:
    """A judged finding's confidence is a real signal from the critic and must survive."""
    findings = [_finding("PLAIN-AUDIENCE", 2, lane="judged", confidence="low")]

    envelope = merge.assemble(
        skill="critique-clarity", artifact=artifact, findings=findings, repo_root=REPO_ROOT
    )

    assert envelope["findings"][0]["confidence"] == "low"


def test_the_assembled_envelope_is_contract_valid(artifact: Path) -> None:
    """PLAIN-ACTIVE is scripted, so the model's copy of it is dropped (D1); WILLIAMS-CHARACTER-ACTION
    is declared judged, so it is kept. The envelope is valid either way."""
    findings = [
        _finding("PLAIN-ACTIVE", 3, lane="scripted"),
        _finding("WILLIAMS-CHARACTER-ACTION", 2, lane="judged"),
    ]

    envelope = merge.assemble(
        skill="critique-clarity", artifact=artifact, findings=findings, repo_root=REPO_ROOT
    )

    result = validate_document(envelope)
    assert result.ok, result.errors


def test_rubrics_are_derived_from_the_criteria_actually_cited(artifact: Path) -> None:
    """run.rubrics must cover every namespace the findings draw on, or the validator's
    rubrics-cover-findings rule fails. Deriving it removes one more thing to get wrong.

    Both PLAIN-AUDIENCE and WILLIAMS-CHARACTER-ACTION are declared judged criteria, so both are
    kept (unlike a scripted criterion's copy, which D1 drops before it could cite a namespace)."""
    findings = [
        _finding("PLAIN-AUDIENCE", 2, lane="judged"),
        _finding("WILLIAMS-CHARACTER-ACTION", 2, lane="judged"),
    ]

    envelope = merge.assemble(
        skill="critique-clarity", artifact=artifact, findings=findings, repo_root=REPO_ROOT
    )

    assert envelope["run"]["rubrics"] == ["PLAIN", "WILLIAMS"]


def test_the_artifact_sha256_is_computed_not_supplied(artifact: Path) -> None:
    """One less field the critic can transcribe wrongly."""
    envelope = merge.assemble(
        skill="critique-clarity",
        artifact=artifact,
        findings=[_finding("PLAIN-ACTIVE", 2)],
        repo_root=REPO_ROOT,
    )

    assert envelope["run"]["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()


def test_prose_is_normalised_so_a_stray_dash_cannot_invalidate_the_envelope(artifact: Path) -> None:
    """Same rule bench/baseline/postprocess.py applies, for the same reason: the model was never
    told the house style, and a stray dash should not cost a whole run. PLAIN-AUDIENCE is a
    declared judged criterion, so, unlike a scripted criterion's copy, this finding is kept."""
    em = chr(0x2014)
    findings = [_finding("PLAIN-AUDIENCE", 2, violation=f"Two readers{em}staff and public{em}at once.")]

    envelope = merge.assemble(
        skill="critique-clarity", artifact=artifact, findings=findings, repo_root=REPO_ROOT
    )

    assert em not in envelope["findings"][0]["violation"]
    assert validate_document(envelope).ok


def test_no_findings_is_a_clean_pass(artifact: Path) -> None:
    envelope = merge.assemble(
        skill="critique-clarity", artifact=artifact, findings=[], repo_root=REPO_ROOT
    )

    assert envelope["findings"] == []
    assert envelope["summary"]["gate"] == "pass"
    assert validate_document(envelope).ok


def test_the_cli_reads_findings_on_stdin_and_prints_one_envelope(artifact: Path) -> None:
    """The shape the critic actually invokes: findings in, envelope out, nothing else on stdout."""
    payload = json.dumps({"findings": [_finding("PLAIN-ACTIVE", 2, lane="scripted")]})

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills" / "_shared" / "merge.py"),
            "--skill",
            "critique-clarity",
            "--artifact",
            str(artifact),
        ],
        input=payload,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert proc.returncode == 0, proc.stderr
    envelope = json.loads(proc.stdout)
    assert validate_document(envelope).ok
    assert envelope["run"]["skill"] == "critique-clarity"


def test_the_cli_accepts_a_bare_list_of_findings(artifact: Path) -> None:
    """Models emit both {"findings": [...]} and a bare [...]. Rejecting either would cost a run
    for a formatting choice that carries no meaning."""
    payload = json.dumps([_finding("PLAIN-ACTIVE", 2)])

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills" / "_shared" / "merge.py"),
            "--skill",
            "critique-clarity",
            "--artifact",
            str(artifact),
        ],
        input=payload,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert proc.returncode == 0, proc.stderr
    assert validate_document(json.loads(proc.stdout)).ok


def test_the_cli_reads_findings_from_a_file(artifact: Path, tmp_path: Path) -> None:
    """--findings, because stdin plumbing is what actually broke it in the field.

    Measured in a real session 2026-08-09: the run invoked merge.py with nothing on stdin, got
    "stdin is not valid JSON", then wrote its findings to a JSON file and abandoned the assembler.
    Writing a file first is the natural move for an agent, especially when the command also has to
    `cd` to reach the script, so the tool accepts what it was already doing.
    """
    findings_file = tmp_path / "findings.json"
    findings_file.write_text(json.dumps({"findings": [_finding("PLAIN-ACTIVE", 2)]}), encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills" / "_shared" / "merge.py"),
            "--skill",
            "critique-clarity",
            "--artifact",
            str(artifact),
            "--findings",
            str(findings_file),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert proc.returncode == 0, proc.stderr
    assert validate_document(json.loads(proc.stdout)).ok


def test_an_empty_stdin_says_what_to_do_about_it(artifact: Path) -> None:
    """The observed failure mode deserves an actionable message rather than a JSON parser error,
    because the run that hit it gave up on the tool instead of correcting the call."""
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills" / "_shared" / "merge.py"),
            "--skill",
            "critique-clarity",
            "--artifact",
            str(artifact),
        ],
        input="",
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert proc.returncode != 0
    assert "--findings" in proc.stderr, "the error must name the flag that avoids stdin entirely"


def test_the_cli_fails_loudly_rather_than_printing_an_invalid_envelope(artifact: Path) -> None:
    """Never print something that does not validate: a downstream reader cannot tell a broken
    envelope from a real one, and runner.py already holds this line for the scripted lane.

    Severity 7 on PLAIN-AUDIENCE, a declared judged criterion, rather than an odd criterion name:
    since D2 (requirement 5), an undeclared, non-BYOR criterion is its own rejection (MergeError,
    naming the ID) before the schema validator ever runs. An out-of-range severity does not reach
    the schema validator either, and predates this branch: `by_severity_histogram`
    (`skills/_shared/envelope.py`) keys its counter dict by the five valid severities only, so
    severity 7 raises an uncaught `KeyError` first, with the traceback on stderr and nothing on
    stdout. That still satisfies this test's real guarantee - no invalid envelope ever reaches
    stdout, whatever broke the run - so the assertions stay; only the superseded claim that this
    input reaches the schema validator's own failure path is removed.
    """
    payload = json.dumps({"findings": [_finding("PLAIN-AUDIENCE", 7)]})

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "skills" / "_shared" / "merge.py"),
            "--skill",
            "critique-clarity",
            "--artifact",
            str(artifact),
        ],
        input=payload,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert proc.returncode != 0
    assert proc.stdout.strip() == "", "an invalid envelope must never reach stdout"
    assert "severity" in proc.stderr.lower()
