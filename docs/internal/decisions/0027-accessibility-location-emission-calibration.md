# 0027 - critique-accessibility 0.1.1: the one permitted calibration is a location-emission fix, not a criteria change

## TL;DR
- **Decision:** spend the single pre-committed calibration iteration on **where `critique-accessibility` says a defect is**, not on what it looks for. `skills/critique-accessibility/scripts/checks.py`'s `_loc` helper stops discarding the element id it is already holding: every scripted finding now leads with a `#id` token, or with a bounded CSS path in double quotes for an element carrying no id, and keeps the line number as a trailing human convenience. `SKILL.md` gains a "Naming a location" section and per-criterion sweep discipline in the judged lane so a hand-written finding is held to the same rule. Skill version 0.1.1.
- **Why:** the skill's detection is already correct. Run locally over the whole accessibility corpus, `checks.py` finds 13 of 13 scripted-lane-targeted planted defects at criterion level with zero false positives and zero findings on the clean artifact, and only 1 of 85 sonnet defect instances was never noticed by either lane. What it could not do was name a place: 55 of 65 sonnet scripted claims (84.6 percent) and 54 of 65 haiku claims (83.1 percent) resolved to no node at all, because `line 21, <img> element` is not an anchor in the `html` location grammar. [0026](0026-location-level-re-examination-of-baseline-gates.md) recorded the resulting substantive AC-6 failure (location recall 0.306 sonnet, 0.176 haiku, against a baseline of 0.776 and 0.376). The gap was a formatting defect in one helper, sitting downstream of a correct critique.
- **What it is not:** no criterion was deleted, weakened, moved between lanes, or re-scoped. No corpus manifest, generator, or artifact was touched. No scoring rule, tolerance, or metric definition was changed, and the frozen baseline was not re-postprocessed (bounding parity already held). The permitted-lever list was pre-committed before the diagnosis was read, and every change below sits inside it.
- **Status:** Accepted (2026-07-31). **Measured 2026-08-01.** This ADR deliberately claimed no score;
  the re-measurement that supplies one is
  [0028 - Post-calibration verdict: critique-accessibility 0.1.1 clears AC-6 on re-measurement](0028-post-calibration-verdict-accessibility-clears-ac-6.md).
  The diagnosis below was correct and the predicted mechanism is the one that moved: location
  resolvability, not detection.

- **Status:** Accepted, outcome measured in [0028](0028-post-calibration-verdict-accessibility-clears-ac-6.md)
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, P3 calibration pass (Claude)

## Builds on

- [0026 - Location-level re-examination of the baseline gates](0026-location-level-re-examination-of-baseline-gates.md), which produced the failing verdict this iteration answers, and whose ancestor-window objection turns out to have a mirror image on the skill's own side (see "The greedy-assignment loss" below).
- [0012 - Location grammar: free text now, structured selector reserved](0012-location-grammar-freetext-plus-reserved-selector.md). `location` stays free text and stays the metric key. This ADR changes what one producer writes into that string, not the field's contract, and it does not start populating the reserved `selector` object: no v0.1 consumer reads it, so writing it would change nothing measurable.
- [0015 - Location tolerance keyed on artifact type](0015-location-tolerance-per-artifact-type.md). The `html` tolerance is applied unchanged. Nothing about which locations count as a hit was altered; only which locations the skill emits.

## Context and problem statement

`critique-accessibility` is a core skill that lost its baseline comparison on both pinned tiers and on both metrics. [S-05](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md)'s AC-6 makes that a release blocker with three named remedies: iterate once inside P3, halt with a handover diagnosis, or ship with the failure published. The iterate branch was taken, under a policy fixed in advance: **one iteration, from a permitted lever list, with an ADR**. The permitted levers are scripted-check bug fixes, location-emission wording, severity-anchor wording, four-pass protocol emphasis, and measurement-parity fixes. Deleting or weakening criteria, editing the corpus to make defects easier, and changing scoring to favour the skill are forbidden outright, and remain so whether or not the iteration succeeds.

