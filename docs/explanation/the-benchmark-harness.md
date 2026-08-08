---
title: The benchmark harness, and why it does not affect you
description: What bench/run_bench.py is, why it exists, and why using this plugin never requires an API key
audience: both
level: beginner
---

# The benchmark harness, and why it does not affect you

## Start here: do you need an API key?

**No.** Not to install this plugin, not to run any skill, not to use anything it produces.

You need one thing to use this library: `pip install "jsonschema>=4.20,<5"`. That is a small
open-source package for checking that data matches a schema. It is not a Claude thing, it costs
nothing, and it talks to no one.

There is exactly one file in this repository that can use an API key, `bench/run_bench.py`, and it
is a **maintainer tool for re-checking our own published numbers**. It is not part of the plugin. It
is not on any path a skill takes. You can delete it and every skill still works.

If that answers your question, you can stop reading. The rest is for people who want to know what
that file is and why a library about honest measurement keeps one around.

---

## The short version

This library publishes numbers about how well its own skills perform. `run_bench.py` is the program
that produces those numbers, so that someone who does not trust us can run it and check.

It needs a model for part of its job, because part of what it measures is a judgment call that only
a model can make. That is the whole reason an API key enters the picture at all, and it enters it
only for the person re-running the measurement, never for the person using the skills.

## Why skills need no key but the benchmark does

This is the distinction that makes everything else make sense.

**When you use a skill, you are already talking to a model.** You are in Claude Code, or another
agent, and it is reading the skill's instructions and following them. The skill is a set of
instructions, not a program that calls anything. There is nothing for it to authenticate with,
because it never places a call. It is being *read* by the model you are already using.

**When the benchmark runs, nobody is there.** It is a Python script, running on its own, possibly on
a build machine at three in the morning. When it needs a model's judgment, it has to go and get one.
A Python script cannot borrow your Claude Code login, any more than a script you wrote could stream
music using your Spotify subscription. Different program, different door. The door a program uses is
the API, and the API asks for a key.

So the key is not a property of the measurement. It is a property of **having written the
measurement as a standalone program**. Hold that thought, because it is the thing that can change.

---

## What the harness actually does

Seven steps. Two of them touch a model.

| Step | What happens | Model needed? |
|---|---|---|
| 1 | Work out the job list: which skills, which test files, which model tiers, how many repeats | no |
| 2 | Run the **scripted half** of each skill: the plain-Python checks in `scripts/checks.py` | no |
| 3 | Run the **judged half**: the criteria that need reading for meaning | **yes** |
| 4 | Merge both halves and apply the output-bounding rule over the combined pool | no |
| 5 | Validate the assembled record against the frozen contract, refusing to write an invalid one | no |
| 6 | Run the **baseline**: a plain "critique this" prompt with no skill, on the same files | **yes** |
| 7 | Score everything into `results.json`, which generates the published tables | no |

Five of seven steps are ordinary Python with no network call.

### Why steps 3 and 6 cannot be scripted away

**Step 3.** Of the 96 criteria across the six skills, 42 are scripted and 54 are judged. A scripted
criterion is one a program can decide alone: contrast ratios, heading depth, sentence length,
whether an `alt` attribute exists. A judged criterion needs someone to read for meaning: whether an
argument's warrant is missing, whether an error message tells you what to do next, whether a page is
really a tutorial. There is no clever way to compute that. More than half the library's criteria are
in this category by design, because the alternative is only shipping criteria a regex can decide,
which would be a much smaller and much less useful library.

**Step 6.** The baseline is the comparison that makes any of the numbers mean something. It answers
"does a rubric-cited skill actually beat just asking a model nicely?" You cannot answer that without
asking a model nicely. The baseline is definitionally a model call.

---

## Why this file exists at all

The honest history, because it explains why the file feels vestigial.

**The published numbers were not produced by this script.** They came from a Claude Code multi-agent
workflow: 460 measurement runs, one fresh clean-context subagent each, orchestrated live in a
session over two days. That happened, it worked, and the resulting records are committed under
`bench/results/runs/`.

Then the project audited itself and found something uncomfortable: **nothing committed to this
repository could have produced those numbers.** There was no program in the repo that called a
model. The measurements existed. The machine that made them did not.

For a library whose entire pitch is "we publish our measured performance rather than asserting it,"
that is a real hole. If nobody outside the project can re-run the measurement, "measured" quietly
degrades into "we measured it once, please trust us."

`run_bench.py` was built to close that hole. It is the answer to "prove it."

**Its honest status today: it has never been run live. Not once.** It is insurance, not machinery.
Its value is entirely that someone *could* check us, which is real, but nothing in the project
depends on it running.

---

## How to run it

