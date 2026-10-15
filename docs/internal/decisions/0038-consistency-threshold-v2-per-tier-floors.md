# 0038 - Consistency threshold v2: per-tier floors on the overall lane, an expected value for the scripted lane, and the judged lane as a diagnostic

## TL;DR
- **Decision:** a new skill's consistency gate is set per tier, on the overall lane cut. **Sonnet:
  0.450**, the lowest current-harness figure among the three core skills. **Haiku: 0.309**, carried
  from [ADR 0022](0022-consistency-floor-overall-lane-min-core.md) with its provenance stated beside
  it. The scripted lane has an expected value of 1.000, reported and not gated. The judged lane is
  published per cell as a diagnostic, with no threshold.
- **Why the sonnet floor moved:** a new skill is measured through the current benchmark harness, so
  the floor it is compared to must come from that harness too. ADR 0022's 0.309 came from the
  build-run mechanism that [ADR 0030](0030-replace-the-api-key-in-the-bench-harness.md) replaced.
- **Why haiku did not move:** only two current-harness haiku cells exist, and only one of them is a
  core skill. The rule below re-derives the haiku floor once all three core skills have
  current-harness haiku data.
- **Ruled:** by the maintainer on 2026-10-15, choosing the recommended option on each of three
  decisions (scripted lane, judged lane, overall floor).
- **Status:** Accepted (2026-10-15). Amends ADR 0022; does not supersede it.

- **Status:** Accepted
- **Date:** 2026-10-15
- **Deciders:** Jonathan Prisant (the ruling). Drafted by Claude from the committed run directories.

## Builds on

- [0022 - Consistency floor: 0.309, overall lane](0022-consistency-floor-overall-lane-min-core.md),
  whose method this ADR keeps and whose sonnet reading it replaces.
- [0030 - Replace the API key in the bench harness](0030-replace-the-api-key-in-the-bench-harness.md),
  which defines the current harness every new skill is measured through.
