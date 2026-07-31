# 0006 - Copyright posture: paraphrase policy retained

## TL;DR
- **Decision:** Retain the paraphrase policy for every rubric source: book-sourced and standard-derived criteria (Nielsen, Williams, Toulmin, NN/g, alongside the genuinely open standards WCAG and Diataxis) are operationalized in the library's own words, never reproduced verbatim, with short anchor quotes permitted only in references, for orientation, never as the criterion text itself.
- **Why:** The user accepts the residual copyright risk, but the paraphrased operationalization is not a workaround around that risk, it is the product itself, and the repository is public.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

Several of the six skills' rubric sources are copyrighted works, not open standards: Nielsen's ten usability heuristics and severity ratings, Williams' *Style: Lessons in Clarity and Grace*, the Toulmin model of argumentation, and NN/g's error-message guidelines. WCAG and Diataxis are open standards and do not raise this question; their upstream criterion identifiers are adopted directly (S-02, the critique-contract spec). The decision was how the library operationalizes the copyrighted rubrics into machine-checkable criteria without reproducing the source text, and whether that constraint is worth keeping given the repository is public and will be read by people, potentially including the rights holders themselves.

## Decision drivers

- Legal exposure of a public repository quoting or closely paraphrasing copyrighted rubric text at length.
- The library's actual differentiator, per the strategy brief, is that its rubrics are operationalized: broken into permanent criterion IDs, each with a paraphrased test a finding must satisfy. That operationalization is transformative work distinct from the source text, not a reproduction of it.
- Every book-sourced rubric's `rubric_sources` block already requires ISBN and page or chapter citation (S-05, skills-slate spec, Non-Functional Requirements), so provenance is preserved even without verbatim text.

## Considered options

1. **License or seek permission for verbatim rubric reproduction.** Not pursued: out of scope for an autonomous build run with no publisher relationship in place, and unnecessary given that the operationalized-paraphrase approach is the actual product, not a substitute for one.
2. **Retain the paraphrase policy (chosen).** Every criterion is the library's own operationalization of the source idea, cited by source and page range, with short anchor quotes permitted only in references, for orientation.

## Decision outcome

Option 2. This is a continuation of an existing policy, not a newly originated one; the decisions log records it as "retained," meaning the planning session revisited and reaffirmed it rather than inventing it from scratch.

## Consequences

**Positive:** the library's intellectual-property posture is defensible (transformative operationalization, not reproduction) and consistent across all six skills. The S-04 skill-template's self-test enforces the policy structurally, rather than relying on each skill pipeline to remember it independently (S-05 Non-Functional Requirements: "Paraphrase policy D6 enforced by the S-04 self-test").

**Negative:** residual copyright risk is explicitly accepted, not eliminated, by the user. Paraphrasing well enough to be both legally safe and operationally precise is genuine authoring work, repeated across every book-sourced criterion.

**Neutral:** open-standard sources (WCAG, Diataxis) carry no such risk and use upstream criterion numbers directly, so this policy's real cost concentrates in the book-sourced skills: `critique-usability`, `critique-clarity`, `critique-argument`, and `critique-microcopy`.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per S-05 (skills-slate spec) requirements and Non-Functional Requirements, this decision will be enforced at:

- `skills/critique-*/references/` - one file per rubric source, paraphrased criterion tables with ISBN or standard citation, for each of the six skills.
- The S-04 skill-template's self-test runner, which checks the paraphrase policy structurally (S-04, skill-template spec; the self-test's exact mechanism is that effort's own scope, not detailed further here).
