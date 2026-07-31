# 0003 - Skill slate: three core, three gated stretch

## TL;DR
- **Decision:** Ship three core skills unconditionally (`critique-usability`, `critique-accessibility`, `critique-clarity`) and three stretch skills conditionally (`critique-docs`, `critique-microcopy`, `critique-argument`); a stretch skill ships in v0.1.0 only if it beats the frozen baseline prompt and clears the consistency floor set empirically during the build run.
- **Why:** Locks in a defensible core slate while letting the harder, judged-heavier domains earn their place with evidence instead of assumption, so a bad number becomes a documented hold rather than a shipped weak skill.
- **Status:** Accepted (2026-07-31).

- **Status:** Accepted
- **Date:** 2026-07-31
- **Deciders:** Jonathan Prisant, planning session with Claude

## Context and problem statement

The methodology's provisional slate spans far more domains than one release can operationalize and measure credibly (`00-README.md` known gaps records a 12-domain provisional slate with no completed survey behind it). Six domains were chosen for v0.1.0 (`01-strategy-brief.md`; S-05, the skills-slate spec), split by confidence: usability, accessibility, and clarity have the clearest scriptable signal and established rubric sources (WCAG, the US Federal Plain Language Guidelines, Nielsen's heuristics). Docs, microcopy, and argument are judged-heavier and less proven at the shared 0-4 severity scale; severity-scale transfer to prose and argumentation domains is explicitly flagged untested in `00-README.md`. The decision was whether all six ship unconditionally, or whether the harder three should be gated on results the build run itself produces.

## Decision drivers

- The consistency floor for the stretch-skill gate (release plan open item R1) is genuinely unknown until measured; the release plan's own recommendation is to set it as "the lowest core-skill consistency, minus nothing," computed in phase P3, not pre-committed.
- Shipping a skill nobody has evidence for would contradict the full-slate-with-evidence decision (see [0002 - Full slate scope for v0.1.0](0002-full-slate-scope.md)).
- Refusing to attempt the harder domains at all would waste the build run's parallel capacity (the P2 phase already runs six pipelines, per `workflow/workflow-design.md`) and would forecloses coverage that might succeed on the first attempt.

## Considered options

1. **Ship all six unconditionally.** Not pursued: contradicts the evidence-first posture of [0002 - Full slate scope for v0.1.0](0002-full-slate-scope.md) if any of the harder three fails to beat baseline or falls below the consistency floor. The strategy brief calls out this exact failure risk for usability already, the most broadly appealing skill and, per the brief, the one with "the weakest scripted lane and the hardest corpus to seed."
2. **Build only the three core skills; treat the rest as pure roadmap items.** Not pursued: this forgoes the build run's already-planned parallel capacity and forecloses domains that might succeed on the first attempt without ever giving them a fair, measured chance.
3. **Build all six identically through the S-04 template, gate stretch skills on measured results (chosen).** Core skills ship regardless of first-pass numbers, but their numbers still publish as measured, and a core skill failing baseline is a release blocker requiring one calibration iteration, not silent shipping. Stretch skills ship only if they beat baseline AND clear the R1 (consistency floor, release plan open item) threshold; a stretch skill that fails is retained in-tree under a documented `status: incubating`, with its numbers published in `bench/results/` and the hold explicitly recorded rather than the skill being quietly deleted.

## Decision outcome

Option 3. This produces a slate where, per the strategy brief's own framing, "any outcome is publishable" for the stretch-skill pass rate: a stretch skill that ships does so with numbers behind it, and one that does not ship still leaves an honest, measured record.

## Consequences

**Positive:** no skill ships without evidence it deserves to. A held-back stretch skill is documented, not silently dropped: `RELEASE-NOTES.md` and `rc-handover.md` must record the hold (per S-08's requirements and the release plan's RC-definition item 5). Core skills get exactly one calibration iteration on baseline failure before the release halts (`workflow-design.md` failure policy), so a fixable core miss does not by itself sink the release.

**Negative:** three of six skills carry real ship-or-hold uncertainty into the build run; the strategy brief rates confidence on the stretch-skill pass rate as "medium... unknowable until P3 runs." A held-back skill still consumes real build effort with no v0.1.0 shipping payoff beyond its published numbers.

**Neutral:** `critique-usability`'s narrow artifact claim (release plan open item R2: HTML and markdown UI specs, explicitly not live applications) is a related but separately decided mitigation for the hardest core-skill risk in this same slate.

## Implementation sites

Not yet created; the repository is pre-scaffold as of this ADR's date. Per S-05 (skills-slate spec) requirements, this decision will be enforced at:

- `library.json` - the `components` array excludes a held-back stretch skill even though its directory remains in-tree (S-05 requirements, "incubating in-tree retention rather than deletion").
- `bench/results/` - per-skill envelopes and the ship or hold verdict for each stretch skill (S-05 AC-7).
- Each stretch skill's own `SKILL.md` - carries `status: incubating` if held back.

The R1 consistency-floor threshold itself is set during the build run's phase P3 and is recorded as its own, separate ADR at that time; it is not fixed by this ADR.
