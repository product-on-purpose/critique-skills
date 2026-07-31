# 0017 - critique-argument lane split: the scripted assists are their own criteria

## TL;DR
- **Decision:** `critique-argument`'s registry carries **eight** criteria, not six. Toulmin's six elements (`TOULMIN-CLAIM`, `TOULMIN-GROUNDS`, `TOULMIN-WARRANT`, `TOULMIN-BACKING`, `TOULMIN-QUALIFIER`, `TOULMIN-REBUTTAL`) are all **judged**. The two scripted assists [S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) names for this skill get their own permanent IDs, `TOULMIN-CLAIM-MARKER` and `TOULMIN-HEDGE-DENSITY`, and are the entire **scripted** lane. Both stay in the `TOULMIN` namespace. Neither is a proxy for the element criterion beside it, and the registry says so explicitly.
- **Why:** the skill template forbids a criterion appearing in both lanes, and folding a surface signal into an element criterion would make a determinism claim the library cannot back: the presence of the word *therefore* is not the adequacy of a conclusion. Splitting is what [criterion-ids.md](../../reference/criterion-ids.md)'s permanence rule 4 already requires of a rubric item bundling two independently checkable things.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P2 `critique-argument` pipeline (Claude)

## Context and problem statement

[S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) specifies this skill in two places that do not obviously fit together.

Its slate table gives the expected lane balance as judged-heavy with scripted assists, and names those assists exactly: claim-marker detection and hedging density. Its AC-2 gives the registry floor as `argument >=6 (claim, grounds, warrant, backing, qualifier, rebuttal)`, which is Toulmin's six-part schema and nothing else.

Every one of those six is judged. Deciding whether a passage is the argument's claim, whether a passage supports a claim or restates it, whether an unstated principle is common ground for this audience: each needs the argument read whole, which is the definition the skill template's "Scripted lane discipline" gives for the judged lane. So AC-2's six criteria produce a skill with an empty scripted lane, while the slate table promises two scripted checks that AC-2 does not name. The two scripted assists have to live somewhere, and where they live is a decision with consequences for `checks.py`, the bench corpus module, and how P3 reads this skill's recall numbers.

Three constraints bound the answer, all of them already binding before this ADR:

- The template's lane manifest rule: **no criterion ID appears in both `checks.scripted` and `checks.judged`**, enforced by `scripts/skill-selftest.py`'s `lane-overlap`. A criterion that is sometimes one lane and sometimes the other is two criteria.
- [criterion-ids.md](../../reference/criterion-ids.md) permanence rule 4, one criterion one ID: a rubric item that bundles two independently checkable things is split into two IDs before it ships.
- The namespace registry in the same document assigns `critique-argument` exactly one namespace, `TOULMIN`.

## Decision drivers

- The scripted lane is a determinism claim the whole library rests on. A criterion in it asserts that the same artifact yields the same finding on any machine, forever. Putting a criterion there whose real question needs judgment spends that claim on something that cannot honor it, and the cost lands on every skill, not just this one.
- P3 measures per-criterion recall. If a scripted check shares an ID with a judged element, its recall number reads as the element's recall, and a skill that reliably detects the word *therefore* would publish as a skill that reliably detects claims. That is a false claim made automatically, which is the failure mode [ADR 0016 (contract enforcement boundary)](0016-contract-enforcement-boundary.md) already ruled against in the validator.
- IDs are permanent. Whatever this pipeline picks is reserved forever, including through a later decision to drop a check, so a shape chosen for convenience now is not cheaply undone.
- The skill has to have something for `scripts/checks.py` to implement. A skill whose `checks.py` implements nothing still has to exist, still has to pass its own pytest suite, and gives the corpus module no scripted-lane coverage to seed.
- A reader of a `TOULMIN-*` finding should be able to tell from the ID which question was asked.

## Considered options

1. **Dual-lane the elements.** Declare `TOULMIN-CLAIM` in both `checks.scripted` and `checks.judged`, the script producing a first pass and the judged sweep refining it. Rejected: forbidden outright by the template's lane manifest rule and caught mechanically by `lane-overlap`. It is also incoherent under the contract, where `finding.lane` is a per-finding claim about how a finding was reached; two findings on one ID with different lanes cannot be reconciled by a consumer reading `summary`.

2. **Fold the assists into the element criteria and call those criteria scripted.** `TOULMIN-CLAIM` becomes conclusion-marker detection; `TOULMIN-QUALIFIER` becomes hedge counting. Rejected as the most damaging option, for the same reason [ADR 0016](0016-contract-enforcement-boundary.md) rejected heuristic approximation of the field contracts. It fails in both directions: an artifact whose opening sentence is a direct recommendation has a perfectly good claim and no marker, and an artifact stuffed with the word *therefore* can still have no conclusion at all. Worse, it renames the question. A reader who sees `TOULMIN-CLAIM: satisfied` would take that as a verdict on the argument's conclusion, when the machine only ever looked for a phrase.

3. **Ship six judged criteria and an empty scripted lane (`scripted: []`).** Honest, mechanically valid, and the shape the template fixture itself uses. Rejected on three counts: it abandons the two assists S-05 explicitly specifies for this skill; the template says outright that an empty judged lane is a property of the toy fixture and not a model, and the mirror case here is no better; and it leaves `checks.py` with nothing to implement, so the skill contributes no deterministic floor and the corpus module has no scripted criteria to seed.

