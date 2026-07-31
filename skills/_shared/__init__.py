"""Shared library every critique-<domain> skill's scripts/checks.py
imports for its scripted lane: finding emission, envelope assembly,
artifact loading, and gate exit codes.

Why this package exists (S-04 skill-template spec, AC-4): the critique
contract's gate semantics (docs/reference/critique-contract.md, "Gate
exit codes") must mean exactly the same thing in every skill. This
package wraps `contract/validate.py` rather than reimplementing any of
its logic, so that "same thing" is structurally true, not just a
convention six skill pipelines are asked to follow independently.

Modules:

    artifact.py   load_artifact(): read a file, hash it, and compute the
                  contract-valid relative POSIX path recorded as
                  run.artifact.
    findings.py   RawFinding, the shape a check function returns; turns
                  a RawFinding into a full contract finding dict with
                  lane forced to "scripted" and confidence forced to
                  "high" (methodology section 7).
    envelope.py   assemble_envelope(): the four-pass protocol's pass 4
                  (rank and bound) plus the run record and summary,
                  producing one contract-valid envelope.
    gate.py       Re-exports contract.validate's gate_exit_code and
                  validate_document. Nothing here is reimplemented.
    runner.py     run_scripted_lane(): the whole of a skill's
                  scripts/checks.py main(), parameterized by the
                  skill's own check function.

A skill's scripts/checks.py is usually invoked directly
(`python skills/critique-clarity/scripts/checks.py <artifact>`), not via
`python -m`, so nothing puts the repository root on sys.path
automatically. See docs/internal/skill-template.md, "Wiring
scripts/checks.py", for the two-line bootstrap every checks.py starts
with before importing this package.
"""
