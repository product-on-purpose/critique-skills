# 0024 - Tier backfill: Convergent, because the critic subagent is a Convergent-tier component

## TL;DR
- **Decision:** `library.json`'s `tier` field is `"convergent"` (Silver), not `"universal"` (Bronze), as of the P2 phase commit that registered `agents/critique-critic.md` under `components.subagents`. This ADR is a backfill: it records, after the fact, a tier bump the P2 integrator already made in the manifest without an accompanying decision record.
- **Why:** Standard sec 2.1 (Tier 1, Universal/Bronze) lists exactly three eligible component families at Universal, agentskills.io skills, `AGENTS.md`, and MCP server definitions, and subagents are not among them. Standard sec 2.5's tier-requirements table places subagents in Silver's "Components allowed" row ("+ subagents, commands, workflows, plugin packaging, chain contracts"), not Bronze's. `critique-critic` is a subagent, so once `library.json` registers it, declaring `tier: universal` is not an option the Standard leaves open; `tier: convergent` is the only honest declaration.
- **Status:** Accepted (2026-07-31, backfill; the underlying manifest change was made 2026-07-31 during P2, commit `e88bcd8`).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, P3 integration pass (Claude)

## Builds on

- [0010 - Universal tier launch, Silver pre-wired](0010-universal-tier-launch-silver-prewired.md), which declared `tier: universal` for v0.1.0 while deliberately pre-wiring the `prefix` and `components` fields "so the eventual Silver climb...adds fields and passes new checks rather than renaming components or restructuring." This ADR is that anticipated climb, exercised earlier than 0010 expected (0010 pointed the roadmap's Silver work at v0.3.0), because the critic subagent shipped in the same phase (P2), not a later one.

## Context and problem statement

[P2 slate audit report](../execution/P2-report.md) records, in its GATE row, that the gate's declared-tier line moved from `Tier: Universal` (per the P1 report) to `Tier: Convergent` during P2, because `library.json`'s `components.skills` and `components.subagents` were populated for the first time in that phase, including one subagent, `critique-critic` (`agents/critique-critic.md`, registered per S06-AC1). The same report's Deviations section calls this "expected, not a defect" and explicitly recommends closing the gap: "record an ADR accepting Convergent as the v0.1.0 target tier so this stops appearing as an open item every audit." No such ADR was written at P2 time; `library.json`'s `tier` field simply changed from `"universal"` to `"convergent"` inside the same commit (`e88bcd8`) that added the `components` entries, with no decision record explaining why that specific value, as opposed to some other tier, was now correct. This ADR is that missing record, written retroactively against the manifest state and the P2 report as they already exist.

## Decision drivers

- **Standard sec 2.1 does not list subagents as a Universal-tier component.** The Universal (Bronze) component list is exactly agentskills.io skills (`SKILL.md` + `references/`, `scripts/`, `assets/`), `AGENTS.md`, and MCP server definitions. A subagent is not on that list under any reading.
- **Standard sec 2.5's "Tier requirements (concrete)" table settles it explicitly.** The "Components allowed" row reads: Bronze = "agentskills.io skills + references/assets, AGENTS.md, MCP"; Silver = "+ subagents, commands, workflows, plugin packaging, chain contracts". Subagents are a named Silver-tier addition, not a Bronze-tier component under a different name.
- **`library.json` already carries the subagent at `tier: "convergent"` in its own component entry** (`components.subagents[0].tier`), per the P2 report's S06-AC1 row. A plugin-level `tier: "universal"` alongside a registered `tier: "convergent"` component entry would be an internally inconsistent manifest, and per Standard sec 2.4 ("Tooling MUST be able to verify a claimed tier and MUST report the highest tier a plugin actually satisfies"), a `universal` claim while shipping a Silver-only component is exactly the false conformance claim [0010](0010-universal-tier-launch-silver-prewired.md) committed to never making ("the tier claim in `library.json` is never false").
- **Standard sec 5.1 confirms the manifest fields this bump requires are already present.** `agent-targets`, `prefix`, and a populated `components` index are REQUIRED at Convergent+; `library.json` already declares all three (`agent-targets: ["claude"]`, `prefix: "critique-"`, populated `components.skills`/`components.subagents`), so the bump needed no new fields, only the declaration to catch up to what was already there.
- **The P2 report already treats this as a tier advance, not a regression**, and the gate confirms it gate-passes at the new declared tier with zero errors and zero warnings counting toward the exit code (re-verified directly for this ADR: `node scripts/check.mjs` reports "Tier: Convergent... 0 error(s), 0 warning(s)" as of this commit).

## Considered options

1. **Revert `library.json` to `tier: universal` and unregister or hold the critic subagent.** Rejected. The subagent is built, gate-conformant, and required by [S-06 (critic subagent)](../release-plans/plan_v0.1.0/S-06_critic-subagent/spec.md) for v0.1.0; there is no defect in it to justify pulling it, and doing so purely to preserve a lower tier claim would be optimizing the declared tier over the actual deliverable, the opposite of what [0010](0010-universal-tier-launch-silver-prewired.md) was written to prevent.
2. **Leave the tier bump undocumented, relying on the P2 report's Deviations narrative as the explanation.** Rejected. An audit report documents what happened; it is not a decision record accepting a tier claim going forward, and the P2 report itself names this exact gap as an open item for a later phase to close, not as already closed.
3. **Backfill an ADR now, accepted, citing Standard sec 2.1/2.5 as the reason the bump is not discretionary, and recording it as superseding [0010](0010-universal-tier-launch-silver-prewired.md)'s Universal-launch clause in the direction that ADR itself welcomed (chosen).**

## Decision outcome

Option 3. `library.json`'s `tier: "convergent"` stands as already declared. This ADR **supersedes [0010 - Universal tier launch, Silver pre-wired](0010-universal-tier-launch-silver-prewired.md)'s launch-tier clause** ("Launch v0.1.0 at Universal (Bronze) tier conformance"), in the good direction: 0010's own "Consequences" section named the Silver climb as additive by design ("adds fields and passes new checks rather than renaming components or restructuring"), and that is exactly what happened here. Nothing in 0010's reasoning was wrong; its stated tier value for v0.1.0 is simply overtaken by this phase shipping a Convergent-tier component earlier than 0010's roadmap reference (v0.3.0) anticipated. 0010's decision to pre-wire `prefix` and `components` remains in force, unedited, and is the reason this bump required a manifest-field declaration change and nothing else.

## Consequences

**Positive:** the declared tier now matches shipped reality, closing the gap the P2 report flagged as an open item. No renaming or restructuring was required to make the climb, exactly as [0010](0010-universal-tier-launch-silver-prewired.md) predicted when it pre-wired `prefix` and `components`. The gate's own tier-satisfaction report (`Tier: Convergent`, zero errors, zero warnings) is now backed by a decision record, not just a manifest edit.

**Negative:** none specific to this choice; the alternative (misdeclaring `universal`) would have been a conformance-honesty defect, not a cost avoided. Convergent tier does carry higher standing requirements (declared `agent-targets`, per-target emission for Convergent components, chain-contract declarations where chaining is used) than Universal, but `library.json` already satisfies the ones that apply here.

**Neutral:** this ADR settles only the Bronze-vs-Silver question [0010](0010-universal-tier-launch-silver-prewired.md) left as a phased climb; it does not decide whether v0.1.0 pursues Gold (Advanced) tier. The gate's 21 Gold-tier informational findings (`INDEX.md`, folder-`README.md` coverage, an architecture-overview/detailed doc pair) remain open items regardless of this ADR, as the P2 report's own "Open items for P2" section already recorded.

## Implementation sites

- [`library.json`](../../../library.json) - `tier: "convergent"` (already declared; this ADR backfills the record, it does not change the value), `components.subagents[0]` (`critique-critic`, `tier: "convergent"`, already declared).
- [P2 slate audit report](../execution/P2-report.md) - GATE row and Deviations section, cited above as the evidentiary basis for this ADR; not edited by this ADR.
- [0010 - Universal tier launch, Silver pre-wired](0010-universal-tier-launch-silver-prewired.md) - the ADR this one supersedes on the launch-tier clause specifically; left as written, since it remains an accurate record of the P0-era decision and its own reasoning is what this bump fulfills, not contradicts.
