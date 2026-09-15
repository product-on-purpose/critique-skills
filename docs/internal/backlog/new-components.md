# New-component backlog

> Proposals to ADD a component (skill, command, subagent, hook, chain, and so on) to this plugin
> (Standard sec 7.1). Each item records the proposed `name`, component type, target `tier`,
> `agent-targets`, rationale, and status, and passes a why-gate before it is accepted. Changes to
> components that already exist live in [enhancements.md](enhancements.md) instead.

## The why-gate

A proposal enters this file only after answering four questions on the record. Two of them are
sharper here than in the family default, because of what this project has committed to publicly:

1. **Is it warranted?** Which published standard does it critique against, with a URL or an ISBN?
   `ROADMAP.md`'s "Deliberately not doing" section rules out taste-based criteria with no citable
   source.
2. **Does it duplicate an existing component?** Six critique skills ship today. A proposal that is
   really a mode of one of them is an enhancement, not a component.
3. **Can it be measured?** A seeded-defect corpus and a results table are load-bearing here, not
   polish. `ROADMAP.md` says plainly that a skill which cannot be measured against ground truth does
   not ship, regardless of how well its rubric reads. A proposal must name the artifact type it
   would be seeded into and confirm the corpus generator can actually produce it.
4. **What does it cost across the catalog?** Every new skill edits the joint-routing eval and, in
   practice, the descriptions of the six skills it competes with for routing.

All four proposals below entered on 2026-09-11 from the backlog-expansion intake, and all four are
carried from `ROADMAP.md`, so their warrant is already public. What this file adds is the recorded
gate verdict, the dependency each one actually has, and an honest note on which of them is blocked
on infrastructure rather than on effort.

**Sequencing, as it stands on 2026-09-14.** `ROADMAP.md` names all three skills under v0.2.0 and
orders them deck, forms, dataviz. Two maintainer rulings have since changed that. v0.2.0 was ruled
Option A plus Option C on 2026-09-11, and on 2026-09-14 the survey was deferred and **forms was
prioritized ahead of deck**. The order is now:

| | Skill | Release | Why |
|---|---|---|---|
| 1 | **N2 critique-forms** | **v0.2.0** | Reuses the shipped `html` artifact type and resolver; no new corpus machinery |
| 2 | N1 critique-deck | v0.3.0 | Needs a new corpus module for a domain that does not exist |
| 3 | N3 critique-dataviz | unscheduled | Needs a chart-spec generator mode that does not exist and is unscoped |

`ROADMAP.md` still states the old order and is deliberately not edited here; see
[the shape options brief](../release-plans/v0.2.0-shape-options.md).

---

## N1 - critique-deck (assertion-evidence presentation critique)

- **Proposed name:** `critique-deck`
- **Component type:** skill.
- **Target tier:** convergent (Silver), matching the six shipped skills.
- **Agent-targets:** claude, codex.
- **Rationale:** assertion-evidence critique of markdown decks. `ROADMAP.md:52` names it first and
  lowest-risk of the second wave because the corpus work is straightforward: it reuses the existing
  `markdown-tree` and `markdown-prose` location grammar rather than needing a new artifact type.
- **Why-gate verdict:** PASSES on all four. Warranted (assertion-evidence is a citable published
  method); not a duplicate (no shipped skill critiques deck structure); measurable (it reuses an
  existing artifact type, so the generator already produces its shape); and the cost is understood
  and is the reason for going first. This is the reference implementation that proves the skill
  template and prices the cross-skill routing work before two more skills have to pay it.
- **Evidence:** `ROADMAP.md:52`; `skills/` (no `critique-deck` directory); `bench/corpus/` (no
  `deck/` domain among accessibility, argument, clarity, docs, microcopy, toy, usability);
  `evals/README.md:20-21,35-38` (the joint-routing cases and their hand-scoring).
- **Done looks like:** the skill and its references, a corpus module, joint-routing cases including
  edits to the six existing descriptions, golden examples, and k=5 measurement on both pinned tiers
  present in the README scoreboard.
- **Size:** L. **Release:** v0.3.0.
- **Ruling 2026-09-11, superseded:** brought into v0.2.0 as Option C's one new skill.
- **DEPRIORITIZED 2026-09-14 by the maintainer, behind N2 (critique-forms).** Deck was sequenced
  first because `ROADMAP.md:52` calls it the lowest-risk of the wave. That reasoning does not
  survive inspection: deck needs a **new corpus module** for a domain that does not exist, while
  forms reuses `critique-accessibility`'s shipped `html` artifact type and its element, CSS and id
  resolver. On the measure that actually matters here, how much new infrastructure a skill needs,
  **forms is the lower-risk starter and deck is not**. The swap is better sequencing, not a
  concession.
- **Blocks:** nothing. The `ROADMAP.md` sequence that had deck blocking forms was convention, not
  a technical dependency, and is superseded.
- **Depends on:** E30 (skill-template gaps) hard, E2 (sonnet unblock) for two-tier k=5, and a new
  corpus module for the deck domain.
- **Status:** backlog (recorded 2026-09-11).

## N2 - critique-forms (form usability, Wroblewski and Baymard)

- **Proposed name:** `critique-forms`
- **Component type:** skill.
- **Target tier:** convergent (Silver).
- **Agent-targets:** claude, codex.
- **Rationale:** form-usability critique sourced to Wroblewski's form-design work and Baymard's
  research. `ROADMAP.md:53` sequences it second because HTML forms have a strong scriptable share
  and it reuses `critique-accessibility`'s existing `html` artifact type and its element, CSS and
  id resolver rather than building new tooling.