**There is no API key anywhere in this, and there is no decision left to make.** As of v0.1.4 the
harness reaches the model through the Claude Code CLI, so it authenticates from a Claude
subscription exactly the way you already do.

### On your own machine

```
python bench/run_bench.py --skills critique-clarity --k 1 --tiers haiku --out-dir /tmp/bench-run
```

Needs `claude` on PATH and logged in, which it is if you use Claude Code. No secret, no token, no
CI configuration. This is the lowest-ceremony way to re-verify anything.

### On a build machine

`bench.yml` installs the CLI and passes a `claude setup-token` credential from the
`CLAUDE_CODE_OAUTH_TOKEN` repository secret. Probed on a clean `ubuntu-24.04` runner on 2026-08-08:
it authenticates and answers.

This is the mode the public roadmap's "first live `bench.yml` dispatch, on infrastructure the
maintainer does not control end to end" refers to. Running locally cannot satisfy that item, since
the whole point is that the machine is not the maintainer's.

**The token is a real credential.** Long-lived, tied to a personal subscription rather than to the
repository, and granting whatever that subscription grants. Rotate with `claude setup-token` again
and re-set the secret.

### Without running anything

```
python bench/run_bench.py --skills all --k 5 --dry-run
```

Plans the entire grid and prints every cell it would run, **without calling any model or needing the
CLI at all**. Useful for checking the wiring after changing a skill or the corpus.

### What is still true about the numbers

The published figures came from a live multi-agent workflow, not from this harness, and
[`bench/results/README.md`](../../bench/results/README.md) says so under Provenance. Moving the
transport to Claude Code narrows that gap but does not close it: the judged lane here is still a
prompt this harness assembles, rather than the shipped skill being run. Closing that is the
remaining half of [ADR 0030](../internal/decisions/0030-replace-the-api-key-in-the-bench-harness.md).

## Technical reference

### Invocation

```
python bench/run_bench.py [--skills all] [--k 5] [--tiers ""] [--dry-run] [--out-dir PATH]
```

| Flag | Meaning |
|---|---|
| `--skills` | Comma-separated skill names, or `all`. Resolved against `library.json` |
| `--k` | Repeats per (skill, artifact, tier) cell. The published grid used 5 |
| `--tiers` | Comma-separated tier aliases. Blank means the pinned tiers from `measurement-manifest.json` |
| `--dry-run` | Plan and print the grid; import nothing, call nothing, require no key |
| `--out-dir` | Where new records are written. Never implied, always chosen by the caller |

### Where its inputs come from

Nothing is hardcoded. The grid is derived from what the repository already declares:

- **Skills** from `library.json`
- **Artifacts** from `bench/corpus/<domain>/*.manifest.json`
- **Model tiers** from `bench/results/measurement-manifest.json`, the same file
  [ADR 0023](../internal/decisions/0023-v0.1.0-measurement-basis-two-pinned-tiers-k5.md) records the
  measurement basis in
- **Judged criteria** from each skill's `SKILL.md` frontmatter, restricted to `checks.judged`, since
  the scripted criteria are already covered by step 2

### Safety properties worth knowing

- **It never touches existing evidence.** `bench/results/runs*/` is immutable. The harness never
  reads those files and never writes to that directory; new records go to `--out-dir`.
- **It never writes an invalid record.** Every assembled record is validated against the contract
  first, and a failure means nothing is written.
- **A live run cannot happen by accident.** The script checks for the Claude Code CLI up front
  and stops with a message naming the remedy, rather than planning a grid and failing partway
  through it.
- **`--dry-run` provably imports nothing.** A test poisons `sys.modules["anthropic"]` and asserts
  the dry-run path still exits 0.

### Dependencies

| File | Contents | Who needs it |
|---|---|---|
| `requirements.txt` | `jsonschema` | **Everyone**, and it is the whole list |
| `requirements-dev.txt` | adds `pytest` | Contributors running the test suite |

There is no third file and no API client. As of v0.1.4 the harness reaches the model through the
Claude Code CLI, so the `anthropic` package and the `requirements-bench.txt` that carried it are
both gone.

The obvious command, `pip install -r requirements.txt`, installs one small open-source package and
nothing else.

---

## What this file is not

- **Not part of the plugin.** No skill, no command, and no subagent reaches it.
- **Not required for CI.** Every other job in `ci.yml` needs `jsonschema` and nothing more.
- **Not how the published numbers were made.** See
  [`bench/results/README.md`](../../bench/results/README.md) under Provenance, which states plainly
  that a re-run through this harness should be expected to differ from the published figures.
- **Not a thing you have to think about.** If you came here worried that this library wants an API
  key from you: it does not, and nothing about it ever will.
