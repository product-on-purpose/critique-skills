---
title: critique-docs worked example
description: A walkthrough of critiquing one how-to page against the Diataxis framework with critique-docs, reproducing the scripted lane yourself, and reading a filled-in disposition log
audience: both
level: beginner
---

# critique-docs worked example

This is one complete pass through `critique-docs`: an artifact, a critique of it, and the human
decisions that came after. If you are a PM, a technical writer, or anyone deciding whether to trust
this skill before pointing it at your own documentation set, this page is the place to see what it
actually produces first.

## What the artifact is

`artifact.md` in this folder is a short markdown how-to page, "Reset your account password." It
declares itself `mode: how-to` in its frontmatter and lays out three steps: open account settings,
enable two-factor authentication, choose a new password. It is a documentation page, not a live
docs site; nobody rendered it or clicked through it to produce the findings below, it is text a
critic reads and reasons about against the Diataxis framework, the same way it is the kind of page
this skill is built to review before it ships to a docs tree.

It is copied verbatim from `skills/critique-docs/examples/docs-golden-02-mode-and-goal.md`, one of
this skill's own validated golden fixtures, so this folder is self-contained: everything needed to
reproduce what follows is here, byte for byte identical to its source (confirmed by matching
`artifact_sha256` below).

Of `critique-docs`'s four golden fixtures, this one was chosen because it is the richest: it is the
only one that produces both a scripted finding and a judged finding, at two different severities,
on a failing gate. The other three either pass clean (`docs-golden-03-clean.md`, a reference page,
zero findings), carry two scripted findings only (`docs-golden-01-heading-and-nav.md`), or carry one
judged finding only (`docs-golden-04-explanation-context.md`).

## Honesty labeling

Two different things are true about the findings below, and this page keeps them apart:

- **Scripted lane, bit for bit reproducible.** One finding comes from `scripts/checks.py`, a
  deterministic script. Run the exact command below yourself and you get the exact JSON below,
  every time, on any machine. This was verified by actually running the command against the copy of
  the artifact in this folder, not typed from memory.
- **Judged lane, curated from a validated golden fixture.** One finding comes from a model reading
  the page against the Diataxis framework, the same four-pass protocol a live `critique-docs` run
  follows. It is not something this page ran live and pasted in; it is copied verbatim from this
  skill's own golden envelope (`skills/critique-docs/examples/golden-02.json`), a fixture that
  passed `python -m contract.validate` before it was accepted into the skill's test suite. A live
  judged-lane run against the same artifact should land on the same criterion and severity, but the
  exact wording of `violation` and `fix` can vary run to run, the way any model output does.

Nothing on this page is authored content presented as a live run. Where a claim is reproducible, the
command to reproduce it is given. Where it is curated, that is stated plainly, right next to it.

## Running the scripted lane yourself

From the repository root:

```
python skills/critique-docs/scripts/checks.py examples/docs/artifact.md
```

This is what that command actually printed when this example was built:

```json
{
  "findings": [
    {
      "confidence": "high",
      "criterion": "DIATAXIS-MODE",
      "evidence": "Because two-factor authentication protects the account from password reuse elsewhere, we recommend turning it on now.",
      "fix": "Rewrite the sentence in the page's own declared mode's register, or move this content to a page in the mode it actually belongs to.",
      "id": "F-001",
      "lane": "scripted",
      "location": "Step 2: Enable two-factor authentication, list item 3",
      "severity": 2,
      "violation": "This sentence opens with a lexical marker belonging to a different mode's register than this page's declared how-to mode."
    }
  ],
  "run": {
    "artifact": "examples/docs/artifact.md",
    "artifact_sha256": "39ef4cd8fe88e52eb2e2862774b5957bee5c609ca545be9a0c64edae81d1f4a3",
    "contract_version": "1.0.0",
    "model": "none",
    "rubrics": ["DIATAXIS"],
    "skill": "critique-docs",
    "skill_version": "0.1.0",
    "timestamp": "2026-08-04T04:29:59Z"
  },
  "summary": {
    "by_severity": {"0": 0, "1": 0, "2": 1, "3": 0, "4": 0},
    "gate": "pass",
    "severity_3_threshold": 0,
    "suppressed_count": 0
  }
}
```

