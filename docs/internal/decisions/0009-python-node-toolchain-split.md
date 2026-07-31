# 0009 - Python and Node toolchain split

## TL;DR
- **Decision:** Skill scripts and the bench generator are written in Python; repository tooling (generators, the family conformance-gate wiring) and CI orchestration are written in Node.
- **Why:** Python is agent-portable and matches the existing Vault Generator precedent for deterministic seeded generation; Node matches the family's CI and conformance-gate baseline that `pm-skills` and `thinking-framework-skills` already use.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

critique-skills needs two categories of executable machinery, either of which could reasonably be built in either language: skill-level scripted checks and the bench corpus generator (deterministic, seeded, no external services), and repository-level tooling (the family conformance gate, README and INDEX generators, CI job scripts). A single-language repository is simpler to onboard into, but the two categories have different precedents to match: the family's shared conformance gate and CI baseline in `agent-skills-toolkit` (per that toolkit's own ADR 0025, raising the Node baseline) is Node-based, while the closest family precedent for deterministic seeded generation, the Vault Generator, is Python-based.

## Decision drivers

- Matching each category of machinery to its strongest existing precedent, rather than forcing a single language across the whole repository.
- Python's stdlib-preferred posture suits agent-authored, dependency-light scripted checks and a seeded generator that must produce byte-identical output on repeated runs (S-03, bench-harness spec, requirements).
- Node is already the language the family's conformance gate, CI job scripts, and generator drift-checks are written in across the sibling repos, so wiring critique-skills into that gate (S-01 AC-7; S-07, CI-pipeline spec) is simplest if repository tooling speaks the same language the gate does.

## Considered options

1. **Single language across the whole repository** (either all-Python or all-Node). Not pursued: an all-Python repository would have to reimplement or wrap the family's Node-based conformance gate rather than consume it directly, diverging from the pattern S-01 AC-7 requires (inspect and copy whatever `pm-skills` and `thinking-framework-skills` currently do). An all-Node repository would abandon the Vault Generator's Python precedent for deterministic seeded generation, the closest working example the family has for exactly the bench-corpus-generation problem (S-03).
2. **Split by function: Python for skill scripts and the bench generator, Node for repository tooling and the gate (chosen).**

## Decision outcome

Option 2, matching each half of the repository to the family precedent that already solved its specific problem, rather than optimizing for single-language simplicity.

## Consequences

**Positive:** the bench generator and contract validator can stay Python-stdlib-preferred, with any third-party dependency requiring its own ADR justification (S-02 and S-03 Non-Functional Requirements), keeping them portable and audit-light. The conformance gate, README and INDEX generators, and CI job orchestration reuse the family's existing Node tooling patterns directly instead of reimplementing them.

**Negative:** contributors and build-run agents need both toolchains available (Python 3.12; Node 22.12.0 and 24, per the CI matrix). A class of bugs, drift between what a Python-generated artifact says and what a Node-based generator or gate expects, becomes possible at the seam, and the schema (S-02) is the single enforced contract across that boundary.

**Neutral:** this split by implementation language mirrors, but is orthogonal to, the CI plan's own two-lane philosophy of deterministic-in-CI versus model-dependent-out-of-it.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per S-02 (critique-contract spec) and S-03 (bench-harness spec) Non-Functional Requirements, this decision will place Python at:

- `contract/critique-contract.schema.json`'s validator (Python 3.12 stdlib plus `jsonschema` only).
- `bench/generator/` (Python 3.12, stdlib-preferred).

Per S-07 (CI-pipeline spec) and S-01 AC-7, it will place Node at:

- The family conformance-gate wiring (mechanism, vendored, dependency, or wrapper, chosen and recorded as its own ADR during phase P0, per S-07's own open question).
- The repository's generator scripts, invoked as `npm run gen` and `npm run check`.
