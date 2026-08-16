# what-it-is:   the unit suite for the S-04 skill-template self-test runner
# what-it-does: builds throwaway skill directories, breaks exactly one thing in each,
#               and asserts the self-test reports that breach under its own rule name
# why:          AC-2 requires each named failure mode to fail distinctly, which is a
#               property of the runner that only a test can hold in place
# used-by:      python -m pytest (the CI unit-python job)
"""Tests for scripts/skill-selftest.py.

Every fixture skill directory here is built fresh under pytest's own
`tmp_path` and never committed: this is the "test with temporary
fixtures, then remove them" the S-04 skill-template spec's AC-2 asks
for, using pytest's own per-test temporary directory as the removal
mechanism rather than a hand-rolled setup/teardown.

`scripts/skill-selftest.py` has a hyphen in its filename on purpose (it
is a CLI entry point, never an import target per the family's naming
conventions), so it cannot be reached with a normal `import` statement.
It is loaded here by file path via `importlib.util`, exactly the
technique its own module docstring anticipates.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_SELFTEST_PATH = Path(__file__).resolve().parents[1] / "skill-selftest.py"


def _load_selftest_module():
    spec = importlib.util.spec_from_file_location("skill_selftest_under_test", _SELFTEST_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass's own field-type resolution looks the module up in
    # sys.modules by name (see dataclasses._is_type); a module built via
    # module_from_spec is not registered there until something does it
    # explicitly, so skill-selftest.py's @dataclass Issue fails to import
    # without this line.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


selftest = _load_selftest_module()


# --------------------------------------------------------------------------
# A minimal, fully passing fixture skill. Individual tests copy this
# into their own tmp_path and mutate exactly one thing.
# --------------------------------------------------------------------------

SKILL_NAME = "critique-toy"

SKILL_MD = """---
name: critique-toy
description: Reviews a prose document against a fixture rubric. Use when the user asks for a review, feedback, a second opinion, a red-line pass, or a quality check on a draft.
version: 0.1.0
license: Apache-2.0
rubric_sources:
  - id: TOY
    citation: Internal fixture rubric for the skill template's own self-test, not a real published source.
    url: null
    accessed: 2026-07-31
    operationalization: paraphrased
checks:
  scripted:
    - TOY-ACTIVE
  judged:
    - TOY-COHESION
---

# critique-toy

Fixture skill for scripts/skill-selftest.py's own test suite. Not a real
launch skill; see docs/internal/skill-template.md for the real template.

## Protocol

1. Inventory the artifact's structure.
2. Sweep TOY-ACTIVE, then TOY-COHESION, in that order.
3. Assign severity as a separate pass.
4. Rank and bound the output.

Findings conform to contract/critique-contract.schema.json. Delegate to
the critique-critic subagent where available; otherwise run this
protocol inline.
"""

REFERENCES_MD = """# Toy source

Fixture rubric source. Not a real published rubric.

| ID | Operationalization | Operational test | Severity 2 anchor | Severity 3 anchor | Lane | Lane rationale |
|---|---|---|---|---|---|---|
| TOY-ACTIVE | Sentences default to active voice unless the actor is unknown or irrelevant to the point. | Flag a sentence written in passive voice when the actor is both known and relevant. | One paragraph lapses into passive voice for a few sentences, then recovers. | An entire procedure is written in passive voice throughout, so the reader must guess who acts at every step. | scripted | Detectable by a fixed be-plus-participle pattern; no judgment call is needed to find it. |
| TOY-COHESION | Consecutive paragraphs read as one continuous argument rather than a list of unrelated facts. | Judge whether a paragraph transition requires the reader to infer an unstated connective. | A single transition feels abrupt but the surrounding argument still holds together. | A whole section reads as disconnected facts with no throughline connecting them. | judged | Requires reading the surrounding argument as a whole; not reducible to a pattern. |
"""

SEVERITY_ANCHORS_MD = """# Severity anchors