Only your `timestamp` will differ; everything else, including `artifact_sha256`, reproduces exactly
because the scripted lane is a deterministic pattern match over the page's own frontmatter and
sentence structure, not a model call. This is the same finding as `F-002` in the full envelope below
(`envelope.json`), field for field: same criterion, same location, same evidence, same violation,
same fix. The ID differs only because the scripted lane numbers findings within its own run, while
the full envelope numbers all findings, both lanes, together, in the skill's fixed sweep order.
Content, not the label, is the reproducible part.

**Worth noticing on this artifact in particular:** the scripted lane alone reports `"gate": "pass"`,
because a single severity-2 finding does not clear the default severity-3 gate threshold. The full
envelope's gate is `"fail"`. That gap exists because the finding that actually fails the gate,
`F-001` below, is judged-lane only; a scripted-only pass on this page would hand back a false
"pass" on the one problem that matters most. This is exactly why `critique-docs` runs both lanes by
default rather than treating the scripted lane as a cheaper substitute for the full critique.

The scripted lane only ever covers three of this skill's nine criteria
(`DIATAXIS-HEADING-DEPTH`, `DIATAXIS-MODE`, `DIATAXIS-NAV-LENGTH`); that is why one command run
produces one finding here, not two.

## Running the full critique

Inside a Claude Code session with this plugin installed, the natural way to ask for the full
critique, both lanes, is to just say so:

> Critique this with critique-docs.

or, pointed at this file directly, without naming the skill at all:

> Give this how-to page a quality check before it ships: `examples/docs/artifact.md`.

Either phrasing matches this skill's own trigger description, so it fires without you having to name
`critique-critic` yourself. Under the hood, `critique-docs`'s `SKILL.md` hands the artifact to the
`critique-critic` subagent, which runs in a fresh context that has never seen this page or any
framing about it, sweeps all nine criteria in fixed order, runs `scripts/checks.py` itself for the
scripted lane, and returns one contract-valid run envelope, the same shape as `envelope.json` in
this folder. Unlike the command above, this step calls a model, so it is not bit for bit
reproducible; expect the same criterion and severity on the judged finding, not always identical
wording.

## Findings tour

`envelope.json` in this folder is the full, validated golden envelope for this artifact, both lanes
combined. It carries exactly two findings, one judged, one scripted, both walked through here in
full; this particular fixture is a short, deliberately compact page, so unlike some of this
library's other worked examples there is no larger set to pick a representative subset from. Both
findings, per the golden fixture's own curation note, trace back to the same root problem, Step 2
does not belong on this page, seen through two different criteria's own tests.

### F-001, DIATAXIS-HOWTO-GOAL, severity 3, judged

**What you would see:** the page's title and named goal is resetting an account password. Step 2,
between "Step 1: Open account settings" and "Step 3: Choose a new password," is titled "Enable
two-factor authentication" and instructs toggling on 2FA and scanning a QR code with an
authenticator app.

**Why it is a violation:** `DIATAXIS-HOWTO-GOAL` asks a how-to page to carry a reader through
exactly the steps its one named task requires, without widening into a second task the reader did
not ask for (`references/DIATAXIS.md`). A reader who wants only to reset a password has to read and
perform an unrelated security change, enabling two-factor authentication, sitting directly on the
path between the first and third steps of the task they actually came for.

**What the fix means:** remove Step 2 from this page and link out to a separate how-to page for
enabling two-factor authentication instead, keeping this page to the three steps that actually reset
a password.

**What severity 3 signals:** major, fix before release. The docs domain's own severity anchors
(`docs/reference/severity-scale.md`) draw the line here on whether the reader's task is blocked, not
merely interrupted: this Step 2 sits directly on the path to Step 3, so a reader following the page
straight through cannot reach the step that finishes their own task without also completing an
unrelated one first.