The diagnosis pass ran before any edit and ranked candidate mechanisms by how many of the 85 sonnet defect instances each explains.

| Mechanism | Instances | Verdict |
|---|---|---|
| Scripted-lane location emission (`_loc` discards the element id) | 50 | dominant cause |
| Judged-lane location emission (class or prose instead of an id) | 8 | real, secondary |
| Greedy-assignment loss into the ancestor window | 5 | scoring artifact, self-correcting |
| Judged-lane true detection failure | 1 | negligible |
| Output bounding suppressing sub-threshold findings | 1 | ruled out quantitatively |
| Scripted-check detection bugs | 0 | none exist |

Two of those rows deserve stating plainly, because they are the reason this ADR changes no criteria.

**There is no detection bug to fix.** A deterministic local re-run of `checks.py` over `bench/corpus/accessibility/*.html` emits 7 findings on `accessibility-001` (7 planted defects), 6 on `accessibility-002` (6 planted), 0 on `accessibility-003` (whose 4 planted defects are all judged-lane criteria, correctly out of the scripted lane's scope), and 0 on the clean `accessibility-004`. That is 13 of 13 scripted-lane-targeted defects, each named under exactly the criterion the manifest planted it under, with no false positives anywhere.

**Output bounding is not capping recall on this corpus, and the clarity domain proves it.** Across all 40 accessibility envelopes, `suppressed_count` totals 1 on sonnet and 0 on haiku; only 6 of 20 sonnet runs and 0 of 20 haiku runs even reach the five-finding sub-threshold cap. `critique-clarity` reaches that cap in 15 of 20 sonnet runs and suppresses 42 findings, on a corpus that plants *more* defects per artifact and more of them in the sub-threshold band, and it scores 0.890 and 0.780 location recall. Recall in this run set tracks location resolvability, not bounding pressure. Had the single suppressed sonnet finding been a perfect hit, recall would have gone from 0.306 to 0.318 against a 47-point gap.

## The defect

`skills/critique-accessibility/scripts/checks.py`, in 0.1.0:

```python
def _loc(node, descriptor):
    return f"line {node.line}, {descriptor}"
```

Every one of the 17 planted accessibility defects is anchored by `kind: element-id`, and `bench/metrics/resolve_html.resolve` recognizes exactly four `html` anchors (bench/README.md, "Location tolerance"): an element id, a quoted bounded selector, an ordinal over a frozen noun table, and a quoted span of element text that is unique on the page. A line number is none of them, so a location built from one names nothing, however precisely it reads to a person.

Two of the thirteen resolved anyway, by coincidence: `#html` and `#body` are planted ids that happen to equal the tag names the descriptor prints, and the resolver's bare-token pass found them in the prose. That coincidence is why the failure looked partial rather than total.

The model was not the problem at any point. All 65 scripted findings survived into the envelope, and the location string is byte-identical to `checks.py` output in 98.5 percent of sonnet findings and 89.2 percent of haiku findings. Of the 50 sonnet misses attributable to this mechanism, 29 carry the truth element id verbatim inside the finding's own `evidence` field. The information was in the envelope; it was in the wrong field.

## Decision outcome

### 1. `checks.py` emits an anchor, not a line number (permitted lever: scripted-check fix, location emission)

`_loc` now composes `<anchor>, <descriptor>, line <n>`, with two new helpers beside it:

- `_element_anchor(node)` returns `#<id>` when the element carries an id matching the bare-token grammar the resolver recognizes, and otherwise a double-quoted bounded CSS path (`"html > body > main > p:nth-of-type(2) > a"`) built by `_css_path_parts`, using tag names, the child combinator, and `:nth-of-type` only, all inside the documented bounded engine. An id outside the bare-token grammar is carried inside that path as `tag#id` rather than dropped.
- The line number moves to the end of the string and is documented, in the module docstring and in `SKILL.md`, as a human convenience that is never the anchor.

The result is truncated to the contract's 400-character `locationText` bound with the anchor intact, since the anchor leads.

One descriptor changed wording: WCAG-1.4.4's `meta name="viewport" element` became `<meta> viewport element`, so the descriptor no longer contains a stray double-quoted span that the resolver would try, and fail, to read as a selector.

**Measured effect, scripted lane alone, deterministically, no model in the loop.** Over the four corpus artifacts, using the committed scorer (`bench.metrics.score.score_artifact_location`) and the committed tolerance:

| Artifact | Defects matched | Claims matched | Unresolvable claims |
|---|---|---|---|
| accessibility-001 | 7 / 7 | 7 / 7 | 0 |
| accessibility-002 | 6 / 6 | 6 / 6 | 0 |
| accessibility-003 | 0 / 4 (all judged-lane criteria) | 0 / 0 | 0 |
| accessibility-004 (clean) | 0 / 0 | 0 / 0 | 0 |
| **total** | **13 / 17 = 0.765** | **13 / 13** | **0** |

That figure is a diagnostic, not a published metric: it is the scripted lane on its own, with no judged lane and no model, and it is not comparable to the 0.306 and 0.176 in `results.json`, which are model-in-the-loop numbers over the full grid. It is reported because it is reproducible from the repository with no API call, and because it isolates the thing that changed.

### 2. The greedy-assignment loss self-corrects

On `accessibility-001` the 0.1.0 WCAG-3.1.1 claim `line 2, <html> element` did resolve (canonical key `#html`), but `bench/metrics/match.py` sorts candidates by `truth_anchor_key`, so `id:head-title` was consumed first and that claim was spent crediting the head-title defect through the two-step ancestor window; WCAG-3.1.1 then scored zero on both tiers. This is [0026](0026-location-level-re-examination-of-baseline-gates.md)'s ancestor-window objection appearing on the skill's side of the ledger, and it accounts for 5 instances. **No scoring code was touched to address it.** Once each claim names its own element, the greedy assignment has no reason to reach for an ancestor, and `accessibility-001` scores 7 of 7. Fixing an emitter is not the same as fixing a scorer, and only the first was permitted.

### 3. `SKILL.md` states the same rule for the judged lane (permitted levers: location emission, four-pass emphasis)

The judged lane leaks for the same reason at a smaller scale: 8 of the 20 sonnet judged-target instances were detected and located unresolvably, typically by naming a class in prose (`line 47, div.wizard-steps in section 'Schedule changes'`) where an id was available. A class name is inside the resolver's bounded engine; a class name that is not in double quotes is not, because nothing marks it as a selector rather than as prose.

- A new **"Naming a location"** section gives the preference order (element `id` as `#token`; else a double-quoted bounded selector; else a double-quoted span of the element's own text of at least eight characters), then says what a location is not: a line number, a section title, a bare class name in prose, or a phrase naming a neighbourhood. It states explicitly that a hand-written judged finding is held to the same rule as `checks.py` output, because a reader cannot tell which lane a finding came from.
- **Pass 1 (Inventory)** now says to record each element's `id` while mapping, since recovering it afterwards is where locations decay into line numbers.
- **Pass 2 (Criterion sweep)** now requires each judged criterion to be swept against every element it governs, naming the element by id as it is judged, with the criteria that most often go shallow called out by name (WCAG-4.1.2, WCAG-1.4.1, WCAG-3.3.1, WCAG-1.3.2, WCAG-2.4.6). It also says the scripted lane's silence on a judged criterion means only that no script was asked to look.
- `references/WCAG.md` carries a three-line pointer to the same rule, so a reviewer working criterion by criterion out of the registry meets it where they are reading.

### 4. The five golden examples now show the rule they teach

`examples/golden-01` through `golden-04` were regenerated from the current `checks.py` (findings, severities, evidence, violations, fixes, and summaries are byte-identical to 0.1.0; only the location strings and `skill_version` changed). `golden-05`, the hand-written judged-lane example, had all four of its locations rewritten by hand from `line 27 and 30, the two <label> elements carrying class="required-label"` to `"label.required-label", the two required-field labels, lines 27 and 30`, and each was verified to resolve through `bench.metrics.resolve_html`. A golden example that demonstrates the old habit would teach it back.

### 5. Levers deliberately not pulled

- **Severity-anchor wording.** Permitted, and not needed: nothing was being under-rated into the suppressed band, because almost nothing was suppressed (1 finding across 40 envelopes). Rewriting anchors to lift severities with no evidence of mis-rating would be inflation dressed as calibration, and the anchors have to stay defensible per domain.
- **Baseline postprocess parity.** The parity check came back true, so nothing in `bench/baseline/` was touched and no `.v2.json` files were produced. The frozen baseline stays frozen.
- **Anything touching criteria, corpus, or scoring.** Forbidden by the pre-committed policy, and, on this diagnosis, unnecessary: the criteria detected 13 of 13, and the corpus was never the difficulty.

## Consequences

**Positive:** the skill now names elements the way the family's own resolver, and a human opening dev tools, both read them. The scripted lane resolves 13 of 13 corpus claims to their planted node with no unresolvable claims, from 2 of 13. The judged lane has one written rule instead of an implicit habit, and the golden examples demonstrate it. The fix is in one helper, so it is small enough to review and hard to have broken something else with.

**Negative:** the published `results.json` figures for `critique-accessibility` are 0.1.0 figures and stay that way until a rerun over the pinned grid, which this iteration does not perform. **This ADR does not claim a new score.** [0026](0026-location-level-re-examination-of-baseline-gates.md)'s recorded AC-6 failure stands as the measured state of the run set `p3-2026-07-31`; whether 0.1.1 clears the gate is unmeasured, and any statement otherwise would be exactly the kind of unevidenced claim this library exists to avoid. The one permitted iteration is now spent: a second pass at this skill is a release-owner decision, not a build-run one.

> **Resolved 2026-08-01.** The rerun this paragraph declined to perform was performed as run set `cal1-2026-08-01`: 40 envelopes, the same four artifacts at the same sha256 values, the same two pinned model IDs, k=5. 0.1.1 reads location recall 0.988 (haiku) and 0.965 (sonnet) against the frozen baseline's 0.376 and 0.776, at higher precision on both tiers. The refusal to claim a score before measuring one was the right call and the measurement vindicated the diagnosis; see [0028](0028-post-calibration-verdict-accessibility-clears-ac-6.md), including the checks run against the result and the three things it still does not establish. The statement that the one permitted iteration is spent stands.

**Neutral:** locations are longer, and a CSS-path fallback is uglier to read than an id. Every corpus artifact and most real markup carries ids, so the fallback is the exception. Skill version 0.1.1 makes `library.json`'s component entry disagree with the plugin's own 0.1.0 version; that is intended, since components version independently of the plugin, and `scripts/lib/version-manifest.mjs` reads only the three plugin-level manifests, so the release tag guard is unaffected.

## Implementation sites

- `skills/critique-accessibility/scripts/checks.py`: `_MAX_LOCATION_CHARS`, `_BARE_ID_RE`, `_css_path_parts`, `_element_anchor`, `_loc`, the WCAG-1.4.4 descriptor, the "Location emission" paragraph in the module docstring, and `skill_version` in `main`.
- `skills/critique-accessibility/scripts/tests/test_checks_accessibility.py`: the "Location emission" and "Corpus regression" sections. 13 parametrized cases, one per scripted-lane-targeted planted defect, each asserting the emitted location resolves to that defect's own node under `bench.metrics.resolve_html.is_hit`; 4 cases asserting no corpus finding is unresolvable; plus id-anchor, CSS-path-fallback, no-leading-line-number, and 400-character-bound tests. The two determinism tests are unchanged and still pass.
- `skills/critique-accessibility/SKILL.md`: frontmatter `version`, the new "Naming a location" section, and passes 1 and 2 of the protocol.
- `skills/critique-accessibility/references/WCAG.md`: the location-naming pointer under "Scope".
- `skills/critique-accessibility/examples/golden-01.json` through `golden-05.json`: locations and `skill_version`.
- `library.json`: the `critique-accessibility` component version, with `.claude-plugin/plugin.json` regenerated from it.
