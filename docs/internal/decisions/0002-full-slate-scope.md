# 0002 - Full slate scope for v0.1.0

## TL;DR
- **Decision:** v0.1.0 ships the full slate together: the methodology document, the contract schema, the skills, a seeded-defect benchmark with published results, gate mode, and triggering evals, rather than staging these across releases.
- **Why:** "A skill with no measured performance is a draft." The library's whole thesis is accountable, measured critique, so a release that ships skills without numbers undermines the exact trust the project exists to build.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

critique-skills is the third library in the product-on-purpose family, and its differentiator, per `01-strategy-brief.md`, is that critique is rubric-cited, machine-parseable, and measured, not merely produced. A conventional first release of a skills library could reasonably ship the skills alone and add a benchmark, contract schema, or gate mode in a follow-up release once real usage data exists. That path was available and would have reduced first-release scope. But the strategy brief's problem-space analysis (section 2) is explicit that a mediocre launch is unusually damaging for this particular library: "A skills library that claims 'measured performance' and ships without numbers, or publishes numbers that do not replicate, damages the exact trust it exists to build." The decision was whether v0.1.0 is allowed to be a partial slate (skills first, evidence later) or must be the full slate (skills and their evidence, together, on day one).

## Decision drivers

- The library's differentiator is the evidence itself, not the skills alone; almost any agent can write a critique prompt, but almost nobody in the niche publishes recall, precision, and consistency numbers against a benchmark.
- "Solved" for v0.1.0 is defined in the strategy brief as every shipped skill having a published recall, precision, and consistency number against a seeded corpus, and a baseline comparison it wins.
- Shipping skills without that evidence would make v0.1.0 indistinguishable from every other critique-prompt library already in the niche, defeating the point of the launch.

## Considered options

1. **Partial slate: skills first, benchmark and gate mode in a later release.** Grounded in the strategy brief's own problem-space warning about shipping unmeasured claims. Not pursued: it would leave the launch with nothing to differentiate it from an ordinary prompt library, and it would require re-opening every skill's contract surface later to retrofit measurement, which conflicts with the foundation-serial build order chosen separately (see [0007 - Foundation-serial, skills-parallel build architecture](0007-foundation-serial-skills-parallel-build.md)), which freezes the contract before skills exist specifically so measurement is designed in, not bolted on afterward.
2. **Full slate: methodology, contract, skills, benchmark with results, gate mode, and triggering evals together in v0.1.0 (chosen).**

## Decision outcome

Option 2. "Full slate" is bounded scope, not unlimited scope: the strategy brief's 80/20 recommendation (section 5) explicitly defers Silver-tier conformance, the docs site, Substack essays, community intake, the taxonomy-survey regeneration, and any GUI. Full slate means every piece needed to make the accountable-critique claim credible ships together in v0.1.0; everything else ships later, on the roadmap.

## Consequences

**Positive:** the launch's central claim is evidenced on day one rather than promised for later; the release-plan's own gates (`05-release-plan.md` gates (g) and (h)) have real numbers to check at RC review, not placeholders.

**Negative:** materially larger first-release scope than a skills-only launch. This is carried by the fully autonomous build model (see [0008 - Fully autonomous build to RC](0008-fully-autonomous-build-to-rc.md)) rather than by staging the work across incremental releases. If a core skill fails to beat baseline, the release plan's gate (g) makes that a release blocker, so this decision accepts the possibility of a launch delay over shipping an unmeasured skill.

**Neutral:** the known-gaps section of `00-README.md` (the missing taxonomy survey, the placeholder consistency floor) shows that "full slate" does not mean every open question is pretended closed; it means every claim the release actually makes is backed by a repo artifact.

## Implementation sites

No single code implementation site; this is a scope decision, not a behavior a script enforces. It is operationalized structurally by:

- The release-plan gates in `05-release-plan.md` (gates (f) through (i)), migrating to `docs/internal/release-plans/plan_v0.1.0/` per the S-01 spec.
- The eight specs S-01 through S-08, which together cover contract, bench, skills, and docs as one coordinated release rather than a sequence of separate releases.

None of the in-repo artifacts above exist yet; the repository is pre-scaffold as of this ADR's date.
