# The frozen baseline

Every skill is compared against a generic prompt on the same corpus, on the same pinned models
(docs/explanation/methodology.md section 8, "Baseline comparison"; bench/README.md, "Baseline
comparison (next stage)"). This directory holds the two frozen artifacts that comparison rests on,
plus the deterministic code that connects them to the contract:

- [`prompt.txt`](prompt.txt): the exact prompt text, unchanged for the life of v0.1.0.
- [`postprocess.py`](postprocess.py): the documented, fixed rule that maps the model's free-text
  response into a contract-valid run envelope carrying `skill: "baseline-generic"`.
- [`tests/`](tests/): unit tests for `postprocess.py`.

**What this directory does not do.** It does not call a model. Obtaining a raw response by running
`prompt.txt` against a pinned model tier is the P3 baseline runner's job, described below as an
interface this directory's code satisfies, not as code this directory ships. `bench/generator/` and
`bench/metrics/` are already built and require no model call; the baseline is the one part of the
bench that necessarily does, because it is a comparison against what an unstructured model response
looks like.

## Why the prompt is shaped the way it is

`prompt.txt` asks a model to critique a document with no rubric, no criteria, and no severity scale:
it is deliberately the least accountable thing this library ever asks a model to do, because that is
the comparison point every skill has to beat. The one piece of structure it does require, four
labeled lines per problem, is not a rubric. It exists because a finding with no location cannot be
scored at all (bench/README.md, "Unresolvable locations": "a skill that cannot say where has not made
a falsifiable claim"), and a comparison against a baseline that could not be scored would not be a
comparison. Requiring `Location`, `Evidence`, `Problem`, and `Fix` on their own labeled lines is the
minimum structure that keeps the baseline scoreable by the same code path as every skill, without
handing it anything resembling a rubric.

Changing the prompt text, in any way, after the first published run invalidates every existing
baseline comparison (bench/README.md says so explicitly) and requires a new run set. If the prompt
ever needs to change, bump `BASELINE_VERSION` in `postprocess.py` in the same change.

## The post-processing rule, and what is fixed policy versus what is parsed

`postprocess.postprocess(raw_response, *, artifact, artifact_sha256, model, timestamp)` is a pure
function of the model's raw text plus the run identity the caller already knows. It never opens a
file and never calls a model.

Parsing is generous about whitespace and line wrapping (a field's value can continue onto
unlabeled following lines) but strict about content: a block missing any of the four required labels
is dropped rather than guessed at, so a malformed response never turns into a fabricated finding.
`"No problems found."`, matched exactly, produces zero findings.

Several fields in the resulting envelope are not present anywhere in the model's text at all, because
the prompt never asks for them. These are fixed policy constants, named at their definition in
`postprocess.py`, not inferred from what the model wrote:

| Field | Value | Why fixed rather than parsed |
|---|---|---|
| `criterion` | `BASELINE-GENERIC` | The baseline has no rubric to cite a criterion from; `BASELINE` is its own namespace, existing only so a schema-valid finding can name something. |
| `severity` | `3` (major) | v0.1 metrics do not score severity agreement (bench/README.md, "What the bench does not measure"), so this choice affects only `summary.gate` and `summary.suppressed_count`, never recall, precision, or consistency. |
| `confidence` | `medium` | Neutral default for a `judged`-lane finding; `lane` can never be `scripted` here, since nothing about the baseline is deterministic. |
| `run.skill` | `baseline-generic` | The contract's own reserved example (`critique-contract.schema.json`, `run.skill`). |
| `run.skill_version` | `BASELINE_VERSION` | Bumped only when `prompt.txt` or the mapping rule changes. |
| `run.rubrics` | `["BASELINE"]` | The one namespace every baseline finding's criterion belongs to. |

Every parsed field (`location`, `evidence`, `violation`, `fix`) is sanitized before it reaches the
envelope: U+2014 and U+2013 are replaced with `" - "` (the model was never told the contract's house
style, so this rule enforces it on the model's behalf), internal whitespace is collapsed, and an
overlong field is truncated to its schema maximum. A truncated but contract-valid envelope is
preferred to a faithful-but-invalid one.

Output bounding (methodology section 7) is applied the same way a skill applies it: every severity 3
and 4 finding is kept, plus at most five below that threshold. Because every baseline finding is
severity 3 by fixed policy, this never actually suppresses anything today; the code still applies the
rule rather than assuming the constant will always make it moot.

## Runner spec: how P3 invokes this (interface, not code)

The judged-lane runner that calls a real model is S-03/S-06 scope and is built in a later phase
(bench/run_bench.py's own docstring: "The judged-lane runner itself is S-03 (bench-harness) and S-06
(critic subagent) scope"). What follows is the interface this package's code satisfies, frozen here so
that stage can be built against it without re-opening the mapping rule.

1. **Obtain the raw response.** Invoke `prompt.txt`'s exact text against a pinned model tier, with the
   artifact as the only other input, through `critique-critic` where subagents are available
   (methodology section 7, "Clean-context critique"), or directly against the model API otherwise. No
   rubric, no criterion list, and no prior critique are ever added to the prompt; doing so would stop
   this being a baseline.
2. **Call `postprocess()`.** Pass the raw text plus the run identity the runner already has: the
   artifact's repository-relative path, its sha256 (computed from the same bytes `bench/generator`
   wrote and `bench/metrics` will re-verify), the pinned model id, and an RFC 3339 UTC timestamp.
3. **Write the envelope.** The returned dict is already contract-valid (see `tests/test_postprocess.py`,
   which checks every fixture against `contract.validate.validate_document`); write it to
   `bench/results/<run-set>/` beside the skill envelopes it will be compared against.
4. **Score it.** `python -m bench.metrics score` reads a `baseline-generic` envelope through exactly
   the same code path as any skill's: same resolver, same tolerance, same assignment
   (bench/README.md, "Baseline comparison (next stage)"). `bench/report.py`'s baseline-comparison table
   is computed by matching `(domain, model)` pairs where one entry carries
   `skill: "baseline-generic"`, so no separate baseline-specific code exists downstream of this
   directory at all.

`k` (the repeat count) and the pinned model tiers are P3 concerns, not this module's: `postprocess()`
is called once per raw response, however many times the runner collects one.

## Convenience CLI

`python -m bench.baseline postprocess --raw RESPONSE.txt --artifact bench/corpus/toy/toy-001.md
--artifact-file bench/corpus/toy/toy-001.md --model claude-sonnet-4-5-20250929 --timestamp
2026-07-31T00:00:00Z --out envelope.json` maps one already-saved raw response into an envelope file,
for reproducing or spot-checking the mapping rule by hand. It is not the P3 runner (step 1 above,
obtaining the raw response, is not this CLI's job); it starts from step 2.
