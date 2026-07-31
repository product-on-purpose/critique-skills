# 0008 - Fully autonomous build to RC

## TL;DR
- **Decision:** Run the v0.1.0 build as one fully autonomous, phase-sequenced agent workflow with zero user involvement until the release-candidate handover. All work happens on branch `build/v0.1.0` with commits at phase boundaries, and the run itself never pushes, tags, or opens a PR.
- **Why:** Jonathan requested a long-form autonomous agentic development run. The design compensates for concentrating all human judgment into one final review with phase-boundary commits, an ADR for every in-run decision, and a halt-on-second-failure policy instead of quietly working around problems.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

Building six skill pipelines, a shared contract, a benchmark harness, CI, and documentation to a releasable state is a large, mostly mechanical, multi-agent task. The alternative to full autonomy is a staged model with human review at each phase boundary, catching problems as they happen rather than only at the end. Full autonomy was the mode requested: `workflow/workflow-design.md` records its authorization basis as "Jonathan requested a long-form autonomous agentic development run." The strategy brief names the resulting tradeoff honestly, not as a free choice: "Full autonomy to RC concentrates all human judgment into one review at the end" (`01-strategy-brief.md`, "Concerns worth naming").

## Decision drivers

- The explicit user request for a long-form autonomous run.
- The practical cost of staged human review across phases P0 through P5, an estimated six checkpoints across 60 to 85 agents, against a single-review model.
- The availability of compensating mechanisms, phase self-audit agents, ADRs, and a run journal, that can substitute for live human oversight without eliminating the concentration-of-judgment risk the strategy brief names.

## Considered options

1. **Fully autonomous to a single RC review (chosen).** One orchestrated run, phase-sequenced (P0 through P5); the orchestrator reads each phase's structured self-audit result and refuses to open the next phase on any failing exit criterion, but no human reviews any phase until `rc-handover.md` exists.
2. **Staged, human-reviewed checkpoints at each phase boundary.** The natural alternative implied by the strategy brief's own framing of the concentration-of-judgment risk. Not chosen: it was not the mode requested, and the compensating mechanisms actually adopted, phase-boundary commits an owner can audit after the fact, ADRs recording every in-run decision, and a run journal under `docs/internal/execution/`, exist specifically so a post-hoc audit trail is available even without live checkpoints.

A related sub-decision, explicit in the workflow design's failure policy, governs how the run behaves when something goes wrong mid-phase:

3. **Ship-around behavior:** quietly work around a failure, for example shipping a core skill that failed baseline without flagging it, so the run always produces something. Rejected, per `workflow-design.md`'s failure policy, which names this alternative directly only to reject it.
4. **Halt-on-second-failure (chosen, folded into this ADR).** An agent-level failure retries once, one tier up; a core-skill baseline failure gets exactly one calibration iteration; a second failure at any interface or measurement level halts the run and produces `rc-handover.md` in failed-run form (what completed, what halted, diagnosis, options), rather than a silently degraded release.

## Decision outcome

Option 1 for the overall autonomy model, with option 4 (halt-on-second-failure) as its explicit failure-handling companion. The publish boundary is a hard constraint, not a preference: the run never pushes, tags, opens PRs, or touches `main` or any other repository; `agent-plugins` is read-only to the run. The only writes the run makes outside `build/v0.1.0`-scoped work are `rc-handover.md` and `marketplace-listing-pr.md`, both staged for Jonathan's own action.

## Consequences

**Positive:** a single, well-prepared review point (the RC handover) is efficient and matches the request. The compensating mechanisms make the run auditable after the fact even without live checkpoints, which the strategy brief names as the residual risk worth naming rather than hiding. A halted run is explicitly "a delivered artifact, not a silent death" (`workflow-design.md`), so a failure is informative rather than wasted effort.

**Negative:** real problems in early phases, for example a flawed contract design at P1, are not caught until P3 measurement or later, by which point six skill pipelines have already built against it. Taste drift in prose-heavy artifacts (docs, README) is named as a residual risk; the strategy brief's own 80/20 recommendation is to review those first at RC precisely because nobody caught them in real time.

**Neutral:** the branch and commit discipline (`build/v0.1.0`, commits at named phase boundaries, the session-trailer convention) exists specifically to make the single eventual review tractable, not to substitute for it.

## Implementation sites

Not yet created; the scaffold-builder creates branch `build/v0.1.0` as part of phase P0 (S-01, repo-scaffold spec), which is a separate task from this ADR-authoring work. The failure and halt policy is documented now, at `workflow/workflow-design.md` (Failure and halt policy section, currently at `_local/initial-plan/workflow/workflow-design.md`); that document exists as of this ADR's date. Its enforcement, the concrete Workflow orchestration script authored at launch, does not exist yet. `rc-handover.md` (release-plan RC-definition item 5) is written at phase P5 and does not exist yet.
