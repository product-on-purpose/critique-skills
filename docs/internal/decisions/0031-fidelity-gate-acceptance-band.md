# 0031 - The fidelity gate's acceptance band: making ADR 0030's gate failable

## TL;DR
- **Decision:** ADR 0030's fidelity gate is specified as a numeric band, published before the run
  it judges, in [`bench/results/variance.json`](../../../bench/results/variance.json) and computed
  by `python -m bench.variance`. The gate is evaluated on the two location-level metrics of the
  re-run cell; the criterion-level pair and consistency are reported and not gated.
- **Why:** ADR 0030 accepts the rewritten judged lane on "a partial re-run whose figures land
  within measured run-to-run variance of the committed ones." **No such variance figure existed.**
  `bench/results/results.json` pools every k=5 repetition and every artifact of a domain into one
  cell figure, so every published number is a ratio of sums carrying no recorded spread. The gate
  as written could not be failed, and a re-run returning almost anything could have been declared
  faithful.
- **What it cost to find out:** nothing. The band is computed from the 500 committed envelopes with
  no new model runs, by regrouping them on the repetition index in their filenames.
- **The finding that changes the run:** **haiku's bands are 2.3x wider than sonnet's** (median width
  0.145 against 0.063). The cheap tier is the weak test, which reverses the obvious budget choice.
- **Status:** Accepted (2026-08-15).

- **Status:** Accepted
- **Date:** 2026-08-15
- **Deciders:** Jonathan Prisant

## Builds on

- [0030 - Replace the API key in the bench harness](0030-replace-the-api-key-in-the-bench-harness.md),
  whose "Open questions" item 2 sets the gate this ADR makes falsifiable. That ADR is not
  superseded: its gate stands, and this one supplies the threshold it was missing.
- [0023 - v0.1.0 measurement basis: two pinned tiers, k=5](0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md),
  which chose k=5 precisely because single runs vary. This ADR is the first time that variation was
  measured rather than assumed.
- [0022 - Consistency floor: 0.309, overall lane](0022-consistency-floor-overall-lane-min-core.md),
  whose floor this ADR reports it cannot band, and says why.

## Context and problem statement

ADR 0030 replaced the benchmark's judged lane. The harness used to assemble its own prompt from a
skill's `SKILL.md` and parse findings back out; it now runs the real skill through
`claude --plugin-dir` and keeps the envelope the skill emits. That was the right change, and it
means **the committed figures in `bench/results/` were produced by a harness that no longer
exists.** Nothing in the repository claims otherwise, and nothing may, until the fidelity gate runs.

The gate ADR 0030 sets is "a partial re-run whose figures land within measured run-to-run variance
of the committed ones." Costing that run surfaced the problem: the phrase names a quantity this
repository has never computed.

`results.json`'s entries are keyed by `(skill, skill_version, model, domain)` and pool every
repetition and every artifact into one numerator over one denominator. A `critique-clarity` sonnet
row reads `recall_location: 89/100`, and those 100 planted defects are 4 artifacts times k=5
repetitions collapsed into a single ratio. **The five repetitions that produced it are not recorded
anywhere as five things.**

So "within measured run-to-run variance" had no threshold behind it. Any re-run figure could have
been argued into or out of the gate after the fact, which is the failure mode worse than a wrong
number: an unfalsifiable one.

## Decision drivers

- **The bar must be published before the measurement.** This library leads its results page with
  the numbers that do not flatter it. Choosing an acceptance criterion after seeing the result would
  undercut that more thoroughly than a failed gate ever could.
- **The band must cost no model spend.** The evidence is already committed. A gate threshold that
  itself required a paid run would be circular.
- **The decomposition must be provable.** A per-repetition figure that does not sum back to the
  published figure is measuring something else, and a band on top of it would be a number about
  nothing.
- **The band must not claim more than it covers.** It is repetition variance within one run set. A
  fidelity re-run also changes transport, date, staging and isolation flags.

