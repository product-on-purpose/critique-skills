---
title: Gate in CI, worked example
description: A tiny fictional consumer repo wired to fail its build on a severity-4 finding and pass once the finding is fixed, both gated for real
audience: engineer
level: intermediate
---

# Gate in CI, worked example

[Gate in CI](../../docs/how-to/gate-in-ci.md) documents `contract/validate.py --gate` field by field.
This recipe is the same idea worked through one small, fictional repository end to end: a page with a
real defect, the CI job that gates on it, one run that fails the build, and one that passes it after
the fix.

**What's reproducible here and what's authored.** The consumer repo, its page, and the two run
envelopes below are fictional, built for this recipe; no such repository exists. Nothing about that
is hidden. What is real: both envelopes were validated and gated with the exact commands printed
below, against the exact JSON shown, before this page was written, and the exit codes are what
`contract/validate.py` actually returned. The passing envelope is also, separately, exactly what this
repository's own `scripts/checks.py` reports when pointed at the fixed page, verified the same way. So
read the envelope contents as illustration and the exit-code behavior as something you can reproduce
yourself against the same JSON.

## The fictional consumer repo

A small internal site, `northwind-retail/storefront`, with one help page and a CI job that gates its
critique envelope:

```
northwind-retail/storefront/
├── .github/
│   └── workflows/
│       └── critique-gate.yml
├── docs/
│   └── checkout-help.html
└── critique/
    └── checkout-help-envelope.json
```

