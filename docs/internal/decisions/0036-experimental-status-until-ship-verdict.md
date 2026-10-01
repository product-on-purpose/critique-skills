# 0036 - A new skill is registered `experimental` until its ship verdict

## TL;DR
- **Decision:** a skill that is built but not yet measured is listed in `library.json` with
  `status: experimental`. It moves to `active` only on a ship verdict. A skill that is held stays
  `experimental`. `critique-forms` is the first skill registered this way.
- **Why:** `experimental` keeps an unmeasured skill out of every surface that advertises skills,
  while the bench harness can still plan and run it. The two older alternatives each break
  something: `active` advertises a skill with no evidence, and leaving the skill out of
  `library.json` hides it from the harness that must measure it.
- **What it changes:** where [ADR 0003](0003-skill-slate-core-and-gated-stretch.md) says a held
  skill is marked `incubating` and left out of `library.json`, read `experimental` in
  `library.json`. `incubating` is not a status the Standard accepts.
- **Status:** Proposed, accepted when PR 60 (the `critique-forms` build) merges
- **Date:** 2026-10-01
- **Deciders:** Jonathan Prisant; proposed by Claude during the N2 (critique-forms) build
- **Supersedes in part:** [ADR 0003](0003-skill-slate-core-and-gated-stretch.md), only its
  `status: incubating` wording and its two implementation-site bullets about `library.json` and
  `SKILL.md`. Its decision, that a stretch skill ships only on measured results, stands unchanged.

## Builds on

- [0003 - Skill slate: three core, three gated stretch](0003-skill-slate-core-and-gated-stretch.md),
  which gates a stretch skill on measured results and keeps a held skill in the tree.
- The [N2 (critique-forms) spec](../release-plans/_unassigned/N2_critique-forms/spec.md), AC-11 (the
  README scoreboard at k=5) and AC-12 (the ship or hold verdict).
- The Standard's section 3.7, at the version `library.json` declares (0.17). Every `library.json`
  component entry REQUIRES a `status`, and its values are `active`, `deprecated` and `experimental`.

## Context and problem statement

ADR 0003 was written before the repository existed. It said a held stretch skill would be left out
of `library.json` and would carry `status: incubating` in its own `SKILL.md`. That mechanism was
never used, because all three v0.1.0 stretch skills shipped.

`critique-forms` is the first skill added after v0.1.0, and it needed a status from its first
commit. Two facts about the repository ruled out ADR 0003's mechanism:

1. **The Standard rejects `incubating`.** The toolkit's G6 check
   (`scripts/checks/deprecation.mjs` in the toolkit) accepts only `active`, `deprecated` and
   `experimental`, and reports any other value as an error.
2. **The bench harness discovers skills from `library.json`.** `declared_skills()` in
   `bench/run_bench.py` reads `components.skills`, so a skill left out of `library.json` cannot be
   planned or measured. AC-11 and AC-12 need it measured.

Meanwhile, `active` would advertise the skill before any evidence existed. Three generators read
`status` and render only `active` skills:

| Reader | What it renders |
|---|---|
| `scripts/gen-readme-catalog.mjs` | The README's skill catalog |
| `scripts/gen-site.mjs` (`loadSkills`) | Every skill page on the documentation site |
| `bench/report.py` (`_active_versions`) | The README's scoreboard, one row per active skill |

Three other readers ignore `status`. `scripts/gen-index.mjs` lists every skill in `INDEX.md`.
`bench/run_bench.py` plans every skill. And `python -m bench.report table` renders every measured
skill in the full grid in `bench/README.md`.

## Considered options

1. **Register the skill as `experimental` until its verdict.** Chosen.
2. **Register it as `active` at once.** Rejected: the README catalog, the scoreboard and the site
   would present a skill with no measurement. That contradicts ADR 0003's rule that no skill ships
   without evidence.
3. **Leave it out of `library.json` until its verdict, as ADR 0003 described.** Rejected: the
   harness could not measure it, so the verdict that would admit it could never be produced.
4. **Use `incubating`, as ADR 0003 and the N2 spec's AC-12 wrote it.** Rejected: the gate fails
   on it.

## Decision

1. **A new skill enters `library.json` as `experimental`,** in the pull request that builds it.
2. **Its paid measurement runs while it is `experimental`.** Name the skill in the dispatch. Running
   `--skills all` also measures every `experimental` skill, because the harness ignores `status`.
3. **On a ship verdict, the status moves to `active`,** and every generator that reads it is re-run
   in the same change. The README catalog, the scoreboard and the site then show the skill for the
   first time.
4. **On a hold verdict, the status stays `experimental`.** The figures are still published in the
   full grid, which reads every measured skill. The hold is recorded where ADR 0003 requires it, in
   the verdict record and in `RELEASE-NOTES.md`.
5. **`library.json` is the only place a skill's status is recorded.** The Standard RECOMMENDS a
   `metadata.status` key in `SKILL.md` frontmatter. No skill in this library declares one, and this
   ADR does not add one.

## Consequences

- **`experimental` means "not advertised", not "not installed".** Claude Code loads every skill
  under `skills/`, whatever `library.json` says. The N2 joint-routing eval loaded `critique-forms`
  through `claude --plugin-dir` and routed requests to it. So a user who installs the plugin can
  invoke an `experimental` skill by name.
- **AC-11 can be met only after a ship verdict.** AC-11 asks for the skill's row on the README
  scoreboard, and the scoreboard renders only `active` skills. So the order is: paid run, AC-12
  verdict, status change, then the scoreboard row. On a hold, the scoreboard row never appears and
  the figures publish in the full grid instead. Whether that satisfies AC-11 is the maintainer's
  ruling.
- **The scoreboard's docstring equates `active` with what a reader can install.** Under this ADR,
  `active` means what the library advertises. The docstring and the filter are left unchanged.
- **`INDEX.md` lists `experimental` skills.** `INDEX.md` is a map for agents, and an agent needs to
  find an installed skill.
- **Every later skill follows the same path,** including N5 (critique-checkout). This ADR is the
  precedent, so no new ADR is needed per skill.

## Implementation sites

- `library.json`: `critique-forms` is registered with `"status": "experimental"` (PR 60).
- `AGENTS.md`, "Components": names `critique-forms` as `experimental`, says what that hides, and
  links here.
- [ADR 0003](0003-skill-slate-core-and-gated-stretch.md): its Status line points here.
- The N2 spec's AC-12 still says `incubating`. This ADR does not edit the spec, because its wording
  is the maintainer's. Read the word as `experimental`.
