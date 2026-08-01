# 0022 - Consistency floor for stretch gating: 0.309, the minimum core-skill overall-lane consistency

## TL;DR
- **Decision:** the [R1 (consistency floor value)](../release-plans/plan_v0.1.0/plan_v0.1.0.md) floor for v0.1.0 is **0.309**, the lowest per-tier consistency measured on any of the three core skills in run set `p3-2026-07-31`, taken on the **overall lane cut** (every finding, scripted and judged together). It comes from `critique-clarity` on `claude-haiku-4-5-20251001`. A stretch skill clears the gate when its consistency is at or above 0.309 on the tier being cited, read from the published three-decimal value in [`bench/results/results.json`](../../../bench/results/results.json).
- **Also published, not gating:** the judged-lane-only cut, whose core minimum is **0.090** (`critique-accessibility` on haiku). That is the honest instrument reading of the part of the library that needs a model. It is published in [`bench/results/README.md`](../../../bench/results/README.md) as a diagnostic and is the number to watch across versions, but it does not gate v0.1.0.
- **Why overall gates:** it is the stricter of the two floors against this data, it is what a user of the skill actually experiences, and it is the only one of the two that a reader can reproduce from committed files with a committed command.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, build-run P3 calibration judge (Claude)

## Context and problem statement

[R1 (consistency floor value)](../release-plans/plan_v0.1.0/plan_v0.1.0.md) left the stretch-skill consistency gate unset on purpose: the 0.7 Jaccard target in [methodology section 8](../../explanation/methodology.md) is a placeholder, and a pre-committed arbitrary number would either block every stretch skill or gate none of them. The plan's recommendation is `floor = min(core-skill consistency)` measured in P3, "minus nothing", so that the public claim is "stretch skills ship only if they are at least as consistent as the core skills we measured first".

P3 has now run. Run set `p3-2026-07-31` covers 460 envelopes, 23 artifacts, two pinned tiers, k=5, complete grid, zero quarantined. That resolves the missing data but exposes a choice the plan's one-line recommendation does not settle: **consistency of what?**

Every skill emits findings on two lanes ([methodology section 7](../../explanation/methodology.md)). The scripted lane is deterministic by construction, so its run-to-run Jaccard is at or near 1.000 for every skill that has one. The judged lane is where variance actually lives. Pooling them produces a number that is partly a measure of how large a skill's scripted lane is. Splitting them produces a number that measures only the model, and that no committed file carries.

The two cuts give materially different floors:

| Lane cut | Core minimum | Set by |
|---|---|---|
| Overall (scripted plus judged) | **0.309** | `critique-clarity` / haiku |
| Judged only | **0.090** | `critique-accessibility` / haiku |

Full core-skill consistency, both cuts, all six cells:

| Skill | Tier | Consistency (overall) | Consistency (judged only) |
|---|---|---|---|
| critique-clarity | haiku | **0.309** | 0.150 |
| critique-accessibility | haiku | 0.362 | **0.090** |
| critique-usability | haiku | 0.378 | 0.304 |
| critique-clarity | sonnet | 0.466 | 0.418 |
| critique-accessibility | sonnet | 0.605 | 0.449 |
| critique-usability | sonnet | 0.642 | 0.597 |

## Decision drivers

- **The floor has to be reproducible from committed files.** [`bench/results/results.schema.json`](../../../bench/results/results.schema.json) states the repository's own rule: no number appears in any document here that is not present in a committed `results.json`. That file carries one `consistency` field per (skill, skill_version, model, domain) group, and that field is the overall cut. Its entry object sets `additionalProperties: false` and has no lane dimension, so a judged-only figure cannot be carried there without a schema change, which is out of scope for this run. A gate whose threshold is not in the file the gate is checked against is a gate on a number nobody else can recompute with the shipped CLI.
- **Overall is the stricter gate against this data.** The floor and the candidate are read on the same cut, so the comparison that matters is the margin. Every stretch cell clears both floors, but the thinnest margin under the overall floor (`critique-argument` on haiku, +0.062) is a quarter of the thinnest margin under the judged floor (+0.230). Choosing overall is the conservative choice, not the flattering one.
- **Overall is what the user experiences.** A user reads one critique. They do not receive the judged lane separately, and a skill whose scripted lane reliably catches the same defects every run genuinely is more repeatable in use than one that does not have a scripted lane. Gating on the number the user meets is defensible in a way that gating on an internal diagnostic is not.
- **A 0.090 floor would not be a gate.** Published as the release threshold, it says a stretch skill may ship if roughly one judged finding in eleven repeats between two runs of the same skill on the same artifact on the same tier. That is not a bar; it is a number that happens to be lower than everything else. R1's "minus nothing" instruction is about not padding the floor downward, and adopting the weaker of two honest readings is padding by another route.
- **The judged reading must still be published.** The reason to look at the judged cut is that it is the one that will move as skills are revised, and hiding it would make the overall figure look like a claim about model behavior when it is partly a claim about lane composition. It publishes beside the gating number, labelled as derived, with the recipe to recompute it.
- **Both cuts produce identical verdicts here.** All six stretch cells pass both floors. The choice is therefore about what the library says it measures, not about who ships, which is the right condition under which to settle a definition.

## Considered options