`docs/checkout-help.html` is the page under review. `critique/checkout-help-envelope.json` is where an
earlier job step (or a committed file, or an artifact store, the same open question
[Gate in CI](../../docs/how-to/gate-in-ci.md#before-you-gate-anything) leaves to your own pipeline) has
already placed a `critique-accessibility` run envelope for that page. The job below starts from the
point that file exists.

## The page, first pass

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Checkout help</title>
</head>
<body>
<main>
<h1>Finish your order</h1>
<p>Review your cart, then confirm the order below. Delivery usually takes three to five business days.</p>
<p>Order total: $84.00, including tax and shipping.</p>
<button class="btn-buy" type="submit"><img src="/icons/arrow-right.svg"></button>
</main>
</body>
</html>
```

The page's one order-submission control is a button whose only content is an icon image with no `alt`
attribute, no `aria-label`, and no visible text anywhere else identifying it. A screen-reader user
reaches this button and gets no name for it at all, on the one page whose entire purpose is completing
the order.

## The CI job

Same job shape as [Gate in CI](../../docs/how-to/gate-in-ci.md#a-worked-github-actions-example)'s own
worked example, a pinned checkout of this library plus one dependency install, adapted to this repo's
own file path:

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
        run: python -m contract.validate critique/checkout-help-envelope.json --gate --threshold 0
```

`--threshold 0` is set explicitly rather than left to fall back to whatever the envelope declares,
because this envelope was not produced by Northwind Retail's own CI; per
[Gate in CI](../../docs/how-to/gate-in-ci.md#threshold-configuration), pass `--threshold` explicitly
whenever the envelope is not yours. A GitHub Actions `run:` step already fails the job on any nonzero
exit code, so nothing beyond this one command is needed to make the job fail or pass with the envelope.

## Run one: the button as shipped, exit 1

`critique/checkout-help-envelope.json` for the page above (illustrative excerpt):

```json
{
  "run": {
    "skill": "critique-accessibility",
    "skill_version": "0.1.1",
    "contract_version": "1.0.0",
    "artifact": "docs/checkout-help.html",
    "artifact_sha256": "5c6e3c1858d06b457a5c18505aa4fbaf4bfe99538e0500993934f8fbcf1bec98",
    "model": "none",
    "timestamp": "2026-08-03T09:00:00Z",
    "rubrics": ["WCAG"]
  },
  "findings": [
    {
      "id": "F-001",
      "criterion": "WCAG-1.1.1",
      "lane": "scripted",
      "severity": 4,
      "location": "\"html > body > main > button > img\", <img> element, line 12",
      "evidence": "<img src=\"/icons/arrow-right.svg\">",
      "violation": "No text alternative is present and the element is not marked decorative. This image is the only content of the page's one order-submission control, so its missing name leaves that control fully unidentifiable to a screen reader.",
      "fix": "Add alt=\"\" to the icon and aria-label=\"Complete purchase\" to the enclosing button, or replace the icon with visible button text.",
      "confidence": "high"
    }
  ],
  "summary": {
    "by_severity": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 1},
    "suppressed_count": 0,
    "gate": "fail",
    "severity_3_threshold": 0
  }
}
```

**On the severity value, specifically.** Every other field in this finding, criterion, location down
to the CSS selector and line number, evidence, and even the violation and fix wording, is exactly what
this repository's own `python skills/critique-accessibility/scripts/checks.py` reports when pointed at
this exact page: it flags the missing text alternative under `WCAG-1.1.1`, at severity 2, the script's
own mechanical rule for a single missing instance
([`references/severity-anchors.md`](../../skills/critique-accessibility/references/severity-anchors.md)).
No severity-4 finding exists anywhere in this repository's own fixtures or bench results yet to draw
one from directly, so the 4 shown here is authored for this recipe, an escalation
`references/severity-anchors.md` explicitly allows as "a finding-level judgment about a specific
artifact, not a property of a criterion," reserved for a defect that makes the artifact "fully
non-functional for a whole class of user." This is that case: the missing name sits on the page's only
control that completes its one task, with no alternative path and no recovery. A real judged-lane
escalation from 2 to 4 for this exact instance is a defensible call, not a mechanical one, which is
exactly why it did not come out of the script.

Validated and gated, from the repository root, against the JSON above:

```
$ python -m contract.validate critique/checkout-help-envelope.json
valid
$ echo $?
0

$ python -m contract.validate critique/checkout-help-envelope.json --gate --threshold 0
valid
$ echo $?
1
```

Exit 1: any severity-4 finding fails the build regardless of the threshold
([Gate in CI](../../docs/how-to/gate-in-ci.md#exit-codes)). The CI job's `run:` step fails on this exit
code with no further wiring needed, and the pull request is blocked.

## The fix

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Checkout help</title>
</head>
<body>
<main>
<h1>Finish your order</h1>
<p>Review your cart, then confirm the order below. Delivery usually takes three to five business days.</p>
<p>Order total: $84.00, including tax and shipping.</p>
<button class="btn-buy" type="submit" aria-label="Complete purchase"><img src="/icons/arrow-right.svg" alt=""></button>
</main>
</body>
</html>
```

`aria-label="Complete purchase"` names the button; `alt=""` marks the now-redundant icon decorative so
assistive technology skips announcing it a second time.

## Run two: after the fix, exit 0

This envelope is not authored. It is exactly what `python skills/critique-accessibility/scripts/checks.py`
reports when pointed at the fixed page above, verified before this page was written:

```json
{
  "run": {
    "skill": "critique-accessibility",
    "skill_version": "0.1.1",
    "contract_version": "1.0.0",
    "artifact": "docs/checkout-help.html",
    "artifact_sha256": "09384ed0160877ff2060c8d5fd27ae8607fe57c1622b8ad3a793a7573ae4eb0d",
    "model": "none",
    "timestamp": "2026-08-03T09:15:00Z",
    "rubrics": ["WCAG"]
  },
  "findings": [],
  "summary": {
    "by_severity": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0},
    "suppressed_count": 0,
    "gate": "pass",
    "severity_3_threshold": 0
  }
}
```

```
$ python -m contract.validate critique/checkout-help-envelope.json
valid
$ echo $?
0

$ python -m contract.validate critique/checkout-help-envelope.json --gate --threshold 0
valid
$ echo $?
0
```

Exit 0: no severity-4 finding, and the severity-3 count (zero) is at or below the threshold. The CI
job's `run:` step passes, and the pull request is unblocked.

## Reading the two runs side by side

| | Run one | Run two |
|---|---|---|
| Artifact | `docs/checkout-help.html`, icon-only button, no accessible name | Same path, button now carries `aria-label` |
| `by_severity["4"]` | 1 | 0 |
| `summary.gate` | `fail` | `pass` |
| `--gate --threshold 0` exit | 1 | 0 |

Nothing about the CI job itself changed between the two runs. Both times it is the same one-line
`python -m contract.validate ... --gate --threshold 0`, reading whatever envelope sits at
`critique/checkout-help-envelope.json` when the job runs. What changed is the page, and therefore the
envelope a `critique-accessibility` run produces against it.

## See also

- [Gate in CI](../../docs/how-to/gate-in-ci.md), the full exit-code table and threshold reference this
  recipe builds on.
- [Severity scale](../../docs/reference/severity-scale.md), what severity 4 means and why it is rare.
- [Dispositions](../../docs/how-to/dispositions.md), what happens after a gate passes, recording a
  human decision on any remaining lower-severity findings.