## Considered options

1. **Publish the band, gate on it.** Chosen.
2. **Gate on a judgement call**, comparing figures and deciding by eye whether they are "close".
   Rejected: this is what the gate already was, and it is unfalsifiable.
3. **Pick a round number**, for instance plus or minus 0.05 on every metric. Rejected: it is
   arbitrary, and the measured widths span 0.000 to 0.247, so any single figure is far too tight on
   some cells and far too loose on others.
4. **Re-measure the full grid instead**, publishing new figures and abandoning the fidelity
   argument. Rejected on cost: the skill condition alone is 230 cells and 24 to 46 hours serial, and
   a within-run-set baseline comparison would require re-running the baseline too, roughly doubling
   it. The fidelity gate exists precisely so this is not necessary.

## Decision

### Method

`python -m bench.variance`, three steps, in order, because the third is worthless if the second
does not hold.

1. **Scope.** Score the documented view: a run set minus its probe directories. `runs/steering/`
   holds two prompt-injection-resistance probes that share identity fields with the grid and pool
   into `critique-clarity` / sonnet if included, taking it from 20 scored runs to 22 and from 40
   consistency pairs to 51. `bench/results/README.md` already records this and excludes them by
   hand in its reproduction recipe, and separately notes that a recipe step is a fragile place to
   put a rule. Here the exclusion is the tool's default.

2. **Decompose, and prove it.** An envelope's filename carries its repetition index
   (`haiku-r3.json`); no contract field records it, which is the `run_set` and lane schema debt
   `ROADMAP.md` lists as v0.2.0 measurement debt and is why this parses paths. Regrouping on that
   index and pooling within one repetition yields k figures where `results.json` has one, through
   the same `bench.metrics.score` calls `build_results` uses.

   Pooling every repetition back together must then reproduce the committed numerator and
   denominator **exactly**. `build_variance` refuses to emit a band otherwise, and refuses equally
   when no cell lined up with a committed entry at all, because silence is not verification.
   **Measured: 104 of 104 cell-metrics reproduce exactly**, across both committed run sets.

3. **Band.** The published statistic is `sum(numerators) / sum(denominators)`, not a mean of
   per-repetition ratios, so its sampling variation is estimated by resampling **whole repetitions**
   with replacement and recomputing the pooled ratio. Whole repetitions rather than individual
   artifact scores, because that preserves both the ratio-of-sums structure and the
   within-repetition correlation across artifacts. 20000 draws, seed 20260815, 2.5th to 97.5th
   percentile.

### The gate

> **Scope.** The gate is evaluated on `recall_location` and `precision_location` for the re-run
> cell. The criterion-level pair is reported alongside but not gated: it is highly correlated with
> the location-level pair, and gating both inflates the false-failure rate without adding
> independent evidence.
>
> **Pass.** Both gated figures fall inside the published band for that same cell, computed over the
> same artifacts at the same k.
>
> **A single marginal miss triggers investigation, not automatic failure.** Two metrics each at 95
> percent give a perfectly faithful re-run roughly a 10 percent chance of landing outside on at
> least one; gating all four would push that to roughly 18 percent. One miss is a prompt to find out
> what moved. Both missing, or a miss wider than the band's own width, is a failure.
>
> **Consistency is reported, not gated.** A re-run at k=5 produces one, and no band exists for it
> (see below), so gating it would be gating against a number with no measured uncertainty.
>
> **Coverage must be complete.** The band assumes all of the cell's artifacts at full k. A cell that
> exhausts `SKILL_RUN_ATTEMPTS` produces a coverage gap, and `run_bench.py` records that as a
> failure and continues the grid rather than aborting, so a gapped run completes and yields a
> smaller pooled figure that is not comparable. Any gap invalidates the comparison: re-dispatch the
> affected cells, or recompute the band over exactly the coverage obtained.
>
> **A pass is evidence, not proof.** The band covers repetition variance within one run set. It does
> not cover the transport change, the date, the staging, or the isolation flags, all of which differ
> in the re-run.

