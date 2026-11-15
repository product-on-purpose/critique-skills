---
title: Cross-library composition, worked example
description: A pm-skills PRD critiqued by critique-clarity in one live, dated run, through dispositions to a revision brief a person acts on, including what the run got wrong
audience: both
level: intermediate
---

# Cross-library composition, worked example

The [README](../../README.md#-the-family) says the Product on Purpose libraries compose along one
value chain: think with one, make with another, judge the result with this one. This recipe runs
that chain once, across a repository boundary. A product requirements document (PRD) from
[`pm-skills`](https://github.com/product-on-purpose/pm-skills) goes through one live
`critique-clarity` run, then a disposition log, then a revision brief that a person acts on.

**What the run showed.** The chain ran end to end: the skill accepted the sibling's PRD, emitted a
contract-valid envelope, and the brief writer turned the accepted findings into a revision brief.
The run also showed two limits a reader should know before trusting the numbers.

- **8 of the 29 findings shown misread markdown tables.** The scripted lane read table rows as prose
  sentences and paragraphs, so it reported, for example, a four-row table as a "104-word sentence".
  This is [E82 (tables read as prose)](../../docs/internal/backlog/enhancements.md), filed from this
  run.
- **No judged finding is visible.** The judged lane ran and found 5 severity-2 findings, but the
  output bound keeps only five findings below severity 3, and scripted findings filled every slot.
  This is evidence for [E80 (should the output bound rank by lane)](../../docs/internal/backlog/enhancements.md).

Both limits are reported here rather than worked around, because an example that hides how a skill
behaves on real input is the asserted claim this recipe exists to replace.

**A same-organization demonstration.** Both libraries are maintained by the same organization. This
recipe shows the chain works between them. It does not satisfy the v1.0 criterion of an external
consumer, which needs a project outside this organization to adopt the library.

## What is real here and what is authored

| Part | Status |
|---|---|
| `prd.md` | Real: an extract of a file committed in `pm-skills` at tag `v2.35.1`, byte for byte, with the source named below |
| `envelope.json` | Real: the unedited output of one live `critique-clarity` run on 2026-11-15, one attempt |
| `provenance.json` | Real: the run's date, CLI version, model, instruction, and the input's source and hashes |
| `dispositions.json` | Authored for this recipe by Claude, as one plausible reviewer's call. Every note says so, because the contract has no field for who decided |
| `revision-brief.json` | Real: the output of `revision_loop.py brief` on the two files above; re-running the command reproduces it bit for bit |

## Step 1: the sibling's output

`pm-skills`'s `deliver-prd` skill writes PRDs, and `critique-clarity`'s Artifact claim names PRDs
among the documents it reviews, so the pairing needs no new skill text on either side.

The input is `library/skill-output-samples/deliver-prd/sample_deliver-prd_storevine_sms-optin.md`
in `pm-skills` at tag `v2.35.1` (file sha256 `cdcba3b9…31e5fe`). `prd.md` is its Output section,
source lines 70 to 159, verbatim, with the sample's Apache-2.0 attribution comment kept at the top.
The sample's Scenario and Prompt sections, and its Appendix, are left out: they describe the sample,
not the product.

Two facts about the input matter:

- **It was produced by `deliver-prd` 2.2.0.** At the tag, the skill is at 3.1.0, so a fresh PRD
  from it may be shaped differently.
- **`pm-skills` labels this sample "a written worked example".** Its own note says the sample is not
  a transcript of an executed run. It is still the sibling's committed output, which is what this
  recipe needs, but it is not a live `deliver-prd` run.

## Step 2: the critique run

This step calls a model, so it costs one skill run. It ran once, on 2026-11-15, after the
maintainer's recorded go. The run used the benchmark harness's transport: a staged copy of the
plugin, Claude Code's isolation flags, a fixed tool allowlist, and a working directory holding only
`prd.md`. It ran under Claude Code 2.1.325 (the benchmark pins 2.1.300) on `claude-sonnet-5`, and
took one attempt. To run the same thing yourself, from a folder holding only a copy of `prd.md`:

```bash
claude --plugin-dir <path-to-critique-skills> --model claude-sonnet-5 \
  --setting-sources "" --strict-mcp-config \
  --allowedTools Read,Bash,Glob,Grep,Task,Skill \
  -p "Use the critique-clarity skill to critique prd.md. Follow the skill's protocol exactly, including running its scripted lane. Output ONLY the final run envelope: one JSON object, with no prose before or after it and no markdown code fence."
```

**A re-run will not return identical findings.** The scripted lane is deterministic, so its findings
repeat exactly. The judged lane is a model's reading, so its findings change in wording and
sometimes in which criteria fire. `critique-clarity`'s measured consistency on Sonnet is in
[`bench/results/`](../../bench/results/).

### What came back

```
summary.by_severity: severity 3: 24, severity 2: 49 (73 found)
findings shown: 29 (every severity-3 finding, plus five severity-2 findings)
summary.suppressed_count: 44
gate (threshold 0): fail, exit 2
```

Every finding shown is from the scripted lane. You can confirm that, and recover the judged lane's
share, without calling a model. Run the scripted lane alone from `skills/critique-clarity/`:

```bash
python scripts/checks.py --repo-root ../../examples/recipes/cross-library-prd \
  ../../examples/recipes/cross-library-prd/prd.md
```

It reports 68 findings (24 at severity 3, 44 at severity 2) and the same 29 findings shown. The live
run found 73. The difference is 5 severity-2 findings, which can only have come from the judged
lane, and all 5 were suppressed by the output bound. Their content is not recoverable from the
envelope.

The 8 table-sourced findings are F-001, F-007, F-012, F-013, F-015, F-024, F-025 and F-026: each
one's evidence is the text of a markdown table. Six of them are at severity 3, so they alone push
the gate past any threshold below six.

## Step 3: dispositions

A person decides on each finding: accept, reject, or defer. `dispositions.json` is authored for
this recipe, and each note begins by saying so. Its decisions:

| Decision | Findings | Why |
|---|---|---|
| Accept (4) | F-002, F-003, F-014, F-028 | Two scope sentences hold lists in prose form, and one sentence never says who retains consent records |
| Defer (4) | F-004, F-005, F-006, F-029 | The fix depends on the engineering owner or on legal |
| Reject (21) | the 8 table findings, 4 paragraph findings, 8 transition findings, F-027 | Tables read as prose; bold run-in labels read as opening sentences; labeled reference items that need no transitions; a natural passive |

Rejecting a finding is the disposition step working as designed. The brief carries only what a
person accepted, so a false positive costs a reader one decision, not a wrong edit.

## Step 4: stop-check and revision brief

These commands call no model. Run them from `examples/recipes/cross-library-prd/`:

```bash
python ../../../skills/_shared/revision_loop.py stop-check --envelope envelope.json --iteration 1
python ../../../skills/_shared/revision_loop.py brief --envelope envelope.json \
  --dispositions dispositions.json --out revision-brief.json
```

The stop-check returns `"decision": "continue"`, because 24 findings at severity 3 remain and this is
iteration 1 of at most 3. The brief writer checks that `dispositions.json` binds this exact envelope
by its sha256, then writes `revision-brief.json` with 4 items, one per accepted finding, each with
its criterion, location and fix. All three documents validate:

```bash
python -m contract.validate examples/recipes/cross-library-prd/envelope.json
python -m contract.validate examples/recipes/cross-library-prd/dispositions.json
python -m contract.validate examples/recipes/cross-library-prd/revision-brief.json
```

## Step 5: a person acts on the brief

The brief goes to the PRD's owner, the person who asked `deliver-prd` for it. They revise the PRD
themselves, or re-run `deliver-prd` with the brief's items in their prompt, on their own authority.
`critique-skills` never writes to the PRD: no step in this recipe opens the sibling's file for
writing, and the revision loop's
[boundary](../../docs/explanation/revision-loop-boundary.md) holds across the repository line as it
does inside one. A second iteration would critique the revised PRD and compare the two runs with
`revision_loop.py compare`.

## Keeping this evidence honest

The envelope is dated and names the CLI version and model it ran under, in `provenance.json`. That
is the freshness check the maintainer chose for this recipe: a reader can tell a stale run from a
current one by its date and versions, and no automated test re-runs it. When either library moves,
this run stays a record of what happened on 2026-11-15, not a claim about today.
`.gitattributes` marks the folder `-text`, so the hashes that bind its files to each other hold on
every platform.
