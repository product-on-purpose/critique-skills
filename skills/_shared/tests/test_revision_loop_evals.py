"""Execute every case in evals/*.eval.json (N4 decisions D6 and D8; Gold check G3).

The toolkit's G3 check confirms only that each chain edge in agents/_chain-permitted.yaml has an
eval set naming it. It never runs the cases. This file does, in the existing unit-python job, so an
eval's `expect` is a tested claim and not a sentence. Each case carries a machine-readable `run`
object beside its human `given` and `expect`. No case calls a model (AC-10).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skills._shared import revision_loop as rl

REPO_ROOT = Path(__file__).resolve().parents[3]
# Only chain eval sets. evals/ also holds joint-routing.eval.json, a `covers.skill` routing eval
# with its own scorer (scripts/run-joint-routing.py), which this file must not try to execute.
EVAL_FILES = sorted(
    p
    for p in (REPO_ROOT / "evals").glob("*.eval.json")
    if "chain" in json.loads(p.read_text("utf-8")).get("covers", {})
)
CHAIN_FILE = REPO_ROOT / "agents" / "_chain-permitted.yaml"
SKILLS = sorted(p.parent.name for p in (REPO_ROOT / "skills").glob("critique-*/SKILL.md"))


def _contract_edges() -> set[tuple[str, str]]:
    """Parse the chain contract's `caller:` / `  - callee` shape without a YAML dependency."""
    edges: set[tuple[str, str]] = set()
    caller = None
    for line in CHAIN_FILE.read_text("utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[0].isspace() and line.rstrip().endswith(":"):
            caller = line.rstrip()[:-1]
        elif line.strip().startswith("- ") and caller is not None:
            edges.add((caller, line.strip()[2:].strip()))
    return edges


def _cases() -> list[tuple[str, int, dict]]:
    out = []
    for path in EVAL_FILES:
        data = json.loads(path.read_text("utf-8"))
        for index, case in enumerate(data["cases"]):
            out.append((path.name, index, case))
    return out


def test_every_registered_skill_has_an_edge_to_the_critic():
    # N4 decision D7: the loop accepts all seven registered skills, uniformly.
    assert _contract_edges() == {(skill, "critique-critic") for skill in SKILLS}


def test_every_edge_has_exactly_one_eval_set_and_no_eval_is_stale():
    covered = []
    for path in EVAL_FILES:
        covered.append(tuple(json.loads(path.read_text("utf-8"))["covers"]["chain"]))
    assert sorted(covered) == sorted(_contract_edges())


@pytest.mark.parametrize("file,index,case", _cases(), ids=lambda v: str(v) if not isinstance(v, dict) else "")
def test_eval_case(file: str, index: int, case: dict, tmp_path: Path):
    run = case["run"]
    assert run["command"] == "brief"
    envelope = rl.load_envelope(REPO_ROOT / run["envelope"])
    log = rl.load_disposition_log(REPO_ROOT / run["dispositions"], envelope=envelope)
    if "iteration" in run:
        log = {**log, "contract_version": "1.1.0", "iteration": run["iteration"]}

    check, brief = rl.pause(envelope, log)

    assert check.decision == run["decision"], f"{file} case {index}"
    if run["brief"] is None:
        assert brief is None
    else:
        expected = (REPO_ROOT / run["brief"]).read_text("utf-8")
        assert rl.serialize_brief(brief) == expected, f"{file} case {index}"


def test_no_eval_case_names_a_model():
    # AC-10: every case runs on committed fixtures, never a model.
    for file, index, case in _cases():
        assert "model" not in case["run"], f"{file} case {index}"