### F-002, DIATAXIS-MODE, severity 2, scripted

**What you would see:** inside Step 2, the third list item reads: "Because two-factor authentication
protects the account from password reuse elsewhere, we recommend turning it on now."

**Why it is a violation:** `DIATAXIS-MODE` asks every sentence on a page to stay inside its declared
mode's register, here how-to's imperative, action-first register, and flags any sentence that opens
with a fixed marker belonging to a different mode instead (`references/DIATAXIS.md`, "Marker
registry and thresholds"). This sentence opens with "Because," one of the closed set of
explanation-register markers, which is exactly the pattern this skill's scripted check exists to
catch mechanically, no judgment call required.

**What the fix means:** rewrite the sentence in the how-to page's own imperative register, for
example an instruction to turn it on now, or move the reasoning itself to a page in the mode it
actually belongs to.

**What severity 2 signals:** minor, backlog. This is a single flagged sentence, not a pattern that
recurs across the page; `references/DIATAXIS.md`'s recurrence rule for this criterion holds severity
at 2 for one instance and reserves 3 for two or more instances on the same page reading as the
page's own habitual register.

## Disposition log

Critique never edits the artifact and never auto-applies a fix; a person decides what happens to
each finding. `dispositions.json` in this folder is that decision, recorded against `envelope.json`,
`accept`, `reject`, or `defer` with a one-line reason on each. Not every finding gets accepted here,
on purpose: always-accept is not what review actually looks like.

| Finding | Criterion | Severity | Disposition | Why |
|---|---|---|---|---|
| F-001 | DIATAXIS-HOWTO-GOAL | 3 | accept | Confirmed against the page: Step 2 really does carry a reader through an unrelated task on the direct path to Step 3. Cutting Step 2 out to its own how-to page before this ships. |
| F-002 | DIATAXIS-MODE | 2 | defer | The flagged sentence lives entirely inside Step 2, the same step F-001 removes. Rewriting its wording now risks throwaway work if the removal ships first; revisit only if Step 2 is kept on this page instead of being split out. |

That defer is the honest kind: the reviewer is not disputing that F-002 names a real problem, they
are saying the fix is entangled with a bigger change already in motion, and the note says exactly
that rather than hiding a punt behind a vague "later."

## Validating the files in this example

Both JSON files here were checked against the contract before this page was written, not asserted
clean:

```
python -m contract.validate examples/docs/envelope.json
valid
python -m contract.validate examples/docs/envelope.json --gate
valid
(exit code 2, meaning "fail": one severity-3 finding above the default threshold of 0)

python -m contract.validate examples/docs/dispositions.json
valid
```

Resolving `dispositions.json`'s finding IDs against `envelope.json` needs both files loaded together
(the single-file CLI cannot do this on its own; see `docs/how-to/dispositions.md`), and that check
also ran clean before this page shipped, every `finding_id` in the log resolves in the envelope, and
every denormalized `criterion` matches.

## Files in this folder

| File | What it is |
|---|---|
| `artifact.md` | The how-to page being critiqued. Verbatim copy of `skills/critique-docs/examples/docs-golden-02-mode-and-goal.md`. |
| `envelope.json` | The full, validated run envelope for this artifact, both lanes. Verbatim copy of the `expected_envelope` in `skills/critique-docs/examples/golden-02.json`. |
| `dispositions.json` | This walkthrough's disposition log against `envelope.json`. |
| `README.md` | This page. |

## See also

- [`skills/critique-docs/SKILL.md`](../../skills/critique-docs/SKILL.md), the skill's own protocol
  and artifact claim.
- [`skills/critique-docs/references/DIATAXIS.md`](../../skills/critique-docs/references/DIATAXIS.md),
  the full nine-criterion registry, operational tests, and severity anchors cited above.
- [`docs/reference/severity-scale.md`](../../docs/reference/severity-scale.md), the 0-4 scale every
  finding's severity comes from.
- [`docs/how-to/dispositions.md`](../../docs/how-to/dispositions.md), the full shape and purpose of
  the disposition log format used above.
