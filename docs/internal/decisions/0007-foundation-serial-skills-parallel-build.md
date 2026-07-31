# 0007 - Foundation-serial, skills-parallel build architecture

## TL;DR
- **Decision:** Freeze the Critique Contract schema and the shared 0-4 severity scale before starting any of the six skill pipelines, then run all six skill pipelines, plus the critic subagent, in parallel against the frozen interfaces.
- **Why:** Under a fully autonomous build with no human checkpoint until the release candidate, interface stability matters more than early visible output; letting six pipelines evolve the shared contract concurrently is the exact drift the methodology exists to prevent.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Builds on

- [0008 - Fully autonomous build to RC](0008-fully-autonomous-build-to-rc.md), the autonomy model this build order is designed to be safe under.

## Context and problem statement

The build run (`workflow/workflow-design.md`) executes six skill pipelines and one bench harness under full autonomy (see [0008 - Fully autonomous build to RC](0008-fully-autonomous-build-to-rc.md)), with no human review until the RC handover. The contract schema, severity scale, and criterion-ID grammar (S-02, the critique-contract spec) are consumed by every one of those pipelines. If each pipeline is free to shape the contract as it builds its own skill, the six pipelines can converge on six incompatible interpretations of the same fields, and nobody catches the drift until integration, deep into a run nobody is watching in real time. Three build shapes were evaluated in the planning session for how to sequence contract design against skill construction (`01-strategy-brief.md` section 4).

## Decision drivers

- Interface stability is non-negotiable under full autonomy, because no human is in the loop to catch drift as it happens.
- The methodology's own thesis, rubric-cited, machine-parseable, measured critique, depends on every skill emitting the identical contract shape.
- Parallel execution capacity already exists in the workflow design (phase P2 runs six pipelines) and should not be wasted by needlessly serializing skill-building too.

## Considered options

1. **Foundation-serial, skills-parallel (chosen).** Freeze the contract, severity scale, and bench harness (phase P1) before the six-skill parallel fan-out (phase P2); measure everything in one phase (P3); gate the stretch skills on results. Pros: interface stability under full autonomy, honest gating, still gets parallel scale wherever it is safe (across skills, not across contract design). Cons: no visible output until mid-run; the foundation phase concentrates design risk into P0 and P1. Mitigation: the foundation specs, S-02 and S-03, are the most detailed in the suite and get the strongest model attention (opus-tier contract-designer and bench-architect roles, per `workflow-design.md`'s model-routing table) plus adversarial review.
2. **Bench-spine.** Corpus and baselines before any skill exists. Rejected for v0.1.0 (`01-strategy-brief.md` section 4, option B): the purest credibility path, ground truth exists before anything is measured against it, but the generator would be designed blind to what real skills actually need to express, and the hardest calibration work (what counts as a defect, what location-match tolerance a domain needs) would happen with the least information available.
3. **Skill-slice pipelining.** Build and evolve the contract incrementally, one skill at a time, each iteration refining the shared interfaces. Rejected (`01-strategy-brief.md` section 4, option C): concurrent contract evolution across six slices is precisely the drift the methodology exists to prevent; the shared, frozen, machine-parseable contract every skill honors identically would not survive this build order intact.

## Decision outcome

Option 1, chosen explicitly over options 2 and 3 in the planning session. The phase DAG in `workflow-design.md` operationalizes it: P0 scaffold, then P1 foundation (contract frozen, bench core verified, CI live) as an explicit gate before P2's six-pipeline fan-out opens.

## Consequences

**Positive:** every skill pipeline in P2 builds against a contract that cannot move under it. The interface-level halt rule (`workflow-design.md` failure policy item 3: "any post-P1 change to contract required fields is a halt, never a quiet edit") makes drift structurally visible instead of silently absorbed.

**Negative:** P0 and P1 concentrate real design risk into the phases with the least parallel review capacity (an estimated 4 to 12 agents, versus P2's estimated 30 to 40). A mistake frozen at P1 propagates to all six pipelines before P3 measurement would even have a chance to surface it. The committed mitigation is opus-tier design roles plus adversarial review specifically at this phase.

**Neutral:** no visible product output exists until mid-run; anyone auditing the build's progress before P2 completes sees interfaces and infrastructure, not skills.

## Implementation sites

`workflow/workflow-design.md` (the Autonomous Build-Run Design document, currently at `_local/initial-plan/workflow/workflow-design.md`, migrating to `docs/internal/release-plans/plan_v0.1.0/` per S-01's requirement) already encodes the phase ordering as of this ADR's date; that document exists now. The concrete Workflow orchestration script implementing phases P0 through P5 is authored at launch, per that document's own convention ("Concrete scripts are authored at launch; they must reference real repo state"), and does not exist yet. The interface freeze itself will be enforced by S-02's frozen `contract/critique-contract.schema.json` plus the halt-on-post-P1-change policy; neither exists yet in this pre-scaffold repository.
