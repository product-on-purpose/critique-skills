# E35 validator run: 2026-10-23

The two external validators that release plan phase B5 named, `plugin-dev:plugin-validator` and
`plugin-dev:skill-reviewer`, ran against `main` at `4c31c59` on 2026-10-23. Neither had run in the
seven releases since v0.1.0 ([RC-HANDOVER](RC-HANDOVER.md), "Carry to v0.2"). This page records
what each reported and what was done with each finding, which closes
[E35 (run the plugin validators)](../backlog/enhancements.md).

## What ran

| Check | How it ran | Verdict |
|---|---|---|
| `plugin-dev:plugin-validator` | A read-only subagent on Sonnet, given the repository and told which manifest is generated | Loads cleanly: 2 warnings, 4 informational findings |
| `plugin-dev:skill-reviewer` | A read-only subagent on Sonnet, reviewing the seven registered skills | 1 major, 4 minor, 2 informational findings |
| `claude plugin validate .` | Claude Code CLI 2.1.310, run from the repository root | "Validation passed", with 1 warning |

Two plugin-validator findings rested on inference about Claude Code's loader. They were checked
against the Claude Code documentation on the same day, and the dispositions below say what that
settled.

## Dispositions

The rule for this run was to fix only a mechanical finding that touches no `SKILL.md`. A change to a
`SKILL.md` moves that skill's version and puts its measured numbers in question, so such a finding
is listed here for the skill's next version, not applied. **No finding met the rule, so none was
applied on 2026-10-23.**

**Addendum, 2026-10-26.** [E73 (merge runs the scripted lane itself)](../release-plans/_unassigned/E73_merge-runs-scripted-lane/spec.md)'s
D6 ruled that R2, R3, R4, V1 and V2 ride its own `SKILL.md` edits rather than wait for a version
move of their own, because none of the five changes what a skill reports. E73's build fixed all
five on that date, named "Fixed in E73's build (2026-10-26)" in the table below. R1 still waits for
a change of its own, since a description edit changes triggering, which the trigger evals measure,
not this run. Per [D4](../release-plans/_unassigned/E73_merge-runs-scripted-lane/spec.md#d4-whether-every-skills-version-moves-decided),
no `metadata.version` moved for these five fixes: the version move for every skill E73 touches is
deferred to the release that also carries E67.

| ID | Source | Severity | Location | Finding | Disposition |
|---|---|---|---|---|---|
| R1 | skill-reviewer | major | `skills/critique-docs/SKILL.md`, description | Six of the seven descriptions name a sibling skill they are not, in a clause of the form "judges X, not Y". The critique-docs description names no sibling, although critique-clarity claims adjacent artifacts such as memos and proposals. The trigger evals already test this boundary with negative cases. | Listed for critique-docs's next version. It changes a description, which is what selects the skill. |
| R2 | skill-reviewer | minor | `skills/critique-clarity/SKILL.md:56` | The out-of-scope list names "the other five launch skills' artifact types". | Fixed in E73's build (2026-10-26). The "five launch skills" count stayed, since critique-forms shipped in v0.2.0 and is not a launch skill; the example list now also names an HTML form, routed to `critique-forms`, alongside the UI spec, error-message list and essay-structure examples it already named. |
| R3 | skill-reviewer | minor | `skills/critique-microcopy/SKILL.md:14-29` | The frontmatter `checks.scripted` and `checks.judged` lists are not in ascending ID order, while the body says the sweep runs in ascending ID order and every sibling lists its IDs that way. | Fixed in E73's build (2026-10-26): both lists reordered to ascending ID order. No criterion was added, removed, or moved between lanes. |
| R4 | skill-reviewer | minor | `skills/critique-docs/SKILL.md:65` | Only this skill renders the citation of `docs/reference/severity-scale.md` as a link; the six siblings write it as a plain path. | Fixed with V1 in E73's build (2026-10-26); see V1 for which form was kept and why. |
| R5 | skill-reviewer | minor | the seven `SKILL.md` files | The statement of which artifacts a skill claims is an H2 heading in two skills, a bold lead-in in three and plain prose in two. | No change proposed by the reviewer. Recorded as an observation. |
| R6 | skill-reviewer | info | `skills/critique-forms/SKILL.md:7-87` | The frontmatter lists 15 `rubric_sources`, against one or two for every sibling. | No change. `references/FORMS.md` says the list is one entry per publisher, by design. |
| R7 | skill-reviewer | info | the seven `SKILL.md` files | The protocol, output-bounding and delegation sections repeat nearly verbatim across the seven files. | No change. The critic reads only the named skill's own files, so each `SKILL.md` must stand alone. |
| V1 | plugin-validator | warning | the seven `SKILL.md` files | The protocol text cites repository-root paths such as `docs/reference/severity-scale.md` and `contract/critique-contract.schema.json`, while critique-docs once uses the skill-relative form `../../docs/...` for the same file. Whether each form resolves at run time is inferred, not tested. | Fixed in E73's build (2026-10-26): critique-docs's one link, to `docs/reference/severity-scale.md`, now matches the six siblings' plain repository-root path, the minimal change that resolves both R4 and V1 at once. The repository-root form is kept, not the skill-relative one, because every sibling already uses it and it has run in every bench dispatch with no known failure. |
| V2 | plugin-validator | warning | `agents/critique-critic.md:146` | The critic's instructions call `run.model` "this subagent's own pinned model id", but the frontmatter declares no `model`, so the model is whichever one the caller runs. | Fixed in E73's build (2026-10-26): reworded to "the id of whichever model is running this subagent", which matches the frontmatter (no pinned `model` field) without changing what the critic records. |
| V3 | plugin-validator | info | `agents/critique-critic.md:4-6` | `tools` is written as a YAML list, and the validator could not confirm the list form is accepted. | Resolved, no change. The Claude Code subagents documentation says the field takes "a comma-separated string such as `Read, Grep, Bash` or a YAML list". |
| V4 | plugin-validator | info | `agents/critique-critic.md:7-12` | The `metadata` block is not a field Claude Code's agent loader reads. | No change. The loader ignores it and this repository's gate reads it, as designed. |
| V5 | plugin-validator | info | `.claude-plugin/plugin.json:11` | `keywords` is empty, because `library.json` sets none. | Left for the maintainer. The generator copies a `keywords` array from `library.json`, so the fix is one field there, but which keywords to publish is a discoverability choice. |
| V6 | plugin-validator | info | `skills/_template-fixture/`, `skills/_shared/` | Neither holds a `SKILL.md` at `skills/<dir>/SKILL.md`, so neither should be discovered as a skill. | No change, and still inferred. The Claude Code documentation gives the skill location as `skills/<skill-name>/SKILL.md` but does not say whether a deeper `SKILL.md` is discovered, or whether a leading underscore matters. A live install that lists the loaded skills would settle it. |
| V7 | `claude plugin validate` | warning | `.claude-plugin/` | The plugin has no icon. The CLI says the first icon a listing receives cannot be changed later. | Left for the maintainer. An icon is a branding choice, and the first one is permanent. |

## What this run did not check

- **No live install.** Nothing here loaded the plugin into a Claude Code session and listed the skills
  it discovered, so V1 and V6 remain inferences.
- **No triggering measurement.** R1 rests on reading the descriptions and the trigger evals. It does
  not rest on a measured misroute, because running the trigger evals calls a model.
