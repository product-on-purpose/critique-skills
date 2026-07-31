# 0013 - The critique contract versions independently of the plugin, starting at 1.0.0

## TL;DR
- **Decision:** `contract_version` is a semantic version owned by `contract/critique-contract.schema.json` alone, unrelated to the plugin version in `library.json`. It starts at `1.0.0` while the plugin is at `0.1.0`. The schema file validates 1.x documents only: `contract_version` is patterned `^1\.<minor>\.<patch>`, so a 2.x document is rejected here by design and validates against a future 2.x schema file at a different path. The release version-bump tooling must never touch it.
- **Why:** the plugin version tracks a shipping slate that will move fast (v0.1 six skills, v0.2 BYOR, v0.3 revision loops), while the contract is the frozen interface that skills, the bench, the critic subagent, CI, and any downstream script all pin against. Tying the two would either force a contract major bump every time a skill ships, or force skills to stall behind an interface that has not changed. Starting at 1.0.0 rather than 0.1.0 states the actual promise: phase A3's decision gate already makes a required-field change a build-run stop condition, and 0.x in semver means the opposite.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P1 contract-designer pass (Claude)

## Context and problem statement

[S-02 (critique-contract spec)](../release-plans/plan_v0.1.0/S-02_critique-contract/spec.md) OQ-2 asks "whether `contract_version` starts at `1.0.0` independent of plugin version," recommends yes, and directs an ADR at phase P1. The same spec places "contract versioning machinery beyond a `contract_version` field" out of scope, so the decision needed here is the versioning policy and its enforcement in the schema, not a migration framework.

The field exists because the envelope has to be self-describing. An envelope in `bench/results/` outlives the run that produced it and is read by metrics code, by table generators, by an external reader reproducing a published number, and by whatever the library becomes in a year. Without a version in the document, a consumer meeting an envelope has to guess which shape it is from the fields present, which is exactly the failure mode the contract exists to remove.

## Decision drivers

- The two things version at different rates and for different reasons. `library.json` is at `0.1.0` and moves when the skill slate, the plugin surface, or the packaged components change. The contract moves only when the interface between producers and consumers changes. In v0.1 the plugin will ship, hold, or drop stretch skills based on measured results, and none of those outcomes is a contract change.
- The contract has consumers the plugin version cannot speak for. `bench/metrics/`, the gate exit codes consumed by other people's CI, and the disposition log written by a human hours after the run all pin the contract. A downstream script pinning "critique-skills 0.1.0" learns nothing about whether `summary.severity_3_threshold` exists.
- Semver 0.x explicitly means the public API may change at any time. The build plan says the opposite about this file: after phase A3 (contract frozen), a change to finding or envelope required fields is a stop condition requiring a written handover. Publishing that interface as 0.x would understate a commitment already made.
- A schema file that silently accepts a document written for a different major version is worse than one that rejects it, because the failure surfaces later, in a metric, as a wrong number rather than an error.
- [S-07 (CI-pipeline spec)](../release-plans/plan_v0.1.0/S-07_ci-pipeline/spec.md) requires all version-bearing files to be enumerated in one place consumed by both the release workflow and the version-bump script, and `release.yml` to enforce tag-equals-manifests consistency. An independently versioned contract is a trap for exactly that machinery unless it is excluded explicitly.

## Considered options

1. **`contract_version` mirrors the plugin version.** Rejected: every skill-slate release would bump the contract, so the number would stop meaning "the interface changed" within one release cycle, and a consumer could not tell a real interface change from a packaging change. It also makes the v0.1 contract 0.1.0, advertising instability the build plan does not intend.
2. **No `contract_version` field, with the schema's `$id` carrying the version.** Rejected: the envelope stops being self-describing, and a stored envelope read without its schema URL cannot be routed. `$id` is a schema identity, not a document assertion.
3. **Independent semver starting at `0.1.0`.** Rejected for the semantics: 0.x invites breaking changes, and the first thing this contract does is forbid them.
4. **Independent semver starting at `1.0.0`, with the schema file constrained to its own major (chosen).**

## Decision outcome

Option 4, with these rules.

**Numbering.** Contract 1.0.0 ships with plugin 0.1.0. The two numbers are never compared, added to a table together, or bumped in the same operation.

**What each level means, for this contract specifically:**

- **Patch** (1.0.x): editorial only. Descriptions, titles, examples, `$comment` text. No document that validated before may fail after, and no document that failed before may pass.
- **Minor** (1.x.0): backward-compatible for producers. New optional fields, new `$defs`, relaxed constraints, added enum members. A 1.0.0 document still validates against a 1.1.0 schema. A 1.1.0 document may fail against the 1.0.0 schema, because every object sets `additionalProperties: false`; that asymmetry is intended, and it is why consumers read `contract_version` rather than assuming.
- **Major** (2.0.0): anything else. Adding or removing a required field, tightening a constraint, renaming, or changing what a field means. A major version ships as a new schema file at a new path with its own `$id`, and this file keeps validating 1.x forever.

**Enforcement in the schema.** `$defs/contractVersion` is patterned `^1\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)` with an end-of-input assertion: no leading `v`, no prerelease or build metadata, major pinned to 1. `run.contract_version` and `dispositionLog.contract_version` are both required, so every stored document declares which contract it was written against. The plugin's own `skill_version` uses the full Semantic Versioning 2.0.0 grammar (`$defs/semver`) including prerelease, and is a separate definition precisely so the two can never be conflated by a future edit.

**Enforcement outside the schema.** The version-bump script and `release.yml` version-consistency check (S-07, CI-pipeline spec) enumerate version-bearing files; `contract/critique-contract.schema.json` and the `contract_version` values inside envelopes and fixtures are excluded from that enumeration by name, and the exclusion is commented as deliberate. A tag-equals-manifests check that reaches into the contract is a defect.

## Consequences

**Positive:** the interface can hold still through a fast-moving release slate, and a stored envelope tells any future reader exactly which rules it was written under. Downstream consumers pin one small number that changes rarely. A 2.x document cannot be quietly mis-measured by 1.x tooling, because the schema rejects it at the version field rather than at whichever field happened to change.

**Negative:** two version numbers exist in one repository, which is a documentation burden and an obvious place for a contributor or an agent to "helpfully" synchronize them. The mitigation is stated exclusion in the release tooling plus this ADR; the risk is real and permanent.

**Neutral:** the contract will likely sit at 1.0.0 for the whole of v0.1 and possibly longer. A version number that does not move is doing its job.

## Implementation sites

- `contract/critique-contract.schema.json`: `$defs/contractVersion` (pattern and description), `$defs/semver` (the separate, full grammar for skill versions), `run.contract_version`, `dispositionLog.contract_version`, and the root `$comment` and `description` naming the file as contract 1.0.0.
- `contract/README.md`: the versioning section, including the compatibility rules above.
- Not yet created: the version-bump script and `.github/workflows/release.yml` (S-07, CI-pipeline spec), which must exclude the contract from the plugin version sweep; `contract/validate.py`, which reads `contract_version` for routing and error reporting.