- [0031 - The fidelity gate's acceptance band](0031-fidelity-gate-acceptance-band.md), which records
  that consistency cannot be banded, so neither floor here carries an uncertainty estimate.
- [E26 (consistency threshold v2)](../backlog/enhancements.md), which this ADR closes.

## Context and problem statement

ADR 0022 set one floor, 0.309, from one run set: `critique-clarity` on haiku in `p3-2026-07-31`. It
said the number was provisional. E26 asked for its replacement, "a calibrated per-lane threshold
published with its method". Two things had to exist before that was possible. The results schema
needed a lane dimension, which results version 1.2.0 added. And the current harness needed data on
both tiers. Sonnet has it for all seven skills since 2026-10-14. Haiku has it for two.

Overall-lane, judged-lane and scripted-lane consistency, from every current-harness run directory:

| Skill | Tier | Overall | Judged | Scripted | Run |
|---|---|---|---|---|---|
| `critique-docs` 0.1.0 | sonnet | 0.967 | 0.950 | 1.000 | `38673837025` |
| `critique-microcopy` 0.1.0 | sonnet | 0.924 | 0.914 | 1.000 | `38683363024` |
| `critique-accessibility` 0.1.1 | sonnet | 0.745 | 0.620 | 0.969 | `38673834829` |
| `critique-forms` 0.1.0 | sonnet | 0.651 | 0.507 | 0.928 | `37091134037` |
| `critique-argument` 0.1.0 | sonnet | 0.645 | 0.602 | 1.000 | `38678419907` |
| `critique-usability` 0.1.0 | sonnet | 0.573 | 0.520 | 1.000 | `34917728793` |
| `critique-clarity` 0.1.0 | sonnet | **0.450** | 0.277 | 0.907 | `34917562578` |
| `critique-forms` 0.1.0 | haiku | 0.691 | 0.317 | 0.816 | `37091134037` |
| `critique-clarity` 0.1.0 | haiku | 0.337 | 0.042 | 0.825 | `31988100372` |

Three things in that table shaped the decision.

**The scripted lane reads below 1.000 in five of nine cells.** Its checks are deterministic code, so
two runs on one artifact should report identical scripted findings. They do not, because the model
transports the script's findings into the envelope and sometimes drops or relabels them.
[E73 (make the merge step run the scripted lane itself)](../backlog/enhancements.md) names the
defect and the fix.

**The judged lane spans 0.042 to 0.950.** It is where run-to-run variance actually lives, as ADR 0022
already observed. A threshold set at its lowest existing cell passes every existing skill by
definition.

**The current harness reads lower consistency than the published figures in five of the six launch
skills on sonnet.** Accessibility 0.1.1 reads 0.745 against 0.808 published, argument 0.645 against
0.737, clarity 0.450 against 0.466, docs 0.967 against 1.000, and usability 0.573 against 0.642.
Microcopy is the exception, at 0.924 against 0.853. So the sonnet floor below is lower than p3's
sonnet core minimum of 0.466. That is because the instrument reads lower, not because a skill
regressed.

## Decision drivers

- **A floor and a candidate must come from the same instrument.** Every new skill is measured through
  the current harness, as `critique-forms` was. Comparing its figure with a floor from the replaced
  mechanism mixes two instruments, and the table above shows they disagree.
- **Keep ADR 0022's rule shape.** The floor is the minimum over the core skills, per tier, "minus
  nothing". The public claim stays the same: a new skill ships only if it is at least as consistent
  as the core skills measured first.
- **Do not turn a known defect into a standard.** A scripted-lane threshold calibrated to the five
  cells below 1.000 would publish the transport defect as the expected behaviour.
- **A threshold must be able to fail something.** On the judged lane, the haiku minimum is 0.042, a
  bar that gates nothing.
- **Do not build a floor on the thinnest data.** Haiku has two current-harness cells. One is
  `critique-forms`, which is not a core skill. The other completed 19 of its 20 runs.

## Considered options

Three decisions, each ruled on the recommended option.

**The scripted lane.**

1. **Expected value 1.000, reported and not gated until E73 lands (chosen).** A measured shortfall is
   read as the transport defect, not as calibration data.
2. **Gate on 1.000 now.** Rejected. Five of nine current-harness cells would fail today, including
   the shipped `critique-forms` on both tiers, for a defect in the harness rather than the skill.
3. **Calibrate a threshold to the data, around 0.816.** Rejected by the driver above.

**The judged lane.**

1. **Publish per cell as a diagnostic, with no threshold (chosen).** `bench.report table` already
   prints it in its per-lane block, so no new tooling is needed.
2. **Gate new skills at the current-harness minimum per tier, 0.277 on sonnet and 0.042 on haiku.**
   Rejected. The haiku figure gates almost nothing, and the sonnet figure adds little to the overall
   floor, which already includes the judged findings.

**The overall floor.**

1. **Per tier: sonnet from the current harness, haiku carried from p3 with its provenance (chosen).**
2. **Haiku at 0.337, the lower of the two current-harness haiku cells.** Rejected. It is a minimum
   over two cells, only one of them a core skill, and that one has a coverage gap.
3. **Run paid haiku dispatches for `critique-usability` and `critique-accessibility` first, then set
   the haiku floor from them.** Not taken. It needs a fresh approval for paid runs, and it is not
   needed for any skill now in flight.

## Decision outcome

**The gate.** A new skill clears the consistency condition on a tier when its overall-lane
consistency, measured through the current harness at k=5, is at or above that tier's floor. The
comparison uses the published three-decimal value, as under ADR 0022.

| Tier | Floor | Source cell | Run | Instrument |
|---|---|---|---|---|
| sonnet | **0.450** | `critique-clarity` 0.1.0 | `34917562578`, 2026-09-15 | the current harness |
| haiku | **0.309** | `critique-clarity` 0.1.0 | `p3-2026-07-31` | the build-run mechanism ADR 0030 replaced |

The sonnet floor is the minimum over three core-skill cells: clarity at 0.450, usability at 0.573
(run `34917728793`) and accessibility 0.1.1 at 0.745 (run `38673834829`).

**The method, per tier.** The floor is the minimum overall-lane consistency over the most recent
current-harness measurement of each of the three core skills, at the version `library.json` ships.
Haiku keeps 0.309 until all three core skills have current-harness haiku data, and the same rule
then re-derives it. Re-measuring a core skill re-derives its tier's floor. The floor can move in
either direction, and the change that moves it states the old value and the new one.

**The scripted lane.** Its expected consistency is 1.000, by construction. The measured figure is
reported per cell. A figure below 1.000 is read as the defect E73 names. Nothing gates on this lane
until E73 lands, and the change that closes E73 decides whether to gate on it afterwards.

**The judged lane.** Its consistency is published per cell as a diagnostic, in `bench/README.md`'s
per-lane table, and nothing gates on it.

**The shipped skills, read against the new floors.** No skill's status changes. Every shipped skill
clears both floors, and clarity sits exactly on each one, because it sets them.

| Skill | Sonnet, current harness | Margin vs 0.450 | Haiku, published | Margin vs 0.309 |
|---|---|---|---|---|
| `critique-accessibility` 0.1.1 | 0.745 | +0.295 | 0.625 | +0.316 |
| `critique-argument` 0.1.0 | 0.645 | +0.195 | 0.371 | +0.062 |
| `critique-clarity` 0.1.0 | 0.450 | 0.000 | 0.309 | 0.000 |
| `critique-docs` 0.1.0 | 0.967 | +0.517 | 0.842 | +0.533 |
| `critique-forms` 0.1.0 | 0.651 | +0.201 | 0.691 | +0.382 |
| `critique-microcopy` 0.1.0 | 0.924 | +0.474 | 0.768 | +0.459 |
| `critique-usability` 0.1.0 | 0.573 | +0.123 | 0.378 | +0.069 |

**Reproducing the sonnet floor.** None of the three source runs is in the top-level `results.json`,
and the two older ones carry no `results.json` of their own. Each figure is recomputed from its
committed envelopes with the committed scorer, calling no model:

```
python -m bench.metrics score --corpus bench/corpus --runs bench/results/runs-dispatch-34917562578 --out /tmp/clarity-sonnet.json --run-set bench-34917562578
python -m bench.metrics score --corpus bench/corpus --runs bench/results/runs-dispatch-34917728793 --out /tmp/usability-sonnet.json --run-set bench-34917728793
python -m bench.metrics score --corpus bench/corpus --runs bench/results/runs-dispatch-38673834829 --out /tmp/accessibility-sonnet.json --run-set bench-38673834829
```

Read `consistency.value` on the skill's `overall` entry in each output. On 2026-10-15 these read
0.450, 0.573 and 0.745, each over 40 pairs.

## Consequences

**Positive:** on sonnet, the gate now compares like with like. The scripted-lane defect stays visible
as a defect instead of being absorbed into a threshold. And each lane now has a stated treatment and
a stated method, which is what E26 asked for.

**Negative:**

- **The sonnet floor is a number no published `results.json` carries.** The rule ADR 0022 quotes says
  no number appears in any document here unless a committed `results.json` holds it. ADR 0022's
  judged-lane figures were the first exception, and results version 1.2.0 closed it. This is the
  second. The envelopes and the command above make it reproducible, but the rule is broken until
  [E63 (dispatch run sets outside results.json)](../backlog/enhancements.md) brings dispatch run sets
  into the published file or amends the rule.
- **The haiku floor mixes instruments.** A new skill measured on haiku through the current harness is
  compared with a floor from the old mechanism. The one core cell measured both ways, clarity on
  haiku, read 0.337 through the current harness against 0.309 published. That suggests the carried
  floor is the more lenient reading, on one cell with a coverage gap, and it shows nothing more.
- **Neither floor has an uncertainty estimate.** ADR 0031 records that consistency cannot be banded
  by the bootstrap method. A candidate within a few hundredths of a floor is inside noise of unknown
  size.
- **Clarity sets both floors, so a skill exactly as consistent as clarity passes.** That is ADR 0022's
  "minus nothing" rule, carried forward unchanged.

**Neutral:** no shipped skill's status or verdict changes, and no code changes. The floor has never
been enforced by a script. It is applied in the recorded ship verdict for each new skill.

## What this ADR does not decide

- Whether to gate on the scripted lane once E73 lands. The change that closes E73 decides it.
- Whether to run paid haiku dispatches for the core skills. That needs its own approval.
- How dispatch run sets join `results.json`. That is E63.
