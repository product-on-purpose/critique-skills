# 0010 - Universal tier launch, Silver pre-wired

## TL;DR
- **Decision:** Launch v0.1.0 at Universal (Bronze) tier conformance, while already declaring the Silver-tier `prefix` and `components` fields in `library.json` from day one.
- **Why:** Universal tier honestly matches what v0.1.0 actually ships (no per-target manifests, no chain or hook eval coverage yet), while pre-wiring the two Silver fields that the naming decision already commits to costs nothing now and turns the eventual Silver climb into a checklist rather than a refactor.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Builds on

- [0001 - Critique- prefix naming](0001-critique-prefix-naming.md), which already commits to declaring `prefix` and a `components` inventory in `library.json` from v0.1.0.

## Context and problem statement

The family Standard defines conformance tiers (Universal or Bronze, up through Convergent or Silver, and Gold) with increasing requirements. Full Silver conformance, per-target manifests, `agent-targets`, and the full S1 through S8 check set, is real scope the roadmap explicitly places at v0.3.0, not v0.1.0 (S-01, repo-scaffold spec, Non-Goals: "Silver-tier conformance (roadmap v0.3)"). The decision was which tier v0.1.0 declares itself at, and whether to declare any Silver-only fields early even though they are not yet required.

## Decision drivers

- Honesty of the declared tier: claiming Silver without the underlying S1 through S8 work would be a false conformance claim.
- [0001 - Critique- prefix naming](0001-critique-prefix-naming.md) already commits to declaring `prefix` and a `components` inventory in `library.json` from v0.1.0, and those happen to be two of the fields Silver tier requires.
- The roadmap's v0.3.0 wave is explicitly scoped as "a checklist climb" (`02-roadmap.md`), a claim that only holds if nothing needs renaming or restructuring to get there.

## Considered options

1. **Launch directly at Silver tier.** Not viable for v0.1.0: it would require `agent-targets`, per-target manifests, and the rest of S1 through S8 conformance work that S-01's own Non-Goals place explicitly at roadmap v0.3.0, not in this plan suite; claiming Silver now would be a tier claim the repository could not back with real conformance work.
2. **Launch at Universal tier, declaring only the fields Universal strictly requires** (`name`, `version`, `description`, `standard`, `tier`), leaving `prefix` and `components` undeclared until Silver actually requires them. Not pursued: this is the same rename-cliff problem [0001 - Critique- prefix naming](0001-critique-prefix-naming.md) already rejected at the naming level. Since that decision already commits to declaring `prefix` and `components` early, declining to declare them in the same manifest that carries the `tier` field would be inconsistent with it, not a real cost saved.
3. **Universal tier, with `prefix` and `components` pre-wired from v0.1.0 (chosen).** Matches [0001 - Critique- prefix naming](0001-critique-prefix-naming.md) exactly and treats the Silver climb as adding new required fields and new checks to an already-consistent manifest, not restructuring an existing one.

## Decision outcome

Option 3. v0.1.0 declares `tier: universal` honestly, while `library.json` already carries `prefix: "critique-"` and a full `components` inventory, so roadmap v0.3.0's Silver climb (`agent-targets`, per-target manifests, full S1 through S8 green) is purely additive.

## Consequences

**Positive:** the tier claim in `library.json` is never false. The Silver climb, when it happens, adds fields and passes new checks rather than renaming components or restructuring the manifest that already exists, which directly delivers on [0001 - Critique- prefix naming](0001-critique-prefix-naming.md)'s stated purpose of keeping the Silver and Gold path open with no rename.

**Negative:** none specific to this choice; the Standard permits optional early declaration of higher-tier fields at a lower declared tier, so there is no conformance cost to declaring them early.

**Neutral:** the marketplace listing itself only requires L1 through L4 of the listing contract at launch (`01-strategy-brief.md` section 4), a separate and lower bar than either conformance tier, so this tier decision does not by itself determine what the marketplace listing requires.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per S-01 (repo-scaffold spec) AC-2, this decision will be enforced at:

- `library.json` - `tier: "universal"`, `prefix: "critique-"`, and a `components` array (empty allowed at phase P0).

The roadmap's Silver-tier climb items (`agent-targets`, per-target manifests, full S1 through S8 checks) are listed in `02-roadmap.md`'s v0.3.0 section and are out of scope for this ADR's own implementation.
