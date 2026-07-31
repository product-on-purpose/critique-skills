# 0021 - critique-usability lane split: each scripted assist is a structural floor with its own ID

## TL;DR
- **Decision:** `critique-usability`'s registry carries **20** criteria across the 10 heuristics. The three scripted assists [S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) names for this skill get their own permanent IDs and are the entire scripted lane: `NNG-H3-DEADEND` (orphan states), `NNG-H4-CONTROL-NAMING` (control naming consistency), `NNG-H6-LABELED` (label presence). Each sits beside a judged sibling under the same heuristic (`NNG-H3-EXIT`, `NNG-H4-INTERNAL`, `NNG-H6-RECALL`) that covers the judgment the script cannot make, and a de-duplication rule in `references/NNG-HEURISTICS.md` says which one reports.
- **Why:** the [skill template](../skill-template.md) forbids one criterion appearing in both lanes, and folding a structural check into a heuristic criterion would make a determinism claim the library cannot back: a state having zero outgoing links is not the same claim as a user being able to get out of it. Splitting is what [criterion-ids.md](../../reference/criterion-ids.md)'s permanence rule 4 already requires of a rubric item bundling two independently checkable things.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P2 `critique-usability` pipeline (Claude)

## Context and problem statement

S-05 specifies this skill in two places that have to be reconciled before `checks.py` exists.

Its slate table gives the expected lane balance as judged-heavy with scripted assists, naming those assists exactly: label presence, control naming consistency, orphan states. Its AC-2 gives the registry population as exactly the 10 heuristics with sub-criteria as needed.

Nielsen's heuristics are judged criteria by construction. Whether a flow gives the user an obvious and cheap way out, whether a confirmation adequately gates a costly action, whether a screen surfaces only what its task needs: each requires reading the artifact as a whole, which is the definition the skill template's "Scripted lane discipline" section gives for the judged lane. Taken alone, then, AC-2 yields a skill with an empty scripted lane, while the slate table promises three deterministic checks. The three assists have to live somewhere.

This is the same problem the `critique-argument` pipeline solved for its two assists in [ADR 0017 (argument lane split)](0017-argument-lane-split-scripted-assists-as-criteria.md), and the answer here is deliberately the same shape, so the family reads consistently.

## Decision drivers

- **No criterion in two lanes.** The template states it flatly, and `scripts/skill-selftest.py` fails on it (`lane-overlap`). A criterion that is sometimes scripted and sometimes judged is two criteria.
- **The determinism claim is load-bearing.** The scripted lane's promise is same artifact, same output bytes, on any machine. A criterion whose text asks whether the user can get out of a flow cannot honor that promise, no matter how good the heuristic behind the script is.
- **Permanence rule 4.** A rubric item bundling two independently checkable things is split before it ships, not merged. Heuristic 3 bundles the structural question (is there an exit at all) with the quality question (is it visible, predictable, and cheap). Heuristics 4 and 6 bundle analogous pairs.
- **Seeding coverage.** The template's corpus-module obligation requires an injector and a recipe for every scripted-lane criterion. An assist with no ID cannot be seeded, cannot be planted, and therefore cannot have recall reported for it at P3, which would make the scripted lane's numbers unmeasurable exactly where they are supposed to be strongest.
- **A script must not silently understate a heuristic.** If `NNG-H3-EXIT` were the scripted criterion, a run that found every state to have some outgoing link would report that heuristic clean, when the artifact might still hide every exit behind an unlabeled corner control. That is a false negative dressed as determinism.

## Considered options

1. **Empty scripted lane; all 17 criteria judged.** Rejected: it contradicts the slate table's lane balance, and it discards three checks that genuinely are deterministic and genuinely catch defects (a dead-end state, a form of unnamed inputs, three synonyms for one commit action).
2. **Put the heuristic-level criteria in the scripted lane and let the script approximate them.** Rejected: the determinism claim would be false in the direction that matters, false negatives on criteria the library says are machine-decided. This is the failure mode the template's "when in doubt, judged" rule exists to prevent.
3. **Give each assist its own ID inside the heuristic it serves, with a judged sibling and a stated de-duplication rule (chosen).** The scripted claim is exactly what a script can decide, the judged criterion keeps the heuristic's actual meaning, and the pair is explicitly not a proxy relationship.
4. **Give the assists a separate namespace (for example `NNGX-*`).** Rejected: they operationalize the same source, and criterion-ids' namespace registry gives this skill one namespace. A second namespace would also appear in `run.rubrics` as a source the skill does not have.