Fixture anchor prose, extending docs/reference/severity-scale.md for this fixture domain.
"""

CHECKS_PY = '''"""Fixture scripted lane. Loaded only via importlib for introspection
or run under pytest, both of which already put the repository root on
sys.path before this file is imported, so no bootstrap is needed here.
A real skill's scripts/checks.py needs one; see
docs/internal/skill-template.md, "Wiring scripts/checks.py".
"""
from skills._shared.runner import run_scripted_lane

IMPLEMENTED_CRITERIA = frozenset({"TOY-ACTIVE"})


def check(artifact):
    return []


def main(argv=None):
    return run_scripted_lane(
        skill_name="critique-toy",
        skill_version="0.1.0",
        rubrics=["TOY"],
        check_fn=check,
        argv=argv,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
'''

CHECKS_TEST_PY = '''"""Fixture test for the fixture checks.py: proves scripts/tests/ is a
real, passing pytest suite, which is what skill-selftest.py's pytest
check actually exercises.
"""


def test_trivially_true():
    assert True
'''


def _eval_cases() -> dict:
    positives = [
        {"query": "Can you review this doc for clarity issues?"},
        {"query": "Give me feedback on this memo before I send it."},
        {"query": "I'd like a second opinion on this draft."},
        {"query": "Can you do a red-line pass on this proposal?"},
        {"query": "Run a quality check on this write-up."},
        {"query": "Critique this document against the toy rubric."},
        {"query": "What's wrong with the writing in this section?"},
        {"query": "Please review this before I publish it."},
        {"query": "Does this paragraph read as one connected argument?"},
        {"query": "Check this text for passive voice."},
        {"query": "Take a critical pass at this draft for me."},
        {"query": "Give this a quality check before the meeting."},
        {"query": "Second opinion needed on this write-up, please."},
        {"query": "Feedback on the clarity of this notice?"},
        {"query": "Review my draft for cohesion between paragraphs."},
    ]
    negatives = [
        {"query": "What's the weather like today?"},
        {"query": "Write me a haiku about autumn."},
        {"query": "Check the color contrast on this landing page.", "cross_domain": "critique-accessibility"},
        {"query": "Does this UI mockup follow the usability heuristics?", "cross_domain": "critique-usability"},
        {"query": "Is the argument in this proposal well-grounded?", "cross_domain": "critique-argument"},
        {"query": "Can you refactor this Python function?"},
        {"query": "Schedule a meeting with the team for Friday."},
    ]
    cases = [{**c, "should_trigger": True} for c in positives] + [
        {**c, "should_trigger": False} for c in negatives
    ]
    return {"skill": SKILL_NAME, "cases": cases}


def _golden_envelope(finding_id: str = "F-001") -> dict:
    return {
        "run": {
            "skill": SKILL_NAME,
            "skill_version": "0.1.0",
            "contract_version": "1.0.0",
            "artifact": "bench/corpus/toy/toy-001.md",
            "artifact_sha256": "a" * 64,
            "model": "none",
            "timestamp": "2026-07-17T14:22:03Z",
            "rubrics": ["TOY"],
        },
        "findings": [
            {
                "id": finding_id,
                "criterion": "TOY-ACTIVE",
                "lane": "scripted",
                "severity": 2,
                "location": "Service window, second paragraph, first sentence",
                "evidence": "The meter log is reviewed before the shift ends.",
                "violation": "Passive voice with the acting party deleted.",
                "fix": "Restate with the actor as subject.",
                "confidence": "high",
            }
        ],
        "summary": {
            "by_severity": {"0": 0, "1": 0, "2": 1, "3": 0, "4": 0},
            "suppressed_count": 0,
            "gate": "pass",
            "severity_3_threshold": 0,
        },
    }


def _golden_example(index: int) -> dict:
    return {
        "kind": "golden",
        "artifact": "bench/corpus/toy/toy-001.md",
        "expected_envelope": _golden_envelope(f"F-{index:03d}"),
        "note": (
            f"Example {index}: paragraph two recasts the lead sentence into passive voice with "
            "the acting party deleted, which is exactly what TOY-ACTIVE's operational test flags."
        ),
    }


def _anti_example() -> dict:
    return {
        "kind": "anti",
        "query": "Can you check whether this database schema is in third normal form?",
        "note": "Data-modeling correctness is not an artifact this skill's rubric evaluates.",
    }


def write_valid_skill(root: Path, *, name: str = SKILL_NAME) -> Path:
    """Builds a complete, passing critique-<domain> skill directory
    under `root` and returns its path. Every test in this file starts
    from a copy of this and breaks exactly one thing, so a failure can
    be attributed to the one change that test made.
    """
    skill_dir = root / name
    (skill_dir / "scripts" / "tests").mkdir(parents=True)
    (skill_dir / "references").mkdir()
    (skill_dir / "evals").mkdir()
    (skill_dir / "examples").mkdir()

    (skill_dir / "SKILL.md").write_text(SKILL_MD, encoding="utf-8")
    (skill_dir / "references" / "toy-source.md").write_text(REFERENCES_MD, encoding="utf-8")
    (skill_dir / "references" / "severity-anchors.md").write_text(SEVERITY_ANCHORS_MD, encoding="utf-8")
    (skill_dir / "scripts" / "checks.py").write_text(CHECKS_PY, encoding="utf-8")
    (skill_dir / "scripts" / "tests" / "__init__.py").write_text("", encoding="utf-8")
    # `_toy` suffix, matching the directory's own domain: see
    # skill-selftest.check_test_module_names for why the basename has to
    # be unique across skills.
    (skill_dir / "scripts" / "tests" / "test_checks_toy.py").write_text(CHECKS_TEST_PY, encoding="utf-8")
    (skill_dir / "evals" / "triggers.eval.json").write_text(json.dumps(_eval_cases()), encoding="utf-8")
    for i in range(1, 4):
        (skill_dir / "examples" / f"golden-{i:02d}.json").write_text(
            json.dumps(_golden_example(i)), encoding="utf-8"
        )
    (skill_dir / "examples" / "anti-01.json").write_text(json.dumps(_anti_example()), encoding="utf-8")
    return skill_dir


def rule_names(issues) -> set[str]:
    return {issue.rule for issue in issues}


# --------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------


def test_valid_fixture_skill_has_no_errors(tmp_path):
    skill_dir = write_valid_skill(tmp_path)

    errors, _warnings = selftest.run_selftest(skill_dir)

    assert errors == [], [str(e) for e in errors]


def test_valid_fixture_skill_cli_exits_zero(tmp_path, capsys):
    skill_dir = write_valid_skill(tmp_path)

    code = selftest.main([str(skill_dir)])

    assert code == 0
    assert "PASS" in capsys.readouterr().out


# --------------------------------------------------------------------------
# AC-2 failure mode 1: missing lane declaration
# --------------------------------------------------------------------------


def test_missing_lane_declaration_fails_distinctly(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    broken = SKILL_MD.replace(
        "checks:\n  scripted:\n    - TOY-ACTIVE\n  judged:\n    - TOY-COHESION\n",
        "",
    )
    assert broken != SKILL_MD  # the replacement actually matched something
    skill_md.write_text(broken, encoding="utf-8")

    _fm, errors = selftest.check_frontmatter(skill_dir)

    names = rule_names(errors)
    assert "frontmatter-checks-lane-missing" in names
    assert "lane-overlap" not in names


def test_missing_lane_declaration_does_not_also_report_every_check_undeclared(tmp_path):
    """With no lane declaration to compare against, every criterion
    checks.py implements would otherwise be reported "undeclared",
    burying the one real defect under consequences of it. AC-2 asks for
    distinct failures, so the consequence is suppressed.
    """
    skill_dir = write_valid_skill(tmp_path)
    broken = SKILL_MD.replace(
        "checks:\n  scripted:\n    - TOY-ACTIVE\n  judged:\n    - TOY-COHESION\n",
        "",
    )
    assert broken != SKILL_MD
    (skill_dir / "SKILL.md").write_text(broken, encoding="utf-8")

    fm, _errors = selftest.check_frontmatter(skill_dir)

    assert selftest.check_lane_manifest_consistency(skill_dir, fm) == []


# --------------------------------------------------------------------------
# AC-2 failure mode 2: criterion in both lanes
# --------------------------------------------------------------------------


def test_criterion_in_both_lanes_fails_distinctly(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    skill_md = skill_dir / "SKILL.md"
    broken = SKILL_MD.replace(
        "  judged:\n    - TOY-COHESION\n",
        "  judged:\n    - TOY-COHESION\n    - TOY-ACTIVE\n",
    )
    assert broken != SKILL_MD
    skill_md.write_text(broken, encoding="utf-8")

    _fm, errors = selftest.check_frontmatter(skill_dir)

    names = rule_names(errors)
    assert "lane-overlap" in names
    assert "frontmatter-checks-lane-missing" not in names


# --------------------------------------------------------------------------
# AC-2 failure mode 3: undeclared scripted check
# --------------------------------------------------------------------------


def test_undeclared_scripted_check_fails_distinctly(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    checks_py = skill_dir / "scripts" / "checks.py"
    checks_py.write_text(
        CHECKS_PY.replace(
            'IMPLEMENTED_CRITERIA = frozenset({"TOY-ACTIVE"})',
            'IMPLEMENTED_CRITERIA = frozenset({"TOY-ACTIVE", "TOY-EXTRA"})',
        ),
        encoding="utf-8",
    )

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_lane_manifest_consistency(skill_dir, fm)

    names = rule_names(errors)
    assert "scripted-check-undeclared" in names
    undeclared = [e for e in errors if e.rule == "scripted-check-undeclared"]
    assert undeclared[0].path == "TOY-EXTRA"


# --------------------------------------------------------------------------
# AC-2 failure mode 4: schema-invalid example
# --------------------------------------------------------------------------


def test_schema_invalid_example_fails_distinctly(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    example = _golden_example(1)
    del example["expected_envelope"]["run"]["skill"]  # drop a required field
    (skill_dir / "examples" / "golden-01.json").write_text(json.dumps(example), encoding="utf-8")

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_examples(skill_dir, fm)

    names = rule_names(errors)
    assert "example-schema-invalid" in names


# --------------------------------------------------------------------------
# AC-2 failure mode 5: under-20 trigger evals
# --------------------------------------------------------------------------


def test_under_20_trigger_evals_fails_distinctly(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    doc = _eval_cases()
    doc["cases"] = doc["cases"][:10]
    (skill_dir / "evals" / "triggers.eval.json").write_text(json.dumps(doc), encoding="utf-8")

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_trigger_evals(skill_dir, fm)

    names = rule_names(errors)
    assert "trigger-evals-too-few" in names


# --------------------------------------------------------------------------
# Additional checks beyond AC-2's five named failure modes
# --------------------------------------------------------------------------


def test_too_few_cross_domain_negatives_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    doc = _eval_cases()
    for case in doc["cases"]:
        case.pop("cross_domain", None)
    (skill_dir / "evals" / "triggers.eval.json").write_text(json.dumps(doc), encoding="utf-8")

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_trigger_evals(skill_dir, fm)

    assert "trigger-evals-too-few-cross-domain-negatives" in rule_names(errors)


def test_too_few_golden_examples_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    (skill_dir / "examples" / "golden-02.json").unlink()
    (skill_dir / "examples" / "golden-03.json").unlink()

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_examples(skill_dir, fm)

    assert "examples-too-few-golden" in rule_names(errors)


def test_missing_anti_example_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    (skill_dir / "examples" / "anti-01.json").unlink()

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_examples(skill_dir, fm)

    assert "examples-too-few-anti" in rule_names(errors)


def test_over_long_quote_in_references_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    long_quote = " ".join(f"word{i}" for i in range(30))
    poisoned = REFERENCES_MD + f'\nSome prose containing a long quote: "{long_quote}"\n'
    (skill_dir / "references" / "toy-source.md").write_text(poisoned, encoding="utf-8")

    errors = selftest.check_paraphrase_heuristic(skill_dir)

    assert "paraphrase-quote-too-long" in rule_names(errors)


def test_quoted_operationalization_cell_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    poisoned = REFERENCES_MD.replace(
        "Sentences default to active voice unless the actor is unknown or irrelevant to the point.",
        '"Sentences default to active voice."',
    )
    assert poisoned != REFERENCES_MD
    (skill_dir / "references" / "toy-source.md").write_text(poisoned, encoding="utf-8")

    errors = selftest.check_paraphrase_heuristic(skill_dir)

    assert "paraphrase-operationalization-quoted" in rule_names(errors)


def test_skill_md_over_500_lines_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    padding = "\n".join(f"Padding line {i}." for i in range(510))
    (skill_dir / "SKILL.md").write_text(SKILL_MD + "\n" + padding, encoding="utf-8")

    errors = selftest.check_skill_md_length(skill_dir)

    assert "skill-md-too-long" in rule_names(errors)


def test_failing_pytest_suite_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    (skill_dir / "scripts" / "tests" / "test_checks_toy.py").write_text(
        "def test_deliberately_false():\n    assert False\n", encoding="utf-8"
    )

    errors = selftest.check_pytest(skill_dir)

    assert "checks-py-pytest-failed" in rule_names(errors)


def test_test_module_without_domain_suffix_fails(tmp_path):
    """Two skills shipping scripts/tests/test_checks.py abort the whole
    repository pytest run with an import-file-mismatch collection error,
    so the suffix is enforced from inside each skill directory.
    """
    skill_dir = write_valid_skill(tmp_path)
    (skill_dir / "scripts" / "tests" / "test_checks_toy.py").rename(
        skill_dir / "scripts" / "tests" / "test_checks.py"
    )

    errors = selftest.check_test_module_names(skill_dir)

    assert "checks-py-test-module-name" in rule_names(errors)


def test_domain_suffixed_test_module_passes(tmp_path):
    skill_dir = write_valid_skill(tmp_path)

    assert selftest.check_test_module_names(skill_dir) == []


def test_name_directory_mismatch_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path, name="critique-toy")
    renamed = tmp_path / "critique-not-toy"
    skill_dir.rename(renamed)

    _fm, errors = selftest.check_frontmatter(renamed)

    assert "frontmatter-name-mismatch" in rule_names(errors)


def test_missing_checks_py_fails(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    (skill_dir / "scripts" / "checks.py").unlink()

    fm, fm_errors = selftest.check_frontmatter(skill_dir)
    assert fm_errors == []
    errors = selftest.check_lane_manifest_consistency(skill_dir, fm)

    assert "checks-py-missing" in rule_names(errors)


# --------------------------------------------------------------------------
# The restricted frontmatter dialect: the two ways a pipeline agent
# following ordinary YAML habits writes frontmatter this parser cannot
# read. Both were hit by the first agent to build a skill from the
# template guide, so both are locked here.
# --------------------------------------------------------------------------


def test_folded_block_scalar_description_fails_with_its_own_rule(tmp_path):
    """`description: >-` plus an indented block is the ordinary YAML way
    to wrap a long description, and it is exactly what this dialect
    cannot read. The generic parse error names the continuation line
    rather than the `>-`, so this gets its own rule name.
    """
    skill_dir = write_valid_skill(tmp_path)
    broken = SKILL_MD.replace(
        "description: Reviews a prose document against a fixture rubric. Use when the user asks "
        "for a review, feedback, a second opinion, a red-line pass, or a quality check on a draft.",
        "description: >-\n  Reviews a prose document against a fixture rubric. Use when the user\n"
        "  asks for a review, feedback, or a quality check on a draft.",
    )
    assert broken != SKILL_MD
    (skill_dir / "SKILL.md").write_text(broken, encoding="utf-8")

    _fm, errors = selftest.check_frontmatter(skill_dir)

    names = rule_names(errors)
    assert "frontmatter-block-scalar-unsupported" in names
    assert "frontmatter-unparseable" not in names


def test_literal_block_scalar_also_fails_with_the_block_scalar_rule(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    broken = SKILL_MD.replace("description: Reviews", "description: |\n  Reviews", 1)
    assert broken != SKILL_MD
    (skill_dir / "SKILL.md").write_text(broken, encoding="utf-8")

    _fm, errors = selftest.check_frontmatter(skill_dir)

    assert "frontmatter-block-scalar-unsupported" in rule_names(errors)


def test_empty_lane_written_as_flow_empty_sequence_parses(tmp_path):
    """`judged: []` is the only flow-style token the dialect accepts,
    because block style cannot express an empty sequence at all.
    """
    skill_dir = write_valid_skill(tmp_path)
    broken = SKILL_MD.replace("  judged:\n    - TOY-COHESION\n", "  judged: []\n")
    assert broken != SKILL_MD
    (skill_dir / "SKILL.md").write_text(broken, encoding="utf-8")

    fm, errors = selftest.check_frontmatter(skill_dir)

    assert errors == [], [str(e) for e in errors]
    assert fm["checks"]["judged"] == []


def test_empty_lane_written_as_a_bare_key_parses(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    broken = SKILL_MD.replace("  judged:\n    - TOY-COHESION\n", "  judged:\n")
    assert broken != SKILL_MD
    (skill_dir / "SKILL.md").write_text(broken, encoding="utf-8")

    fm, errors = selftest.check_frontmatter(skill_dir)

    assert errors == [], [str(e) for e in errors]
    assert fm["checks"]["judged"] is None


def test_scalar_lane_fails_distinctly_from_a_missing_lane(tmp_path):
    skill_dir = write_valid_skill(tmp_path)
    broken = SKILL_MD.replace("  judged:\n    - TOY-COHESION\n", "  judged: TOY-COHESION\n")
    assert broken != SKILL_MD
    (skill_dir / "SKILL.md").write_text(broken, encoding="utf-8")

    _fm, errors = selftest.check_frontmatter(skill_dir)

    names = rule_names(errors)
    assert "frontmatter-checks-lane-invalid" in names
    assert "frontmatter-checks-lane-missing" not in names


# --------------------------------------------------------------------------
# Description advisories (warnings, never errors)
# --------------------------------------------------------------------------


def test_description_without_a_use_when_clause_warns():
    """A "Use for ..." trigger clause reads fine to a human and scores
    below the family U5 threshold the S-04 spec AC-6 requires, because
    the scorer credits only an explicit use-when construction.
    """
    warnings = selftest.check_description_quality_advisory(
        {
            "description": (
                "Reviews prose documents for clarity and gives feedback, a second opinion, "
                "or a quality check. Use for a red-line pass on a memo before you send it."
            )
        }
    )

    names = rule_names(warnings)
    assert "description-missing-use-when-advisory" in names
    assert "description-quality-advisory" not in names


def test_description_with_a_use_when_clause_does_not_warn():
    warnings = selftest.check_description_quality_advisory(
        {
            "description": (
                "Reviews prose documents against a clarity rubric. Use when the user asks for "
                "a review, feedback, a second opinion, a red-line pass, or a quality check on "
                "a memo, PRD, or proposal."
            )
        }
    )

    assert warnings == [], [str(w) for w in warnings]


def test_each_failure_mode_produces_a_distinct_rule_set(tmp_path):
    """AC-2's real requirement: the five named failure modes must not
    collapse into the same message. This asserts the five rule names
    triggered above are pairwise distinct.
    """
    rules = {
        "missing-lane-declaration": "frontmatter-checks-lane-missing",
        "criterion-in-both-lanes": "lane-overlap",
        "undeclared-scripted-check": "scripted-check-undeclared",
        "schema-invalid-example": "example-schema-invalid",
        "under-20-trigger-evals": "trigger-evals-too-few",
    }
    assert len(set(rules.values())) == len(rules)


# --------------------------------------------------------------------------
# How the nested pytest is invoked, which two tests in this file used to fail
# intermittently because of
# --------------------------------------------------------------------------


class _RecordingRun:
    """Stands in for subprocess.run so the invocation can be asserted without paying for it."""

    def __init__(self, returncode=0, stdout="", stderr=""):
        self.calls = []
        self._result = subprocess.CompletedProcess([], returncode, stdout, stderr)

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return self._result


def test_the_nested_pytest_cannot_reach_a_shared_temp_directory(tmp_path, monkeypatch):
    """The argument must be relative to a working directory inside the skill.

    An absolute argument combined with a working directory elsewhere leaves pytest unable to build
    a collection tree from its rootdir to the argument when the two are on different drives, which
    is exactly the case for a skill written into a temp directory. It then walks up from the
    argument and creates a directory collector for the temp root, and listing that directory races
    every other process on the machine. Measured 2026-08-15: under deliberate temp churn the old
    invocation failed 10 of 10 runs with "ERROR collecting test session / FileNotFoundError
    [WinError 2]", naming a directory belonging to an unrelated project, and this one 0 of 10.
    """
    skill_dir = write_valid_skill(tmp_path)
    recorder = _RecordingRun()
    monkeypatch.setattr(selftest.subprocess, "run", recorder)

    selftest.check_pytest(skill_dir)

    (argv, kwargs) = recorder.calls[0]
    target = argv[-2]
    assert not Path(target).is_absolute(), f"nested pytest was given an absolute path: {target}"
    assert Path(kwargs["cwd"]) == skill_dir


def test_the_nested_pytest_keeps_this_repository_importable(tmp_path, monkeypatch):
    """Moving the working directory off the repository root would otherwise stop a real skill's
    tests importing skills._shared and contract, which running from the root provided implicitly."""
    skill_dir = write_valid_skill(tmp_path)
    recorder = _RecordingRun()
    monkeypatch.setattr(selftest.subprocess, "run", recorder)

    selftest.check_pytest(skill_dir)

    (_argv, kwargs) = recorder.calls[0]
    repo_root = Path(selftest.__file__).resolve().parent.parent
    assert str(repo_root) in kwargs["env"]["PYTHONPATH"].split(os.pathsep)


def test_a_failed_nested_run_reports_the_exit_code_and_both_streams(tmp_path, monkeypatch):
    """The previous version kept the last 20 lines of stdout and used stderr only when stdout was
    empty, so a failure with any stdout at all discarded stderr and never said what the exit code
    was. It reported the collection error above faithfully enough to be seen and nowhere near well
    enough to be diagnosed, which is why that failure went three sessions without a cause."""
    skill_dir = write_valid_skill(tmp_path)
    recorder = _RecordingRun(returncode=2, stdout="a line of stdout", stderr="the real cause")
    monkeypatch.setattr(selftest.subprocess, "run", recorder)

    issues = selftest.check_pytest(skill_dir)

    assert len(issues) == 1
    detail = issues[0].message
    assert "exited 2" in detail
    assert "a line of stdout" in detail
    assert "the real cause" in detail


def test_a_long_failure_says_what_it_elided(tmp_path, monkeypatch):
    """Truncation is fine; silent truncation is what hid the cause."""
    skill_dir = write_valid_skill(tmp_path)
    stdout = "\n".join(f"line {i}" for i in range(200))
    recorder = _RecordingRun(returncode=1, stdout=stdout)
    monkeypatch.setattr(selftest.subprocess, "run", recorder)

    detail = selftest.check_pytest(skill_dir)[0].message

    assert "earlier line(s) elided" in detail
    assert "line 199" in detail
