# Contributing to critique-skills

This repository ships rubric-cited, machine-parseable critique skills. What makes a skill belong
here, and what a finding has to look like once it exists, is governed by
[`docs/explanation/methodology.md`](docs/explanation/methodology.md). This document is the
contribution process built on top of that; where the two disagree, the methodology is correct (its
own closing line says as much) and this document has a bug.

## Two kinds of contribution

**A new `critique-<domain>` skill.** Goes through the Two-Part Gate
([methodology.md #2](docs/explanation/methodology.md#2-the-two-part-gate)) before anything else:
the framework must evaluate a concrete, inspectable artifact (a finding must be able to name a
location), and a published, citable external standard must exist that the skill operationalizes
(every criterion must trace to a source with a URL or an ISBN). See that section's rejection table
for worked examples of what fails the gate and why. A framework that fails either half does not
belong in this library, independent of how good the resulting critique reads.

**Everything else.** Bug fixes, doc corrections, calibration passes on an already-shipped skill
(see [ADR 0027](docs/internal/decisions/0027-accessibility-location-emission-calibration.md) for
what one of these looks like), and changes to the contract, bench harness, or repo tooling. These
don't go through the Two-Part Gate, since that gate decides whether a new domain belongs in the
library, not whether existing code is correct. They still have to pass the local gate and, if they
touch a rubric, the paraphrase policy, both below.

## How a new skill gets reviewed

A skill contribution is reviewed against
[methodology.md Section 12](docs/explanation/methodology.md#12-contributing-a-skill), in this
order:

1. **Gate.** States the artifact it evaluates and the standard it operationalizes, with a link.
2. **IDs.** Criteria enumerated with permanent, namespaced identifiers
   ([criterion ID format](docs/reference/criterion-ids.md)).
3. **Lanes.** The scripted/judged split is declared, and the scripted lane is actually
   deterministic.
4. **Contract.** Findings conform to the Critique Contract's finding shape, with real locations and
   quoted or measured evidence.
5. **Severity.** Domain anchors are supplied for the shared 0-4 scale
   ([severity scale](docs/reference/severity-scale.md)).
6. **Provenance.** Sources are cited with the correct `operationalization` value, and no source text
   is reproduced (see the paraphrase policy below).
7. **Evidence.** A seeded corpus and a results table exist.

Item 7 is the one the methodology itself flags as most often skipped and least negotiable
(Section 12): "a skill with no measured performance is a draft, not a contribution." This library's
entire claim is that its skills are measured, so an unmeasured skill weakens that claim more than a
missing skill would. Bring a seeded corpus and a results table, or expect the PR to be treated as a
draft rather than a contribution.

## Provenance and the paraphrase policy

Every skill's rubric sources are declared in frontmatter with an `operationalization` value of
`paraphrased`, `open-standard`, or `byor`
([methodology.md #11](docs/explanation/methodology.md#11-provenance-and-intellectual-property)).
Copyrighted rubrics (Nielsen, Williams, Toulmin, NN/g, and similar) are operationalized into
criteria in the library's own original wording, cited by source and page or section, never
reproduced verbatim, and only ever quoted briefly, for orientation, in a references file, never as
the criterion text itself ([ADR 0006](docs/internal/decisions/0006-copyright-paraphrase-policy.md)).

**A contribution that pastes source text, verbatim or paraphrased closely enough to raise the same
question, from a copyrighted rubric will be rejected outright, not sent back for revision.** This is
the one review item with no remediation path short of rewriting the criterion from scratch in your
own words.

## Running the gate locally

Before opening a PR, run the same conformance gate CI runs:

```
npm run check
```

which is equivalent to `node scripts/check.mjs`. It requires a local checkout of
`agent-skills-toolkit` next to this repository, or an `AGENT_SKILLS_TOOLKIT` environment variable
pointing at one:

```
git clone https://github.com/product-on-purpose/agent-skills-toolkit.git ../agent-skills-toolkit
```

See [`AGENTS.md`](AGENTS.md) ("Checks") for the full command table CI runs, one command per job
(conformance, unit-python, unit-node, schema, corpus, drift, audit): run whichever ones your change
touches before opening the PR, not only the conformance gate.

## Generated files: edit the source, not the output

`.claude-plugin/plugin.json` (generated from `library.json`), `INDEX.md`, and the content inside the
`<!-- bench-results:start/end -->` and `<!-- skill-catalog:start/end -->` markers in `README.md` and
`bench/README.md` are all generated. Edit the source, `library.json`, a skill's frontmatter, a bench
result envelope, and regenerate:

```
npm run gen
```

CI's `drift` job (`npm run gen -- --check`) fails a PR that hand-edited a generated file instead of
its source.

## Commit messages

Use Conventional Commits style (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`) so the
history stays scannable. This is not yet CI-enforced here, so a differently formatted commit will
not block a PR, but match the style where you can.

## Questions

Open an issue. `AGENTS.md` is the agent-facing navigation entrypoint if you want to see how the
rest of the repository's own docs are organized before asking.

---

*By contributing, you agree that your contribution is licensed under Apache-2.0 (code) or CC-BY-4.0
(bench corpus content), matching [`LICENSE`](LICENSE) and `bench/README.md`.*