## Decision outcome

Option 3. The three pairs, with the reporting rule for each:

| Scripted criterion | What the script decides | Judged sibling | De-duplication rule |
|---|---|---|---|
| `NNG-H3-DEADEND` | A defined state has zero outgoing edges in the artifact's own link graph; an edge naming an undefined target does not count. | `NNG-H3-EXIT` | A state with no exit at all is the scripted finding. `NNG-H3-EXIT` is judged only on flows that do have an exit. |
| `NNG-H4-CONTROL-NAMING` | Two or more distinct members of one fixed synonym set (commit, cancel, back) appear as control labels in one artifact. | `NNG-H4-INTERNAL` | A label pair the synonym sets matched is not re-reported as a judgment. `NNG-H4-INTERNAL` covers icons, domain nouns, and repeated patterns the lists cannot see. |
| `NNG-H6-LABELED` | A control or input carries no readable name: no text content, no accessible-name attribute, no associated label. | `NNG-H6-RECALL` | An unnamed control is the scripted finding. `NNG-H6-RECALL` covers information the user needs and cannot see, not the naming of the control. |

Three further consequences of the split, recorded because `checks.py` and the corpus module depend on them:

- **The scripted lane's severities are fixed by rule, not judged**, and `references/severity-anchors.md` states each rule. A judged pass does not re-rate a scripted finding; doing so would reintroduce run-to-run variance into the lane whose entire value is not having any.
- **The sub-criterion suffix is descriptive, not numeric.** `NNG-H3-DEADEND`, not `NNG-H3.1`. Dot notation is reserved for preserving an upstream numbering scheme verbatim (WCAG's `1.4.3`), and Nielsen publishes no sub-numbering to preserve.
- **The split does not widen the artifact claim.** All three scripted checks read a static UI spec or mockup: a link graph, a set of control labels, a set of control names. None of them requires operating an interface (S-05 AC-8).

## Consequences

**Positive:** the scripted lane makes only claims a script can honor, and each of the three is separately seedable, so P3 can report recall per scripted criterion rather than for the lane as a lump. The judged criteria keep the heuristics' real meaning instead of being narrowed to whatever a regex could reach. The registry lands at 20 criteria across exactly the 10 heuristics, satisfying AC-2's population as stated.

**Negative:** three heuristics now carry three sub-criteria each, so a critic sweeping in ID order visits the same heuristic twice and has to apply the de-duplication rule to avoid double-reporting one defect. That rule is a judgment step, and a critic that ignores it inflates the finding count on exactly the defects the scripted lane already caught. The de-duplication table above and the matching section in `references/NNG-HEURISTICS.md` are the mitigation; whether it holds is a P3 question, visible as duplicate `(criterion, location)` pairs in the same run.

**Neutral:** 3 of 20 criteria scripted is a lower scripted share than `critique-clarity` or `critique-accessibility` will carry. That is the slate's own expectation for this domain (judged-heavy), not a shortfall, and the skill's determinism claim is proportionally smaller and correspondingly true.

## Implementation sites

- `skills/critique-usability/SKILL.md`: `checks.scripted` (3 IDs), `checks.judged` (17 IDs), and the "Criteria" section's canonical sweep order.
- `skills/critique-usability/references/NNG-HEURISTICS.md`: the six rows of the three pairs, their Lane and Lane rationale columns, and the "De-duplication rules" section.
- `skills/critique-usability/references/severity-anchors.md`: "Fixed severities for the scripted lane".
- Not yet created: `skills/critique-usability/scripts/checks.py` (its `IMPLEMENTED_CRITERIA` must equal the three scripted IDs exactly) and `bench/generator/domains/usability.py` (an injector and a recipe per scripted criterion, plus at least three judged ones).
