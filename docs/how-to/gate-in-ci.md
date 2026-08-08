---
title: Gate in CI
description: Wiring a consumer repository's CI to fail a build on severity findings using the validator's gate mode
audience: engineer
level: intermediate
---

# Gate in CI

This page is for a repository that consumes critique-skills output, not for this repository's own
CI (see `AGENTS.md` for that). It shows how to fail a build on severity findings using
`contract/validate.py`'s `--gate` mode. For the schema and rules behind the exit codes below, see
[Critique contract](../reference/critique-contract.md).

## Before you gate anything

Gating needs a run envelope: JSON conforming to `#/$defs/envelope` in
`critique-contract.schema.json`, produced by running a `critique-<domain>` skill (or the
`critique-critic` subagent) against your artifact and saving its output. This page starts from the
point where that file already exists at a known path in your workspace, for example
`critique/prd-envelope.json`. How it gets there, committed, produced by an earlier job step, or
fetched from an artifact store, is a decision for your own pipeline.

## Exit codes

`python -m contract.validate <file> --gate [--threshold N] [--strict]` computes its exit code from
the envelope's `summary` object alone.

| Exit | Condition | What it means for your build |
|---|---|---|
| 0 | Clean: no severity 4, and severity-3 count at or below the threshold | Pass the job |
| 1 | Any severity 4 | Fail the job: the artifact has a critical defect |
| 2 | Severity-3 count above the threshold | Fail the job: too many severity-3 defects |
| 3 | Input is not a contract-valid document | Fail the job, but treat this as a pipeline problem, not an artifact defect; the envelope itself is malformed |
| 4 | Usage error: bad arguments, or a file that cannot be read or parsed | Fail the job; check the command and the file path |

Exit 1 takes precedence over exit 2, so a run with both a severity-4 finding and an over-threshold
severity-3 count exits 1. Without `--gate` the CLI exits 0 for a valid document and 1 for an invalid
one; pointing `--gate` at a disposition log is a usage error (exit 4), since a disposition log has
no `summary` and therefore no gate verdict to report. A GitHub Actions `run:` step already fails on
any nonzero exit code, so wiring the gate needs nothing beyond running the command; the table above
is for reading the job log afterward.

## A worked GitHub Actions example

The validator ships inside the critique-skills repository itself, not as a separate package, so a
consumer's CI checks out a pinned copy of it the same way this repository checks out
`agent-skills-toolkit` in its own CI (`.github/workflows/ci.yml`, job `conformance`). Pin `ref` to a
released tag, `v0.1.0` once critique-skills is tagged, or a specific commit before then; a moving
branch is not reproducible.

```yaml
name: critique-gate

on:
  pull_request:
    branches: [main]

jobs:
  critique-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - name: Checkout critique-skills (pinned)
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          repository: product-on-purpose/critique-skills
          ref: v0.1.0
          path: .critique-skills

      - name: Setup Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: '3.12'

      - name: Install the validator's one runtime dependency
        run: pip install "jsonschema>=4.20,<5"

      - name: Gate on the critique envelope
        env:
          PYTHONPATH: ${{ github.workspace }}/.critique-skills
        run: python -m contract.validate critique/prd-envelope.json --gate --threshold 0
```

`contract/validate.py`'s only runtime dependency is `jsonschema`, and installing it directly is
still the leanest thing to do. As of 2026-08-07 `requirements.txt` also contains nothing else: the
`anthropic` package moved to `requirements-bench.txt`, which only someone re-running this
repository's benchmark needs. Either command now gets you the same one package. `PYTHONPATH` points at the pinned checkout so
`python -m contract.validate` resolves as a package without installing anything into your own
repository. This shape, running the module against a path outside the checkout while
`PYTHONPATH` points at it, was verified directly in this repository before writing this page.

## Threshold configuration

The default severity-3 threshold is 0: any severity-3 finding fails the gate unless you say
otherwise. Two independent knobs set it.

**`--threshold N`** on the command line overrides whatever the envelope carries, for that one
invocation. Using the worked example from [Critique contract](../reference/critique-contract.md#envelope-walkthrough)
(one severity-3 finding, `severity_3_threshold: 0` in the envelope):

```
$ python -m contract.validate critique/prd-envelope.json --gate
valid
$ echo $?
2

$ python -m contract.validate critique/prd-envelope.json --gate --threshold 1
valid
$ echo $?
0
```

**`summary.severity_3_threshold`**, stored on the envelope itself, is what the exit code falls back
to when `--threshold` is not given. Storing it there is what keeps the exit code computable from
`summary` alone. But the thing that writes that value is the skill under test, and a run may declare
a threshold generous enough to pass itself; the counts cannot be faked, since the validator
reconciles them against `findings[]`, but the pass mark can be. When a gate passes only because of
an envelope's own declared threshold, the validator prints a warning naming the threshold and the
count it excused. `--strict` promotes that warning to an error (exit 3).

**Pass `--threshold` explicitly whenever the envelope is not yours.** A consumer repository is
almost always gating on someone else's envelope, so the worked example above passes `--threshold 0`
rather than trusting whatever the producing skill wrote. Add `--strict` to the command if you want
any self-declared-threshold pass caught outright rather than logged as a warning.

## See also

- [Critique contract](../reference/critique-contract.md), the full field and rule reference the
  exit codes above are drawn from.
- [Severity scale](../reference/severity-scale.md), what severities 0 through 4 mean.
- [Dispositions](dispositions.md), recording accept, reject, or defer once the gate has run.