4. **Split the assists into their own permanent IDs alongside the six judged elements (chosen).**

## Decision outcome

Option 4. The registry is eight criteria:

| Lane | Criteria |
|---|---|
| judged | `TOULMIN-BACKING`, `TOULMIN-CLAIM`, `TOULMIN-GROUNDS`, `TOULMIN-QUALIFIER`, `TOULMIN-REBUTTAL`, `TOULMIN-WARRANT` |
| scripted | `TOULMIN-CLAIM-MARKER`, `TOULMIN-HEDGE-DENSITY` |

### AC-2 is satisfied exactly, not routed around

AC-2 is a floor (`>=6`) and names six elements. All six are present, each as its own ID, each judged on the question the model actually asks. The two additional IDs are additions above the floor, not substitutions for anything in it. A reviewer checking AC-2 against this registry finds the named six by name.

### The scripted criteria are narrower than the elements they sit beside

This is the point of the split, and the registry states it in prose next to the table so it cannot be read off:

- `TOULMIN-CLAIM-MARKER` asks whether the conclusion is signposted for a scanning reader. It firing does not mean the claim is missing; it staying silent does not mean the claim is good.
- `TOULMIN-HEDGE-DENSITY` reports a distribution over the whole artifact. It says nothing about whether any single claim is qualified correctly, which is `TOULMIN-QUALIFIER`'s judged question, decided against the grounds rather than against a count.

A `TOULMIN-CLAIM-MARKER` finding and a `TOULMIN-CLAIM` finding on the same artifact are two defects, not one reported twice.

### Both stay in the `TOULMIN` namespace

`TOULMIN-HEDGE-DENSITY` is not one of Toulmin's six named elements, which raises whether it belongs under his name at all. It does. The criterion is a Toulmin-derived measurement, the surface trace of qualifier use across an artifact, and it exists only because the qualifier is part of that model. Inventing a second namespace for two surface checks would contradict [criterion-ids.md](../../reference/criterion-ids.md)'s registry table, which assigns this skill exactly one, and would make `run.rubrics` claim two rubric sources where the skill reads one book.

### The citation question is settled here too

The research pass flagged the edition as unverified. Decision: cite the 2003 updated edition, ISBN 978-0521534333, ch. 3, since its chapter numbering is what secondary discussion of the model references. The 1958 first edition is the original publication and its chapter title is the same; page ranges differ, which is why this skill cites a chapter rather than pages.

### Thresholds are declared, not measured

`TOULMIN-HEDGE-DENSITY` fires above a hedged-sentence ratio of 0.35, at severity 3 above 0.50. `TOULMIN-CLAIM-MARKER` fires at zero markers, severity 3 once the artifact reaches 300 words. These are v0.1 defaults chosen so the lane is reproducible, which is the property claimed for it; they are not calibrated. Both are recorded under Thresholds in the registry, and P3 is where they get evidence.

## Consequences

**Positive:** the determinism claim the scripted lane makes is one this skill can actually honor, because both scripted criteria are a lexicon match and an arithmetic ratio. Per-criterion recall from P3 will report what it says it reports: `TOULMIN-CLAIM` recall is claim recall, measured on the judged lane, and cannot be inflated by a marker check riding under the same ID. The skill also satisfies S-05's slate table and AC-2 simultaneously rather than choosing between them.

**Negative:** two of eight IDs are not in Toulmin's vocabulary, so a reader who knows the model will not recognize `TOULMIN-CLAIM-MARKER` or `TOULMIN-HEDGE-DENSITY` as coming from it. The registry's Lane split section carries the derivation, which is a documentation fix for a naming cost that does not go away.

The hedging threshold is the sharpest open risk. Legitimately cautious prose, an academic argument or a risk assessment, hedges heavily on purpose, and a threshold set too low would fire on the artifacts most careful about their own qualifiers. This is the first thing P3 should look at for this skill, and the failure it should look for is a false positive on a clean corpus artifact, not a miss.

**Neutral:** eight criteria over six raises this skill's share of the corpus-module obligation. The template requires an injector and a planting recipe for every scripted criterion plus at least three judged ones, so `bench/generator/domains/argument.py` needs both scripted injectors and three of the six element injectors at minimum, across at least three recipes with at least one clean. That is more work than a six-criterion registry, and it is the work that makes the recall numbers mean anything.

## Implementation sites

- `skills/critique-argument/references/TOULMIN.md`: the eight-row registry, the Lane split section, and the Thresholds section. Written.
- `skills/critique-argument/SKILL.md`: `checks.scripted` and `checks.judged` declaring the split above, and the body's note on what the scripted lane does not claim. Written.
- `skills/critique-argument/references/severity-anchors.md`: the double-counting rule between the scripted findings and the judged elements beside them. Written.
- `skills/critique-argument/scripts/checks.py`: `IMPLEMENTED_CRITERIA` must be exactly `{"TOULMIN-CLAIM-MARKER", "TOULMIN-HEDGE-DENSITY"}`, cross-checked against `checks.scripted` by `scripts/skill-selftest.py`. Not yet written.
- `bench/generator/domains/argument.py`: injectors for both scripted criteria and at least three judged ones, registered in `bench/generator/registry.py`. Not yet written.
- `docs/reference/criterion-ids.md`: no change required. The namespace registry already assigns `TOULMIN` to this skill and this ADR keeps both new IDs inside it.
