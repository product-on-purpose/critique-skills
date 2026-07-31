# 0004 - Plugin surface: skills plus critic subagent

## TL;DR
- **Decision:** The v0.1.0 plugin surface is the six domain skills plus one clean-context critic subagent (`agents/critique-critic.md`); slash commands are explicitly deferred.
- **Why:** The methodology requires critique to happen in a clean context, uninfluenced by the artifact's author. A subagent is the mechanism Claude Code provides for that isolation; commands would add a second invocation surface before the primary one is proven.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

The methodology draft mandates clean-context critique (S-06, critic-subagent spec, section 7 of the methodology): a critique must not inherit the requester's framing, drafts, or stated opinions about the artifact, because a critic that has already absorbed the author's self-assessment is compromised before it starts. Claude Code plugins can expose functionality through skills (triggered by description match, running inline in the host session's existing context), subagents (isolated context, invoked by the host), and slash commands (explicit user invocation). The decision was which of these carry the v0.1.0 surface.

## Decision drivers

- The clean-context requirement is not satisfiable by a skill running inline in the host session, which by definition shares whatever context the user already supplied.
- Claude Code subagents get an isolated context by construction, which is exactly the mechanism the methodology's clean-context mandate needs.
- Slash commands add discoverability but also add a second surface to design, document, and keep in sync with the skills, before the primary skill-plus-subagent surface has any real usage to validate it against.

## Considered options

1. **Skills only, no dedicated clean-context mechanism.** This is the baseline alternative implicit in the decision: build the six skills and rely on their instructions alone to maintain objectivity. Not pursued: it does not satisfy the methodology's clean-context mandate, since a skill invoked mid-conversation inherits whatever framing the user already supplied, and a written instruction not to be influenced is not a structural guarantee.
2. **Skills plus critic subagent, slash commands deferred (chosen).** Six skills carry the domain expertise (rubrics, criterion IDs, lane logic). One subagent, `critique-critic`, implements clean-context execution by receiving only an artifact path, a skill name, and an optional gate threshold, and it refuses inputs that embed authorial framing beyond the artifact itself.
3. **Skills plus critic subagent plus slash commands.** The decisions log records slash commands as explicitly deferred, meaning this fuller surface was named and set aside, not simply unconsidered. Not pursued for v0.1.0: it adds a third invocation surface, its own trigger design, and its own conformance surface, before the primary two are validated by real usage.

## Decision outcome

Option 2. Each of the six `SKILL.md` files instructs delegation to `critique-critic` where subagents are available, with an inline fallback protocol documented for hosts where they are not (S-06 AC-5).

## Consequences

**Positive:** the clean-context guarantee is structural, Claude Code's subagent context isolation, rather than a written instruction a skill might not hold to under context pressure. The subagent never edits the artifact (no auto-fix, per methodology section 10) and is tool-restricted to read and execute only, which is independently verifiable (S-06 AC-4).

**Negative:** two components must be kept in sync, six `SKILL.md` protocols and one subagent's execution logic, instead of one. The subagent's own description must be discoverable to Claude Code's delegation heuristics without depending on its name carrying special meaning (S-06 requirement).

**Neutral:** deferring slash commands is a scope choice, not a rejection of the idea; it is a natural addition once the skill-and-subagent surface has real usage to design commands around.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per S-06 (critic-subagent spec) AC-1, this decision will be enforced at:

- `agents/critique-critic.md` - the subagent definition, registered in `library.json` components.
- `skills/critique-usability/SKILL.md`, `skills/critique-accessibility/SKILL.md`, `skills/critique-clarity/SKILL.md`, `skills/critique-docs/SKILL.md`, `skills/critique-microcopy/SKILL.md`, `skills/critique-argument/SKILL.md` - each carries the delegation instruction to `critique-critic` (S-06 AC-5).