- **Why-gate verdict:** PASSES on all four. Warranted (both sources are citable and published); not
  a duplicate (`critique-accessibility` checks WCAG conformance, not form usability, and the two are
  different criterion sets applied to the same artifact); measurable (the `html` artifact type and
  its resolver already exist); and its cost is the lowest of the three because the infrastructure is
  reuse rather than new build.
- **Evidence:** `ROADMAP.md:53`; `skills/` (no `critique-forms` directory).
- **Done looks like:** the same bar as N1.
- **Size:** L. **Release:** v0.2.0.
- **PRIORITIZED 2026-09-14 by the maintainer, ahead of N1 (critique-deck).** Forms is now the one
  new skill v0.2.0 contains. The dependency on N1 below was removed with it: it was the
  `ROADMAP.md` sequence restated, not a technical constraint. Forms reuses the shipped `html`
  artifact type and `critique-accessibility`'s resolver, so unlike deck it needs no new corpus
  machinery, which makes it the cheaper skill to prove the template on.
- **Blocks:** nothing directly.
- **Depends on:** E30 (skill-template gaps) hard, and E2 (sonnet unblock) for two-tier k=5.
  **No longer depends on N1.**
- **Status:** backlog (recorded 2026-09-11).

## N3 - critique-dataviz (chart critique, Tufte and Cairo)

- **Proposed name:** `critique-dataviz`
- **Component type:** skill.
- **Target tier:** convergent (Silver).
- **Agent-targets:** claude, codex.
- **Rationale:** chart and data-graphic critique sourced to Tufte and Cairo. `ROADMAP.md:54` records
  that this has the strongest demand signal of the three second-wave skills and goes last anyway,
  because it is the only one blocked on infrastructure rather than on sequencing.
- **Why-gate verdict:** PASSES on warrant, non-duplication and cost. **CONDITIONAL on
  measurability**, which is the gate that matters here. The corpus cannot currently produce a
  chart-spec artifact: the `artifact_type` enum, mirrored at `bench/results/results.schema.json:88`,
  admits only `markdown-prose`, `markdown-tree`, `html` and `string-list`. Under `ROADMAP.md`'s own
  rule that an unmeasurable skill does not ship, this proposal is accepted into the backlog but
  cannot be scheduled until the generator mode exists. **That generator mode needs its own spec and
  should be sized separately from the skill.** Treating the two as one item is what makes this read
  as an unschedulable XL rather than two tractable pieces.
- **Evidence:** `ROADMAP.md:54`; `bench/corpus/` (no `dataviz/` domain, no chart-spec generator
  present); `bench/results/results.schema.json:88` (the `artifact_type` enum).
- **Done looks like:** a new chart-spec generator mode with its own spec, then the skill at the same
  bar as N1.
- **Size:** XL as a single unit; roughly L plus M if split at the generator boundary.
- **Release:** unscheduled.
- **Ruling 2026-09-11:** moved out of any numbered release and held in the backlog on the
  maintainer's instruction. It is intended for after v0.2.0, but the timing is deliberately not
  set, because the chart-spec generator it depends on has not been scoped and dating the skill
  before its blocker is sized would be a guess. It stays here, accepted and unscheduled, rather
  than dropped: this is the item whose presence in the v0.2.0 exit gate made that gate
  unclosable, and taking it out of the gate is what the ruling above buys.
- **Blocks:** nothing directly.
- **Depends on:** a chart-spec corpus generator mode that does not exist, plus E30 and E2.
- **Status:** backlog (recorded 2026-09-11), accepted with the measurability condition above.

## N4 - Revision loop as a first-class, invokable chain

- **Proposed name:** the revision-loop chain (name not yet chosen; this is the chain contract plus
  its entry point, not a seventh critique skill).
- **Component type:** chain, with the contract at `agents/_chain-permitted.yaml`.
- **Target tier:** the chain itself is the artifact Gold checks G1 and G3 evaluate; the plugin stays
  at convergent until that coverage exists.
- **Agent-targets:** claude (chain contracts are a Claude-side construct at this tier).
- **Rationale:** critique, disposition, revise, re-critique exists today only as a documented recipe
  at `examples/recipes/revision-loop.md`, with a three-iteration bound, a
  converge-on-zero-severity-3/4 rule, and every revise step hand-authored. `ROADMAP.md:78` names
  making it a real chain as the first v0.3.0 item.
- **Why-gate verdict:** PASSES, with one open question that must be ruled before building rather
  than during. The recipe's revise step is performed by a human today. **Who performs `revise` in an
  automated chain is not decided anywhere in the repository**, and it collides directly with the
  "Deliberately not doing" entry for auto-fix: skills report findings and a human disposes them. A
  chain that revised on its own authority would contradict a published scope commitment. That
  ruling is tracked as E52 (who performs revise) and gates this proposal.
- **Evidence:** `ROADMAP.md:78`; `examples/recipes/revision-loop.md` (the mermaid diagram, the
  three-iteration bound, and the line recording that the revised v2 memo was authored for the
  recipe).
- **Done looks like:** an invokable chain with a defined convergence rule, plus
  `agents/_chain-permitted.yaml` so Gold check G3 has something real to evaluate instead of passing
  vacuously.
- **Size:** L. **Release:** v0.3.0.
- **Blocks:** E55 (chain and hook evaluation coverage, Gold G1 and G3).
- **Depends on:** E52 (rule who performs revise).
- **Status:** backlog (recorded 2026-09-11).