1. **Floor 0.309 on the overall lane cut, judged cut published as a diagnostic (chosen).** Strictest of the honest readings against this data, reproducible from `results.json` with the committed CLI, matches what a user experiences.
2. **Floor 0.090 on the judged lane cut.** Rejected. It is the more informative measurement and the weaker gate, and it is not carried in any committed results file. Adopting it would mean publishing a release threshold that gates nothing and cannot be recomputed without a script this release does not ship.
3. **Gate on both cuts (a stretch skill must clear 0.309 overall and 0.090 judged).** Rejected for v0.1.0, though it is the right shape once the results schema carries a lane dimension. Today it would make the release gate depend on a number no committed artifact holds, and it adds no discrimination: the judged condition is satisfied by every candidate by a wide margin, so it would be a gate in name only.
4. **Keep the methodology's placeholder 0.7.** Rejected, and this is what R1 exists to avoid. Against measured data, 0.7 fails **all six core-skill cells** (the best core cell is `critique-usability` on sonnet at 0.642) while **five of six stretch cells clear it** (only `critique-argument` on haiku, 0.371, does not). The library would be holding stretch skills to a bar that no committed core skill meets, and holding it against the skills that measured *better*. A threshold the shipping skills cannot reach is not a quality bar, it is an unmaintained default.
5. **Floor = min across core skills after averaging the two tiers.** Rejected. Averaging across tiers hides the haiku result, which is where every core skill is weakest and where a cheap-tier user actually lands. Per-tier minimum is the reading that does not launder the worst case.

## Decision outcome

Option 1.

**The floor: 0.309.** Gating cut: overall. Source cell: `critique-clarity` / `claude-haiku-4-5-20251001` / clarity domain, run set `p3-2026-07-31`. Comparison is made on the published three-decimal values, so the gate is a string-stable arithmetic check anyone can rerun.

**Applying it to the three stretch skills** (numbers in [`bench/results/verdicts.md`](../../../bench/results/verdicts.md)):

| Stretch skill | Tier | Consistency (overall) | Margin vs 0.309 | Consistency (judged) |
|---|---|---|---|---|
| critique-argument | haiku | 0.371 | +0.062 | 0.320 |
| critique-argument | sonnet | 0.737 | +0.428 | 0.724 |
| critique-docs | haiku | 0.842 | +0.533 | 0.775 |
| critique-docs | sonnet | 1.000 | +0.691 | 1.000 |
| critique-microcopy | haiku | 0.768 | +0.459 | 0.623 |
| critique-microcopy | sonnet | 0.853 | +0.544 | 0.846 |

All six cells clear the floor. The consistency half of the [S-05 (skills slate)](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-7 stretch gate is therefore satisfied for all three stretch skills; the baseline-win half is assessed separately in `verdicts.md`.

**Scope of the floor.** It is a v0.1.0 number, tied to this run set, these two model IDs, this corpus and this k. It is not a standing library constant and it is not a claim about what judged-lane critique can achieve. Re-measuring on a new run set re-derives it; a later run set with better core skills will raise it, which is the intended ratchet.

**What this does not do.** It does not retroactively bless the core skills. Core ships on the [S-05](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-6 baseline rule regardless of consistency, and 0.309 is a poor number in absolute terms: it means roughly three in ten `(criterion, location)` pairs survive between two runs of `critique-clarity` on haiku. The floor records where the library actually stands, which is the point of setting it empirically.

## Consequences

**Positive:** the stretch gate is now a computable check against a committed file rather than a placeholder. The claim it supports is narrow and true: a stretch skill in v0.1.0 is at least as repeatable as the least repeatable core skill measured on the same corpus, on the same tier, in the same run set. Setting the floor from data also converts an aspiration (0.7) into a published measurement of the gap between aspiration and instrument, which is the more useful artifact for v0.2.

**Negative:** 0.309 is low, and publishing it as a gate invites the fair reading that the gate is easy. It is. It is easy because the core skills it is derived from are not very consistent yet, and the alternative to admitting that is a threshold that blocks the release without improving anything. The floor also inherits the overall cut's structural bias: a skill with a large deterministic scripted lane clears it more easily than a judged-heavy skill of equal model-side quality. `critique-argument` on haiku (0.371 overall, 0.320 judged, +0.062 of margin) is the case where that bias is thinnest and where a small regression in a future run set would flip the verdict.

**Neutral:** the judged-only figures are published but uncommitted to `results.json`, so they carry a weaker reproducibility guarantee than every other number in `bench/results/`. That gap is recorded as an open item for the orchestrator rather than closed here, since closing it means changing the results schema.

## Open items handed to the orchestrator

- **Results schema has no lane dimension.** `bench/results/results.schema.json` fixes `additionalProperties: false` on each entry with no lane discriminator, so judged-only and scripted-only cuts cannot be carried in `results.json`. Recommended for v0.2: add an optional `lane` field to the entry key so the report script can emit all three cuts and `bench/report.py --check` can guard them against drift. Not changed here: schemas are frozen for this run.
- **Consequent tension with a stated repository rule.** `bench/README.md` and the results schema description both state that no number appears in any document in this repository that is not present in a committed `results.json`. The judged-lane figures in `bench/results/README.md` and in this ADR are the first exception. They are labelled as derived and shipped with an exact recomputation recipe, but the rule as written is now broken and should be either amended to cover labelled derived cuts or satisfied by the schema change above.

## Implementation sites

- [`bench/results/verdicts.md`](../../../bench/results/verdicts.md): applies this floor to the three stretch skills, per [S-05](../release-plans/plan_v0.1.0/S-05_skills-slate/spec.md) AC-7.
- [`bench/results/README.md`](../../../bench/results/README.md): publishes both cuts, the floor, and the recomputation recipe.
- [`docs/internal/release-plans/plan_v0.1.0/plan_v0.1.0.md`](../release-plans/plan_v0.1.0/plan_v0.1.0.md): R1 row moves from Open to Resolved, pointing here. Not edited by this ADR.
- [`docs/explanation/methodology.md`](../../explanation/methodology.md) section 8: still carries the 0.7 placeholder and the sentence promising it will be replaced once baseline data exists. That data now exists. Methodology is frozen for this run, so the update is flagged, not made.
