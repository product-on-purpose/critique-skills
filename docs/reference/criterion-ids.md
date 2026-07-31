---
title: Criterion IDs
description: The permanent identifier grammar, its permanence rules, and the namespace registry
audience: engineer
level: intermediate
---

# Criterion IDs

A criterion ID is the permanent handle a finding cites against: `finding.criterion`, typed as `$defs/criterionId` in [`contract/critique-contract.schema.json`](../../contract/critique-contract.schema.json). IDs are what turn a critique into a countable, diffable event instead of a paragraph of opinion: they let a finding be compared across runs, aggregated across artifacts, and pruned by the acceptance-rate signal the disposition log produces.

## Grammar

The exact pattern the schema and validator enforce on `finding.criterion`:

```
^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+(?:\.[A-Z0-9]+)*)+(?![\s\S])
```

Read as `SOURCE-CRITERION`:

- **`SOURCE`**, the namespace: an uppercase letter followed by uppercase letters or digits, no hyphen inside it.
- **`CRITERION`**: one or more hyphen-separated segments, each uppercase letters or digits, and each of those segments may itself carry dot-separated parts so an upstream numbering scheme (WCAG's `1.4.3`) survives verbatim rather than being re-encoded.
- The trailing `(?![\s\S])` is an end-of-input assertion, used in place of `$` throughout the contract. Python's `re` module treats `$` as matching just before a trailing newline, so a value with a stray trailing newline would pass a `$`-anchored check in the Python validator while failing an ECMA-262 one; the lookahead form behaves the same in both.

Maximum length 64 characters. Accepted: `NNG-H4`, `WCAG-1.4.3`, `PLAIN-ACTIVE`, `TOULMIN-WARRANT`, `BYOR-BRAND-VOICE`. Rejected: `nng-h4` (lowercase), `WCAG` (no criterion segment), `WCAG-` (empty segment), `-H4` (missing source), `WCAG_1` (underscore is not in the alphabet).

A criterion's namespace, used in `run.rubrics`, is the text before its first hyphen, matched by `$defs/rubricNamespace`:

```
^[A-Z][A-Z0-9]*(?![\s\S])
```

`WCAG-1.4.3` has namespace `WCAG`. Every finding's namespace must appear in its own run's `rubrics` array; the schema cannot check that cross-reference on its own, so the validator enforces it separately.

That cross-reference imposes a bound the criterion grammar does not state: **a namespace is at most 32 characters**, because `rubricNamespace` caps `run.rubrics` entries there while `criterionId` caps the whole ID at 64. A criterion such as a 40-character source followed by `-X` is well formed on its own and can never appear in a valid envelope, since the namespace it needs listed cannot be listed. The two limits are left as they are rather than reconciled, because narrowing a published pattern is a major contract version and nothing real is anywhere near either limit; the practical rule is that a source abbreviation is short, and 32 characters is the ceiling that actually binds.

## Permanence rules

1. **IDs are permanent.** Once an ID is published, it is never reassigned to a different criterion, even across major skill or contract versions.
2. **Deprecate, never delete.** A criterion the library stops checking is marked deprecated in its skill's registry. Its ID stays reserved so a finding or a disposition log written against it years ago still resolves.
3. **Adopt upstream IDs where they exist.** WCAG publishes its own success-criterion numbers, so `critique-accessibility` uses them directly (`WCAG-1.4.3`) rather than inventing a parallel scheme. A source without its own numbering gets one invented for it (`PLAIN-ACTIVE`, `NNG-H4`).
4. **One criterion, one ID.** A rubric item that actually bundles two independently checkable things is split into two IDs before it ships, not merged into one.

## Namespace registry

The namespace each launch skill draws its criterion IDs from, per [S-05 (skills slate)](../internal/release-plans/plan_v0.1.0/S-05_skills-slate/spec.md):

| Skill | Status | Namespace(s) | Rubric source |
|---|---|---|---|
| critique-clarity | core | `PLAIN`, `WILLIAMS` | US Federal Plain Language Guidelines (open standard); Williams, *Style: Lessons in Clarity and Grace* (paraphrased) |
| critique-accessibility | core | `WCAG` | WCAG 2.2 AA (open standard, upstream IDs) |
| critique-usability | core | `NNG` | Nielsen's 10 usability heuristics (paraphrased) |
| critique-docs | stretch | `DIATAXIS` | Diataxis (open standard) |
| critique-microcopy | stretch | `NNG` | NN/g error-message guidelines (paraphrased) |
| critique-argument | stretch | `TOULMIN` | Toulmin model (paraphrased) |
| BYOR | opt-in, any skill | `BYOR` | Rubric supplied by the requester at run time |

Two notes on this table:

- **`NNG` is shared by two skills on purpose.** critique-usability's Nielsen heuristics (`NNG-H1` through `NNG-H10`) and critique-microcopy's NN/g error-message guidelines (`NNG-EM-*`) are different, unrelated rubrics that both trace to the Nielsen Norman Group, so they share a source letter. No individual ID is reused: `NNG-H4` and `NNG-EM-CONSTRUCTIVE` never collide. A reader who wants to know which of the two rubrics a run actually drew on has to look at the full criterion IDs, not just `run.rubrics`, since the namespace array records the same string `NNG` either way.
- **`PLAIN` and `WILLIAMS` stay separate, and two criterion pairs merged.** S-05 (skills slate) OQ-1 left open whether `WILLIAMS-*` criteria fold into `PLAIN-*` so clarity's registry stays single-sourced. The critique-clarity pipeline resolved it in [ADR 0019 (clarity: two namespaces, merged duplicate criteria)](../internal/decisions/0019-clarity-two-namespaces-merged-duplicate-criteria.md): both namespaces ship, because six of Williams' criteria have no PLAIN equivalent and renaming them would misattribute them to an open standard that never stated them; the two pairs that tested the identical construction across both sources merged into one ID each, `PLAIN-NOMINALIZATION` and `PLAIN-CONCISE`, so no finding can double-cite one flaw. `WILLIAMS-NOMINALIZATION` and `WILLIAMS-CONCISION` were never published and are not reserved. The table above already reflects the outcome.

`BYOR-*` is a reserved namespace, not a skill: any skill running against a user-supplied rubric marks every resulting finding `rubric_source: byor`, which the schema forces whenever `criterion` matches `^BYOR-`.

## See also

- [Critique contract](critique-contract.md), the finding schema `criterion` sits inside.
- [Severity scale](severity-scale.md), the scale every criterion is judged against.
- [Methodology, section 4](../explanation/methodology.md#4-criterion-identifiers), why permanent IDs are the library's load-bearing mechanism.