## Consequences

### What the band shows

**The bands are wide.** Median width across the 28 location-level skill cell-metrics is 0.082; the
widest is 0.247. The single-run spread, the range across the five repetitions, has a median of 0.135
and a maximum of 0.412. `critique-accessibility` 0.1.0 on sonnet publishes a location recall of
0.306 from five runs that measured 0.529, 0.294, 0.353, 0.118 and 0.235. The published figure is an
honest summary of those five; any one of them alone would have told a different story. This is k=5
working as designed, and it is the reason "close to the published number" needed a band rather than
an intuition.

**The cheap tier is the weak test.**

| tier | band width, median | band width, mean | single-run spread, median |
|---|---|---|---|
| haiku | 0.145 | 0.141 | 0.228 |
| sonnet | 0.063 | 0.080 | 0.096 |

Haiku's bands are 2.3x wider. Per skill on location recall: clarity 3.0x, argument 2.7x, microcopy
1.5x, usability 1.2x. (`critique-accessibility` 0.1.0 inverts it, but those are the cells that lost
to baseline and sit near the floor, where the metric is degenerate.) Cost runs the other way: a
haiku cell takes 3m35s to 6m01s, a sonnet cell exceeds nine minutes. **Choosing haiku to save hours
buys a gate roughly twice as easy to pass**, and that trade must be recorded if it is taken, not
absorbed as a cost decision.

**Gate power varies 8x across cells.** Narrowest non-degenerate band: `critique-usability` / sonnet
/ `precision_location` at 0.031. Widest: `critique-accessibility` 0.1.0 / sonnet / `recall_location`
at 0.247. **Which cell is re-run is therefore a decision about how hard the gate is**, and it is
recorded here rather than settled by whichever skill is cheapest. `critique-docs` on sonnet is a
special case: it scored 1.000 in every repetition, so its band has zero width, which is maximally
discriminating and useless as a gate, because a single malformed envelope fails it and that failure
would be about envelope validity rather than fidelity.

**Recommended re-run: `critique-clarity` on sonnet, k=5, all four clarity artifacts, 20 cells.**
Bands `recall_location` [0.860, 0.920] and `precision_location` [0.403, 0.466], tight enough to
fail; not degenerate at either end; the skill every live probe so far has exercised, so harness risk
is lowest; and adjacent to the most-cited published number, since clarity's haiku cell sets the
0.309 consistency floor. Budget 4 to 4.5 hours, noting that the 1.33x retry inflation is borrowed
from haiku because sonnet's post-assembler envelope validity has never been measured, and that at
haiku-like rates there is roughly a 27 percent chance of at least one coverage gap across 20 cells.

### What this ADR does not fix

**The consistency floor has no band and cannot get one by this method.**
`score.score_consistency` compares pairs of envelopes and is undefined for a single repetition, so
it cannot be decomposed the way recall and precision can. **The published 0.309 floor therefore
carries no uncertainty estimate**, and neither does any other consistency figure in `results.json`.
That number is set as a release gate by ADR 0022 and published in `ROADMAP.md` under known
limitations, so it is worth stating plainly rather than leaving implied. A band for it needs a
different construction, resampling pairs or leaving out repetitions, and belongs with the v0.2.0
measurement debt.

**The repetition index is still not a contract field.** `bench/variance.py` parses it out of
filenames, and `parse_repetition_index` is deliberately the single place that knows the convention,
so when the schema debt is paid only that function and one schema string change. `variance.json`
does not repeat the related mistake: every entry carries its own `run_set`, where `results.json`
records one run_set on a file holding two.

**`variance.json` is not regenerated in CI.** It is committed evidence derived from committed
evidence, and regenerating it on every push would spend a minute of CI to reproduce a file that only
changes when the run sets do. The reproduction guard inside `build_variance` is what protects it: it
cannot be regenerated into disagreement with `results.json` without failing loudly.
