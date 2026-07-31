# 0005 - Licensing: Apache-2.0 repo, CC-BY-4.0 bench corpus

## TL;DR
- **Decision:** License the repository Apache-2.0, and license the bench corpus specifically CC-BY-4.0.
- **Why:** Matches the license already shipped by the other two libraries in the family, `pm-skills` and `thinking-framework-skills`, and separates code licensing from the benchmark corpus's generated-content licensing.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

A public GitHub repository needs an explicit license before it can be marketplace-listed under the `agent-plugins` listing contract. critique-skills additionally ships a generated benchmark corpus (`bench/corpus/`, per S-03, the bench-harness spec) whose artifacts are original generated content, not code, which conventionally carries a separate content license from the surrounding codebase.

## Decision drivers

- Consistency with the two sibling family libraries: both `pm-skills` and `thinking-framework-skills` are verified Apache-2.0 (`01-strategy-brief.md` evidence map, verified 2026-07-31).
- Apache-2.0's explicit patent grant fits a library other agents and plugins are meant to depend on and potentially fork.
- CC-BY-4.0 is the standard choice for openly reusable generated content that only requires attribution, matching the stated goal that skeptical external readers be able to reproduce and cite the corpus and its results.

## Considered options

1. **A different code license** (for example MIT, or a copyleft license). Not pursued: nothing in the planning session favored diverging from family precedent, and matching the two sibling libraries reduces the cognitive load for anyone evaluating the family as a whole.
2. **Apache-2.0 for code, CC-BY-4.0 for the corpus (chosen)**, matching `pm-skills` and `thinking-framework-skills`' Apache-2.0 licensing and the standard open-content license for generated benchmark artifacts.

## Decision outcome

Option 2, verified directly against both sibling repositories' `LICENSE` files during the strategy brief's evidence pass (`01-strategy-brief.md` section 6, "Family license precedent").

## Consequences

**Positive:** no license-shopping decision to defend later; the corpus's attribution-only reuse terms match the stated goal of letting skeptical external readers reproduce the results tables.

**Negative:** none identified specific to this choice, beyond the standard obligations either license carries.

**Neutral:** the CC-BY-4.0 notice has to appear specifically in `bench/README.md` (S-03 AC-7), not only in a root `LICENSE` file, since it governs a different class of content (generated corpus artifacts) than the code the root license covers.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per S-01 (repo scaffold spec) requirements and S-03 (bench-harness spec) scope and AC-7, this decision will be enforced at:

- `LICENSE` (repository root) - Apache-2.0 full text.
- `bench/README.md` - the CC-BY-4.0 notice covering the corpus specifically.
