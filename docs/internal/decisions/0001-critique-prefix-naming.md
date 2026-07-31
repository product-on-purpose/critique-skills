# 0001 - Critique- prefix naming

## TL;DR
- **Decision:** Every critique-skills component is named with a `critique-` prefix (`critique-usability`, not `usability-critique`), declared as `prefix: "critique-"` in `library.json` from v0.1.0, even though the family Standard's naming check (S2) only requires a declared prefix starting at Silver tier.
- **Why:** It keeps the future Silver and Gold conformance climb a checklist item instead of a rename, at zero present cost, and it matches the naming pattern the other two libraries in the family already ship.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

The family Standard's component-naming check (S2) requires a declared prefix on every component only from Silver tier upward; at Universal (Bronze) tier, where critique-skills is launching v0.1.0 (see [0010 - Universal tier launch, Silver pre-wired](0010-universal-tier-launch-silver-prewired.md)), a plugin may ship components with no prefix at all. So the prefix is not required for v0.1.0's own conformance gate. But six skills, one subagent, and a shared bench and contract surface are about to be named once, and then referenced permanently: skill directory paths, `SKILL.md` frontmatter, the agent file `agents/critique-critic.md`, and every cross-reference from docs, CI scripts, and eventually external consumers all bake the chosen name in. A name picked for Bronze-tier convenience and changed later, at the Silver climb, touches every one of those surfaces at once.

## Decision drivers

- Standard check S2 compliance path at Silver tier and above.
- Avoiding a disruptive rename at the Silver climb (roadmap v0.3.0).
- Consistency with sibling libraries' already-shipped naming: `thinking-framework-skills` uses `think-`, and `agent-skills-toolkit`'s own naming ADR (0020, skill packaging and naming) established `askit-` for exactly the same collision-avoidance reason.
- The cost of declaring the prefix now is zero, because no components exist yet in this pre-scaffold repository.

## Considered options

1. **Defer prefixing until Silver tier requires it.** Ship v0.1.0 skills unprefixed, or in a verb-suffix form such as `usability-critique`, and add the `critique-` prefix later once check S2 gates it. Rejected: this guarantees a rename of every skill directory, `SKILL.md` frontmatter, agent file, and any external reference the moment the library climbs to Silver, for a decision that costs nothing to make correctly now.
2. **Prefix now, declared in `library.json` from v0.1.0 (chosen).** `critique-usability`, `critique-accessibility`, `critique-clarity`, `critique-docs`, `critique-microcopy`, `critique-argument`, and `critique-critic` (the subagent). No rename is ever required.

A second, narrower question was the naming order itself: `critique-usability` (prefix-first) versus `usability-critique` (prefix-last, verb-suffix style). The decisions log records the prefix-first form as the chosen pattern; the verb-suffix form was the rejected alternative on this axis.

## Decision outcome

Option 2. The prefix carries no triggering weight, by design: per `03-documentation-plan.md`, "the `critique-` prefix carries zero triggering weight by design (family ADR 0020 precedent)." Triggering must come entirely from the `SKILL.md` description's named artifact types and everyday phrasings, not from the name. The prefix's sole job is collision avoidance and Standard conformance, the same role ADR 0020 assigned `askit-`.

## Consequences

**Positive:** the Silver and Gold conformance climb (roadmap v0.3.0) needs zero renames; naming stays consistent and guessable across the family (`think-`, `askit-`, `critique-`); this avoids the exact retrofit pain ADR 0020 records, where two already-shipped subagents had to be renamed after the fact to add a missing prefix.

**Negative:** none material. The longest resulting name, `critique-accessibility`, stays comfortably within the 64-character `agentskills.io` name limit.

**Neutral:** names still have to independently earn triggering strength through their descriptions; this decision has no bearing on that separate risk, which is the S-05 skills-slate effort's problem to solve.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per the S-01 (repo scaffold and family conformance spec) acceptance criteria, this decision will be enforced at:

- `library.json` - the `prefix: "critique-"` field and the `components` array (S-01 AC-2).
- `skills/critique-usability/`, `skills/critique-accessibility/`, `skills/critique-clarity/`, `skills/critique-docs/`, `skills/critique-microcopy/`, `skills/critique-argument/` - the six skill directory names (S-05, skills-slate spec).
- `agents/critique-critic.md` - the subagent file name (S-06, critic-subagent spec, AC-1).

None of these paths exist yet; they are created during the build run's P0 and P2 phases.
