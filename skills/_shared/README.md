---
title: _shared
---

# _shared

The scripted-lane library every `critique-<domain>` skill's `scripts/checks.py` imports. It exists so
gate exit-code semantics, envelope assembly, and output bounding are implemented once rather than six
times ([S-04 skill-template spec](../../docs/internal/release-plans/plan_v0.1.0/S-04_skill-template/spec.md),
AC-4). A skill's `checks.py` writes one check function and calls `run_scripted_lane`; it never
reimplements anything here.

The underscore prefix keeps this directory out of the family gate's skill scan, which treats exactly
`skills/<dir>/SKILL.md` as the set of skills a plugin ships. `_shared` has no `SKILL.md` and is not a
skill.

## Inventory

- `artifact.py` - `load_artifact()`: read a file, hash its raw bytes, and compute the contract-valid
  relative POSIX path recorded as `run.artifact`.
- `findings.py` - `RawFinding`, the shape a check function returns, and its conversion into a full
  contract finding with `lane` forced to `scripted` and `confidence` to `high`.
- `envelope.py` - `assemble_envelope()`: the four-pass protocol's pass 4 (rank and bound) plus the run
  record and summary. The one place "rank and bound" is defined in code.
- `gate.py` - re-exports `contract.validate`'s `gate_exit_code` and `validate_document`. Nothing here
  is reimplemented; `tests/test_gate.py` asserts function identity, not just equivalent behavior.
- `runner.py` - `run_scripted_lane()`: the whole body of a skill's `checks.py` `main()`, parameterized
  by that skill's own check function.
- `merge.py` - the CLI form of `envelope.py`, for the judged lane. `runner.py` gave the scripted lane
  a way to reach `assemble_envelope()`; the critic had none, because it is prose plus `Bash` and that
  was a Python function, so it did pass 4 in its head from instructions. It did not do it reliably:
  measured 2026-08-09, 2 of 7 benchmark cells produced a contract-valid envelope, failing on a
  histogram that did not total `len(findings)` plus `suppressed_count` and on a `scripted` finding
  claiming less than `high` confidence. Findings in on stdin, one validated envelope out, and
  nothing at all on stdout if it would not validate.
- `tests/` - pytest suite for this library, including the determinism comparison
  (`test_runner.py::test_same_artifact_twice_produces_identical_findings_and_summary`) that the
  template's "What determinism does and does not cover" section points at.
- `__init__.py` - package docstring and module map.

## Using it

See [`docs/internal/skill-template.md`](../../docs/internal/skill-template.md), "Wiring
`scripts/checks.py`", for the bootstrap and the whole worked example a pipeline agent copies. A
committed, self-test-passing instance of that pattern lives at
[`skills/_template-fixture/critique-toy/`](../_template-fixture/critique-toy/).
